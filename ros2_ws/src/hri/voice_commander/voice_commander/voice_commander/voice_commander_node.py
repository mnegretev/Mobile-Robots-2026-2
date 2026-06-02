#
# MOBILE ROBOTS - FI-UNAM, 2026-2
#

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from geometry_msgs.msg import PoseStamped
import math

NAME = ""

LOCATIONS = {

    "refrigerador":       ( 9.97, 0.34, 0.0),
    "estufa":             ( 10.29, -1.22, 0.0),
    "mesa":               ( 8.11, 2.73, 0.0),

    "sofa":               ( 2.68, 0.77, 0.0),
    "television":         ( 3.62, -2.83, 0.0),
    "tele":               ( 3.62, -2.83, 0.0),
    "mesa de centro":     ( 3.81, 0.75, 0.0),

    "cama":               (-2.20,  2.48, 0.0),
    "buro":               (-1.88,  3.58, 0.0),
    "ropero":             (-1.76,  3.73, 0.0),
    "escritorio":         (-6.11,  2.93, 0.0),

    "pesas":              ( 3.71,  3.74, 0.0),

}

MOVE_KEYWORDS = ["ve", "ve a", "ir a", "navega", "navega a", "muévete",
                 "muevete", "dirígete", "dirigete", "go to", "move to"]


def normalize(text: str) -> str:
    """Convierte a minúsculas y elimina puntuación básica."""
    return (text.lower()
               .replace(",", "")
               .replace(".", "")
               .replace("¡", "")
               .replace("!", "")
               .replace("¿", "")
               .replace("?", ""))


def find_location(text: str):
    """
    Busca en el texto transcrito si coincide con alguna ubicación conocida.
    Devuelve (nombre, x, y, yaw) o None si no encuentra nada.
    """
    text_norm = normalize(text)
    
    for keyword in sorted(LOCATIONS.keys(), key=len, reverse=True):
        if keyword in text_norm:
            x, y, yaw = LOCATIONS[keyword]
            return keyword, x, y, yaw
    return None


class VoiceCommanderNode(Node):
    def __init__(self):
        super().__init__("voice_commander_node")
        self.get_logger().info("INITIALIZING VOICE COMMANDER NODE - " + NAME)

        self.pub_goal = self.create_publisher(PoseStamped, "/goal_pose", 1)
        self.pub_tts  = self.create_publisher(String, "/tts_query", 1)

        self.sub_recognized = self.create_subscription(
            String,
            "/sp_rec/recognized",
            self.callback_recognized,
            10
        )
        self.get_logger().info("Escuchando comandos de voz en /sp_rec/recognized ...")

    def callback_recognized(self, msg: String):
        text = msg.data
        self.get_logger().info(f"Texto reconocido: '{text}'")

        result = find_location(text)
        if result is None:
            self.get_logger().warn("No se encontró una ubicación conocida en el comando.")
            self.speak("No entendí a dónde quieres que vaya.")
            return

        location_name, x, y, yaw = result
        self.get_logger().info(
            f"Ubicación detectada: '{location_name}' -> x={x:.2f}, y={y:.2f}"
        )
        self.send_goal(x, y, yaw)
        self.speak(f"Voy al {location_name}.")

    def send_goal(self, x: float, y: float, yaw: float):
        """Publica el goal en /goal_pose."""
        goal = PoseStamped()
        goal.header.frame_id = "map"
        goal.header.stamp = self.get_clock().now().to_msg()
        goal.pose.position.x = x
        goal.pose.position.y = y
        goal.pose.position.z = 0.0

        goal.pose.orientation.x = 0.0
        goal.pose.orientation.y = 0.0
        goal.pose.orientation.z = math.sin(yaw / 2.0)
        goal.pose.orientation.w = math.cos(yaw / 2.0)

        self.pub_goal.publish(goal)
        self.get_logger().info(
            f"Goal publicado: ({x:.2f}, {y:.2f}, yaw={math.degrees(yaw):.1f}°)"
        )

    def speak(self, text: str):
        """Publica texto en /tts_query para que PiperTTS lo vocalice."""
        self.pub_tts.publish(String(data=text))


def main(args=None):
    rclpy.init(args=args)
    node = VoiceCommanderNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
