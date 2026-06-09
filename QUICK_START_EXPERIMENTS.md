# GUÍA RÁPIDA: Automatizar Experimentos de RRT

## Resumen
He creado herramientas para **automatizar completamente** tus experimentos en lugar de hacerlo manualmente.

## Archivos Creados

| Archivo | Propósito |
|---------|-----------|
| `test_rrt_experiments.py` | Ejecuta múltiples pruebas del RRT automáticamente |
| `analyze_results.py` | Procesa resultados y genera tablas |
| `rrt_experiments.launch.py` | Launch file para ejecutar todo |
| `run_rrt_experiments.sh` | Script bash para automatizar el flujo completo |
| `EXPERIMENTS_README.md` | Documentación completa |

## Pasos Rápidos (5 minutos de setup)

### 1️⃣ Compilar el Paquete
```bash
cd ~/Fac_Inge/Mobile-Robots-2026-2
colcon build --packages-select path_planner
source install/setup.bash
```

### 2️⃣ Iniciar Servicios Requeridos (en Terminal A)
```bash
# Inicia tu mapa/simulador con map_server
# Ejemplo:
ros2 run map_server map_server ~/path/to/map.yaml
```

### 3️⃣ Iniciar Nodos ROS2 (en Terminal B)
```bash
# Terminal B1: Inicia cost_map
ros2 run path_planner cost_map

# Terminal B2: Inicia RRT (new terminal)
ros2 run path_planner rrt
```

### 4️⃣ Ejecutar Experimentos (en Terminal C)
```bash
ros2 run path_planner test_experiments
```

**Espera 10-15 minutos...** ⏳

Verás algo como:
```
Test 1/64: Start(0.0, 0.0) -> Goal(5.0, 5.0), ε=0.3, N=100
  Result ✓: Time=234.56ms, Path length=15
Test 2/64: ...
```

El script generará un archivo CSV como: `rrt_experiments_20260224_123456.csv`

### 5️⃣ Generar Tablas (en Terminal C o D)
```bash
python3 -m path_planner.analyze_results rrt_experiments_20260224_123456.csv
```

O copiar el archivo a donde colones analyze_results.py y ejecutar:
```bash
python3 analyze_results.py rrt_experiments_20260224_123456.csv
```

## Salida Esperada

El script `analyze_results.py` genera automáticamente:

### 📊 Tabla 1: Éxito vs Epsilon
```
Goal                                             ε=0.3   ε=0.5   ε=1.0   ε=1.5
(0.0, 0.0) → (5.0, 5.0)     8/10 (80%)  9/10 (90%)  10/10 (100%)  10/10 (100%)
(0.0, 0.0) → (8.0, 3.0)     6/10 (60%)  8/10 (80%)  9/10 (90%)    9/10 (90%)
...
```

### 📊 Tabla 2: Éxito vs N (Iteraciones)
```
Goal                              N=100   N=500   N=1000   N=5000
(0.0, 0.0) → (5.0, 5.0)   4/10    8/10    9/10     10/10
(0.0, 0.0) → (8.0, 3.0)   2/10    6/10    9/10     10/10
...
```

### 📊 Tabla 3: Estadísticas Globales
```
Total Experiments: 64
Successful: 48/64 (75.0%)
Average Time: 234.56 ms
Min: 45.23 ms, Max: 956.78 ms
```

### 📋 Formato Markdown (listo para tu documento)
```markdown
| Epsilon | Success | Total | Rate  |
|---------|---------|-------|-------|
| 0.3     | 10      | 16    | 62.5% |
| 0.5     | 12      | 16    | 75.0% |
| 1.0     | 13      | 16    | 81.3% |
| 1.5     | 13      | 16    | 81.3% |
```

## Personalizar Parámetros

Edita `test_rrt_experiments.py` líneas ~76-80:

```python
# Puntos meta a probar
test_goals = [
    ([0.0, 0.0], [5.0, 5.0]),
    ([0.0, 0.0], [8.0, 3.0]),
    # Agrega más aquí
]

# Valores de ε a probar
epsilon_values = [0.3, 0.5, 1.0, 1.5, 2.0]  # Modifica estos

# Valores de N a probar  
max_n_values = [100, 500, 1000, 5000, 10000]  # Modifica estos
```

## ¿Qué Incluir en tu Documento?

Según lo pedido en el proyecto:

### ✅ Punto 6-7: Tabla de Resultados
Copia directamente la salida de `analyze_results.py` o genera una captura:
```bash
python3 analyze_results.py rrt_experiments_20260224_123456.csv | tee resultados.txt
```

### ✅ Capturas Significativas
Guarda 2+ capturas de pantallas de:
- Terminal mostrando algunos experimentos ejecutándose
- Salida de `analyze_results.py` con las tablas
- Consola de RViz mostrando una ruta planificada

## Script Rápido Todo en Uno (Alternativo)

Si prefieres un solo script bash:
```bash
chmod +x run_rrt_experiments.sh
./run_rrt_experiments.sh build  # Compilar
./run_rrt_experiments.sh run    # Ejecutar (asegúrate de tener terminals A,B,C)
./run_rrt_experiments.sh analyze # Analizar resultados
```

## Troubleshooting

| Problema | Solución |
|----------|----------|
| "Waiting for path planning service" | Verifica que `rrt` node esté corriendo en otra terminal |
| "Waiting for inflated map service" | Verifica que `cost_map` node esté corriendo |
| No hay CSV generado | Revisa que tengas permisos de escritura en el directorio |
| Parámetros no se actualizan | Usa `ros2 param set /rrt_node epsilon 0.5` manualmente |

## Estimado de Tiempo

- **Setup**: 5 min (compilar)
- **Ejecución**: 10-15 min (64 experimentos por defecto)
- **Análisis**: 1 min (generar tablas)
- **Total**: ~20-25 minutos

¡Tienes mucho menos trabajo manual ahora! 🎉

---

¿Preguntas? Revisa `EXPERIMENTS_README.md` para documentación completa.
