from launch import LaunchDescription
from launch_ros.actions import Node
import os
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    """
    Launch file to run RRT experiments automatically
    
    Usage: ros2 launch path_planner rrt_experiments.launch.py
    """
    
    # After running this, the experiments should complete automatically
    # and generate a CSV file with results
    
    # Start the cost_map node (required for RRT)
    cost_map_node = Node(
        package='path_planner',
        executable='cost_map',
        name='cost_map_node',
        parameters=[
            {'inflation_radius': 0.1},
            {'cost_radius': 0.3}
        ]
    )
    
    # Start the RRT node
    rrt_node = Node(
        package='path_planner',
        executable='rrt',
        name='rrt_node',
        parameters=[
            {'epsilon': 1.0},
            {'max_n': 100}
        ]
    )
    
    # Start the experimenter (will run tests and exit)
    experimenter_node = Node(
        package='path_planner',
        executable='test_experiments',
        name='rrt_experimenter',
        output='screen',
        prefix=['xterm -e']  # Run in separate window for better visibility
    )
    
    return LaunchDescription([
        cost_map_node,
        rrt_node,
        experimenter_node
    ])
