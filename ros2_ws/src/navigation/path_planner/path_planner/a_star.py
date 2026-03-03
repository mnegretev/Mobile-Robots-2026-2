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

NAME = "Jose Augusto Garcia Mendoza"

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
        #
        # TODO:
        # Implement the A* algorithm for path planning
        # Map is considered to be a 2D array and start and goal positions
        # are given as row-col pairs. You can follow these steps:
        #
        # WHILE open list is not empty and current is different from goal:
        #     Get current node [row,col] from open list (see heapq.heappop function)
        #     Mark current node as 'in_closed_list'
        #     For [r,c,cost] in adjacent nodes:
        #         Get r,c indices of neighbours of current node (check content of adjacents)
        #         Discard if r,c is out of map, occupied, unknonw or in closed list, and continue
        #         get a g-value g as: g-value of current node + dist + cost of neighbour r,c
        #         Calculate heuristic 
        #         Calculate f-value
        #         IF g < g_value of neighbour r,c:
        #             set g as g_value of neighbour r,c
        #             set f as f_value of neighbour r,c
        #             SET current node row,col as parent of neighbour r,c
        #         If neighbour r,c is not in open list:
        #             mark r,c as 'in_open_list'
        #             add r,c to open list (check heapq.heappush)
        #
        
        #
        # END OF WHILE
        #
                # ---------------------------
        # A* (grid: filas/columnas)
        # ---------------------------

        # Caso trivial
        if start_r == goal_r and start_c == goal_c:
            return [[start_r, start_c]]

        # Si inicio o meta son no transitables, no hay ruta
        if grid_map[start_r, start_c] < 0 or grid_map[start_r, start_c] > 50:
            return []
        if grid_map[goal_r, goal_c] < 0 or grid_map[goal_r, goal_c] > 50:
            return []

        # Heurística (h): Euclidiana si hay diagonales; Manhattan si no
        def heuristic(r, c):
            if use_diagonals:
                return math.hypot(goal_r - r, goal_c - c)
            return abs(goal_r - r) + abs(goal_c - c)

        # Inicializa f del nodo inicial para evitar pops “viejos” al inicio
        f_values[start_r, start_c] = heuristic(start_r, start_c)

        # Nodo actual (se actualiza con heappop)
        row, col = start_r, start_c

        # WHILE open list is not empty and current is different from goal:
        while len(open_list) > 0 and not (row == goal_r and col == goal_c):

            # Get current node [row,col] from open list
            current_f, [row, col] = heapq.heappop(open_list)

            # Si ya fue cerrado, ignora esta entrada (heapq puede tener duplicados)
            if in_closed_list[row, col]:
                continue

            # Si esta entrada no corresponde al mejor f conocido, ignora
            if current_f > f_values[row, col]:
                continue

            # Mark current node as 'in_closed_list'
            in_closed_list[row, col] = True
            in_open_list[row, col] = False

            # For [r,c,cost] in adjacent nodes:
            for [dr, dc, move_cost] in adjacents:

                # Get indices of neighbour
                nr = row + dr
                nc = col + dc

                # Discard if out of map
                if nr < 0 or nr >= height or nc < 0 or nc >= width:
                    continue

                # Discard if occupied, unknown or in closed list
                if in_closed_list[nr, nc]:
                    continue

                cell = grid_map[nr, nc]
                if cell < 0 or cell > 50:
                    continue

                # g = g(current) + dist + cost(neighbour)
                # dist ~ move_cost (1 o sqrt(2)); cost(neighbour) lo tomamos del cost_map normalizado
                extra_cost = float(cost_map[nr, nc]) / 100.0
                g = g_values[row, col] + float(move_cost) + extra_cost

                # Calculate heuristic and f
                h = heuristic(nr, nc)
                f = g + h

                # IF g < g_value of neighbour:
                if g < g_values[nr, nc]:
                    g_values[nr, nc] = g
                    f_values[nr, nc] = f
                    parent_nodes[nr, nc] = [row, col]

                    # If neighbour is not in open list, add it
                    # (aunque ya esté, se inserta de nuevo; se filtran duplicados al hacer pop)
                    if not in_open_list[nr, nc]:
                        in_open_list[nr, nc] = True
                    heapq.heappush(open_list, (f, [nr, nc]))
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
