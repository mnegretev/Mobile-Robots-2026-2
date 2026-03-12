#
# MOBILE ROBOTS - FI-UNAM, 2026-2
# THE PLATFORM ROS 
#
# Instructions:
# Write a program to move the robot forwards until the laser
# detects an obstacle in front of it.
# Also, publish a point stamped with fixed coordinates
# Required publishers and subscribers are already declared and initialized.

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist, PointStamped
from sensor_msgs.msg import LaserScan

FULL_NAME = "FULL NAME"

class RosBasicsNode(Node):
    def __init__(self):
        print("INITIALIZING ROS BASICS NODE - ", FULL_NAME)
        super().__init__("ros_basics_node")
        self.pub_cmd_vel = self.create_publisher(Twist, '/cmd_vel', 1)
        self.pub_point   = self.create_publisher(PointStamped, '/testing_point', 1)
        self.sub_scan = self.create_subscription(LaserScan, '/scan', self.callback_scan, 1)
        self.timer = self.create_timer(0.1, self.callback_timer)
        self.obstacle_detected = False

    def callback_timer(self):
        #
        # TODO:
        # Declare a Twist message and assign the appropiate speeds:
        # Move forward if there is no obstacle in front of the robot, and stop otherwise.
        # Use the 'obstacle_detected' variable to check if there is an obstacle. 
        # Publish the Twist message using the already declared publisher 'pub_cmd_vel'.
        # Publish a point stamped with fixed coordinates (1,0)
        #
        
        return

    def callback_scan(self, msg):
        #
        # TODO:
        # Do something to detect if there is an obstacle in front of the robot.
        # Set the 'obstacle_detected' variable with True or False, accordingly.
        #
        
        return


def main(args=None):
    rclpy.init(args=args)
    ros_basics_node = RosBasicsNode()
    rclpy.spin(ros_basics_node)
    ros_basics_node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
