from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():
    final_project_pkg= get_package_share_directory('final_project')
    rviz_config_file = os.path.join(final_project_pkg, 'rviz', 'final_project.rviz')
    mvn_planning_pkg = get_package_share_directory('motion_planning')
    map_config_file  = os.path.join(mvn_planning_pkg, 'maps', 'appartment.yaml')

    return LaunchDescription([
        Node(
            name='lira_gui',
            package='lira_gui',
            executable='lira_gui_node',
            parameters=[{'use_sim_time':True}]
        ),
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            arguments=['-d', rviz_config_file,'--ros-args', '-p', 'use_sim_time:=True',],
        ),        
        Node(
            package='nav2_map_server',
            executable='map_server',
            name='map_server',
            output='screen',
            parameters=[{'yaml_filename':map_config_file}, {'use_sim_time':True}]
        ),
        Node(
            package='nav2_amcl',
            executable='amcl',
            name='amcl',
            output='screen',
            parameters=[
                {'base_frame_id':'base_link'},
                {'set_initial_pose':True},
                {'use_sim_time':True},
                {'alpha1':0.01},
                {'alpha2':0.01},
                {'alpha3':0.1},
                {'alpha4':0.1}
            ]
        ),
        TimerAction(
            period=5.0,
            actions=[
                Node(
                    package='nav2_util',
                    executable='lifecycle_bringup',
                    name='lifecycle_bringup',
                    output='screen',
                    arguments=['map_server', 'amcl']
                ),
                Node(
                    package='path_planner',
                    executable='cost_map_solved',
                    name='cost_map',
                    parameters=[{'inflation_radius':0.25}, {'cost_radius':0.5}]
                ),
            ]
        ),
        TimerAction(
            period=10.0,
            actions=[
                Node(
                    package='path_planner',
                    executable='a_star_solved',
                    name='a_star',
                ),
                Node(
                    package='path_planner',
                    executable='path_smoothing_solved',
                    name='path_smoothing',
                ),
                Node(
                    package='path_follower',
                    executable='pure_pursuit_solved',
                    name='pure_pursuit',
                    parameters=[{'alpha':0.1}, {'beta':0.1}]
                ),
            ]
        ),
    ])