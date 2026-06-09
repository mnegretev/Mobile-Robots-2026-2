import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import requests
import json

class OllamaPlanningNode(Node):
    def __init__(self):
        super().__init__('ollama_planning_node')
        self.get_logger().info('INITIALIZING OLLAMA PLANNING NODE')
        
        # Configuración de Ollama
        self.url_api = "http://localhost:11434/api/generate"
        self.model = "llama3"
        
        # Historial de conversación
        self.msg_history = []
        
        # Publicador para respuestas
        self.publisher = self.create_publisher(String, '/llm_response', 10)
        
        # Timer para enviar prompts automáticos
        self.timer = self.create_timer(10, self.timer_callback)
        self.prompt_count = 0
        
        self.get_logger().info('OLLAMA PLANNING NODE READY')
        
    def send_prompt(self, prompt):
        """Envía un prompt a Ollama y publica la respuesta"""
        self.get_logger().info(f'Sending prompt: {prompt}')
        
        # Preparar el payload para /api/generate
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_ctx": 8192,
                "temperature": 0.7
            }
        }
        
        try:
            # Enviar petición a Ollama
            resp = requests.post(self.url_api, json=payload, timeout=30)
            
            # Verificar respuesta
            if resp.status_code != 200:
                self.get_logger().error(f'Ollama error {resp.status_code}: {resp.text}')
                return None
            
            # Parsear respuesta
            data = resp.json()
            
            # Extraer el texto de respuesta
            if 'response' in data:
                response_text = data['response']
                self.get_logger().info(f'Response: {response_text[:200]}')
                
                # Publicar en tópico ROS2
                msg = String()
                msg.data = response_text
                self.publisher.publish(msg)
                
                return response_text
            else:
                self.get_logger().error(f'Unexpected response format: {data}')
                return None
                
        except requests.exceptions.ConnectionError:
            self.get_logger().error('Cannot connect to Ollama. Make sure it is running with: OLLAMA_NUM_GPU=0 ollama serve')
            return None
        except Exception as e:
            self.get_logger().error(f'Error: {e}')
            return None
    
    def timer_callback(self):
        """Envía prompts automáticos cada cierto tiempo"""
        prompts = [
            "Genera respuestas de máximo veinte palabras",
            "Eres un robot de servicio, responde de forma amable",
            "¿Cómo puedes ayudar a un usuario?"
        ]
        
        if self.prompt_count < len(prompts):
            self.send_prompt(prompts[self.prompt_count])
            self.prompt_count += 1
        else:
            self.get_logger().info('Waiting for new prompt...')

def main(args=None):
    rclpy.init(args=args)
    node = OllamaPlanningNode()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('Shutting down...')
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()