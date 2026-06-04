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

NAME = "DOMINGUEZ PALACIOS JESUS ALEJANDRO y JONATHAN"

class YoloNode(Node):
    def callback_img(self, msg):
        img_bgr = self.br.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        if img_bgr is None or not hasattr(img_bgr, 'shape'):
            self.get_logger().warn("Received empty or invalid image frame")
            return
        h, w = img_bgr.shape[:2]
        results = self.model(img_bgr, verbose=False)
        idxs = results[0].boxes.cls.cpu().tolist()
        confs = results[0].boxes.conf.cpu().tolist()
        bboxes = results[0].boxes.xywh.cpu().tolist()
        names = results[0].names

        # Construir lista de detecciones para publicar
        detecciones = []
        for i in range(len(idxs)):
            clase = names[int(idxs[i])]
            conf = confs[i]
            cx, cy, bw, bh = bboxes[i]
            # Posicion horizontal normalizada: -1 (izq) a +1 (der), 0 = centro
            cx_norm = (cx - w/2.0) / (w/2.0)
            # Tamano relativo del objeto (que tan grande se ve = que tan cerca)
            area_rel = (bw * bh) / (w * h)
            if conf > 0.4:  # solo detecciones confiables
                detecciones.append({
                    "clase": clase,
                    "conf": round(conf, 2),
                    "cx_norm": round(cx_norm, 3),
                    "area_rel": round(area_rel, 3)
                })

        # Publicar las detecciones como JSON
        msg_out = String()
        msg_out.data = json.dumps(detecciones)
        self.pub_det.publish(msg_out)

        # Mostrar ventana con anotaciones
        annotated_frame = results[0].plot()
        cv2.imshow("YOLO Detection", annotated_frame)
        cv2.waitKey(1)

    def __init__(self):
        print("INITIALIZING YOLO NODE - " + NAME)
        super().__init__("yolo_node")
        self.br = CvBridge()
        model_path = os.path.join(get_package_share_directory("neural_networks"), "models", "yolov8n.pt")
        self.declare_parameter('model_path', model_path)
        print(f'Initializing yolo model from path :{model_path}')
        self.model = YOLO(model_path)
        self.model.to('cpu')
        print("Model initialized succesfully")
        self.sub_img = self.create_subscription(Image, '/front_camera/image_raw', self.callback_img, 1)
        self.pub_det = self.create_publisher(String, '/yolo/detections', 1)

def main(args=None):
    rclpy.init(args=args)
    yolo_node = YoloNode()
    rclpy.spin(yolo_node)
    yolo_node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
