#
# MOBILE ROBOTS - FI-UNAM, 2026-2
# INVERSE KINEMATICS BY NEWTON-RAPHSON
#
# Instructions:
# Write the code necessary to solve the inverse kinematics problem
# using the Newton-Raphson method.
# MODIFY ONLY THE SECTIONS MARKED WITH THE 'TODO' COMMENT
#
import rclpy
from rclpy.node import Node
from manip_msgs.srv import *
import numpy
import math

NAME = "DOMINGUEZ PALACIOS JESÚS ALEJANDRO"

H0 = [[1.0, 0.0, 0.0, 0.000], # link1 to link_base, joint rotates on Z
      [0.0, 1.0, 0.0, 0.000],
      [0.0, 0.0, 1.0, 0.267],
      [0.0, 0.0, 0.0, 1.000]]

H1 = [[1.0,  0.0, 0.0, 0.0], #link2 to link1, joint rotates on Z
      [0.0,  0.0, 1.0, 0.0],
      [0.0, -1.0, 0.0, 0.0],
      [0.0,  0.0, 0.0, 1.0]]

H2 = [[1.0, 0.0, 0.0,  0.0535], #link3 to link2, joint rotates on Z
      [0.0, 1.0, 0.0, -0.2845],
      [0.0, 0.0, 1.0,  0.000],
      [0.0, 0.0, 0.0,  1.000]]

H3 = [[1.0,  0.0, 0.0, 0.0775], #link4 to link3, joint rotates on Z
      [0.0,  0.0, 1.0, 0.3425],
      [0.0, -1.0, 0.0, 0.000],
      [0.0,  0.0, 0.0, 1.000]]

H4 = [[1.0, 0.0,  0.0, 0.000], #link5 to link4, joint rotates on Z
      [0.0, 0.0, -1.0, 0.000],
      [0.0, 1.0,  0.0, 0.000],
      [0.0, 0.0,  0.0, 1.000]]

H5 = [[1.0,  0.0, 0.0, 0.076], #link6 to link5, joint rotates on Z
      [0.0,  0.0, 1.0, 0.097],
      [0.0, -1.0, 0.0, 0.000],
      [0.0,  0.0, 0.0, 1.000]]

H6 = [[1.0, 0.0, 0.0, 0.000], #link6 to link_tcp (final effector), fixed joint
      [0.0, 1.0, 0.0, 0.000],
      [0.0, 0.0, 1.0, 0.172],
      [0.0, 0.0, 0.0, 1.000]]

Hs = [numpy.asarray(H0), numpy.asarray(H1), numpy.asarray(H2),
     numpy.asarray(H3), numpy.asarray(H4), numpy.asarray(H5),
     numpy.asarray(H6)]

class IKNewtonRaphsonNode(Node):
    def matrix_to_euler_xyz(self, R):
        # Calculate pitch (sy)
        sy = numpy.sqrt(R[0, 0] * R[0, 0] + R[1, 0] * R[1, 0])
    
        singular = sy < 1e-6 # Check for gimbal lock
    
        if not singular:
            x = numpy.arctan2(R[2, 1], R[2, 2])
            y = numpy.arctan2(-R[2, 0], sy)
            z = numpy.arctan2(R[1, 0], R[0, 0])
        else:
            # Gimbal lock case
            x = numpy.arctan2(-R[1, 2], R[1, 1])
            y = numpy.arctan2(-R[2, 0], sy)
            z = 0
            
        return x,y,z

    def forward_kinematics(self, Q):
        #
        # TODO:
        # Calculate the forward kinematics given the set of six angles 'q'
        #
        H = numpy.identity(4)
        for i in range(len(Q)):
            c = math.cos(Q[i])
            s = math.sin(Q[i])
            Rz = numpy.asarray([[c, -s, 0.0, 0.0],
                                [s,  c, 0.0, 0.0],
                                [0.0, 0.0, 1.0, 0.0],
                                [0.0, 0.0, 0.0, 1.0]])
            H = H @ Hs[i] @ Rz
        H = H @ Hs[6]
        x = H[0, 3]
        y = H[1, 3]
        z = H[2, 3]
        R, P, Y = self.matrix_to_euler_xyz(H[0:3, 0:3])
        return numpy.asarray([x, y, z, R, P, Y])

    def jacobian(self, Q):
        delta_q = 0.000001
        Q = numpy.asarray(Q, dtype=float)
        n = len(Q)
        J = numpy.zeros((6, n))
        #
        # TODO:
        # Calculate the Jacobian evaluated in the point Q
        # Use the numeric approximation:   f'(x) = (f(x+delta) - f(x-delta))/(2*delta)
        #
        for i in range(n):
            q_next = numpy.copy(Q)
            q_prev = numpy.copy(Q)
            q_next[i] += delta_q
            q_prev[i] -= delta_q
            J[:, i] = (self.forward_kinematics(q_next) - self.forward_kinematics(q_prev)) / (2.0 * delta_q)
        return J
        
    def inverse_kinematics(self, Xd, init_guess=numpy.zeros(7), max_iter=2000):
        Xd = numpy.asarray(Xd)
        Q = numpy.asarray(init_guess, dtype=float)
        iterations = 0
        TOL = 0.00001

        #
        # TODO:
        # Solve the IK problem given a desired configuration.
        # Use the Newton-Raphson method for root finding.
        #
        X = self.forward_kinematics(Q)
        error = X - Xd
        # Ensure orientation angles of error are in (-pi, pi]
        for i in range(3, 6):
            while error[i] >   math.pi: error[i] -= 2 * math.pi
            while error[i] <= -math.pi: error[i] += 2 * math.pi

        while numpy.linalg.norm(error) > TOL and iterations < max_iter:
            J = self.jacobian(Q)
            Q = Q - numpy.linalg.pinv(J) @ error
            # Ensure all angles q are in [-pi, pi]
            for i in range(len(Q)):
                while Q[i] >  math.pi: Q[i] -= 2 * math.pi
                while Q[i] < -math.pi: Q[i] += 2 * math.pi
            X = self.forward_kinematics(Q)
            error = X - Xd
            for i in range(3, 6):
                while error[i] >   math.pi: error[i] -= 2 * math.pi
                while error[i] <= -math.pi: error[i] += 2 * math.pi
            iterations += 1
        
        success = iterations < max_iter
        if success:
            self.get_logger().info("IK solved after " + str(iterations) + " steps. Q=" + str(Q))
        else:
            self.get_logger().info("Cannot solve IK")
        return success, Q

    def callback_ik_pose2pose(self, req, resp):
        N = self.get_parameter('N').get_parameter_value().integer_value
        Xd = [req.x, req.y, req.z, req.roll, req.pitch, req.yaw]
        self.get_logger().info("Calculating IK for " +  str(Xd) + "with max " + str(N) + " iterations and Qo=" + str(req.initial_guess))
        success, Q = self.inverse_kinematics(Xd, req.initial_guess, N)
        resp.q = Q if success else []
        return resp
    
    def __init__(self):
        super().__init__("inverse_kinematics")
        self.get_logger().info("INITIALIZING INVERSE KINEMATICS BY NEWTON-RAPHSON NODE - " + NAME)
        self.declare_parameter('N', 100)
        self.srv_smooth_path = self.create_service(InverseKinematicsPose2Pose, '/manipulation/ik_pose2pose', self.callback_ik_pose2pose)

def main(args=None):
    rclpy.init(args=args)
    ik_node = IKNewtonRaphsonNode()
    rclpy.spin(ik_node)
    ik_node.destroy_node()
    rclpy.shutdown()
    
    

if __name__ == '__main__':
    main()