# 🗺️ Sistema de Navegación por Ubicaciones Nominadas

## Descripción

El **State Machine Planner (SM Planner)** permite que el robot navegue a ubicaciones predefinidas usando comandos simples como:
- "Ve a la cocina"
- "Navega a la sala"
- "Ve al dormitorio"

---

## 📋 Componentes

### 1. **sm_planner.py** - Nodo principal
```python
# Características:
- LocationDatabase: base de datos de ubicaciones con coordenadas
- SMPlanner: nodo ROS2 que maneja la navegación
- Integración con Nav2 para planificación automática
- Estados de navegación (IDLE, NAVIGATING, ARRIVED, FAILED)
```

### 2. **locations.json** - Configuración de ubicaciones
```json
{
  "kitchen": {
    "position": [-3.0, 0.0],    // [x, y] en metros
    "orientation": 0.0,          // ángulo en radianes
    "description": "Área de cocina"
  }
}
```

### 3. **nav_command_client.py** - Cliente de comandos
```bash
# Enviar comandos de navegación
python3 nav_command_client.py "go to kitchen"
```

---

## 🚀 Uso Rápido

### Terminal 1: Lanzar el robot y el planner
```bash
cd ~/Fac_Inge/Mobile-Robots-2026-2/ros2_ws
source install/setup.bash

# Lanzar robot con todas las capacidades
ros2 launch final_project final_project_utils.launch.py

# En otra ventana del mismo terminal, ejecutar el planner
python3 src/final_project/final_project/sm_planner.py
```

### Terminal 2: Enviar comandos
```bash
python3 src/final_project/final_project/nav_command_client.py --help
```

---

## 🗺️ Definir Ubicaciones

### Opción A: Editar JSON (Recomendado)

1. Abre `locations.json`
2. Agrega nuevas ubicaciones:

```json
"my_room": {
  "position": [1.5, 2.5],
  "orientation": 1.5708,
  "description": "My custom room"
}
```

3. Guarda el archivo

### Opción B: Código Python

En `sm_planner.py`, en `LocationDatabase.__init__()`:

```python
self.locations = {
    'my_location': {
        'position': (1.5, 2.5),
        'orientation': math.pi/4,
        'description': 'My location'
    },
    # ... más ubicaciones
}
```

### Opción C: Agregar en Tiempo de Ejecución

```python
planner = SMPlanner()
planner.locations_db.add_location('my_room', 1.5, 2.5, 0.0)
```

---

## 📊 Formato de Coordenadas

### Sistema de Coordenadas
```
    +Y (norte)
     ↑
     |
+----+----+X (este)
     |
     ↓
   -Y (sur)
```

### Valores de Orientación (radianes)
- `0.0` = Facing +X (east/derecha)
- `π/2` (1.5708) = Facing +Y (north/arriba)
- `π` (3.1416) = Facing -X (west/izquierda)
- `-π/2` (-1.5708) = Facing -Y (south/abajo)

### Ejemplos
```python
# Ubicación 1: Centro del hallway
hallway = (0.0, 0.0, 0.0)

# Ubicación 2: Cocina a la izquierda
kitchen = (-3.0, 0.0, 0.0)

# Ubicación 3: Sala diagonal
living_room = (-1.0, -2.0, math.pi/4)

# Ubicación 4: Habitación a la derecha
bedroom = (2.0, -1.0, -math.pi/2)
```

---

## 🎮 Comandos Soportados

### Formatos válidos:
```bash
"go to kitchen"
"navigate to living room"
"move to bedroom"
"visit bathroom"
"head to garage"
"kitchen"              # Ubicación directa
```

### Palabras clave reconocidas:
- `go to`
- `navigate to`
- `move to`
- `visit`
- `head to`

---

## 🔄 Flujo de Navegación

```
Usuario: "Go to kitchen"
    ↓
Planner: Procesa comando
    ↓
Planner: Busca "kitchen" en LocationDatabase
    ↓
Planner: Crea PoseStamped goal
    ↓
Planner: Envía a Nav2 via NavigateToPose action
    ↓
Nav2: Planifica ruta (A*, RRT*)
    ↓
PathFollower: Sigue ruta (Pure Pursuit o Stanley)
    ↓
Robot: Se mueve hacia la cocina
    ↓
Planner: Recibe resultado (SUCCESS/FAILED)
    ↓
Usuario: Notificado de llegada
```

---

## 📊 Estados de Navegación

| Estado | Significado | Acciones |
|--------|-------------|----------|
| IDLE | Listo para recibir comandos | Esperar comando |
| NAVIGATING | Navegando a destino | En progreso |
| ARRIVED | Llegó al destino | Ejecutar acción |
| FAILED | No pudo llegar | Reintentar/Cancelar |

---

## 🔍 Monitoreo y Diagnóstico

### Ver disponibilidad de ubicaciones:
```bash
ros2 param get /sm_planner locations
```

### Monitorear estado de navegación:
```bash
ros2 topic echo /sm_planner/state
```

### Ver ruta planificada:
```bash
ros2 topic echo /plan
```

### Verificar posición actual:
```bash
ros2 topic echo /odom
```

---

## ⚠️ Troubleshooting

### Problema: "Location not found"
**Solución:** Verificar ortografía en `locations.json` o en el comando

### Problema: "Goal rejected"
**Causas:**
- Nav2 no está corriendo
- Costmap no está inicializado
- Posición fuera del mapa

**Soluciones:**
1. Espera 20 segundos después de lanzar
2. Verifica que costmap se inicialice: `ros2 topic echo /global_costmap/costmap`
3. Verifica posición en mapa

### Problema: "Goal accepted but not reaching"
**Causas:**
- Ruta no existe (obstáculos)
- Planificador no encontró ruta
- Controlador inestable

**Soluciones:**
1. Cambia ubicación destino a un lugar más cercano
2. Verifica que la ruta sea despejada
3. Revisa parámetros de `pure_pursuit` en `launch/final_project_utils.launch.py`

---

## 🎯 Ejemplo Completo

```python
#!/usr/bin/env python3
import rclpy
from sm_planner import SMPlanner
import time

def main():
    rclpy.init()
    planner = SMPlanner()
    
    # Secuencia: Kitchen → Living Room → Bedroom → Kitchen
    locations = ['kitchen', 'living_room', 'bedroom', 'kitchen']
    
    for loc in locations:
        print(f'\n📍 Dirigiéndose a {loc}...')
        planner.process_command(f'go to {loc}')
        time.sleep(15)  # Espera a que termine
        print(f'Status: {planner.get_status()}')
        time.sleep(2)

if __name__ == '__main__':
    main()
```

---

## 📝 Próximas Mejoras

1. **Reconocimiento de voz**: Integrar STT (Speech-to-Text)
2. **Aprendizaje de ubicaciones**: Guardar ubicaciones automáticamente
3. **Mapeo automático**: Crear mapa de ubicaciones en tiempo real
4. **Múltiples robots**: Navegación colaborativa
5. **Ejecución de tareas**: "Ve a la cocina y trae el café"

---

**Última actualización:** 09/06/2026
**Versión:** 1.0
**Requisitos:** ROS2, Nav2, final_project package
