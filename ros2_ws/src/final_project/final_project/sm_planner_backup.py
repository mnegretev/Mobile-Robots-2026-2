import rclpy
from rclpy.node import Node
from rclpy.duration import Duration
from std_msgs.msg import String, Bool
from geometry_msgs.msg import PoseStamped
import requests

SM_WAIT_FOR_COMMAND  = 0
SM_INTERPRET_COMMAND = 10
SM_EXECUTE_PLAN      = 20
SM_WAIT_GOAL_REACHED = 40
SM_DONE              = 80

LOCATIONS = {
    "home":         {"x":  0.0,  "y":  0.0,  "w": 1.0},
    "refrigerator": {"x":  3.5,  "y":  2.5,  "w": 1.0},
    "kitchen":      {"x":  3.0,  "y":  1.0,  "w": 1.0},
    "table":        {"x":  1.5,  "y": -1.0,  "w": 1.0},
    "sofa":         {"x": -2.0,  "y":  1.5,  "w": 1.0},
    "bed":          {"x": -3.0,  "y": -2.0,  "w": 1.0},
    "tv":           {"x": -1.5,  "y":  2.5,  "w": 1.0},
    "door":         {"x":  0.5,  "y": -3.5,  "w": 1.0},
    "stove":        {"x":  4.0,  "y":  0.5,  "w": 1.0},
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

OLLAMA_URL   = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "llama3"


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
        self.msg_history  = []
        self.pub_goal = self.create_publisher(PoseStamped, "/goal_pose", 1)
        self.pub_tts  = self.create_publisher(String,      "/tts_query", 1)
        self.create_subscription(String, "/sp_rec/recognized", self._cb_recognized, 1)
        self.create_subscription(Bool,   "/navigation/goal_reached", self._cb_goal_reached, 1)
        self.get_logger().info("Esperando instruccion en /sp_rec/recognized ...")

    def _cb_recognized(self, msg):
        if self.state == SM_WAIT_FOR_COMMAND:
            self.command     = msg.data.strip().lower()
            self.new_command = True
            self.get_logger().info(f"Instruccion recibida: {self.command}")

    def _cb_goal_reached(self, msg):
        if msg.data:
            self.goal_reached = True
            self.get_logger().info("Meta alcanzada.")

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
        self.get_logger().info(f"Meta publicada: {location_key} ({loc[chr(120)]}, {loc[chr(121)]})")
        return True

    def _speak(self, text):
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
            resp = requests.post(OLLAMA_URL, json={"model": OLLAMA_MODEL, "messages": self.msg_history, "stream": False, "options": {"num_ctx": 4096}}, timeout=15)
            resp.raise_for_status()
            reply = resp.json()["message"]["content"].strip()
            self.msg_history.append({"role": "assistant", "content": reply})
            self.get_logger().info(f"Ollama respondio: {reply}")
            return self._parse_plan(reply)
        except Exception as e:
            self.get_logger().warn(f"Ollama fallo: {e}")
            return None

    def _parse_plan(self, text):
        plan = []
        for line in text.splitlines():
            line = line.strip()
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
                        self.state = SM_WAIT_GOAL_REACHED
                    else:
                        self._speak(f"No conozco el lugar {arg}.")
                elif action == "SPEAK":
                    self._speak(arg)
                    self._sleep(3.0)
                elif action == "DETECT":
                    self._speak(f"Buscando {arg}.")
                    self._sleep(3.0)
                elif action == "STOP":
                    self._speak("Deteniendome.")
                    self._sleep(1.0)
                elif action == "END":
                    self.state = SM_DONE
            elif self.state == SM_WAIT_GOAL_REACHED:
                if self.goal_reached:
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
