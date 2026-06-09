# Proyecto Final — Robot de Propósito General

**Materia:** Robots Móviles / Temas Selectos de Mecatrónica  
**Profesor:** Dr. Marco Antonio Negrete Villanueva  
**Semestre:** 2026-2  
**Institución:** Facultad de Ingeniería, UNAM  
**Autor:** Zambrano Miranda Isaac Jaciel  
**Rama:** `zambrano_miranda`  

---

## Objetivo

Desarrollar un sistema donde un robot móvil simulado pueda recibir instrucciones en lenguaje natural, interpretar la intención del usuario, generar un plan de acción usando un modelo de lenguaje grande (Ollama/llama3.2:3b), ejecutar las acciones disponibles y responder cuando no puede realizar algo.

---

## Arquitectura del sistema

```
Voz del usuario
      ↓
speech2text (faster_whisper) → /sp_rec/recognized
      ↓
sm_planner (máquina de estados)
      ↓
Ollama llama3.2:3b / reglas de palabras clave
      ↓
Plan de acciones: NAVIGATE, SPEAK, DETECT, MANIPULATE, STOP
      ↓
┌─────────────────────────────────────────┐
│  NAVIGATE → /goal_pose → pure_pursuit   │
│  SPEAK    → /tts_query → text2speech    │
│  DETECT   → /yolo/detections → YOLO     │
│  MANIPULATE → /xarm6_traj_controller    │
│  STOP     → /cmd_vel (velocidad cero)   │
└─────────────────────────────────────────┘
```

---

## Módulos del curso integrados

| Módulo | Descripción | Estado |
|--------|-------------|--------|
| `speech2text` | Reconocimiento de voz con Faster Whisper | ✅ |
| `text2speech` | Síntesis de voz con Piper TTS | ✅ |
| `llm_planning` | Planificación con Ollama (llama3.2:3b) | ✅ |
| `neural_networks/yolo` | Detección de objetos con YOLOv8 | ✅ |
| `path_planner/a_star` | Planeación de rutas con A* | ✅ |
| `path_planner/cost_map` | Mapa de costos e inflación de obstáculos | ✅ |
| `path_planner/path_smoothing` | Suavizado de trayectorias | ✅ |
| `path_planner/pot_fields` | Evasión de obstáculos por campos potenciales | ✅ |
| `path_planner/rrt` | Planeación por árboles aleatorios (RRT) | ✅ |
| `path_follower/pure_pursuit` | Seguimiento de trayectoria Pure Pursuit | ✅ |
| `path_follower/stanley` | Seguimiento de trayectoria Stanley | ✅ |
| `manipulation/ik_numeric` | Cinemática inversa Newton-Raphson | ✅ |
| `house_simul` | Simulación del entorno doméstico | ✅ |
| `final_project/sm_planner` | Máquina de estados principal | ✅ |

---

## Dependencias

```bash
# ROS2 Jazzy (ya instalado)
# Ollama
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3.2:3b

# Python
pip install ultralytics "numpy<2" faster-whisper --break-system-packages
```

---

## Compilar

```bash
cd ~/Mobile-Robots-2026-2/ros2_ws
colcon build
source install/setup.bash
```

---

## Ejecutar el sistema completo

Abrir 7 terminales. En cada una correr primero:
```bash
cd ~/Mobile-Robots-2026-2/ros2_ws && source install/setup.bash
```

**T1 — Simulación:**
```bash
ros2 launch house_simul house_simul.launch.py
```

**T2 — Navegación:**
```bash
ros2 launch motion_planning motion_planning.launch.py
```

**T3 — Seguidor de trayectoria:**
```bash
ros2 run path_follower pure_pursuit
```

**T4 — Síntesis de voz:**
```bash
ros2 run text2speech t2s
```

**T5 — Nodo principal (máquina de estados):**
```bash
ros2 run final_project sm_planner
```

**T6 — Reconocimiento de voz:**
```bash
ros2 run speech2text faster_whisper_asr
```

**T7 — Detección de objetos:**
```bash
ros2 run neural_networks yolo
```

---

## Comandos de voz soportados

| Ejemplo | Acción |
|---------|--------|
| "ve al refri" | Navega al refrigerador |
| "ve a la mesa y luego al sofá" | Navega a múltiples destinos |
| "busca una silla" | Detecta el objeto con YOLO |
| "trae el vaso" | Navega, detecta e intenta manipular |
| "robot vuela" | Responde "No puedo volar" |
| "detente" | Publica velocidad cero |
| "dime qué puedes hacer" | Describe capacidades |

---

## Destinos disponibles

| Nombre | Coordenadas (x, y) |
|--------|-------------------|
| home | 0.0, 0.0 |
| refrigerator | 10.35, 0.39 |
| kitchen | 10.53, -2.26 |
| table | 8.92, 1.41 |
| sofa | 2.45, 1.15 |
| tv | 2.98, -2.97 |
| bed | -3.95, 2.25 |
| door | 10.29, -2.71 |
| stove | 5.59, 0.78 |

---

## Tópicos principales

| Tópico | Tipo | Dirección |
|--------|------|-----------|
| `/sp_rec/recognized` | `std_msgs/String` | Entrada |
| `/goal_pose` | `geometry_msgs/PoseStamped` | Salida |
| `/tts_query` | `std_msgs/String` | Salida |
| `/cmd_vel` | `geometry_msgs/Twist` | Salida |
| `/yolo/detections` | `std_msgs/String` (JSON) | Entrada |
| `/xarm6_traj_controller/joint_trajectory` | `trajectory_msgs/JointTrajectory` | Salida |
| `/navigation/goal_reached` | `std_msgs/Bool` | Entrada |

---

## Limitaciones conocidas

- El gripper del xarm6 no funciona de forma confiable en la simulación actual. La acción MANIPULATE mueve el brazo a posiciones predefinidas pero no garantiza agarre real.
- El reconocimiento de voz puede captar el audio del TTS. Se implementó un filtro de ruido y cooldown para mitigarlo.
- Las coordenadas de destinos fueron calibradas manualmente en RViz y pueden requerir ajuste fino.

---

## Fixes aplicados

- `cost_map.py`: Fix `ZeroDivisionError` cuando `map_res = 0` al inicio.
- `pure_pursuit.py`: Fix `IndexError` cuando A* devuelve path vacío.
- `faster_whisper_asr.py`: Cambio de `language="zh"` a `language="es"` y umbral de potencia ajustado.
