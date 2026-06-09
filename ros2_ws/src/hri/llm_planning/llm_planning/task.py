import rclpy
from rclpy.node import Node
from std_msgs.msg import String

class TaskExecutor(Node):
    def __init__(self):
        super().__init__('task_executor')
        self.sub_task = self.create_subscription(String,'/robot_task',self.callback_task,10)
        self.get_logger().info("Task Executor Ready")
        
    def callback_task(self, msg):
        self.get_logger().info("Received task: " + msg.data)

def main(args=None):
    rclpy.init(args=args)
    node = TaskExecutor()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()