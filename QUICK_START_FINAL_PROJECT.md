# 🚀 Quick Start - Final Project

## Paso 1: Verificar dependencias

```bash
# Instalar paquetes Python requeridos
pip3 install faster_whisper sounddevice soundfile requests

# Descargar modelo Whisper (si no existe)
python3 -c "from faster_whisper import WhisperModel; WhisperModel('base')"
```

## Paso 2: Compilar el paquete ROS2

```bash
cd ~/Fac_Inge/Mobile-Robots-2026-2.worktrees/agents-faster-whisper-asr-node-setup/ros2_ws
colcon build --packages-select final_project
source install/setup.bash
```

## Paso 3: Iniciar Ollama (Nueva Terminal)

```bash
ollama serve
```

## Paso 4: Usar el script launcher (Nueva Terminal)

```bash
cd ~/Fac_Inge/Mobile-Robots-2026-2.worktrees/agents-faster-whisper-asr-node-setup
bash launch_final_project.sh
```

**ó Iniciar manualmente en nuevas terminales:**

### Terminal A: Nodo ASR

```bash
source ~/Fac_Inge/Mobile-Robots-2026-2.worktrees/agents-faster-whisper-asr-node-setup/ros2_ws/install/setup.bash
ros2 run final_project faster_whisper_asr
```

### Terminal B: Nodo de Planificación

```bash
source ~/Fac_Inge/Mobile-Robots-2026-2.worktrees/agents-faster-whisper-asr-node-setup/ros2_ws/install/setup.bash
ros2 run final_project ollama_planning
```

### Terminal C: Monitor (Opcional)

```bash
# Ver instrucciones de voz
ros2 topic echo /speech_to_text

# Ver comandos generados (en otra terminal)
ros2 topic echo /robot_commands
```

## Prueba sin Micrófono

Si no tienes micrófono o quieres probar, usa el script de integración:

```bash
source ~/Fac_Inge/Mobile-Robots-2026-2.worktrees/agents-faster-whisper-asr-node-setup/ros2_ws/install/setup.bash
python3 ~/Fac_Inge/Mobile-Robots-2026-2.worktrees/agents-faster-whisper-asr-node-setup/ros2_ws/src/final_project/test_integration.py
```

## Flujo de Datos

```
Micrófono
   ↓
[faster_whisper_asr]
   ↓ Publica: /speech_to_text
   ↓
[ollama_planning]
   ↓ Publica: /robot_commands (JSON)
   ↓
[Tu sistema de control]
```

## Ejemplo de Salida

**Instrucción:** "Recoge la taza"  
**Respuesta:** `{"action": "pick", "target": "taza", "confidence": 0.9}`

**Instrucción:** "Vuela al techo"  
**Respuesta:** `{"action": "sorry", "reason": "No tengo capacidad de vuelo"}`

---

**¿Problemas?** Consulta el archivo `README.md` en la carpeta del proyecto.
