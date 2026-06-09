import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import requests
import json

class OllamaPlanningNode(Node):
    def __init__(self):
        super().__init__('ollama_planning')
        
        # Suscribirse al texto del ASR
        self.subscription = self.create_subscription(
            String,
            '/speech_to_text',
            self.speech_callback,
            10
        )
        
        # Publicar comandos para el robot
        self.publisher_ = self.create_publisher(String, '/robot_commands', 10)
        
        # URL de Ollama
        self.ollama_url = "http://localhost:11434/api/generate"
        
        # Prompt del sistema
        self.system_prompt = """Eres un robot de servicio doméstico. 
Tus únicas habilidades son:
1. Moverte a posiciones específicas en el hogar
2. Extender tu brazo para simular que recoges un objeto

Instrucciones:
- Si te piden algo que PUEDES hacer (moverte o recoger), responde SOLO con un comando JSON estructurado así:
  {"action": "move|pick", "target": "descripción del lugar", "confidence": valor_0_a_1}
  
- Si te piden algo FUERA de tus capacidades (volar, cocinar, limpiar, etc), responde SOLO con:
  {"action": "sorry", "reason": "breve explicación de por qué no puedes hacerlo"}

Ejemplos:
- Usuario: "Recoge la taza de la mesa" → {"action": "pick", "target": "mesa", "confidence": 0.9}
- Usuario: "Muévete a la cocina" → {"action": "move", "target": "cocina", "confidence": 0.95}
- Usuario: "Vuela hasta el techo" → {"action": "sorry", "reason": "No tengo capacidad de vuelo"}
- Usuario: "Cociname un café" → {"action": "sorry", "reason": "No tengo hardware de cocina"}

IMPORTANTE: Responde SOLO con JSON, sin explicaciones adicionales."""
        
        self.get_logger().info('Nodo Ollama Planning iniciado')
        self.get_logger().info('Esperando instrucciones del ASR...')
    
    def speech_callback(self, msg):
        self.get_logger().info(f'Instrucción recibida: {msg.data}')
        
        try:
            # Llamar a Ollama
            response = self.query_ollama(msg.data)
            
            # Publicar respuesta/comando
            cmd_msg = String()
            cmd_msg.data = response
            self.publisher_.publish(cmd_msg)
            self.get_logger().info(f'Comando publicado: {response}')
            
        except Exception as e:
            self.get_logger().error(f'Error en Ollama: {str(e)}')
    
    def query_ollama(self, user_input):
        payload = {
            "model": "ollama",
            "prompt": f"{self.system_prompt}\n\nUsuario: {user_input}",
            "stream": False,
            "temperature": 0.3,
        }
        
        try:
            response = requests.post(self.ollama_url, json=payload, timeout=30)
            response.raise_for_status()
            result = response.json()
            return result.get('response', '{"action": "error", "reason": "No response"}')
        except requests.exceptions.ConnectionError:
            self.get_logger().error('❌ No se pudo conectar a Ollama en http://localhost:11434')
            self.get_logger().error('   Asegúrate de que Ollama está ejecutándose: ollama serve')
            return '{"action": "error", "reason": "Ollama no disponible"}'
        except Exception as e:
            return f'{{"action": "error", "reason": "{str(e)}"}}'

def main(args=None):
    rclpy.init(args=args)
    node = OllamaPlanningNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
