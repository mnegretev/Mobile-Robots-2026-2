# 🤖 Guía de Prueba: Robot Móvil + Brazo Xarm6

## Introducción

Se han creado 4 scripts de prueba para verificar el funcionamiento del robot:
- Base móvil (mbot)
- Brazo robótico (xarm6)
- Combinación de ambos

---

## 📋 Pasos Iniciales

### 1. Compilar y sourcer workspace:
```bash
cd /home/danielgrioja/Fac_Inge/Mobile-Robots-2026-2/ros2_ws

# Compilar (solo si hay cambios)
colcon build --packages-select final_project

# Sourcer
source install/setup.bash
```

### 2. Lanzar el robot (Terminal 1):
```bash
ros2 launch final_project final_project_utils.launch.py
```

Espera ~15-20 segundos a que todo inicie (Gazebo, RViz, controladores, etc.)

---

## 🧪 Scripts de Prueba Disponibles

### Test 1: Base Móvil (test_movement.py)
```bash
python3 src/final_project/final_project/test_movement.py
```

**Lo que hace:**
- Mueve la base 1 metro hacia adelante
- Retorna 0.5 metros hacia atrás
- Duración: ~8 segundos

**Resultado esperado:**
- En Gazebo: Robot se mueve en línea recta
- En RViz: TF del robot se actualiza

---

### Test 2: Brazo - Básico (test_arm_movement.py) ⭐
```bash
python3 src/final_project/final_project/test_arm_movement.py
```

**Lo que hace:**
- Posición HOME (brazos rectos, sin movimiento)
- Posición UP (levanta el brazo)
- Posición SIDE (brazo a un lado)
- Retorna a HOME

**Duración:** ~12 segundos

**Resultado esperado:**
- En Gazebo: Brazo se levanta, gira, y retorna
- En RViz: Articulaciones se actualizan en tiempo real

---

### Test 3: Brazo - Avanzado (test_arm_advanced.py)
```bash
python3 src/final_project/final_project/test_arm_advanced.py
```

**Lo que hace:**
1. Reach Forward (alcance hacia adelante)
2. Reach Up (alcance hacia arriba)
3. Reach Left (alcance hacia la izquierda)
4. Reach Right (alcance hacia la derecha)
5. Rotate Wrist (rotación de muñeca)
6. Return to Home (retorna a posición inicial)

**Duración:** ~13 segundos

**Mejores para:** Ver rango de movimiento completo del brazo

---

### Test 4: Combinado - Base + Brazo (test_combined.py)
```bash
python3 src/final_project/final_project/test_combined.py
```

**Escenario 1:**
- Mueve la base hacia adelante (1m) MIENTRAS levanta el brazo (en paralelo)

**Escenario 2:**
- Levanta el brazo → Mueve base → Rota brazo → Retorna
- Secuencia compleja

**Duración:** ~20 segundos

**Mejor para:** Verificar coordinación de ambos sistemas

---

## 📊 Articulaciones del Brazo

| Articulación | Nombre        | Rango (rad) | Rango (°) | Descripción |
|-------------|---------------|-------------|-----------|------------|
| joint1      | Base          | -π to +π    | -180-+180 | Rotación de la base |
| joint2      | Hombro        | -2.0-+2.0   | -115-+115 | Levanta/baja brazo |
| joint3      | Codo          | -2.0-+2.0   | -115-+115 | Flexión del codo |
| joint4      | Muñeca (R)    | -π to +π    | -180-+180 | Rotación muñeca 1 |
| joint5      | Muñeca (I)    | -π to +π    | -180-+180 | Inclinación muñeca |
| joint6      | Muñeca (R2)   | -π to +π    | -180-+180 | Rotación muñeca 2 |

---

## 🎮 Control Manual (Alternativa)

### Opción A: Publicar comando de velocidad (Base)
```bash
ros2 topic pub /cmd_vel geometry_msgs/msg/Twist "linear: {x: 0.5}" --rate 10
```

### Opción B: Publicar trayectoria (Brazo)
```bash
ros2 topic pub /xarm6_traj_controller/joint_trajectory trajectory_msgs/msg/JointTrajectory '{
  joint_names: [joint1, joint2, joint3, joint4, joint5, joint6],
  points: [
    {
      positions: [0.0, -1.57, 1.57, 0.0, 0.0, 0.0],
      velocities: [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
      time_from_start: {sec: 3}
    }
  ]
}' --once
```

### Opción C: Monitorear estado
```bash
# Ver estado de articulaciones en tiempo real
ros2 topic echo /joint_states

# Ver velocidades de comando
ros2 topic echo /cmd_vel

# Ver información de controlador
ros2 service call /controller_manager/list_controllers controller_manager_msgs/srv/ListControllers
```

---

## 🔍 Verificación del Sistema

### Verificar que todo está corriendo:
```bash
# Ver nodos activos
ros2 node list

# Ver tópicos disponibles
ros2 topic list

# Ver servicios disponibles
ros2 service list
```

### Verificar controladores:
```bash
ros2 service call /controller_manager/list_controllers controller_manager_msgs/srv/ListControllers
```

Deberías ver:
- `joint_state_broadcaster` (estado de articulaciones)
- `xarm6_traj_controller` (control del brazo)
- `mbot_traj_controller` (control de la base)

---

## ⚠️ Troubleshooting

### Problema: "El brazo no se mueve"
**Solución:**
1. Espera 20 segundos después de lanzar
2. Verifica: `ros2 topic list | grep xarm`
3. Revisa: `ros2 service call /controller_manager/list_controllers controller_manager_msgs/srv/ListControllers`
4. Mira logs de Gazebo en la terminal del launch

### Problema: "Gazebo se abre pero no veo el robot"
**Solución:**
1. Aumenta la altura Z en el spawn (ya está a 1.0m)
2. Revisa que el URDF se genere correctamente
3. Mira los logs de stderr en terminal

### Problema: "El robot se mueve lentamente"
**Solución:**
- Aumenta el parámetro `speed` en el script
- O reduce el valor de `duration` en movimientos del brazo

### Problema: "Errores de conexión ROS2"
**Solución:**
1. Asegúrate de haber corrido `source install/setup.bash`
2. Comprueba que ROS2 esté instalado: `ros2 --version`
3. Reinicia el bash shell

---

## 📝 Ejemplos de Poses Personalizadas

### Pose: Brazo recto hacia adelante
```python
[0.0, -0.5, 0.5, 0.0, 0.0, 0.0]
```

### Pose: Brazo totalmente levantado
```python
[0.0, -1.57, 1.57, 0.0, 0.0, 0.0]
```

### Pose: Brazo a la izquierda
```python
[1.57, -1.0, 1.0, 0.0, 0.0, 0.0]
```

### Pose: Brazo a la derecha
```python
[-1.57, -1.0, 1.0, 0.0, 0.0, 0.0]
```

---

## ✅ Checklist de Funcionalidad

- [ ] Base móvil se mueve hacia adelante
- [ ] Base móvil se mueve hacia atrás
- [ ] Brazo se levanta
- [ ] Brazo rota hacia los lados
- [ ] Brazo retorna a posición inicial
- [ ] Base y brazo pueden moverse simultáneamente
- [ ] RViz muestra actualización de TF en tiempo real
- [ ] Gazebo muestra movimientos suave sin interferencias

---

## 🚀 Próximos Pasos

1. **MoveIt Integration**: Usar MoveIt para planificación automática
2. **Sensores**: Integrar cámara, LIDAR para toma de decisiones
3. **Visión**: Usar la cámara D435i para manipulación visual
4. **GUI**: Crear interfaz de usuario en lira_gui para control
5. **Automatización**: Crear secuencias de tareas complejas

---

**Última actualización:** 09/06/2026
**Archivos de prueba:** `final_project/final_project/test_*.py`
**Documentación:** `ARM_CONTROL_GUIDE.md`

