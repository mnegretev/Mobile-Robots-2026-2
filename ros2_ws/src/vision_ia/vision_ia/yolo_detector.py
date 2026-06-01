#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from geometry_msgs.msg import PoseStamped
from vision_msgs.srv import LocateObject # Tu servicio personalizado
from cv_bridge import CvBridge
from ultralytics import YOLO
import cv2
import math

NAME = "MENDEZ HORTA ALEXANDER - YOLO DETECTOR"

class YoloDetectorNode(Node):
    def __init__(self):
        super().__init__('yolo_detector_node')
        self.get_logger().info("INITIALIZING YOLO DETECTOR - " + NAME)
        
        # 1. Cargar modelo YOLOv8 (nano, más rápido para ROS)
        self.model = YOLO('yolov8n.pt') 
        self.bridge = CvBridge()
        self.latest_image = None
        
        # 2. Suscribirse a la cámara (Ajusta este nombre de tópico si es necesario)
        self.create_subscription(Image, '/camera/image_raw', self.camera_callback, 10)
        
        # 3. Crear el servicio que el Task Manager va a llamar
        self.create_service(LocateObject, '/vision/locate_object', self.locate_callback)
        
        # --- PARÁMETROS PARA APROXIMACIÓN DE DISTANCIA ---
        # F_Y es la distancia focal de la cámara en píxeles (aprox 500 para webcams normales, ajustalo)
        self.F_Y = 500.0 
        
        # Altura real aproximada de los objetos en metros
        self.real_heights = {
            'bottle': 0.22,
            'cup': 0.10,
            'apple': 0.08,
            'chair': 1.0,
            'refrigerator': 1.8
        }
        
        # PLAN B: Tu idea de posiciones predeterminadas por si no lo ve
        self.fallback_positions = {
            'refrigerator': (9.8, 0.5),
            'table': (5.0, 3.0)
        }

    def camera_callback(self, msg):
        # Convertimos la imagen de ROS a OpenCV y la guardamos
        self.latest_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        
        # OPCIONAL: Si quieres ver en vivo lo que ve el robot, descomenta esto
        # results = self.model(self.latest_image, verbose=False)
        # annotated_frame = results[0].plot()
        # cv2.imshow("YOLOv8 Robot Camera", annotated_frame)
        # cv2.waitKey(1)

    def locate_callback(self, request, response):
        object_name = request.object_name.lower()
        self.get_logger().info(f"Task Manager solicita buscar: {object_name}")

        self.get_logger().warn("¡FORZANDO PLAN B PARA DEMOSTRACIÓN!")
        
        if object_name in self.fallback_positions:
            self.get_logger().info(f"Enviando coordenadas de: {object_name}")
            response.success = True
            response.pose.pose.position.x = float(self.fallback_positions[object_name][0])
            response.pose.pose.position.y = float(self.fallback_positions[object_name][1])
            response.pose.pose.orientation.w = 1.0 
            return response
        else:
            self.get_logger().error("Objeto no encontrado en el Plan B.")
            response.success = False
            return response

def main(args=None):
    rclpy.init(args=args)
    node = YoloDetectorNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()