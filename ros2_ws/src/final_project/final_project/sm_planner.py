import rclpy
from rclpy.node import Node
from rclpy.duration import Duration
from std_msgs.msg import String, Bool
from geometry_msgs.msg import PoseStamped, Twist
import requests
import json
import time

SM_WAIT_FOR_COMMAND  = 0
SM_INTERPRET_COMMAND = 10
SM_EXECUTE_PLAN      = 20
SM_WAIT_GOAL_REACHED = 40
SM_DONE              = 80

LOCATIONS = {
    "home":         {"x":  0.0,  "y":  0.0,  "w": 1.0},  # origen del mapa
    "refrigerator": {"x": 10.35, "y":  0.39, "w": 1.0},  # calibrado en RViz
    "kitchen":      {"x": 10.53, "y": -2.26, "w": 1.0},  # calibrado en RViz
    "table":        {"x":  8.92, "y":  1.41, "w": 1.0},  # calibrado en RViz
    "sofa":         {"x":  2.45, "y":  1.15, "w": 1.0},  # calibrado en RViz
    "tv":           {"x":  2.98, "y": -2.97, "w": 1.0},  # calibrado en RViz
    "bed":          {"x": -3.95, "y":  2.25, "w": 1.0},  # calibrado en RViz
    "door":         {"x": 10.29, "y": -2.71, "w": 1.0},  # calibrado en RViz
    "stove":        {"x":  5.59, "y":  0.78, "w": 1.0},  # calibrado en RViz
}

SYNONYMS = {
    "refri": "refrigerator", "refrigerador": "refrigerator",
    "nevera": "refrigerator", "refrigerator": "refrigerator",
    "cocina": "kitchen",     "kitchen": "kitchen",
    "mesa": "table",         "table": "table",
    "sofa": "sofa",          "sillon": "sofa",
    "cama": "bed",           "bed": "bed",
    "tele": "tv",            "television": "tv", "tv": "tv",
    "puerta": "door",        "door": "door",
    "estufa": "stove",       "stove": "stove",
    "inicio": "home",        "casa": "home", "base": "home", "home": "home",
}

IMPOSSIBLE = {
    "vuela": "No puedo volar.",
    "volar": "No puedo volar.",
    "teleporta": "No puedo teleportarme.",
    "desaparece": "No puedo desaparecer.",
}

SYSTEM_PROMPT = (
    "Eres un planificador de acciones para un robot móvil de servicio en simulación. "
    "Respondes ÚNICAMENTE con listas de acciones ejecutables, una por línea, sin explicaciones ni texto adicional. "
    "Termina siempre con END en la última línea.\n"
    "Lugares disponibles: refrigerator, kitchen, table, sofa, bed, tv, door, stove, home.\n"
    "Acciones disponibles:\n"
    "  NAVIGATE lugar  -> mueve el robot al lugar indicado\n"
    "  SPEAK texto     -> el robot dice el texto en voz alta\n"
    "  DETECT objeto   -> el robot busca el objeto con la camara\n"
    "  STOP            -> detiene el robot\n"
    "  END             -> fin del plan\n"
    "Reglas:\n"
    "1. Responde solo con acciones, una por linea, sin numeracion ni explicaciones.\n"
    "2. Termina siempre con END.\n"
    "3. Si la instruccion esta fuera de las capacidades, responde: SPEAK <razon breve> seguido de END.\n"
    "4. Si te preguntan que puedes hacer, responde con SPEAK describiendo tus capacidades, luego END.\n"
    "5. Para instrucciones compuestas como \'ve al refri y luego a la mesa\', genera multiples NAVIGATE.\n"
    "Ejemplos:\n"
    "Instruccion: ve al refri\n"
    "NAVIGATE refrigerator\n"
    "SPEAK Llegue al refrigerador.\n"
    "END\n"
    "Instruccion: robot vuela\n"
    "SPEAK No puedo volar.\n"
    "END\n"
    "Instruccion: dime que puedes hacer\n"
    "SPEAK Puedo navegar a lugares, detectar objetos con la camara y hablar. No puedo manipular objetos ni volar.\n"
    "END\n"
    "Instruccion: busca una bebida en la cocina\n"
    "NAVIGATE kitchen\n"
    "DETECT bebida\n"
    "SPEAK Busque una bebida en la cocina.\n"
    "END"
)

OLLAMA_URL   = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "llama3.2:3b"

# Timeout de navegacion: numero de ciclos de 0.05s antes de continuar (2400 = 120 segundos)
NAV_TIMEOUT_CYCLES = 2400


class SmPlannerNode(Node):

    def __init__(self):
        super().__init__("sm_planner_node")
        self.get_logger().info("INICIANDO SM PLANNER NODE")
        self.state        = SM_WAIT_FOR_COMMAND
        self.command      = ""
        self.new_command  = False
        self.plan         = []
        self.plan_index   = 0
        self.goal_reached = False
        self.nav_timeout  = 0   # FIX: contador de timeout de navegacion

        # FIX: historial inicializado con el prompt del sistema
        self.msg_history = [
            {"role": "user",      "content": SYSTEM_PROMPT},
            {"role": "assistant", "content": "Entendido."},
        ]

        self.pub_goal    = self.create_publisher(PoseStamped, "/goal_pose", 1)
        self.pub_tts     = self.create_publisher(String,      "/tts_query", 1)
        self.pub_cmd_vel = self.create_publisher(Twist,       "/cmd_vel",   1)
        self.create_subscription(String, "/sp_rec/recognized",       self._cb_recognized,   1)
        self.create_subscription(Bool,   "/navigation/goal_reached", self._cb_goal_reached, 1)
        self.create_subscription(String, "/yolo/detections",         self._cb_yolo,         1)
        self.yolo_detections = []
        self.get_logger().info("Esperando instruccion en /sp_rec/recognized ...")

    # Frases de ruido que Whisper genera con silencio o audio del TTS
    NOISE_FILTERS = [
        "amara", "subtítulos", "subtitulos", "transcripción",
        "transcripcion", "comunidad", "gracias por ver",
    ]

    def _cb_recognized(self, msg):
        if self.state == SM_WAIT_FOR_COMMAND:
            text = msg.data.strip().lower()
            # Filtrar ruido de Whisper
            if any(noise in text for noise in self.NOISE_FILTERS):
                self.get_logger().warn(f"Texto filtrado como ruido: '{text}'")
                return
            if len(text) < 3:
                return
            self.command     = text
            self.new_command = True
            self.get_logger().info(f"Instruccion recibida: {self.command}")

    def _cb_goal_reached(self, msg):
        if msg.data:
            self.goal_reached = True
            self.get_logger().info("Meta alcanzada.")

    def _cb_yolo(self, msg):
        try:
            self.yolo_detections = json.loads(msg.data)
        except Exception:
            self.yolo_detections = []

    def _publish_goal(self, location_key):
        loc = LOCATIONS.get(location_key)
        if loc is None:
            self.get_logger().warn(f"Lugar desconocido: {location_key}")
            return False
        msg = PoseStamped()
        msg.header.frame_id    = "map"
        msg.header.stamp       = self.get_clock().now().to_msg()
        msg.pose.position.x    = loc["x"]
        msg.pose.position.y    = loc["y"]
        msg.pose.position.z    = 0.0
        msg.pose.orientation.w = loc["w"]
        self.pub_goal.publish(msg)
        self.get_logger().info(f"Meta publicada: {location_key} ({loc['x']}, {loc['y']})")
        return True

    def _speak(self, text):
        import time
        self._last_tts_time = time.time()
        self.pub_tts.publish(String(data=text))
        self.get_logger().info(f"TTS: {text}")

    def _sleep(self, seconds):
        steps = int(seconds / 0.05)
        for _ in range(steps):
            rclpy.spin_once(self, timeout_sec=0)
            self.get_clock().sleep_for(Duration(seconds=0.05))

    def _rule_based_interpret(self, cmd):
        for word, response in IMPOSSIBLE.items():
            if word in cmd:
                return [("SPEAK", response), ("END", "")]
        words = cmd.replace(",", " ").replace("y luego", " ").replace("despues", " ").replace("luego", " ").split()
        found_locations = []
        for w in words:
            key = SYNONYMS.get(w)
            if key and (not found_locations or found_locations[-1] != key):
                found_locations.append(key)
        if found_locations:
            plan = [("NAVIGATE", loc) for loc in found_locations]
            plan.append(("SPEAK", "Tarea terminada."))
            plan.append(("END", ""))
            return plan
        if any(w in cmd for w in ["alto", "detente", "para", "stop"]):
            return [("STOP", ""), ("END", "")]
        return None

    def _ollama_interpret(self, cmd):
        try:
            self.msg_history.append({"role": "user", "content": cmd})
            resp = requests.post(
                OLLAMA_URL,
                json={
                    "model":    OLLAMA_MODEL,
                    "messages": self.msg_history,
                    "stream":   False,
                    "options":  {"num_ctx": 4096},
                },
                timeout=45,
            )
            resp.raise_for_status()
            reply = resp.json()["message"]["content"].strip()
            self.msg_history.append({"role": "assistant", "content": reply})
            self.get_logger().info(f"Ollama respondio:\n{reply}")
            return self._parse_plan(reply)
        except Exception as e:
            self.get_logger().warn(f"Ollama fallo: {e}")
            return None

    def _parse_plan(self, text):
        plan = []
        for line in text.splitlines():
            line  = line.strip()
            if not line:
                continue
            upper = line.upper()
            if upper.startswith("NAVIGATE"):
                parts = line.split(None, 1)
                if len(parts) == 2:
                    loc = SYNONYMS.get(parts[1].strip().lower(), parts[1].strip().lower())
                    if loc in LOCATIONS:
                        plan.append(("NAVIGATE", loc))
            elif upper.startswith("SPEAK"):
                parts = line.split(None, 1)
                plan.append(("SPEAK", parts[1].strip() if len(parts) == 2 else "Entendido."))
            elif upper.startswith("DETECT"):
                parts = line.split(None, 1)
                plan.append(("DETECT", parts[1].strip() if len(parts) == 2 else "objeto"))
            elif upper == "STOP":
                plan.append(("STOP", ""))
            elif upper == "END":
                plan.append(("END", ""))
                break
        return plan if plan else None

    def _detect_object(self, target):
        """Gira el robot buscando el objeto con YOLO. Maximo 360 grados."""
        self._speak(f"Buscando {target}.")
        self.get_logger().info(f"[DETECT] Buscando objeto: {target}")

        # Mapeo de nombres en espanol a clases YOLO
        YOLO_CLASSES = {
            "silla":        "chair",
            "chair":        "chair",
            "sofa":         "couch",
            "sillon":       "couch",
            "cama":         "bed",
            "bed":          "bed",
            "tele":         "tv",
            "television":   "tv",
            "tv":           "tv",
            "refrigerador": "refrigerator",
            "refri":        "refrigerator",
            "refrigerator": "refrigerator",
            "persona":      "person",
            "person":       "person",
            "bebida":       "bottle",
            "bottle":       "bottle",
            "vaso":         "cup",
            "cup":          "cup",
            "pelota":       "sports ball",
        }
        yolo_class = YOLO_CLASSES.get(target.lower(), target.lower())

        # Girar hasta 360 grados buscando el objeto
        VEL_GIRO  = 0.3   # rad/s
        T_MAX     = (2 * 3.14159) / VEL_GIRO  # ~21 segundos para 360 grados
        t_inicio  = time.time()
        encontrado = False

        twist = Twist()
        twist.angular.z = VEL_GIRO

        while time.time() - t_inicio < T_MAX and rclpy.ok():
            # Revisar detecciones actuales
            for det in self.yolo_detections:
                if det.get("clase") == yolo_class and det.get("conf", 0) > 0.4:
                    encontrado = True
                    break
            if encontrado:
                break
            self.pub_cmd_vel.publish(twist)
            rclpy.spin_once(self, timeout_sec=0)
            self.get_clock().sleep_for(Duration(seconds=0.05))

        # Detener giro
        self.pub_cmd_vel.publish(Twist())

        if encontrado:
            self.get_logger().info(f"[DETECT] Objeto '{target}' encontrado.")
            self._speak(f"Encontre {target}.")
        else:
            self.get_logger().warn(f"[DETECT] Objeto '{target}' no encontrado.")
            self._speak(f"No encontre {target}.")
        self._sleep(2.0)

    def spin(self):
        while rclpy.ok():
            rclpy.spin_once(self, timeout_sec=0)
            self.get_clock().sleep_for(Duration(seconds=0.05))

            if self.state == SM_WAIT_FOR_COMMAND:
                if self.new_command:
                    self.new_command = False
                    self.state = SM_INTERPRET_COMMAND

            elif self.state == SM_INTERPRET_COMMAND:
                self.get_logger().info("Interpretando instruccion...")
                plan = self._rule_based_interpret(self.command)
                if plan is None:
                    self.get_logger().info("Consultando Ollama...")
                    plan = self._ollama_interpret(self.command)
                if plan is None:
                    plan = [("SPEAK", "No entendi la instruccion."), ("END", "")]
                self.plan       = plan
                self.plan_index = 0
                self.get_logger().info(f"Plan: {self.plan}")
                self.state = SM_EXECUTE_PLAN

            elif self.state == SM_EXECUTE_PLAN:
                if self.plan_index >= len(self.plan):
                    self.state = SM_DONE
                    continue
                action, arg = self.plan[self.plan_index]
                self.plan_index += 1
                if action == "NAVIGATE":
                    if self._publish_goal(arg):
                        self.goal_reached = False
                        self.nav_timeout  = 0
                        self.state = SM_WAIT_GOAL_REACHED
                    else:
                        self._speak(f"No conozco el lugar {arg}.")
                elif action == "SPEAK":
                    self._speak(arg)
                    self._sleep(3.0)
                elif action == "DETECT":
                    self._detect_object(arg)
                elif action == "STOP":
                    self._speak("Deteniendome.")
                    self._sleep(1.0)
                elif action == "END":
                    self.state = SM_DONE

            elif self.state == SM_WAIT_GOAL_REACHED:
                # FIX: timeout para que la demo no se cuelgue si el robot se atasca
                if self.goal_reached:
                    self.goal_reached = False
                    self.nav_timeout  = 0
                    self.state = SM_EXECUTE_PLAN
                else:
                    self.nav_timeout += 1
                    if self.nav_timeout > NAV_TIMEOUT_CYCLES:
                        self.get_logger().warn("Timeout de navegacion. Continuando plan.")
                        self.nav_timeout  = 0
                        self.goal_reached = False
                        self.state = SM_EXECUTE_PLAN

            elif self.state == SM_DONE:
                self.get_logger().info("Plan completado. Esperando nueva instruccion.")
                self.plan       = []
                self.plan_index = 0
                self.state      = SM_WAIT_FOR_COMMAND


def main(args=None):
    rclpy.init(args=args)
    node = SmPlannerNode()
    node.spin()
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
