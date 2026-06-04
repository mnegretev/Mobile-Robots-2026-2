import rclpy
import requests
import json
import math
import time
from rclpy.node import Node
from std_msgs.msg import String, Bool
from geometry_msgs.msg import PoseStamped, Twist
from sensor_msgs.msg import LaserScan

NAME = "DOMINGUEZ PALACIOS JESUS ALEJANDRO y JONATHAN"

# ====== ZONAS APROXIMADAS DE OBJETOS (coordenada x,y en 'map') ======
# PROVISIONALES: ajustar con Publish Point en RViz.
ZONAS = {
    "sofa":         {"xy": (-2.00, 1.00),  "yolo": "couch"},
    "refrigerador": {"xy": (1.10, 2.70),   "yolo": "refrigerator"},
    "television":   {"xy": (0.50, 3.00),   "yolo": "tv"},
    "silla":        {"xy": (-1.00, -1.00), "yolo": "chair"},
    "comoda":       {"xy": (0.80, 2.50),   "yolo": "bench"},
    "persona":      {"xy": (0.00, 3.00),   "yolo": "person"},
    "pelota":       {"xy": (2.00, 0.00),   "yolo": "sports ball"},
}

# Estados de la maquina
IDLE = 0
NAVEGANDO = 1
BUSCANDO = 2

# Parametros de busqueda visual
VEL_GIRO = 0.3          # rad/s al girar buscando
TOL_CENTRO = 0.12       # |cx_norm| < esto = centrado
TIMEOUT_BUSQUEDA = 25.0 # segundos max girando antes de rendirse

SYSTEM_PROMPT = """Eres el cerebro de un robot movil de servicio en una casa.

PUEDES navegar a estos objetos/lugares conocidos:
sofa, refrigerador, television, silla, comoda, persona, pelota.

NO PUEDES (es imposible para ti):
- Volar, nadar, saltar, subir escaleras.
- Agarrar o levantar objetos pesados.
- Salir de la casa o ir a lugares que no estan en tu lista.
- Cocinar, limpiar.

El usuario te dara una instruccion en lenguaje natural. Responde
UNICAMENTE con un objeto JSON valido, sin texto adicional, sin markdown.

FORMATOS:
1. Si pide ir a uno o varios lugares conocidos (respeta el orden):
   {"accion": "ir", "lugares": ["refrigerador", "sofa"], "texto": "Voy al refrigerador y luego al sofa"}
2. Si pide algo imposible, pregunta, o lugar desconocido:
   {"accion": "decir", "texto": "Lo siento, no puedo volar"}

Usa exactamente estos nombres: sofa, refrigerador, television, silla, comoda, persona, pelota.
Responde SIEMPRE en espanol en el campo texto. Solo JSON."""


class SMPlannerNode(Node):
    def __init__(self):
        super().__init__("sm_planner_node")
        self.get_logger().info("INITIALIZING FINAL PROJECT SM PLANNER - " + NAME)

        self.ollama_url = "http://localhost:11434/api/chat"
        self.model = "llama3.2:3b"

        self.estado = IDLE
        self.cola_destinos = []
        self.new_command = None
        self.objetivo_yolo = None      # clase YOLO que busca ahora
        self.t_inicio_busqueda = 0.0

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

    def cb_voz(self, msg):
        texto = msg.data.strip()
        if len(texto) < 2:
            return
        if self.estado != IDLE:
            self.get_logger().info("Ocupado, ignoro: " + texto)
            return
        self.get_logger().info("Comando recibido: " + texto)
        self.new_command = texto

    def cb_llegada(self, msg):
        # Llego a la zona -> pasar a BUSCAR el objeto con la camara
        if msg.data and self.estado == NAVEGANDO:
            self.get_logger().info("Zona alcanzada. Iniciando busqueda visual...")
            self.estado = BUSCANDO
            self.t_inicio_busqueda = time.time()

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

    def detener_robot(self):
        self.pub_cmd.publish(Twist())  # todo en cero

    def buscar_objetivo_en_detecciones(self):
        # Devuelve cx_norm del objetivo si lo ve, si no None
        for d in self.detecciones:
            if d.get("clase") == self.objetivo_yolo:
                return d.get("cx_norm", 0.0)
        return None

    def ciclo(self):
        if self.estado == IDLE:
            if self.new_command is not None:
                comando = self.new_command
                self.new_command = None
                self.procesar_comando(comando)

        elif self.estado == BUSCANDO:
            self.ciclo_busqueda()

    def ciclo_busqueda(self):
        # Timeout: si tarda mucho, rendirse
        if time.time() - self.t_inicio_busqueda > TIMEOUT_BUSQUEDA:
            self.detener_robot()
            self.hablar("No encuentro el objeto.")
            self.terminar_destino_actual()
            return

        cx = self.buscar_objetivo_en_detecciones()
        cmd = Twist()
        if cx is None:
            # No lo veo: girar lentamente para buscar
            cmd.angular.z = VEL_GIRO
            self.pub_cmd.publish(cmd)
        else:
            # Lo veo: girar para centrarlo
            if abs(cx) < TOL_CENTRO:
                # Centrado -> (Capa 3 sera avanzar; por ahora paramos)
                self.detener_robot()
                self.hablar("Veo el objetivo, esta centrado.")
                self.terminar_destino_actual()
            else:
                # girar hacia el objeto: si cx>0 (derecha) -> giro negativo
                cmd.angular.z = -0.5 * cx
                # limitar velocidad
                if cmd.angular.z > VEL_GIRO: cmd.angular.z = VEL_GIRO
                if cmd.angular.z < -VEL_GIRO: cmd.angular.z = -VEL_GIRO
                self.pub_cmd.publish(cmd)

    def terminar_destino_actual(self):
        # Pasa al siguiente destino de la cola, o vuelve a IDLE
        if self.cola_destinos:
            self.enviar_siguiente_destino()
        else:
            self.estado = IDLE
            self.hablar("Tarea completada.")

    def procesar_comando(self, comando):
        respuesta = self.consultar_llm(comando)
        if respuesta is None:
            self.hablar("Lo siento, no entendi.")
            return
        accion = respuesta.get("accion", "decir")
        texto = respuesta.get("texto", "")
        if accion == "ir":
            lugares = respuesta.get("lugares", [])
            validos = [l for l in lugares if l in ZONAS]
            if not validos:
                self.hablar("No conozco ese lugar.")
                return
            self.cola_destinos = validos
            if texto:
                self.hablar(texto)
            self.enviar_siguiente_destino()
        else:
            self.hablar(texto if texto else "No puedo hacer eso.")

    def enviar_siguiente_destino(self):
        lugar = self.cola_destinos.pop(0)
        self.objetivo_yolo = ZONAS[lugar]["yolo"]
        x, y = ZONAS[lugar]["xy"]
        goal = PoseStamped()
        goal.header.frame_id = "map"
        goal.header.stamp = self.get_clock().now().to_msg()
        goal.pose.position.x = float(x)
        goal.pose.position.y = float(y)
        goal.pose.orientation.w = 1.0
        self.pub_goal.publish(goal)
        self.estado = NAVEGANDO
        self.get_logger().info(f"Navegando a zona de '{lugar}' ({x}, {y}), buscare '{self.objetivo_yolo}'")

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
