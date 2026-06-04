import rclpy
import requests
import json
import math
import time
from rclpy.node import Node
from std_msgs.msg import String, Bool
from geometry_msgs.msg import PoseStamped, Twist
from sensor_msgs.msg import LaserScan
from tf2_ros import Buffer, TransformListener
from tf_transformations import euler_from_quaternion

NAME = "DOMINGUEZ PALACIOS JESUS ALEJANDRO y JONATHAN"

# ====== WAYPOINTS DE PATRULLA (celdas blancas seguras en 'map') ======
WAYPOINTS = [
    (2.93, -2.41),    # sala (sofa, tele)
    (8.88, -1.63),    # cocina (refrigerador)
    (10.83, 2.57),    # comedor / cocina norte
    (3.30, 2.51),     # centro (pelota, paso)
    (-2.30, -1.16),   # zona sur / centro
    (-3.88, 1.65),    # pasillo a recamara
]

# ====== NOMBRE EN ESPANOL -> CLASE YOLO ======
OBJETOS = {
    "sofa":         "couch",
    "refrigerador": "refrigerator",
    "television":   "tv",
    "silla":        "chair",
    "cama":         "bed",
    "pelota":       "sports ball",
    "persona":      "person",
}

# Palabras que cancelan la tarea en curso
PALABRAS_CANCELAR = ["cancela", "cancelar", "detente", "para", "alto", "stop", "detener"]

# Estados de la maquina
IDLE = 0
NAVEGANDO = 1       # yendo a un waypoint de patrulla
BUSCANDO = 2        # girando 360 en el waypoint, mirando con YOLO
CENTRANDO = 3       # vio el objeto, gira para centrarlo antes de medir
YENDO_A_OBJETO = 4  # mando meta al a_star, navegando hacia el objeto

# Parametros de busqueda visual
VEL_GIRO = 0.3          # rad/s al girar
TOL_CENTRO = 0.10       # |cx_norm| < esto = centrado
DIST_PARADA_OBJ = 1.0   # m: dejar la meta a esta distancia ENFRENTE del objeto
DIST_LLEGADA = 0.5      # m: se da por llegado si esta a menos de esto de la meta

# Umbral de tamano en pantalla (area_rel) para decidir aproximarse.
# El objeto debe verse al menos asi de grande para lanzarse hacia el.
# Si se ve mas chico (esta lejos), sigue patrullando hasta verlo mas grande.
# AJUSTAR con: ros2 topic echo /yolo/detections (mira el area_rel cuando se ve bien)
AREA_MIN_APROX = 0.015  # ~1.5% del cuadro. Subir si se lanza demasiado pronto.

# Giro de observacion: una vuelta completa (~360 grados)
T_OBSERVAR = (2 * math.pi) / VEL_GIRO

# Timeouts (anti-bucle)
T_CENTRAR_MAX = 12.0    # seg max centrando antes de rendirse
T_PERDIDO_MAX = 4.0     # seg max sin ver el objeto mientras centra
T_NAV_OBJ_MAX = 40.0    # seg max navegando hacia el objeto

SYSTEM_PROMPT = """Eres el cerebro de un robot movil de servicio en una casa.

PUEDES buscar y acercarte a estos objetos conocidos:
sofa, refrigerador, television, silla, cama, pelota, persona.

NO PUEDES (es imposible para ti):
- Volar, nadar, saltar, subir escaleras.
- Agarrar o levantar objetos pesados.
- Salir de la casa o ir a lugares que no estan en tu lista.
- Cocinar, limpiar.

El usuario te dara una instruccion en lenguaje natural. Responde
UNICAMENTE con un objeto JSON valido, sin texto adicional, sin markdown.

FORMATOS:
1. Si pide buscar uno o varios objetos conocidos (respeta el orden):
   {"accion": "ir", "lugares": ["refrigerador", "sofa"], "texto": "Voy a buscar el refrigerador y luego el sofa"}
2. Si pide algo imposible, pregunta, o objeto desconocido:
   {"accion": "decir", "texto": "Lo siento, no puedo volar"}

Usa exactamente estos nombres: sofa, refrigerador, television, silla, cama, pelota, persona.
Responde SIEMPRE en espanol en el campo texto. Solo JSON."""


class SMPlannerNode(Node):
    def __init__(self):
        super().__init__("sm_planner_node")
        self.get_logger().info("INITIALIZING FINAL PROJECT SM PLANNER - " + NAME)

        self.ollama_url = "http://localhost:11434/api/chat"
        self.model = "llama3.2:3b"

        self.estado = IDLE
        self.cola_objetivos = []
        self.new_command = None
        self.objetivo_yolo = None
        self.idx_waypoint = 0
        self.t_inicio_observar = 0.0
        self.t_inicio_centrar = 0.0
        self.t_ultima_vista = 0.0
        self.t_inicio_nav_obj = 0.0
        self.meta_obj = None           # (x, y) meta calculada del objeto

        # TF para leer la pose del robot en 'map'
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

        # Suscripciones
        self.create_subscription(String, '/sp_rec/recognized', self.cb_voz, 1)
        self.create_subscription(Bool, '/navigation/goal_reached', self.cb_llegada, 1)
        self.create_subscription(String, '/yolo/detections', self.cb_yolo, 1)
        self.create_subscription(LaserScan, '/scan', self.cb_scan, 1)

        # Publicadores
        self.pub_goal = self.create_publisher(PoseStamped, '/goal_pose', 1)
        self.pub_tts = self.create_publisher(String, '/tts_query', 1)
        self.pub_cmd = self.create_publisher(Twist, '/cmd_vel', 1)

        self.detecciones = []
        self.dist_frente = 99.0

        self.create_timer(0.1, self.ciclo)
        self.get_logger().info("SM Planner listo. Esperando comandos de voz...")

    # ---------- Callbacks ----------
    def cb_voz(self, msg):
        texto = msg.data.strip().lower()
        if len(texto) < 2:
            return
        self.get_logger().info("Comando recibido: " + texto)
        self.new_command = texto

    def cb_llegada(self, msg):
        if not msg.data:
            return
        if self.estado == NAVEGANDO:
            # Llegue a un waypoint -> observar
            self.get_logger().info("Waypoint alcanzado. Observando...")
            self.estado = BUSCANDO
            self.t_inicio_observar = time.time()
        elif self.estado == YENDO_A_OBJETO:
            # Llegue a la meta del objeto
            self.get_logger().info("Llegue a la meta del objeto.")
            self.detener_robot()
            self.hablar("Llegue al objetivo.")
            self.terminar_objetivo_actual()

    def cb_yolo(self, msg):
        try:
            self.detecciones = json.loads(msg.data)
        except Exception:
            self.detecciones = []

    def cb_scan(self, msg):
        n = len(msg.ranges)
        if n > 0:
            centro = msg.ranges[n // 2]
            if not math.isinf(centro) and not math.isnan(centro):
                self.dist_frente = centro

    # ---------- Utilidades ----------
    def detener_robot(self):
        self.pub_cmd.publish(Twist())

    def ve_objetivo(self):
        # Devuelve (cx_norm, area_rel) del objetivo si lo ve, si no None
        for d in self.detecciones:
            if d.get("clase") == self.objetivo_yolo:
                return (d.get("cx_norm", 0.0), d.get("area_rel", 0.0))
        return None

    def es_cancelacion(self, texto):
        return any(p in texto for p in PALABRAS_CANCELAR)

    def cancelar_todo(self):
        self.detener_robot()
        self.cola_objetivos = []
        self.objetivo_yolo = None
        self.estado = IDLE
        self.hablar("Busqueda cancelada.")

    def get_pose_robot(self):
        # Devuelve (x, y, yaw) del robot en 'map', o None si no hay TF
        try:
            t = self.tf_buffer.lookup_transform('map', 'base_link', rclpy.time.Time())
            x = t.transform.translation.x
            y = t.transform.translation.y
            q = t.transform.rotation
            _, _, yaw = euler_from_quaternion([q.x, q.y, q.z, q.w])
            return (x, y, yaw)
        except Exception as e:
            self.get_logger().warn("No pude leer TF map->base_link: " + str(e))
            return None

    # ---------- Ciclo principal ----------
    def ciclo(self):
        # Comandos nuevos en cualquier estado (interrupcion en caliente)
        if self.new_command is not None:
            comando = self.new_command
            self.new_command = None
            if self.es_cancelacion(comando):
                self.get_logger().info("Cancelacion solicitada.")
                self.cancelar_todo()
                return
            self.detener_robot()
            self.procesar_comando(comando)
            return

        if self.estado == BUSCANDO:
            self.ciclo_observar()
        elif self.estado == CENTRANDO:
            self.ciclo_centrar()
        elif self.estado == YENDO_A_OBJETO:
            self.ciclo_yendo_a_objeto()

    def ciclo_observar(self):
        objetivo = self.ve_objetivo()
        if objetivo is not None:
            cx, area = objetivo
            if area >= AREA_MIN_APROX:
                # Se ve suficientemente grande -> vale la pena aproximarse
                self.get_logger().info(
                    f"Objetivo detectado (area={area:.3f}). Centrando...")
                self.detener_robot()
                self.estado = CENTRANDO
                self.t_inicio_centrar = time.time()
                self.t_ultima_vista = time.time()
                return
            else:
                # Lo veo pero muy chico (lejos): no me lanzo, sigo observando/patrulla
                self.get_logger().info(
                    f"Veo el objetivo pero chico (area={area:.3f} < {AREA_MIN_APROX}). Sigo buscando.")

        if time.time() - self.t_inicio_observar > T_OBSERVAR:
            self.detener_robot()
            self.siguiente_waypoint()
            return

        cmd = Twist()
        cmd.angular.z = VEL_GIRO
        self.pub_cmd.publish(cmd)

    def ciclo_centrar(self):
        ahora = time.time()

        # Timeout total centrando
        if ahora - self.t_inicio_centrar > T_CENTRAR_MAX:
            self.get_logger().info("Centrar tardo demasiado. Sigo patrulla.")
            self.detener_robot()
            self.siguiente_waypoint()
            return

        objetivo = self.ve_objetivo()
        if objetivo is None:
            # Lo perdi: girar despacio para reencontrarlo, con limite
            if ahora - self.t_ultima_vista > T_PERDIDO_MAX:
                self.get_logger().info("Perdi el objetivo al centrar. Sigo patrulla.")
                self.detener_robot()
                self.siguiente_waypoint()
                return
            cmd = Twist()
            cmd.angular.z = VEL_GIRO
            self.pub_cmd.publish(cmd)
            return

        cx, area = objetivo
        self.t_ultima_vista = ahora

        if abs(cx) >= TOL_CENTRO:
            # Aun no centrado: girar
            cmd = Twist()
            cmd.angular.z = -0.5 * cx
            if cmd.angular.z > VEL_GIRO:  cmd.angular.z = VEL_GIRO
            if cmd.angular.z < -VEL_GIRO: cmd.angular.z = -VEL_GIRO
            self.pub_cmd.publish(cmd)
            return

        # Centrado! Calcular la posicion del objeto y mandar meta al a_star
        self.detener_robot()
        self.calcular_y_mandar_meta()

    def calcular_y_mandar_meta(self):
        pose = self.get_pose_robot()
        if pose is None:
            self.hablar("No puedo ubicarme. Sigo buscando.")
            self.siguiente_waypoint()
            return

        rx, ry, ryaw = pose
        d = self.dist_frente   # distancia frontal al objeto (laser)

        # Si el laser no ve nada util, no arriesgar
        if d > 90.0:
            self.get_logger().info("Laser sin lectura frontal valida. Sigo patrulla.")
            self.siguiente_waypoint()
            return

        # Dejar la meta a DIST_PARADA_OBJ enfrente del objeto (no encima)
        d_meta = max(d - DIST_PARADA_OBJ, 0.0)
        ox = rx + d_meta * math.cos(ryaw)
        oy = ry + d_meta * math.sin(ryaw)
        self.meta_obj = (ox, oy)

        goal = PoseStamped()
        goal.header.frame_id = "map"
        goal.header.stamp = self.get_clock().now().to_msg()
        goal.pose.position.x = float(ox)
        goal.pose.position.y = float(oy)
        goal.pose.orientation.w = 1.0
        self.pub_goal.publish(goal)

        self.estado = YENDO_A_OBJETO
        self.t_inicio_nav_obj = time.time()
        self.get_logger().info(
            f"Objeto a {d:.2f} m. Meta en ({ox:.2f}, {oy:.2f}). Navegando con a_star...")
        self.hablar("Encontre el objetivo, voy hacia el.")

    def ciclo_yendo_a_objeto(self):
        ahora = time.time()

        # Timeout de navegacion al objeto
        if ahora - self.t_inicio_nav_obj > T_NAV_OBJ_MAX:
            self.get_logger().info("Navegacion al objeto tardo demasiado. Sigo patrulla.")
            self.detener_robot()
            self.siguiente_waypoint()
            return

        # Respaldo: si ya estoy muy cerca de la meta segun TF, dar por llegado
        pose = self.get_pose_robot()
        if pose is not None and self.meta_obj is not None:
            rx, ry, _ = pose
            mx, my = self.meta_obj
            if math.hypot(mx - rx, my - ry) < DIST_LLEGADA:
                self.get_logger().info("Cerca de la meta del objeto (por TF).")
                self.detener_robot()
                self.hablar("Llegue al objetivo.")
                self.terminar_objetivo_actual()
                return
        # Si no, esperar a /navigation/goal_reached (manejado en cb_llegada)

    # ---------- Flujo de objetivos / patrulla ----------
    def siguiente_waypoint(self):
        self.idx_waypoint += 1
        if self.idx_waypoint < len(WAYPOINTS):
            self.ir_a_waypoint(self.idx_waypoint)
        else:
            self.hablar("No encontre el objeto.")
            self.terminar_objetivo_actual()

    def terminar_objetivo_actual(self):
        if self.cola_objetivos:
            self.iniciar_busqueda_siguiente()
        else:
            self.estado = IDLE
            self.hablar("Tarea completada.")

    def procesar_comando(self, comando):
        respuesta = self.consultar_llm(comando)
        if respuesta is None:
            self.hablar("Lo siento, no entendi.")
            self.estado = IDLE
            return
        accion = respuesta.get("accion", "decir")
        texto = respuesta.get("texto", "")
        if accion == "ir":
            lugares = respuesta.get("lugares", [])
            validos = [l for l in lugares if l in OBJETOS]
            if not validos:
                self.hablar("No conozco ese objeto.")
                self.estado = IDLE
                return
            self.cola_objetivos = validos
            if texto:
                self.hablar(texto)
            self.iniciar_busqueda_siguiente()
        else:
            self.hablar(texto if texto else "No puedo hacer eso.")
            self.estado = IDLE

    def iniciar_busqueda_siguiente(self):
        objetivo = self.cola_objetivos.pop(0)
        self.objetivo_yolo = OBJETOS[objetivo]
        self.idx_waypoint = 0
        self.get_logger().info(f"Buscando '{objetivo}' (clase YOLO '{self.objetivo_yolo}')")
        self.ir_a_waypoint(0)

    def ir_a_waypoint(self, idx):
        x, y = WAYPOINTS[idx]
        goal = PoseStamped()
        goal.header.frame_id = "map"
        goal.header.stamp = self.get_clock().now().to_msg()
        goal.pose.position.x = float(x)
        goal.pose.position.y = float(y)
        goal.pose.orientation.w = 1.0
        self.pub_goal.publish(goal)
        self.estado = NAVEGANDO
        self.get_logger().info(f"Navegando al waypoint {idx} ({x}, {y})")

    def hablar(self, texto):
        msg = String()
        msg.data = texto
        self.pub_tts.publish(msg)
        self.get_logger().info("Robot dice: " + texto)

    def consultar_llm(self, comando):
        try:
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": comando}
                ],
                "stream": False,
                "format": "json",
                "options": {"temperature": 0.2}
            }
            resp = requests.post(self.ollama_url, json=payload, timeout=30)
            contenido = resp.json()["message"]["content"]
            self.get_logger().info("LLM respondio: " + contenido)
            return json.loads(contenido)
        except Exception as e:
            self.get_logger().error("Error consultando LLM: " + str(e))
            return None


def main(args=None):
    rclpy.init(args=args)
    node = SMPlannerNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()