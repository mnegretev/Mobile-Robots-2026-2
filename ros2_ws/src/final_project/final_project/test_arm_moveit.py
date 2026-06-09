#!/usr/bin/env python3
"""Test arm movement using MoveIt (advanced)"""

import rclpy
from rclpy.node import Node
from moveit_msgs.srv import GetPositionIK
from geometry_msgs.msg import Pose, Point, Quaternion
import math
import time

class ArmMoveItTest(Node):
    def __init__(self):
        super().__init__('arm_moveit_test')
        self.get_logger().info('MoveIt Arm Test Node Started')
        self.get_logger().info('Waiting for MoveIt services...')
        time.sleep(3)
        
    def test_ik(self):
        """Test inverse kinematics"""
        self.get_logger().info('=== Testing Inverse Kinematics ===')
        
        # Create a pose request
        pose = Pose()
        pose.position = Point(x=0.3, y=0.0, z=0.5)
        pose.orientation = Quaternion(x=0.0, y=0.0, z=0.0, w=1.0)
        
        self.get_logger().info(f'Target pose: x={pose.position.x}, y={pose.position.y}, z={pose.position.z}')
        self.get_logger().info('Note: MoveIt IK services need to be running separately')

def main(args=None):
    rclpy.init(args=args)
    node = ArmMoveItTest()
    
    try:
        node.test_ik()
        node.destroy_node()
        rclpy.shutdown()
    except KeyboardInterrupt:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
