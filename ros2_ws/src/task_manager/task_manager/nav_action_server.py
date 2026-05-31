#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from rclpy.action import ActionServer
from rclpy.callback_groups import ReentrantCallbackGroup
from nav2_msgs.action import NavigateToPose
from nav_msgs.srv import GetPlan
from geometry_msgs.msg import PoseStamped
import time

NAME = "MENDEZ HORTA ALEXANDER - NAV ACTION SERVER"

class NavActionServer(Node):
    def __init__(self):
        super().__init__('nav_action_server_node')
        self.get_logger().info("INITIALIZING NAV ACTION SERVER - " + NAME)
        
        # Grupo de callbacks reentrante para permitir llamadas a servicios dentro de la acción
        self.cb_group = ReentrantCallbackGroup()
        
        # 1. El Action Server que el LLM/Task Manager va a llamar
        self._action_server = ActionServer(
            self,
            NavigateToPose,
            '/nav/go_to_pose',
            self.execute_callback,
            callback_group=self.cb_group
        )
        
        # 2. Cliente para conectarnos a tu A* existente
        self.clt_plan_path = self.create_client(GetPlan, '/path_planning/plan_path')

    def execute_callback(self, goal_handle):
        self.get_logger().info('Recibiendo meta de navegación...')
        
        # Extraemos la meta (X, Y)
        target_pose = goal_handle.request.pose
        
        # --- PASO 1: Llamar a tu A* para calcular la ruta ---
        while not self.clt_plan_path.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('Esperando al servicio de A* (/path_planning/plan_path)...')
            
        req = GetPlan.Request()
        # Aquí se asume que el robot parte de su posición actual (puedes enlazar tf2 luego)
        req.start = PoseStamped() # Pose actual simulada
        req.goal = target_pose    # La meta que nos pidió la IA
        
        self.get_logger().info('Calculando ruta con A*...')
        future = self.clt_plan_path.call_async(req)
        rclpy.spin_until_future_complete(self, future)
        
        plan = future.result().plan
        
        if len(plan.poses) == 0:
            self.get_logger().error('A* falló al encontrar una ruta.')
            goal_handle.abort()
            return NavigateToPose.Result()
            
        self.get_logger().info(f'Ruta encontrada con {len(plan.poses)} puntos.')
        
        # --- PASO 2: Mandar al path_follower a ejecutar la ruta ---
        # TODO: Aquí debes publicar el 'plan' en el tópico que escuche tu path_follower
        # y monitorear si el robot ya llegó a la meta.
        
        # Simulamos el tiempo de viaje enviando feedback
        feedback_msg = NavigateToPose.Feedback()
        for i in range(1, 6):
            if goal_handle.is_cancel_requested:
                goal_handle.canceled()
                self.get_logger().info('Navegación cancelada.')
                return NavigateToPose.Result()
                
            feedback_msg.distance_remaining = float(5 - i)
            goal_handle.publish_feedback(feedback_msg)
            time.sleep(1.0) # Simulando que el robot se mueve
            
        # --- PASO 3: Reportar Éxito ---
        goal_handle.succeed()
        self.get_logger().info('¡Meta alcanzada con éxito!')
        
        result = NavigateToPose.Result()
        # NavigateToPose.Result() está vacío en nav2_msgs, solo devuelve success
        return result

def main(args=None):
    rclpy.init(args=args)
    nav_action_server = NavActionServer()
    # Usamos MultiThreadedExecutor para manejar el Action y el Service al mismo tiempo
    executor = rclpy.executors.MultiThreadedExecutor()
    rclpy.spin(nav_action_server, executor=executor)
    nav_action_server.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()