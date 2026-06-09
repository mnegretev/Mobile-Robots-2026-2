#!/usr/bin/env python3
"""Combined test: Move base and arm simultaneously"""

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from builtin_interfaces.msg import Duration
import time
import threading

class CombinedRobotTest(Node):
    def __init__(self):
        super().__init__('combined_robot_test')
        
        # Publishers
        self.base_publisher = self.create_publisher(Twist, '/cmd_vel', 10)
        self.arm_publisher = self.create_publisher(
            JointTrajectory, 
            '/xarm6_traj_controller/joint_trajectory', 
            10
        )
        
        self.get_logger().info('Combined Robot Test Started')
        time.sleep(2)
        
    def move_base(self, distance=1.0, speed=0.3):
        """Move base forward"""
        duration = distance / speed
        msg = Twist()
        msg.linear.x = float(speed)
        
        start_time = time.time()
        while (time.time() - start_time) < duration:
            self.base_publisher.publish(msg)
            time.sleep(0.1)
        
        # Stop
        msg.linear.x = 0.0
        self.base_publisher.publish(msg)
        self.get_logger().info(f'Base movement complete: {distance}m')
        
    def move_arm(self, positions, duration=2.0):
        """Move arm to positions"""
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
        self.arm_publisher.publish(trajectory)
        self.get_logger().info(f'Arm movement sent: {[f"{p:.2f}" for p in positions]}')
        
    def test_scenario_1(self):
        """Scenario 1: Move forward while raising arm"""
        self.get_logger().info('=== SCENARIO 1: Move Forward + Raise Arm ===')
        
        # Move base and arm in parallel
        base_thread = threading.Thread(target=self.move_base, args=(1.0, 0.3))
        arm_thread = threading.Thread(target=self.move_arm, args=([0.0, -1.57, 1.57, 0.0, 0.0, 0.0], 3.0))
        
        base_thread.start()
        arm_thread.start()
        
        base_thread.join()
        arm_thread.join()
        
        time.sleep(1)
        
    def test_scenario_2(self):
        """Scenario 2: Complex sequence"""
        self.get_logger().info('=== SCENARIO 2: Complex Sequence ===')
        
        # Start with arm in UP position
        self.move_arm([0.0, -1.57, 1.57, 0.0, 0.0, 0.0], 2.0)
        time.sleep(0.5)
        
        # Move forward
        self.get_logger().info('Moving forward...')
        self.move_base(1.0, 0.3)
        time.sleep(0.5)
        
        # Rotate arm while moving
        self.get_logger().info('Rotating arm...')
        self.move_arm([1.57, -1.57, 1.57, 0.0, 0.0, 0.0], 2.0)
        time.sleep(0.5)
        
        # Return to home
        self.get_logger().info('Returning to home position...')
        self.move_arm([0.0, 0.0, 0.0, 0.0, 0.0, 0.0], 2.0)

def main(args=None):
    rclpy.init(args=args)
    node = CombinedRobotTest()
    
    try:
        # Test Scenario 1
        node.test_scenario_1()
        time.sleep(2)
        
        # Test Scenario 2
        node.test_scenario_2()
        
        node.get_logger().info('✓ All tests complete!')
        node.destroy_node()
        rclpy.shutdown()
        
    except KeyboardInterrupt:
        node.get_logger().info('Test interrupted')
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
