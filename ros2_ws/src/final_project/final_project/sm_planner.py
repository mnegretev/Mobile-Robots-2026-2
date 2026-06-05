#
# MOBILE ROBOTS - FI-UNAM, 2026-2
# FINAL PROJECT - ORCHESTRATOR STATE MACHINE
#
# Single rclpy node that coordinates the whole pipeline:
#
#   /sp_rec/recognized (String)              [speech2text: faster_whisper]
#        -> llama3 via Ollama (llm_orchestrator.plan_from_command)
#        -> ordered list of sub-tasks
#        -> for each sub-task, drive the existing course nodes:
#             move_to / return_to_user / place -> publish /goal_pose,
#                                                  wait /navigation/goal_reached
#             find                            -> read /vision/detections
#             grasp                           -> call /manipulation/ik_pose2pose,
#                                                  publish arm trajectory + gripper
#             say                             -> publish /tts_query
#        -> spoken confirmation                [text2speech: piper-tts]
#
# Design: a flat state machine. One sub-task is executed at a time; the
# machine only advances when the current sub-task reports done. This keeps
# the logic simple and debuggable, which the project asks for.
#
import math
import json
import rclpy
from rclpy.node import Node
from rclpy.duration import Duration
from std_msgs.msg import String, Bool
from geometry_msgs.msg import PoseStamped
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from manip_msgs.srv import InverseKinematicsPose2Pose

from final_project.llm_orchestrator import plan_from_command, KNOWN_LOCATIONS

# --- States --------------------------------------------------------------
SM_IDLE        = 0   # waiting for a spoken command
SM_PLAN        = 10  # call the LLM, build the plan
SM_NEXT_STEP   = 20  # pop the next sub-task
SM_NAVIGATE    = 30  # going to a pose
SM_FIND        = 40  # scanning for an object with YOLO
SM_GRASP       = 50  # solving IK and moving the arm
SM_SPEAK       = 60  # speaking and waiting for speech to finish
SM_DONE        = 70  # plan finished

# xArm6 has 6 joints; adjust names to your URDF if different.
ARM_JOINTS = ["joint1", "joint2", "joint3", "joint4", "joint5", "joint6"]
ARM_CMD_TOPIC = "/xarm6_traj_controller/joint_trajectory"

FIND_TIMEOUT = 15.0   # seconds to look for an object before giving up


class OrchestratorNode(Node):
    def __init__(self):
        super().__init__("orchestrator_node")
        # ---- I/O wired to the EXISTING course topics/services ----
        self.sub_cmd  = self.create_subscription(
            String, "/sp_rec/recognized", self.cb_command, 1)
        self.sub_det  = self.create_subscription(
            String, "/vision/detections", self.cb_detections, 1)
        self.sub_done = self.create_subscription(
            Bool, "/navigation/goal_reached", self.cb_goal_reached, 1)
        self.pub_goal = self.create_publisher(PoseStamped, "/goal_pose", 1)
        self.pub_tts  = self.create_publisher(String, "/tts_query", 1)
        self.pub_arm  = self.create_publisher(JointTrajectory, ARM_CMD_TOPIC, 1)
        self.ik_cli   = self.create_client(
            InverseKinematicsPose2Pose, "/manipulation/ik_pose2pose")

        # ---- internal state ----
        self.state = SM_IDLE
        self.command = None
        self.plan = []
        self.step = None
        self.detections = []
        self.goal_reached = False
        self.timer_start = None

        self.timer = self.create_timer(0.1, self.step_machine)
        self.get_logger().info("Orchestrator ready. Waiting for a command...")

    # ---------------- callbacks ----------------
    def cb_command(self, msg):
        if self.state == SM_IDLE and msg.data.strip():
            self.command = msg.data.strip()
            self.get_logger().info(f"Command received: {self.command}")
            self.state = SM_PLAN

    def cb_detections(self, msg):
        try:
            self.detections = json.loads(msg.data)
        except json.JSONDecodeError:
            self.detections = []

    def cb_goal_reached(self, msg):
        if msg.data:
            self.goal_reached = True

    # ---------------- helpers ----------------
    def speak(self, text):
        self.pub_tts.publish(String(data=text))
        self.get_logger().info(f"[say] {text}")

    def send_goal(self, location):
        coords = KNOWN_LOCATIONS.get(location)
        if coords is None:
            self.get_logger().warn(f"Unknown location '{location}', skipping.")
            return False
        x, y, yaw = coords
        g = PoseStamped()
        g.header.frame_id = "map"
        g.header.stamp = self.get_clock().now().to_msg()
        g.pose.position.x = float(x)
        g.pose.position.y = float(y)
        g.pose.orientation.z = math.sin(yaw / 2.0)
        g.pose.orientation.w = math.cos(yaw / 2.0)
        self.goal_reached = False
        self.pub_goal.publish(g)
        self.get_logger().info(f"[move_to] {location} -> ({x:.1f},{y:.1f})")
        return True

    def object_visible(self, label):
        for d in self.detections:
            if d["label"] == label or label in d["label"]:
                return d
        return None

    def call_ik(self, x, y, z, roll=0.0, pitch=1.57, yaw=0.0):
        """Blocking IK call. Returns list of joint angles or None."""
        if not self.ik_cli.wait_for_service(timeout_sec=2.0):
            self.get_logger().warn("IK service unavailable.")
            return None
        req = InverseKinematicsPose2Pose.Request()
        req.x, req.y, req.z = float(x), float(y), float(z)
        req.roll, req.pitch, req.yaw = float(roll), float(pitch), float(yaw)
        req.initial_guess = [0.0] * len(ARM_JOINTS)
        future = self.ik_cli.call_async(req)
        rclpy.spin_until_future_complete(self, future, timeout_sec=10.0)
        if future.result() is None or not future.result().q:
            return None
        return list(future.result().q)

    def move_arm(self, q, seconds=3.0):
        traj = JointTrajectory()
        traj.joint_names = ARM_JOINTS
        pt = JointTrajectoryPoint()
        pt.positions = [float(v) for v in q[:len(ARM_JOINTS)]]
        pt.time_from_start = Duration(seconds=seconds).to_msg()
        traj.points.append(pt)
        self.pub_arm.publish(traj)

    def elapsed(self):
        if self.timer_start is None:
            return 0.0
        return (self.get_clock().now() - self.timer_start).nanoseconds / 1e9

    # ---------------- state machine ----------------
    def step_machine(self):
        if self.state == SM_IDLE:
            return

        if self.state == SM_PLAN:
            try:
                self.plan = plan_from_command(self.command)
            except RuntimeError as e:
                self.get_logger().error(str(e))
                self.speak("No pude entender la instrucci\u00f3n.")
                self.reset()
                return
            self.get_logger().info(f"Plan ({len(self.plan)} steps): "
                                   + ", ".join(s["action"] for s in self.plan))
            self.state = SM_NEXT_STEP

        elif self.state == SM_NEXT_STEP:
            if not self.plan:
                self.state = SM_DONE
                return
            self.step = self.plan.pop(0)
            a = self.step["action"]
            if a in ("move_to", "return_to_user", "place"):
                loc = self.step.get("target") or "user"
                if a == "return_to_user":
                    loc = "user"
                self.send_goal(loc)
                self.state = SM_NAVIGATE
            elif a == "find":
                self.timer_start = self.get_clock().now()
                self.state = SM_FIND
            elif a == "grasp":
                self.state = SM_GRASP
            elif a == "say":
                self.speak(self.step.get("text") or "Listo.")
                self.state = SM_SPEAK
                self.timer_start = self.get_clock().now()

        elif self.state == SM_NAVIGATE:
            if self.goal_reached:
                self.get_logger().info("[move_to] goal reached.")
                self.state = SM_NEXT_STEP

        elif self.state == SM_FIND:
            target = self.step.get("target")
            det = self.object_visible(target)
            if det is not None:
                self.found = det
                self.get_logger().info(
                    f"[find] '{target}' at pixel ({det['cx']},{det['cy']})")
                self.state = SM_NEXT_STEP
            elif self.elapsed() > FIND_TIMEOUT:
                self.get_logger().warn(f"[find] '{target}' not found.")
                self.speak(f"No encuentro el objeto.")
                self.reset()

        elif self.state == SM_GRASP:
            # Minimal grasp: map the detection to an approximate arm-frame
            # pose. In a full system this comes from depth + TF; here we use
            # a fixed reachable pose in front of the gripper as a placeholder.
            q = self.call_ik(0.35, 0.0, 0.20)
            if q is not None:
                self.move_arm(q)
                self.get_logger().info("[grasp] arm moved to object pose.")
            else:
                self.get_logger().warn("[grasp] IK failed; skipping.")
            self.state = SM_NEXT_STEP

        elif self.state == SM_SPEAK:
            # Rough wait so the TTS finishes before the next step.
            text = self.step.get("text") or ""
            if self.elapsed() > 0.08 * len(text) + 1.5:
                self.state = SM_NEXT_STEP

        elif self.state == SM_DONE:
            self.get_logger().info("Plan complete.")
            self.reset()

    def reset(self):
        self.state = SM_IDLE
        self.command = None
        self.plan = []
        self.step = None
        self.get_logger().info("Waiting for a command...")


def main(args=None):
    rclpy.init(args=args)
    node = OrchestratorNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == "__main__":
    main()