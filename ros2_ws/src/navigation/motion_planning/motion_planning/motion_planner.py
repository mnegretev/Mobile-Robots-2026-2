#
# MOBILE ROBOTS - FI-UNAM, 2026-2
# VOICE TO PATH PLANNING BRIDGE
#

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped
from std_msgs.msg import String  

FULL_NAME = "Oscar Saldivar Pantoja"

class MotionPlannerNode(Node):
    def __init__(self):
        print("INITIALIZING MOTION PLANNER BRIDGE - ", FULL_NAME)
        super().__init__("motion_planner_node")
        
        # Publicador de metas directo hacia el suscriptor oficial de tu Pure Pursuit (/goal_pose)
        self.pub_goal = self.create_publisher(PoseStamped, '/goal_pose', 1)
        
        # Suscriptor al puente del micrófono asíncrono
        self.sub_voice = self.create_subscription(String, 'voice_commands', self.callback_voice, 10)
        
        # Diccionario con las coordenadas reales de house_simul
        self.lugares = {
            "gimnasio": {"x": 5.8,  "y": 4.6},
            "comedor":  {"x": 8.1,  "y": 2.0},
            "refri":    {"x": 9.85, "y": 0.4}
        }

    def callback_voice(self, msg):
        comando = msg.data.lower().strip()
        
        if comando in self.lugares:
            self.get_logger().info(f"🎤 Orden de voz recibida: Viajando a {comando.upper()}")
            
            # Construimos la estructura PoseStamped limpia requerida por el callback_goal_pose de Pure Pursuit
            goal_msg = PoseStamped()
            
            # Estampa de tiempo y marco de referencia del mapa global
            goal_msg.header.stamp = self.get_clock().now().to_msg()
            goal_msg.header.frame_id = "map"
            
            # Asignamos las posiciones del mapa
            goal_msg.pose.position.x = self.lugares[comando]["x"]
            goal_msg.pose.position.y = self.lugares[comando]["y"]
            goal_msg.pose.position.z = 0.0
            
            # Orientación neutra reglamentaria (quaternion unitario válido)
            goal_msg.pose.orientation.x = 0.0
            goal_msg.pose.orientation.y = 0.0
            goal_msg.pose.orientation.z = 0.0
            goal_msg.pose.orientation.w = 1.0
            
            # Publicamos la meta sellada para activar la máquina de estados
            self.pub_goal.publish(goal_msg)
            self.get_logger().info(f"🚀 Meta inyectada con éxito en /goal_pose para activar Pure Pursuit.")
            
        elif comando == "stop":
            self.get_logger().warn("⚠️ ¡Orden de detención recibida por voz!")

def main(args=None):
    rclpy.init(args=args)
    node = MotionPlannerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()