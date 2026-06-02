#
# MOBILE ROBOTS - FI-UNAM, 2026-2
# LAUNCH: Sistema de navegación por voz
#
# Arranca:
#   1. faster_whisper_asr  -> graba micrófono y publica en /sp_rec/recognized
#   2. voice_commander     -> interpreta texto y publica goal en /goal_pose
#
# Requisitos previos (en terminales separadas):
#   $ ros2 launch house_simul house_simul.launch.py
#   $ ros2 launch motion_planning motion_planning_utils.launch.py
#   $ ros2 run path_follower pure_pursuit  (o stanley)
#   $ ros2 run path_planner a_star         (o rrt / pot_fields)
#

from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([

        Node(
            package="voice_commander",
            executable="faster_whisper_asr",
            name="faster_whisper_node",
            output="screen",
        ),

        Node(
            package="voice_commander",
            executable="voice_commander_node",
            name="voice_commander_node",
            output="screen",
        ),
    ])
