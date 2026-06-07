#!/usr/bin/env python3
#
# MOBILE ROBOTS - FI-UNAM, 2026-2
# Mueve el brazo xArm6 a una pose de articulaciones fija.
# Sirve para apuntar la camara (en link6) hacia donde queramos
# y es la base de la accion 'move_arm' del sm_planner.
#
# Uso (terminal de ROS, SIN venv):
#   python3 move_arm_pose.py
# Edita la lista POSE (6 angulos en radianes) y vuelve a correr
# hasta que la camara mire a donde quieres (observa la ventana de YOLO).
#
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from control_msgs.action import FollowJointTrajectory
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from builtin_interfaces.msg import Duration

# ----------------- AJUSTA AQUI -----------------
# Orden: [joint1, joint2, joint3, joint4, joint5, joint6]  (radianes)
#  joint1 = giro de la base del brazo (mira izquierda/derecha)
#  joint2 = "hombro": positivo inclina el brazo hacia el frente/abajo
#  joint3 = "codo": dobla el antebrazo
#  joint4 = giro del antebrazo
#  joint5 = "muñeca": inclina la punta (y la camara) arriba/abajo
#  joint6 = giro de la punta
# Pose de partida sugerida (brazo doblado al frente, camara mirando adelante).
# Si algo se ve raro o al reves, cambia el signo del angulo correspondiente.
POSE = [0.0, -1.0, 0.0, 0.0, -0.5, 0.0]
MOVE_TIME = 3.0   # segundos para llegar a la pose (mas grande = mas suave)
# ------------------------------------------------

JOINT_NAMES = ['joint1', 'joint2', 'joint3', 'joint4', 'joint5', 'joint6']
ACTION_NAME = '/xarm6_traj_controller/follow_joint_trajectory'


class MoveArmPose(Node):
    def __init__(self):
        super().__init__('move_arm_pose')
        self.ac = ActionClient(self, FollowJointTrajectory, ACTION_NAME)

    def send(self, pose, move_time):
        self.get_logger().info('Esperando el servidor de accion del brazo...')
        if not self.ac.wait_for_server(timeout_sec=10.0):
            self.get_logger().error('No aparecio ' + ACTION_NAME + ' (¿esta activo el controlador?)')
            return False

        goal = FollowJointTrajectory.Goal()
        goal.trajectory = JointTrajectory()
        goal.trajectory.joint_names = JOINT_NAMES
        pt = JointTrajectoryPoint()
        pt.positions = [float(a) for a in pose]
        sec = int(move_time)
        pt.time_from_start = Duration(sec=sec, nanosec=int((move_time - sec) * 1e9))
        goal.trajectory.points = [pt]

        self.get_logger().info('Mandando pose: ' + str(pose))
        send_future = self.ac.send_goal_async(goal)
        rclpy.spin_until_future_complete(self, send_future)
        gh = send_future.result()
        if gh is None or not gh.accepted:
            self.get_logger().error('La meta fue rechazada por el controlador')
            return False

        res_future = gh.get_result_async()
        rclpy.spin_until_future_complete(self, res_future)
        result = res_future.result().result
        # error_code 0 = SUCCESSFUL en FollowJointTrajectory
        if result.error_code == 0:
            self.get_logger().info('Brazo en la pose objetivo.')
            return True
        self.get_logger().warn('Termino con error_code=' + str(result.error_code) +
                               ' (' + str(result.error_string) + ')')
        return False


def main(args=None):
    rclpy.init(args=args)
    node = MoveArmPose()
    try:
        node.send(POSE, MOVE_TIME)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()