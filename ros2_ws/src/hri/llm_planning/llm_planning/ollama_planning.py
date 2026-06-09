import os
import requests
import json
import rclpy
from rclpy.node import Node
from rclpy.duration import Duration
from std_msgs.msg import String, Bool
from ament_index_python.packages import get_package_share_directory

SM_INIT = 0
SM_LOAD_INITIAL_PROMPTS = 10
SM_LOOK_FOR_PERSON = 20
SM_RANDOM_MOVEMENT = 30
SM_APPROACH_TO_PERSON = 40
SM_INITIAL_INTERACTION = 50
SM_INTERACTION = 60


class OllamaPlanningNode(Node):

    def __init__(self):
        super().__init__("ollama_planning_node")
        self.get_logger().info("INITIALIZING OLLAMA PLANNING NODE")
        self.msg_history = []
        self.url_api = "http://localhost:11434/api/chat"
        self.prompt = ""
        self.new_prompt = False
        
        # Suscripción
        self.sub_query = self.create_subscription(String, '/sp_rec/recognized', self.callback_prompt, 1)
        self.prompt_enable_sub = self.create_subscription(Bool, '/prompt_enable',self.enable_prompt_callback,10)
        
        # Publicadores unificados aquí (Mantenemos los tuyos y sumamos el canal del TaskExecutor)
        self.pub_tts = self.create_publisher(String, '/tts_query', 1)
        self.pub_nav_goal = self.create_publisher(String, '/nav_goal', 1)
        self.pub_search = self.create_publisher(String, '/search_object', 1)
        self.pub_robot_task = self.create_publisher(String, '/robot_task', 10) # <-- Canal para conectar con TaskExecutor

        self.recieve_new_prompt = True

    def enable_prompt_callback (self,msg):
        self.recieve_new_prompt = msg.data

    def load_prompts(self, path):
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        return [content]

    def send_prompt(self, msg):
        self.msg_history.append({"role": "user", "content": msg})
        resp = requests.post(self.url_api, json={"model": "llama3", "messages": self.msg_history, "stream": False, "options": {"num_ctx": 8192}})
        self.msg_history.append(resp.json()["message"])

    def callback_prompt(self, msg):
        if self.new_prompt:
            self.get_logger().info("Ignoring received prompt...")
            return
        self.prompt = msg.data
        self.new_prompt = True

    def spin(self):
        prompts_file = os.path.join(get_package_share_directory('llm_planning'), "config", "Prompts.txt")
        prompts = self.load_prompts(prompts_file)
        self.send_prompt("Genera respuestas de máximo veinte palabras")
        for p in prompts:
            self.get_logger().info("Sending prompt: " + p)
            self.send_prompt(p)
            self.get_logger().info("Response received: " + self.msg_history[-1]["content"])
        self.send_prompt("Da respuestas muy sintetizadas y concisas en formato JSON string")
        
        
        self.get_logger().info("Waiting for new prompt...")
        while rclpy.ok():
            if self.new_prompt:
                self.get_logger().info("Sending prompt: " + self.prompt)
                self.send_prompt(self.prompt)
                self.get_logger().info("Response received: " + self.msg_history[-1]["content"])
                response = self.msg_history[-1]["content"].strip()

                # --- VALIDACIÓN E INTERPRETACIÓN PARA EL TASK EXECUTOR ---
                try:
                    # Parseas el JSON que viene de Ollama
                    task_data = json.loads(response)

                    if not isinstance(task_data, dict):
                         raise json.JSONDecodeError("Response is not a JSON object",response,0)

                    action = task_data.get("action", "")

                    if action == "FIND_OBJECT":
                        self.get_logger().info("SEARCH MODE ACTIVATED")
                        # Tu lógica original de publicación
                        self.pub_search.publish(String(data="search"))
                        # Reenvío al TaskExecutor
                        self.pub_robot_task.publish(String(data=response))

                    elif action == "MOVE_ARM":
                        self.get_logger().info("MOVE ARM MODE ACTIVATED")
                        self.pub_tts.publish(String(data="Moviendo el brazo articulado"))
                        # Reenvío directo al TaskExecutor para activar las 6 articulaciones
                        self.pub_robot_task.publish(String(data=response))

                    elif action == "PICK_OBJECT":
                        self.get_logger().info("PICK OBJECT MODE ACTIVATED")
                        self.pub_robot_task.publish(String(data=response))

                    elif action == "FIND_PERSON":
                        self.get_logger().info("FIND PERSON MODE ACTIVATED")
                        self.pub_robot_task.publish(String(data=response))

                    elif action == "NAVIGATE":
                        destination = task_data.get("destination", "")
                        self.get_logger().info(f"NAVIGATION GOAL TO DESTINATION: {destination}")
                        self.pub_tts.publish(String(data=f"Navegando hacia {destination}"))
                        # Reenvío directo al TaskExecutor
                        self.pub_robot_task.publish(String(data=response))

                    elif action == "UNSUPPORTED":
                        # Acción rechazada / fuera de capacidades
                        self.pub_tts.publish(String(data="Lo siento, esa acción no está dentro de mis capacidades"))

                    else:
                        # Si es una respuesta normal o pregunta informativa
                        self.pub_tts.publish(String(data=response))

                except Exception:
                    # Si por alguna razón Ollama no responde un JSON limpio (texto plano residual)
                    if response == "3":
                        self.get_logger().info("SEARCH MODE ACTIVATED")
                        self.pub_search.publish(String(data="search"))
                    elif "Ese objeto no está aquí" in response:
                        self.pub_tts.publish(String(data="Ese objeto no está aquí"))
                    elif response == "Eso no está dentro de mis capacidades":
                        self.pub_tts.publish(String(data=response))
                    elif response == "Esa pregunta no la puedo responder":
                        self.pub_tts.publish(String(data=response))
                    else:
                        # Intento de coordenadas nativo de tu código original
                        try:
                            values = response.split()
                            if len(values) == 2:
                                x = float(values[0])
                                y = float(values[1])
                                self.get_logger().info(f"NAVIGATION GOAL: ({x}, {y})")
                                self.pub_nav_goal.publish(String(data=f"{x} {y}"))
                            else:
                                self.pub_tts.publish(String(data=response))
                        except ValueError:
                            self.pub_tts.publish(String(data=response))
                # ---------------------------------------------------------

                delay_counter = int(1.9 * len(self.msg_history[-1]["content"]) + 20)
                while delay_counter > 0 and rclpy.ok() and not self.recieve_new_prompt:
                    rclpy.spin_once(self, timeout_sec=0)
                    self.get_clock().sleep_for(Duration(seconds=0.05))
                    self.get_logger().info("Ejecutando una accion, espere para solicitar otra cosa")
                    delay_counter -= 1
                self.get_logger().info("Waiting for new prompt")
                self.new_prompt = False
                
            rclpy.spin_once(self, timeout_sec=0)
            self.get_clock().sleep_for(Duration(seconds=0.05))


def main(args=None):
    rclpy.init(args=args)
    ollama_planning_node = OllamaPlanningNode()
    ollama_planning_node.spin()
    ollama_planning_node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()