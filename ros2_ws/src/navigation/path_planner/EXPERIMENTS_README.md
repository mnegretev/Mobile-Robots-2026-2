# RRT Algorithm Automated Experiments

Este directorio contiene herramientas para automatizar las pruebas del algoritmo RRT.

## Archivos Creados

### 1. `test_rrt_experiments.py`
Script que ejecuta automáticamente múltiples pruebas del algoritmo RRT con diferentes parámetros:
- **Puntos meta**: 4 diferentes combinaciones (puedes modificarlos en `test_goals`)
- **Valores de ε (epsilon)**: [0.3, 0.5, 1.0, 1.5] (puedes modificarlos)
- **Valores de N (max_n)**: [100, 500, 1000, 5000] (puedes modificarlos)

Para cada combinación registra:
- Si se encontró la ruta (éxito/fracaso)
- Tiempo de ejecución en milisegundos
- Longitud del camino

### 2. `analyze_results.py`
Script que analiza los resultados guardados en CSV y genera:
- Tablas formateadas
- Estadísticas globales
- Tablas por parámetro (epsilon y N)
- Formato Markdown para incluir en documentos

### 3. `rrt_experiments.launch.py`
Launch file que inicia automáticamente:
- El nodo de cost_map
- El nodo RRT
- El script de experimentos

## Cómo Usar

### Opción 1: Método Manual (Recomendado para control total)

**Paso 1: Compilar el paquete**
```bash
cd ~/Fac_Inge/Mobile-Robots-2026-2
colcon build --packages-select path_planner
source install/setup.bash
```

**Paso 2: En Terminal 1 - Iniciar el servidor de mapa**
```bash
# Asume que tienes un map_server corriendo o puedes usar tu simulador
ros2 run map_server map_server ~/path/to/your/map.yaml
```

**Paso 3: En Terminal 2 - Iniciar cost_map y RRT**
```bash
ros2 run path_planner cost_map
# En otra terminal
ros2 run path_planner rrt
```

**Paso 4: En Terminal 3 - Ejecutar experimentos**
```bash
ros2 run path_planner test_experiments
```

Esto generará un archivo CSV como `rrt_experiments_20260224_123456.csv`

**Paso 5: Analizar resultados**
```bash
python3 analyze_results.py rrt_experiments_20260224_123456.csv
```

### Opción 2: Usando el Launch File

```bash
ros2 launch path_planner rrt_experiments.launch.py
```

## Personalizar los Experimentos

Para modificar los parámetros de testing, edita `test_rrt_experiments.py`:

```python
# Línea ~76: Define los puntos meta
test_goals = [
    ([0.0, 0.0], [5.0, 5.0]),      # Start -> Goal
    ([0.0, 0.0], [8.0, 3.0]),
    # Agrega más puntos aquí
]

# Línea ~79: Define los valores de epsilon
epsilon_values = [0.3, 0.5, 1.0, 1.5]

# Línea ~80: Define los valores de N
max_n_values = [100, 500, 1000, 5000]
```

## Salida de Resultados

### Archivo CSV
El script genera un archivo `rrt_experiments_YYYYMMDD_HHMMSS.csv` con columnas:
- Start X, Start Y: Posición inicial
- Goal X, Goal Y: Posición objetivo
- Epsilon: Parámetro ε usado
- Max N: Número máximo de iteraciones usado
- Success: true/false (¿Se encontró la ruta?)
- Time (ms): Tiempo de ejecución en milisegundos
- Path Length: Número de waypoints en la ruta

### Tablas Formateadas
Al ejecutar `analyze_results.py` obtendrás:

1. **TABLE 1**: Tasa de éxito y tiempo promedio por meta y epsilon
2. **TABLE 2**: Tasa de éxito y tiempo promedio por meta y N
3. **TABLE 3**: Tabla detallada de todos los experimentos
4. **STATISTICS**: Estadísticas generales incluyendo:
   - Tasa de éxito global
   - Tiempos mínimo, máximo y promedio
   - Tasas de éxito por epsilon
   - Tasas de éxito por N

5. **MARKDOWN FORMAT**: Salida en formato Markdown lista para copiar a tu documento

## Ejemplo de Salida

```
==================================================
STATISTICS
==================================================

Total Experiments: 64
Successful: 48/64 (75.0%)
Average Execution Time: 234.56 ms
Min Execution Time: 45.23 ms
Max Execution Time: 956.78 ms

Success Rate by Epsilon:
  ε=0.3: 10/16 (62.5%)
  ε=0.5: 12/16 (75.0%)
  ε=1.0: 13/16 (81.3%)
  ε=1.5: 13/16 (81.3%)

Success Rate by Max N:
  N=  100:  8/16 (50.0%), Avg Time= 89.45ms
  N=  500: 12/16 (75.0%), Avg Time=234.56ms
  N= 1000: 14/16 (87.5%), Avg Time=456.78ms
  N= 5000: 14/16 (87.5%), Avg Time=678.90ms
```

## Notas Importantes

1. **Tiempo de ejecución**: Dependiendo del número total de experimentos (goal × ε × N), la ejecución puede tomar varios minutos.
2. **Reproducibilidad**: Aunque RRT es aleatorio, ejecutar varios experimentos por parámetro ayuda a obtener estadísticas confiables.
3. **Mapa**: Asegúrate que tu mapa (simulador o map_server) esté disponible antes de ejecutar los experimentos.
4. **Parámetros del mapa**: Puedes ajustar `inflation_radius` y `cost_radius` en el launch file si es necesario.

## Troubleshooting

**Error: "Waiting for path planning service"**
- Asegúrate de que el nodo RRT está corriendo en otra terminal
- Verifica que el nodo cost_map también está disponible

**Error: "Couldn't parse parameter override rule"**
- Recuerda usar guiones bajos en los nombres de parámetros: `inflation_radius` NO `inflation radius`

**Archivo CSV no se crea**
- Verifica que tengas permisos de escritura en el directorio donde ejecutas el script
- Revisa la salida de la terminal para mensajes de error

## Para tu Documento

Puedes incluir:
1. **Capturas de pantalla** de los resultados de `analyze_results.py`
2. **Copiar las tablas** en formato Markdown generadas por el script
3. **Incluir gráficos voluntarios** de los datos (no requeridos, pero mejora presentación)

---

¡Éxito con tus experimentos! 🚀
