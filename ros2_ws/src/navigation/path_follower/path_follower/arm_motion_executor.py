import os
import time
import yaml

import rclpy
from rclpy.node import Node

from std_msgs.msg import String, Bool
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from builtin_interfaces.msg import Duration
from ament_index_python.packages import get_package_share_directory


class ArmMotionExecutor(Node):
    def __init__(self):
        super().__init__('arm_motion_executor')

        default_file = os.path.join(
            get_package_share_directory('path_follower'),
            'config',
            'arm_actions.yaml'
        )

        self.declare_parameter('actions_file', default_file)
        self.actions_file = self.get_parameter('actions_file').value

        with open(self.actions_file, 'r') as file:
            data = yaml.safe_load(file)

        self.joint_names = data['joint_names']
        self.poses = data['poses']
        self.actions = data['actions']

        self.pub_trajectory = self.create_publisher(
            JointTrajectory,
            '/xarm6_traj_controller/joint_trajectory',
            10
        )

        self.pub_done = self.create_publisher(
            Bool,
            '/arm_action_done',
            10
        )

        self.sub_command = self.create_subscription(
            String,
            '/arm_command',
            self.command_callback,
            10
        )

        self.busy = False

        self.aliases = {
            'agarrar abajo': 'agarrar_abajo',
            'agarra abajo': 'agarrar_abajo',
            'tomar abajo': 'agarrar_abajo',
            'objeto abajo': 'agarrar_abajo',

            'agarrar medio': 'agarrar_medio',
            'agarra medio': 'agarrar_medio',
            'tomar medio': 'agarrar_medio',
            'objeto medio': 'agarrar_medio',
            'agarrar enfrente': 'agarrar_medio',
            'agarra enfrente': 'agarrar_medio',

            'agarrar arriba': 'agarrar_arriba',
            'agarra arriba': 'agarrar_arriba',
            'tomar arriba': 'agarrar_arriba',
            'objeto arriba': 'agarrar_arriba',

            'saludar': 'saludar',
            'saluda': 'saludar',
            'di hola': 'saludar',
            'hola': 'saludar'
        }

        self.get_logger().info('Arm motion executor listo.')
        self.get_logger().info(f'Acciones disponibles: {list(self.actions.keys())}')

    def normalize_command(self, text):
        text = text.lower().strip()

        if text in self.actions:
            return text

        for alias, action in self.aliases.items():
            if alias in text:
                return action

        return text

    def command_callback(self, msg):
        if self.busy:
            self.get_logger().warn('El brazo ya está ejecutando una acción.')
            return

        action_name = self.normalize_command(msg.data)

        if action_name not in self.actions:
            self.get_logger().warn(f'Acción no encontrada: {action_name}')
            self.get_logger().info(f'Acciones disponibles: {list(self.actions.keys())}')
            return

        self.execute_action(action_name)

    def execute_action(self, action_name):
        self.busy = True

        trajectory = JointTrajectory()
        trajectory.joint_names = self.joint_names

        accumulated_time = 0.0

        for step in self.actions[action_name]:
            pose_name = step['pose']
            duration = float(step['duration'])

            if pose_name not in self.poses:
                self.get_logger().error(f'Pose no encontrada: {pose_name}')
                self.busy = False
                return

            accumulated_time += duration

            point = JointTrajectoryPoint()
            point.positions = [float(q) for q in self.poses[pose_name]['joints']]
            point.time_from_start = self.seconds_to_duration(accumulated_time)

            trajectory.points.append(point)

        self.pub_trajectory.publish(trajectory)

        self.get_logger().info(f'Ejecutando acción del brazo: {action_name}')
        self.get_logger().info(f'Duración total aproximada: {accumulated_time:.2f} s')

        time.sleep(accumulated_time + 0.5)

        self.pub_done.publish(Bool(data=True))
        self.get_logger().info(f'Acción terminada: {action_name}')

        self.busy = False

    def seconds_to_duration(self, seconds):
        sec = int(seconds)
        nanosec = int((seconds - sec) * 1e9)

        duration = Duration()
        duration.sec = sec
        duration.nanosec = nanosec

        return duration


def main(args=None):
    rclpy.init(args=args)

    node = ArmMotionExecutor()
    rclpy.spin(node)

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
