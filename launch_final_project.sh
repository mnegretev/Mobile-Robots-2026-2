#!/bin/bash

# Script para iniciar fácilmente los nodos del proyecto final

ROS_WS="/home/danielgrioja/Fac_Inge/Mobile-Robots-2026-2.worktrees/agents-faster-whisper-asr-node-setup/ros2_ws"

# Colores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Final Project ROS2 Launcher ===${NC}"
echo ""

# Verificar que Ollama está ejecutándose
echo -e "${YELLOW}Verificando Ollama...${NC}"
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo -e "${RED}❌ Ollama no está ejecutándose${NC}"
    echo -e "   Inicia en otra terminal: ${YELLOW}ollama serve${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Ollama activo${NC}"

# Verificar workspace
if [ ! -d "$ROS_WS/install/final_project" ]; then
    echo -e "${RED}❌ Paquete no compilado${NC}"
    echo -e "   Compila con: ${YELLOW}cd $ROS_WS && colcon build --packages-select final_project${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Paquete compilado${NC}"

# Source ROS setup
source $ROS_WS/install/setup.bash

echo ""
echo -e "${YELLOW}Iniciando nodos...${NC}"
echo ""

# Crear sesiones tmux si no existen
SESSION="final_project"

if ! tmux has-session -t $SESSION 2>/dev/null; then
    # ASR
    tmux new-session -d -s $SESSION -n asr \
        "echo 'Iniciando faster_whisper_asr...' && \
         ros2 run final_project faster_whisper_asr"
    
    # Planning
    tmux new-window -t $SESSION -n planning \
        "echo 'Iniciando ollama_planning...' && \
         ros2 run final_project ollama_planning"
    
    # Monitor
    tmux new-window -t $SESSION -n monitor \
        "ros2 topic monitor /speech_to_text /robot_commands"
    
    echo -e "${GREEN}✓ Sesión tmux '$SESSION' creada${NC}"
    echo ""
    echo -e "${YELLOW}Ventanas:${NC}"
    echo "  - asr       : Nodo de reconocimiento de voz"
    echo "  - planning  : Nodo de planificación con Ollama"
    echo "  - monitor   : Monitor de tópicos"
    echo ""
    echo -e "${YELLOW}Comandos:${NC}"
    echo "  Ver los nodos:    tmux attach-session -t $SESSION"
    echo "  Cambiar ventana:  Ctrl+B + N (siguiente) o Ctrl+B + P (anterior)"
    echo "  Ver ventana ASR:  tmux select-window -t $SESSION:asr"
    echo "  Ver planning:     tmux select-window -t $SESSION:planning"
    echo "  Ver monitor:      tmux select-window -t $SESSION:monitor"
    echo "  Salir:            Ctrl+B + D (detach)"
    echo ""
else
    echo -e "${YELLOW}Sesión '$SESSION' ya existe${NC}"
    echo "Adjuntando a la sesión..."
fi

tmux attach-session -t $SESSION
