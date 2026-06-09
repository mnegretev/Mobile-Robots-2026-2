# Final Project - ASR + LLM Planning Robot

Integración de **Faster Whisper ASR** (reconocimiento de voz) con **Ollama Planning** (razonamiento del robot) para un robot doméstico con limitaciones definidas.

## Arquitectura

```
┌─────────────────────┐
│   Micrófono         │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────────────────────────────┐
│  faster_whisper_asr (Node)                  │
│  - Captura audio del micrófono              │
│  - Transcribe a texto con Whisper           │
│  - Publica en /speech_to_text               │
└──────────┬──────────────────────────────────┘
           │
           ▼
      /speech_to_text (String topic)
           │
           ▼
┌─────────────────────────────────────────────┐
│  ollama_planning (Node)                     │
│  - Recibe texto del ASR                     │
│  - Consulta a Ollama con prompt del sistema │
│  - Publica comandos estructurados           │
│  - Publica en /robot_commands               │
└──────────┬──────────────────────────────────┘
           │
           ▼
    /robot_commands (String/JSON)
           │
           ▼
    ┌──────────────────┐
    │  Robot Control   │  (Implementación futura)
    │  - Mover         │
    │  - Agarrar       │
    └──────────────────┘
```

## Instalación de Dependencias

### 1. Paquetes Python requeridos

```bash
pip3 install faster_whisper piper-tts ultralytics
pip3 install sounddevice soundfile  # Para captura de audio
pip3 install requests               # Para comunicar con Ollama
```

### 2. Descargar modelo Whisper

```bash
# Instala automáticamente en primer uso, o descárgalo manualmente:
python3 -c "from faster_whisper import WhisperModel; WhisperModel('base')"
```

### 3. Instalar y ejecutar Ollama

```bash
# Descarga de https://ollama.ai
# Luego ejecuta en otra terminal:
ollama serve

# En otra terminal, descarga un modelo (ej: mistral):
ollama pull mistral
```

## Uso

### 1. Compilar el paquete

```bash
cd ~/Fac_Inge/Mobile-Robots-2026-2.worktrees/agents-faster-whisper-asr-node-setup/ros2_ws
colcon build --packages-select final_project
source install/setup.bash
```

### 2. Terminal 1: Iniciar Ollama

```bash
ollama serve
```

### 3. Terminal 2: Iniciar el nodo de ASR

```bash
source ~/Fac_Inge/Mobile-Robots-2026-2.worktrees/agents-faster-whisper-asr-node-setup/ros2_ws/install/setup.bash
ros2 run final_project faster_whisper_asr
```

### 4. Terminal 3: Iniciar el nodo de Planificación

```bash
source ~/Fac_Inge/Mobile-Robots-2026-2.worktrees/agents-faster-whisper-asr-node-setup/ros2_ws/install/setup.bash
ros2 run final_project ollama_planning
```

### 5. Terminal 4 (Opcional): Monitor de tópicos

```bash
# Ver mensajes de entrada (instrucciones de voz)
ros2 topic echo /speech_to_text

# Ver comandos generados (en otra terminal)
ros2 topic echo /robot_commands
```

## Ejemplos de Uso

### Comando que el robot PUEDE ejecutar

**Micrófono:**  
"Recoge la taza de la mesa"

**Output esperado:**
```json
{"action": "pick", "target": "mesa", "confidence": 0.9}
```

**Micrófono:**  
"Muévete a la cocina"

**Output esperado:**
```json
{"action": "move", "target": "cocina", "confidence": 0.95}
```

### Comando que el robot NO PUEDE ejecutar

**Micrófono:**  
"Vuela hasta el techo"

**Output esperado:**
```json
{"action": "sorry", "reason": "No tengo capacidad de vuelo, no tengo alas"}
```

**Micrófono:**  
"Cociname un sándwich"

**Output esperado:**
```json
{"action": "sorry", "reason": "No tengo hardware de cocina, solo puedo moverme y recoger objetos"}
```

## Nodos

### `faster_whisper_asr`

**Función:** Captura audio del micrófono y lo transcribe a texto

**Publisher:** `/speech_to_text` (String)

**Parámetros:**
- Duración de grabación: 10 segundos
- Idioma: Español
- Modelo: base (80M parámetros)

**Requisitos:**
- Micrófono funcional
- `sounddevice` y `soundfile`

---

### `ollama_planning`

**Función:** Recibe texto y genera comandos estructurados usando Ollama

**Subscriber:** `/speech_to_text` (String)  
**Publisher:** `/robot_commands` (String)

**Prompt del Sistema:**
```
Eres un robot de servicio doméstico. 
Tus únicas habilidades son:
1. Moverte a posiciones específicas en el hogar
2. Extender tu brazo para simular que recoges un objeto

Responde SOLO con JSON estructurado:
- action: "move" | "pick" | "sorry"
- target: ubicación/objeto
- confidence: valor 0-1 (para move/pick)
- reason: explicación (para sorry)
```

**Parámetros:**
- URL Ollama: `http://localhost:11434`
- Temperatura: 0.3 (respuestas deterministas)
- Timeout: 30 segundos

## Troubleshooting

### ❌ "No se pudo conectar a Ollama"

```bash
# Asegúrate que Ollama está ejecutándose
ollama serve
```

### ❌ "No se captura audio"

```bash
# Verifica tu micrófono
pactl list short sources
# O prueba con:
arecord -D default -d 3 test.wav
```

### ❌ "ModuleNotFoundError: No module named 'faster_whisper'"

```bash
pip3 install faster_whisper
```

### ❌ Respuestas no estructuradas de Ollama

- Prueba con un modelo diferente: `ollama pull neural-chat`
- Aumenta parámetros de contexto
- Ajusta la temperatura

## Próximos Pasos

1. **Crear nodo de control del robot:**
   - Parsear JSON de `/robot_commands`
   - Generar mensajes de control (velocidad, pose)

2. **Integrar con simulador Gazebo:**
   - Control de movimiento
   - Simulación del brazo

3. **Agregar retroalimentación:**
   - Tópicos de estado del robot
   - Confirmar ejecución de comandos

## Archivos del Proyecto

```
src/final_project/
├── package.xml              # Metadatos del paquete
├── setup.py                 # Configuración de instalación
├── final_project/
│   ├── __init__.py
│   ├── faster_whisper_asr.py    # Nodo ASR
│   └── ollama_planning.py       # Nodo de planificación
└── README.md                # Este archivo
```

---

**Autor:** Final Project ROS2  
**Licencia:** LGPL-3.0-only
