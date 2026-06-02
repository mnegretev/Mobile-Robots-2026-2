#
# MOBILE ROBOTS - FI-UNAM, 2026-2
# SPEECH TO TEXT - Faster Whisper ASR (español)
#

import pyaudio
import wave
import numpy
from faster_whisper import WhisperModel
import rclpy
from rclpy.node import Node
from rclpy.duration import Duration
from std_msgs.msg import String

#
# Parametros de grabación de audio
#
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100
WAVE_OUTPUT_FILENAME = "/dev/shm/recorder_audio.wav"


class FasterWhisperNode(Node):
    def __init__(self):
        super().__init__("faster_whisper_node")
        self.get_logger().info("INITIALIZING FASTER WHISPER NODE")
        self.model_size = "small"
        self.pwr_threshold = 0.05
        self.pub_recognized = self.create_publisher(String, "/sp_rec/recognized", 1)

    def spin(self):
        self.get_logger().info(
            "Cargando modelo Faster Whisper (size=" + self.model_size + ") ..."
        )
        model = WhisperModel(self.model_size, device="cpu", compute_type="int8")
        self.get_logger().info("Modelo listo.")

        p = pyaudio.PyAudio()
        stream = p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK,
        )

        while rclpy.ok():
            frames = []

            self.get_logger().info("Esperando audio con suficiente potencia...")
            pwr = 0.0
            while pwr < self.pwr_threshold and rclpy.ok():
                data = stream.read(CHUNK)
                arr = numpy.frombuffer(data, dtype=numpy.int16) / 32768.0
                pwr = numpy.mean(arr ** 2)

            self.get_logger().info("Audio detectado. Grabando...")
            no_audio_counter = 0
            frames.append(data)
            while no_audio_counter < 20 and rclpy.ok():
                data = stream.read(CHUNK)
                frames.append(data)
                arr = numpy.frombuffer(data, dtype=numpy.int16) / 32768.0
                pwr = numpy.mean(arr ** 2)
                if pwr < self.pwr_threshold:
                    no_audio_counter += 1
                else:
                    no_audio_counter = 0
            self.get_logger().info("Grabación terminada.")

            wf = wave.open(WAVE_OUTPUT_FILENAME, "wb")
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(p.get_sample_size(FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(b"".join(frames))
            wf.close()

            # Transcribir en ESPAÑOL
            segments, info = model.transcribe(
                WAVE_OUTPUT_FILENAME, beam_size=5, language="es"
            )
            self.get_logger().info(
                "Idioma detectado: '%s' (prob=%.2f)"
                % (info.language, info.language_probability)
            )
            full_text = ""
            for segment in segments:
                self.get_logger().info(
                    "[%.2fs -> %.2fs] %s"
                    % (segment.start, segment.end, segment.text)
                )
                full_text += segment.text + " "

            if full_text.strip():
                self.pub_recognized.publish(String(data=full_text.strip()))

            rclpy.spin_once(self, timeout_sec=0)
            self.get_clock().sleep_for(Duration(seconds=0.005))

        stream.stop_stream()
        stream.close()
        p.terminate()


def main(args=None):
    rclpy.init(args=args)
    faster_whisper_node = FasterWhisperNode()
    faster_whisper_node.spin()
    faster_whisper_node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
