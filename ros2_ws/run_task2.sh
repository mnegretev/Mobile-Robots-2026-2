cat << 'EOF' > run_task.sh
#!/bin/bash

# 1. Cargar el entorno de ROS 2 Jazzy y tu workspace
source /opt/ros/jazzy/setup.bash
source install/setup.bash

# 2. Lanzar la simulación en segundo plano
echo "Lanzando simulación de la casa..."
ros2 launch house_simul house_simul.launch.py &
sleep 10  # Esperamos a que Gazebo cargue completamente

# 3. Lanzar utilidades de planeación en segundo plano
echo "Lanzando utilidades de planeación..."
ros2 launch motion_planning motion_planning_utils.launch.py &
sleep 5

# 4. Correr el inflado de mapas (este se queda en primer plano para ver los logs)
echo "Iniciando procesamiento de mapa de costos..."
ros2 run path_planner cost_map --ros-args -p inflation_radius:=0.1 -p cost_radius:=0.1
EOF
