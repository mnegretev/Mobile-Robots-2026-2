#!/bin/bash
cd ~/Desktop/robots_repo/Mobile-Robots-2026-2
source /opt/ros/$ROS_DISTRO/setup.bash
source ros2_ws/install/setup.bash
export PYTHONPATH=$PWD/venv/lib/python3.12/site-packages:$PYTHONPATH