#
# MOBILE ROBOTS - FI-UNAM, 2026-2
# YOLO NODE - con publicacion de detecciones en /yolo/detections
#
import rclpy
from rclpy.node import Node
from ament_index_python.packages import get_package_share_directory
import cv2
import json
from sensor_msgs.msg import Image
from std_msgs.msg import String
from cv_bridge import CvBridge
import numpy
import os
from ultralytics import YOLO

NAME = "Zambrano Miranda Isaac Jaciel"

class YoloNode(Node):

    def callback_img(self, msg):
        img_bgr = self.br.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        if img_bgr is None or not hasattr(img_bgr, 'shape'):
            self.get_logger().warn("Frame invalido recibido")
            return

        results = self.model(img_bgr, verbose=False)
        idxs   = results[0].boxes.cls.cpu().tolist()
        confs  = results[0].boxes.conf.cpu().tolist()
        bboxes = results[0].boxes.xywhn.cpu().tolist()  # normalizado 0-1

        # Construir lista de detecciones
        detections = []
        h, w = img_bgr.shape[:2]
        for i in range(len(idxs)):
            class_id = int(idxs[i])
            clase    = self.model.names[class_id]
            conf     = round(confs[i], 3)
            cx_n, cy_n, bw_n, bh_n = bboxes[i]
            area_rel = bw_n * bh_n
            detections.append({
                "clase":    clase,
                "conf":     conf,
                "cx_norm":  round(cx_n - 0.5, 3),  # centrado en 0: negativo=izq, positivo=der
                "cy_norm":  round(cy_n - 0.5, 3),
                "area_rel": round(area_rel, 4),
            })

        # Publicar como JSON
        self.pub_detections.publish(String(data=json.dumps(detections)))

        # Mostrar ventana con anotaciones
        annotated = results[0].plot()
        cv2.imshow("YOLO Detection", annotated)
        cv2.waitKey(1)

    def __init__(self):
        print("INITIALIZING YOLO NODE - " + NAME)
        super().__init__("yolo_node")
        self.br = CvBridge()

        model_path = os.path.join(
            get_package_share_directory("neural_networks"), "models", "yolov8n.pt"
        )
        self.declare_parameter('model_path', model_path)
        print(f'Cargando modelo YOLO desde: {model_path}')
        self.model = YOLO(model_path)
        self.model.to('cuda')
        print("Modelo inicializado correctamente")

        # Suscriptor a imagen de camara
        self.sub_img = self.create_subscription(
            Image, '/camera/color/image_raw', self.callback_img, 1
        )

        # Publicador de detecciones como JSON
        self.pub_detections = self.create_publisher(String, '/yolo/detections', 1)
        self.get_logger().info("Publicando detecciones en /yolo/detections")


def main(args=None):
    rclpy.init(args=args)
    node = YoloNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
