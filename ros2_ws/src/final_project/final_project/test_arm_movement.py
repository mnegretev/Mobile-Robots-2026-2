#!/usr/bin/env python3
"""Simple test node to move xarm6 robot arm"""

import rclpy
from rclpy.node import Node
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from builtin_interfaces.msg import Duration
import time

class ArmMovementTest(Node):
    def __init__(self):
        super().__init__('arm_movement_test')
        # Publisher for arm trajectory
        self.publisher = self.create_publisher(
            JointTrajectory, 
            '/xarm6_traj_controller/joint_trajectory', 
            10
        )
        self.get_logger().info('Arm Movement Test Node Started')
        time.sleep(2)  # Wait for connections
        self.get_logger().info('Moving arm...')
        
    def move_arm(self, positions, duration=3.0):
        """
        Move arm to specified joint positions
        
        Args:
            positions: List of 6 joint angles in radians
            duration: Time to reach target position (seconds)
        """
        trajectory = JointTrajectory()
        trajectory.joint_names = [
            'joint1', 'joint2', 'joint3', 
            'joint4', 'joint5', 'joint6'
        ]
        
        # Create trajectory point
        point = JointTrajectoryPoint()
        point.positions = positions
        point.velocities = [0.0] * 6
        point.time_from_start = Duration(sec=int(duration), nanosec=int((duration % 1) * 1e9))
        
        trajectory.points.append(point)
        
        self.publisher.publish(trajectory)
        self.get_logger().info(f'Trajectory sent: {positions}')

def main(args=None):
    rclpy.init(args=args)
    node = ArmMovementTest()
    
    try:
        # Home position (all zeros)
        node.get_logger().info('=== Moving to HOME position ===')
        node.move_arm([0.0, 0.0, 0.0, 0.0, 0.0, 0.0], duration=3.0)
        time.sleep(4)
        
        # Raise arm position (bend joints 2 and 3)
        node.get_logger().info('=== Moving to UP position ===')
        node.move_arm([0.0, -1.57, 1.57, 0.0, 0.0, 0.0], duration=3.0)
        time.sleep(4)
        
        # Side position (rotate joint 1)
        node.get_logger().info('=== Moving to SIDE position ===')
        node.move_arm([1.57, -1.57, 1.57, 0.0, 0.0, 0.0], duration=3.0)
        time.sleep(4)
        
        # Return to home
        node.get_logger().info('=== Returning to HOME ===')
        node.move_arm([0.0, 0.0, 0.0, 0.0, 0.0, 0.0], duration=3.0)
        time.sleep(4)
        
        node.get_logger().info('Movement test complete!')
        node.destroy_node()
        rclpy.shutdown()
        
    except KeyboardInterrupt:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
