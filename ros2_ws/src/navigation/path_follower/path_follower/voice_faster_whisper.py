import os
import wave
import time
import tempfile

import rclpy
from rclpy.node import Node

from std_msgs.msg import String

import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel


class VoiceFasterWhisperNode(Node):
    def __init__(self):
        super().__init__('voice_faster_whisper_node')

        self.pub_command = self.create_publisher(String, '/voice_text', 10)

        self.declare_parameter('model_size', 'base')
        self.declare_parameter('device', 'cpu')
        self.declare_parameter('compute_type', 'int8')
        self.declare_parameter('sample_rate', 16000)
        self.declare_parameter('record_seconds', 4.0)
        self.declare_parameter('input_device', -1)

        self.model_size = self.get_parameter('model_size').value
        self.device = self.get_parameter('device').value
        self.compute_type = self.get_parameter('compute_type').value
        self.sample_rate = int(self.get_parameter('sample_rate').value)
        self.record_seconds = float(self.get_parameter('record_seconds').value)
        self.input_device = int(self.get_parameter('input_device').value)

        self.valid_words = [
            'cama',
            'cuarto',

            'refrigerador',
            'refri',
            'nevera',

            'sillon',
            'sillón',
            'sofa',
            'sofá',

            'pesas',
            'gym',
            'ejercicio',

            'tele',
            'television',
            'televisión',
            'tv',

            'pelota',
            'balon',
            'balón',

            'puerta',
            'salida'
        ]

        if self.input_device >= 0:
            sd.default.device = self.input_device
            self.get_logger().info(f'Usando dispositivo de audio: {self.input_device}')
        else:
            self.get_logger().info('Usando dispositivo de audio por defecto.')

        self.get_logger().info('Cargando modelo Faster Whisper...')
        self.model = WhisperModel(
            self.model_size,
            device=self.device,
            compute_type=self.compute_type
        )
        self.get_logger().info('Modelo cargado correctamente.')

    def record_audio_to_wav(self):
        self.get_logger().info('Escuchando comando...')

        audio = sd.rec(
            int(self.record_seconds * self.sample_rate),
            samplerate=self.sample_rate,
            channels=1,
            dtype='float32'
        )

        sd.wait()

        audio = np.squeeze(audio)

        max_level = np.max(np.abs(audio))
        self.get_logger().info(f'Nivel de audio: {max_level:.4f}')

        if max_level < 0.001:
            self.get_logger().warn('Audio muy bajo. No se detectó voz clara.')
            return None

        audio_int16 = np.int16(audio * 32767)

        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
        temp_path = temp_file.name
        temp_file.close()

        with wave.open(temp_path, 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(self.sample_rate)
            wav_file.writeframes(audio_int16.tobytes())

        return temp_path

    def transcribe_audio(self, audio_path):
        segments, info = self.model.transcribe(
            audio_path,
            language='es',
            beam_size=5,
            vad_filter=True
        )

        text = ''

        for segment in segments:
            text += segment.text + ' '

        return text.lower().strip()

    def contains_valid_location(self, text):
        for word in self.valid_words:
            if word in text:
                return True

        return False

    def run(self):
        self.get_logger().info('Nodo de voz listo.')
        self.get_logger().info('Comandos ejemplo: "ve al refri", "ve a la cama", "ve a la puerta".')

        while rclpy.ok():
            try:
                audio_path = self.record_audio_to_wav()

                if audio_path is None:
                    rclpy.spin_once(self, timeout_sec=0.1)
                    continue

                text = self.transcribe_audio(audio_path)

                if os.path.exists(audio_path):
                    os.remove(audio_path)

                if text == '':
                    self.get_logger().warn('No se pudo transcribir audio.')
                    rclpy.spin_once(self, timeout_sec=0.1)
                    continue

                self.get_logger().info(f'Texto reconocido: "{text}"')

                if not self.contains_valid_location(text):
                    self.get_logger().warn('No se detectó una locación válida.')
                    rclpy.spin_once(self, timeout_sec=0.1)
                    continue

                msg = String()
                msg.data = text
                self.pub_command.publish(msg)

                self.get_logger().info(f'Comando publicado en /route_command: "{text}"')

                time.sleep(1.0)
                rclpy.spin_once(self, timeout_sec=0.1)

            except KeyboardInterrupt:
                break

            except Exception as e:
                self.get_logger().error(f'Error en el nodo de voz: {e}')
                time.sleep(1.0)


def main(args=None):
    rclpy.init(args=args)

    node = VoiceFasterWhisperNode()
    node.run()

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
