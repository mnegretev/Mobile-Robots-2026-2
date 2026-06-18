#!/usr/bin/env python3
#
# MOBILE ROBOTS - FI-UNAM, 2026-2
# NODE TO CAPTURE MICROPHONE AUDIO AND PUBLISH TO ROS 2
#

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import speech_recognition as sr

class VoiceMicNode(Node):
    def __init__(self):
        super().__init__('voice_mic_node')
        # Publicador que se conecta directo con tu pure_pursuit.py
        self.pub_voice = self.create_publisher(String, '/voice_command', 10)
        
        # Inicializar el reconocedor de voz de Google
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
        # Ajustar el umbral de ruido ambiental al iniciar
        with self.microphone as source:
            self.get_logger().info("Calibrando micrófono para el ruido ambiental... Silencio por favor.")
            self.recognizer.adjust_for_ambient_noise(source, duration=2)
            
        self.get_logger().info("¡Micrófono listo y escuchando! Puedes hablar ahora...")
        
        # Crear un temporizador que revise el micrófono constantemente
        self.create_timer(0.1, self.listen_microphone)

    def listen_microphone(self):
        with self.microphone as source:
            try:
                # Escucha una frase corta (máximo 4 segundos de silencio)
                audio = self.recognizer.listen(source, timeout=1.0, phrase_time_limit=5.0)
                self.get_logger().info("Procesando audio recibido...")
                
                # Convertir audio a texto usando la API de Google en Español de México
                text = self.recognizer.recognize_google(audio, language='es-MX')
                self.get_logger().info(f"Texto reconocido: '{text}'")
                
                # Publicar el texto en ROS 2
                msg = String()
                msg.data = text
                self.pub_voice.publish(msg)
                
            except sr.WaitTimeoutError:
                # No pasa nada, simplemente nadie habló en ese segundo
                pass
            except sr.UnknownValueError:
                self.get_logger().warn("No entendí lo que dijiste, intenta de nuevo.")
            except sr.RequestError as e:
                self.get_logger().error(f"Error con el servicio de Google Speech: {e}")
            except Exception as e:
                # Previene que el nodo muera si hay un parpadeo en el micrófono
                pass

def main(args=None):
    rclpy.init(args=args)
    node = VoiceMicNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()