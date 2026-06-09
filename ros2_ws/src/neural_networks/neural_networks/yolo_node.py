#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
from ultralytics import YOLO

class YOLONode(Node):
    def __init__(self):
        super().__init__('yolo_node')
        self.bridge = CvBridge()
        self.get_logger().info('Loading YOLO model...')
        self.model = YOLO('yolov8n.pt')
        self.get_logger().info('YOLO model loaded')
        
        self.subscription = self.create_subscription(
    Image,
    '/camera/image_raw',
    self.callback,
    10)
        self.publisher = self.create_publisher(Image, '/yolo/detections', 10)
        self.get_logger().info('YOLO Node initialized. Waiting for /camera/image_raw...')

    def callback(self, msg):
        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, 'bgr8')
            results = self.model(cv_image)
            annotated = results[0].plot()
            self.publisher.publish(self.bridge.cv2_to_imgmsg(annotated, 'bgr8'))
            cv2.imshow('YOLO Detections', annotated)
            cv2.waitKey(1)
        except Exception as e:
            self.get_logger().error(f'Error in callback: {e}')

def main(args=None):
    rclpy.init(args=args)
    node = YOLONode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
