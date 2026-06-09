import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node

def generate_launch_description():
    # Rutas a los paquetes del profesor
    house_simul_dir = get_package_share_directory('house_simul')
    motion_planning_dir = get_package_share_directory('motion_planning')

    # --- FASE 1: El Simulador pesado ---
    simulador = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(house_simul_dir, 'launch', 'house_simul.launch.py')
        )
    )
    
    # --- FASE 2: Los módulos que necesitan que Gazebo ya exista ---
    navegacion = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(motion_planning_dir, 'launch', 'motion_planning.launch.py')
        )
    )
    
    yolo_node = Node(
        package='vision_ia',
        executable='yolo_detector',
        name='yolo_detector_node',
        output='screen'
    )
    
    nav_server_node = Node(
        package='task_manager',
        executable='nav_action_server',
        name='nav_action_server',
        output='screen'
    )
    
    task_manager_node = Node(
        package='task_manager',
        executable='task_manager_node',
        name='task_manager',
        output='screen'
    )

    # --- LA MAGIA DEL TEMPORIZADOR ---
    return LaunchDescription([
        simulador,                     # 1. Arranca Gazebo inmediatamente
        TimerAction(
            period=20.0,               # 2. Espera exactamente 20 segundos
            actions=[                  # 3. Libera todo el ecosistema
                navegacion, 
                yolo_node, 
                nav_server_node, 
                task_manager_node
            ]
        )
    ])