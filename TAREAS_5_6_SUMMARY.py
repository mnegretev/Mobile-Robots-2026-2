#!/usr/bin/env python3
"""
RESUMEN: TAREAS 5 Y 6 - A* Y COMPARACIÓN CON RRT
Mobile Robots - FI-UNAM 2026-2
"""

def main():
    summary = """
╔════════════════════════════════════════════════════════════════════════════════╗
║           AUTOMATIZACIÓN TAREAS 5 Y 6: A* Y COMPARACIÓN CON RRT              ║
║                          Mobile Robots - FI-UNAM 2026-2                       ║
╚════════════════════════════════════════════════════════════════════════════════╝

📋 TAREA 5: Implementar y probar A*
✅ TAREA 6: Comparar A* vs RRT

════════════════════════════════════════════════════════════════════════════════

✅ HERRAMIENTAS CREADAS:

1. TEST_ASTAR_EXPERIMENTS.PY
   📝 Prueba automáticamente A* con:
      • 4 puntos meta (mismos que RRT)
      • 4 valores de cost_radius: [0.1, 0.2, 0.3, 0.5]
      • Con/sin diagonales: [False, True]
   
   📊 Total: 32 experimentos (4×4×2)
   
   🚀 Ejecución:
      ros2 run path_planner test_astar
      ⏳ Tiempo: 5-10 minutos

   📁 Genera: astar_experiments_YYYYMMDD_HHMMSS.csv

────────────────────────────────────────────────────────────────────────────────

2. COMPARE_ALGORITHMS.PY
   📝 Compara RRT vs A* automáticamente
   
   📊 Genera:
      • Tabla resumen RRT
      • Tabla resumen A*
      • Tabla comparativa por punto meta
      • Formato Markdown para documento
   
   🚀 Ejecución:
      python3 compare_algorithms.py rrt_experiments_*.csv astar_experiments_*.csv
      
────────────────────────────────────────────────────────────────────────────────

3. TAREAS_5_6_GUIDE.MD
   📝 Guía completa con:
      • Procedimiento paso a paso
      • Variables y parámetros a probar
      • Estructura para reporte
      • Análisis esperado

════════════════════════════════════════════════════════════════════════════════

🚀 PROCEDIMIENTO RÁPIDO:

PASO 1: Compilar
─────────────────
cd ~/Fac_Inge/Mobile-Robots-2026-2/ros2_ws
colcon build --packages-select path_planner
source install/setup.bash

PASO 2: Iniciar Servicios (4 Terminales Diferentes)
───────────────────────────────────────────────────
Terminal A - Map Server:
  ros2 run map_server map_server ~/path/to/your/map.yaml

Terminal B - Cost Map:
  ros2 run path_planner cost_map

Terminal C - A* Node:
  ros2 run path_planner a_star

Terminal D - Experimentos (Espera 5-10 minutos):
  ros2 run path_planner test_astar
  → Genera: astar_experiments_20260303_120000.csv

PASO 3: Analizar Resultados
───────────────────────────
Análisis A* individual:
  python3 ros2_ws/src/navigation/path_planner/path_planner/analyze_results.py \
    astar_experiments_20260303_120000.csv

Comparación RRT vs A*:
  python3 ros2_ws/src/navigation/path_planner/path_planner/compare_algorithms.py \
    ros2_ws/rrt_experiments_20260224_012246.csv \
    astar_experiments_20260303_120000.csv

════════════════════════════════════════════════════════════════════════════════

📊 PARÁMETROS A PROBAR:

A* (Tarea 5):
─────────────
• Cost Radius: [0.1, 0.2, 0.3, 0.5]
• Diagonales: [False, True]
• Puntos Meta: 4 diferentes (0,0)→(5,5), (0,0)→(8,3), etc.

RRT (Tarea 4 - Ya tienes datos):
────────────────────────────────
• Epsilon: [0.3, 0.5, 1.0, 1.5]
• Max N: [100, 500, 1000, 5000]
• Puntos Meta: 4 diferentes

════════════════════════════════════════════════════════════════════════════════

📈 DATOS REGISTRADOS (Por experimento):

Para A*:
  ✓ Start X, Y (posición inicial)
  ✓ Goal X, Y (posición objetivo)
  ✓ Cost Radius (parámetro)
  ✓ Use Diagonals (parámetro)
  ✓ Success (¿ruta encontrada?)
  ✓ Time (ms) (tiempo ejecución)
  ✓ Path Length (número de waypoints)

Para RRT:
  ✓ Start X, Y
  ✓ Goal X, Y
  ✓ Epsilon
  ✓ Max N
  ✓ Success
  ✓ Time (ms)
  ✓ Path Length

════════════════════════════════════════════════════════════════════════════════

📋 TABLAS GENERADAS AUTOMÁTICAMENTE:

Tabla 1: Características de A* (Tarea 5 - Punto 11)
───────────────────────────────────────────────────
| Start | Goal | Cost Radius | Diagonales | Éxitos | Tiempo Promedio |
| (0,0) | (5,5) | 0.1 | No | 4/4 | 45.23 ms |
| ... | ... | ... | ... | ... | ... |

→ Generada por: analyze_results.py

Tabla 2: Comparación RRT vs A* (Tarea 6 - Punto 12)
───────────────────────────────────────────────────
| Métrica | RRT | A* | Ganador |
| Tasa Éxito | 100% | ??? | ??? |
| Tiempo Promedio | 946.52 ms | ??? ms | ??? |
| Tiempo Mínimo | 6.06 ms | ??? ms | ??? |
| Tiempo Máximo | 4085.62 ms | ??? ms | ??? |

→ Generada por: compare_algorithms.py

════════════════════════════════════════════════════════════════════════════════

💡 ANÁLISIS PARA TU REPORTE (Tarea 6):

Plataforma:
  ✓ Sistema Operativo: Ubuntu 24.04
  ✓ ROS2 Versión: Jazzy
  ✓ Mapa: [tu mapa aquí]
  ✓ Robot: [tu robot aquí]

Variables (Tarea 5):
  ✓ ¿Cómo afecta cost_radius a éxito?
  ✓ ¿Importan los movimientos diagonales?
  ✓ ¿Cambia el tiempo con los parámetros?

Comparación (Tarea 6):
  ✓ RRT vs A*: ¿Cuál es más rápido?
  ✓ ¿Cuál encuentra más rutas?
  ✓ ¿Cuál da rutas más cortas?
  ✓ ¿Cuál es más consistente?

════════════════════════════════════════════════════════════════════════════════

📁 ARCHIVOS CSV ESPERADOS:

Después de los experimentos:
  • rrt_experiments_20260224_012246.csv        (de Tarea 4)
  • astar_experiments_20260303_120000.csv      (nuevo)

════════════════════════════════════════════════════════════════════════════════

🎯 ESTRUCTURA PARA TU DOCUMENTO:

TAREA 5 (Puntos 10-11):
┌─ Punto 10: Descripción de pruebas
│  → Parámetros probados
│  → Puntos meta
│  └─ Con/sin diagonales
└─ Punto 11: Tabla de resultados
   → Generada automáticamente por analyze_results.py
   → Incluir 2+ capturas de pantalla

TAREA 6 (Punto 12):
┌─ Desarrollo:
│  ├─ Descripción plataforma
│  ├─ Variables de prueba
│  └─ Datos registrados
├─ Resultados:
│  ├─ Tabla comparativa
│  ├─ Gráficos (opcional)
│  └─ Datos de Tarea 4 incluidos
└─ Análisis:
   ├─ Desempeño A*
   ├─ Desempeño RRT
   └─ Conclusiones comparativas

════════════════════════════════════════════════════════════════════════════════

⚡ COMANDOS COPIAR-PEGAR:

# 1. Build
cd ~/Fac_Inge/Mobile-Robots-2026-2/ros2_ws
colcon build --packages-select path_planner
source install/setup.bash

# 2. Terminal A (map_server)
ros2 run map_server map_server ~/path/to/map.yaml

# 3. Terminal B (cost_map)
ros2 run path_planner cost_map

# 4. Terminal C (a_star)
ros2 run path_planner a_star

# 5. Terminal D (experiments - ⏳ 5-10 min)
ros2 run path_planner test_astar

# 6. Analyze A*
python3 src/navigation/path_planner/path_planner/analyze_results.py \
  astar_experiments_*.csv

# 7. Compare RRT vs A*
python3 src/navigation/path_planner/path_planner/compare_algorithms.py \
  rrt_experiments_20260224_012246.csv \
  astar_experiments_*.csv

════════════════════════════════════════════════════════════════════════════════

❓ PREGUNTAS COMUNES:

P: ¿Necesito modificar los parámetros de prueba?
R: Los predeterminados están bien. Si quieres otros, edita las listas en:
   - test_astar_experiments.py (línea ~78-80)

P: ¿Qué pasa si A* es mucho más lento que RRT?
R: Es normal. Depende del mapa. Incluye en análisis por qué.

P: ¿Cómo añado mis comentarios al análisis?
R: El script genera tablas. Tú añades interpretación y conclusiones.

P: ¿Puedo usar datos de RRT que ejecuté antes?
R: SÍ. Reutiliza: rrt_experiments_20260224_012246.csv

════════════════════════════════════════════════════════════════════════════════

📖 DOCUMENTACIÓN COMPLETA:

Ver: TAREAS_5_6_GUIDE.md

════════════════════════════════════════════════════════════════════════════════

¡Éxito con tus tareas! 🚀

Para dudas específicas, consulta TAREAS_5_6_GUIDE.md o los comentarios
en los scripts test_astar_experiments.py y compare_algorithms.py

════════════════════════════════════════════════════════════════════════════════
"""
    print(summary)

if __name__ == '__main__':
    main()
