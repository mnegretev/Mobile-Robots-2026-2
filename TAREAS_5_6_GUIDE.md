# TAREAS 5 Y 6: A* Y COMPARACIÓN CON RRT

## Resumen

Para las tareas 5 y 6, necesitas:
1. **(Tarea 5)** Implementar A*, probar con diferentes parámetros y registrar resultados
2. **(Tarea 6)** Comparar desempeño A* vs RRT

He creado herramientas automatizadas para hacer esto sin trabajo manual.

---

## Archivos Creados

### 1. `test_astar_experiments.py` 
Script que prueba A* automáticamente con:
- **4 puntos meta diferentes** (mismos que en RRT)
- **4 valores de cost_radius**: [0.1, 0.2, 0.3, 0.5]
- **Con/sin diagonales**: [False, True]

Total: **32 experimentos** (4 goals × 4 radios × 2 opciones diagonales)

Genera: `astar_experiments_YYYYMMDD_HHMMSS.csv`

### 2. `compare_algorithms.py`
Script que compara RRT vs A* generando:
- Tablas comparativas de ambos algoritmos
- Estadísticas por parámetro
- Formato Markdown para tu documento

---

## Procedimiento (Mismo que RRT)

### Terminal A: Map Server
```bash
cd ~/Fac_Inge/Mobile-Robots-2026-2
ros2 run map_server map_server ~/path/to/your/map.yaml
```

### Terminal B: Cost Map
```bash
cd ~/Fac_Inge/Mobile-Robots-2026-2
source ros2_ws/install/setup.bash
ros2 run path_planner cost_map
```

### Terminal C: A* Node
```bash
cd ~/Fac_Inge/Mobile-Robots-2026-2
source ros2_ws/install/setup.bash
ros2 run path_planner a_star
```

### Terminal D: Ejecutar Experimentos (⏳ 5-10 minutos)
```bash
cd ~/Fac_Inge/Mobile-Robots-2026-2
source ros2_ws/install/setup.bash
ros2 run path_planner test_astar
```

Generará: `astar_experiments_20260303_120000.csv` (nombre con timestamp)

---

## Análisis de Resultados

### Individual (Solo A*)
```bash
python3 ros2_ws/src/navigation/path_planner/path_planner/analyze_results.py astar_experiments_20260303_120000.csv
```

### Comparación (RRT vs A*)
```bash
python3 ros2_ws/src/navigation/path_planner/path_planner/compare_algorithms.py \
  ros2_ws/rrt_experiments_20260224_012246.csv \
  astar_experiments_20260303_120000.csv
```

---

## Variables Registradas

### Para cada experimento se registra:

| Data | Descripción |
|------|-------------|
| Start X, Y | Punto inicial |
| Goal X, Y | Punto objetivo |
| Cost Radius | Radio de costo usado (A*) |
| Use Diagonals | ¿Movimientos diagonales? (A*) |
| Success | ¿Se encontró ruta? (true/false) |
| Time (ms) | Tiempo de ejecución en milisegundos |
| Path Length | Número de puntos en la ruta |

### En RRT (Tarea 4)

| Data | Descripción |
|------|-------------|
| Start X, Y | Punto inicial |
| Goal X, Y | Punto objetivo |
| Epsilon | Tamaño de paso |
| Max N | Máximo de iteraciones |
| Success | ¿Se encontró ruta? |
| Time (ms) | Tiempo en milisegundos |
| Path Length | Número de puntos en ruta |

---

## Tablas para Tu Documento

### Tabla 1: Resultados A* (Punto 11)

```markdown
| Start | Goal | Cost Radius | Diagonals | Éxitos | Tiempo Promedio |
|-------|------|-------------|-----------|--------|-----------------|
| (0,0) | (5,5) | 0.1 | No | 2/2 | 45.32 ms |
| (0,0) | (5,5) | 0.1 | Si | 2/2 | 48.21 ms |
| ... | ... | ... | ... | ... | ... |
```

El script `analyze_results.py` lo genera automáticamente.

### Tabla 2: Comparación RRT vs A* (Punto 12)

```markdown
| Métrica | RRT | A* | Ganador |
|---------|-----|----|----|
| Tasa de Éxito | 100% | 100% | Empate |
| Tiempo Promedio | 946.52 ms | ??? ms | ??? |
| Tiempo Mínimo | 6.06 ms | ??? ms | ??? |
| Tiempo Máximo | 4085.62 ms | ??? ms | ??? |
```

El script `compare_algorithms.py` lo genera automáticamente.

---

## Pasos Completos para Tarea 5

1. **Implementar A*** ✅ (ya lo hiciste)  
2. **Compilar**
   ```bash
   cd ~/Fac_Inge/Mobile-Robots-2026-2/ros2_ws
   colcon build --packages-select path_planner
   source install/setup.bash
   ```

3. **Ejecutar experimentos**
   - Inicia Terminals A, B, C (map_server, cost_map, a_star)
   - En Terminal D: `ros2 run path_planner test_astar`
   - Espera 5-10 minutos
   - Genera `astar_experiments_*.csv`

4. **Generar análisis**
   ```bash
   python3 ros2_ws/src/navigation/path_planner/path_planner/analyze_results.py astar_experiments_*.csv
   ```

5. **Captura pantallas**
   - Experimentos ejecutándose
   - Tabla de resultados del análisis
   - RViz mostrando una ruta A* planificada

6. **Para el documento**
   - Copia las tablas generadas
   - Incluye capturas
   - Describe parámetros probados

---

## Pasos Completos para Tarea 6 (Comparación)

1. **Reutiliza datos RRT** (Tarea 4)
   - Deberías tener: `ros2_ws/rrt_experiments_20260224_012246.csv`
   - Si no, necesitas volver a ejecutar RRT

2. **Ejecuta experimentos A*** (mismo que Tarea 5)
   - Genera un nuevo `astar_experiments_*.csv`

3. **Compara algoritmos**
   ```bash
   python3 ros2_ws/src/navigation/path_planner/path_planner/compare_algorithms.py \
     ros2_ws/rrt_experiments_20260224_012246.csv \
     astar_experiments_20260303_120000.csv
   ```

4. **Genera tablas comparativas**
   El script genera automáticamente:
   - Resumen RRT
   - Resumen A*
   - Tabla comparativa por meta
   - Formato Markdown listo para copiar

5. **Para el documento**
   - Describe plataforma de pruebas (mismo mapa, mismo ROS)
   - Describe variables (ε, N para RRT; cost_radius, diagonales para A*)
   - Incluye tablas comparativas
   - Análisis: ¿cuál es mejor? ¿Por qué?

---

## Análisis Esperado para Tarea 6

Cuando compares, busca responder:

| Pregunta | Busca |
|----------|-------|
| ¿Cuál tiene mejor tasa de éxito? | Porcentaje de rutas encontradas |
| ¿Cuál es más rápido? | Tiempo promedio de ejecución |
| ¿Cuál es más predecible? | Menor variación en tiempos |
| ¿Cuál da mejores rutas? | Menor longitud de ruta |
| ¿Cómo afectan los parámetros? | Epsilon/N en RRT, cost_radius/diagonales en A* |

---

## Archivos CSV Generados

Después de los experimentos tendrás:

```
ros2_ws/
├── rrt_experiments_20260224_012246.csv      ← De Tarea 4
├── astar_experiments_20260303_120000.csv    ← Tu nuevo A*
└── (resultados de análisis se imprimen en terminal)
```

---

## Troubleshooting

| Problema | Solución |
|----------|----------|
| "Waiting for path planning service" | Verifica que A* esté en Terminal C |
| "ImportError: No module pandas" | El script funciona sin pandas, genera sumario de todos modos |
| Los tiempos son diferentes entre runs | Normal - depende de carga del sistema |
| A* es mucho más lento que RRT | Posible - depende del mapa y parámetros |

---

## Para Tu Reporte

La estructura debería ser:

```
##Desarrollo (Descripción de pasos)
- Plataforma: ROS2 Jazzy, Ubuntu 24.04, [tu robot]
- Mapa: [descripción del mapa]
- Variables RRT: ε ∈ {0.3, 0.5, 1.0, 1.5}, N ∈ {100, 500, 1000, 5000}
- Variables A*: cost_radius ∈ {0.1, 0.2, 0.3, 0.5}, diagonales ∈ {No, Sí}
- Datos registrados: Éxito, Tiempo ejecución, Longitud ruta

## Resultados (Tablas y gráficas)
- [Tabla Resultados A*]
- [Tabla Comparativa RRT vs A*]
- [Gráfico opcional: tiempo vs parámetros]

## Análisis
- RRT: [conclusiones]
- A*: [conclusiones]
- Comparación: [A* es mejor porque X, RRT es mejor porque Y]
```

---

## Comandos Rápidos (Copiar-Pegar)

```bash
# Build
cd ~/Fac_Inge/Mobile-Robots-2026-2/ros2_ws
colcon build --packages-select path_planner
source install/setup.bash

# Run A* experiments (después de Terminals A, B, C)
ros2 run path_planner test_astar

# Analyze A*
python3 src/navigation/path_planner/path_planner/analyze_results.py astar_experiments_*.csv

# Compare RRT vs A*
python3 src/navigation/path_planner/path_planner/compare_algorithms.py \
  rrt_experiments_20260224_012246.csv \
  astar_experiments_*.csv
```

---

¿Necesitas ayuda con algo específico? Puedo:
- Ajustar los parámetros de prueba
- Generar gráficos automatizados
- Ayudarte a interpretar los resultados
