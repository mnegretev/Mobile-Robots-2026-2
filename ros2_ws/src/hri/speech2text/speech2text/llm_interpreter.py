#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from std_msgs.msg import String, Int32
import ollama

class LLMInterpreterNode(Node):
    def __init__(self):
        super().__init__('llm_interpreter')
        self.subscription = self.create_subscription(
            String,
            '/speech/text',
            self.listener_callback,
            10)
        self.publisher_ = self.create_publisher(Int32, '/llm/action_code', 10)
        self.get_logger().info("Nodo LLM Interpreter listo. Esperando comandos...")

    def listener_callback(self, msg):
        command_text = msg.data.lower()
        self.get_logger().info(f'Comando recibido: "{command_text}"')

        # Prompt para el LLM
        prompt = f"""
        [INST] <<SYS>>
        Eres un clasificador de comandos para un robot. Tu única tarea es asignar un código numérico a la intención del usuario. No des explicaciones.
        - Si la intención del comando está relacionada con abrir el refrigerador, revisar su interior o traer algo de él, responde ÚNICAMENTE con el número 0001.
        - Si es relacionada con la PUERTA (abrir, cerrar, acercarse), responde ÚNICAMENTE con: 0002
        - Si es relacionada con la FOTO del CUARTO (traer, buscar, mostrar), responde ÚNICAMENTE con: 0003
        - Para CUALQUIER OTRA intención, responde ÚNICAMENTE con el número 0000.
        <</SYS>>
        Texto del comando: "{command_text}"
        [/INST]
        """

        try:
            # Llamar al modelo Ollama
            response = ollama.generate(model='llama3.2', prompt=prompt)
            code_str = response['response'].strip()
            action_code = int(code_str)

            self.get_logger().info(f'Código de acción generado: {action_code:04d}')
            msg = Int32()
            msg.data = action_code
            self.publisher_.publish(msg)

        except ValueError:
            self.get_logger().error(f'Ollama devolvió una respuesta no numérica: "{code_str}". Publicando 0000 por defecto.')
            msg = Int32()
            msg.data = 0
            self.publisher_.publish(msg)
        except Exception as e:
            self.get_logger().error(f'Error al comunicarse con Ollama: {e}. Publicando código 0000.')
            msg = Int32()
            msg.data = 0
            self.publisher_.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = LLMInterpreterNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()