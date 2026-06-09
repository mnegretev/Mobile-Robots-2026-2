"""
hri_proyecto.brain
==================
Voice-controlled robot brain node.

Pipeline
--------
1. /sp_rec/recognized  ->  raw transcribed text arrives
2. LLM (Ollama)        ->  classifies intent and extracts destination
3. Dispatcher          ->  publishes /nav_command  AND/OR  /tts_query reply
"""

import json
import urllib.request
import urllib.error
from dataclasses import dataclass
from typing import Optional

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from geometry_msgs.msg import Twist


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.2:1b"

# Request timeout for the Ollama HTTP call (seconds).
OLLAMA_TIMEOUT = 120

# Known locations: name -> (x, y)
LOCATIONS: dict[str, tuple[float, float]] = {
    "refrigerador": (10.0,  0.5),
    "estufa":       (10.5, -1.5),
    "lavamanos":    (10.0, -3.0),
    "mesa cocina":  ( 8.0,  2.0),
    "gimnasio":     ( 5.0,  4.0),
    "cama":         (-2.5,  3.2),
}

# The prompt sent to the LLM. The model must reply with JSON only.
SYSTEM_PROMPT = """
Eres el cerebro de un robot doméstico. Clasifica el mensaje del usuario y responde SOLO con JSON.

Lugares a los que puedes ir:
- refrigerador (sinónimos: nevera, refri, comida, hambre, agua)
- estufa (sinónimos: cocina, horno, cocinar)
- lavamanos (sinónimos: baño, manos, lavarme)
- mesa cocina (sinónimos: mesa, comer, cenar, almorzar)
- gimnasio (sinónimos: gym, ejercicio, entrenar, deporte)
- cama (sinónimos: dormir, descansar, cuarto, habitacion, recamara)

Solo puedes moverte. No puedes traer objetos, abrir puertas, encender aparatos ni hacer acciones físicas.

Responde SOLO con este JSON, sin texto adicional:
{"intent": "navigate", "destination": "refrigerador", "reply": "Voy al refrigerador."}

Usa intent "navigate" si el usuario quiere ir a un lugar.
Usa intent "stop" si quiere que te detengas.
Usa intent "unable" si pide algo que no puedes hacer fisicamente.
Usa intent "chat" para saludos o preguntas simples.

Para "navigate", pon el nombre exacto del lugar en destination.
Para "stop", "unable" y "chat", pon null en destination.
"""


# ---------------------------------------------------------------------------
# Data model for a parsed LLM response
# ---------------------------------------------------------------------------

@dataclass
class ParsedIntent:
    intent: str               # "navigate" | "stop" | "chat" | "unable"
    destination: Optional[str]
    reply: str


# ---------------------------------------------------------------------------
# Node
# ---------------------------------------------------------------------------

class BrainNode(Node):
    """
    Subscribes to /sp_rec/recognized, queries Ollama to parse intent,
    then publishes to /nav_command and /tts_query.
    """

    def __init__(self) -> None:
        super().__init__("hri_proyecto_brain")

        # -- Subscribers --
        self.speech_sub = self.create_subscription(
            String,
            "/sp_rec/recognized",
            self._on_speech,
            10,
        )

        # -- Publishers --
        self.tts_pub = self.create_publisher(String, "/tts_query", 10)
        self.nav_pub = self.create_publisher(String, "/nav_command", 10)
        self.vel_pub = self.create_publisher(Twist, "/cmd_vel", 10)

        self.get_logger().info("Brain node started. Waiting for speech input...")

    # ------------------------------------------------------------------
    # Callback
    # ------------------------------------------------------------------

    def _on_speech(self, msg: String) -> None:
        text = msg.data.strip()
        if not text:
            return

        self.get_logger().info(f"[Speech received] '{text}'")

        # Step 1 - parse intent via LLM
        parsed = self._query_llm(text)
        if parsed is None:
            self._speak("No pude procesar tu mensaje. Intenta de nuevo.")
            return

        self.get_logger().info(
            f"[Intent] {parsed.intent} | destination={parsed.destination}"
        )

        # Step 2 - dispatch
        if parsed.intent == "navigate" and parsed.destination:
            self._navigate(parsed.destination, parsed.reply)

        elif parsed.intent == "stop":
            self._stop(parsed.reply)

        elif parsed.intent == "unable":
            self.get_logger().warning(f"[Unable] Action not supported.")
            self._speak(parsed.reply)

        else:  # "chat"
            self._speak(parsed.reply)

    # ------------------------------------------------------------------
    # LLM interaction
    # ------------------------------------------------------------------

    def _query_llm(self, user_text: str) -> Optional[ParsedIntent]:
        """
        Send user_text to Ollama and parse the JSON response.
        Returns None if the call fails or the response is malformed.
        """
        payload = json.dumps({
            "model": OLLAMA_MODEL,
            "prompt": user_text,
            "system": SYSTEM_PROMPT,
            "stream": False,
        }).encode("utf-8")

        self.get_logger().info("[LLM] Sending request to Ollama...")

        try:
            req = urllib.request.Request(
                OLLAMA_URL,
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=OLLAMA_TIMEOUT) as resp:
                raw = json.loads(resp.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            self.get_logger().error(f"[LLM] Connection error: {exc}")
            return None
        except Exception as exc:
            self.get_logger().error(f"[LLM] Unexpected error: {exc}")
            return None

        llm_text = raw.get("response", "").strip()
        self.get_logger().info(f"[LLM] Raw response: {llm_text}")

        return self._parse_llm_response(llm_text)

    def _parse_llm_response(self, text: str) -> Optional[ParsedIntent]:
        """
        Parse the LLM JSON string into a ParsedIntent.
        Returns None if parsing fails.
        """
        text = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()

        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            self.get_logger().error(f"[LLM] JSON decode error: {exc}")
            return None

        intent = data.get("intent", "chat")
        destination = data.get("destination")
        reply = data.get("reply", "Entendido.")

        # Validate destination only for navigate intent
        if intent == "navigate" and destination not in LOCATIONS:
            self.get_logger().warning(
                f"[LLM] Unknown destination '{destination}'. Falling back to chat."
            )
            intent = "chat"
            destination = None
            reply = "No reconozco ese lugar. Por favor repite el destino."

        return ParsedIntent(intent=intent, destination=destination, reply=reply)

    # ------------------------------------------------------------------
    # Action helpers
    # ------------------------------------------------------------------

    def _navigate(self, destination: str, reply: str) -> None:
        """Publish a nav_command string and speak the reply."""
        nav_msg = String()
        nav_msg.data = f"go to {destination}"
        self.nav_pub.publish(nav_msg)

        self.get_logger().info(f"[Navigate] Published to /nav_command -> 'go to {destination}'")
        self._speak(reply)

    def _stop(self, reply: str) -> None:
        """Publish a zero-velocity Twist and speak the reply."""
        self.vel_pub.publish(Twist())
        self.get_logger().info("[Stop] Zero-velocity command published.")
        self._speak(reply)

    def _speak(self, text: str) -> None:
        """Publish a string to the TTS topic."""
        msg = String()
        msg.data = text
        self.tts_pub.publish(msg)
        self.get_logger().info(f"[TTS] '{text}'")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main(args=None) -> None:
    rclpy.init(args=args)
    node = BrainNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("Shutting down brain node.")
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()