import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import threading
import io
import numpy as np
from faster_whisper import WhisperModel

class FasterWhisperASRNode(Node):
    def __init__(self):
        super().__init__('faster_whisper_asr')
        
        self.publisher_ = self.create_publisher(String, '/speech_to_text', 10)
        
        # Cargar modelo Whisper base
        self.model = WhisperModel("base", device="cpu", compute_type="int8")
        
        self.get_logger().info('Nodo Faster Whisper ASR iniciado')
        self.get_logger().info('Esperando audio del micrófono...')
        
        # Iniciar captura en thread separado
        self.capture_thread = threading.Thread(target=self.capture_and_transcribe, daemon=True)
        self.capture_thread.start()
    
    def capture_and_transcribe(self):
        try:
            import sounddevice as sd
            import soundfile as sf
        except ImportError:
            self.get_logger().error('Instala: pip install sounddevice soundfile')
            return
        
        try:
            while rclpy.ok():
                self.get_logger().info('Grabando... (presiona Ctrl+C para detener)')
                # Grabar 10 segundos de audio
                duration = 10
                samplerate = 16000
                audio_data = sd.rec(int(samplerate * duration), samplerate=samplerate, 
                                   channels=1, dtype='float32')
                sd.wait()
                
                # Transcribir
                segments, info = self.model.transcribe(audio_data, language="es")
                text = " ".join([segment.text for segment in segments])
                
                if text.strip():
                    msg = String()
                    msg.data = text.strip()
                    self.publisher_.publish(msg)
                    self.get_logger().info(f'Publicado: {msg.data}')
                
        except Exception as e:
            self.get_logger().error(f'Error en captura: {str(e)}')

def main(args=None):
    rclpy.init(args=args)
    node = FasterWhisperASRNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
