#
# MOBILE ROBOTS - FI-UNAM, 2026-2
# THE PLATFORM ROS 
#
# Instructions:
# Write a program to move the robot forwards until the laser
# detects an obstacle in front of it.
# Also, publish a point stamped with fixed coordinates
# Required publishers and subscribers are already declared and initialized.

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist, PointStamped
from sensor_msgs.msg import LaserScan
from std_msgs.msg import String  # Importación para recibir los comandos de voz

FULL_NAME = "Oscar Saldivar Pantoja"

class RosBasicsNode(Node):
    def __init__(self):
        print("INITIALIZING ROS BASICS NODE - ", FULL_NAME)
        super().__init__("ros_basics_node")
        
        # Publicadores y suscriptores de la plantilla original
        self.pub_cmd_vel = self.create_publisher(Twist, '/cmd_vel', 1)
        self.pub_point   = self.create_publisher(PointStamped, '/testing_point', 1)
        self.sub_scan    = self.create_subscription(LaserScan, '/scan', self.callback_scan, 1)
        
        # --- NUEVAS CONFIGURACIONES PARA CONTROL POR VOZ ---
        # Suscriptor al nodo de voz que creaste (voice_navigation_bridge)
        self.sub_voice   = self.create_subscription(String, 'voice_commands', self.callback_voice, 10)
        
        # Diccionario con las coordenadas reales obtenidas de tu simulación
        self.lugares = {
            "gimnasio": {"x": 5.8,  "y": 4.6},
            "comedor":  {"x": 8.1,  "y": 2.0},
            "refri":    {"x": 9.85, "y": 0.4}
        }
        
        # Variables de control de navegación
        self.target_x = None
        self.target_y = None
        
        # Timer original
        self.timer = self.create_timer(0.1, self.callback_timer)
        self.obstacle_detected = False

    def callback_voice(self, msg):
        """ Recibe el comando de voz y actualiza el objetivo del robot """
        comando = msg.data.lower()
        
        if comando in self.lugares:
            self.get_logger().info(f"🎤 Orden de voz recibida: Viajando a {comando.upper()}")
            self.target_x = self.lugares[comando]["x"]
            self.target_y = self.lugares[comando]["y"]
        elif comando == "stop":
            self.get_logger().warn("⚠️ ¡Orden de detención recibida por voz!")
            # Cancelamos el objetivo para detener la marcha
            self.target_x = None
            self.target_y = None

    def callback_timer(self):
        # Declaramos un mensaje Twist (por defecto todos sus campos inician en 0.0)
        twist_msg = Twist()
        
        # Si no hay una orden de destino activa por voz, el robot se queda quieto
        if self.target_x is None or self.target_y is None:
            self.pub_cmd_vel.publish(twist_msg)
            return

        # Evaluamos el estado del obstáculo según las lecturas del láser
        if self.obstacle_detected:
            self.get_logger().warn("Obstáculo detectado al frente. Frenando por seguridad.")
            twist_msg.linear.x = 0.0
            twist_msg.angular.z = 0.0
        else:
            # Si el camino está libre y tenemos un destino, avanzamos al frente
            # Nota: Aquí es donde posteriormente implementarás el cálculo matemático de orientación
            twist_msg.linear.x = 0.2  
            twist_msg.angular.z = 0.0

        # Publicamos la velocidad calculada al robot
        self.pub_cmd_vel.publish(twist_msg)

        # Requisito de la práctica: Publicar el punto estampado con coordenadas fijas (1,0)
        point_msg = PointStamped()
        point_msg.header.stamp = self.get_clock().now().to_msg()
        point_msg.header.frame_id = "map"
        point_msg.point.x = 1.0
        point_msg.point.y = 0.0
        point_msg.point.z = 0.0
        self.pub_point.publish(point_msg)

    def callback_scan(self, msg):
        # Buscamos el centro del arreglo del láser (representa el frente del robot)
        centro = len(msg.ranges) // 2
        
        # Tomamos una pequeña ventana de lecturas centrales para evitar falsos positivos (+-15 grados)
        lecturas_frente = msg.ranges[centro-15 : centro+15]
        
        # Umbral de distancia segura de frenado (en metros)
        distancia_segura = 0.6 
        
        self.obstacle_detected = False
        
        # Analizamos las lecturas del frente
        for distancia in lecturas_frente:
            # Descartamos lecturas fuera de rango o ruidos numéricos
            if msg.range_min < distancia < distancia_segura:
                self.obstacle_detected = True
                break


def main(args=None):
    rclpy.init(args=args)
    ros_basics_node = RosBasicsNode()
    rclpy.spin(ros_basics_node)
    ros_basics_node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()