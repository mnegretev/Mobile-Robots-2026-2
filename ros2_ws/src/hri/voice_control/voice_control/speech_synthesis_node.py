#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# NODO DE SINTESIS DE VOZ (text-to-speech)
# Robots Moviles, FI-UNAM, 2026-2 - Proyecto final
#
# Se suscribe a /speech y dice en voz alta cualquier texto que llegue.
# El interprete publica aqui para que el robot "conteste".
#
# Dependencias:
#   sudo apt install espeak-ng
#   pip3 install pyttsx3

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

import pyttsx3


class SpeechSynthesisNode(Node):
    def __init__(self):
        super().__init__('speech_synthesis_node')
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 150)
        self.create_subscription(String, '/speech', self.speak_callback, 10)
        self.get_logger().info('Sintesis lista. Publica en /speech.')

    def speak_callback(self, msg):
        text = msg.data
        self.get_logger().info('Diciendo: "%s"' % text)
        lang = 'es' if self._looks_spanish(text) else 'en'
        try:
            self.engine.setProperty('voice', lang)
        except Exception:
            pass
        self.engine.say(text)
        self.engine.runAndWait()

    def _looks_spanish(self, text):
        hints = ['é', 'í', 'ó', 'á', 'ú', 'ñ', 'lleg', 'refri', 'voy',
                 'hacia', 'mesa', 'silla', 'cuadro', 'inicio', 'detenido']
        t = text.lower()
        return any(h in t for h in hints)


def main(args=None):
    rclpy.init(args=args)
    node = SpeechSynthesisNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
