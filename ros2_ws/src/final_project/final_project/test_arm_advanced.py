#!/usr/bin/env python3
"""Advanced arm movement examples for xarm6"""

import rclpy
from rclpy.node import Node
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from builtin_interfaces.msg import Duration
import time
import math

class AdvancedArmTest(Node):
    def __init__(self):
        super().__init__('advanced_arm_test')
        self.publisher = self.create_publisher(
            JointTrajectory, 
            '/xarm6_traj_controller/joint_trajectory', 
            10
        )
        self.get_logger().info('Advanced Arm Test Started')
        time.sleep(2)
        
    def move_arm(self, positions, duration=2.0, description=""):
        """Move arm to specified joint positions"""
        if description:
            self.get_logger().info(f'=== {description} ===')
        
        trajectory = JointTrajectory()
        trajectory.joint_names = [
            'joint1', 'joint2', 'joint3', 
            'joint4', 'joint5', 'joint6'
        ]
        
        point = JointTrajectoryPoint()
        point.positions = positions
        point.velocities = [0.0] * 6
        point.time_from_start = Duration(sec=int(duration), nanosec=int((duration % 1) * 1e9))
        
        trajectory.points.append(point)
        self.publisher.publish(trajectory)
        time.sleep(duration + 0.5)

def main(args=None):
    rclpy.init(args=args)
    node = AdvancedArmTest()
    
    try:
        # 1. Simple reach forward
        node.move_arm([0.0, -0.5, 0.5, 0.0, 0.0, 0.0], 2.0, "Reach Forward")
        
        # 2. Reach up
        node.move_arm([0.0, -1.57, 1.57, 0.0, 0.0, 0.0], 2.0, "Reach Up")
        
        # 3. Reach left
        node.move_arm([1.57, -1.0, 1.0, 0.0, 0.0, 0.0], 2.0, "Reach Left")
        
        # 4. Reach right
        node.move_arm([-1.57, -1.0, 1.0, 0.0, 0.0, 0.0], 2.0, "Reach Right")
        
        # 5. Rotate wrist (joint 6)
        node.move_arm([0.0, -0.5, 0.5, 0.0, 0.0, 1.57], 2.0, "Rotate Wrist +90°")
        
        # 6. Back to neutral
        node.move_arm([0.0, 0.0, 0.0, 0.0, 0.0, 0.0], 2.0, "Return to Home")
        
        node.get_logger().info('✓ All movements complete!')
        node.destroy_node()
        rclpy.shutdown()
        
    except KeyboardInterrupt:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
