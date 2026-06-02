#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# NODO DE INTERPRETACION (el cerebro del proyecto de voz)
# Robots Moviles, FI-UNAM, 2026-2 - Proyecto final
# Dominguez Palacios Jesus Alejandro
#
# Conecta el reconocimiento de voz con la navegacion que YA tienes funcionando.
#
# Flujo:
#   /recognized_speech (texto) -> interpretar -> comando cerrado
#       -> publica meta en /goal_pose  (tu pure_pursuit la sigue)
#       -> espera /navigation/goal_reached
#       -> avisa por voz en /speech
#
# La interpretacion es en dos capas (reglas + Ollama opcional), como
# recomienda la rubrica. Si Ollama no esta, sigue solo con reglas.

import math

import rclpy
from rclpy.node import Node

from std_msgs.msg import String, Bool
from geometry_msgs.msg import PoseStamped, Twist

try:
    import requests
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False


# =============================================================================
# LUGARES CONOCIDOS  ->  coordenada (x, y, theta) en el marco "map"
#
# ¡¡AJUSTA ESTAS COORDENADAS!!  Son de ejemplo.
# Para sacar las reales de tu mapa "appartment":
#   1. Lanza tu navegacion y abre RViz.
#   2. Usa el boton "Publish Point" y haz clic sobre cada mueble.
#   3. Mira la coordenada en la terminal (topico /clicked_point) o en RViz.
#   4. Pon esos valores (x, y) aqui. theta es la orientacion final en radianes.
#
# La CLAVE de cada entrada es el comando cerrado (igual que en la rubrica).
# =============================================================================
PLACES = {
    'go_to_refrigerator': (3.0,  2.0,  0.0),
    'go_to_table':        (1.5, -1.0,  0.0),
    'go_to_chair':        (-2.0, 1.5,  1.57),
    'go_to_sofa':         (-3.0, 0.5,  1.57),
    'go_to_painting':     (0.0, -3.0, -1.57),
    'go_home':            (0.0,  0.0,  0.0),
}

# Frases -> comando cerrado, para la capa de REGLAS. Bilingue (es / en).
RULES = {
    'go_to_refrigerator': ['refri', 'refrigerador', 'refrigerator', 'fridge',
                           'cocina', 'kitchen'],
    'go_to_table':        ['mesa', 'table'],
    'go_to_chair':        ['silla', 'chair'],
    'go_to_sofa':         ['sofa', 'sofá', 'couch', 'sala'],
    'go_to_painting':     ['cuadro', 'pintura', 'painting', 'picture'],
    'go_home':            ['inicio', 'regresa', 'home', 'origen', 'start'],
    'stop':               ['detente', 'alto', 'para', 'stop'],
}

# Lo que dice el robot al llegar, por lugar.
ARRIVAL = {
    'go_to_refrigerator': ('He llegado al refrigerador',
                           'I have arrived at the refrigerator'),
    'go_to_table':        ('He llegado a la mesa',
                           'I have arrived at the table'),
    'go_to_chair':        ('He llegado a la silla',
                           'I have arrived at the chair'),
    'go_to_sofa':         ('He llegado al sofá',
                           'I have arrived at the sofa'),
    'go_to_painting':     ('He llegado al cuadro',
                           'I have arrived at the painting'),
    'go_home':            ('He regresado al inicio',
                           'I have returned home'),
}


class CommandInterpreter(Node):
    def __init__(self):
        super().__init__('command_interpreter')

        self.declare_parameter('use_ollama', True)
        self.declare_parameter('ollama_model', 'llama3.2')
        self.use_ollama = self.get_parameter('use_ollama').value
        self.ollama_model = self.get_parameter('ollama_model').value

        # ---- Publicadores ----
        # /goal_pose es el topico que escucha tu pure_pursuit. CONFIRMADO.
        self.goal_pub = self.create_publisher(PoseStamped, '/goal_pose', 10)
        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.speech_pub = self.create_publisher(String, '/speech', 10)

        # ---- Suscriptores ----
        self.create_subscription(String, '/recognized_speech',
                                 self.speech_callback, 10)
        # Tu pure_pursuit publica True aqui cuando el robot llega. CONFIRMADO.
        self.create_subscription(Bool, '/navigation/goal_reached',
                                 self.goal_reached_callback, 10)

        # ---- Estado ----
        self.pending_command = None   # comando en curso, esperando llegada
        self.pending_lang = 'es'

        self.get_logger().info('Interprete listo. Ollama=%s' %
                               (self.use_ollama and OLLAMA_AVAILABLE))

    # ------------------------------------------------------------------ #
    def speech_callback(self, msg):
        text = msg.data.strip().lower()
        if not text:
            return
        self.get_logger().info('Texto recibido: "%s"' % text)

        command = self.interpret(text)
        if command is None:
            self.say('No entendí el comando', 'es')
            self.get_logger().warn('Sin comando para: "%s"' % text)
            return

        lang = 'en' if self.is_english(text) else 'es'
        self.get_logger().info('Comando cerrado: %s' % command)
        self.execute(command, lang)

    def goal_reached_callback(self, msg):
        # Llega cuando el robot termina de navegar.
        if msg.data and self.pending_command is not None:
            cmd = self.pending_command
            self.pending_command = None
            if cmd in ARRIVAL:
                es, en = ARRIVAL[cmd]
                self.say(en if self.pending_lang == 'en' else es,
                         self.pending_lang)
            self.get_logger().info('Robot llego. Meta %s completada.' % cmd)

    # ------------------------------------------------------------------ #
    #  INTERPRETACION: capa 1 (reglas) -> capa 2 (Ollama)
    # ------------------------------------------------------------------ #
    def interpret(self, text):
        cmd = self.interpret_rules(text)
        if cmd is not None:
            return cmd
        if self.use_ollama and OLLAMA_AVAILABLE:
            return self.interpret_ollama(text)
        return None

    def interpret_rules(self, text):
        for command, keywords in RULES.items():
            for kw in keywords:
                if kw in text:
                    return command
        return None

    def interpret_ollama(self, text):
        valid = list(PLACES.keys()) + ['stop']
        prompt = (
            "Eres un traductor de comandos para un robot de servicio. "
            "Traduce la instruccion del usuario a UNO de estos comandos "
            "exactos: " + ', '.join(valid) + ". "
            "Responde SOLO con el comando, sin explicaciones ni puntuacion. "
            "Si no corresponde a ninguno, responde: none.\n"
            "Instruccion: " + text
        )
        try:
            r = requests.post(
                'http://localhost:11434/api/generate',
                json={'model': self.ollama_model, 'prompt': prompt,
                      'stream': False},
                timeout=15)
            answer = r.json().get('response', '').strip().lower()
            self.get_logger().info('Ollama respondio: "%s"' % answer)
            for v in valid:
                if v in answer:
                    return v
        except Exception as e:
            self.get_logger().warn('Ollama no disponible: %s' % str(e))
        return None

    def is_english(self, text):
        english = ['go', 'bring', 'the', 'to', 'kitchen', 'couch', 'sofa',
                   'painting', 'table', 'chair', 'fridge', 'refrigerator',
                   'home', 'stop']
        padded = ' ' + text + ' '
        return any((' ' + w + ' ') in padded for w in english)

    # ------------------------------------------------------------------ #
    #  EJECUCION
    # ------------------------------------------------------------------ #
    def execute(self, command, lang):
        if command == 'stop':
            self.stop_robot()
            self.pending_command = None
            self.say('Detenido' if lang == 'es' else 'Stopped', lang)
            return

        if command in PLACES:
            self.publish_goal(PLACES[command])
            self.pending_command = command
            self.pending_lang = lang
            place = command.replace('go_to_', '').replace('go_home', 'inicio')
            self.say(('Voy hacia el ' + place) if lang == 'es'
                     else ('Going to the ' + place), lang)

    def publish_goal(self, coords):
        x, y, theta = coords
        msg = PoseStamped()
        msg.header.frame_id = 'map'
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.pose.position.x = float(x)
        msg.pose.position.y = float(y)
        msg.pose.orientation.z = math.sin(theta / 2.0)
        msg.pose.orientation.w = math.cos(theta / 2.0)
        self.goal_pub.publish(msg)
        self.get_logger().info('Meta publicada en /goal_pose: %s' % str(coords))

    def stop_robot(self):
        self.cmd_pub.publish(Twist())   # velocidad cero

    def say(self, text, lang='es'):
        msg = String()
        msg.data = text
        self.speech_pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = CommandInterpreter()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
