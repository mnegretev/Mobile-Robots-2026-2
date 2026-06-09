#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import requests
import json

class OllamaPlanningNode(Node):
    def __init__(self):
        super().__init__('ollama_planning')
        self.subscription = self.create_subscription(
            String,
            '/llm_query',
            self.callback,
            10)
        self.publisher = self.create_publisher(String, '/llm_response', 10)
        self.get_logger().info('Ollama Planning Node initialized')

    def callback(self, msg):
        prompt = msg.data
        self.get_logger().info(f'Received query: {prompt}')
        
        try:
            response = requests.post(
                'http://localhost:11434/api/generate',
                json={'model': 'tinyllama', 'prompt': prompt, 'stream': False}
            )
            if response.status_code == 200:
                result = response.json()
                response_msg = String()
                response_msg.data = result['response']
                self.publisher.publish(response_msg)
                self.get_logger().info(f'Response: {response_msg.data}')
            else:
                self.get_logger().error(f'Ollama error: {response.status_code}')
        except Exception as e:
            self.get_logger().error(f'Error: {e}')

def main(args=None):
    rclpy.init(args=args)
    node = OllamaPlanningNode()
    rclpy.spin(node)

if __name__ == '__main__':
    main()
