#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# RESPALDO POR TECLADO
# Robots Moviles, FI-UNAM, 2026-2 - Proyecto final
#
# La rubrica pide un respaldo escrito por terminal en caso de fallo del
# microfono. Este nodo lee texto del teclado y lo publica en
# /recognized_speech, el MISMO topico que usa el reconocimiento de voz.
# Asi el interprete funciona igual con voz o con teclado.

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class KeyboardBackup(Node):
    def __init__(self):
        super().__init__('keyboard_backup')
        self.pub = self.create_publisher(String, '/recognized_speech', 10)
        self.timer = self.create_timer(0.1, self.read_input)
        self.get_logger().info('Respaldo por teclado listo. Escribe un comando '
                               '(ej: "ve al refrigerador") y Enter.')

    def read_input(self):
        try:
            text = input('comando> ')
        except EOFError:
            return
        if text.strip():
            self.pub.publish(String(data=text))
            self.get_logger().info('Publicado: "%s"' % text)


def main(args=None):
    rclpy.init(args=args)
    node = KeyboardBackup()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
