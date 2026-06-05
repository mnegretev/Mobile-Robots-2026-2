#
# MOBILE ROBOTS - FI-UNAM, 2026-2
# FINAL PROJECT - ORCHESTRATOR BRINGUP
#
# Brings up ONLY the new HRI/AI layer + perception publisher:
#   - speech2text (faster_whisper)   -> /sp_rec/recognized
#   - text2speech (piper-tts)        <- /tts_query
#   - yolo_detector                  -> /vision/detections
#   - sm_orchestrator                (the brain)
#
# Run the simulator and navigation stack separately, e.g.:
#   ros2 launch house_simul house_simul.launch.py
#   ros2 launch final_project final_project_utils.launch.py   (map+amcl+planner+follower)
#   ros2 launch final_project orchestrator.launch.py          (THIS file)
#
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        # NOTE: speech2text/setup.py currently has an EMPTY console_scripts list.
        # Register the entry point first (see SUMMARY/INSTRUCTIONS), then this works:
        Node(
            package='speech2text',
            executable='faster_whisper_asr',
            name='faster_whisper_asr',
            output='screen',
        ),
        Node(
            package='text2speech',
            executable='ts2',          # real entry point in text2speech/setup.py
            name='text2speech',
            output='screen',
        ),
        Node(
            package='final_project',
            executable='yolo_detector',
            name='yolo_detector',
            output='screen',
            parameters=[{'device': 'cuda', 'conf': 0.4}],
        ),
        Node(
            package='final_project',
            executable='sm_orchestrator',
            name='orchestrator',
            output='screen',
            parameters=[{'use_sim_time': True}],
        ),
    ])