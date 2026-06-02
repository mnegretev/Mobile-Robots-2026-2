# Proyecto Final — Control de Robot Móvil por Comandos de Voz

Robots Móviles, FI-UNAM, 2026-2. Dominguez Palacios Jesus Alejandro.

El robot recibe una instrucción hablada (es/en), la interpreta como un comando
cerrado, navega al lugar correspondiente usando la navegación que ya tienes
(A* + pure pursuit) y avisa por voz al llegar.

## Flujo

```
voz -> speech_recognition_node -> /recognized_speech
    -> command_interpreter -> /goal_pose -> pure_pursuit (A* + seguimiento) -> robot
    -> robot llega -> /navigation/goal_reached -> command_interpreter
    -> /speech -> speech_synthesis_node -> "He llegado al refrigerador"
```

Tu sistema de navegación ya estaba completo: `pure_pursuit.py` se suscribe a
`/goal_pose` y publica `/navigation/goal_reached` al terminar. Este proyecto
solo conecta la voz a esos dos tópicos.

## Nodos de este paquete

| Nodo                      | Función                                            |
|---------------------------|----------------------------------------------------|
| `command_interpreter`     | El cerebro: texto -> comando -> meta en /goal_pose |
| `speech_recognition_node` | Micrófono -> texto (bilingüe es/en)                |
| `speech_synthesis_node`   | Texto -> voz, para que el robot conteste           |
| `keyboard_backup`         | Respaldo escrito si falla el micrófono             |

## Comandos reconocidos

| Instrucción hablada              | Comando cerrado     |
|----------------------------------|---------------------|
| "ve al refri / refrigerador"     | go_to_refrigerator  |
| "ve a la mesa"                   | go_to_table         |
| "ve a la silla"                  | go_to_chair         |
| "ve al sofá"                     | go_to_sofa          |
| "ve al cuadro"                   | go_to_painting      |
| "regresa al inicio"              | go_home             |
| "detente / alto"                 | stop                |

## PASO 1 — Ajustar coordenadas (obligatorio)

En `command_interpreter.py`, el diccionario `PLACES` tiene coordenadas de
EJEMPLO. Cámbialas por las de tu mapa "appartment":

1. Lanza tu navegación y abre RViz.
2. En RViz usa "Publish Point" y haz clic sobre cada mueble.
3. Lee la coordenada que aparece (publica en `/clicked_point`):
   ```bash
   ros2 topic echo /clicked_point
   ```
4. Pon esos valores `(x, y)` en `PLACES`. `theta` es la orientación final
   en radianes (0 = mirando +x, 1.57 = +y, -1.57 = -y, 3.14 = -x).

## PASO 2 — Dependencias (una vez)

```bash
sudo apt install python3-pyaudio portaudio19-dev flac espeak-ng
pip3 install SpeechRecognition pyttsx3

# Opcional (interpretación con LLM, recomendado por la rúbrica):
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3.2
pip3 install requests
```

## PASO 3 — Registrar los nodos en setup.py

Crea un paquete (o usa uno existente en `hri`) y en su `setup.py`, dentro de
`entry_points`, agrega:

```python
entry_points={
    'console_scripts': [
        'command_interpreter = TU_PAQUETE.command_interpreter:main',
        'speech_recognition_node = TU_PAQUETE.speech_recognition_node:main',
        'speech_synthesis_node = TU_PAQUETE.speech_synthesis_node:main',
        'keyboard_backup = TU_PAQUETE.keyboard_backup:main',
    ],
},
```

Reemplaza `TU_PAQUETE` por el nombre real. Luego:

```bash
cd ~/Mobile-Robots-2026-2/ros2_ws
colcon build --packages-select TU_PAQUETE
source install/setup.bash
```

## PASO 4 — Ejecución (varias terminales)

```bash
# T1: simulador + navegación (lo que ya usas)
ros2 launch motion_planning motion_planning.launch.py

# T2: síntesis de voz
ros2 run TU_PAQUETE speech_synthesis_node

# T3: el cerebro
ros2 run TU_PAQUETE command_interpreter

# T4: reconocimiento por voz...
ros2 run TU_PAQUETE speech_recognition_node
#   ...O respaldo por teclado (si el micrófono falla):
ros2 run TU_PAQUETE keyboard_backup
```

Di "ve al refrigerador" o "go to the kitchen". El robot navega y, al llegar,
contesta por voz.

## Verificar tópicos (si algo no conecta)

```bash
ros2 topic list | grep -iE 'goal|recognized|speech|reached|cmd_vel'
```

Si algún nombre difiere, cámbialo en `command_interpreter.py` (`__init__`).

## Sobre la cámara / reconocimiento visual

El paquete `vision/vision_utils` está vacío (solo `__init__.py`), así que no
hay detección de objetos por cámara en el repo. La rúbrica marca la cámara
como OPCIONAL y dice que no debe bloquear el funcionamiento principal. Este
proyecto usa coordenadas fijas, que es lo que se evalúa (interpretación 30%,
navegación 20%, ROS 15%). La cámara puede añadirse después como extra.
```
