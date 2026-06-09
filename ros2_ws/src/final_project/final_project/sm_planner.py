# sm_planner.py — Robot de Propósito General
# Materia: Robots Móviles, FI-UNAM 2026-2
# Autor: Zambrano Miranda Isaac Jaciel
# Versión: ULTIMATE — final demo académica robusta
#
# ESTADO: Versión final para demo académica robusta. NO producción real.
# Producción requiere NavigateToPose ActionClient con cancel_goal_async()
# y confirmación de llegada por goal_id real, no por Bool genérico.

import re
import os
import json
import math
import time
import threading
import unicodedata as _UD

import rclpy
from rclpy.node import Node
from rclpy.duration import Duration
from std_msgs.msg import String, Bool
from geometry_msgs.msg import PoseStamped, Twist
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
import requests

# ─────────────────────────────────────────────────────────────────────────────
# ESTADOS
# ─────────────────────────────────────────────────────────────────────────────
SM_WAIT_FOR_COMMAND  = 0
SM_INTERPRET_COMMAND = 10
SM_WAIT_OLLAMA       = 15
SM_EXECUTE_PLAN      = 20
SM_WAIT_GOAL_REACHED = 40
SM_DONE              = 80

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURACIÓN
# ─────────────────────────────────────────────────────────────────────────────
ALLOW_MANIPULATION = False
NAV_TIMEOUT_CYCLES = 2400    # 120 s
MAX_PLAN_STEPS     = 10
MAX_SPEAK_CHARS    = 250
MAX_DETECT_CHARS   = 50
OLLAMA_URL         = "http://localhost:11434/api/chat"
OLLAMA_MODEL       = "llama3.2:3b"
OLLAMA_TIMEOUT     = 10

# ─────────────────────────────────────────────────────────────────────────────
# ENTORNO
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
    "vuela":      "No puedo volar.",
    "volar":      "No puedo volar.",
    "teleporta":  "No puedo teleportarme.",
    "desaparece": "No puedo desaparecer.",
}

NEGATIONS = [
    "no vayas", "no navegues", "no te muevas",
    "no quiero que vayas", "no vayas a", "no ir",
]

SEARCH_KEYWORDS = {
    "busca", "buscar", "detecta", "detectar", "encuentra",
    "encontrar", "identifica", "identificar", "localiza", "localizar",
}

PATROL_WAYPOINTS = ["sofa", "tv", "table", "refrigerator", "kitchen", "bed", "home"]

# ─────────────────────────────────────────────────────────────────────────────
# SYSTEM PROMPT
# ─────────────────────────────────────────────────────────────────────────────
_manip_line = (
    "  MANIPULATE objeto  -> deshabilitado en modo seguro\n"
    if not ALLOW_MANIPULATION else
    "  MANIPULATE objeto  -> intenta manipular con el brazo\n"
)
_manip_cap = (
    "No puedo manipular objetos en modo seguro."
    if not ALLOW_MANIPULATION else
    "Puedo intentar manipular objetos con el brazo."
)

SYSTEM_PROMPT = (
    "Eres un planificador de acciones para un robot móvil de servicio en simulación. "
    "Respondes ÚNICAMENTE con listas de acciones ejecutables, una por línea, "
    "sin texto libre, sin explicaciones, sin markdown. "
    "Termina siempre con END.\n"
    "Lugares: refrigerator, kitchen, table, sofa, bed, tv, door, stove, home.\n"
    "Acciones:\n"
    "  NAVIGATE lugar\n"
    "  SPEAK texto\n"
    "  DETECT objeto\n"
    f"{_manip_line}"
    "  STOP\n"
    "  END\n"
    "Reglas: sin numeracion, sin markdown, sin texto libre. "
    "Instrucciones imposibles: SPEAK razon END. "
    "Negaciones: SPEAK Entendido END.\n"
    "Ejemplo:\n"
    "Instruccion: ve al refri\n"
    "NAVIGATE refrigerator\n"
    "END\n"
    "Instruccion: busca una silla\n"
    "DETECT silla\n"
    "END"
)


# ─────────────────────────────────────────────────────────────────────────────
# NODO
# ─────────────────────────────────────────────────────────────────────────────
class SmPlannerNode(Node):

    NOISE_FILTERS = [
        "amara", "subtitulos", "transcripcion", "comunidad",
        "gracias por ver", "suscribete", "like", "comparte",
    ]

    WAKE_RE = re.compile(
        r"\b(oye\s+robot|hey\s+robot|hola\s+robot|robot)\b",
        re.IGNORECASE,
    )

    _PLAN_LINE_RE = re.compile(
        r"^(NAVIGATE|SPEAK|DETECT|MANIPULATE|PATROL|STOP|END)(?:\s+(.*))?$",
        re.IGNORECASE,
    )

    _MARKDOWN_RE = re.compile(r"^```")

    _YOLO_CLASSES = {
        "silla": "chair",       "chair": "chair",
        "sofa":  "couch",       "sillon": "couch",
        "cama":  "bed",         "bed": "bed",
        "tele":  "tv",          "television": "tv",      "tv": "tv",
        "refrigerador": "refrigerator", "refri": "refrigerator",
        "refrigerator": "refrigerator",
        "persona": "person",    "person": "person",
        "bebida":  "bottle",    "botella": "bottle",     "bottle": "bottle",
        "vaso":    "cup",       "cup": "cup",
        "pelota":  "sports ball",
    }

    def __init__(self):
        super().__init__("sm_planner_node")
        self.get_logger().info("INICIANDO SM PLANNER NODE — ULTIMATE")

        self.state            = SM_WAIT_FOR_COMMAND
        self.command          = ""
        self.new_command      = False
        self.plan             = []
        self.plan_index       = 0
        self.goal_reached     = False
        self.nav_timeout      = 0
        self.cancel_requested = False

        self.current_location = "home"
        self.target_location  = None

        self.yolo_detections    = []
        self.object_memory      = {}

        self._last_tts_time     = 0.0
        self._last_tts_duration = 0.0
        self._last_person_greet = 0.0
        self._fail_count        = 0

        # FIX #2: lock y request_id para Ollama thread-safe
        self._ollama_lock       = threading.Lock()
        self._ollama_request_id = 0
        self._ollama_result     = None
        self._ollama_thread     = None

        # FIX #4: protección contra goal_reached demasiado rápido
        self._goal_sent_time         = 0.0
        self._min_goal_reached_delay = 0.5

        self.msg_history = [{"role": "system", "content": SYSTEM_PROMPT}]

        self.pub_goal    = self.create_publisher(PoseStamped, "/goal_pose", 1)
        self.pub_tts     = self.create_publisher(String,      "/tts_query", 1)
        self.pub_cmd_vel = self.create_publisher(Twist,       "/cmd_vel",   1)
        self.pub_traj    = self.create_publisher(
            JointTrajectory, "/xarm6_traj_controller/joint_trajectory", 1)

        self.create_subscription(
            String, "/sp_rec/recognized",       self._cb_recognized,   1)
        self.create_subscription(
            Bool,   "/navigation/goal_reached", self._cb_goal_reached, 1)
        self.create_subscription(
            String, "/yolo/detections",         self._cb_yolo,         1)

        log_path = os.path.expanduser("~/robot_activity_log.txt")
        try:
            self._log_file = open(log_path, "a")
            self._log_file.write(
                f"\n=== Sesion iniciada: {time.strftime('%Y-%m-%d %H:%M:%S')} ===\n"
            )
            self._log_file.flush()
            self.get_logger().info(f"Log: {log_path}")
        except Exception as e:
            self._log_file = None
            self.get_logger().warn(f"No se pudo abrir log: {e}")

        self.get_logger().info("Esperando instruccion...")

    # ── Callbacks ─────────────────────────────────────────────────────────

    def _cb_recognized(self, msg):
        text = msg.data.strip().lower()
        if len(text) < 3:
            return

        # 1. Emergency stop — siempre primero, antes de cualquier filtro
        if self._contains_emergency_stop(text):
            if self.state != SM_WAIT_FOR_COMMAND:
                self._do_cancel()
                return

        # 2. FIX #2: detectar wake word ANTES del filtro de ruido
        wake_match    = self.WAKE_RE.search(text[:40])
        wake_detected = bool(wake_match)

        # 3. Filtrar ruido — pero NO si hay wake word clara (Whisper puede agregar ruido al final)
        text_norm = _norm(text)
        if any(n in text_norm for n in self.NOISE_FILTERS) and not wake_detected:
            return

        # 4. Si hay wake word, verificar emergency stop en el comando extraído
        if wake_detected:
            command_text = text[wake_match.end():].strip(" ,.:;")
            if self._contains_emergency_stop(command_text):
                if self.state != SM_WAIT_FOR_COMMAND:
                    self._do_cancel()
                    return

        if self.state != SM_WAIT_FOR_COMMAND:
            return

        # FIX #2 v16: cooldown solo sin wake word
        elapsed  = time.time() - self._last_tts_time
        cooldown = max(self._last_tts_duration + 1.5, 3.0)
        if elapsed < cooldown and not wake_detected:
            self.get_logger().warn(
                f"Cooldown TTS ({elapsed:.1f}s/{cooldown:.1f}s), ignorando sin wake word"
            )
            return

        if not wake_detected:
            return

        command = text[wake_match.end():].strip(" ,.:;")
        command = self._strip_noise_phrases(command)  # FIX #2: limpiar ruido del final
        if len(command) < 2:
            self._speak("Dime que quieres que haga.")
            return

        self.cancel_requested = False
        self.command     = command
        self.new_command = True
        self._log(f"INSTRUCCION: {self.command}")
        self.get_logger().info(f"Instruccion: '{self.command}'")

    def _cb_goal_reached(self, msg):
        # TODO PRODUCCION: Bool sin goal_id. No garantiza correspondencia con
        # target_location actual. Migrar a NavigateToPose ActionClient.
        if msg.data:
            # FIX #4: ignorar si llegó demasiado rápido (falso positivo)
            if time.time() - self._goal_sent_time < self._min_goal_reached_delay:
                self.get_logger().warn("goal_reached ignorado: llego demasiado pronto.")
                return
            self.goal_reached = True

    def _cb_yolo(self, msg):
        try:
            data = json.loads(msg.data)
        except json.JSONDecodeError as e:
            self.get_logger().warn(f"YOLO JSON invalido: {e}")
            self.yolo_detections = []
            return
        if not isinstance(data, list):
            self.yolo_detections = []
            return
        self.yolo_detections = [d for d in data if isinstance(d, dict)]

        if self.state == SM_WAIT_FOR_COMMAND:
            for det in self.yolo_detections:
                try:
                    conf = float(det.get("conf", 0))
                except (TypeError, ValueError):
                    conf = 0.0
                if self._norm_yolo_label(det.get("clase", "")) == "person" and conf > 0.6:
                    now = time.time()
                    if now - self._last_person_greet > 30.0:
                        self._last_person_greet = now
                        self._speak(
                            "Hola, soy tu robot de servicio. "
                            "Dime: robot, seguido de tu instruccion."
                        )
                        break

    # ── Helpers ───────────────────────────────────────────────────────────

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
        # FIX #4: registrar tiempo de envío
        self._goal_sent_time = time.time()
        self._log(f"NAVEGANDO A: {location_key}")
        return True

    def _speak(self, text: str):
        if text is None:
            text = ""
        text = str(text).strip()
        if len(text) > MAX_SPEAK_CHARS:
            text = text[:MAX_SPEAK_CHARS] + "..."
        self._last_tts_time     = time.time()
        self._last_tts_duration = max(len(text) * 0.08, 2.0)
        self.pub_tts.publish(String(data=text))
        self.get_logger().info(f"TTS: {text}")
        self._log(f"ROBOT DIJO: {text}")

    def _sleep(self, seconds: float) -> bool:
        steps = int(seconds / 0.05)
        for _ in range(steps):
            if self.cancel_requested or not rclpy.ok():
                return False
            rclpy.spin_once(self, timeout_sec=0)
            self.get_clock().sleep_for(Duration(seconds=0.05))
        return True

    def _log(self, event: str):
        if not self._log_file:
            return
        try:
            self._log_file.write(f"[{time.strftime('%H:%M:%S')}] {event}\n")
            self._log_file.flush()
        except Exception as e:
            self.get_logger().warn(f"Log error: {e}")

    def _do_cancel(self):
        # TODO PRODUCCION: publicar Twist() es respaldo local.
        # Cancelación formal requiere ActionClient con cancel_goal_async().
        self.get_logger().warn("[CANCEL] Cancelacion.")
        self.pub_cmd_vel.publish(Twist())
        # FIX #2: invalidar thread de Ollama con lock
        with self._ollama_lock:
            self._ollama_request_id += 1
            self._ollama_result = False
        self.cancel_requested  = True
        self.plan              = []
        self.plan_index        = 0
        self.goal_reached      = False
        self.nav_timeout       = 0
        self.new_command       = False
        self.command           = ""
        self.target_location   = None
        self.state             = SM_WAIT_FOR_COMMAND
        self._speak("Tarea cancelada. Listo.")

    def _strip_noise_phrases(self, text: str) -> str:
        """Elimina frases de ruido de Whisper cuando aparecen como cola del comando.
        Solo corta si el ruido aparece después de contenido útil, para no mutilar
        comandos que contengan coincidencias de palabras de ruido de forma legítima.
        """
        raw  = text.strip(" ,.:;")
        norm = _norm(raw)
        for noise in self.NOISE_FILTERS:
            idx = norm.find(noise)
            if idx == -1:
                continue
            prefix = raw[:idx].strip(" ,.:;")
            suffix = norm[idx:].strip(" ,.:;")
            # Solo cortar si hay prefijo útil y el ruido aparece como cola
            if prefix and suffix.startswith(noise):
                return prefix
        return raw

    # FIX #1 v17 + FIX #5: emergency stop unificado con variantes naturales
    def _contains_emergency_stop(self, text: str) -> bool:
        t = _norm(text)
        # FIX #6: negaciones ampliadas
        _negative_patterns = [
            r"\bno\s+(canceles?|cancelar|abortes?)\b",
            r"\bno\s+te\s+detengas\b",
            r"\bno\s+te\s+pares\b",
            r"\bno\s+pares\b",
            r"\bno\s+pares\s+el\s+robot\b",
            r"\bno\s+lo\s+detengas\b",
            r"\bno\s+detengas\s+el\s+robot\b",
            r"\bno\s+quiero\s+que\s+te\s+detengas\b",
        ]
        if any(re.search(p, t) for p in _negative_patterns):
            return False
        patterns = [
            r"\bcancela\b",
            r"\bcancel\b",
            r"\baborta\b",
            r"\bdetente\b",
            r"\balto\b",
            r"\bstop\b",
            r"\bparate\b",        # FIX #5
            r"\bpara\s+todo\b",
            r"\bpara\s+ya\b",     # FIX #5
            r"\bdetente\s+ya\b",  # FIX #5
            r"\bdeten\s+todo\b",
        ]
        return any(re.search(p, t) for p in patterns)

    def _norm_yolo_label(self, label: str) -> str:
        return _norm(str(label)).strip().replace("_", " ")

    def _map_yolo_class(self, target: str) -> str:
        words = re.findall(r"\b\w+\b", _norm(target))
        for word in words:
            if word in self._YOLO_CLASSES:
                return self._YOLO_CLASSES[word]
        return _norm(target)

    # FIX #3: helper estructural para encontrar primera ubicación
    def _find_first_location(self, words):
        for w in words:
            candidate = SYNONYMS.get(w)
            if candidate:
                return candidate
        return None

    # FIX #3: extracción estructural de plan de búsqueda
    def _extract_search_plan(self, cmd_norm: str):
        words = re.findall(r"\b\w+\b", cmd_norm)

        # Encontrar índice de la primera palabra de búsqueda
        search_idx = None
        for i, w in enumerate(words):
            if w in SEARCH_KEYWORDS:
                search_idx = i
                break

        if search_idx is None:
            return None

        before_search = words[:search_idx]
        after_search  = words[search_idx + 1:]

        loc          = None
        target_words = after_search

        # Caso: "busca una bebida en la cocina"
        if "en" in after_search:
            en_idx       = after_search.index("en")
            target_words = after_search[:en_idx]
            loc_words    = after_search[en_idx + 1:]
            loc          = self._find_first_location(loc_words)
            # FIX #2: lugar especificado pero desconocido → abortar con aviso
            if loc is None and loc_words:
                # FIX #3: limpiar artículos y stopwords para mensaje más limpio
                _loc_stopwords = {
                    "el", "la", "los", "las", "un", "una", "al", "a",
                    "por", "favor", "porfavor", "me",
                }
                clean_lw = [w for w in loc_words if w not in _loc_stopwords]
                unknown_loc = " ".join(clean_lw[:3]) if clean_lw else " ".join(loc_words[:3])
                return [("SPEAK", f"No conozco el lugar {unknown_loc}."), ("END", "")]

        # Caso: "ve al refri y busca una botella"
        if loc is None:
            move_words = {"ve", "ir", "vete", "navega", "muevete", "mueve"}
            if any(w in move_words for w in before_search):
                loc = self._find_first_location(before_search)

        _obj_stopwords = {
            "una", "un", "el", "la", "los", "las",
            "al", "a", "por", "favor", "me", "si",
            "hay", "que", "y", "luego", "despues",
        }

        obj_words = [
            w for w in target_words
            if w not in _obj_stopwords and w not in SEARCH_KEYWORDS
        ]
        obj = " ".join(obj_words).strip() if obj_words else "objeto"

        if loc:
            return [("NAVIGATE", loc), ("DETECT", obj), ("END", "")]
        return [("DETECT", obj), ("END", "")]

    # ── Interpretación ────────────────────────────────────────────────────

    def _rule_based_interpret(self, cmd: str):
        cmd_norm = _norm(cmd)
        tokens   = set(re.findall(r"\b\w+\b", cmd_norm))

        # 1. Memoria
        if any(p in cmd_norm for p in ["donde esta", "has visto", "viste"]):
            for obj, lugar in self.object_memory.items():
                if obj in cmd_norm:
                    return [("SPEAK", f"La ultima vez vi {obj} en {lugar}."), ("END", "")]
            return [("SPEAK", "No recuerdo haber visto ese objeto."), ("END", "")]

        # 2. Imposibles
        for word, response in IMPOSSIBLE.items():
            if word in cmd_norm:
                return [("SPEAK", response), ("END", "")]

        # 3. Emergency stop
        if tokens & {"alto", "detente", "stop", "parate"}:
            return [("STOP", ""), ("END", "")]
        if re.search(r"\bpara\s+todo\b", cmd_norm):
            return [("STOP", ""), ("END", "")]
        if re.search(r"\bpara\s+ya\b", cmd_norm):
            return [("STOP", ""), ("END", "")]
        if re.search(r"\bdetente\s+ya\b", cmd_norm):
            return [("STOP", ""), ("END", "")]
        if re.search(r"\bdeten\s+todo\b", cmd_norm):
            return [("STOP", ""), ("END", "")]

        # 4. Capacidades / estado
        if any(w in cmd_norm for w in [
            "como estas", "estado", "que puedes", "capacidades",
            "que sabes", "presentate",
        ]):
            return [("SPEAK", self._build_status_report()), ("END", "")]

        # 5. Negaciones
        if any(neg in cmd_norm for neg in NEGATIONS):
            return [("SPEAK", "Entendido, no realizare esa accion."), ("END", "")]

        # 6. FIX #3: búsqueda compuesta estructural
        if bool(tokens & SEARCH_KEYWORDS):
            return self._extract_search_plan(cmd_norm)

        # 7. Patrulla
        if any(w in cmd_norm for w in ["patrulla", "patrol", "recorre", "inspecciona"]):
            return [("PATROL", ""), ("END", "")]

        # 8. Navegación pura
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

        return None

    # FIX #2: Ollama en thread con request_id
    def _ollama_call_thread(self, cmd: str, request_id: int):
        # FIX #1: snapshot del historial bajo lock — ningún thread viejo altera msg_history
        with self._ollama_lock:
            if request_id != self._ollama_request_id:
                return
            history_snapshot = list(self.msg_history)

        if len(history_snapshot) > 18:
            history_snapshot = history_snapshot[:1] + history_snapshot[-17:]
        messages = history_snapshot + [{"role": "user", "content": cmd}]

        try:
            resp = requests.post(
                OLLAMA_URL,
                json={
                    "model":    OLLAMA_MODEL,
                    "messages": messages,
                    "stream":   False,
                    "options":  {"num_ctx": 4096},
                },
                timeout=OLLAMA_TIMEOUT,
            )
            resp.raise_for_status()
            data  = resp.json()
            reply = data.get("message", {}).get("content", "").strip()
            if not reply:
                raise ValueError(f"Respuesta vacia: {data}")
            self.get_logger().info(f"Ollama:\n{reply}")
            result = self._parse_plan(reply)
            # Commitear historial y resultado solo si request_id sigue vigente
            with self._ollama_lock:
                if request_id != self._ollama_request_id:
                    return
                self.msg_history    = messages + [{"role": "assistant", "content": reply}]
                self._ollama_result = result if result else False
        except Exception as e:
            self.get_logger().warn(f"Ollama fallo: {e}")
            # No tocar msg_history — solo marcar fallo si sigue siendo vigente
            with self._ollama_lock:
                if request_id == self._ollama_request_id:
                    self._ollama_result = False

    def _parse_plan(self, text: str):
        plan = []
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            if self._MARKDOWN_RE.match(line):
                self.get_logger().warn("[PARSE] Markdown, abortando plan.")
                return [("SPEAK", "Plan invalido recibido. Abortare la tarea."), ("END", "")]
            m = self._PLAN_LINE_RE.match(line)
            if not m:
                self.get_logger().warn(f"[PARSE] Linea invalida: '{line}'")
                return [("SPEAK", "Plan invalido recibido. Abortare la tarea."), ("END", "")]

            action = m.group(1).upper()
            arg    = (m.group(2) or "").strip()

            if action == "NAVIGATE":
                if not arg:
                    plan.append(("SPEAK", "NAVIGATE sin destino."))
                    plan.append(("END", ""))
                    break
                loc = None
                for aw in _norm(arg).split():
                    c = SYNONYMS.get(aw, aw)
                    if c in LOCATIONS:
                        loc = c
                        break
                if loc:
                    plan.append(("NAVIGATE", loc))
                else:
                    plan.append(("SPEAK", f"No conozco el lugar {arg[:40]}."))
                    plan.append(("END", ""))
                    break

            elif action == "SPEAK":
                plan.append(("SPEAK", arg[:MAX_SPEAK_CHARS] if arg else "Entendido."))

            elif action == "DETECT":
                plan.append(("DETECT", arg[:MAX_DETECT_CHARS] if arg else "objeto"))

            elif action == "MANIPULATE":
                if not ALLOW_MANIPULATION:
                    plan.append(("SPEAK", "No puedo manipular objetos en modo seguro."))
                    plan.append(("END", ""))
                    break
                plan.append(("MANIPULATE", arg[:MAX_DETECT_CHARS] if arg else "objeto"))

            elif action == "PATROL":
                # FIX #4: PATROL no debe traer argumentos
                if arg:
                    return [("SPEAK", "Plan invalido recibido. Abortare la tarea."), ("END", "")]
                plan.append(("PATROL", ""))

            elif action == "STOP":
                # FIX #4: STOP no debe traer argumentos
                if arg:
                    return [("SPEAK", "Plan invalido recibido. Abortare la tarea."), ("END", "")]
                plan.append(("STOP", ""))
                plan.append(("END", ""))
                break

            elif action == "END":
                # FIX #4: END no debe traer argumentos
                if arg:
                    return [("SPEAK", "Plan invalido recibido. Abortare la tarea."), ("END", "")]
                plan.append(("END", ""))
                break

            if len(plan) >= MAX_PLAN_STEPS:
                self.get_logger().warn("[PARSE] Limite alcanzado.")
                if not plan or plan[-1][0] != "END":
                    plan.append(("END", ""))
                break

        if plan and plan[-1][0] != "END":
            plan.append(("END", ""))

        return plan if plan else None

    # ── Acciones ──────────────────────────────────────────────────────────

    def _detect_object(self, target: str):
        self._speak(f"Buscando {target}.")
        yolo_class = self._norm_yolo_label(self._map_yolo_class(target))

        VEL_GIRO   = 0.3
        T_MAX      = (2 * 3.14159) / VEL_GIRO
        t_inicio   = time.time()
        encontrado = False
        cancelado  = False

        twist = Twist()
        twist.angular.z = VEL_GIRO
        try:
            while time.time() - t_inicio < T_MAX and rclpy.ok():
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
                    if self._norm_yolo_label(det.get("clase", "")) == yolo_class and conf > 0.4:
                        encontrado = True
                        break
                if encontrado:
                    break
                self.pub_cmd_vel.publish(twist)
                rclpy.spin_once(self, timeout_sec=0)
                self.get_clock().sleep_for(Duration(seconds=0.05))
        finally:
            self.pub_cmd_vel.publish(Twist())

        if cancelado:
            return
        if encontrado:
            self.object_memory[yolo_class]    = self.current_location
            self.object_memory[_norm(target)] = self.current_location
            self._speak(f"Encontre {target} en {self.current_location}.")
        else:
            self._speak(f"No encontre {target}.")
        self._sleep(2.0)

    def _send_arm_trajectory(self, positions, duration_sec=2) -> bool:
        if not isinstance(positions, (list, tuple)):
            self.get_logger().error("[ARM] positions debe ser lista.")
            return False
        if len(positions) != 6:
            self.get_logger().error("[ARM] Se esperaban 6 joints.")
            return False
        for v in positions:
            if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v):
                self.get_logger().error(f"[ARM] Valor invalido: {v}")
                return False
        if (isinstance(duration_sec, bool) or
                not isinstance(duration_sec, (int, float)) or
                not math.isfinite(duration_sec) or
                duration_sec < 1.0):   # FIX #6: mínimo 1.0 s
            self.get_logger().error(f"[ARM] duration_sec invalido o < 1.0: {duration_sec}")
            return False
        msg = JointTrajectory()
        msg.header.stamp  = self.get_clock().now().to_msg()
        msg.joint_names   = ["joint1","joint2","joint3","joint4","joint5","joint6"]
        p = JointTrajectoryPoint()
        p.positions              = list(positions)
        sec    = int(duration_sec)
        nanosec = int(round((duration_sec - sec) * 1e9))
        nanosec = max(0, min(nanosec, 999_999_999))  # FIX #7: clamp
        p.time_from_start.sec    = sec
        p.time_from_start.nanosec = nanosec
        msg.points.append(p)
        self.pub_traj.publish(msg)
        return True

    def _manipulate(self, target: str):
        if not ALLOW_MANIPULATION:
            self._speak("No puedo manipular objetos en modo seguro.")
            return
        self._speak(f"Intentare manipular {target}.")
        if not self._sleep(2.0): return
        HOME  = [0.0,  0.0,  0.0, 0.0, 0.0, 0.0]
        REACH = [0.0, -0.5, -1.4, 0.0, 0.3, 0.0]
        GRASP = [0.0, -0.8, -1.2, 0.0, 0.6, 0.0]
        try:
            if self.cancel_requested: return
            if not self._send_arm_trajectory(REACH, 2): raise RuntimeError("REACH")
            if not self._sleep(3.0): return
            if self.cancel_requested: return
            if not self._send_arm_trajectory(GRASP, 2): raise RuntimeError("GRASP")
            if not self._sleep(3.0): return
            if self.cancel_requested: return
            if not self._send_arm_trajectory(HOME, 2):  raise RuntimeError("HOME")
            if not self._sleep(3.0): return
            self._speak("Manipulacion completada.")
        except Exception as e:
            self.get_logger().warn(f"[MANIPULATE] {e}")
            self._send_arm_trajectory(HOME, 2)
            self._speak("No pude completar la manipulacion.")

    def _patrol(self):
        self._speak("Iniciando patrulla.")
        cancelado = False
        visitados = 0
        errores   = 0

        for waypoint in PATROL_WAYPOINTS:
            if not rclpy.ok() or self.cancel_requested:
                cancelado = True
                break
            if not self._publish_goal(waypoint):
                self.get_logger().warn(f"[PATROL] Fallo publicar {waypoint}. Abortando.")
                errores += 1
                break

            self.target_location = waypoint
            self.goal_reached    = False
            self.nav_timeout     = 0

            while not self.goal_reached and self.nav_timeout < NAV_TIMEOUT_CYCLES and rclpy.ok():
                if self.cancel_requested:
                    cancelado = True
                    break
                rclpy.spin_once(self, timeout_sec=0)
                self.get_clock().sleep_for(Duration(seconds=0.05))
                self.nav_timeout += 1

            if cancelado:
                break

            if self.goal_reached:
                self.current_location = self.target_location
                visitados += 1
            else:
                self.get_logger().warn(f"[PATROL] Timeout en {waypoint}. Abortando.")
                errores += 1
                break

            self.goal_reached    = False
            self.nav_timeout     = 0
            self.target_location = None

        self.pub_cmd_vel.publish(Twist())
        self.target_location = None

        if cancelado:
            self._speak("Patrulla cancelada.")
        elif errores > 0:
            self._speak(f"Patrulla incompleta. Visite {visitados} puntos.")
        else:
            self._speak("Patrulla completada. Todo en orden.")

    def _build_status_report(self) -> str:
        mem = self.object_memory
        loc = self.current_location.replace("_", " ")
        mem_str = (
            "Recuerdo: " + ", ".join(f"{o} en {l}" for o, l in list(mem.items())[:3]) + "."
            if mem else "No recuerdo objetos detectados."
        )
        return (
            f"Estoy en {loc}. {mem_str} "
            f"Puedo navegar, detectar objetos y hablar. "
            f"{_manip_cap} No puedo volar."
        )

    # ── Máquina de estados ────────────────────────────────────────────────

    def spin(self):
        while rclpy.ok():
            rclpy.spin_once(self, timeout_sec=0)
            self.get_clock().sleep_for(Duration(seconds=0.05))

            if self.state == SM_WAIT_FOR_COMMAND:
                if self.new_command:
                    self.new_command      = False
                    self.cancel_requested = False
                    self.state = SM_INTERPRET_COMMAND

            elif self.state == SM_INTERPRET_COMMAND:
                plan = self._rule_based_interpret(self.command)
                if plan is not None:
                    self._fail_count = 0
                    self.plan        = plan
                    self.plan_index  = 0
                    self.get_logger().info(f"Plan (reglas): {self.plan}")
                    self.state = SM_EXECUTE_PLAN
                else:
                    self.get_logger().info("Consultando Ollama (thread)...")
                    # FIX #2: incrementar request_id con lock
                    with self._ollama_lock:
                        self._ollama_request_id += 1
                        request_id           = self._ollama_request_id
                        self._ollama_result  = None
                    self._ollama_thread = threading.Thread(
                        target=self._ollama_call_thread,
                        args=(self.command, request_id),
                        daemon=True,
                    )
                    self._ollama_thread.start()
                    self.state = SM_WAIT_OLLAMA

            elif self.state == SM_WAIT_OLLAMA:
                if self.cancel_requested:
                    self.state = SM_DONE
                    continue
                # FIX #4: leer y consumir en un solo lock
                with self._ollama_lock:
                    result = self._ollama_result
                    if result is None:
                        continue
                    self._ollama_result = None
                plan = result if isinstance(result, list) else None
                if plan is None:
                    self._fail_count += 1
                    if self._fail_count >= 3:
                        self._fail_count = 0
                        plan = [("SPEAK",
                            "No entiendo. Di: robot ve al refri, "
                            "robot busca una silla, o robot dime que puedes hacer."),
                            ("END", "")]
                    else:
                        plan = [("SPEAK", "No entendi la instruccion."), ("END", "")]
                else:
                    self._fail_count = 0
                self.plan       = plan
                self.plan_index = 0
                self.get_logger().info(f"Plan (Ollama): {self.plan}")
                self.state = SM_EXECUTE_PLAN

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
                    # FIX #3: ya está en el destino → no publicar goal
                    if arg == self.current_location:
                        self._speak(f"Ya estoy en {arg.replace('_', ' ')}.")
                        continue
                    if self._publish_goal(arg):
                        self.goal_reached    = False
                        self.nav_timeout     = 0
                        self.target_location = arg
                        self.state = SM_WAIT_GOAL_REACHED
                    else:
                        self._speak(f"No conozco el lugar {arg}.")
                        self.plan       = []
                        self.plan_index = 0
                        self.state = SM_DONE

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
                    self.plan            = []
                    self.plan_index      = 0
                    self.target_location = None
                    self.goal_reached    = False
                    self.nav_timeout     = 0
                    self.state = SM_DONE

                elif action == "END":
                    self.state = SM_DONE

            elif self.state == SM_WAIT_GOAL_REACHED:
                if self.cancel_requested:
                    self.state = SM_DONE
                    continue
                if self.goal_reached:
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
                    if self.nav_timeout > NAV_TIMEOUT_CYCLES:
                        dest = (self.target_location or "destino").replace("_", " ")
                        self._speak(f"No pude llegar a {dest}. Abortare la tarea.")
                        self.plan            = []
                        self.plan_index      = 0
                        self.target_location = None
                        self.goal_reached    = False
                        self.nav_timeout     = 0
                        self.state = SM_DONE

            elif self.state == SM_DONE:
                self.get_logger().info("Plan completado.")
                self.plan             = []
                self.plan_index       = 0
                self.cancel_requested = False
                self.state = SM_WAIT_FOR_COMMAND


# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────
def main(args=None):
    rclpy.init(args=args)
    node = None
    try:
        node = SmPlannerNode()
        node.spin()
    finally:
        if node is not None:
            try:
                node.pub_cmd_vel.publish(Twist())
            except Exception:
                pass
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
