#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import sounddevice as sd
import numpy as np
from faster_whisper import WhisperModel
import threading
import queue
import time
import math

# Parámetros de audio
SAMPLE_RATE = 16000
CHUNK_DURATION = 0.5          # segundos por bloque de análisis
CHUNK_SAMPLES = int(SAMPLE_RATE * CHUNK_DURATION)
SILENCE_TIMEOUT = 1.0         # segundos de silencio para finalizar comando
ENERGY_THRESHOLD = 0.01      # umbral RMS (ajústalo según tu micrófono)

class SpeechToTextNode(Node):
    def __init__(self):
        super().__init__('stt_node')
        self.declare_parameter('model_size', 'base')
        self.declare_parameter('language', 'es')
        model_size = self.get_parameter('model_size').value
        language = self.get_parameter('language').value

        self.publisher_ = self.create_publisher(String, '/speech/text', 10)

        # Modelo Whisper
        self.get_logger().info(f'Cargando modelo {model_size}...')
        self.model = WhisperModel(model_size, device='cpu', compute_type='int8')
        self.get_logger().info('Modelo listo.')

        # Cola de audio en bruto
        self.audio_queue = queue.Queue()
        self.recording = True

        # Estado de VAD
        self.is_speaking = False
        self.speech_buffer = []        # lista de fragmentos de audio
        self.last_speech_time = 0

        # Hilo de captura continua
        self.stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype='float32',
            blocksize=CHUNK_SAMPLES,
            callback=self.audio_callback
        )
        self.stream.start()
        self.get_logger().info("Microfono activo, esperando comando de voz...")

        # Hilo de procesamiento de audio
        self.process_thread = threading.Thread(target=self.process_loop)
        self.process_thread.start()

    def audio_callback(self, indata, frames, time_info, status):
        """Se llama cada CHUNK_DURATION segundos."""
        if status:
            self.get_logger().warn(f"Status audio: {status}")
        # Calcular energía RMS del bloque
        rms = math.sqrt(np.mean(indata**2))
        # Detección de habla
        if rms > ENERGY_THRESHOLD:
            if not self.is_speaking:
                # Inicio de habla
                self.is_speaking = True
                self.speech_buffer = []   # reiniciar buffer
                self.get_logger().debug("Inicio de voz detectado")
            # Agregar el fragmento al buffer
            self.speech_buffer.append(indata.copy().flatten())
            self.last_speech_time = time.time()
        else:
            if self.is_speaking:
                # Estamos en silencio después de haber hablado
                # Verificar si el silencio duró más que el timeout
                if time.time() - self.last_speech_time > SILENCE_TIMEOUT:
                    # Fin del comando
                    self.is_speaking = False
                    if self.speech_buffer:
                        audio_chunk = np.concatenate(self.speech_buffer)
                        self.audio_queue.put_nowait(audio_chunk)
                        self.get_logger().debug("Comando completado, enviando a transcripción")
                    self.speech_buffer = []
            # Si nunca se habló, no hacemos nada

    def process_loop(self):
        while self.recording:
            try:
                audio = self.audio_queue.get(timeout=0.5)
            except queue.Empty:
                continue
            self.get_logger().info("Transcribiendo...")
            try:
                segments, _ = self.model.transcribe(audio, language='es')
                text = " ".join([seg.text for seg in segments]).strip()
                if text:
                    self.get_logger().info(f"STT: {text}")
                    msg = String()
                    msg.data = text
                    self.publisher_.publish(msg)
            except Exception as e:
                self.get_logger().error(f"Error transcripción: {e}")

    def __del__(self):
        self.recording = False
        if hasattr(self, 'stream'):
            self.stream.stop()
            self.stream.close()
        if hasattr(self, 'process_thread'):
            self.process_thread.join(timeout=2)

def main(args=None):
    rclpy.init(args=args)
    node = SpeechToTextNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()