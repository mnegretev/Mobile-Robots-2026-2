import json
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint


class TaskExecutor(Node):

    def __init__(self):
        super().__init__('task_executor')

        self.sub_task = self.create_subscription(
            String,
            '/robot_task',
            self.callback_task,
            10
        )

        self.pub_traj = self.create_publisher(
            JointTrajectory,
            '/xarm6_traj_controller/joint_trajectory',
            1
        )

        self.get_logger().info("Task Executor Ready")

    def move_arm(self):

        msg = JointTrajectory()

        msg.header.stamp = self.get_clock().now().to_msg()

        msg.joint_names = [
            "joint1",
            "joint2",
            "joint3",
            "joint4",
            "joint5",
            "joint6"
        ]

        p = JointTrajectoryPoint()

        p.positions = [
            0.0,
            -0.5,
            0.5,
            0.0,
            0.0,
            0.0
        ]

        p.time_from_start.sec = 1

        msg.points.append(p)

        self.get_logger().info(
            "Sending arm trajectory"
        )

        self.pub_traj.publish(msg)

    def callback_task(self, msg):

        self.get_logger().info(
            f"Received task: {msg.data}"
        )

        try:

            data = json.loads(msg.data)

            action = data.get("action", "")

            self.get_logger().info(
                f"Action: {action}"
            )

            if action == "MOVE_ARM":

                self.move_arm()

            elif action == "NAVIGATE":

                destination = data.get(
                    "destination",
                    ""
                )

                self.get_logger().info(
                    f"Navigating to {destination}"
                )

            elif action == "FIND_OBJECT":

                obj = data.get(
                    "object",
                    ""
                )

                self.get_logger().info(
                    f"Searching for {obj}"
                )

            elif action == "PICK_OBJECT":

                obj = data.get(
                    "object",
                    ""
                )

                self.get_logger().info(
                    f"Picking {obj}"
                )

            elif action == "FIND_PERSON":

                self.get_logger().info(
                    "Searching for person"
                )

            elif action == "APPROACH_PERSON":

                self.get_logger().info(
                    "Approaching person"
                )

            elif action == "GO_TO_OBJECT":

                obj = data.get(
                    "object",
                    ""
                )

                self.get_logger().info(
                    f"Going to object {obj}"
                )

            else:

                self.get_logger().warn(
                    f"Unsupported action: {action}"
                )

        except Exception as e:

            self.get_logger().error(
                f"Error: {e}"
            )


def main(args=None):

    rclpy.init(args=args)

    node = TaskExecutor()

    rclpy.spin(node)

    node.destroy_node()

    rclpy.shutdown()


if __name__ == '__main__':
    main()
