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

NAME = "Gonzalez Fernandez Jonathan Uriel"

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
        # Inicializamos H como una matriz identidad 4x4
        H = numpy.eye(4)
        
        # Iteramos sobre las 6 articulaciones activas (H0 a H5)
        for i in range(6):
            q = Q[i]
            # Transformación homogénea de rotación pura en Z
            R = numpy.array([
                [math.cos(q), -math.sin(q), 0.0, 0.0],
                [math.sin(q),  math.cos(q), 0.0, 0.0],
                [0.0,          0.0,         1.0, 0.0],
                [0.0,          0.0,         0.0, 1.0]
            ])
            # Multiplicación sucesiva: H_nueva = H_actual * Hs[i] * R
            # En numpy, usamos np.dot() o el operador @ para matrices
            H = H @ Hs[i] @ R
            
        # Finalmente, multiplicamos por la matriz fija del efector (TCP)
        H = H @ Hs[6]
        
        # Extraemos la posición cartesiana (última columna de la matriz)
        x = H[0, 3]
        y = H[1, 3]
        z = H[2, 3]
        
        # Extraemos los ángulos de Euler usando la función de la clase
        R_roll, P_pitch, Y_yaw = self.matrix_to_euler_xyz(H)
        
        return numpy.asarray([x, y, z, R_roll, P_pitch, Y_yaw])

    def jacobian(self, Q):
        delta_q = 0.000001
        J = numpy.asarray([[0.0 for q in Q] for i in range(6)])
        
        # Iteramos SOLO sobre los 6 grados de libertad móviles
        for i in range(6):
            # Es crucial hacer una copia para no modificar el arreglo original Q en cada iteración
            q_next = numpy.copy(Q)
            q_prev = numpy.copy(Q)
            
            # Perturbamos la i-ésima articulación hacia adelante (+delta) y hacia atrás (-delta)
            q_next[i] += delta_q
            q_prev[i] -= delta_q
            
            # Evaluamos la cinemática directa en ambos puntos
            fk_next = self.forward_kinematics(q_next)
            fk_prev = self.forward_kinematics(q_prev)
            
            # Calculamos la columna aproximada por diferencias finitas
            col_derivada = (fk_next - fk_prev) / (2.0 * delta_q)
            
            # Asignamos los valores calculados a la i-ésima columna de nuestra matriz Jacobiana J
            for j in range(6):
                J[j, i] = col_derivada[j]
                
        return J
        
    def inverse_kinematics(self, Xd, init_guess=numpy.zeros(7), max_iter=2000):
        Xd= numpy.asarray(Xd)
        Q = numpy.array(init_guess, dtype=float)
        iterations = 0

        
        TOL = 1e-4  # Tolerancia para el error

        # Calculate Forward Kinematics 'X' by calling the corresponding function
        X = self.forward_kinematics(Q)
        
        # Calcualte error = X - Xd
        error = X - Xd
        
        # Ensure orientation angles of error are in (-pi,pi]
        for i in range(3, 6):
            error[i] = (error[i] + math.pi) % (2 * math.pi) - math.pi

        # WHILE |error| > TOL and iterations < maximum iterations:
        while numpy.linalg.norm(error) > TOL and iterations < max_iter:
            # Calculate Jacobian
            J = self.jacobian(Q)
            
            # Update estimated Q with Q = Q - pseudo_inverse(J)*error
            # Usamos pinv para la pseudoinversa de Moore-Penrose (muy robusta)
            J_inv = numpy.linalg.pinv(J)
            delta_q = J_inv @ error
            
            # Actualizamos solo las primeras 6 articulaciones
            Q[:6] = Q[:6] - delta_q
            
            # Ensure all angles q are in [-pi,pi]
            for i in range(6):
                Q[i] = (Q[i] + math.pi) % (2 * math.pi) - math.pi
                
            # Recalculate forward kinematics X
            X = self.forward_kinematics(Q)
            
            # Recalculate error and ensure angles are in (-pi,pi]
            error = X - Xd
            for i in range(3, 6):
                error[i] = (error[i] + math.pi) % (2 * math.pi) - math.pi
                
            # Increment iterations
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
        resp.q = Q.tolist() if success else []
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
