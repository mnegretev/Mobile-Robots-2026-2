#
# MOBILE ROBOTS - FI-UNAM, 2026-2
# FINAL PROJECT - YOLO OBJECT DETECTION PUBLISHER
#
# Companion to vision/neural_networks/yolo.py. The course yolo.py only
# shows an OpenCV window; the orchestrator needs the detections as a
# ROS topic. This node subscribes to the simulator camera and publishes,
# for every frame, the detected objects as a JSON string:
#   [{"label": "remote", "conf": 0.83, "cx": 312.0, "cy": 197.0,
#     "w": 60.0, "h": 24.0, "img_w": 640, "img_h": 480}, ...]
#
# cx, cy are the bounding-box center in pixels (image frame).
#
import json
import os
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import String
from cv_bridge import CvBridge
from ament_index_python.packages import get_package_share_directory
from ultralytics import YOLO

# NOTE: the simulator publishes on /camera/image_raw (see house_simul
# config/gz_bridge.yaml). The original yolo.py used /camera/color/image_raw,
# which does not exist in this sim -> fixed here.
CAMERA_TOPIC = "/camera/image_raw"
DETECTIONS_TOPIC = "/vision/detections"


class YoloDetectorNode(Node):
    def __init__(self):
        super().__init__("yolo_detector_node")
        self.br = CvBridge()
        model_path = os.path.join(
            get_package_share_directory("neural_networks"), "models", "yolov8n.pt")
        self.declare_parameter("model_path", model_path)
        self.declare_parameter("device", "cuda")     # set to "cpu" if no GPU
        self.declare_parameter("conf", 0.4)
        model_path = self.get_parameter("model_path").value
        self.conf = float(self.get_parameter("conf").value)

        self.get_logger().info(f"Loading YOLO model: {model_path}")
        self.model = YOLO(model_path)
        try:
            self.model.to(self.get_parameter("device").value)
        except Exception as e:
            self.get_logger().warn(f"Could not move model to GPU ({e}); using CPU")

        self.pub = self.create_publisher(String, DETECTIONS_TOPIC, 1)
        self.sub = self.create_subscription(Image, CAMERA_TOPIC, self.cb_img, 1)
        self.get_logger().info("YOLO detector ready.")

    def cb_img(self, msg):
        img = self.br.imgmsg_to_cv2(msg, desired_encoding="bgr8")
        if img is None or not hasattr(img, "shape"):
            return
        h, w = img.shape[:2]
        results = self.model(img, verbose=False, conf=self.conf)
        names = results[0].names
        dets = []
        for box in results[0].boxes:
            cls = int(box.cls.item())
            cx, cy, bw, bh = box.xywh[0].cpu().tolist()
            dets.append({
                "label": names[cls],
                "conf": round(float(box.conf.item()), 3),
                "cx": round(cx, 1), "cy": round(cy, 1),
                "w": round(bw, 1), "h": round(bh, 1),
                "img_w": w, "img_h": h,
            })
        self.pub.publish(String(data=json.dumps(dets)))


def main(args=None):
    rclpy.init(args=args)
    node = YoloDetectorNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()