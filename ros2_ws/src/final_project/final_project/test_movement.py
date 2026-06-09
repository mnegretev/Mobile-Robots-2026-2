#!/usr/bin/env python3
"""Simple test node to move robot 1 meter forward"""

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
import time

class RobotMovementTest(Node):
    def __init__(self):
        super().__init__('robot_movement_test')
        self.publisher = self.create_publisher(Twist, '/cmd_vel', 10)
        self.get_logger().info('Robot Movement Test Node Started')
        self.get_logger().info('Moving robot 1 meter forward...')
        
    def move_forward(self, distance, speed):
        """Move robot forward by specified distance at given speed"""
        # Calculate time needed: distance = speed * time
        duration = abs(distance / speed)
        
        msg = Twist()
        msg.linear.x = float(speed)  # Move forward
        msg.linear.y = 0.0
        msg.linear.z = 0.0
        msg.angular.x = 0.0
        msg.angular.y = 0.0
        msg.angular.z = 0.0
        
        # Publish velocity command
        start_time = time.time()
        while (time.time() - start_time) < duration:
            self.publisher.publish(msg)
            time.sleep(0.1)
        
        # Stop the robot
        msg.linear.x = 0.0
        self.publisher.publish(msg)
        self.get_logger().info(f'Movement complete! Moved {distance}m forward.')

    def angular_movement(self, angle, angular_speed):
        """Rotate robot by specified angle at given angular speed"""
        # Calculate time needed: angle = angular_speed * time
        duration = abs(angle / angular_speed)
        
        msg = Twist()
        msg.linear.x = 0.0
        msg.linear.y = 0.0
        msg.linear.z = 0.0
        msg.angular.x = 0.0
        msg.angular.y = 0.0
        msg.angular.z = float(angular_speed)  # Rotate
        
        # Publish velocity command
        start_time = time.time()
        while (time.time() - start_time) < duration:
            self.publisher.publish(msg)
            time.sleep(0.1)
        
        # Stop the robot
        msg.angular.z = 0.0
        self.publisher.publish(msg)
        self.get_logger().info(f'Rotation complete! Rotated {angle} radians.')

def main(args=None):
    rclpy.init(args=args)
    node = RobotMovementTest()
    
    try:
        # Move forward 1 meter
        node.move_forward(distance=1.0, speed=0.3)
        time.sleep(1)
        
        # Optional: Move backward
        node.get_logger().info('Moving robot backward 0.5 meters...')
        node.move_forward(distance=0.5, speed=-0.3)

        # Optional: Rotate 90 degrees        
        node.get_logger().info('Rotating robot 90 degrees...')
        node.angular_movement(angle=1.57, angular_speed=0.5)
        
        node.destroy_node()
        rclpy.shutdown()
    except KeyboardInterrupt:
        pass

if __name__ == '__main__':
    main()
