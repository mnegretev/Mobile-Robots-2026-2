#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# NODO DE RECONOCIMIENTO DE VOZ (speech-to-text)
# Robots Moviles, FI-UNAM, 2026-2 - Proyecto final
#
# Escucha el microfono, convierte voz a texto (es / en) y publica el texto
# en /recognized_speech, que es lo que escucha el interprete.
#
# Dependencias:
#   sudo apt install python3-pyaudio portaudio19-dev flac
#   pip3 install SpeechRecognition
#
# recognize_google requiere internet. Para offline ver la nota al final.

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

import speech_recognition as sr


class SpeechRecognitionNode(Node):
    def __init__(self):
        super().__init__('speech_recognition_node')
        self.pub = self.create_publisher(String, '/recognized_speech', 10)

        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        with self.microphone as source:
            self.get_logger().info('Calibrando ruido ambiente, silencio...')
            self.recognizer.adjust_for_ambient_noise(source, duration=1.5)
        self.get_logger().info('Listo. Habla cuando quieras.')

        self.timer = self.create_timer(0.1, self.listen_once)
        self.listening = False

    def listen_once(self):
        if self.listening:
            return
        self.listening = True
        try:
            with self.microphone as source:
                self.get_logger().info('Escuchando...')
                audio = self.recognizer.listen(source, timeout=5,
                                                phrase_time_limit=5)
            text = self.transcribe(audio)
            if text:
                self.get_logger().info('Reconocido: "%s"' % text)
                self.pub.publish(String(data=text))
        except sr.WaitTimeoutError:
            pass
        except Exception as e:
            self.get_logger().warn('Error escuchando: %s' % str(e))
        finally:
            self.listening = False

    def transcribe(self, audio):
        # Intenta espanol y luego ingles -> bilingue.
        for lang in ('es-MX', 'en-US'):
            try:
                return self.recognizer.recognize_google(audio, language=lang)
            except sr.UnknownValueError:
                continue
            except sr.RequestError as e:
                self.get_logger().error('Sin conexion: %s' % str(e))
                return None
        return None


def main(args=None):
    rclpy.init(args=args)
    node = SpeechRecognitionNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()

# NOTA offline: instala Vosk (pip3 install vosk), descarga un modelo es/en de
# https://alphacephei.com/vosk/models y reemplaza recognize_google por la
# version de Vosk. El resto del nodo no cambia.
