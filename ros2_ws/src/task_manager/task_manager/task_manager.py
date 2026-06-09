#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32  # Cambiamos a String para leer "0001"
from rclpy.action import ActionClient
from nav2_msgs.action import NavigateToPose
from vision_msgs.srv import LocateObject
from geometry_msgs.msg import PoseStamped

NAME = "MENDEZ HORTA ALEXANDER - TASK MANAGER V2"

class TaskManager(Node):
    def __init__(self):
        super().__init__('task_manager_node')
        self.get_logger().info("INITIALIZING TASK MANAGER - " + NAME)
        
        self.state = 'IDLE'
        self.state = 'IDLE'
        self.returning_to_base = False  # NUEVO: Bandera para saber el sentido del viaje
        
        # 1. ESCUCHAMOS DIRECTO AL NODO DE OLLAMA (Cambiamos el tópico y el tipo)
        self.create_subscription(Int32, '/llm/action_code', self.task_callback, 10)
        
        self.vision_client = self.create_client(LocateObject, '/vision/locate_object')
        self.nav_client = ActionClient(self, NavigateToPose, '/nav/go_to_pose')
        
        # 2. EL DICCIONARIO DE MISIONES (Fácil de escalar)
        self.mission_catalog = {
            1: {"name": "Ir al Refrigerador", "target": "refrigerator"},
            2: {"name": "Ir a la Mesa", "target": "table"},
            3: {"name": "Ir a la Puerta", "target": "door"},
            0: {"name": "Comando no reconocido", "target": None}
        }
        
        self.get_logger().info("Esperando instrucciones de voz...")

    def task_callback(self, msg):
        if self.state != 'IDLE':
            self.get_logger().warn("¡Robot ocupado! Ignorando nueva orden.")
            return
            
        action_code = msg.data
        
        if action_code not in self.mission_catalog:
            self.get_logger().error(f"Código desconocido recibido: {action_code}")
            return
            
        mission = self.mission_catalog[action_code]
        
        if mission["target"] is None:
            self.get_logger().info("Ollama no entendió el comando. Esperando nueva orden...")
            return
            
        self.state = 'RUNNING'
        self.get_logger().info(f"---- TAREA RECIBIDA DE VOZ: {mission['name']} ----")
        self.locate_and_go(mission["target"])

    # --- PASO 1: Llamar a Visión (YOLO) ---
    def locate_and_go(self, object_name):
        # ... (El resto del código se queda exactamente igual) ...
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
        # Si NO está regresando, significa que acaba de llegar al objetivo (ej. el refri)
        if not self.returning_to_base:
            self.get_logger().info("¡Llegó al objetivo! Recogiendo objeto (simulado) y volviendo a la base...")
            self.returning_to_base = True
            self.go_to_base()
            
        # Si SÍ estaba regresando, significa que ya volvió al cuarto principal
        else:
            self.get_logger().info("¡MISIÓN COMPLETADA CON ÉXITO! El robot está de vuelta en el cuarto principal.")
            self.state = 'IDLE'
            self.returning_to_base = False

    def go_to_base(self):
        # Creamos la coordenada de regreso a mano
        base_pose = PoseStamped()
        base_pose.header.frame_id = 'map'
        base_pose.header.stamp = self.get_clock().now().to_msg()
        
        # --- MODIFICA TUS COORDENADAS AQUÍ ---
        base_pose.pose.position.x = -1.8  # Coordenada X del cuarto principal
        base_pose.pose.position.y = 2.73  # Coordenada Y del cuarto principal
        
        # Orientación (1.0 es viendo hacia el frente original)
        base_pose.pose.orientation.w = 1.0  
        
        self.get_logger().info(f"Iniciando viaje de retorno a X:{base_pose.pose.position.x}, Y:{base_pose.pose.position.y}...")
        
        # Usamos la misma función que ya tenías para mandarle la meta
        self.send_nav_goal(base_pose)

def main(args=None):
    rclpy.init(args=args)
    node = TaskManager()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()