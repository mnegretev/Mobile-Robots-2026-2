import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped
from std_msgs.msg import Float32, Bool, Int16, String

SM_WAITING = 0
SM_BUSSY = 1

class SMPlanner(Node):
    def __init__(self):
        super().__init__('sm_planner')
        #self.goal_pose_pub = self.create_publisher(PoseStamped, '/goal_pose', 10)
        #self.pruebas_suscriptor = self.create_subscription(Bool,'/pruebas',self.pruebas_callback,10)

        self.start_navigation = self.create_subscription(PoseStamped,'/goal_pose',self.start_navigation_callback,10)
        self.end_navigation = self.create_subscription(Bool,'/navigation/goal_reached',self.end_navigation_callback,10)

        self.prompt_enable = self.create_publisher (Bool, '/prompt_enable',10)

        self.state = SM_WAITING

        self.timer = self.create_timer(0.01, self.machine_loop)

    #ros2 topic pub --once /pruebas std_msgs/msg/Bool "{data: true}"
    
    def start_navigation_callback (self,msg):
            #self.get_logger().info("Received new goal pose: ")
            self.state = SM_BUSSY

    def end_navigation_callback (self,msg):
       
            self.state = SM_WAITING

    def machine_loop(self):
        msg_prompt = Bool()
        if self.state == SM_WAITING:
            msg_prompt.data = True
            #self.get_logger().info("Nuevo prompt")

        if self.state == SM_BUSSY:
            msg_prompt.data = False
            #self.get_logger().info("Ocupado")

        self.prompt_enable.publish(msg_prompt)


    

    

    # def pruebas_callback (self,msg):

    #     if msg.data == True:
    #         self.get_logger().info ("INICIANDO PRUEBA")
    #         self.target_position (3.0,3.0)

    #     return


    # def target_position(self, target_x, target_y):
    #     msg = PoseStamped()

    #     msg.header.frame_id = "map"
    #     msg.header.stamp = self.get_clock().now().to_msg()

    #     msg.pose.position.x = target_x
    #     msg.pose.position.y = target_y
    #     msg.pose.position.z = 0.0

    #     msg.pose.orientation.x = 0.0
    #     msg.pose.orientation.y = 0.0
    #     msg.pose.orientation.z = 0.0
    #     msg.pose.orientation.w = 1.0

    #     self.goal_pose_pub.publish(msg)

    #     self.get_logger().info("Meta publicada")
        
    #     return

def main():
    #1-Activar el housesimul:
    #ros2 launch house_simul house_simul.launch.py
    #2-Levantar el launch de este proyecto final:
    #ros2 launch final_project final_project_utils.launch.py 


    #Para ejecutar el pure pursuit junto con el smooth y el planner basta con mandar la posición objetivo con el comando:
    #ros2 topic pub --once /goal_pose geometry_msgs/msg/PoseStamped "{header: {stamp: {sec: 0, nanosec: 0}, frame_id: 'map'}, pose: {position: {x: 3.0, y: 3.0, z: 0.0}, orientation: {x: 0.0, y: 0.0, z: 0.0, w: 1.0}}}"
    print('Hi from final_project.')
    rclpy.init()
    sm_planner = SMPlanner()
    rclpy.spin(sm_planner)
    sm_planner.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
