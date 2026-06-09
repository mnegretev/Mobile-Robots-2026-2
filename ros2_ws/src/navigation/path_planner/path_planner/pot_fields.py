#
# MOBILE ROBOTS - FI-UNAM, 2026-2
# OBSTACLE AVOIDANCE BY POTENTIAL FIELDS
#
# Instructions:
# Complete the code to implement obstacle avoidance by potential fields
# using the attractive and repulsive fields technique.
# Tune the constants alpha and beta to get a smooth movement. 
#

import rclpy
from rclpy.node import Node
#from rclpy.duration import Duration
from std_msgs.msg import Bool
from geometry_msgs.msg import Twist, PoseStamped, Point, Vector3
from visualization_msgs.msg import MarkerArray, Marker
from sensor_msgs.msg import LaserScan
from tf2_ros import TransformException
from tf2_ros.buffer import Buffer
from tf2_ros.transform_listener import TransformListener
from builtin_interfaces.msg import Duration
from ament_index_python.packages import get_package_share_directory
import math
import numpy
import time

NAME = "Zambrano Miranda Isaac Jaciel"

SM_INIT = 0
SM_WAIT_FOR_NEW_GOAL = 10
SM_POT_FIELDS = 40

class PotFieldsNode(Node):

    def calculate_control(self, goal_x, goal_y, alpha, beta):
        v_max = 0.5
        w_max = 0.8
        # error_d: distancia al goal en frame del robot
        # error_a: angulo al goal en frame del robot
        error_d = math.sqrt(goal_x**2 + goal_y**2)
        error_a = math.atan2(goal_y, goal_x)
        # Ley de control:
        # v = v_max * exp(-error_a^2 / alpha)  -> rapido cuando apunta al goal
        # w = w_max * (2/(1+exp(-error_a/beta)) - 1)  -> gira hacia el goal
        v = v_max * math.exp(-error_a * error_a / alpha)
        w = w_max * (2.0 / (1.0 + math.exp(-error_a / beta)) - 1.0)
        return [v, w]

    def attraction_force(self, goal_x, goal_y, eta):
        # Fuerza atractiva: proporcional al vector hacia el goal
        # Fa = eta * (goal - robot)
        # En frame del robot, robot esta en origen, goal en (goal_x, goal_y)
        force_x = eta * goal_x
        force_y = eta * goal_y
        return numpy.asarray([force_x, force_y])

    def rejection_force(self, laser_readings, zeta, d0):
        N = len(laser_readings)
        if N == 0:
            return numpy.asarray([0.0, 0.0])
        force_x, force_y = 0.0, 0.0
        count = 0
        for dist, angle in laser_readings:
            # Ignorar lecturas invalidas
            if math.isinf(dist) or math.isnan(dist) or dist <= 0:
                continue
            if dist > d0:
                # Obstaculo fuera del rango de influencia
                continue
            # Fuerza repulsiva segun campo potencial:
            # Fr = zeta * (1/d - 1/d0) * (1/d^2) * direccion_unitaria_desde_obstaculo
            # direccion desde obstaculo hacia robot = -direccion al obstaculo
            obs_x = dist * math.cos(angle)
            obs_y = dist * math.sin(angle)
            # Vector del obstaculo al robot (negativo del vector al obstaculo)
            dir_x = -obs_x / dist
            dir_y = -obs_y / dist
            magnitud = zeta * (1.0/dist - 1.0/d0) * (1.0 / (dist * dist))
            force_x += magnitud * dir_x
            force_y += magnitud * dir_y
            count += 1
        if count > 0:
            force_x /= count
            force_y /= count
        return numpy.asarray([force_x, force_y])

    def move_by_pot_fields(self, global_goal_x, global_goal_y, epsilon, tol, eta, zeta, d0, alpha, beta):
        goal_x, goal_y = self.get_goal_point_wrt_robot(global_goal_x, global_goal_y)
        dist_to_goal = math.sqrt(goal_x**2 + goal_y**2)

        while dist_to_goal > tol and rclpy.ok():
            # Fuerza atractiva hacia el goal
            Fa = self.attraction_force(goal_x, goal_y, eta)
            # Fuerza repulsiva de obstaculos (laser)
            Fr = self.rejection_force(self.laser_readings, zeta, d0)
            # Fuerza resultante
            F = Fa + Fr
            # Siguiente posicion deseada por gradiente descendente
            next_x = -epsilon * F[0]
            next_y = -epsilon * F[1]
            # Senales de control
            v, w = self.calculate_control(next_x, next_y, alpha, beta)
            # Publicar velocidad y marcadores
            self.publish_speed_and_forces(v, w, Fa, Fr, F)
            # Actualizar posicion del goal en frame del robot
            goal_x, goal_y = self.get_goal_point_wrt_robot(global_goal_x, global_goal_y)
            dist_to_goal = math.sqrt(goal_x**2 + goal_y**2)

        return

    def get_goal_point_wrt_robot(self, goal_x, goal_y):
        self.robot_p, self.robot_a = self.get_robot_pose()
        delta_x = goal_x - self.robot_p[0]
        delta_y = goal_y - self.robot_p[1]
        goal_x =  delta_x*math.cos(self.robot_a) + delta_y*math.sin(self.robot_a)
        goal_y = -delta_x*math.sin(self.robot_a) + delta_y*math.cos(self.robot_a)
        return [goal_x, goal_y]
    
    def publish_speed_and_forces(self, v, w, Fa, Fr, F):        
        self.pub_cmd_vel.publish(Twist(linear=Vector3(x=v), angular=Vector3(z=w)))
        mrks = MarkerArray()
        mrks.markers.append(self.get_force_marker(Fa[0], Fa[1], [0.0, 0.0, 1.0, 1.0], 0))
        mrks.markers.append(self.get_force_marker(Fr[0], Fr[1], [1.0, 0.0, 0.0, 1.0], 1))
        mrks.markers.append(self.get_force_marker(F [0], F [1], [0.0, 0.6, 0.0, 1.0], 2))
        self.pub_markers.publish(mrks)
        rclpy.spin_once(self)
        time.sleep(0.001)

    def get_force_marker(self, force_x, force_y, color, id):
        mrk = Marker()
        mrk.header.frame_id = "base_link"
        mrk.header.stamp = self.get_clock().now().to_msg()
        mrk.lifetime = Duration(sec=0, nanosec=100000)
        mrk.ns = "pot_fields"
        mrk.id = id
        mrk.type = Marker.ARROW
        mrk.action = Marker.ADD
        mrk.pose.orientation.w = 1.0
        mrk.color.r, mrk.color.g, mrk.color.b, mrk.color.a = color
        mrk.scale.x, mrk.scale.y, mrk.scale.z = [0.07, 0.1, 0.15]
        mrk.points.append(Point(x=0.0, y=0.0))
        mrk.points.append(Point(x=-force_x, y=-force_y))
        return mrk

    def get_robot_pose(self):
        try:
            t = self.tf_buffer.lookup_transform("map","base_link", rclpy.time.Time())
            robot_x = t.transform.translation.x
            robot_y = t.transform.translation.y
            robot_pose = numpy.asarray([robot_x, robot_y])
            robot_a = math.atan2(t.transform.rotation.z, t.transform.rotation.w)*2
        except TransformException as ex:
            print("Could not get robot pose")
            robot_pose = numpy.asarray([0.0,0.0])
            robot_a = 0.0
        return robot_pose, robot_a

    def callback_scan(self, msg):
        self.laser_readings = [[msg.ranges[i], msg.angle_min+i*msg.angle_increment] for i in range(len(msg.ranges))]

    def callback_pot_fields_goal(self, msg):
        self.global_goal_x, self.global_goal_y = msg.pose.position.x, msg.pose.position.y
        self.new_goal_pose = True    
        
    def __init__(self):
        print("INITIALIZING POTENTIAL FIELDS NODE - ", NAME)
        super().__init__("pot_fields_node")
        self.new_goal_pose = False
        self.laser_readings = []
        self.robot_p = numpy.asarray([0.0, 0.0])
        self.robot_a = 0.0
        self.global_goal_x = 0.0
        self.global_goal_y = 0.0
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)
        self.declare_parameter('epsilon', 0.5)
        self.declare_parameter('tol', 0.5)
        self.declare_parameter('eta', 1.0)
        self.declare_parameter('zeta',1.0)
        self.declare_parameter('d0',  3.0)
        self.declare_parameter('alpha',0.5)
        self.declare_parameter('beta', 0.5)
        self.sub_scan = self.create_subscription(LaserScan, '/scan', self.callback_scan, 1)
        self.sub_goal = self.create_subscription(PoseStamped, '/goal_pose', self.callback_pot_fields_goal, 1)
        self.pub_cmd_vel = self.create_publisher(Twist, '/cmd_vel', 1)
        self.pub_markers = self.create_publisher(MarkerArray, '/navigation/pot_field_markers', 1)

    def spin(self):
        robot_pose_tf_ready = False
        print("Waiting for robot pose tf to be available")
        while rclpy.ok() and not robot_pose_tf_ready:
            try:
                t = self.tf_buffer.lookup_transform("map","base_link", rclpy.time.Time())
                robot_pose_tf_ready = True
            except TransformException as ex:
                robot_pose_tf_ready = False
            rclpy.spin_once(self)
            time.sleep(0.001)
        print("Robot pose tf is now available")

        state = SM_INIT
        while rclpy.ok():
            if state == SM_INIT:
                print("Ready to execute new goal pose. Waiting for new goal...")
                state = SM_WAIT_FOR_NEW_GOAL
            elif state == SM_WAIT_FOR_NEW_GOAL:
                if self.new_goal_pose:
                    self.new_goal_pose = False
                    state = SM_POT_FIELDS
            elif state == SM_POT_FIELDS:
                epsilon = self.get_parameter('epsilon').get_parameter_value().double_value
                tol     = self.get_parameter('tol').get_parameter_value().double_value
                eta     = self.get_parameter('eta').get_parameter_value().double_value
                zeta    = self.get_parameter('zeta').get_parameter_value().double_value
                d0      = self.get_parameter('d0').get_parameter_value().double_value
                alpha   = self.get_parameter('alpha').get_parameter_value().double_value
                beta    = self.get_parameter('beta').get_parameter_value().double_value
                print("Moving to goal point " + str([self.global_goal_x, self.global_goal_y]) + " by potential fields")
                print("Parameters [epsilon, tol, eta, zeta, d0, alpha, beta]:", [epsilon, tol, eta, zeta, d0, alpha, beta])
                self.move_by_pot_fields(self.global_goal_x, self.global_goal_y, epsilon, tol, eta, zeta, d0, alpha, beta)
                self.pub_cmd_vel.publish(Twist())
                print("Goal point reached")
                state = SM_INIT
            rclpy.spin_once(self)
            time.sleep(0.001)


def main(args=None):
    rclpy.init(args=args)
    pot_fields_node = PotFieldsNode()
    pot_fields_node.spin()
    pot_fields_node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
