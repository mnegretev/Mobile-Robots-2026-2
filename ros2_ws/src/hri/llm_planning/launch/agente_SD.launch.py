import os
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import ExecuteProcess

def generate_launch_description():
    
    # Directorio local para guardar el modelo y no descargarlo de nuevo
    hf_cache_dir = os.path.expanduser('~/.cache/huggingface')
    
    # 1. Servidor de Inteligencia Artificial (vLLM en Docker para Jetson)
    # vllm_server = ExecuteProcess(
    #     cmd=[
    #         'docker', 'run', '--rm', '--runtime=nvidia', '--network', 'host',
    #         '-v', f'{hf_cache_dir}:/root/.cache/huggingface',
    #         'ghcr.io/nvidia-ai-iot/vllm:latest-jetson-orin',
    #         'vllm', 'serve', 'RedHatAI/Qwen3-4B-quantized.w4a16',
    #         '--gpu-memory-utilization', '0.4', '--max-model-len', '32678'
    #     ],
    #     output='screen'
    # )
    
    # 2. Nodo del Oído (ASR - Reconocimiento de voz de audio a texto)
    asr_node = Node(
        package='speech2text',
        executable='faster_whisper_asr',  
        name='faster_whisper_asr',
        output='screen'
    )
    
    # 3. Nodo del Cerebro (LLM - Tu código OllamaPlanningNode adaptado a JSON)
    llm_node = Node(
        package='llm_planning',
        executable='ollama_planning',
        name='ollama_planning_node',
        output='screen'
    )
    
    # 4. Nodo de la Boca (TTS - Texto a Voz para que el robot hable)
    tts_node = Node(
        package='text2speech',
        executable='pipertts',
        name='text_to_speech_subscriber',
        output='screen'
    )

    # 5. Nodo de los Músculos (TaskExecutor - El ejecutor físico de trayectorias)
    task_executor_node = Node(
        package='llm_planning',             # Cambia por el nombre de tu paquete si es diferente
        executable='task_executor',         # Asegúrate de que este sea el nombre del entry_point en tu setup.py
        name='task_executor_node',
        output='screen'
    )

    # Retornamos la lista completa de procesos y nodos que se iniciarán juntos
    return LaunchDescription([
        #vllm_server,
        asr_node,
        llm_node,
        tts_node,
        task_executor_node                  # <-- Incorporado con éxito
    ])