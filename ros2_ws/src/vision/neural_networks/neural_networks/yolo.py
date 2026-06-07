import rclpy
from rclpy.node import Node
from ament_index_python.packages import get_package_share_directory
import cv2
from sensor_msgs.msg import Image, JointState
from std_msgs.msg import String
from cv_bridge import CvBridge
import numpy
import os
import json
import torch
from ultralytics import YOLO

NAME = "JESUS ALEXIS PEREZ LEON"

class YoloNode(Node):
    def callback_img(self, msg):
        img_bgr = self.br.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        if img_bgr is None or not hasattr(img_bgr, 'shape'):
            self.get_logger().warn("Received empty or invalid image frame")
            return
        results = self.model(img_bgr, verbose=False)

        idxs = results[0].boxes.cls.cpu().tolist()
        confs = results[0].boxes.conf.cpu().tolist()
        bboxes = results[0].boxes.xywh.cpu().tolist()   # [cx, cy, w, h] en pixeles

        # Arma la lista de detecciones {name, conf, cx, cy, w, h}
        detections = []
        for cls_idx, conf, box in zip(idxs, confs, bboxes):
            name = self.model.names[int(cls_idx)]   # idx de clase -> nombre (COCO)
            cx, cy, w, h = box
            detections.append({
                "name": name,
                "conf": round(float(conf), 3),
                "cx": round(float(cx), 1),
                "cy": round(float(cy), 1),
                "w":  round(float(w), 1),
                "h":  round(float(h), 1),
            })

        # Publica las detecciones como JSON (String) para el sm_planner
        out = String()
        out.data = json.dumps(detections)
        self.pub_det.publish(out)

        if detections:
            self.get_logger().info("Veo: " + ", ".join(d["name"] for d in detections))

        # Ventana de depuracion (igual que antes)
        annotated_frame = results[0].plot()
        cv2.imshow("YOLO Detection", annotated_frame)
        cv2.waitKey(1)

    def __init__(self):
        print("INITIALIZING YOLO NODE - " + NAME)
        super().__init__("yolo_node")
        self.br = CvBridge()
        model_path = os.path.join(get_package_share_directory("neural_networks"), "models", "yolov8n.pt")
        self.declare_parameter('model_path', model_path)
        #model_path  = self.get_parameter('model_path').get_parameter_value().string_value
        print(f'Initializing yolo model from path :{model_path}')
        self.model = YOLO(model_path)
        # Usa GPU si hay; si no, CPU (asi no truena en maquinas sin CUDA)
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.model.to(device)
        print(f"Model initialized succesfully on device: {device}")
        self.sub_img = self.create_subscription(Image, '/camera/color/image_raw', self.callback_img, 1)
        self.pub_det = self.create_publisher(String, '/yolo/detections', 10)

def main(args=None):
    rclpy.init(args=args)
    yolo_node = YoloNode()
    rclpy.spin(yolo_node)
    yolo_node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()