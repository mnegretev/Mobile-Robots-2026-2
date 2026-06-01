import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node

def generate_launch_description():
    # Rutas a los paquetes del profesor
    house_simul_dir = get_package_share_directory('house_simul')
    motion_planning_dir = get_package_share_directory('motion_planning')

    return LaunchDescription([
        # 1. El Simulador (Gazebo + Justina)
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(house_simul_dir, 'launch', 'house_simul.launch.py')
            )
        ),
        
        # 2. Navegación del Profesor (A*, Suavizado, Pure Pursuit)
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(motion_planning_dir, 'launch', 'motion_planning.launch.py')
            )
        ),
        
        # 3. Visión Inteligente (YOLO)
        Node(
            package='vision_ia',
            executable='yolo_detector',
            name='yolo_detector_node',
            output='screen'
        ),
        
        # 4. Action Server (El Puente)
        Node(
            package='task_manager',
            executable='nav_action_server',
            name='nav_action_server',
            output='screen'
        ),
        
        # 5. Cerebro Orquestador
        Node(
            package='task_manager',
            executable='task_manager',
            name='task_manager_node',
            output='screen'
        )
    ])