#
# MOBILE ROBOTS - FI-UNAM, 2026-2
# ASYNCHRONOUS MIC BRIDGE FOR JAZZY
#

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import speech_recognition as sr
import threading
import time

class VoiceCommander(Node):
    def __init__(self):
        super().__init__('voice_commander_node')
        self.publisher_ = self.create_publisher(String, 'voice_commands', 10)
        self.get_logger().info('🎤 MINDFUL MIC NODE INITIALIZED - WAITING FOR NATURAL COMMANDS...')
        self.get_logger().info('💡 Formato aceptado: "ve al gimnasio", "muévete al refri", "camina al comedor", "para".')
        
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
        # Calibración rápida de ruido estático ambiental
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
            
        self.stop_listening = self.recognizer.listen_in_background(self.microphone, self.callback_audio)

    def callback_audio(self, recognizer, audio):
        try:
            # Procesamos el audio con Google en español de México
            command = recognizer.recognize_google(audio, language="es-MX")
            self.get_logger().info(f'📝 Escuchado completo: "{command}"')
            
            # Limpiamos cadenas básicas
            command_clean = command.lower().strip()
            
            # Definimos los prefijos obligatorios de comando de movimiento
            prefijos_movimiento = ["ve al", "ve a la", "muévete al", "muévete a la", "camina al", "camina a la", "dirígete al", "dirígete a la"]
            
            # Caso especial: Comando de emergencia inmediato
            if "stop" in command_clean or "para" in command_clean or "detente" in command_clean:
                msg = String()
                msg.data = "stop"
                self.publisher_.publish(msg)
                self.get_logger().info('🚨 Mandando "STOP" inmediato al motion_planner')
                return

            # Validamos si la frase inicia con alguna de las acciones de movimiento permitidas
            tiene_accion_valida = any(command_clean.startswith(prefijo) for prefijo in prefijos_movimiento)
            
            if tiene_accion_valida:
                # Buscamos el destino final dentro de la frase estructurada
                for palabra in ["gimnasio", "comedor", "refri", "refrigerador"]:
                    if palabra in command_clean:
                        # Homologamos refrigerador a la palabra clave que espera tu motion_planner
                        palabra_envio = "refri" if palabra == "refrigerador" else palabra
                        
                        msg = String()
                        msg.data = palabra_envio
                        self.publisher_.publish(msg)
                        self.get_logger().info(f'🚀 Estructura correcta. Mandando destino "{palabra_envio.upper()}" al motion_planner')
                        return
                
                self.get_logger().warn('⚠️ Dijiste una acción de movimiento, pero el destino no es válido (usa comedor, gimnasio o refri).')
            else:
                # Si solo dijo la palabra clave sin la acción previa, mandamos una advertencia educativa
                for palabra in ["gimnasio", "comedor", "refri", "refrigerador"]:
                    if palabra in command_clean:
                        self.get_logger().warn(f'❌ Comando rechazado. Dijiste "{command_clean}". Debes usar una frase completa, ej: "ve al {palabra}"')
                        return
                    
        except sr.UnknownValueError:
            pass # Ruido común de fondo sin reconocer, lo ignoramos para mantener la consola limpia
        except sr.RequestError as e:
            self.get_logger().error(f"Error de conexión con la API de Google: {e}")

def main(args=None):
    # Forzamos la salida inmediata en consola sin caché en sistemas Linux
    rclpy.init(args=args)
    node = VoiceCommander()
    try:
        while rclpy.ok():
            rclpy.spin_once(node, timeout_sec=0.1)
            time.sleep(0.02)
    except KeyboardInterrupt:
        pass
    finally:
        node.stop_listening(wait_for_stop=False)
        try:
            node.destroy_node()
        except:
            pass
        rclpy.shutdown()

if __name__ == '__main__':
    main()  