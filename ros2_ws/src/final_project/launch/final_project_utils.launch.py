from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import IncludeLaunchDescription, TimerAction, RegisterEventHandler, SetEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import PathJoinSubstitution, Command
from launch_ros.substitutions import FindPackageShare
from ament_index_python.packages import get_package_share_directory
from launch.event_handlers import OnProcessStart
import os

def generate_launch_description():
    final_project_pkg= get_package_share_directory('final_project')
    rviz_config_file = os.path.join(final_project_pkg, 'rviz', 'final_project.rviz')
    mvn_planning_pkg = get_package_share_directory('motion_planning')
    map_config_file  = os.path.join(mvn_planning_pkg, 'maps', 'appartment.yaml')
    
    # Gazebo world
    house_simul_pkg = get_package_share_directory('house_simul')
    gazebo_world = os.path.join(house_simul_pkg, 'worlds', 'house.world')
    
    # Robot URDF configuration
    mbot_demo_pkg = get_package_share_directory('mbot_demo')
    urdf_file = os.path.join(mbot_demo_pkg, 'urdf', 'base_with_arm.urdf.xacro')
    
    # Set Gazebo models path
    env_var_gz_models = SetEnvironmentVariable(
        'GZ_SIM_RESOURCE_PATH',
        os.path.join(house_simul_pkg, 'models')
    )
    
    # Robot state publisher node with properly compiled xacro
    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{
            'use_sim_time': True,
            'robot_description': Command([
                'xacro ',
                urdf_file,
                ' ros2_control_plugin:=gz_ros2_control/GazeboSimSystem',
                ' load_gazebo_plugin:=true',
                ' add_gripper:=false'
            ])
        }],
    )
    
    # Gazebo launch
    gazebo_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(PathJoinSubstitution([FindPackageShare('ros_gz_sim'), 'launch', 'gz_sim.launch.py'])),
        launch_arguments={
            'gz_args': f' -r -v 3 {gazebo_world}',
        }.items(),
    )
    
    # Gazebo spawn entity node - increased Z to prevent collision with ground
    gazebo_spawn_entity_node = Node(
        package="ros_gz_sim",
        executable="create",
        output='screen',
        arguments=[
            '-topic', 'robot_description',
            '-name', 'justina_with_xarm',
            '-x', '-2.25',
            '-y', '-1.50',
            '-z', '1.0',
            '-Y', '0.00'
        ],
        parameters=[{'use_sim_time': True}],
    )
    
    # ROS-Gazebo bridge
    mbot_demo_pkg_path = get_package_share_directory('mbot_demo')
    gz_bridge_params_path = os.path.join(mbot_demo_pkg_path, 'config', 'gz_bridge.yaml')
    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '--ros-args', '-p',
            f'config_file:={gz_bridge_params_path}',
            '-p', 'use_sim_time:=True',
        ],
        output='screen'
    )
    
    # Load controllers
    controller_nodes = [
        Node(
            package='controller_manager',
            executable='spawner',
            output='screen',
            arguments=['joint_state_broadcaster', '--controller-manager', '/controller_manager'],
            parameters=[{'use_sim_time': True}],
        ),
        Node(
            package='controller_manager',
            executable='spawner',
            output='screen',
            arguments=['xarm6_traj_controller', '--controller-manager', '/controller_manager'],
            parameters=[{'use_sim_time': True}],
        ),
        Node(
            package='controller_manager',
            executable='spawner',
            output='screen',
            arguments=['mbot_traj_controller', '--controller-manager', '/controller_manager'],
            parameters=[{'use_sim_time': True}],
        ),
    ]

    return LaunchDescription([
        env_var_gz_models,
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
        # Gazebo with robot
        RegisterEventHandler(
            event_handler=OnProcessStart(
                target_action=robot_state_publisher_node,
                on_start=gazebo_launch,
            )
        ),
        RegisterEventHandler(
            event_handler=OnProcessStart(
                target_action=robot_state_publisher_node,
                on_start=gazebo_spawn_entity_node,
            )
        ),
        RegisterEventHandler(
            event_handler=OnProcessStart(
                target_action=robot_state_publisher_node,
                on_start=bridge,
            )
        ),
        robot_state_publisher_node,
        # Map and navigation
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
                # Node(
                #     package='path_planner',
                #     executable='cost_map_solved',
                #     name='cost_map',
                #     parameters=[{'inflation_radius':0.25}, {'cost_radius':0.5}]
                # ),
            ] + controller_nodes
        ),
        # TimerAction(
        #     period=10.0,
        #     # actions=[
        #     #     Node(
        #     #         package='path_planner',
        #     #         executable='a_star_solved',
        #     #         name='a_star',
        #     #     ),
        #     #     Node(
        #     #         package='path_planner',
        #     #         executable='path_smoothing_solved',
        #     #         name='path_smoothing',
        #     #     ),
        #     #     Node(
        #     #         package='path_follower',
        #     #         executable='pure_pursuit_solved',
        #     #         name='pure_pursuit',
        #     #         parameters=[{'alpha':0.1}, {'beta':0.1}]
        #     #     ),
        #     # ]
        # ),
    ])
