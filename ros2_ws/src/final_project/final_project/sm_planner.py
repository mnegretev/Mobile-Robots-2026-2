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

NAME = "DOMINGUEZ PALACIOS JESUS ALEJANDRO y JONATHAN URIEL GONZALEZ FERNANDEZ"

# Estos son los puntos por los que el robot va pasando para buscar (los saque
# del mapa, son lugares donde el robot cabe bien y no se atora en paredes)
WAYPOINTS = [
    (2.66, 2.47),     # 0: el centro, aqui empieza
    (8.88, -1.63),    # 1: la cocina (donde esta el refri)
    (10.83, 2.57),    # 2: el comedor
    (3.30, 2.51),     # 3: centro otra vez (por la pelota)
    (-2.30, -1.16),   # 4: la parte de abajo
    (-3.88, 1.65),    # 5: la recamara
    (2.93, -2.41),    # 6: la sala, este es el ultimo
]

# Aqui guardo cada objeto que el robot puede buscar. Le puse el nombre en espanol
# y a cada uno su clase de YOLO (en ingles) y unos numeros que fui ajustando a prueba
# y error:
#   area_min = que tan grande se tiene que ver para que diga "ya lo encontre"
#   dist_directo = si esta mas cerca que esto, le mando la meta directa. Los objetos
#                  grandes (refri, sofa, cama) van directo desde lejos porque de cerca
#                  YOLO ya no los reconoce bien. La pelota es chica asi que se acerca poco a poco.
#   dist_parada = que tan cerca se queda del objeto al final (para no quedar encima)
OBJETOS = {

    "sofa":         {"yolo": "couch",        "area_min": 0.030, "dist_directo": 9.0, "dist_parada": 1.0},
    "refrigerador": {"yolo": "refrigerator", "area_min": 0.030, "dist_directo": 9.0, "dist_parada": 0.7},
    "television":   {"yolo": "tv",           "area_min": 0.020, "dist_directo": 6.0, "dist_parada": 1.0},
    "silla":        {"yolo": "chair",        "area_min": 0.020, "dist_directo": 5.0, "dist_parada": 0.5},
    "cama":         {"yolo": "bed",          "area_min": 0.040, "dist_directo": 9.0, "dist_parada": 1.0},   
    "pelota":       {"yolo": "sports ball",  "area_min": 0.006, "dist_directo": 4.0, "dist_parada": 0.5},
    "persona":      {"yolo": "person",       "area_min": 0.010, "dist_directo": 5.0, "dist_parada": 0.5},

}

# Si el usuario dice alguna de estas palabras, el robot cancela lo que estaba haciendo
PALABRAS_CANCELAR = ["cancela", "cancelar", "detente", "para", "alto", "stop", "detener"]

# Los estados de la maquina de estados (le puse numeros para que sea facil)
IDLE = 0            # sin hacer nada, esperando
NAVEGANDO = 1       # yendo a un punto de busqueda
BUSCANDO = 2        # girando en su lugar buscando con la camara
CENTRANDO = 3       # ya vio el objeto y se acomoda para quedar de frente
YENDO_A_OBJETO = 4  # ya calculo donde esta y va para alla

# Velocidades y tolerancias que fui calibrando
VEL_GIRO = 0.25         # que tan rapido gira buscando (lo baje porque si gira rapido se pierde la localizacion)
VEL_CENTRAR = 0.3       # velocidad para acomodarse de frente al objeto
TOL_CENTRO = 0.20       # si el objeto esta casi al centro de la camara, ya cuenta como centrado
DIST_LLEGADA = 0.5      # si esta a menos de esto de la meta, ya llego

PASO_INTERMEDIO = 3.0   # cuanto avanza de un jalon cuando va por pedazos hacia el objeto

MOV_MIN_LLEGADA = 0.5   # cuanto se tiene que haber movido para creerse que ya llego
                        # (solo lo reviso cuando todavia esta lejos, por si el goal_reached miente)

# Solo interrumpo el camino si estoy MUY seguro (85%) de que es el objeto
CONF_INTERRUMPIR = 0.85

# Cuanto tarda en dar una vuelta completa girando
T_OBSERVAR = (2 * math.pi) / VEL_GIRO

# Tiempos maximos para que no se quede pegado en algo
T_CENTRAR_MAX = 12.0    # max acomodandose antes de rendirse
T_PERDIDO_MAX = 4.0     # max sin ver el objeto mientras se acomoda
T_NAV_OBJ_MAX = 60.0    # max yendo hacia el objeto (le puse harto porque el robot va lento)

# Cuantas veces reintenta un tramo si se tarda mucho antes de rendirse
MAX_REINTENTOS_TRAMO = 1

# Esto es lo que le digo al modelo de lenguaje (ollama) para que entienda las ordenes
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

        # Datos para conectarme a ollama (el modelo de lenguaje corre local)
        self.ollama_url = "http://localhost:11434/api/chat"
        self.model = "llama3.2:3b"

        # Variables de estado del robot
        self.estado = IDLE
        self.cola_objetivos = []        # lista de objetos que tengo que ir buscando en orden
        self.new_command = None         # aqui guardo el ultimo comando que llego
        self.objetivo_yolo = None       # la clase de YOLO del objeto que busco ahorita
        self.es_primer_objetivo = True  # para saber si es el primero de la orden
        self.area_min_actual = 0.015    # los parametros del objeto actual (se actualizan)
        self.dist_directo_actual = 4.0
        self.dist_parada_actual = 1.0
        self.yaw_anterior = None        # para medir cuanto he girado de verdad usando el TF
        self.angulo_girado = 0.0        # acumulo el angulo girado aqui
        self.orden_visita = []          # el orden en que voy a visitar los waypoints
        self.idx_orden = 0              # en cual voy
        self.escaneo_en_sitio = False   # True cuando giro en mi lugar antes de patrullar
        self.t_inicio_observar = 0.0
        self.t_inicio_centrar = 0.0
        self.t_ultima_vista = 0.0
        self.t_inicio_nav_obj = 0.0
        self.meta_obj = None            # el punto al que voy ahorita (puede ser un pedazo del camino)
        self.meta_final = None          # el punto final donde esta el objeto (no cambia)
        self.pose_al_mandar_meta = None # donde estaba cuando mande la meta (para revisar si me movi)
        self.meta_es_intermedia = False # True si es un paso intermedio (objeto chico, vuelvo a buscar)
        self.meta_es_tramo = False      # True si es un pedazo del camino al objeto (no vuelvo a buscar)
        self.reintentos_tramo = 0

        # El TF me dice donde esta el robot en el mapa
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

        # Me suscribo a los topicos que necesito escuchar
        self.create_subscription(String, '/sp_rec/recognized', self.cb_voz, 1)        # los comandos de voz
        self.create_subscription(Bool, '/navigation/goal_reached', self.cb_llegada, 1) # cuando llego a una meta
        self.create_subscription(String, '/yolo/detections', self.cb_yolo, 1)          # lo que ve la camara
        self.create_subscription(LaserScan, '/scan', self.cb_scan, 1)                  # el laser

        # Los topicos donde publico cosas
        self.pub_goal = self.create_publisher(PoseStamped, '/goal_pose', 1)  # mando metas al navegador
        self.pub_tts = self.create_publisher(String, '/tts_query', 1)        # hago que el robot hable
        self.pub_cmd = self.create_publisher(Twist, '/cmd_vel', 1)           # muevo el robot directo (para girar)

        self.detecciones = []      # ultimas cosas que vio YOLO
        self.dist_frente = 99.0    # distancia al frente segun el laser

        # Un timer que llama a self.ciclo cada 0.1 segundos (10 veces por segundo)
        self.create_timer(0.1, self.ciclo)
        self.get_logger().info("SM Planner listo. Esperando comandos de voz...")

    # ---------- Callbacks (se llaman solos cuando llega info) ----------
    def cb_voz(self, msg):
        # Llega un comando de voz, lo guardo para procesarlo en el ciclo
        texto = msg.data.strip().lower()
        if len(texto) < 2:
            return
        self.get_logger().info("Comando recibido: " + texto)
        self.new_command = texto

    def cb_llegada(self, msg):
        # El navegador me avisa que llegue a la meta
        if not msg.data:
            return
        if self.estado == NAVEGANDO:
            # Llegue a un waypoint, ahora me pongo a girar para buscar
            self.get_logger().info("Waypoint alcanzado. Observando...")
            self.estado = BUSCANDO
            self.t_inicio_observar = time.time()
            self.yaw_anterior = None
            self.angulo_girado = 0.0
        elif self.estado == YENDO_A_OBJETO:
            # Llegue cerca del objeto, reviso si de verdad llegue
            pose = self.get_pose_robot()
            if pose is not None:
                self.procesar_llegada_a_meta(pose)

    def cb_yolo(self, msg):
        # Guardo lo que ve la camara (viene en JSON)
        try:
            self.detecciones = json.loads(msg.data)
        except Exception:
            self.detecciones = []

    def cb_scan(self, msg):
        # Saco la distancia al frente. No uso solo el rayo del centro sino un
        # pedacito de enfrente y agarro el mas cercano, asi no me equivoco si
        # justo el rayo del centro se mete por un hueco
        n = len(msg.ranges)
        if n > 0:
            c = n // 2
            ventana = msg.ranges[max(0, c - 10):min(n, c + 10)]
            validos = [r for r in ventana
                       if not math.isinf(r) and not math.isnan(r) and r > 0.05]
            if validos:
                self.dist_frente = min(validos)

    # ---------- Funciones de ayuda ----------
    def detener_robot(self):
        # Mando velocidad cero para que se pare
        self.pub_cmd.publish(Twist())

    def ve_objetivo(self):
        # Reviso si entre lo que ve la camara esta mi objetivo. Devuelve sus datos o None
        for d in self.detecciones:
            if d.get("clase") == self.objetivo_yolo:
                return (d.get("cx_norm", 0.0), d.get("area_rel", 0.0), d.get("conf", 0.0))
        return None

    def es_cancelacion(self, texto):
        # Reviso si el comando es una palabra de cancelar
        return any(p in texto for p in PALABRAS_CANCELAR)

    def cancelar_todo(self):
        # Cancelo todo y vuelvo a estar quieto
        self.detener_robot()
        self.cola_objetivos = []
        self.objetivo_yolo = None
        self.meta_final = None
        self.meta_obj = None
        self.escaneo_en_sitio = False
        self.estado = IDLE
        self.hablar("Busqueda cancelada.")

    def get_pose_robot(self):
        # Le pregunto al TF donde estoy en el mapa. Devuelve (x, y, angulo) o None
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

    def waypoint_mas_cercano(self, pose):
        # Busco cual waypoint esta mas cerca de donde estoy ahorita
        rx, ry, _ = pose
        mejor_idx = 0
        mejor_dist = float('inf')
        for i, (wx, wy) in enumerate(WAYPOINTS):
            d = math.hypot(wx - rx, wy - ry)
            if d < mejor_dist:
                mejor_dist = d
                mejor_idx = i
        return mejor_idx

    def construir_orden_visita(self, idx_inicio):
        # Armo el orden de waypoints empezando por uno y dando la vuelta completa,
        # para no saltarme ninguno. Ej: empiezo en el 3 -> [3,4,5,6,0,1,2]
        n = len(WAYPOINTS)
        return [(idx_inicio + k) % n for k in range(n)]

    # ---------- El ciclo principal (se repite cada 0.1s) ----------
    def ciclo(self):
        # Primero reviso si llego un comando nuevo (esto manda sobre todo lo demas)
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

        # Segun el estado en el que este, hago una cosa u otra
        if self.estado == NAVEGANDO:
            self.ciclo_navegando()
        elif self.estado == BUSCANDO:
            self.ciclo_observar()
        elif self.estado == CENTRANDO:
            self.ciclo_centrar()
        elif self.estado == YENDO_A_OBJETO:
            self.ciclo_yendo_a_objeto()

    def ciclo_navegando(self):
        # Mientras voy a un waypoint, voy checando si ya veo el objeto. Si lo veo
        # muy seguro y bien grande, mejor me desvio y voy por el de una vez
        objetivo = self.ve_objetivo()
        if objetivo is not None:
            cx, area, conf = objetivo
            if conf >= CONF_INTERRUMPIR and area >= self.area_min_actual:
                self.get_logger().info(
                    f"Objetivo visto en ruta (conf={conf:.2f}, area={area:.3f}). "
                    f"Interrumpo viaje y me aproximo.")
                self.detener_robot()
                self.estado = CENTRANDO
                self.t_inicio_centrar = time.time()
                self.t_ultima_vista = time.time()
        # Si no lo veo, dejo que el navegador siga llevandome al waypoint

    def ciclo_observar(self):
        # Aqui giro en mi lugar buscando el objeto con la camara
        objetivo = self.ve_objetivo()
        if objetivo is not None:
            cx, area, conf = objetivo
            if area >= self.area_min_actual:
                # Lo veo bien grande, vale la pena ir por el
                self.get_logger().info(
                    f"Objetivo detectado (area={area:.3f}). Centrando...")
                self.escaneo_en_sitio = False
                self.detener_robot()
                self.estado = CENTRANDO
                self.t_inicio_centrar = time.time()
                self.t_ultima_vista = time.time()
                return
            else:
                # Lo veo pero chiquito (lejos), todavia no me lanzo
                self.get_logger().info(
                    f"Veo el objetivo pero chico (area={area:.3f} < {self.area_min_actual}). Sigo buscando.")

        # Voy midiendo cuanto he girado de verdad con el TF, asi se cuando ya di la
        # vuelta completa sin importar si el robot gira mas rapido o mas lento
        pose = self.get_pose_robot()
        if pose is not None:
            _, _, yaw = pose
            if self.yaw_anterior is not None:
                d = yaw - self.yaw_anterior
                while d > math.pi:  d -= 2 * math.pi   # esto es para que el angulo no se brinque
                while d < -math.pi: d += 2 * math.pi
                self.angulo_girado += abs(d)
            self.yaw_anterior = yaw

        if self.angulo_girado >= 2 * math.pi:
            # Ya di la vuelta completa
            self.detener_robot()
            if self.escaneo_en_sitio:
                # Era un escaneo en mi lugar y no encontre nada, entonces empiezo a
                # patrullar pero desde el waypoint mas cercano (para no regresarme hasta el inicio)
                self.escaneo_en_sitio = False
                pose = self.get_pose_robot()
                if pose is not None:
                    inicio = self.waypoint_mas_cercano(pose)
                else:
                    inicio = 0
                self.orden_visita = self.construir_orden_visita(inicio)
                self.idx_orden = 0
                self.get_logger().info(
                    f"Escaneo en sitio sin exito. Inicio patrulla en waypoint {inicio}. "
                    f"Orden: {self.orden_visita}")
                self.ir_a_waypoint(self.orden_visita[0])
            else:
                # Era un waypoint normal, me voy al siguiente
                self.get_logger().info("Vuelta completa sin encontrar (suficientemente grande).")
                self.siguiente_waypoint()
            return

        # Sigo girando
        cmd = Twist()
        cmd.angular.z = VEL_GIRO
        self.pub_cmd.publish(cmd)

    def ciclo_centrar(self):
        # Ya vi el objeto, ahora giro tantito para quedar de frente a el
        ahora = time.time()

        # Si me tardo mucho centrando, mejor me rindo y sigo patrullando
        if ahora - self.t_inicio_centrar > T_CENTRAR_MAX:
            self.get_logger().info("Centrar tardo demasiado. Sigo patrulla.")
            self.detener_robot()
            self.siguiente_waypoint()
            return

        objetivo = self.ve_objetivo()
        if objetivo is None:
            # Lo perdi de vista, giro despacito a ver si lo reencuentro
            if ahora - self.t_ultima_vista > T_PERDIDO_MAX:
                self.get_logger().info("Perdi el objetivo al centrar. Sigo patrulla.")
                self.detener_robot()
                self.siguiente_waypoint()
                return
            cmd = Twist()
            cmd.angular.z = VEL_CENTRAR
            self.pub_cmd.publish(cmd)
            return

        cx, area, conf = objetivo
        self.t_ultima_vista = ahora

        if abs(cx) >= TOL_CENTRO:
            # Todavia no esta centrado, giro hacia donde esta (despacio para no pasarme)
            cmd = Twist()
            cmd.angular.z = -0.5 * cx
            if cmd.angular.z > VEL_CENTRAR:  cmd.angular.z = VEL_CENTRAR
            if cmd.angular.z < -VEL_CENTRAR: cmd.angular.z = -VEL_CENTRAR
            self.pub_cmd.publish(cmd)
            return

        # Ya quedo centrado, ahora calculo donde esta el objeto y voy por el
        self.detener_robot()
        self.calcular_y_mandar_meta()

    def calcular_y_mandar_meta(self):
        # Calculo en que coordenada esta el objeto usando mi posicion + el laser
        pose = self.get_pose_robot()
        if pose is None:
            self.hablar("No puedo ubicarme. Sigo buscando.")
            self.siguiente_waypoint()
            return

        rx, ry, ryaw = pose
        d = self.dist_frente   # que tan lejos esta el objeto segun el laser

        # Si el laser no leyo nada bueno, no me arriesgo
        if d > 90.0:
            self.get_logger().info("Laser sin lectura frontal valida. Sigo patrulla.")
            self.siguiente_waypoint()
            return

        if d > self.dist_directo_actual:
            # El objeto esta mas lejos que su "distancia directa", entonces me acerco
            # poco a poco y vuelvo a buscar (esto es para objetos chicos como la pelota)
            d_meta = PASO_INTERMEDIO
            ox = rx + d_meta * math.cos(ryaw)
            oy = ry + d_meta * math.sin(ryaw)
            self.meta_obj = (ox, oy)
            self.meta_final = None
            self.pose_al_mandar_meta = (rx, ry)
            self.meta_es_intermedia = True
            self.meta_es_tramo = False
            self.reintentos_tramo = 0
            self._publicar_goal(ox, oy)
            self.estado = YENDO_A_OBJETO
            self.t_inicio_nav_obj = time.time()
            self.get_logger().info(
                f"Objeto LEJOS a {d:.2f} m (>{self.dist_directo_actual}). Meta intermedia en ({ox:.2f}, {oy:.2f}). Acercandome...")
            self.hablar("Veo el objetivo a lo lejos, me acerco.")
        else:
            # El objeto ya esta cerca, calculo el punto final y voy directo por pedazos
            # (esto es para objetos grandes como el refri, que de cerca YOLO ya no reconoce
            # bien, por eso ya no vuelvo a buscar, solo voy al punto que calcule)
            d_meta = max(d - self.dist_parada_actual, 0.0)
            fx = rx + d_meta * math.cos(ryaw)
            fy = ry + d_meta * math.sin(ryaw)
            self.meta_final = (fx, fy)
            self.reintentos_tramo = 0
            self.get_logger().info(
                f"Objeto a {d:.2f} m. META FINAL fija en ({fx:.2f}, {fy:.2f}) "
                f"(parada a {self.dist_parada_actual} m). Avanzando por tramos sin volver a buscar...")
            self.hablar("Encontre el objetivo, voy hacia el.")
            self._mandar_siguiente_tramo(pose)

    def _mandar_siguiente_tramo(self, pose):
        # Voy al punto final pero por pedazos (max 3m cada uno), asi el navegador no
        # tiene que planear un camino larguisimo de un jalon (que se tardaba mucho)
        rx, ry, _ = pose
        fx, fy = self.meta_final
        dx, dy = fx - rx, fy - ry
        dist_restante = math.hypot(dx, dy)

        # Si ya estoy bien cerca del punto final, ya llegue (no mando otro pedazo,
        # asi evito que si la localizacion brinca el robot se regrese)
        if dist_restante < DIST_LLEGADA:
            self.get_logger().info(
                f"Ya estoy a {dist_restante:.2f} m de la meta final (<{DIST_LLEGADA}). Llegue.")
            self.detener_robot()
            self.meta_es_tramo = False
            self.meta_es_intermedia = False
            self.get_logger().info("Llegue al objetivo.")
            self.hablar("Llegue al objetivo.")
            self.meta_final = None
            self.terminar_objetivo_actual()
            return

        if dist_restante <= PASO_INTERMEDIO:
            # Lo que falta cabe en un solo pedazo, mando directo al final
            tx, ty = fx, fy
            self.meta_es_tramo = False  # este ya es el ultimo
        else:
            # Avanzo solo 3m en direccion al objeto
            ux, uy = dx / dist_restante, dy / dist_restante
            tx = rx + PASO_INTERMEDIO * ux
            ty = ry + PASO_INTERMEDIO * uy
            self.meta_es_tramo = True   # todavia faltan mas pedazos

        self.meta_obj = (tx, ty)
        self.meta_es_intermedia = False
        self.pose_al_mandar_meta = (rx, ry)
        self.reintentos_tramo = 0
        self._publicar_goal(tx, ty)
        self.estado = YENDO_A_OBJETO
        self.t_inicio_nav_obj = time.time()
        self.get_logger().info(
            f"Tramo hacia meta final: voy a ({tx:.2f}, {ty:.2f}), "
            f"faltan {dist_restante:.2f} m a la meta.")

    def _publicar_goal(self, x, y):
        # Mando una meta al navegador (a_star)
        goal = PoseStamped()
        goal.header.frame_id = "map"
        goal.header.stamp = self.get_clock().now().to_msg()
        goal.pose.position.x = float(x)
        goal.pose.position.y = float(y)
        goal.pose.orientation.w = 1.0
        self.pub_goal.publish(goal)

    def ciclo_yendo_a_objeto(self):
        ahora = time.time()

        # Si me tardo mucho en este pedazo del camino...
        if ahora - self.t_inicio_nav_obj > T_NAV_OBJ_MAX:
            # ...le doy un reintento (tanto a los pedazos del refri como a los pasos de la pelota)
            navegando_con_reintento = (self.meta_final is not None) or self.meta_es_intermedia
            if navegando_con_reintento and self.reintentos_tramo < MAX_REINTENTOS_TRAMO:
                self.reintentos_tramo += 1
                self.get_logger().info(
                    f"Tramo/paso tardo demasiado. Reintento {self.reintentos_tramo}/{MAX_REINTENTOS_TRAMO} del mismo destino.")
                if self.meta_obj is not None:
                    self._publicar_goal(self.meta_obj[0], self.meta_obj[1])
                    self.t_inicio_nav_obj = time.time()
                return
            # Si ya reintento y nada, me rindo y sigo patrullando
            self.get_logger().info("Navegacion al objeto tardo demasiado. Sigo patrulla.")
            self.detener_robot()
            self.meta_final = None
            self.siguiente_waypoint()
            return

        # Por si el navegador no avisa, yo mismo checo con el TF si ya estoy cerca de la meta
        pose = self.get_pose_robot()
        if pose is not None and self.meta_obj is not None:
            rx, ry, _ = pose
            mx, my = self.meta_obj
            if math.hypot(mx - rx, my - ry) < DIST_LLEGADA:
                self.procesar_llegada_a_meta(pose)
                return

    def procesar_llegada_a_meta(self, pose):
        # Llegue (o eso parece). Primero reviso que de verdad me haya movido
        rx, ry, _ = pose

        # Si ya estoy pegadito a la meta, ya llegue y punto (sin importar cuanto me movi).
        # Lo de revisar el movimiento solo aplica cuando todavia estoy lejos, por si el
        # navegador miente y dice que llegue sin haberme movido
        cerca_de_meta = False
        if self.meta_obj is not None:
            mx, my = self.meta_obj
            if math.hypot(mx - rx, my - ry) < DIST_LLEGADA:
                cerca_de_meta = True

        if not cerca_de_meta and self.pose_al_mandar_meta is not None:
            px, py = self.pose_al_mandar_meta
            movido = math.hypot(rx - px, ry - py)
            if movido < MOV_MIN_LLEGADA:
                # Casi no me movi y todavia estoy lejos, fue un aviso falso, reintento
                self.get_logger().warn(
                    f"goal_reached pero solo me movi {movido:.2f} m (<{MOV_MIN_LLEGADA}) "
                    f"y aun lejos de la meta. Lo ignoro y sigo intentando.")
                if self.meta_obj is not None:
                    self._publicar_goal(self.meta_obj[0], self.meta_obj[1])
                    self.t_inicio_nav_obj = time.time()
                return

        # Ya llegue de verdad
        self.detener_robot()

        # Caso 1: era un pedazo del camino al objeto grande, mando el siguiente pedazo
        if self.meta_es_tramo and self.meta_final is not None:
            self.get_logger().info("Llegue al tramo. Sigo hacia la meta final (sin buscar).")
            self._mandar_siguiente_tramo(pose)
            return

        # Caso 2: era un paso intermedio de objeto chico (pelota), vuelvo a buscar de cerca
        if self.meta_es_intermedia:
            self.get_logger().info("Llegue a meta intermedia. Vuelvo a observar para recalcular.")
            self.estado = BUSCANDO
            self.t_inicio_observar = time.time()
            self.yaw_anterior = None
            self.angulo_girado = 0.0
            return

        # Caso 3: era la meta final, ya llegue al objeto
        self.get_logger().info("Llegue al objetivo.")
        self.hablar("Llegue al objetivo.")
        self.meta_final = None
        self.terminar_objetivo_actual()

    # ---------- Manejo de la lista de objetivos y la patrulla ----------
    def siguiente_waypoint(self):
        # Me voy al siguiente waypoint de la lista de visita
        self.idx_orden += 1
        if self.idx_orden < len(self.orden_visita):
            self.ir_a_waypoint(self.orden_visita[self.idx_orden])
        else:
            # Ya recorri todos y no lo encontre
            self.hablar("No encontre el objeto.")
            self.terminar_objetivo_actual()

    def terminar_objetivo_actual(self):
        # Termine con un objeto. Si quedan mas en la cola, sigo con el siguiente
        if self.cola_objetivos:
            self.iniciar_busqueda_siguiente()
        else:
            self.estado = IDLE
            self.hablar("Tarea completada.")

    def procesar_comando(self, comando):
        # Le paso el comando al modelo de lenguaje para que lo entienda
        respuesta = self.consultar_llm(comando)
        if respuesta is None:
            self.hablar("Lo siento, no entendi.")
            self.estado = IDLE
            return
        accion = respuesta.get("accion", "decir")
        texto = respuesta.get("texto", "")
        if accion == "ir":
            # Me pidio ir por uno o varios objetos
            lugares = respuesta.get("lugares", [])
            validos = [l for l in lugares if l in OBJETOS]  # me quedo solo con los que conozco
            if not validos:
                self.hablar("No conozco ese objeto.")
                self.estado = IDLE
                return
            self.cola_objetivos = validos
            self.es_primer_objetivo = True   # el primero arranca con patrulla normal
            if texto:
                self.hablar(texto)
            self.iniciar_busqueda_siguiente()
        else:
            # Me pidio algo que no puedo, solo lo digo
            self.hablar(texto if texto else "No puedo hacer eso.")
            self.estado = IDLE

    def iniciar_busqueda_siguiente(self):
        # Empiezo a buscar el siguiente objeto de la cola
        objetivo = self.cola_objetivos.pop(0)
        info = OBJETOS[objetivo]
        self.objetivo_yolo = info["yolo"]
        self.area_min_actual = info["area_min"]
        self.dist_directo_actual = info["dist_directo"]
        self.dist_parada_actual = info["dist_parada"]
        # Limpio todo lo del objetivo anterior para no confundirme
        self.meta_final = None
        self.meta_obj = None
        self.meta_es_tramo = False
        self.meta_es_intermedia = False
        self.reintentos_tramo = 0
        self.detecciones = []
        self.dist_frente = 99.0

        self.get_logger().info(
            f"Buscando '{objetivo}' (clase YOLO '{self.objetivo_yolo}', area_min={self.area_min_actual}, "
            f"dist_directo={self.dist_directo_actual}, dist_parada={self.dist_parada_actual})")

        if self.es_primer_objetivo:
            # Es el primero de la orden: empiezo la patrulla normal desde el waypoint 0
            self.es_primer_objetivo = False
            self.escaneo_en_sitio = False
            self.orden_visita = self.construir_orden_visita(0)
            self.idx_orden = 0
            self.ir_a_waypoint(self.orden_visita[0])
        else:
            # Ya no es el primero: como ya estoy en algun lado de la casa, primero
            # giro aqui mismo a ver si ya veo el siguiente objeto. Si lo veo, voy directo.
            # Si no, ciclo_observar arranca la patrulla desde el waypoint mas cercano
            self.get_logger().info("No es el primer objetivo: escaneo en el sitio antes de patrullar.")
            self.escaneo_en_sitio = True
            self.estado = BUSCANDO
            self.t_inicio_observar = time.time()
            self.yaw_anterior = None
            self.angulo_girado = 0.0

    def ir_a_waypoint(self, idx):
        # Mando al robot a un waypoint de la lista
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
        # Hago que el robot diga algo (lo manda al text2speech)
        msg = String()
        msg.data = texto
        self.pub_tts.publish(msg)
        self.get_logger().info("Robot dice: " + texto)

    def consultar_llm(self, comando):
        # Le mando el comando a ollama y espero que me responda en JSON
        try:
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": comando}
                ],
                "stream": False,
                "format": "json",
                "options": {"temperature": 0.2}  # temperatura baja para que sea mas predecible
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