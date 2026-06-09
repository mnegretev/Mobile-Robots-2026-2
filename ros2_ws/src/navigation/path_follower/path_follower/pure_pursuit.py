#
# MOBILE ROBOTS - FI-UNAM, 2026-2
# PATH FOLLOWING BY PURE PURSUIT
#
# Instructions:
# Write the code necessary to move the robot along a given path.
# Consider a differential base. Max linear and angular speeds
# must be 0.8 and 1.0 respectively.
#

import rclpy
from rclpy.node import Node
from rclpy.duration import Duration
from std_msgs.msg import Bool
from nav_msgs.msg import Path
from nav_msgs.srv import GetPlan
from navig_msgs.srv import ProcessPath
from geometry_msgs.msg import Twist, PoseStamped, Pose, Point
from tf2_ros import TransformException
from tf2_ros.buffer import Buffer
from tf2_ros.transform_listener import TransformListener
from ament_index_python.packages import get_package_share_directory
import math
import numpy

NAME = "Claudia Eunce Vazquez Rios"

# === DICCIONARIO ESTRUCTURADO DE COORDENADAS COSECHADAS ===
NAV_TARGETS = {
    "dormitorio": {
        "root": [-0.926, 0.674, 0.0471],
        "cama": [-3.85, 2.1, 0.00378],
        "ventana": [-6.3, 1.19, 0.00022],
        "silla": [-5.99, -2.08, 0.00184],
        "pelota": [-3.86, -2.55, 0.00282],
        "cuadro_grupo": [-3.99, 0.705, 0.00416],
        "cuadro_persona": [-4.15, -0.441, -0.0000896],
        "entrada": [-0.142, 0.519, 0.0329],
        "mesa_noche": [-2.04, 3.79, 0.00517],
        "armario": [-1.41, 3.68, 0.00203]
    },
    "sala": {
        "root": [2.79, 0.544, 0.00241],
        "comedor": [1.8, 5.09, 0.0017],
        "gym": [5.64, 3.65, 0.00425],
        "tv": [2.94, -2.67, -0.000328],
        "cuadro_persona": [0.954, -3.19, 0.00249],
        "varios_cuadros": [5.07, -3.4, 0.00149],
        "aire_acondicionado": [0.358, -2.84, -0.00238],
        "zapateria": [6.55, -3.08, 0.00104]
    },
    "cocina": {
        "root": [10.4, -2.91, 0.0049],
        "puerta": [8.16, -3.56, 0.00274],
        "comedor": [10.1, 2.56, 0.0026],
        "refrigerador": [10.2, 0.616, 0.0328],
        "ventana": [11.1, 2.96, 0.00149],
        "cuadro_mujer": [10.0, 4.12, -0.00103],
        "cuadro_hombre": [8.05, 4.18, 0.202]
    }
}

VALID_ACTIONS = ["ve", "ve al", "camina a", "dirígete a", "desplázate a", "ir al", "ir a la", "ir"]
CANCEL_KEYWORDS = ["para", "detente", "alto", "cancela", "stop", "parar"]

SM_INIT = 0
SM_WAIT_FOR_NEW_GOAL = 10
SM_PLAN_PATH = 20
SM_SMOOTH_PATH = 30
SM_FOLLOWING_PATH = 40
SM_SAVE_DATA = 50

class PurePursuitNode(Node):
    def parse_voice_command(self, command_text):
        command = command_text.lower()
        
        # --- VERIFICACIÓN DE COMANDOS DE CANCELACIÓN ---
        if any(keyword in command for keyword in CANCEL_KEYWORDS):
            return "CANCEL", "Orden de detención recibida."
        
        has_valid_action = any(action in command for action in VALID_ACTIONS)
        if not has_valid_action:
            return None, "Acción inválida o incoherente para el robot."

        selected_room = None
        if "dormitorio" in command or "habitación" in command or "cuarto" in command or "cama" in command:
            selected_room = "dormitorio"
        elif "sala" in command:
            selected_room = "sala"
        elif "cocina" in command:
            selected_room = "cocina"

        if selected_room:
            for item, coords in NAV_TARGETS[selected_room].items():
                item_name = item.replace("_", " ")
                if item_name in command or (item == "root" and selected_room in command):
                    return coords, f"Destino localizado: {item_name} en {selected_room}."
        else:
            matches = []
            for room, items in NAV_TARGETS.items():
                for item, coords in items.items():
                    item_name = item.replace("_", " ")
                    if item_name in command:
                        matches.append((coords, room, item_name))
            
            if len(matches) == 1:
                return matches[0][0], f"Destino único localizado: {matches[0][2]}."
            elif len(matches) > 1:
                return None, "Ambigüedad detectada. Especifica la habitación."

        return None, "El destino no está registrado en el mapa semántico."

    def calculate_control(self, robot_x, robot_y, robot_a, goal_x, goal_y, alpha, beta, v_max, w_max):
        v, w = 0, 0
        theta_goal = math.atan2(goal_y - robot_y, goal_x - robot_x)
        error_a = theta_goal - robot_a
        error_a = (error_a + math.pi) % (2 * math.pi) - math.pi
        
        v = v_max * math.exp(-error_a * error_a / alpha)
        w = w_max * (2 / (1 + math.exp(-error_a / beta)) - 1)
        
        v = max(0.0, min(v, v_max))
        w = max(-w_max, min(w, w_max))
        return [v, w]

    def pure_pursuit(self, path, alpha, beta, v_max, w_max, tol):
        idx = 0
        Pg = path[idx]
        Pr, robot_a = self.get_robot_pose()
        
        # El bucle correrá siempre y cuando no se active la bandera de aborto voluntario
        while numpy.linalg.norm(path[-1] - Pr) > tol and rclpy.ok() and not self.abort_path:
            v, w = self.calculate_control(Pr[0], Pr[1], robot_a, Pg[0], Pg[1], alpha, beta, v_max, w_max)
            self.publish_and_save_data(Pr[0], Pr[1], robot_a, Pg[0], Pg[1], v, w)
            
            Pr, robot_a = self.get_robot_pose()
            
            if numpy.linalg.norm(Pg - Pr) < 0.25:
                idx = min(len(path) - 1, idx + 1)
                Pg = path[idx]
        return

    def publish_and_save_data(self, robot_x, robot_y, robot_a, goal_x, goal_y, v, w):
        self.nav_data.append([robot_x, robot_y, robot_a, goal_x, goal_y, v, w])
        msg = Twist()
        msg.linear.x = v
        msg.angular.z = w
        self.pub_cmd_vel.publish(msg)
        rclpy.spin_once(self, timeout_sec=0.001)
        self.get_clock().sleep_for(Duration(seconds=0.005))

    def get_robot_pose(self):
        try:
            t = self.tf_buffer.lookup_transform("map", "base_link", rclpy.time.Time())
            robot_x = t.transform.translation.x
            robot_y = t.transform.translation.y
            robot_pose = numpy.asarray([robot_x, robot_y])
            
            q = t.transform.rotation
            siny_cosp = 2 * (q.w * q.z + q.x * q.y)
            cosy_cosp = 1 - 2 * (q.y * q.y + q.z * q.z)
            robot_a = math.atan2(siny_cosp, cosy_cosp)
            
            self.robot_pose = robot_pose
            self.robot_a = robot_a
        except TransformException:
            robot_pose = self.robot_pose
            robot_a = self.robot_a
        return robot_pose, robot_a

    def callback_goal_pose(self, msg):
        self.goal_pose = numpy.asarray([msg.pose.position.x, msg.pose.position.y])
        self.get_logger().info("Received new goal pose from RViz: " + str(self.goal_pose))
        self.new_goal_pose = True
        self.abort_path = False

    def callback_voice_command(self, msg):
        self.get_logger().info(f"Processing voice input: '{msg.data}'")
        coords, response_text = self.parse_voice_command(msg.data)
        
        if coords == "CANCEL":
            self.get_logger().warn("🚨 PARO DE EMERGENCIA MANDADO POR VOZ. CANCELANDO...")
            self.abort_path = True
            # Mandamos detener los motores inmediatamente desde el callback
            self.pub_cmd_vel.publish(Twist())
        elif coords is not None:
            self.get_logger().info(f"🎉 {response_text}")
            self.goal_pose = numpy.asarray([coords[0], coords[1]])
            self.new_goal_pose = True
            self.abort_path = False
        else:
            self.get_logger().warn(f"❌ Comando rechazado: {response_text}")

    def _init_(self):
        super()._init_("pure_pursuit_node")
        self.get_logger().info("INITIALIZING PATH FOLLOWER BY PURE PURSUIT NODE ...")
        self.nav_data = []
        self.data_file = get_package_share_directory('path_follower') + "/data.txt"
        self.robot_pose = numpy.asarray([0.0, 0.0])
        self.robot_a = 0.0
        self.new_goal_pose = False
        self.goal_pose = numpy.asarray([0.0, 0.0])
        self.abort_path = False # Bandera de interrupción voluntaria
        
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)
        
        # --- PARÁMETROS CALIBRADOS MODO RÁPIDO SEGURO ---
        self.declare_parameter('v_max', 0.45)
        self.declare_parameter('w_max', 0.85)
        self.declare_parameter('alpha', 0.65)
        self.declare_parameter('beta',  0.45)
        self.declare_parameter('tol',  0.30)
        
        self.clt_plan_path = self.create_client(GetPlan, '/path_planning/plan_path')
        self.clt_smooth_path = self.create_client(ProcessPath, '/path_planning/smooth_path')
        self.pub_cmd_vel = self.create_publisher(Twist, '/cmd_vel', 1)
        self.pub_goal_reached = self.create_publisher(Bool, '/navigation/goal_reached', 1)
        
        self.sub_goal_pose = self.create_subscription(PoseStamped, '/goal_pose', self.callback_goal_pose, 1)
        self.sub_voice = self.create_subscription(String, '/voice_command', self.callback_voice_command, 1)

    def spin(self):
        self.get_logger().info("Waiting for plan path service...")
        while not self.clt_plan_path.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('Waiting for plan path service...')
        self.get_logger().info("Plan path service is now available...")
        
        clt_timeout = 3
        self.get_logger().info("Waiting for smooth path service...")
        while not self.clt_smooth_path.wait_for_service(timeout_sec=0.5) and clt_timeout > 0:
            self.get_logger().info("Waiting for smooth path service...")
            clt_timeout -= 1
            
        self.get_logger().info("Waiting for robot pose tf to be available")
        robot_pose_tf_ready = False
        while rclpy.ok() and not robot_pose_tf_ready:
            try:
                now = rclpy.time.Time()
                if self.tf_buffer.can_transform("map", "base_link", now, rclpy.duration.Duration(seconds=0.1)):
                    self.tf_buffer.lookup_transform("map", "base_link", now)
                    robot_pose_tf_ready = True
            except TransformException:
                robot_pose_tf_ready = False
            rclpy.spin_once(self)
            self.get_clock().sleep_for(Duration(seconds=0.02))
        self.get_logger().info("Robot pose tf is now available")

        state = SM_INIT
        while rclpy.ok():
            robot_p, robot_a = self.get_robot_pose()
            if state == SM_INIT:
                self.get_logger().info("Ready to execute new path. Waiting for new goal...")
                state = SM_WAIT_FOR_NEW_GOAL

            elif state == SM_WAIT_FOR_NEW_GOAL:
                if self.new_goal_pose:
                    self.new_goal_pose = False
                    state = SM_PLAN_PATH

            elif state == SM_PLAN_PATH:
                if self.abort_path: # Si cancelan mientras planea, aborta al inicio
                    state = SM_INIT
                    continue
                self.get_logger().info("Trying to plan path from " + str(self.robot_pose) + " to " + str(self.goal_pose))
                request = GetPlan.Request()
                request.start.pose.position.x = self.robot_pose[0]
                request.start.pose.position.y = self.robot_pose[1]
                request.goal.pose.position.x = self.goal_pose[0]
                request.goal.pose.position.y = self.goal_pose[1]
                future = self.clt_plan_path.call_async(request)
                rclpy.spin_until_future_complete(self, future)
                path = future.result().plan
                self.get_logger().info("Path planned with " + str(len(path.poses)) + " points")
                state = SM_SMOOTH_PATH

            elif state == SM_SMOOTH_PATH:
                if self.abort_path:
                    state = SM_INIT
                    continue
                req = ProcessPath.Request()
                req.path = path
                if self.clt_smooth_path.wait_for_service(timeout_sec=0.1):
                    future = self.clt_smooth_path.call_async(req)
                    rclpy.spin_until_future_complete(self, future)
                    path = future.result().processed_path
                    self.get_logger().info("Path smoothed successfully")
                else:
                    self.get_logger().info("Smooth path service is not available")
                state = SM_FOLLOWING_PATH

            elif state == SM_FOLLOWING_PATH:
                v_max = self.get_parameter('v_max').get_parameter_value().double_value
                w_max = self.get_parameter('w_max').get_parameter_value().double_value
                alpha = self.get_parameter('alpha').get_parameter_value().double_value
                beta  = self.get_parameter('beta').get_parameter_value().double_value
                tol   = self.get_parameter('tol').get_parameter_value().double_value
                self.get_logger().info("Following path with tuned parameters.")
                path_points = [numpy.asarray([p.pose.position.x, p.pose.position.y]) for p in path.poses]
                
                # Ejecuta el bucle. Si dices "detente", saldrá de inmediato de pure_pursuit()
                self.pure_pursuit(path_points, alpha, beta, v_max, w_max, tol)
                
                # Forzamos frenado físico de los motores de la base móvil mbot
                self.pub_cmd_vel.publish(Twist())
                
                if self.abort_path:
                    self.get_logger().warn("Ruta cancelada exitosamente en movimiento.")
                    state = SM_INIT
                else:
                    self.pub_goal_reached.publish(Bool(data=True))
                    self.get_logger().info("Global goal point reached")
                    state = SM_SAVE_DATA

            elif state == SM_SAVE_DATA:
                s = ""
                for d in self.nav_data:
                    s += str(d[0]) + "," + str(d[1]) + "," + str(d[2]) + "," + str(d[3]) + "," + str(d[4]) + "," + str(d[5]) + "," + str(d[6]) + "\n"
                try:
                    with open(self.data_file, "w") as f:
                        f.write(s)
                except Exception as e:
                    self.get_logger().error(f"Could not save telemetry data: {e}")
                state = SM_INIT
                
            rclpy.spin_once(self)
            self.get_clock().sleep_for(Duration(seconds=0.005))

def main(args=None):
    rclpy.init(args=args)
    pure_pursuit_node = PurePursuitNode()
    pure_pursuit_node.spin()
    pure_pursuit_node.destroy_node()
    rclpy.shutdown()

if _name_ == '_main_':
    main()