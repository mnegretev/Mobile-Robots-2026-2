#
# MOBILE ROBOTS - FI-UNAM, 2026-2
#

import requests
import rclpy
from rclpy.node import Node
from rclpy.duration import Duration
from std_msgs.msg import String, Bool
from geometry_msgs.msg import PoseStamped
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
import math
import json

NAME = "Carrazco Mesa. Dominguez Osio. Mercado Alejandre"

LOCATIONS = {
    "refrigerador":   ( 9.97,  0.34, 0.0),
    "estufa":         (10.29, -1.22, 0.0),
    "mesa":           ( 8.11,  2.73, 0.0),
    "sofa":           ( 3.20,  1.28, 0.0),
    "sofá":           ( 3.20,  1.28, 0.0),
    "television":     ( 3.62, -2.83, 0.0),
    "televisión":     ( 3.62, -2.83, 0.0),
    "tele":           ( 3.62, -2.83, 0.0),
    "mesa de centro": ( 3.81,  0.75, 0.0),
    "cama":           (-2.20,  2.48, 0.0),
    "buro":           (-1.74,  2.54, 0.0),
    "buró":           (-1.74,  2.54, 0.0),
    "ropero":         (-1.76,  3.73, 0.0),
    "escritorio":     (-4.91,  1.78, 0.0),
    "pesas":          ( 3.71,  3.74, 0.0),
}

LOCATIONS_LIST = ", ".join(sorted(set(LOCATIONS.keys())))

# Lugares donde tiene sentido recoger objetos
PICKUP_LOCATIONS = ["escritorio", "mesa", "mesa de centro", "estufa", "refrigerador", "buro"]


class OllamaPlanningNode(Node):

    def send_prompt(self, msg):
        self.msg_history.append({"role": "user", "content": msg})
        try:
            resp = requests.post(
                self.url_api,
                json={
                    "model": "qwen2.5:0.5b",
                    "messages": self.msg_history,
                    "stream": False,
                    "options": {"num_ctx": 4096}
                },
                timeout=60
            )
            reply = resp.json()["message"]
            self.msg_history.append(reply)
            return reply["content"]
        except Exception as e:
            self.get_logger().error("Error comunicando con Ollama: " + str(e))
            return ""

    def extract_location(self, text):
        text_low = text.lower()
        for key in sorted(LOCATIONS.keys(), key=len, reverse=True):
            if key in text_low:
                return key
        return None

    def send_goal(self, x, y, yaw=0.0):
        goal = PoseStamped()
        goal.header.frame_id = "map"
        goal.header.stamp = self.get_clock().now().to_msg()
        goal.pose.position.x = x
        goal.pose.position.y = y
        goal.pose.position.z = 0.0
        goal.pose.orientation.z = math.sin(yaw / 2.0)
        goal.pose.orientation.w = math.cos(yaw / 2.0)
        self.pub_goal.publish(goal)

    def move_arm_pickup(self):
        msg = JointTrajectory()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.joint_names = ["joint1", "joint2", "joint3", "joint4", "joint5", "joint6"]
        p = JointTrajectoryPoint()
        p.positions = [0.0, -1.8, 0.0, 0.0, 0.0, 0.0]
        p.time_from_start.sec = 2
        msg.points.append(p)
        self.pub_arm.publish(msg)
        self.get_logger().info("Movimiento de brazo ejecutado.")

    def wait_for_goal_reached(self, timeout_sec=60.0):
        self.goal_reached = False
        elapsed = 0.0
        while not self.goal_reached and elapsed < timeout_sec and rclpy.ok():
            rclpy.spin_once(self, timeout_sec=0)
            self.get_clock().sleep_for(Duration(seconds=0.1))
            elapsed += 0.1
        return self.goal_reached

    def callback_goal_reached(self, msg):
        if msg.data:
            self.goal_reached = True

    def callback_prompt(self, msg):
        if self.new_prompt:
            self.get_logger().info("Ignorando prompt, aún procesando...")
            return
        self.prompt = msg.data
        self.new_prompt = True

    def __init__(self):
        super().__init__("ollama_planning_node")
        self.get_logger().info("INITIALIZING OLLAMA PLANNING NODE - " + NAME)
        self.msg_history = []
        self.url_api = "http://localhost:11434/api/chat"
        self.prompt = ""
        self.new_prompt = False
        self.goal_reached = False

        self.sub_query        = self.create_subscription(String, '/sp_rec/recognized', self.callback_prompt, 1)
        self.sub_goal_reached = self.create_subscription(Bool, '/navigation/goal_reached', self.callback_goal_reached, 1)
        self.pub_tts  = self.create_publisher(String, '/tts_query', 1)
        self.pub_goal = self.create_publisher(PoseStamped, '/goal_pose', 1)
        self.pub_arm  = self.create_publisher(JointTrajectory, '/xarm6_traj_controller/joint_trajectory', 1)

    def spin(self):
        system_prompt = f"""Eres Justina, un robot de servicio móvil en una casa simulada.
Puedes navegar a: {LOCATIONS_LIST}.
Puedes recoger objetos de: {', '.join(PICKUP_LOCATIONS)}.

Responde SIEMPRE con JSON válido y nada más, usando uno de estos formatos:

Para navegar: {{"accion": "navegar", "lugar": "nombre_lugar", "mensaje": "Voy al <lugar>."}}
Para traer objeto: {{"accion": "traer", "lugar": "nombre_lugar", "objeto": "nombre_objeto", "mensaje": "Voy a traer el <objeto> del <lugar>."}}
Para lo que no puedes: {{"accion": "no_puedo", "mensaje": "Lo siento, no puedo hacer eso."}}
Para conversar: {{"accion": "conversar", "mensaje": "tu respuesta"}}"""

        self.get_logger().info("Enviando prompt inicial al LLM...")
        self.send_prompt(system_prompt)
        self.get_logger().info("LLM listo. Esperando comandos de voz...")

        while rclpy.ok():
            if self.new_prompt:
                self.get_logger().info(f"Procesando: '{self.prompt}'")
                traer_keywords = ["tráeme", "traeme", "trae", "recoge", "busca", "ve por"]
                if any(k in self.prompt.lower() for k in traer_keywords):
                    loc = self.extract_location(self.prompt)
                    if loc:
                        x, y, yaw = LOCATIONS[loc]
                        self.pub_tts.publish(String(data=f"Voy a traerte algo del {loc}."))
                        self.send_goal(x, y, yaw)
                        self.wait_for_goal_reached(timeout_sec=90.0)
                        self.move_arm_pickup()
                        for _ in range(30):
                            rclpy.spin_once(self, timeout_sec=0)
                            self.get_clock().sleep_for(Duration(seconds=0.1))
                        self.pub_tts.publish(String(data="Regresando con el objeto."))
                        self.send_goal(0.0, 0.0, 0.0)
                        self.wait_for_goal_reached(timeout_sec=90.0)
                        self.new_prompt = False
                        self.get_logger().info("Esperando nuevo comando...")
                        continue
                        continue
                response_text = self.send_prompt(self.prompt)
                self.get_logger().info(f"Respuesta LLM: {response_text}")

                try:
                    start = response_text.find('{')
                    end   = response_text.rfind('}') + 1
                    data  = json.loads(response_text[start:end])
                    accion  = data.get("accion", "conversar")
                    mensaje = data.get("mensaje", response_text)
                    lugar   = data.get("lugar", "")

                    if accion == "navegar":
                        loc = self.extract_location(lugar)
                        if loc:
                            x, y, yaw = LOCATIONS[loc]
                            self.send_goal(x, y, yaw)
                            self.pub_tts.publish(String(data=mensaje))
                            self.get_logger().info(f"Navegando a {loc} ({x:.2f}, {y:.2f})")
                        else:
                            self.pub_tts.publish(String(data=f"No conozco el lugar {lugar}."))

                    elif accion == "traer":
                        loc = self.extract_location(lugar)
                        if loc:
                            x, y, yaw = LOCATIONS[loc]
                            self.pub_tts.publish(String(data=mensaje))
                            self.get_logger().info(f"Yendo a recoger en {loc}")

                            
                            self.send_goal(x, y, yaw)
                            self.wait_for_goal_reached(timeout_sec=90.0)

                            
                            self.get_logger().info("Recogiendo objeto...")
                            self.move_arm_pickup()
                           
                            for _ in range(30):
                                rclpy.spin_once(self, timeout_sec=0)
                                self.get_clock().sleep_for(Duration(seconds=0.1))

                           
                            self.get_logger().info("Regresando al origen...")
                            self.pub_tts.publish(String(data="Regresando con el objeto."))
                            self.send_goal(0.0, 0.0, 0.0)

                        else:
                            self.pub_tts.publish(String(data=f"No conozco el lugar {lugar}."))

                    elif accion == "no_puedo":
                        self.pub_tts.publish(String(data=mensaje))

                    else:
                        self.pub_tts.publish(String(data=mensaje))

                except (json.JSONDecodeError, ValueError):
                    self.get_logger().warn("Respuesta no es JSON, usando fallback")
                    mensaje = response_text[:100]
                    loc = self.extract_location(self.prompt)
                    if loc:
                        x, y, yaw = LOCATIONS[loc]
                        self.send_goal(x, y, yaw)
                        mensaje = f"Voy al {loc}."
                        self.pub_tts.publish(String(data=mensaje))
                    else:
                        self.pub_tts.publish(String(data=mensaje))

                delay_counter = int(1.9 * len(mensaje) + 20)
                while delay_counter > 0 and rclpy.ok():
                    rclpy.spin_once(self, timeout_sec=0)
                    self.get_clock().sleep_for(Duration(seconds=0.05))
                    delay_counter -= 1

                self.new_prompt = False
                self.get_logger().info("Esperando nuevo comando...")

            rclpy.spin_once(self, timeout_sec=0)
            self.get_clock().sleep_for(Duration(seconds=0.05))


def main(args=None):
    rclpy.init(args=args)
    node = OllamaPlanningNode()
    node.spin()
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
