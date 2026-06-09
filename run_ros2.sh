#!/bin/bash
# Script para ejecutar CUALQUIER nodo ROS2 con el entorno correcto

# Limpiar PYTHONPATH conflictivo
unset PYTHONPATH

# Activar el venv
source $HOME/Mobile-Robots-2026-2/venv/bin/activate

# Agregar la ruta del venv al PYTHONPATH
export PYTHONPATH=$HOME/Mobile-Robots-2026-2/venv/lib/python3.10/site-packages:$PYTHONPATH

# Source de ROS2 Humble
source /opt/ros/humble/setup.bash

# Source de tu workspace
source $HOME/Mobile-Robots-2026-2/ros2_ws/install/setup.bash

# Verificar dependencias críticas
echo "=== Verificando dependencias ==="
python -c "import pyaudio" 2>/dev/null && echo "✅ PyAudio OK" || echo "❌ PyAudio NO encontrado"
python -c "import faster_whisper" 2>/dev/null && echo "✅ FasterWhisper OK" || echo "❌ FasterWhisper NO encontrado"
python -c "from piper.voice import PiperVoice" 2>/dev/null && echo "✅ Piper OK" || echo "❌ Piper NO encontrado"
echo "================================"

echo "✅ Entorno listo"

# Fix hri_proyecto executable path
mkdir -p ~/Mobile-Robots-2026-2/ros2_ws/install/hri_proyecto/lib/hri_proyecto
ln -sf ~/Mobile-Robots-2026-2/ros2_ws/install/hri_proyecto/bin/brain ~/Mobile-Robots-2026-2/ros2_ws/install/hri_proyecto/lib/hri_proyecto/brain
mkdir -p ~/Mobile-Robots-2026-2/ros2_ws/install/speech2text/lib/speech2text
ln -sf ~/Mobile-Robots-2026-2/ros2_ws/install/speech2text/bin/faster_whisper_asr ~/Mobile-Robots-2026-2/ros2_ws/install/speech2text/lib/speech2text/faster_whisper_asr
mkdir -p ~/Mobile-Robots-2026-2/ros2_ws/install/speech2text_pro/lib/speech2text_pro
ln -sf ~/Mobile-Robots-2026-2/ros2_ws/install/speech2text_pro/bin/faster_whisper_asr ~/Mobile-Robots-2026-2/ros2_ws/install/speech2text_pro/lib/speech2text_pro/faster_whisper_asr
