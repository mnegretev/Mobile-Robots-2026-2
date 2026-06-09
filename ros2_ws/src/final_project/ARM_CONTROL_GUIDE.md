# Guía de Prueba: Movimiento del Robot

## 1. Movimiento de la Base Móvil ✓

### Script de prueba básico:
```bash
# Terminal 1: Lanzar el robot
cd /home/danielgrioja/Fac_Inge/Mobile-Robots-2026-2/ros2_ws
source install/setup.bash
ros2 launch final_project final_project_utils.launch.py

# Terminal 2: Ejecutar prueba (esperar ~15 segundos a que inicie todo)
python3 src/final_project/final_project/test_movement.py
```

El robot se moverá 1 metro hacia adelante, luego 0.5 metros hacia atrás.

---

## 2. Movimiento del Brazo (Xarm6)

### Opción A: Script de Control de Trayectoria (RECOMENDADO)

```bash
# Terminal 2: Ejecutar prueba del brazo
python3 src/final_project/final_project/test_arm_movement.py
```

**Lo que hace:**
- Posición HOME (brazos rectos)
- Posición UP (levanta el brazo)
- Posición SIDE (brazo a un lado)
- Retorna a HOME

Cada movimiento tarda ~3 segundos.

### Opción B: Control Manual con CLI

```bash
# Publicar comando de trayectoria manualmente
ros2 topic pub /xarm6_traj_controller/joint_trajectory trajectory_msgs/msg/JointTrajectory "
joint_names: ['joint1', 'joint2', 'joint3', 'joint4', 'joint5', 'joint6']
points:
  - positions: [0.0, -1.57, 1.57, 0.0, 0.0, 0.0]
    velocities: [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    time_from_start: {sec: 3, nanosec: 0}
" --once
```

### Opción C: Verificar Estado de las Articulaciones

```bash
# Ver el estado actual del brazo
ros2 topic echo /joint_states
```

---

## 3. Parámetros de Control

### Articulaciones del Xarm6:
- `joint1`: Rotación base (radios)
- `joint2`: Hombro (radios)
- `joint3`: Codo (radios)
- `joint4`: Muñeca rotación (radios)
- `joint5`: Muñeca inclinación (radios)
- `joint6`: Muñeca rotación (radios)

### Rangos típicos:
- Rango: -π a +π radios (-3.14 a 3.14)
- Valores comunes:
  - 0.0 = posición neutra
  - ±1.57 ≈ ±90°
  - ±3.14 ≈ ±180°

### Ejemplos de poses:
```python
HOME       = [0.0,  0.0,  0.0, 0.0, 0.0, 0.0]  # Posición inicial
UP         = [0.0, -1.57, 1.57, 0.0, 0.0, 0.0]  # Levanta el brazo
SIDE       = [1.57, -1.57, 1.57, 0.0, 0.0, 0.0] # Brazo a un lado
READY      = [0.0, -0.5,  0.5,  0.0, 0.0, 0.0]  # Posición de preparación
```

---

## 4. Troubleshooting

### El brazo no se mueve:
1. Verifica que el controlador está activo: `ros2 service call /controller_manager/list_controllers controller_manager_msgs/srv/ListControllers {}`
2. Verifica el nombre del tópico: `ros2 topic list | grep xarm`
3. Revisa los logs: `ros2 node list` (debe haber nodos de controlador)

### El brazo se mueve lentamente:
Aumenta el valor de `duration` en el script (en segundos)

### Error de conexión:
Espera 15-20 segundos después de lanzar el launch antes de ejecutar el script de prueba

---

## 5. Próximas Mejoras

Para movimientos más complejos, considera:
- Usar **MoveIt** para planificación automática
- Implementar **IK (Inverse Kinematics)** para posiciones cartesianas
- Crear **secuencias de movimiento** personalizadas
- Integrar **visión** para manipulación adaptativa

