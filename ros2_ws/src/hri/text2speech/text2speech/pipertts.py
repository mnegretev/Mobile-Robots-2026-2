import rclpy
from rclpy.node import Node
from std_msgs.msg import String, Bool
from ament_index_python.packages import get_package_share_directory
import os
import time
import wave
from piper.voice import PiperVoice
from piper.config import SynthesisConfig

AUDIO_BASH = 'aplay "/dev/shm/tts_output.wav"'


class TTSSubscriber(Node):

    def __init__(self):
        super().__init__('text_to_speech_subscriber')
        package_path = get_package_share_directory('text2speech')
        self.model = os.path.join(package_path, "models/es_MX-claude-high.onnx")
        self.config = os.path.join(package_path, "models/es_MX-claude-high.onnx.json")
        self.voice = PiperVoice.load(model_path=self.model, config_path=self.config)
        self.syn_config = SynthesisConfig(
            volume=0.5,
            length_scale=1.0,
            noise_scale=0.667,
            noise_w_scale=0.8,
            normalize_audio=False,
        )

        self.subscription = self.create_subscription(
            String, '/tts_query', self.listener_callback, 10)

        # --- anti-eco: avisamos al ASR cuando el robot esta hablando ---
        self.pub_speaking = self.create_publisher(Bool, '/tts_speaking', 10)
        self.set_speaking(False)   # estado inicial conocido: NO hablando

    def set_speaking(self, value):
        self.pub_speaking.publish(Bool(data=value))

    def generate_speech(self, txt):
        with wave.open("/dev/shm/tts_output.wav", "wb") as wav_file:
            self.voice.synthesize_wav(txt, wav_file)

    def listener_callback(self, msg):
        self.get_logger().info('Processing txt: "%s"' % msg.data)
        self.generate_speech(msg.data)     # 0) sintetiza el wav (sin sonido aun)
        self.set_speaking(True)            # 1) AVISAR antes de que suene
        time.sleep(0.15)                   # 2) dar tiempo a que el ASR reciba el aviso
        os.system(AUDIO_BASH)              # 3) reproducir (bloqueante hasta terminar)
        time.sleep(0.4)                    # 4) margen para que muera el eco/cola de audio
        self.set_speaking(False)           # 5) liberar el microfono


def main(args=None):
    rclpy.init(args=args)
    tts_processor = TTSSubscriber()
    rclpy.spin(tts_processor)
    tts_processor.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()