import rclpy
from rclpy.node import Node
from nav_msgs.srv import GetPlan
from geometry_msgs.msg import PoseStamped
import time
import math
import numpy as np
import csv

class RRTTester(Node):
    def __init__(self):
        super().__init__('rrt_tester_node')
        self.client = self.create_client(GetPlan, '/path_planning/plan_path')
        
        while not self.client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('Esperando a que el servicio RRT esté disponible...')
        self.get_logger().info('Servicio RRT detectado. Listo para iniciar batería de pruebas.')

    def calculate_path_length(self, path_poses):
        length = 0.0
        for i in range(1, len(path_poses)):
            p1 = path_poses[i-1].pose.position
            p2 = path_poses[i].pose.position
            length += math.sqrt((p2.x - p1.x)**2 + (p2.y - p1.y)**2)
        return length

    def run_tests(self, start_x, start_y, goal_x, goal_y, iterations=30):
        self.get_logger().info(f'Iniciando {iterations} iteraciones...')
        
        results = []
        success_count = 0

        for i in range(iterations):
            req = GetPlan.Request()
            req.start = PoseStamped()
            req.start.pose.position.x = float(start_x)
            req.start.pose.position.y = float(start_y)
            
            req.goal = PoseStamped()
            req.goal.pose.position.x = float(goal_x)
            req.goal.pose.position.y = float(goal_y)

            t_start = time.time()
          
            future = self.client.call_async(req)
            rclpy.spin_until_future_complete(self, future)
            
            t_end = time.time()
            delta_ms = (t_end - t_start) * 1000.0 
            
            response = future.result()
            path_len = 0.0
            success = False
          
            if response is not None and len(response.plan.poses) > 1:
                success = True
                success_count += 1
                path_len = self.calculate_path_length(response.plan.poses)
                self.get_logger().info(f'Iteración {i+1}: Éxito | Tiempo: {delta_ms:.2f} ms | Nodos ruta: {len(response.plan.poses)}')
            else:
                self.get_logger().warning(f'Iteración {i+1}: Fallo | Tiempo: {delta_ms:.2f} ms')

            results.append({
                'iteracion': i + 1,
                'exito': success,
                'tiempo_ms': delta_ms,
                'longitud_ruta': path_len,
                'nodos_en_ruta': len(response.plan.poses) if success else 0
            })

      
        success_rate = (success_count / iterations) * 100
        successful_times = [r['tiempo_ms'] for r in results if r['exito']]
        successful_lengths = [r['longitud_ruta'] for r in results if r['exito']]

        avg_time = np.mean(successful_times) if successful_times else 0.0
        std_time = np.std(successful_times) if successful_times else 0.0
        avg_len = np.mean(successful_lengths) if successful_lengths else 0.0

        self.get_logger().info('=== RESUMEN DE PRUEBAS RRT ===')
        self.get_logger().info(f'Tasa de Éxito: {success_rate}% ({success_count}/{iterations})')
        self.get_logger().info(f'Tiempo Promedio (éxitos): {avg_time:.2f} ms (Desviación: {std_time:.2f} ms)')
        self.get_logger().info(f'Longitud Promedio de Ruta: {avg_len:.4f} m')

        
        filename = f'rrt_results_iter_{iterations}.csv'
        with open(filename, mode='w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=['iteracion', 'exito', 'tiempo_ms', 'longitud_ruta', 'nodos_en_ruta'])
            writer.writeheader()
            writer.writerows(results)
        self.get_logger().info(f'Datos guardados en {filename}')

def main(args=None):
    rclpy.init(args=args)
    tester_node = RRTTester()
    
    START_X = 0.0
    START_Y = 0.0
    GOAL_X = 6.0
    GOAL_Y = 6.7
    NUM_ITERACIONES = 30 
    
    tester_node.run_tests(START_X, START_Y, GOAL_X, GOAL_Y, iterations=NUM_ITERACIONES)
    
    tester_node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()