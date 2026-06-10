#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import String
from geometry_msgs.msg import Twist
from cv_bridge import CvBridge
from ultralytics import YOLO
import os
from ament_index_python.packages import get_package_share_directory

class YoloController(Node):
    def __init__(self):
        super().__init__('yolo_controller')
        self.br = CvBridge()
        # Cargar modelo  YOLO
        model_path = os.path.join(get_package_share_directory("neural_networks"), "models", "yolov8n.pt")
        self.model = YOLO(model_path)
        self.model.to('cpu')
        self.get_logger().info("Modelo YOLO cargado")

        # Variables de estado
        self.target_object = None
        self.last_detection_time = self.get_clock().now().seconds_nanoseconds()[0]

        # Suscripciones
        self.sub_img = self.create_subscription(Image, '/camera/image_raw', self.image_callback, 1)
        self.sub_voice = self.create_subscription(String, '/sp_rec/recognized', self.voice_callback, 10)

        # Publicadores
        self.pub_cmd = self.create_publisher(Twist, '/cmd_vel', 10)
        self.pub_tts = self.create_publisher(String, '/tts_query', 10)

        # Timer para timeout
        self.create_timer(0.5, self.check_timeout)

    def voice_callback(self, msg):
        command = msg.data.lower().strip()
        self.get_logger().info(f"Comando de voz: '{command}'")
        # Extraer el objeto (por ejemplo, última palabra)
        words = command.split()
        if words:
            target = words[-1]
            self.target_object = target
            self.get_logger().info(f"Objetivo actual: {self.target_object}")
            # Anunciar por voz
            tts_msg = String()
            tts_msg.data = f"Buscando {target}"
            self.pub_tts.publish(tts_msg)
            self.last_detection_time = self.get_clock().now().seconds_nanoseconds()[0]

    def image_callback(self, msg):
        if self.target_object is None:
            # No hay objetivo, robot quieto
            self.move_robot(0.0, 0.0)
            return

        # Convertir imagen a OpenCV
        cv_image = self.br.imgmsg_to_cv2(msg, 'bgr8')
        results = self.model(cv_image, verbose=False)
        found = False
        best_center_x = None
        best_conf = 0.0
        img_width = msg.width

        for r in results:
            if r.boxes is not None:
                for box in r.boxes:
                    cls_id = int(box.cls[0])
                    label = self.model.names[cls_id]
                    conf = float(box.conf[0])
                    if label.lower() == self.target_object.lower() and conf > 0.5:
                        found = True
                        x1, y1, x2, y2 = box.xyxy[0]
                        center_x = (x1 + x2) / 2
                        if conf > best_conf:
                            best_conf = conf
                            best_center_x = center_x

        if found and best_center_x is not None:
            error = best_center_x - (img_width / 2)
            angular = -error / 300.0      # Ajusta sensibilidad
            linear = 0.2 if abs(error) < 50 else 0.0
            self.move_robot(linear, angular)
            self.last_detection_time = self.get_clock().now().seconds_nanoseconds()[0]
        else:
            # No ve el objeto: gira para buscarlo
            self.move_robot(0.0, 0.5)

    def move_robot(self, linear_x, angular_z):
        cmd = Twist()
        cmd.linear.x = linear_x
        cmd.angular.z = angular_z
        self.pub_cmd.publish(cmd)

    def check_timeout(self):
        if self.target_object is not None:
            now = self.get_clock().now().seconds_nanoseconds()[0]
            if now - self.last_detection_time > 5.0:  # 5 segundos sin verlo
                self.get_logger().info(f"Timeout: no se ve '{self.target_object}'")
                tts_msg = String()
                tts_msg.data = f"No encuentro {self.target_object}"
                self.pub_tts.publish(tts_msg)
                self.target_object = None
                self.move_robot(0.0, 0.0)

def main(args=None):
    rclpy.init(args=args)
    node = YoloController()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
