#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from geometry_msgs.msg import Twist

class RobotPlanner(Node):
    def __init__(self):
        super().__init__('robot_planner')

        # USA SOLO UN tópico — el que tu simulador realmente escucha
        # Comenta uno y prueba cuál funciona
        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        # self.cmd_pub = self.create_publisher(Twist, '/cmd_vel_unstamped', 10)

        self.tts_pub = self.create_publisher(String, '/tts_query', 10)

        self.subscription = self.create_subscription(
            String,
            '/sp_rec/recognized',
            self.process_command,
            10)

        self.current_twist = Twist()
        self.is_moving = False      # ← Solo publica cuando hay movimiento activo
        self.stop_timer = None

        # Timer de publicación continua a 20 Hz
        self.publish_timer = self.create_timer(0.05, self.publish_loop)

        self.get_logger().info('Robot Planner Node initialized')
        self.say("Robot listo.")

    def say(self, text):
        msg = String()
        msg.data = text
        self.tts_pub.publish(msg)
        self.get_logger().info(f'TTS: {text}')

    def publish_loop(self):
        """Solo publica si hay un movimiento activo."""
        if self.is_moving:
            self.cmd_pub.publish(self.current_twist)
            self.get_logger().debug(
                f'Publicando: linear={self.current_twist.linear.x:.2f} '
                f'angular={self.current_twist.angular.z:.2f}'
            )

    def set_velocity(self, linear_x=0.0, angular_z=0.0):
        self.current_twist = Twist()
        self.current_twist.linear.x = linear_x
        self.current_twist.angular.z = angular_z
        self.is_moving = True

    def schedule_stop(self, delay_seconds):
        if self.stop_timer is not None:
            self.stop_timer.cancel()
            self.stop_timer = None
        self.stop_timer = self.create_timer(delay_seconds, self._timed_stop)

    def _timed_stop(self):
        self.stop_timer.cancel()
        self.stop_timer = None
        self.stop()

    def process_command(self, msg):
        command = msg.data.lower().strip()
        if len(command) < 3:
            return
        self.get_logger().info(f'Comando recibido: {command}')

        if 'avanzar' in command or 'adelante' in command:
            self.move_forward()
        elif 'retroceder' in command or 'atras' in command:
            self.move_backward()
        elif 'girar izquierda' in command or 'izquierda' in command:
            self.turn_left()
        elif 'girar derecha' in command or 'derecha' in command:
            self.turn_right()
        elif 'detener' in command or 'parar' in command:
            self.stop()
        elif 'saludar' in command or 'hola' in command:
            self.greet()
        else:
            self.say(f"No entiendo: {command}")

    def move_forward(self):
        self.get_logger().info('→ ADELANTE')
        self.set_velocity(linear_x=0.2)
        self.say("Avanzando")
        self.schedule_stop(1.5)

    def move_backward(self):
        self.get_logger().info('→ ATRAS')
        self.set_velocity(linear_x=-0.2)
        self.say("Retrocediendo")
        self.schedule_stop(1.5)

    def turn_left(self):
        self.get_logger().info('→ IZQUIERDA')
        self.set_velocity(angular_z=0.5)
        self.say("Girando izquierda")
        self.schedule_stop(1.0)

    def turn_right(self):
        self.get_logger().info('→ DERECHA')
        self.set_velocity(angular_z=-0.5)
        self.say("Girando derecha")
        self.schedule_stop(1.0)

    def stop(self):
        self.get_logger().info('■ STOP')
        self.is_moving = False          # ← Deja de publicar en el loop
        # Manda cero explícitamente 3 veces para asegurar parada
        zero = Twist()
        for _ in range(3):
            self.cmd_pub.publish(zero)
        self.current_twist = zero
        self.say("Detenido")

    def greet(self):
        self.say("Hola, soy tu robot asistente")

def main(args=None):
    rclpy.init(args=args)
    node = RobotPlanner()
    rclpy.spin(node)

if __name__ == '__main__':
    main()
