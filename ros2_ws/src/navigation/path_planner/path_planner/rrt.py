# MOBILE ROBOTS - FI-UNAM, 2026-2
# RAPIDLY EXPLORING RANDOM TREES - TAREA 04
import rclpy
from rclpy.node import Node
from rclpy.time import Time, Duration
from geometry_msgs.msg import PoseStamped, Pose, Point
from visualization_msgs.msg import Marker
from nav_msgs.msg import Path
from nav_msgs.srv import *
from builtin_interfaces.msg import Duration
import numpy
import math
import csv

NAME = "Oscar Saldivar Pantoja"

class TreeNode:
    def __init__(self, x, y, parent=None):
        self.children = []
        self.parent = parent
        self.x = x
        self.y = y

class RRTNode(Node):
    def in_free_space(self, x, y, grid_map):
        c = int((x - grid_map.info.origin.position.x)/grid_map.info.resolution)
        r = int((y - grid_map.info.origin.position.y)/grid_map.info.resolution)
        if r >= grid_map.info.height or c >= grid_map.info.width or r < 0 or c < 0:
            return False
        return grid_map.data[r*grid_map.info.width + c] < 40 and grid_map.data[r*grid_map.info.width + c] >= 0
    
    def get_random_q(self, grid_map):
        min_x = grid_map.info.origin.position.x
        min_y = grid_map.info.origin.position.y
        max_x = min_x + grid_map.info.width * grid_map.info.resolution
        max_y = min_y + grid_map.info.height * grid_map.info.resolution
        is_free = False
        attempts = 100
        while not is_free and attempts > 0:
            x = numpy.random.uniform(min_x, max_x)
            y = numpy.random.uniform(min_y, max_y)
            is_free = self.in_free_space(x, y, grid_map)
            attempts -= 1
        return [x, y]

    def get_nearest_node(self, tree, x, y):
        S, N = [tree], []
        while len(S) > 0:
            n = S.pop(); N.append(n)
            for c in n.children: S.append(c)
        distances = numpy.asarray([math.sqrt((x - n.x)**2 + (y - n.y)**2) for n in N])
        return N[numpy.argmin(distances)]
    
    def get_new_node(self, nearest_node, rnd_x, rnd_y, epsilon):
        dist = math.sqrt((nearest_node.x - rnd_x)**2 + (nearest_node.y - rnd_y)**2)
        mag = min(dist, epsilon)
        if dist == 0: return None
        nx = nearest_node.x + mag*(rnd_x - nearest_node.x)/dist
        ny = nearest_node.y + mag*(rnd_y - nearest_node.y)/dist
        return TreeNode(nx, ny, nearest_node)
    
    def check_collision(self, n1, n2, grid_map, epsilon):
        n = 2*int(max(abs(n2.x-n1.x), abs(n2.y-n1.y))/grid_map.info.resolution) + 2
        P = numpy.linspace([n1.x, n1.y], [n2.x, n2.y], n)
        for x, y in P:
            if not self.in_free_space(x, y, grid_map): return True
        return False

    def rrt(self, start_x, start_y, goal_x, goal_y, grid_map, epsilon, max_attempts):
        tree = TreeNode(start_x, start_y, None)
        goal_node = TreeNode(goal_x, goal_y, None)
        while goal_node.parent is None and max_attempts > 0:
            [x, y] = self.get_random_q(grid_map)
            nearest = self.get_nearest_node(tree, x, y)
            new_n = self.get_new_node(nearest, x, y, epsilon)
            if new_n and not self.check_collision(nearest, new_n, grid_map, epsilon):
                nearest.children.append(new_n)
                if not self.check_collision(new_n, goal_node, grid_map, epsilon):
                    new_n.children.append(goal_node); goal_node.parent = new_n
            max_attempts -= 1
        path = []
        curr = goal_node
        if curr.parent is not None:
            while curr is not None:
                path.insert(0, [curr.x, curr.y]); curr = curr.parent
        return tree, path

    def callback_rrt(self, req, resp):
        sx, sy = req.start.pose.position.x, req.start.pose.position.y
        gx, gy = req.goal.pose.position.x, req.goal.pose.position.y
        epsilons, max_ns = [0.1, 0.5, 2.0], [50, 200, 1000]
        intentos_por_config = 100 
        resultados = []

        self.get_logger().info(f"Iniciando experimentos: {intentos_por_config} intentos por configuración...")

        for e in epsilons:
            for n in max_ns:
                exitos_acumulados, tiempos_acumulados = 0, 0.0
                for i in range(intentos_por_config):
                    start_t = self.get_clock().now()
                    tree, path = self.rrt(sx, sy, gx, gy, self.grid_map, e, n)
                    end_t = self.get_clock().now()
                    if len(path) > 0:
                        exitos_acumulados += 1
                        tiempos_acumulados += (end_t.nanoseconds - start_t.nanoseconds)/1e6
                
                promedio_ms = tiempos_acumulados / exitos_acumulados if exitos_acumulados > 0 else 0.0
                resultados.append([gx, gy, e, n, exitos_acumulados, intentos_por_config, promedio_ms])
                self.get_logger().info(f"e={e}, N={n} -> Éxitos: {exitos_acumulados}/{intentos_por_config}")

        with open('resultados_rrt_oscar.csv', 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Meta_X', 'Meta_Y', 'Epsilon', 'Max_N', 'Veces_Exito', 'Total_Intentos', 'Tiempo_Promedio_ms'])
            writer.writerows(resultados)
        
        self.get_logger().info("Tabla de 100 intentos guardada exitosamente.")
        self.msg_path = Path()
        resp.plan = self.msg_path
        return resp

    def get_tree_marker(self, tree):
        mrk = Marker()
        mrk.header.stamp, mrk.header.frame_id = self.get_clock().now().to_msg(), "map"
        mrk.ns, mrk.id, mrk.type, mrk.action = "path_planning", 0, Marker.LINE_LIST, Marker.ADD
        mrk.color.r, mrk.color.g, mrk.color.b, mrk.color.a = 0.7, 0.4, 1.0, 0.9
        mrk.scale.x, mrk.pose.orientation.w = 0.03, 1.0
        S = [tree]
        while len(S) > 0:
            n = S.pop()
            for c in n.children:
                mrk.points.append(Point(x=n.x, y=n.y, z=0.0))
                mrk.points.append(Point(x=c.x, y=c.y, z=0.0))
                S.append(c)
        return mrk

    def get_inflated_map(self):
        f = self.clt_inflated_map.call_async(GetMap.Request())
        rclpy.spin_until_future_complete(self, f)
        return f.result().map

    def callback_timer(self):
        self.pub_path.publish(self.msg_path); self.pub_tree.publish(self.msg_tree)

    def __init__(self):
        super().__init__("rrt_node")
        self.get_logger().info("INITIALIZING RRT NODE - " + NAME)
        self.clt_inflated_map = self.create_client(GetMap, '/get_inflated_map')
        while not self.clt_inflated_map.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('Esperando servicio de mapa...')
        self.grid_map = self.get_inflated_map()
        self.srv_plan_path = self.create_service(GetPlan, '/path_planning/plan_path', self.callback_rrt)
        self.pub_path = self.create_publisher(Path, '/path_planning/path', 10)
        self.pub_tree = self.create_publisher(Marker, '/path_planning/rrt_tree', 10)
        self.msg_path, self.msg_tree = Path(), self.get_tree_marker(TreeNode(0,0))
        self.timer = self.create_timer(0.5, self.callback_timer)

def main(args=None):
    rclpy.init(args=args); node = RRTNode(); rclpy.spin(node); rclpy.shutdown()

if __name__ == '__main__': main()