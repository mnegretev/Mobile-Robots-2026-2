# sm_planner.py — Robot de Propósito General
# Materia: Robots Móviles, FI-UNAM 2026-2
# Autor: Zambrano Miranda Isaac Jaciel
# Versión: v14 — auditoria completa, correcciones de seguridad operativa

import re
import os
import json
import time
import unicodedata as _UD

import rclpy
from rclpy.node import Node
from rclpy.duration import Duration
from std_msgs.msg import String, Bool
from geometry_msgs.msg import PoseStamped, Twist
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
import requests

# ─────────────────────────────────────────────────────────────────────────────
# ESTADOS DE LA MÁQUINA
# ─────────────────────────────────────────────────────────────────────────────
SM_WAIT_FOR_COMMAND  = 0
SM_INTERPRET_COMMAND = 10
SM_EXECUTE_PLAN      = 20
SM_WAIT_GOAL_REACHED = 40
SM_DONE              = 80

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURACIÓN GLOBAL
# ─────────────────────────────────────────────────────────────────────────────

# FIX #9/#12: Bandera de seguridad para manipulación.
# Cambiar a True solo cuando el brazo esté validado.
ALLOW_MANIPULATION = False

# Timeout de navegación: ciclos de 0.05 s (2400 = 120 s)
NAV_TIMEOUT_CYCLES = 2400

# Límites del parser
MAX_PLAN_STEPS  = 10
MAX_SPEAK_CHARS = 250
MAX_DETECT_CHARS = 50

# Ollama
OLLAMA_URL   = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "llama3.2:3b"
OLLAMA_TIMEOUT = 12  # FIX #15: reducir de 45 a 12 s

# ─────────────────────────────────────────────────────────────────────────────
# DATOS DEL ENTORNO
# ─────────────────────────────────────────────────────────────────────────────
LOCATIONS = {
    "home":         {"x":  0.0,  "y":  0.0,  "w": 1.0},
    "refrigerator": {"x": 10.35, "y":  0.39, "w": 1.0},
    "kitchen":      {"x": 10.53, "y": -2.26, "w": 1.0},
    "table":        {"x":  8.92, "y":  1.41, "w": 1.0},
    "sofa":         {"x":  2.45, "y":  1.15, "w": 1.0},
    "tv":           {"x":  2.98, "y": -2.97, "w": 1.0},
    "bed":          {"x": -3.95, "y":  2.25, "w": 1.0},
    "door":         {"x": 10.29, "y": -2.71, "w": 1.0},
    "stove":        {"x":  5.59, "y":  0.78, "w": 1.0},
}

def _norm(s: str) -> str:
    """Normaliza: quita acentos, lowercase."""
    return _UD.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii").lower()

SYNONYMS = {
    "refri": "refrigerator", "refrigerador": "refrigerator",
    "nevera": "refrigerator", "refrigerator": "refrigerator",
    "cocina": "kitchen",     "kitchen": "kitchen",
    "mesa":   "table",       "table": "table",
    "sofa":   "sofa",        "sillon": "sofa",
    "cama":   "bed",         "bed": "bed",
    "tele":   "tv",          "television": "tv", "tv": "tv",
    "puerta": "door",        "door": "door",
    "estufa": "stove",       "stove": "stove",
    "inicio": "home",        "casa": "home", "base": "home", "home": "home",
}

IMPOSSIBLE = {
    "vuela":     "No puedo volar.",
    "volar":     "No puedo volar.",
    "teleporta": "No puedo teleportarme.",
    "desaparece":"No puedo desaparecer.",
}

NEGATIONS = [
    "no vayas", "no navegues", "no te muevas",
    "no quiero que vayas", "no vayas a", "no ir",
]

PATROL_WAYPOINTS = ["sofa", "tv", "table", "refrigerator", "kitchen", "bed", "home"]

# ─────────────────────────────────────────────────────────────────────────────
# SYSTEM PROMPT
# FIX #12: coherente con ALLOW_MANIPULATION=False
# ─────────────────────────────────────────────────────────────────────────────
_manip_line = (
    "  MANIPULATE objeto  -> deshabilitado en modo seguro\n"
    if not ALLOW_MANIPULATION else
    "  MANIPULATE objeto  -> el robot intenta manipular el objeto con el brazo\n"
)
_manip_cap = (
    "No puedo manipular objetos en modo seguro."
    if not ALLOW_MANIPULATION else
    "Puedo intentar manipular objetos con el brazo."
)

SYSTEM_PROMPT = (
    "Eres un planificador de acciones para un robot móvil de servicio en simulación. "
    "Respondes ÚNICAMENTE con listas de acciones ejecutables, una por línea, sin explicaciones ni texto adicional. "
    "Termina siempre con END en la última línea.\n"
    "Lugares disponibles: refrigerator, kitchen, table, sofa, bed, tv, door, stove, home.\n"
    "Acciones disponibles:\n"
    "  NAVIGATE lugar  -> mueve el robot al lugar indicado\n"
    "  SPEAK texto     -> el robot dice el texto en voz alta\n"
    "  DETECT objeto   -> el robot busca el objeto con la camara\n"
    f"{_manip_line}"
    "  STOP            -> detiene el robot\n"
    "  END             -> fin del plan\n"
    "Reglas:\n"
    "1. Responde solo con acciones, una por linea, sin numeracion ni explicaciones.\n"
    "2. Termina siempre con END.\n"
    "3. Si la instruccion esta fuera de las capacidades, responde: SPEAK <razon breve> seguido de END.\n"
    "4. Si te preguntan que puedes hacer, responde con SPEAK describiendo tus capacidades, luego END.\n"
    "5. Para instrucciones compuestas, genera multiples NAVIGATE.\n"
    "6. Si el usuario niega una accion (no vayas, no hagas), responde: SPEAK Entendido, no realizare esa accion. END\n"
    "Ejemplos:\n"
    "Instruccion: ve al refri\n"
    "NAVIGATE refrigerator\n"
    "END\n"
    "Instruccion: robot vuela\n"
    "SPEAK No puedo volar.\n"
    "END\n"
    "Instruccion: dime que puedes hacer\n"
    f"SPEAK Puedo navegar a lugares, detectar objetos con la camara y hablar. {_manip_cap}\n"
    "END\n"
    "Instruccion: busca una bebida en la cocina\n"
    "NAVIGATE kitchen\n"
    "DETECT bebida\n"
    "END"
)


# ─────────────────────────────────────────────────────────────────────────────
# NODO PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────────
class SmPlannerNode(Node):

    # ── Constantes de clase ───────────────────────────────────────────────
    NOISE_FILTERS = [
        "amara", "subtítulos", "subtitulos", "transcripción",
        "transcripcion", "comunidad", "gracias por ver",
        "suscríbete", "suscribete", "like", "comparte",
    ]
    WAKE_WORDS   = ["oye robot", "hey robot", "hola robot", "robot"]
    CANCEL_WORDS = ["cancela", "cancel", "para todo", "aborta", "detén todo", "deten todo"]

    # Regex estricta para parsear líneas del plan (FIX #11)
    _PLAN_LINE_RE = re.compile(
        r"^(NAVIGATE|SPEAK|DETECT|MANIPULATE|PATROL|STOP|END)(?:\s+(.*))?$",
        re.IGNORECASE,
    )

    # ── __init__ ──────────────────────────────────────────────────────────
    def __init__(self):
        super().__init__("sm_planner_node")
        self.get_logger().info("INICIANDO SM PLANNER NODE — v14")

        # Estado de la máquina
        self.state            = SM_WAIT_FOR_COMMAND
        self.command          = ""
        self.new_command      = False
        self.plan             = []
        self.plan_index       = 0
        self.goal_reached     = False
        self.nav_timeout      = 0
        self.cancel_requested = False   # FIX #2: bandera global de cancelación

        # Ubicaciones (FIX #6: separar target de current)
        self.current_location = "home"
        self.target_location  = None

        # Memoria y detección
        self.yolo_detections    = []
        self.object_memory      = {}

        # Atributos dinámicos — inicializados aquí para evitar AttributeError (FIX #5)
        self._last_tts_time     = 0.0
        self._last_tts_duration = 0.0
        self._last_person_greet = 0.0
        self._fail_count        = 0

        # Historial Ollama — FIX #1: role='system'
        self.msg_history = [
            {"role": "system", "content": SYSTEM_PROMPT},
        ]

        # Publicadores
        self.pub_goal    = self.create_publisher(PoseStamped, "/goal_pose", 1)
        self.pub_tts     = self.create_publisher(String,      "/tts_query", 1)
        self.pub_cmd_vel = self.create_publisher(Twist,       "/cmd_vel",   1)
        self.pub_traj    = self.create_publisher(
            JointTrajectory, "/xarm6_traj_controller/joint_trajectory", 1
        )

        # Suscriptores
        self.create_subscription(String, "/sp_rec/recognized",       self._cb_recognized,   1)
        self.create_subscription(Bool,   "/navigation/goal_reached", self._cb_goal_reached, 1)
        self.create_subscription(String, "/yolo/detections",         self._cb_yolo,         1)

        # Log de actividad (FIX #2: try/except)
        log_path = os.path.expanduser("~/robot_activity_log.txt")
        try:
            self._log_file = open(log_path, "a")
            self._log_file.write(
                f"\n=== Sesion iniciada: {time.strftime('%Y-%m-%d %H:%M:%S')} ===\n"
            )
            self._log_file.flush()
            self.get_logger().info(f"Log de actividad en: {log_path}")
        except Exception as e:
            self._log_file = None
            self.get_logger().warn(f"No se pudo abrir log: {e}")

        self.get_logger().info("Esperando instruccion en /sp_rec/recognized ...")

    # ── Callbacks ─────────────────────────────────────────────────────────

    def _cb_recognized(self, msg):
        text = msg.data.strip().lower()
        if len(text) < 3:
            return

        # Filtrar ruido de Whisper
        if any(noise in text for noise in self.NOISE_FILTERS):
            self.get_logger().warn(f"Ruido filtrado: '{text}'")
            return

        # FIX #2: cancelación sin wake word requerida cuando robot está ocupado
        is_cancel_bare = any(cw in text for cw in self.CANCEL_WORDS)
        wake_detected  = any(ww in text[:40] for ww in self.WAKE_WORDS)

        if wake_detected:
            command_text = text
            for ww in sorted(self.WAKE_WORDS, key=len, reverse=True):
                if ww in command_text[:40]:
                    command_text = re.sub(
                        rf"^.*?{re.escape(ww)}\s*[,.]?\s*", "", command_text, count=1
                    ).strip()
                    break
            if any(cw in command_text for cw in self.CANCEL_WORDS):
                self._do_cancel()
                return

        if is_cancel_bare and self.state != SM_WAIT_FOR_COMMAND:
            # Cancelación sin wake word si el robot está ocupado
            self._do_cancel()
            return

        if self.state != SM_WAIT_FOR_COMMAND:
            return

        # Cooldown post-TTS
        elapsed  = time.time() - self._last_tts_time
        cooldown = max(self._last_tts_duration + 1.5, 3.0)
        if elapsed < cooldown:
            self.get_logger().warn(
                f"Cooldown TTS activo ({elapsed:.1f}s/{cooldown:.1f}s), ignorando: '{text}'"
            )
            return

        if not wake_detected:
            self.get_logger().info(f"Sin wake word, ignorando: '{text}'")
            return

        # Extraer instrucción (FIX #3+4: regex para quitar wake word)
        command = text
        for ww in sorted(self.WAKE_WORDS, key=len, reverse=True):
            if ww in command[:40]:
                command = re.sub(
                    rf"^.*?{re.escape(ww)}\s*[,.]?\s*", "", command, count=1
                ).strip()
                break

        if len(command) < 2:
            self._speak("Dime que quieres que haga.")
            return

        self.cancel_requested = False  # FIX #2: nueva instrucción limpia bandera
        self.command     = command
        self.new_command = True
        self._log(f"INSTRUCCION: {self.command}")
        self.get_logger().info(f"Wake word detectado. Instruccion: '{self.command}'")

    def _cb_goal_reached(self, msg):
        if msg.data:
            self.goal_reached = True
            self.get_logger().info("Meta alcanzada.")

    def _cb_yolo(self, msg):
        # FIX #5: validación estricta del JSON
        try:
            data = json.loads(msg.data)
        except json.JSONDecodeError as e:
            self.get_logger().warn(f"YOLO JSON inválido: {e}")
            self.yolo_detections = []
            return

        if not isinstance(data, list):
            self.get_logger().warn(f"YOLO: se esperaba lista, se recibió {type(data)}")
            self.yolo_detections = []
            return

        # Filtrar solo dicts válidos
        self.yolo_detections = [d for d in data if isinstance(d, dict)]

        if self.state == SM_WAIT_FOR_COMMAND:
            for det in self.yolo_detections:
                conf = det.get("conf", 0)
                try:
                    conf = float(conf)
                except (TypeError, ValueError):
                    continue
                if det.get("clase") == "person" and conf > 0.6:
                    now = time.time()
                    if now - self._last_person_greet > 30.0:
                        self._last_person_greet = now
                        self._speak(
                            "Hola, soy tu robot de servicio. "
                            "Puedo ayudarte si me dices: robot, seguido de tu instruccion."
                        )
                        break

    # ── Utilidades de bajo nivel ──────────────────────────────────────────

    def _publish_goal(self, location_key: str) -> bool:
        loc = LOCATIONS.get(location_key)
        if loc is None:
            self.get_logger().warn(f"Lugar desconocido: {location_key}")
            return False
        msg = PoseStamped()
        msg.header.frame_id    = "map"
        msg.header.stamp       = self.get_clock().now().to_msg()
        msg.pose.position.x    = loc["x"]
        msg.pose.position.y    = loc["y"]
        msg.pose.position.z    = 0.0
        msg.pose.orientation.w = loc["w"]
        self.pub_goal.publish(msg)
        self.get_logger().info(f"Meta publicada: {location_key} ({loc['x']}, {loc['y']})")
        self._log(f"NAVEGANDO A: {location_key}")
        return True

    def _speak(self, text: str):
        self._last_tts_time     = time.time()
        self._last_tts_duration = max(len(text) * 0.08, 2.0)
        self.pub_tts.publish(String(data=text))
        self.get_logger().info(f"TTS: {text}")
        self._log(f"ROBOT DIJO: {text}")

    def _sleep(self, seconds: float) -> bool:
        """Pausa cancelable. Retorna True si completó, False si fue interrumpida."""
        steps = int(seconds / 0.05)
        for _ in range(steps):
            if self.cancel_requested or not rclpy.ok():  # FIX #3
                return False
            rclpy.spin_once(self, timeout_sec=0)
            self.get_clock().sleep_for(Duration(seconds=0.05))
        return True

    def _log(self, event: str):
        # FIX #16: proteger si _log_file es None
        if not self._log_file:
            return
        try:
            ts = time.strftime("%H:%M:%S")
            self._log_file.write(f"[{ts}] {event}\n")
            self._log_file.flush()
        except Exception as e:
            self.get_logger().warn(f"No se pudo escribir log: {e}")

    def _do_cancel(self):
        """FIX #2: cancelación real y global."""
        self.get_logger().warn("[CANCEL] Cancelacion solicitada.")
        self.pub_cmd_vel.publish(Twist())
        self.cancel_requested = True
        self.plan             = []
        self.plan_index       = 0
        self.goal_reached     = False
        self.nav_timeout      = 0
        self.new_command      = False
        self.command          = ""
        self.target_location  = None
        self.state            = SM_WAIT_FOR_COMMAND
        self._speak("Tarea cancelada. Listo para nuevas instrucciones.")
        self.get_logger().info("[CANCEL] Sistema reseteado.")

    # ── Interpretación ────────────────────────────────────────────────────

    def _rule_based_interpret(self, cmd: str):
        # FIX #14: orden correcto de prioridades

        # 1. Consulta de memoria
        if any(p in cmd for p in ["donde esta", "donde está", "has visto", "viste"]):
            for obj, lugar in self.object_memory.items():
                if obj in cmd:
                    return [("SPEAK", f"La ultima vez vi {obj} en {lugar}."), ("END", "")]
            return [("SPEAK", "No recuerdo haber visto ese objeto."), ("END", "")]

        # 2. Imposibles
        for word, response in IMPOSSIBLE.items():
            if word in cmd:
                return [("SPEAK", response), ("END", "")]

        # 3. Cancel / stop
        if any(w in cmd for w in ["alto", "detente", "para", "stop"]):
            return [("STOP", ""), ("END", "")]

        # 4. Capacidades / estado
        if any(w in cmd for w in [
            "como estas", "cómo estás", "estado", "que puedes", "qué puedes",
            "capacidades", "que sabes", "qué sabes", "presentate", "preséntate"
        ]):
            return [("SPEAK", self._build_status_report()), ("END", "")]

        # 5. FIX #13: negaciones — detectar antes de extraer ubicaciones
        if any(neg in cmd for neg in NEGATIONS):
            return [("SPEAK", "Entendido, no realizare esa accion."), ("END", "")]

        # 6. Patrulla
        if any(w in cmd for w in ["patrulla", "patrol", "recorre", "inspecciona"]):
            return [("PATROL", ""), ("END", "")]

        # 7. Navegación por ubicaciones
        cmd_norm = _norm(cmd)
        words = (
            cmd_norm
            .replace(",", " ")
            .replace("y luego", " ")
            .replace("despues", " ")
            .replace("luego", " ")
            .split()
        )
        found_locations = []
        for w in words:
            key = SYNONYMS.get(w)
            if key and (not found_locations or found_locations[-1] != key):
                found_locations.append(key)
        if found_locations:
            plan = [("NAVIGATE", loc) for loc in found_locations]
            plan.append(("SPEAK", "Tarea terminada."))
            plan.append(("END", ""))
            return plan

        # 8. Fallback → Ollama
        return None

    def _ollama_interpret(self, cmd: str):
        # FIX #8: no agregar al historial si el POST falla
        # FIX #15: timeout reducido
        try:
            if len(self.msg_history) > 18:
                self.msg_history = self.msg_history[:1] + self.msg_history[-17:]
            self.msg_history.append({"role": "user", "content": cmd})
            resp = requests.post(
                OLLAMA_URL,
                json={
                    "model":    OLLAMA_MODEL,
                    "messages": self.msg_history,
                    "stream":   False,
                    "options":  {"num_ctx": 4096},
                },
                timeout=OLLAMA_TIMEOUT,
            )
            resp.raise_for_status()
            data  = resp.json()
            reply = data.get("message", {}).get("content", "").strip()
            if not reply:
                raise ValueError(f"Respuesta vacia de Ollama: {data}")
            self.msg_history.append({"role": "assistant", "content": reply})
            self.get_logger().info(f"Ollama respondio:\n{reply}")
            return self._parse_plan(reply)
        except Exception as e:
            # Remover mensaje del usuario para no corromper historial
            if self.msg_history and self.msg_history[-1].get("role") == "user":
                self.msg_history.pop()
            self.get_logger().warn(f"Ollama fallo: {e}")
            return None

    def _parse_plan(self, text: str):
        # FIX #11: regex estricta, límites de longitud, validación
        plan  = []
        lines = text.splitlines()
        for line in lines:
            line = line.strip()
            if not line:
                continue
            m = self._PLAN_LINE_RE.match(line)
            if not m:
                self.get_logger().warn(f"[PARSE] Linea invalida ignorada: '{line}'")
                continue
            action = m.group(1).upper()
            arg    = (m.group(2) or "").strip()

            if action == "NAVIGATE":
                if not arg:
                    continue
                # Buscar ubicación en las palabras del argumento
                loc = None
                for aw in _norm(arg).split():
                    candidate = SYNONYMS.get(aw, aw)
                    if candidate in LOCATIONS:
                        loc = candidate
                        break
                if loc:
                    plan.append(("NAVIGATE", loc))
                else:
                    plan.append(("SPEAK", f"No conozco el lugar {arg[:40]}."))

            elif action == "SPEAK":
                text_arg = arg[:MAX_SPEAK_CHARS] if arg else "Entendido."
                plan.append(("SPEAK", text_arg))

            elif action == "DETECT":
                det_arg = arg[:MAX_DETECT_CHARS] if arg else "objeto"
                plan.append(("DETECT", det_arg))

            elif action == "MANIPULATE":
                if not ALLOW_MANIPULATION:
                    plan.append(("SPEAK", "No puedo manipular objetos en modo seguro."))
                else:
                    plan.append(("MANIPULATE", arg[:MAX_DETECT_CHARS] if arg else "objeto"))

            elif action == "PATROL":
                plan.append(("PATROL", ""))

            elif action == "STOP":
                plan.append(("STOP", ""))

            elif action == "END":
                plan.append(("END", ""))
                break

            if len(plan) >= MAX_PLAN_STEPS:
                self.get_logger().warn("[PARSE] Limite de pasos alcanzado.")
                break

        # Asegurar que el plan termine en END
        if plan and plan[-1][0] != "END":
            plan.append(("END", ""))

        return plan if plan else None

    # ── Acciones ejecutables ──────────────────────────────────────────────

    def _detect_object(self, target: str):
        """Gira el robot buscando el objeto con YOLO. FIX #4: cancelable + try/finally."""
        self._speak(f"Buscando {target}.")
        self.get_logger().info(f"[DETECT] Buscando: {target}")

        YOLO_CLASSES = {
            "silla": "chair",   "chair": "chair",
            "sofa":  "couch",   "sillon": "couch",
            "cama":  "bed",     "bed": "bed",
            "tele":  "tv",      "television": "tv", "tv": "tv",
            "refrigerador": "refrigerator", "refri": "refrigerator",
            "refrigerator": "refrigerator",
            "persona": "person", "person": "person",
            "bebida": "bottle",  "bottle": "bottle",
            "vaso":  "cup",      "cup": "cup",
            "pelota": "sports ball",
        }
        yolo_class = YOLO_CLASSES.get(_norm(target), _norm(target))

        VEL_GIRO   = 0.3
        T_MAX      = (2 * 3.14159) / VEL_GIRO
        t_inicio   = time.time()
        encontrado = False
        cancelado  = False

        twist = Twist()
        twist.angular.z = VEL_GIRO

        try:
            while time.time() - t_inicio < T_MAX and rclpy.ok():
                # FIX #4: revisar cancelación dentro del bucle
                if self.cancel_requested:
                    cancelado = True
                    break
                for det in self.yolo_detections:
                    if not isinstance(det, dict):
                        continue
                    try:
                        conf = float(det.get("conf", 0))
                    except (TypeError, ValueError):
                        conf = 0.0
                    if det.get("clase") == yolo_class and conf > 0.4:
                        encontrado = True
                        break
                if encontrado:
                    break
                self.pub_cmd_vel.publish(twist)
                rclpy.spin_once(self, timeout_sec=0)
                self.get_clock().sleep_for(Duration(seconds=0.05))
        finally:
            # FIX #4: siempre detener el giro
            self.pub_cmd_vel.publish(Twist())

        if cancelado:
            self.get_logger().info("[DETECT] Cancelado.")
            return

        if encontrado:
            self.object_memory[yolo_class]   = self.current_location
            self.object_memory[_norm(target)] = self.current_location
            self.get_logger().info(f"[DETECT] '{target}' encontrado en {self.current_location}.")
            self._speak(f"Encontre {target} en {self.current_location}.")
        else:
            self.get_logger().warn(f"[DETECT] '{target}' no encontrado.")
            self._speak(f"No encontre {target}.")
        self._sleep(2.0)

    def _send_arm_trajectory(self, positions, duration_sec: int = 2) -> bool:
        """FIX #10: validación antes de publicar."""
        if not isinstance(positions, (list, tuple)):
            self.get_logger().error("[ARM] positions debe ser lista o tupla.")
            return False
        if len(positions) != 6:
            self.get_logger().error(f"[ARM] Se esperaban 6 joints, se recibieron {len(positions)}.")
            return False
        if not all(isinstance(v, (int, float)) for v in positions):
            self.get_logger().error("[ARM] Todos los valores de positions deben ser numéricos.")
            return False
        if duration_sec <= 0:
            self.get_logger().error(f"[ARM] duration_sec debe ser > 0, se recibió {duration_sec}.")
            return False

        msg = JointTrajectory()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.joint_names  = ["joint1", "joint2", "joint3", "joint4", "joint5", "joint6"]
        p = JointTrajectoryPoint()
        p.positions              = list(positions)
        p.time_from_start.sec    = int(duration_sec)   # FIX #11
        p.time_from_start.nanosec = 0
        msg.points.append(p)
        self.pub_traj.publish(msg)
        return True

    def _manipulate(self, target: str):
        """FIX #9: solo ejecuta si ALLOW_MANIPULATION=True."""
        if not ALLOW_MANIPULATION:
            self._speak("No puedo manipular objetos en modo seguro.")
            return

        self.get_logger().info(f"[MANIPULATE] Intentando: {target}")
        self._speak(f"Intentare manipular {target}.")
        if not self._sleep(2.0):
            return

        HOME  = [0.0,  0.0,  0.0, 0.0, 0.0, 0.0]
        REACH = [0.0, -0.5, -1.4, 0.0, 0.3, 0.0]
        GRASP = [0.0, -0.8, -1.2, 0.0, 0.6, 0.0]

        try:
            if self.cancel_requested: return
            self.get_logger().info("[MANIPULATE] Alcanzando...")
            if not self._send_arm_trajectory(REACH, 2): raise RuntimeError("Fallo REACH")
            if not self._sleep(3.0): return

            if self.cancel_requested: return
            self.get_logger().info("[MANIPULATE] Agarrando...")
            if not self._send_arm_trajectory(GRASP, 2): raise RuntimeError("Fallo GRASP")
            if not self._sleep(3.0): return

            if self.cancel_requested: return
            self.get_logger().info("[MANIPULATE] Regresando a HOME...")
            if not self._send_arm_trajectory(HOME, 2): raise RuntimeError("Fallo HOME")
            if not self._sleep(3.0): return

            self._speak("Manipulacion completada.")
        except Exception as e:
            self.get_logger().warn(f"[MANIPULATE] Error: {e}")
            self._send_arm_trajectory(HOME, 2)
            self._speak("No pude completar la manipulacion.")

    def _patrol(self):
        """FIX #8: patrulla con cancelación, target_location y manejo de fallos."""
        self.get_logger().info("[PATROL] Iniciando patrulla.")
        self._speak("Iniciando patrulla del departamento.")
        errores = 0

        for waypoint in PATROL_WAYPOINTS:
            if not rclpy.ok() or self.cancel_requested:
                break
            self.get_logger().info(f"[PATROL] Navegando a: {waypoint}")
            if not self._publish_goal(waypoint):
                errores += 1
                continue

            # FIX #6: usar target_location, no current_location
            self.target_location = waypoint
            self.goal_reached    = False
            self.nav_timeout     = 0

            while not self.goal_reached and self.nav_timeout < NAV_TIMEOUT_CYCLES and rclpy.ok():
                if self.cancel_requested:
                    self.pub_cmd_vel.publish(Twist())
                    self.get_logger().info("[PATROL] Cancelada.")
                    return
                rclpy.spin_once(self, timeout_sec=0)
                self.get_clock().sleep_for(Duration(seconds=0.05))
                self.nav_timeout += 1

            if self.goal_reached:
                # FIX #6: solo actualizar current_location al llegar
                self.current_location = self.target_location
            else:
                self.get_logger().warn(f"[PATROL] No se pudo llegar a {waypoint}.")
                errores += 1

            self.goal_reached    = False
            self.nav_timeout     = 0
            self.target_location = None

        self.pub_cmd_vel.publish(Twist())
        if errores == 0:
            self._speak("Patrulla completada. Todo en orden.")
        else:
            self._speak(f"Patrulla completada con {errores} destinos no alcanzados.")
        self.get_logger().info(f"[PATROL] Completada. Errores: {errores}")

    def _build_status_report(self) -> str:
        mem = self.object_memory
        loc = self.current_location.replace("_", " ")
        if mem:
            objetos  = ", ".join(f"{o} en {l}" for o, l in list(mem.items())[:3])
            mem_str  = f"Recuerdo haber visto: {objetos}."
        else:
            mem_str = "No recuerdo haber detectado objetos aun."
        manip_str = (
            "No puedo manipular objetos en modo seguro."
            if not ALLOW_MANIPULATION else
            "Puedo intentar manipular objetos con el brazo."
        )
        return (
            f"Estoy en {loc}. {mem_str} "
            f"Puedo navegar a lugares, detectar objetos con la camara y hablar. "
            f"{manip_str} No puedo volar ni teleportarme."
        )

    # ── Máquina de estados principal ──────────────────────────────────────

    def spin(self):
        while rclpy.ok():
            rclpy.spin_once(self, timeout_sec=0)
            self.get_clock().sleep_for(Duration(seconds=0.05))

            # ── WAIT_FOR_COMMAND ──
            if self.state == SM_WAIT_FOR_COMMAND:
                if self.new_command:
                    self.new_command      = False
                    self.cancel_requested = False
                    self.state = SM_INTERPRET_COMMAND

            # ── INTERPRET_COMMAND ──
            elif self.state == SM_INTERPRET_COMMAND:
                self.get_logger().info("Interpretando instruccion...")
                plan = self._rule_based_interpret(self.command)
                if plan is None:
                    self.get_logger().info("Consultando Ollama...")
                    plan = self._ollama_interpret(self.command)
                if plan is None:
                    self._fail_count += 1
                    if self._fail_count >= 3:
                        self._fail_count = 0
                        plan = [("SPEAK",
                            "No entiendo tus instrucciones. Puedes decirme: "
                            "robot ve al refri, robot busca una silla, "
                            "o robot dime que puedes hacer."),
                            ("END", "")]
                    else:
                        plan = [("SPEAK", "No entendi la instruccion."), ("END", "")]
                else:
                    self._fail_count = 0
                self.plan       = plan
                self.plan_index = 0
                self.get_logger().info(f"Plan: {self.plan}")
                self.state = SM_EXECUTE_PLAN

            # ── EXECUTE_PLAN ──
            elif self.state == SM_EXECUTE_PLAN:
                if self.cancel_requested:
                    self.state = SM_DONE
                    continue
                if self.plan_index >= len(self.plan):
                    self.state = SM_DONE
                    continue
                action, arg = self.plan[self.plan_index]
                self.plan_index += 1

                if action == "NAVIGATE":
                    if self._publish_goal(arg):
                        self.goal_reached    = False
                        self.nav_timeout     = 0
                        # FIX #6: target, NO current
                        self.target_location = arg
                        self.state = SM_WAIT_GOAL_REACHED
                    else:
                        self._speak(f"No conozco el lugar {arg}.")

                elif action == "SPEAK":
                    self._speak(arg)
                    self._sleep(3.0)

                elif action == "DETECT":
                    self._detect_object(arg)

                elif action == "MANIPULATE":
                    self._manipulate(arg)

                elif action == "PATROL":
                    self._patrol()

                elif action == "STOP":
                    self.pub_cmd_vel.publish(Twist())
                    self._speak("Deteniendome.")
                    self._sleep(1.0)

                elif action == "END":
                    self.state = SM_DONE

            # ── WAIT_GOAL_REACHED ──
            elif self.state == SM_WAIT_GOAL_REACHED:
                if self.cancel_requested:
                    self.state = SM_DONE
                    continue

                if self.goal_reached:
                    # FIX #6: actualizar current_location SOLO al llegar
                    if self.target_location:
                        self.current_location = self.target_location
                        self.target_location  = None
                    self.goal_reached = False
                    self.nav_timeout  = 0
                    dest = self.current_location.replace("_", " ")
                    self._speak(f"Llegue a {dest}.")
                    self._sleep(2.0)
                    self.state = SM_EXECUTE_PLAN
                else:
                    self.nav_timeout += 1
                    # FIX #7: timeout aborta el plan completo
                    if self.nav_timeout > NAV_TIMEOUT_CYCLES:
                        dest = (self.target_location or "destino").replace("_", " ")
                        self.get_logger().warn(f"Timeout de navegacion hacia {dest}.")
                        self._speak(f"No pude llegar a {dest}. Abortare la tarea.")
                        self.plan            = []
                        self.plan_index      = 0
                        self.target_location = None
                        self.goal_reached    = False
                        self.nav_timeout     = 0
                        self.state = SM_DONE

            # ── DONE ──
            elif self.state == SM_DONE:
                self.get_logger().info("Plan completado. Esperando nueva instruccion.")
                self.plan            = []
                self.plan_index      = 0
                self.cancel_requested = False
                self.state = SM_WAIT_FOR_COMMAND


# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────
def main(args=None):
    rclpy.init(args=args)
    node = SmPlannerNode()
    try:
        node.spin()
    finally:
        # FIX #17: detener robot al salir
        try:
            node.pub_cmd_vel.publish(Twist())
        except Exception:
            pass
        # FIX #12: cerrar log
        if hasattr(node, "_log_file") and node._log_file:
            try:
                node._log_file.write(
                    f"[{time.strftime('%H:%M:%S')}] === Sesion terminada ===\n"
                )
                node._log_file.close()
            except Exception:
                pass
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
