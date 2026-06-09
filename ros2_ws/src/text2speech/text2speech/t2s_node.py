#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

class TTSNode(Node):
    def __init__(self):
        super().__init__('t2s_node')
        self.subscription = self.create_subscription(
            String,
            '/tts_query',
            self.callback,
            10)
        self.get_logger().info('TTS Node initialized')

    def callback(self, msg):
        self.get_logger().info(f'Received: {msg.data}')

def main(args=None):
    rclpy.init(args=args)
    node = TTSNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
