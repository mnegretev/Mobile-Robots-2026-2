#
# MOBILE ROBOTS - FI-UNAM, 2026-2
# PATH SMOOTHING BY GRADIENT DESCEND
#

import rclpy
from rclpy.node import Node
from nav_msgs.msg import Path
from geometry_msgs.msg import Pose, PoseStamped, Point
from navig_msgs.srv import ProcessPath
import numpy

NAME = "Saldivar Pantoja Oscar"

class PathSmoothingNode(Node):
    def smooth_path(self, Q, w1, w2, max_steps):
        P = numpy.copy(Q)
        tol     = 0.00001                   
        nabla   = numpy.full(Q.shape, float("inf"))
        epsilon = 0.1
        nabla[0], nabla[-1] = 0.0, 0.0
        
        while numpy.linalg.norm(nabla) > tol * len(P) and max_steps > 0:
            for i in range(1, len(Q) - 1):
                nabla[i] = w1 * (2 * P[i] - P[i-1] - P[i+1]) + w2 * (P[i] - Q[i])
            P = P - epsilon * nabla
            max_steps -= 1
        return P

    def callback_smooth_path(self, request, response):
        w1 = self.get_parameter('w1').get_parameter_value().double_value
        w2 = self.get_parameter('w2').get_parameter_value().double_value
        steps = self.get_parameter('steps').get_parameter_value().integer_value
        self.get_logger().info("Smoothing path with params: " + str([w1, w2, steps]))
        
        start_time = self.get_clock().now()
        Q = numpy.asarray([[p.pose.position.x, p.pose.position.y] for p in request.path.poses])
        P = self.smooth_path(Q, w1, w2, steps)
        end_time = self.get_clock().now()
        delta_ms = (end_time.nanoseconds - start_time.nanoseconds) / 1e6
        self.get_logger().info("Path smoothed after " + str(delta_ms) + " ms")
        
        # --- PARCHE DE SEGURIDAD PARA CONTENEDOR GLOBAL ---
        tiempo_actual = self.get_clock().now().to_msg()
        frame_seguro = str(request.path.header.frame_id) if request.path.header.frame_id else "map"
        
        self.msg_smooth_path.header.frame_id = frame_seguro
        self.msg_smooth_path.header.stamp = tiempo_actual
        self.msg_smooth_path.poses = []
        
        for i in range(len(request.path.poses)):
            p = PoseStamped()
            # BLINDAJE UNITARIO: Inyectamos el frame y tiempo a cada punto individual
            p.header.frame_id = frame_seguro
            p.header.stamp = tiempo_actual
            p.pose.position.x = float(P[i, 0])
            p.pose.position.y = float(P[i, 1])
            p.pose.position.z = 0.0
            p.pose.orientation.w = 1.0
            self.msg_smooth_path.poses.append(p)
            
        self.pub_smooth_path.publish(self.msg_smooth_path)
        response.processed_path = self.msg_smooth_path
        return response
            
    def __init__(self):
        super().__init__("path_smoothing_node")
        self.get_logger().info("INITIALIZING PATH SMOOTHING NODE - " + NAME)
        self.declare_parameter('w1', 0.9)
        self.declare_parameter('w2', 0.1)
        self.declare_parameter('steps', 10000)
        self.srv_smooth_path = self.create_service(ProcessPath, '/path_planning/smooth_path', self.callback_smooth_path)
        self.pub_smooth_path = self.create_publisher(Path, '/path_planning/smoothed_path', 10)
        self.msg_smooth_path = Path()
        self.msg_smooth_path.header.frame_id = "map"
            
def main(args=None):
    rclpy.init(args=args)
    path_smoothing_node = PathSmoothingNode()
    rclpy.spin(path_smoothing_node)
    path_smoothing_node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()