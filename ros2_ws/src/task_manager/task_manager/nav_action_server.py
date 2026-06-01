#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from rclpy.action import ActionServer
from nav2_msgs.action import NavigateToPose
from geometry_msgs.msg import PoseStamped
from std_msgs.msg import Bool
import asyncio

class NavActionServer(Node):
    def __init__(self):
        super().__init__('nav_action_server')
        
        # 1. Escucha al Task Manager
        self._action_server = ActionServer(
            self,
            NavigateToPose,
            '/nav/go_to_pose',
            self.execute_callback
        )
        
        # 2. Le habla a tu Pure Pursuit
        self.goal_pub = self.create_publisher(PoseStamped, '/goal_pose', 10)
        
        # 3. NUEVO: Escucha cuando Pure Pursuit termina
        self.reached_sub = self.create_subscription(Bool, '/navigation/goal_reached', self.reached_callback, 10)
        
        # Bandera de estado
        self.is_goal_reached = False
        
        self.get_logger().info("=== ACTION SERVER EN MODO LAZO CERRADO ACTIVO ===")

    def reached_callback(self, msg):
        # Cuando Pure Pursuit publica en el tópico, actualizamos la bandera
        if msg.data:
            self.is_goal_reached = True

    async def execute_callback(self, goal_handle):
        target_pose = goal_handle.request.pose
        self.get_logger().info(f"Delegando meta a Pure Pursuit -> X:{target_pose.pose.position.x:.2f}, Y:{target_pose.pose.position.y:.2f}")

        # Preparamos el mensaje
        target_pose.header.stamp = self.get_clock().now().to_msg()
        target_pose.header.frame_id = 'map'

        # Bajamos la bandera antes de empezar
        self.is_goal_reached = False
        
        # Disparamos el movimiento
        self.goal_pub.publish(target_pose)
        self.get_logger().info("Esperando a que Pure Pursuit llegue a la meta...")

        # NUEVO: Bucle de espera asíncrona.
        # Revisa la bandera cada medio segundo sin congelar ROS 2.
        while not self.is_goal_reached:
            await asyncio.sleep(0.5)

        # ¡Por fin llegó! Avisamos al Orquestador
        goal_handle.succeed()
        result = NavigateToPose.Result()
        self.get_logger().info("=== ¡META ALCANZADA! AVISANDO AL TASK MANAGER ===")
        return result

def main(args=None):
    rclpy.init(args=args)
    node = NavActionServer()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()