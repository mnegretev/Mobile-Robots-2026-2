import json
import requests

import rclpy
from rclpy.node import Node

from std_msgs.msg import String


class LLMTaskPlanner(Node):
    def __init__(self):
        super().__init__('llm_task_planner')

        self.declare_parameter('model', 'qwen2.5:0.5b')
        self.declare_parameter('ollama_url', 'http://localhost:11434/api/generate')

        self.model = self.get_parameter('model').value
        self.ollama_url = self.get_parameter('ollama_url').value

        self.sub_voice_text = self.create_subscription(
            String,
            '/voice_text',
            self.voice_callback,
            10
        )

        self.pub_task_sequence = self.create_publisher(
            String,
            '/task_sequence',
            10
        )

        self.pub_llm_response = self.create_publisher(
            String,
            '/llm_response',
            10
        )

        self.busy = False

        self.location_aliases = {
            'cama': 'cama',
            'cuarto': 'cama',

            'refrigerador': 'refrigerador',
            'refri': 'refrigerador',
            'nevera': 'refrigerador',

            'sillon': 'sillon',
            'sillón': 'sillon',
            'sofa': 'sillon',
            'sofá': 'sillon',

            'pesas': 'pesas',
            'gym': 'pesas',
            'ejercicio': 'pesas',

            'tele': 'tele',
            'television': 'tele',
            'televisión': 'tele',
            'tv': 'tele',

            'pelota': 'pelota',
            'balon': 'pelota',
            'balón': 'pelota',

            'puerta': 'puerta',
            'puertas': 'puerta',
            'salida': 'puerta'
        }

        self.arm_aliases = {
            'saluda': 'saludar',
            'saludar': 'saludar',
            'di hola': 'saludar',

            'agarra abajo': 'agarrar_abajo',
            'agarrar abajo': 'agarrar_abajo',
            'toma abajo': 'agarrar_abajo',
            'tomar abajo': 'agarrar_abajo',

            'agarra medio': 'agarrar_medio',
            'agarrar medio': 'agarrar_medio',
            'agarra enfrente': 'agarrar_medio',
            'agarrar enfrente': 'agarrar_medio',
            'agarra algo': 'agarrar_medio',
            'agarrar algo': 'agarrar_medio',

            'agarra arriba': 'agarrar_arriba',
            'agarrar arriba': 'agarrar_arriba',
            'toma arriba': 'agarrar_arriba',
            'tomar arriba': 'agarrar_arriba'
        }

        self.object_words = [
            'jugo',
            'vaso',
            'botella',
            'objeto',
            'algo',
            'cosa'
        ]

        self.get_logger().info('LLM task planner listo.')
        self.get_logger().info(f'Modelo Ollama: {self.model}')
        self.get_logger().info('Modo seguro: comandos del robot se parsean sin LLM.')

    def voice_callback(self, msg):
        if self.busy:
            self.get_logger().warn('Sistema ocupado. Ignorando comando nuevo.')
            return

        self.busy = True

        try:
            text = msg.data.lower().strip()
            self.get_logger().info(f'Texto recibido de Whisper: "{text}"')

            task_sequence = self.local_task_parser(text)

            if task_sequence is not None:
                out_msg = String()
                out_msg.data = json.dumps(task_sequence)

                self.pub_task_sequence.publish(out_msg)

                self.get_logger().info(f'Secuencia local publicada en /task_sequence: {out_msg.data}')
                return

            response = self.call_ollama_chat(text)

            if response is None or response == '':
                response = 'No tengo una respuesta clara.'

            out_msg = String()
            out_msg.data = response

            self.pub_llm_response.publish(out_msg)

            self.get_logger().info(f'Respuesta chat publicada en /llm_response: {response}')

        finally:
            self.busy = False

    def local_task_parser(self, text):
        events = []

        for alias, location in self.location_aliases.items():
            index = text.find(alias)

            if index != -1:
                events.append({
                    'index': index,
                    'type': 'navigate',
                    'target': location
                })

        for alias, action in self.arm_aliases.items():
            index = text.find(alias)

            if index != -1:
                events.append({
                    'index': index,
                    'type': 'arm',
                    'target': action
                })

        events.sort(key=lambda event: event['index'])

        steps = []

        for event in events:
            step = {
                'type': event['type'],
                'target': event['target']
            }

            if len(steps) == 0:
                steps.append(step)
                continue

            last = steps[-1]

            if last['type'] == step['type'] and last['target'] == step['target']:
                continue

            steps.append(step)

        has_location = any(step['type'] == 'navigate' for step in steps)
        has_arm_action = any(step['type'] == 'arm' for step in steps)
        mentions_object = any(word in text for word in self.object_words)

        if has_location and mentions_object and not has_arm_action:
            steps = self.insert_arm_action_after_refrigerator(steps)

        if len(steps) == 0:
            return None

        return {
            'steps': steps
        }

    def insert_arm_action_after_refrigerator(self, steps):
        new_steps = []
        inserted = False

        for step in steps:
            new_steps.append(step)

            if (
                step['type'] == 'navigate'
                and step['target'] == 'refrigerador'
                and not inserted
            ):
                new_steps.append({
                    'type': 'arm',
                    'target': 'agarrar_medio'
                })
                inserted = True

        if not inserted:
            new_steps.append({
                'type': 'arm',
                'target': 'agarrar_medio'
            })

        return new_steps

    def call_ollama_chat(self, user_text):
        prompt = f"""
Responde brevemente en español.
No generes comandos de robot.
No uses JSON.
Usuario: {user_text}
Respuesta:
"""

        payload = {
            'model': self.model,
            'stream': False,
            'prompt': prompt,
            'options': {
                'temperature': 0.2,
                'num_predict': 80,
                'num_ctx': 512
            },
            'keep_alive': '30m'
        }

        try:
            response = requests.post(
                self.ollama_url,
                json=payload,
                timeout=180
            )

            response.raise_for_status()

            data = response.json()
            content = data.get('response', '')

            return content.strip()

        except Exception as e:
            self.get_logger().error(f'Error llamando a Ollama: {e}')
            return None


def main(args=None):
    rclpy.init(args=args)

    node = LLMTaskPlanner()
    rclpy.spin(node)

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
