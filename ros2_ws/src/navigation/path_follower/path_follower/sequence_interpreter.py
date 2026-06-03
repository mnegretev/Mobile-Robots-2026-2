import json

import rclpy
from rclpy.node import Node

from std_msgs.msg import String, Bool


class SequenceInterpreter(Node):
    def __init__(self):
        super().__init__('sequence_interpreter')

        # Publicador para mandar destinos al selector de rutas
        self.pub_route_command = self.create_publisher(
            String,
            '/route_command',
            10
        )

        # Publicador para mandar acciones al brazo
        self.pub_arm_command = self.create_publisher(
            String,
            '/arm_command',
            10
        )

        # Suscriptor que recibe la secuencia generada por el LLM
        self.sub_task_sequence = self.create_subscription(
            String,
            '/task_sequence',
            self.task_sequence_callback,
            10
        )

        # Suscriptor que avisa cuando el robot móvil llegó a su destino
        self.sub_goal_reached = self.create_subscription(
            Bool,
            '/navigation/goal_reached',
            self.goal_reached_callback,
            10
        )

        # Suscriptor que avisa cuando el brazo terminó su acción
        self.sub_arm_done = self.create_subscription(
            Bool,
            '/arm_action_done',
            self.arm_done_callback,
            10
        )

        self.valid_locations = [
            'cama',
            'refrigerador',
            'sillon',
            'pesas',
            'tele',
            'pelota',
            'puerta'
        ]

        self.valid_arm_actions = [
            'agarrar_abajo',
            'agarrar_medio',
            'agarrar_arriba',
            'saludar'
        ]

        self.steps = []
        self.executing = False
        self.waiting_for = None

        self.get_logger().info('Sequence interpreter listo.')
        self.get_logger().info('Esperando secuencias en /task_sequence.')

    def task_sequence_callback(self, msg):
        if self.executing:
            self.get_logger().warn('Ya hay una secuencia en ejecución. Ignorando nuevo comando.')
            return

        try:
            data = json.loads(msg.data)
        except Exception as e:
            self.get_logger().error(f'JSON inválido en /task_sequence: {e}')
            return

        if 'steps' not in data:
            self.get_logger().error('El JSON no contiene la clave steps.')
            return

        if not isinstance(data['steps'], list):
            self.get_logger().error('La clave steps no es una lista.')
            return

        if len(data['steps']) == 0:
            self.get_logger().warn('La secuencia está vacía.')
            return

        if not self.validate_steps(data['steps']):
            self.get_logger().error(f'Secuencia inválida: {data["steps"]}')
            return

        self.steps = data['steps']
        self.executing = True
        self.waiting_for = None

        self.get_logger().info(f'Secuencia recibida: {self.steps}')

        self.execute_next_step()

    def validate_steps(self, steps):
        for step in steps:
            if not isinstance(step, dict):
                return False

            if 'type' not in step or 'target' not in step:
                return False

            step_type = step['type']
            target = step['target']

            if step_type == 'navigate':
                if target not in self.valid_locations:
                    return False

            elif step_type == 'arm':
                if target not in self.valid_arm_actions:
                    return False

            else:
                return False

        return True

    def execute_next_step(self):
        if len(self.steps) == 0:
            self.get_logger().info('Secuencia terminada.')
            self.executing = False
            self.waiting_for = None
            return

        step = self.steps.pop(0)

        msg = String()
        msg.data = step['target']

        if step['type'] == 'navigate':
            self.pub_route_command.publish(msg)
            self.waiting_for = 'navigation'
            self.get_logger().info(f'Navegando hacia: {step["target"]}')

        elif step['type'] == 'arm':
            self.pub_arm_command.publish(msg)
            self.waiting_for = 'arm'
            self.get_logger().info(f'Ejecutando acción del brazo: {step["target"]}')

    def goal_reached_callback(self, msg):
        if not self.executing:
            return

        if self.waiting_for != 'navigation':
            return

        if not msg.data:
            return

        self.get_logger().info('Destino alcanzado.')
        self.waiting_for = None
        self.execute_next_step()

    def arm_done_callback(self, msg):
        if not self.executing:
            return

        if self.waiting_for != 'arm':
            return

        if not msg.data:
            return

        self.get_logger().info('Acción del brazo terminada.')
        self.waiting_for = None
        self.execute_next_step()


def main(args=None):
    rclpy.init(args=args)

    node = SequenceInterpreter()
    rclpy.spin(node)

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
