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

FULL_NAME = "Claudia Eunice Vazquez Rios"

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
                # Create Twist message
        msg_twist = Twist()

        # Move forward if no obstacle
        if self.obstacle_detected:
            msg_twist.linear.x = 0.0
        else:
            msg_twist.linear.x = 0.3

        # Publish velocity
        self.pub_cmd_vel.publish(msg_twist)

        # Create PointStamped message
        msg_point = PointStamped()
        msg_point.header.frame_id = "base_link"
        msg_point.point.x = 1.0
        msg_point.point.y = 0.0
        msg_point.point.z = 0.0

        # Publish point
        self.pub_point.publish(msg_point)

    def callback_scan(self, msg):
        # Detect obstacle in front (valor central del LIDAR)
        self.obstacle_detected = msg.ranges[len(msg.ranges)//2] < 1.0



def main(args=None):
    rclpy.init(args=args)
    ros_basics_node = RosBasicsNode()
    rclpy.spin(ros_basics_node)
    ros_basics_node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
