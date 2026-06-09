#!/usr/bin/env python3
"""
Simple State Machine Planner (SM Planner) + A* Path Following
Allows robot to navigate to named locations using voice commands
"""

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped, Quaternion, Twist
from nav_msgs.msg import Odometry
from std_msgs.msg import String
import math
from enum import Enum
from rclpy.qos import qos_profile_sensor_data

# Importamos tu planificador A*
from path_planner_astar import PathPlannerAStar

class NavigationState(Enum):
    IDLE = 0
    PLANNING = 1
    NAVIGATING = 2
    ARRIVED = 3
    FAILED = 4

class LocationDatabase:
    def __init__(self):
        # Coordenadas relativas al mapa.
        self.locations = {
            'refrigerador': {'position': (10.0, 0.5), 'orientation': 0.0},
            'estufa': {'position': (10.5, -1.5), 'orientation': math.pi/4},
            'lavamanos': {'position': (10.0, -3.0), 'orientation': -math.pi/2},
            'mesa cocina': {'position': (8.0, 2.0), 'orientation': math.pi},
            'gimnasio': {'position': (5.0, 4.0), 'orientation': 0.0},
            'cama': {'position': (-2.5, 3.2), 'orientation': math.pi/4},
        }
    
    def get_location(self, name):
        name_lower = name.lower().strip()
        return self.locations.get(name_lower)
    
    def list_locations(self):
        return list(self.locations.keys())

class SMPlanner(Node):
    def __init__(self):
        super().__init__('sm_planner')
        
        self.locations_db = LocationDatabase()
        self.state = NavigationState.IDLE
        self.current_location_name = None
        self.current_path = []
        self.control_timer = None
        
        # Publicador de velocidades para mover al robot
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        
        # Suscriptor a odometría
        self.current_pose = None
        self.odom_subscriber = self.create_subscription(Odometry, '/odom', self.odom_callback, qos_profile_sensor_data)        
        # Suscriptor a comandos
        self.command_subscriber = self.create_subscription(String, '/nav_command', self.command_callback, 10)
        
        # Inicializamos tu A* (200x200 celdas de 10cm = 20x20 metros)
        self.planner = PathPlannerAStar(grid_width=300, grid_height=300, resolution=0.1)
        
        # OFFSET: Tu A* usa índices de matriz (positivos).
        # Como tienes coordenadas negativas (ej. cama en x=-2.5), sumaremos este offset 
        # al planear para evitar errores de índice fuera de rango.
        self.OFFSET = 15.0 

        self.get_logger().info('SM Planner Node con A* Iniciado')
        self.get_logger().info('Escuchando en /nav_command...')
        
    def command_callback(self, msg):
        command = msg.data
        self.get_logger().info(f'📍 Comando recibido: "{command}"')
        self.process_command(command)
    
    def odom_callback(self, msg):
        self.current_pose = msg.pose.pose
    
    def navigate_to_location(self, location_name):
        if self.current_pose is None:
            self.get_logger().warn('⏳ Esperando datos de odometría (/odom)...')
            return False

        location_name_lower = location_name.lower().strip()
        location = self.locations_db.get_location(location_name_lower)
        
        if not location:
            self.get_logger().warn(f'❌ Ubicación "{location_name}" no encontrada.')
            return False
        
        self.state = NavigationState.PLANNING
        self.current_location_name = location_name
        
        start_x = self.current_pose.position.x
        start_y = self.current_pose.position.y
        goal_x = location['position'][0]
        goal_y = location['position'][1]
        
        self.get_logger().info(f'🗺️ Planeando ruta de ({start_x:.2f}, {start_y:.2f}) a ({goal_x:.2f}, {goal_y:.2f})')
        
        # Agregamos offset para evitar coordenadas negativas en el Grid de A*
        path = self.planner.plan_path(start_x + self.OFFSET, start_y + self.OFFSET, 
                                      goal_x + self.OFFSET, goal_y + self.OFFSET)
        
        if path:
            # Suavizamos y luego removemos el offset para volver a coordenadas del mundo (Gazebo)
            smoothed_path = self.planner.smooth_path(path)
            self.current_path = [(px - self.OFFSET, py - self.OFFSET) for px, py in smoothed_path]
            
            self.get_logger().info(f'🚀 Ruta encontrada ({len(self.current_path)} puntos). ¡Moviendo el robot!')
            self.state = NavigationState.NAVIGATING
            
            # Iniciamos el bucle de control a 10 Hz
            if self.control_timer:
                self.control_timer.cancel()
            self.control_timer = self.create_timer(0.1, self.follow_path_loop)
            return True
        else:
            self.get_logger().error('❌ A* no pudo encontrar una ruta válida.')
            self.state = NavigationState.FAILED
            return False

    def follow_path_loop(self):
        """Controlador Proporcional para seguir la ruta punto a punto"""
        if not self.current_path or self.state != NavigationState.NAVIGATING:
            self.stop_robot()
            self.state = NavigationState.ARRIVED
            self.get_logger().info(f'✅ ¡Llegué a {self.current_location_name}!')
            self.control_timer.cancel()
            return

        # Obtenemos posición actual
        curr_x = self.current_pose.position.x
        curr_y = self.current_pose.position.y
        
        # Convertimos cuaternión a Yaw (ángulo Z)
        q = self.current_pose.orientation
        siny_cosp = 2 * (q.w * q.z + q.x * q.y)
        cosy_cosp = 1 - 2 * (q.y * q.y + q.z * q.z)
        yaw = math.atan2(siny_cosp, cosy_cosp)

        # Nuestro objetivo actual es el primer punto de la lista
        target_x, target_y = self.current_path[0]
        
        # Matemáticas de control
        dx = target_x - curr_x
        dy = target_y - curr_y
        distance = math.sqrt(dx**2 + dy**2)
        angle_to_target = math.atan2(dy, dx)
        
        # Error de ángulo (normalizado entre -pi y pi)
        angle_error = angle_to_target - yaw
        angle_error = math.atan2(math.sin(angle_error), math.cos(angle_error))

        msg = Twist()
        
        # Si estamos muy cerca del punto (tolerancia de 25 cm), pasamos al siguiente
        if distance < 0.25:
            self.current_path.pop(0)
            return
        
        # Controlador de giro (proporcional al error)
        msg.angular.z = 1.5 * angle_error
        # Limitamos la velocidad de giro máxima
        msg.angular.z = max(min(msg.angular.z, 1.0), -1.0) 

        # Controlador de avance: Solo avanzamos si estamos mirando (más o menos) hacia el objetivo
        if abs(angle_error) < 0.5: # ~30 grados de tolerancia
            msg.linear.x = 0.5 * distance
            msg.linear.x = min(msg.linear.x, 0.4) # Velocidad lineal máxima 0.4 m/s

        self.cmd_vel_pub.publish(msg)

    def stop_robot(self):
        msg = Twist()
        msg.linear.x = 0.0
        msg.angular.z = 0.0
        self.cmd_vel_pub.publish(msg)

    def process_command(self, command_text):
        command_lower = command_text.lower().strip()
        keywords = ['go to', 'navigate to', 'move to', 'visit', 'head to', 've a', 'ir a']
        location_name = None
        
        for keyword in keywords:
            if keyword in command_lower:
                parts = command_lower.split(keyword, 1)
                if len(parts) > 1:
                    location_name = parts[1].strip()
                    break
                    
        if not location_name:
            location_name = command_lower
            
        if location_name:
            self.navigate_to_location(location_name)
        else:
            self.get_logger().warn('⚠️ No entendí la ubicación.')

def main(args=None):
    rclpy.init(args=args)
    planner = SMPlanner()
    try:
        rclpy.spin(planner)
    except KeyboardInterrupt:
        planner.get_logger().info('Apagando...')
        planner.stop_robot()
    finally:
        planner.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()