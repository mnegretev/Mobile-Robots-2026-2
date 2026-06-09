#!/usr/bin/env python3
"""
Complete Navigation Demo
Shows how to use the SM Planner to navigate the robot
"""

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from builtin_interfaces.msg import Duration
import time
import math
import sys
sys.path.insert(0, '/home/danielgrioja/Fac_Inge/Mobile-Robots-2026-2/ros2_ws/src/final_project/final_project')

from sm_planner import SMPlanner

class NavigationDemo(Node):
    """Demo of navigation + arm control"""
    
    def __init__(self):
        super().__init__('nav_demo')
        
        # Create SM Planner
        self.planner = SMPlanner()
        
        # Arm publisher
        self.arm_publisher = self.create_publisher(
            JointTrajectory,
            '/xarm6_traj_controller/joint_trajectory',
            10
        )
        
        self.get_logger().info('Navigation Demo Started')
    
    def move_arm(self, positions, duration=2.0):
        """Move arm to position"""
        trajectory = JointTrajectory()
        trajectory.joint_names = ['joint1', 'joint2', 'joint3', 'joint4', 'joint5', 'joint6']
        
        point = JointTrajectoryPoint()
        point.positions = positions
        point.velocities = [0.0] * 6
        point.time_from_start = Duration(sec=int(duration), nanosec=int((duration % 1) * 1e9))
        
        trajectory.points.append(point)
        self.arm_publisher.publish(trajectory)
    
    def scenario_1(self):
        """Scenario 1: Navigate to kitchen and raise arm"""
        self.get_logger().info('=== SCENARIO 1: Go to Kitchen ===')
        
        # Navigate to kitchen
        self.planner.process_command('go to kitchen')
        
        # Wait for navigation
        time.sleep(12)
        
        # Raise arm when arriving
        self.get_logger().info('Raising arm...')
        self.move_arm([0.0, -1.57, 1.57, 0.0, 0.0, 0.0], 2.0)
        time.sleep(3)
    
    def scenario_2(self):
        """Scenario 2: Multi-location visit"""
        self.get_logger().info('=== SCENARIO 2: Tour ===')
        
        locations = ['kitchen', 'living_room', 'bedroom']
        
        for location in locations:
            self.get_logger().info(f'🗺️  Navigating to {location}...')
            self.planner.process_command(f'go to {location}')
            
            # Wait for arrival
            time.sleep(12)
            
            # Lower arm at each location
            self.move_arm([0.0, -0.5, 0.5, 0.0, 0.0, 0.0], 2.0)
            time.sleep(1)
            
            self.get_logger().info(f'✓ Arrived at {location}')
            time.sleep(2)

def main(args=None):
    rclpy.init(args=args)
    demo = NavigationDemo()
    
    try:
        # Run demo
        demo.scenario_1()
        time.sleep(5)
        
        # Optional: Uncomment to run scenario 2
        # demo.scenario_2()
        
        demo.get_logger().info('✓ Demo complete!')
        
    except KeyboardInterrupt:
        demo.get_logger().info('Demo interrupted')
    finally:
        demo.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
