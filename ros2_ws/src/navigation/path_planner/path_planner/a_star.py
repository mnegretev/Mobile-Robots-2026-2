#
# MOBILE ROBOTS - FI-UNAM, 2026-2
# PATH PLANNING BY A-STAR
#
# Instructions:
# Write the code necessary to plan a path using an
# occupancy grid and the A* algorithm
# MODIFY ONLY THE SECTIONS MARKED WITH THE 'TODO' COMMENT
#
import rclpy
from rclpy.node import Node
from rclpy.time import Time, Duration
from geometry_msgs.msg import PoseStamped, Pose, Point
from nav_msgs.msg import Path
from nav_msgs.srv import *
from builtin_interfaces.msg import Duration
from collections import deque
import numpy
import heapq
import math

NAME = "Gonzalez Fernandez Jonathan Uriel"

class AStarNode(Node):
    def a_star(self, start_r, start_c, goal_r, goal_c, grid_map, cost_map, use_diagonals):
        [height, width] = grid_map.shape
        in_open_list   = numpy.full(grid_map.shape, False)
        in_closed_list = numpy.full(grid_map.shape, False)
        g_values       = numpy.full(grid_map.shape, float("inf"))
        f_values       = numpy.full(grid_map.shape, float("inf"))
        parent_nodes   = numpy.full((grid_map.shape[0],grid_map.shape[1],2),-1)
        open_list = []
        if use_diagonals: #Every adjacent node has: [row_offset, col_offset, cost]
            adjacents = [[1,0,1],[0,1,1],[-1,0,1],[0,-1,1], [1,1,1.414], [-1,1,1.414], [-1,-1,1.414],[1,-1,1.414]]
        else:
            adjacents = [[1,0,1],[0,1,1],[-1,0,1],[0,-1,1]]

        heapq.heappush(open_list, (0, [start_r, start_c]))
        in_open_list[start_r, start_c] = True
        g_values    [start_r, start_c] = 0
        [row, col]= [start_r, start_c]   #Current node
        
        # --- INICIO DEL CICLO PRINCIPAL A* ---
        
        while len(open_list) > 0:
            
            # Extraer el nodo con el menor costo f(n) de la frontera
            current_f, [row, col] = heapq.heappop(open_list)
            
            # Condición de éxito: Hemos llegado a la meta
            if row == goal_r and col == goal_c:
                break
                
            # Marcar el nodo actual como evaluado (cerrado)
            in_closed_list[row, col] = True
            
            # Evaluar todos los nodos adyacentes (vecinos)
            for adj in adjacents:
                r = row + adj[0]
                c = col + adj[1]
                dist_cost = adj[2]
                
                # Descartar si el vecino sale de los límites del mapa
                if r < 0 or r >= height or c < 0 or c >= width:
                    continue
                    
                # Descartar si es obstáculo (>=100), desconocido (-1) o ya fue evaluado
                if grid_map[r, c] >= 100 or grid_map[r, c] == -1 or in_closed_list[r, c]:
                    continue
                    
                # Costo g(n): Costo acumulado + distancia + penalización por cercanía a obstáculos
                tentative_g = g_values[row, col] + dist_cost + cost_map[r, c]
                
                # Heurística h(n): Distancia Euclidiana estimada hacia la meta
                h = ((goal_r - r)**2 + (goal_c - c)**2)**0.5
                
                # Costo total f(n) = g(n) + h(n)
                tentative_f = tentative_g + h
                
                # Si encontramos un camino más óptimo hacia este vecino
                if tentative_g < g_values[r, c]:
                    
                    # Actualizar costos y registrar el nodo padre para trazar la ruta
                    g_values[r, c] = tentative_g
                    f_values[r, c] = tentative_f
                    parent_nodes[r, c] = [row, col]
                    
                    # Agregar el vecino a la frontera de exploración si no estaba ahí
                    if not in_open_list[r, c]:
                        in_open_list[r, c] = True
                        heapq.heappush(open_list, (tentative_f, [r, c]))
                        
        # --- FIN DEL CICLO PRINCIPAL A* ---

        path = []
        while parent_nodes[goal_r, goal_c][0] != -1:
            path.insert(0, [goal_r, goal_c])
            [goal_r, goal_c] = parent_nodes[goal_r, goal_c]
        return path

    def get_maps(self):
        self.get_logger().info("Waiting for inflated map service...")
        while not self.clt_inflated_map.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('Waiting for inflated map service...')
        self.get_logger().info("Inflated map service is now available...")
        self.get_logger().info("Waiting for cost map service...")
        while not self.clt_cost_map.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('Waiting for cost map service...')
        self.get_logger().info("Cost map service is now available...")

        self.get_logger().info("Trying to get inflated map...")
        future = self.clt_inflated_map.call_async(GetMap.Request())
        rclpy.spin_until_future_complete(self, future)
        inflated_map = future.result().map
        self.get_logger().info("Got inflated map.")
        self.get_logger().info("Trying to get cost map...")
        future = self.clt_cost_map.call_async(GetMap.Request())
        rclpy.spin_until_future_complete(self, future)
        cost_map= future.result().map
        self.get_logger().info("Got cost map.")
        return [inflated_map, cost_map]

    def get_path_msg(self, path, res, zx, zy):
        msg_path = Path()
        msg_path.header.frame_id = "map"
        msg_path.header.stamp = self.get_clock().now().to_msg()
        msg_path.poses = []
        for [r,c] in path:
            msg_path.poses.append(PoseStamped(pose=Pose(position=Point(x=(c*res + zx), y=(r*res + zy)))))
        return msg_path

    def callback_a_star(self, req, resp):
        info = self.inflated_map.info
        res = info.resolution
        [sx, sy] = [req.start.pose.position.x, req.start.pose.position.y]
        [gx, gy] = [req.goal .pose.position.x, req.goal .pose.position.y]
        [zx, zy] = [self.inflated_map.info.origin.position.x, self.inflated_map.info.origin.position.y]
        use_diagonals = self.get_parameter('diagonals').get_parameter_value().bool_value
        inflated_grid = numpy.reshape(numpy.asarray(self.inflated_map.data), (info.height, info.width))
        cost_grid     = numpy.reshape(numpy.asarray(self.cost_map.data)    , (info.height, info.width))
        
        self.get_logger().info("Planning path by A* from " + str([sx, sy])+" to "+str([gx, gy]))
        start_time = self.get_clock().now()
        path = self.a_star(int((sy-zy)/res), int((sx-zx)/res), int((gy-zy)/res), int((gx-zx)/res),
                           inflated_grid, cost_grid, use_diagonals)
        end_time = self.get_clock().now()
        delta_ms = (end_time.nanoseconds - start_time.nanoseconds)/1e6
        if len(path) > 0:
            self.get_logger().info("Path planned after " + str(delta_ms) + " ms with " +  str(len(path)) + " points")
        else:
            self.get_logger().info("Cannot plan path from  " + str([sx, sy])+" to "+str([gx, gy]) + " :'(")

        self.msg_path = self.get_path_msg(path, res, zx, zy)
        resp.plan = self.msg_path
        return resp

    def callback_timer(self):
        self.pub_path.publish(self.msg_path)
            
    def __init__(self):
        super().__init__("a_star_node")
        self.get_logger().info("INITIALIZING A STAR NODE - " + NAME)
        self.clt_inflated_map = self.create_client(GetMap, '/get_inflated_map')
        self.clt_cost_map     = self.create_client(GetMap, '/get_cost_map')
        
        [self.inflated_map, self.cost_map] = self.get_maps()
        self.declare_parameter('diagonals', False)
        self.srv_plan_path = self.create_service(GetPlan, '/path_planning/plan_path', self.callback_a_star)
        self.pub_path = self.create_publisher(Path, '/path_planning/path', 10)
        self.msg_path = Path()
        self.timer = self.create_timer(0.5, self.callback_timer)
            
def main(args=None):
    rclpy.init(args=args)
    a_star_node = AStarNode()
    rclpy.spin(a_star_node)
    a_star_node.destroy_node()
    rclpy.shutdown()

    
if __name__ == '__main__':
    main()
