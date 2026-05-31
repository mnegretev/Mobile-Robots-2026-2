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
        self.create_subscription(Image, '/camera/color/image_raw', self.camera_callback, 10)
        
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
            'refrigerator': (2.0, 1.0),
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
        target_name = request.object_name.lower()
        self.get_logger().info(f"Task Manager solicita buscar: {target_name}")
        
        # Si aún no tenemos imágenes de la cámara
        if self.latest_image is None:
            self.get_logger().error("No hay señal de la cámara.")
            response.success = False
            return response
            
        # Correr YOLO en la última imagen recibida
        results = self.model(self.latest_image, verbose=False)
        
        best_match = None
        best_conf = 0.0
        
        # Buscar el objeto solicitado en los resultados de YOLO
        for box in results[0].boxes:
            class_id = int(box.cls[0])
            class_name = self.model.names[class_id]
            conf = float(box.conf[0])
            
            # Si es el objeto que buscamos y tiene buena confianza
            if class_name == target_name and conf > best_conf:
                best_conf = conf
                best_match = box
                
        if best_match is not None:
            # ¡Lo encontramos! Vamos a calcular la distancia
            x1, y1, x2, y2 = best_match.xyxy[0].tolist()
            pixel_height = y2 - y1
            
            # Cálculo Pinhole
            real_h = self.real_heights.get(target_name, 0.5) # Si no sabemos la altura, asumimos 50cm
            distance = (self.F_Y * real_h) / pixel_height
            
            self.get_logger().info(f"¡{target_name} detectado! Distancia aprox: {distance:.2f} m")
            
            # NOTA: Aquí deberías aplicar trigonometría para sumar la posición 
            # del robot + esta distancia. Por ahora, regresaremos la distancia directa en X
            # asumiendo que el robot mira al frente.
            
            pose = PoseStamped()
            pose.header.frame_id = "map"
            pose.pose.position.x = distance 
            pose.pose.position.y = 0.0 # Aproximación
            pose.pose.orientation.w = 1.0
            
            response.pose = pose
            response.success = True
            return response
            
        else:
            self.get_logger().warn(f"No veo '{target_name}'. Usando PLAN B (Posición Predeterminada).")
            # PLAN B
            if target_name in self.fallback_positions:
                x, y = self.fallback_positions[target_name]
                pose = PoseStamped()
                pose.header.frame_id = "map"
                pose.pose.position.x = float(x)
                pose.pose.position.y = float(y)
                pose.pose.orientation.w = 1.0
                
                response.pose = pose
                response.success = True
                return response
                
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