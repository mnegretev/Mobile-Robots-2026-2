#!/usr/bin/env python3
#
# MOBILE ROBOTS - FI-UNAM, 2026-2
# INVERSE KINEMATICS BY NEWTON-RAPHSON
#
# Oscar Saldivar Pantoja
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

NAME = "Oscar Saldivar Pantoja"

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
        sy = numpy.sqrt(R[0, 0] * R[0, 0] + R[1, 0] * R[1, 0])
        singular = sy < 1e-6
    
        if not singular:
            x = numpy.arctan2(R[2, 1], R[2, 2])
            y = numpy.arctan2(-R[2, 0], sy)
            z = numpy.arctan2(R[1, 0], R[0, 0])
        else:
            x = numpy.arctan2(-R[1, 2], R[1, 1])
            y = numpy.arctan2(-R[2, 0], sy)
            z = 0
            
        return x,y,z

    def forward_kinematics(self, Q):
        # 1. H = I (Assign a 4x4 identity matrix)
        H = numpy.identity(4)
        
        # 2. Loop through all 6 operational joints in Q
        for i in range(6):
            q = Q[i]
            # Homogeneous transformation with zero translation rotated q[rad] over z-axis
            R = numpy.asarray([[numpy.cos(q), -numpy.sin(q), 0.0, 0.0],
                               [numpy.sin(q),  numpy.cos(q), 0.0, 0.0],
                               [0.0,           0.0,          1.0, 0.0],
                               [0.0,           0.0,          0.0, 1.0]])
            # H = H * Hs[i] * R
            H = numpy.dot(H, Hs[i])
            H = numpy.dot(H, R)
            
        # 3. H = H * Hs[6] (Apply fixed TCP link transformation)
        H = numpy.dot(H, Hs[6])
        
        # 4. Extract xyz position from H
        x = H[0, 3]
        y = H[1, 3]
        z = H[2, 3]
        
        # 5. Get RPY (Euler angles) from the rotation part of H
        R, P, Y = self.matrix_to_euler_xyz(H[0:3, 0:3])
        
        return numpy.asarray([x, y, z, R, P, Y])

    def jacobian(self, Q):
        delta_q = 0.000001
        J = numpy.asarray([[0.0 for q in Q] for i in range(6)])
        
        # Create perturbated structures for central differences numerical approximation
        for i in range(len(Q)):
            q_next = numpy.copy(Q)
            q_prev = numpy.copy(Q)
            
            # Apply +/- delta to the specific joint column
            q_next[i] += delta_q
            q_prev[i] -= delta_q
            
            # Compute numerical partial derivative column by column: (FK(q+d) - FK(q-d)) / (2*delta)
            J[:, i] = (self.forward_kinematics(q_next) - self.forward_kinematics(q_prev)) / (2.0 * delta_q)
        
        return J
        
    def inverse_kinematics(self, Xd, init_guess=numpy.zeros(7), max_iter=2000):
        Xd = numpy.asarray(Xd)
        Q = numpy.copy(init_guess)
        iterations = 0
        tolerance = 0.001

        # Calculate initial Forward Kinematics and initial error vector
        X = self.forward_kinematics(Q)
        error = X - Xd
        
        # Ensure orientation angles of error are mapped into (-pi, pi]
        for i in range(3, 6):
            error[i] = (error[i] + numpy.pi) % (2.0 * numpy.pi) - numpy.pi

        # WHILE norm of error exceeds TOL and max iterations are not met
        while numpy.linalg.norm(error) > tolerance and iterations < max_iter:
            # Calculate numerical Jacobian evaluated at current Q
            J = self.jacobian(Q)
            
            # Update estimated joint configurations using the Moore-Penrose pseudo-inverse
            Q = Q - numpy.dot(numpy.linalg.pinv(J), error)
            
            # Ensure all joints q map inside the wrapping bounds [-pi, pi]
            for i in range(len(Q)):
                Q[i] = (Q[i] + numpy.pi) % (2.0 * numpy.pi) - numpy.pi
                
            # Recalculate forward kinematics and errors
            X = self.forward_kinematics(Q)
            error = X - Xd
            
            # Force orientation wrap verification for the error components
            for i in range(3, 6):
                error[i] = (error[i] + numpy.pi) % (2.0 * numpy.pi) - numpy.pi
                
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