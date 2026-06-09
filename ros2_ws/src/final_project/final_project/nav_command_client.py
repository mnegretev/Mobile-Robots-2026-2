#!/usr/bin/env python3
"""
Location-based Navigation Command Interface
Sends navigation commands to sm_planner node via ROS2 topic
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import sys
import time

class NavigationCommandClient(Node):
    """Client to send navigation commands to sm_planner"""
    
    def __init__(self, command):
        super().__init__('nav_command_client')
        
        self.command = command
        self.get_logger().info(f'Navigation Command Client initialized')
        
        # Publisher to send commands to sm_planner
        self.command_publisher = self.create_publisher(
            String,
            '/nav_command',
            10
        )
    
    def send_command(self):
        """Send the navigation command"""
        msg = String()
        msg.data = self.command
        
        self.get_logger().info(f'📍 Sending command: "{self.command}"')
        self.command_publisher.publish(msg)
        time.sleep(0.5)  # Brief delay to ensure message is sent
        self.get_logger().info(f'✓ Command sent to sm_planner')

def print_help():
    """Print usage help"""
    print("""
╔════════════════════════════════════════════════════════════════╗
║        LOCATION-BASED NAVIGATION COMMAND INTERFACE             ║
╚════════════════════════════════════════════════════════════════╝

USAGE:
  python3 nav_command_client.py "go to refrigerador"
  python3 nav_command_client.py "navigate to estufa"
  python3 nav_command_client.py --list           (show all locations)
  python3 nav_command_client.py --help           (this message)

AVAILABLE LOCATIONS:
  • refrigerador - Refrigerador area in the kitchen
  • estufa       - estufa area in the kitchen
  • lavamanos    - lavamanos area in the kitchen
  • mesa cocina  - mesa cocina area
  • gimnasio     - gimnasio area
  • cama         - cama area

EXAMPLE COMMANDS:
  python3 nav_command_client.py "go to refrigerador"
  python3 nav_command_client.py "navigate to estufa"
  python3 nav_command_client.py "move to lavamanos"
  python3 nav_command_client.py "visit mesa cocina"
  python3 nav_command_client.py "head to gimnasio"
  python3 nav_command_client.py refrigerador

REQUIREMENTS:
  - sm_planner.py debe estar corriendo en otra terminal
  - Gazebo y Nav2 deben estar inicializados

════════════════════════════════════════════════════════════════
    """)

def main(args=None):
    rclpy.init(args=args)
    
    if not sys.argv[1:]:
        print_help()
        rclpy.shutdown()
        return
    
    command_arg = sys.argv[1]
    
    if command_arg in ['--help', '-h', 'help']:
        print_help()
        rclpy.shutdown()
        return
    
    elif command_arg in ['--list', '-l', 'list']:
        print('Available locations:')
        locations = [
            'refrigerador', 'estufa', 'lavamanos', 'mesa cocina', 
            'gimnasio', 'cama'
        ]
        for loc in locations:
            print(f'  - {loc}')
        rclpy.shutdown()
        return
    
    # Process navigation command
    if command_arg.startswith('go to ') or command_arg.startswith('navigate to ') or \
       command_arg.startswith('move to ') or command_arg.startswith('visit ') or \
       command_arg.startswith('head to '):
        command = command_arg
    else:
        # Assume it's a location name
        command = f'go to {command_arg}'
    
    # Create client and send command
    node = NavigationCommandClient(command)
    node.send_command()
    
    node.destroy_node()
    if rclpy.ok():   
            rclpy.shutdown()
if __name__ == '__main__':
    main()
