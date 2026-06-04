import rclpy
import requests
import json
import math
from rclpy.node import Node
from std_msgs.msg import String, Bool
from geometry_msgs.msg import PoseStamped

# ================== NOMBRE PARA EL LOG (estilo Negrete) ==================
NAME = "DOMINGUEZ PALACIOS JESUS ALEJANDRO y JONATHAN"

# ================== DICCIONARIO DE LUGARES CONOCIDOS ==================
# Coordenadas (x, y) en el marco 'map'. Sacar con "Publish Point" en RViz.
# TODO: ajustar estas coordenadas a los muebles reales de house.world
PLACES = {
    "refrigerador": (1.10, 2.70),
    "sofa":         (-2.00, 1.00),
    "cama":         (3.50, -1.50),
    "cocina":       (1.50, 2.50),
    "sala":         (-1.50, 0.50),
}

# ================== PROMPT DE SISTEMA PARA EL LLM ==================
# Define las capacidades y limitaciones del robot, y obliga a respuesta en JSON.
SYSTEM_PROMPT = """Eres el cerebro de un robot movil de servicio en una casa.

PUEDES:
- Navegar a estos lugares conocidos: refrigerador, sofa, cama, cocina, sala.
- Responder preguntas sobre ti mismo (de que estas hecho, que puedes hacer).

NO PUEDES (es imposible para ti):
- Volar, nadar, saltar, subir escaleras.
- Agarrar o levantar objetos pesados.
- Salir de la casa o ir a lugares que no estan en tu lista.
- Cocinar, limpiar, o tareas que requieran manos habiles.

El usuario te dara una instruccion en lenguaje natural. Debes responder
UNICAMENTE con un objeto JSON valido, sin texto adicional, sin markdown.

FORMATOS DE RESPUESTA:
1. Si pide ir a uno o varios lugares conocidos (en orden):
   {"accion": "ir", "lugares": ["refrigerador", "sofa"], "texto": "Voy al refrigerador y luego al sofa"}
2. Si pide algo imposible, hace una pregunta, o pide un lugar desconocido:
   {"accion": "decir", "texto": "Lo siento, no puedo volar"}

Responde SIEMPRE en espanol en el campo texto. Solo JSON, nada mas."""


class SMPlannerNode(Node):
    def __init__(self):
        super().__init__("sm_planner_node")
        self.get_logger().info("INITIALIZING FINAL PROJECT SM PLANNER - " + NAME)

        # --- Conexion con Ollama ---
        self.ollama_url = "http://localhost:11434/api/chat"
        self.model = "llama3.2:3b"

        # --- Estado interno ---
        self.cola_destinos = []      # lista de lugares pendientes
        self.navegando = False       # True mientras el robot va en camino
        self.new_command = None      # comando de voz recibido

        # --- Suscripciones ---
        self.create_subscription(String, '/sp_rec/recognized', self.cb_voz, 1)
        self.create_subscription(Bool, '/navigation/goal_reached', self.cb_llegada, 1)

        # --- Publicadores ---
        self.pub_goal = self.create_publisher(PoseStamped, '/goal_pose', 1)
        self.pub_tts = self.create_publisher(String, '/tts_query', 1)

        # --- Timer principal del ciclo ---
        self.create_timer(0.2, self.ciclo)
        self.get_logger().info("SM Planner listo. Esperando comandos de voz...")

    # ============ CALLBACK: llega texto de voz ============
    def cb_voz(self, msg):
        texto = msg.data.strip()
        if len(texto) < 2:
            return
        if self.navegando:
            self.get_logger().info("Ocupado navegando, ignoro: " + texto)
            return
        self.get_logger().info("Comando recibido: " + texto)
        self.new_command = texto

    # ============ CALLBACK: el robot llego al destino ============
    def cb_llegada(self, msg):
        if msg.data and self.navegando:
            self.get_logger().info("Destino alcanzado.")
            self.navegando = False
            # Si quedan mas destinos en la cola, manda el siguiente
            if self.cola_destinos:
                self.enviar_siguiente_destino()
            else:
                self.hablar("He llegado a mi destino final.")

    # ============ CICLO PRINCIPAL ============
    def ciclo(self):
        if self.new_command is not None and not self.navegando:
            comando = self.new_command
            self.new_command = None
            self.procesar_comando(comando)

    # ============ PROCESAR: consulta al LLM y decide ============
    def procesar_comando(self, comando):
        respuesta = self.consultar_llm(comando)
        if respuesta is None:
            self.hablar("Lo siento, no entendi.")
            return

        accion = respuesta.get("accion", "decir")
        texto = respuesta.get("texto", "")

        if accion == "ir":
            lugares = respuesta.get("lugares", [])
            # Filtra solo los lugares que conocemos
            validos = [l for l in lugares if l in PLACES]
            if not validos:
                self.hablar("No conozco ese lugar.")
                return
            self.cola_destinos = validos
            if texto:
                self.hablar(texto)
            self.enviar_siguiente_destino()
        else:
            # accion == "decir" (pregunta, imposible, etc.)
            self.hablar(texto if texto else "No puedo hacer eso.")

    # ============ ENVIAR SIGUIENTE DESTINO DE LA COLA ============
    def enviar_siguiente_destino(self):
        lugar = self.cola_destinos.pop(0)
        x, y = PLACES[lugar]
        goal = PoseStamped()
        goal.header.frame_id = "map"
        goal.header.stamp = self.get_clock().now().to_msg()
        goal.pose.position.x = float(x)
        goal.pose.position.y = float(y)
        goal.pose.orientation.w = 1.0
        self.pub_goal.publish(goal)
        self.navegando = True
        self.get_logger().info(f"Navegando a '{lugar}' ({x}, {y})")

    # ============ HABLAR (publica en /tts_query) ============
    def hablar(self, texto):
        msg = String()
        msg.data = texto
        self.pub_tts.publish(msg)
        self.get_logger().info("Robot dice: " + texto)

    # ============ CONSULTAR AL LLM (Ollama) ============
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