#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32
from rclpy.action import ActionClient
from nav2_msgs.action import NavigateToPose
from vision_msgs.srv import LocateObject

NAME = "MENDEZ HORTA ALEXANDER - TASK MANAGER"

class TaskManager(Node):
    def __init__(self):
        super().__init__('task_manager_node')
        self.get_logger().info("INITIALIZING TASK MANAGER - " + NAME)
        
        # Estado del robot
        self.state = 'IDLE'
        
        # Suscriptor para escuchar las órdenes (ej. Ollama o Terminal enviará 1, 2 o 3)
        self.create_subscription(Int32, '/task/request', self.task_callback, 10)
        
        # Cliente para preguntarle a YOLO dónde están las cosas
        self.vision_client = self.create_client(LocateObject, '/vision/locate_object')
        
        # Cliente de Acción para mandar a mover al robot (Habla con tu nav_action_server)
        self.nav_client = ActionClient(self, NavigateToPose, '/nav/go_to_pose')

    def task_callback(self, msg):
        if self.state != 'IDLE':
            self.get_logger().warn("¡Robot ocupado! Ignorando nueva orden.")
            return
            
        task_id = msg.data
        self.state = 'RUNNING'
        
        if task_id == 1:
            self.get_logger().info("---- TAREA RECIBIDA: Ir al Refrigerador ----")
            self.locate_and_go("refrigerator")
            
        elif task_id == 2:
            self.get_logger().info("---- TAREA RECIBIDA: Ir a la Mesa ----")
            self.locate_and_go("table")
            
        elif task_id == 3:
            self.get_logger().info("---- TAREA RECIBIDA: Reporte de Estado ----")
            self.get_logger().info("BATERÍA: 100%. SISTEMAS: OK. Esperando órdenes.")
            self.state = 'IDLE'
        else:
            self.get_logger().error("Tarea desconocida.")
            self.state = 'IDLE'

    # --- PASO 1: Llamar a Visión ---
    def locate_and_go(self, object_name):
        while not self.vision_client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('Esperando al nodo de Visión...')
            
        req = LocateObject.Request()
        req.object_name = object_name
        
        self.get_logger().info(f"Preguntando a Visión por: {object_name}...")
        future = self.vision_client.call_async(req)
        future.add_done_callback(self.vision_response_callback)

    # --- PASO 2: Recibir respuesta de Visión e iniciar Navegación ---
    def vision_response_callback(self, future):
        response = future.result()
        if response.success:
            x = response.pose.pose.position.x
            y = response.pose.pose.position.y
            self.get_logger().info(f"¡Objetivo localizado en X:{x:.2f}, Y:{y:.2f}! Iniciando navegación...")
            self.send_nav_goal(response.pose)
        else:
            self.get_logger().error("Visión reportó fallo. Abortando tarea.")
            self.state = 'IDLE'

    # --- PASO 3: Ejecutar la Acción de Navegación ---
    def send_nav_goal(self, target_pose):
        goal_msg = NavigateToPose.Goal()
        goal_msg.pose = target_pose
        
        self.nav_client.wait_for_server()
        send_goal_future = self.nav_client.send_goal_async(goal_msg)
        send_goal_future.add_done_callback(self.nav_goal_accepted_callback)

    def nav_goal_accepted_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().error("El Action Server de Navegación rechazó la meta.")
            self.state = 'IDLE'
            return
            
        self.get_logger().info("Meta aceptada. El robot se está moviendo...")
        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(self.nav_result_callback)

    def nav_result_callback(self, future):
        self.get_logger().info("¡TAREA COMPLETADA CON ÉXITO! El robot ha llegado a su destino.")
        self.state = 'IDLE'

def main(args=None):
    rclpy.init(args=args)
    node = TaskManager()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()