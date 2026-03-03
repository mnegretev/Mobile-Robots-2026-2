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
# imports nuevos -----------
import os
import csv
from datetime import datetime

NAME = "Irving Rodriguez Ruiz"

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
        while len(open_list) > 0 and (row != goal_r or col != goal_c):
            # Saca el nodo con menor f
            [_, [row, col]] = heapq.heappop(open_list)

            # Si ya lo cerramos antes (porque pudo entrar duplicado al heap), lo saltamos
            if in_closed_list[row, col]:
                continue

            in_closed_list[row, col] = True

            for [row_offset, col_offset, dist] in adjacents:
                r = row + row_offset
                c = col + col_offset

                # 1) fuera del mapa
                if r < 0 or r >= height or c < 0 or c >= width:
                    continue

                # 2) ocupada / desconocida / ya cerrada
                #    grid_map: 0 libre, 100 ocupado, -1 desconocido
                if grid_map[r, c] != 0:
                    continue
                if in_closed_list[r, c]:
                    continue

                # 3) costo acumulado g
                g = g_values[row, col] + dist + cost_map[r, c]

                # 4) heurística (euclidiana en celdas)
                h = math.sqrt((r - goal_r)**2 + (c - goal_c)**2)

                # 5) f
                f = g + h

                # 6) relajación
                if g < g_values[r, c]:
                    g_values[r, c] = g
                    f_values[r, c] = f
                    parent_nodes[r, c] = [row, col]

                    # 7) meter/actualizar en open list
                    if not in_open_list[r, c]:
                        in_open_list[r, c] = True
                    heapq.heappush(open_list, (f_values[r, c], [r, c]))
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
#----------------------------------------------------------------------------------
# Funciones agregadas
    def ejecutar_experimentos_a_star(self, start_xy, goals_xy, reps=5):
        """
        Ejecuta A* varias veces para:
          - cada goal en goals_xy
          - diagonales True/False
          - reps repeticiones

        Guarda UNA FILA POR CORRIDA en un CSV único (raw data).
        Además imprime un resumen por combinación y un resumen global en consola.
        Regresa la mejor ruta global (para visualizarla en RViz).
        """
        info = self.inflated_map.info
        res = info.resolution
        zx = info.origin.position.x
        zy = info.origin.position.y

        # Leer cost_radius real del nodo cost_map
        cost_radius = self.get_parameter('cost_radius').get_parameter_value().double_value

        # CSV único (ojo: os.getcwd() depende de dónde se ejecute ros2 run)
        workspace_root = os.getcwd()
        src_path = os.path.join(workspace_root, "src", "navigation", "path_planner", "path_planner")
        os.makedirs(src_path, exist_ok=True)
        csv_filename = os.path.join(src_path, "a_star_resultados.csv")

        # Convertimos mapas a grids (una vez)
        inflated_grid = numpy.reshape(numpy.asarray(self.inflated_map.data), (info.height, info.width))
        cost_grid     = numpy.reshape(numpy.asarray(self.cost_map.data),     (info.height, info.width))

        # Mejor GLOBAL (para dibujar)
        best_dt = None
        best_path = []
        best_params = None  # (goal, diagonals, rep)

        # Totales globales (para resumen)
        total_trials = 0
        total_success = 0

        # Start a índices
        (sx, sy) = start_xy
        start_r = int((sy - zy) / res)
        start_c = int((sx - zx) / res)

        # Si el archivo no existe, escribimos header
        file_exists = os.path.exists(csv_filename)
        with open(csv_filename, "a", newline="") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow([
                    #"trial_id",
                    "rep",
                    "start",
                    "goal",
                    "diagonals",
                    "cost_radius",
                    "success",
                    "time_ms",
                    "points"
                ])

            trial_id = 0  # contador global (tipo T4)

            for goal in goals_xy:
                (gx, gy) = goal
                goal_r = int((gy - zy) / res)
                goal_c = int((gx - zx) / res)

                for use_diagonals in [True, False]:

                    # Stats locales por combinación (solo para imprimir)
                    exitos = 0
                    min_ms = None
                    sum_ms = 0.0
                    pts_sum_ok = 0
                    pts_min_ok = None

                    for rep in range(reps):
                        trial_id += 1
                        total_trials += 1

                        t0 = self.get_clock().now()
                        path = self.a_star(
                            start_r, start_c, goal_r, goal_c,
                            inflated_grid, cost_grid, use_diagonals
                        )
                        t1 = self.get_clock().now()
                        dt_ms = (t1.nanoseconds - t0.nanoseconds) / 1e6

                        success = 1 if len(path) > 0 else 0
                        pts = len(path)
                        total_success += success

                        # Actualiza stats locales (solo si hubo éxito)
                        sum_ms += dt_ms
                        if success:
                            exitos += 1
                            pts_sum_ok += pts
                            if (min_ms is None) or (dt_ms < min_ms):
                                min_ms = dt_ms
                            if (pts_min_ok is None) or (pts < pts_min_ok):
                                pts_min_ok = pts

                            # Mejor global para visualizar
                            if (best_dt is None) or (dt_ms < best_dt):
                                best_dt = dt_ms
                                best_path = path
                                best_params = (goal, use_diagonals, rep + 1)

                        # CSV: una fila por corrida
                        writer.writerow([
                            #trial_id,
                            rep + 1,
                            start_xy,
                            goal,
                            use_diagonals,
                            cost_radius,
                            success,
                            f"{dt_ms:.3f}",
                            pts
                        ])

                        self.get_logger().info(
                            f"[A*] trial={trial_id} rep={rep+1} goal={goal} diag={use_diagonals} "
                            f"costR={cost_radius} success={success} time={dt_ms:.2f}ms pts={pts}"
                        )

                    # -------- Resumen por combinación (solo consola) --------
                    avg_ms = sum_ms / reps if reps > 0 else float("inf")
                    if exitos > 0:
                        avg_pts_ok = pts_sum_ok / exitos
                        self.get_logger().info(
                            f"goal={goal} diag={use_diagonals} costR={cost_radius} | "
                            f"exitos={exitos}/{reps} | min_ms={min_ms:.3f} | avg_ms={avg_ms:.3f} | "
                            f"pts_min={pts_min_ok} | pts_avg_ok={avg_pts_ok:.2f}"
                        )
                    else:
                        self.get_logger().info(
                            f"goal={goal} diag={use_diagonals} costR={cost_radius} | "
                            f"exitos=0/{reps} | min_ms=NA | avg_ms={avg_ms:.3f} | pts=NA"
                        )
                    self.get_logger().info("-" * 90)

        # -------- Resumen global (solo consola) --------
        if best_dt is None:
            self.get_logger().info(
                f"Resumen -> exitos: {total_success}/{total_trials} | mejor_global: NA | CSV: {csv_filename}"
            )
        else:
            (bgoal, bdiag, brep) = best_params
            self.get_logger().info(
                f"Resumen -> exitos: {total_success}/{total_trials} | "
                f"mejor_global: {best_dt:.3f} ms (goal={bgoal}, diag={bdiag}, rep={brep}) | "
                f"CSV: {csv_filename}"
            )

        self.get_logger().info(f"Resultados guardados en: {csv_filename}")
        return best_path
#----------------------------------------------------------------------------------
    #GOALS_T4 = [(0.5, 0.0), (5.0, 6.5), (10.2, 1.2)]
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
        
        # -------------------------
        run_exp = self.get_parameter('run_experiments').value

        if run_exp:
            goals = [(gx, gy)]  # SOLO el goal actual
            best_path = self.ejecutar_experimentos_a_star(
                start_xy=(sx, sy),
                goals_xy=goals,
                reps=5
            )
            path = best_path  # para visualizar algo en RViz
        else:
            # Corrida normal
            path = self.a_star(int((sy-zy)/res), int((sx-zx)/res), int((gy-zy)/res), int((gx-zx)/res),
                           inflated_grid, cost_grid, use_diagonals)   
        # -------------------------        
        # se pasó al else de arriba, Corrida normal
        #path = self.a_star(int((sy-zy)/res), int((sx-zx)/res), int((gy-zy)/res), int((gx-zx)/res),inflated_grid, cost_grid, use_diagonals)
        end_time = self.get_clock().now()
        delta_ms = (end_time.nanoseconds - start_time.nanoseconds)/1e6
        
        # ----------------------------------------------------------------------
        """
        if len(path) > 0:
            self.get_logger().info("Path planned after " + str(delta_ms) + " ms with " +  str(len(path)) + " points")
        else:
            self.get_logger().info("Cannot plan path from  " + str([sx, sy])+" to "+str([gx, gy]) + " :'(")
        """
        if not run_exp:
            if len(path) > 0:
                self.get_logger().info(f"Path planned after {delta_ms:.3f} ms with {len(path)} points")
            else:
                self.get_logger().info("Cannot plan path ...")
        else:
            self.get_logger().info(f"Benchmark A* terminado en {delta_ms:.3f} ms (ver CSV)")
        
        # -------------------------------------------------------
           
            
            
            
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
        self.declare_parameter('run_experiments', False) # Agregado ----------------
        self.declare_parameter('cost_radius', 0.0)
        
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
