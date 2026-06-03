import rclpy
from rclpy.node import Node

import yaml
import math
import os

from std_msgs.msg import String
from geometry_msgs.msg import PoseStamped
from ament_index_python.packages import get_package_share_directory


class RouteSelector(Node):
    def __init__(self):
        super().__init__('route_selector')

        default_file = os.path.join(
            get_package_share_directory('path_follower'),
            'config',
            'locations.yaml'
        )

        self.declare_parameter('locations_file', default_file)
        locations_file = self.get_parameter('locations_file').value

        with open(locations_file, 'r') as file:
            self.locations = yaml.safe_load(file)['locations']

        self.aliases = {
            'cama': 'cama',
            'cuarto': 'cama',

            'refrigerador': 'refrigerador',
            'refri': 'refrigerador',
            'nevera': 'refrigerador',

            'sillon': 'sillon',
            'sillón': 'sillon',
            'sofa': 'sillon',
            'sofá': 'sillon',

            'pesas': 'pesas',
            'gym': 'pesas',
            'ejercicio': 'pesas',

            'tele': 'tele',
            'tv': 'tele',
            'television': 'tele',
            'televisión': 'tele',

            'pelota': 'pelota',
            'balon': 'pelota',
            'balón': 'pelota',

            'puerta': 'puerta',
            'salida': 'puerta'
        }

        self.goal_pub = self.create_publisher(PoseStamped, '/goal_pose', 10)

        self.command_sub = self.create_subscription(
            String,
            '/route_command',
            self.command_callback,
            10
        )

        self.get_logger().info('Route selector listo.')
        self.get_logger().info(f'Locaciones disponibles: {list(self.locations.keys())}')

    def normalize_command(self, text):
        text = text.lower().strip()

        for alias, location in self.aliases.items():
            if alias in text:
                return location

        return text

    def yaw_to_quaternion(self, yaw):
        qz = math.sin(yaw / 2.0)
        qw = math.cos(yaw / 2.0)
        return qz, qw

    def command_callback(self, msg):
        location_name = self.normalize_command(msg.data)

        if location_name not in self.locations:
            self.get_logger().warn(f'Locación no encontrada: {location_name}')
            self.get_logger().info(f'Locaciones disponibles: {list(self.locations.keys())}')
            return

        location = self.locations[location_name]

        x = float(location['x'])
        y = float(location['y'])
        yaw = float(location['yaw'])

        qz, qw = self.yaw_to_quaternion(yaw)

        goal = PoseStamped()
        goal.header.frame_id = 'map'
        goal.header.stamp = self.get_clock().now().to_msg()

        goal.pose.position.x = x
        goal.pose.position.y = y
        goal.pose.position.z = 0.0

        goal.pose.orientation.x = 0.0
        goal.pose.orientation.y = 0.0
        goal.pose.orientation.z = qz
        goal.pose.orientation.w = qw

        self.goal_pub.publish(goal)

        self.get_logger().info(
            f'Objetivo publicado: {location_name} -> x={x}, y={y}, yaw={yaw}'
        )


def main(args=None):
    rclpy.init(args=args)
    node = RouteSelector()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
