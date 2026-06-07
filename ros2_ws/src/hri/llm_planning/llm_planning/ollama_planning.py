import requests
import rclpy
from rclpy.node import Node
from rclpy.duration import Duration
from std_msgs.msg import String
from ament_index_python.packages import get_package_share_directory
import os
import json


class OllamaPlanningNode(Node):

    def load_prompts(self, path):
        lines = open(path).readlines()
        prompts = []

        for l in lines:
            s = l.rstrip()
            if len(s) > 3:
                prompts.append(s)
        return prompts

    def send_prompt(self, msg):
        self.msg_history.append(
            {"role": "user","content": msg}
        )

        resp = requests.post(
            self.url_api,
            json={"model": "llama3","messages": self.msg_history,"stream": False,"options": {"num_ctx": 8192}}
        )

        self.msg_history.append(resp.json()["message"])

    def callback_prompt(self, msg):

        if self.new_prompt:
            self.get_logger().info("Ignoring received prompt...")
            return

        self.prompt = msg.data
        self.new_prompt = True

    def process_action(self, data):
        action = data.get("action","UNSUPPORTED")
        if action == "ANSWER":
            self.pub_tts.publish(String(data=data.get("message","No tengo respuesta")))
            return

        self.pub_task.publish(String(data=json.dumps(data)))

        if action == "FIND_PERSON":
            self.pub_tts.publish(String(data="Buscando una persona"))

        elif action == "FIND_OBJECT":
            obj = data.get("object","objeto")
            self.pub_tts.publish(String(data=f"Buscando {obj}"))

        elif action == "APPROACH_PERSON":

            self.pub_tts.publish(
                String(data="Acercándome a la persona")
            )

        elif action == "GO_TO_OBJECT":

            obj = data.get(
                "object",
                "objeto"
            )

            self.pub_tts.publish(
                String(data=f"Yendo hacia {obj}")
            )

        elif action == "NAVIGATE":

            destination = data.get(
                "destination",
                "destino"
            )

            self.pub_tts.publish(
                String(
                    data=f"Navegando hacia {destination}"
                )
            )

        elif action == "MOVE_ARM":

            self.pub_tts.publish(
                String(data="Moviendo brazo")
            )

        elif action == "PICK_OBJECT":

            obj = data.get(
                "object",
                "objeto"
            )

            self.pub_tts.publish(
                String(
                    data=f"Intentando tomar {obj}"
                )
            )

        else:

            self.pub_tts.publish(
                String(
                    data="No puedo realizar esa acción"
                )
            )

    def __init__(self):

        super().__init__(
            "ollama_planning_node"
        )

        self.get_logger().info(
            "INITIALIZING OLLAMA PLANNING NODE"
        )

        self.msg_history = []
        self.url_api = "http://localhost:11434/api/chat"
        self.prompt = ""
        self.new_prompt = False

        self.sub_query = self.create_subscription(
            String,
            "/sp_rec/recognized",
            self.callback_prompt,
            1
        )

        self.pub_tts = self.create_publisher(
            String,
            "/tts_query",
            1
        )

        self.pub_task = self.create_publisher(
            String,
            "/robot_task",
            10
        )

    def spin(self):

        prompts_file = os.path.join(
            get_package_share_directory("llm_planning"),
            "config",
            "Prompts.txt"
        )

        prompts = self.load_prompts(
            prompts_file
        )

        self.send_prompt("""
Eres el planificador de un robot móvil.

Capacidades:
- FIND_PERSON
- FIND_OBJECT
- NAVIGATE
- MOVE_ARM
- PICK_OBJECT
- ANSWER
- UNSUPPORTED
- APPROACH_PERSON
- GO_TO_OBJECT

IMPORTANTE:
Responde únicamente con JSON.
No uses markdown.
No agregues explicaciones.
No escribas texto antes ni después del JSON.

Usuario: busca una persona
{"action":"FIND_PERSON"}

Usuario: busca una botella
{"action":"FIND_OBJECT","object":"bottle"}

Usuario: mueve el brazo
{"action":"MOVE_ARM"}

Usuario: ve a la cocina
{"action":"NAVIGATE","destination":"kitchen"}

Usuario: toma la botella
{"action":"PICK_OBJECT","object":"bottle"}

Usuario: quien eres
{"action":"ANSWER","message":"Soy un robot de servicio"}

Usuario: vuela
{"action":"UNSUPPORTED"}

Usuario: acércate a la persona
{"action":"APPROACH_PERSON"}

Usuario: ve hacia la botella
{"action":"GO_TO_OBJECT","object":"bottle"}
""")

        for p in prompts:

            self.get_logger().info(
                "Sending prompt: " + p
            )

            self.send_prompt(p)

            self.get_logger().info(
                "Response received: " +
                self.msg_history[-1]["content"]
            )

        self.get_logger().info(
            "Waiting for new prompt..."
        )

        while rclpy.ok():

            if self.new_prompt:

                self.get_logger().info(
                    "Sending prompt: " +
                    self.prompt
                )

                self.send_prompt(
                    self.prompt
                )

                self.get_logger().info(
                    "Response received: " +
                    self.msg_history[-1]["content"]
                )

                try:

                    data = json.loads(
                        self.msg_history[-1]["content"]
                    )
                    self.process_action(
                        data
                    )
                except Exception as e:
                    self.get_logger().error(
                        f"Error parsing JSON: {e}"
                    )
                    self.pub_tts.publish(
                        String(
                            data="Error procesando instrucción"
                        )
                    )
                self.new_prompt = False
            rclpy.spin_once(self,timeout_sec=0)
            self.get_clock().sleep_for(Duration(seconds=0.05))

def main(args=None):
    rclpy.init(args=args)
    node = OllamaPlanningNode()
    node.spin()
    node.destroy_node()
    rclpy.shutdown()
if __name__ == "__main__":
    main()
