#
# MOBILE ROBOTS - FI-UNAM, 2026-2
# PROYECTO FINAL - CEREBRO / MAQUINA DE ESTADOS
#
# Recibe instrucciones por voz (/sp_rec/recognized), las convierte en un PLAN
# con Ollama (formato JSON) y lo ejecuta llamando a las capacidades del robot.
# Capacidades:
#   - navigate_to : desplazarse a lugares conocidos del departamento (mapa + coordenadas)
#   - say         : hablar
#   - move_arm    : levantar el brazo para que la camara (en link6) mire al frente
#   - detect_object: revisar lo que ve YOLO (/yolo/detections) y anunciarlo
#
import json
import time
import math
import requests
import unicodedata
import difflib

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from std_msgs.msg import String, Bool
from geometry_msgs.msg import PoseStamped, Twist
from control_msgs.action import FollowJointTrajectory
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from builtin_interfaces.msg import Duration

# ============================ CONFIG ============================
OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "llama3"            # cambia por el que tengas en Ollama (llama3.1, qwen2.5, ...)

# Mapa semantico: nombre del lugar -> (x, y) en el frame "map".
# Coordenadas reales capturadas con "2D Nav Goal" / echo de /goal_pose.
LOCATIONS = {
    "recamara":                (-3.424,  1.412),
    "sala de usos multiples":  (-3.516, -1.689),
    "sala":                    ( 3.038,  0.730),
    "desayunador":             ( 1.795,  4.976),
    "gimnasio":                ( 5.083,  5.796),
    "comedor":                 (10.580,  2.340),
    "cocina":                  ( 8.753, -1.711),
}

NAV_TIMEOUT = 210.0        # s: backstop, por encima del tope de stanley (rutas largas)

# ---- Brazo (xArm6) ----
ARM_ACTION = "/xarm6_traj_controller/follow_joint_trajectory"
ARM_JOINTS = ['joint1', 'joint2', 'joint3', 'joint4', 'joint5', 'joint6']
# Pose de "mirar": la camara en link6 queda apuntando al frente (validada en sim).
ARM_VIEW_POSE = [0.0, -1.0, 0.0, 0.0, -0.5, 0.0]
ARM_MOVE_TIME = 3.0        # s para llegar a la pose
ARM_SETTLE   = 1.0         # s extra para que la imagen se estabilice antes de detectar

# ---- Vision / YOLO ----
MIN_DET_CONF = 0.4         # confianza minima para "creer" una deteccion
DETECT_WINDOW = 1.5        # s recolectando detecciones antes de decidir

# ---- Busqueda por escaneo (girar en el lugar para buscar) ----
CMD_VEL_TOPIC   = "/cmd_vel"   # mismo topico que usa la navegacion
SCAN_STEP_DEG   = 45.0         # cuanto gira entre miradas
SCAN_STEPS      = 7            # rotaciones ademas de la mirada inicial (8 miradas = vuelta completa)
SCAN_ROT_SPEED  = 0.5          # rad/s al girar en el lugar (lento y seguro)
SCAN_LOOK_WINDOW = 1.0         # s mirando en cada orientacion
# ================================================================


def _norm(s):
    # minusculas y sin acentos, para casar "Recamara"/"recámara"/"COCINA", etc.
    s = unicodedata.normalize("NFD", str(s).strip().lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


LOCATIONS_NORM = {_norm(k): v for k, v in LOCATIONS.items()}

# Nombre "hablado" (con articulo) para anunciar llegada de forma natural.
SPOKEN_NAME = {
    "recamara":               "la recamara",
    "sala de usos multiples": "la sala de usos multiples",
    "sala":                   "la sala",
    "desayunador":            "el desayunador",
    "gimnasio":               "el gimnasio",
    "comedor":                "el comedor",
    "cocina":                 "la cocina",
}

# Traduccion de clases COCO (ingles) a frase en espanol, para narrar bonito.
# Si una clase no esta aqui, se usa el nombre en ingles tal cual.
COCO_ES = {
    "person": "una persona", "chair": "una silla", "couch": "un sofa",
    "bench": "una banca", "bed": "una cama", "dining table": "una mesa",
    "tv": "una television", "laptop": "una laptop", "bottle": "una botella",
    "cup": "una taza", "bowl": "un tazon", "wine glass": "una copa",
    "fork": "un tenedor", "knife": "un cuchillo", "spoon": "una cuchara",
    "refrigerator": "un refrigerador", "microwave": "un microondas", "oven": "un horno",
    "sink": "un fregadero", "toilet": "un inodoro", "book": "un libro",
    "clock": "un reloj", "vase": "un florero", "potted plant": "una planta",
    "remote": "un control", "cell phone": "un celular", "keyboard": "un teclado",
    "mouse": "un raton", "teddy bear": "un peluche", "backpack": "una mochila",
    "handbag": "una bolsa", "sports ball": "una pelota", "car": "un automovil",
}

# Plural en espanol (singular_con_articulo, plural) para narrar conteos.
COCO_ES_PLURAL = {
    "person": ("una persona", "personas"), "chair": ("una silla", "sillas"),
    "couch": ("un sofa", "sofas"), "bench": ("una banca", "bancas"),
    "bed": ("una cama", "camas"), "tv": ("una television", "televisiones"),
    "bottle": ("una botella", "botellas"), "cup": ("una taza", "tazas"),
    "sports ball": ("una pelota", "pelotas"), "cell phone": ("un celular", "celulares"),
    "book": ("un libro", "libros"),
}


def coco_to_es(name):
    return COCO_ES.get(str(name).lower(), str(name))


def cantidad_es(name, n):
    # "una silla" si n<=1, "2 sillas" si n>1
    sing, plur = COCO_ES_PLURAL.get(str(name).lower(), (coco_to_es(name), str(name) + "s"))
    return sing if n <= 1 else (str(n) + " " + plur)


# Normaliza el nombre que manda el LLM a la clase EXACTA de COCO
# (el LLM a veces dice "phone" en vez de "cell phone", "ball" en vez de "sports ball").
TARGET_CANON = {
    "phone": "cell phone", "movil": "cell phone", "celular": "cell phone",
    "ball": "sports ball", "pelota": "sports ball",
    "tele": "tv", "television": "tv", "televisor": "tv", "televisior": "tv",
    "auto": "car", "automovil": "car", "coche": "car", "carro": "car",
    "sillon": "couch", "sofa": "couch",
}


# En simulacion los muebles se confunden: una silla puede salir como "bench" o
# "couch", etc. Mapa: objeto pedido (ingles o espanol) -> etiquetas COCO que
# CUENTAN como ese objeto. Ajusta segun lo que veas en /yolo/detections.
OBJECT_ALIASES = {
    "chair":  ["chair", "bench", "couch"],
    "silla":  ["chair", "bench", "couch"],
    "sofa":   ["couch", "bench", "chair"],
    "couch":  ["couch", "bench", "chair"],
    "sillon": ["couch", "bench", "chair"],
}


def build_system_prompt():
    lugares = ", ".join(LOCATIONS.keys())
    return (
        "Eres el cerebro de un robot de servicio movil llamado Justina, que se mueve "
        "en un departamento. Conviertes la instruccion del usuario en un PLAN ejecutable, "
        "o indicas que no es posible.\n\n"
        "SOLO puedes usar estas acciones:\n"
        '  {"action": "navigate_to", "location": "<lugar>"}    -> el robot se desplaza a un lugar\n'
        '  {"action": "say", "text": "<texto>"}                -> el robot dice algo en voz alta\n'
        '  {"action": "move_arm"}                               -> levanta el brazo para que la camara mire al frente\n'
        '  {"action": "detect_object", "object": "<objeto>"}    -> revisa si ve un objeto y lo anuncia (sin girar)\n'
        '  {"action": "find_object", "object": "<objeto>", "location": "<lugar opcional>"}\n'
        "                                                       -> BUSCA un objeto: navega al lugar (si se da), apunta\n"
        "                                                          la camara y GIRA en el lugar para barrer el area\n\n"
        "Lugares conocidos (usa EXACTAMENTE estos nombres): " + lugares + "\n\n"
        "Responde UNICAMENTE con un objeto JSON con este formato exacto:\n"
        "{\n"
        '  "feasible": true,\n'
        '  "speech": "<frase corta, maximo 15 palabras, para decir al recibir la orden>",\n'
        '  "plan": [ <lista de acciones> ]\n'
        "}\n\n"
        "Reglas:\n"
        "- Si la instruccion NO se puede cumplir con las acciones o lugares disponibles, "
        'responde {"feasible": false, "speech": "<explica brevemente por que no puedes>", "plan": []}.\n'
        "- Usa solo los nombres de lugares de la lista. No inventes lugares ni acciones.\n"
        "- Para BUSCAR/ENCONTRAR un objeto en un area (ej: 'busca el refrigerador', "
        "'ve a la cocina y busca una silla'), usa find_object. find_object YA navega, "
        "apunta la camara y gira para buscar, asi que con esa accion NO agregues "
        "navigate_to ni move_arm aparte.\n"
        "- Para solo PREGUNTAR si ves algo desde donde estas (ej: '¿ves una silla?'), "
        "usa move_arm y luego detect_object (sin girar, sin navegar).\n"
        '- En "object" usa el nombre del objeto en INGLES y EXACTO de COCO '
        '(ej: bottle, cup, chair, person, tv, cell phone, sports ball, refrigerator).\n'
        "- Si el usuario solo PREGUNTA si ves algo o como '¿ves una X?', NO navegues: "
        "usa solo move_arm y detect_object desde donde estas. Navega SOLO si te piden ir a un lugar.\n"
        "- Si el usuario pregunta 'que ves' o 'que objetos hay' (sin nombrar un objeto), "
        'usa detect_object SIN el campo "object" para que liste todo lo que ve.\n'
        "- 'speech' siempre corto y en espanol.\n"
        "- No escribas nada fuera del JSON.\n\n"
        "Ejemplo 1 (buscar en un lugar). Instruccion: 've a la cocina y busca el refrigerador'\n"
        '{"feasible": true, "speech": "Voy a la cocina a buscar el refrigerador", "plan": ['
        '{"action": "find_object", "object": "refrigerator", "location": "cocina"}]}\n\n'
        "Ejemplo 2 (buscar donde estoy, girando). Instruccion: 'busca una silla'\n"
        '{"feasible": true, "speech": "Voy a buscar una silla", "plan": ['
        '{"action": "find_object", "object": "chair"}]}\n\n'
        "Ejemplo 3 (pregunta, NO navega ni gira). Instruccion: 'dime si ves una silla'\n"
        '{"feasible": true, "speech": "Dejame ver", "plan": ['
        '{"action": "move_arm"}, {"action": "detect_object", "object": "chair"}]}\n\n'
        "Ejemplo 4 (describir todo). Instruccion: 'dime que ves'\n"
        '{"feasible": true, "speech": "Dejame ver", "plan": ['
        '{"action": "move_arm"}, {"action": "detect_object"}]}'
    )


class SmPlannerNode(Node):
    def __init__(self):
        super().__init__("sm_planner_node")
        self.get_logger().info("INITIALIZING SM PLANNER NODE")
        self.system_prompt = build_system_prompt()
        self.instruction = ""
        self.new_instruction = False
        self.nav_done = False
        self.nav_success = False
        self.latest_detections = []     # ultima lista de detecciones de YOLO

        self.sub_rec = self.create_subscription(
            String, '/sp_rec/recognized', self.cb_instruction, 1)
        self.sub_goal_reached = self.create_subscription(
            Bool, '/navigation/goal_reached', self.cb_goal_reached, 1)
        self.sub_yolo = self.create_subscription(
            String, '/yolo/detections', self.cb_yolo, 1)
        self.pub_goal = self.create_publisher(PoseStamped, '/goal_pose', 1)
        self.pub_tts = self.create_publisher(String, '/tts_query', 1)
        self.pub_cmd = self.create_publisher(Twist, CMD_VEL_TOPIC, 10)

        # cliente de accion para el brazo
        self.arm_ac = ActionClient(self, FollowJointTrajectory, ARM_ACTION)

    # ----------------------- callbacks -----------------------
    def cb_instruction(self, msg):
        self.instruction = msg.data
        self.new_instruction = True

    def cb_goal_reached(self, msg):
        # stanley publica True si llego de verdad, False si se rindio/ruta vacia
        self.nav_success = bool(msg.data)
        self.nav_done = True

    def cb_yolo(self, msg):
        try:
            self.latest_detections = json.loads(msg.data)
        except Exception:
            self.latest_detections = []

    # ----------------------- Ollama (planificador) -----------------------
    def plan_with_ollama(self, instruction):
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": instruction},
        ]
        try:
            resp = requests.post(OLLAMA_URL, json={
                "model": MODEL,
                "messages": messages,
                "stream": False,
                "format": "json",          # fuerza a Ollama a devolver JSON valido
                "options": {"temperature": 0.2},
            }, timeout=120)
            content = resp.json()["message"]["content"]
        except Exception as e:
            self.get_logger().error("Error hablando con Ollama: " + str(e))
            return None
        return self.parse_plan(content)

    def parse_plan(self, content):
        try:
            return json.loads(content)
        except Exception:
            # por si el modelo agrega texto extra, extraemos el bloque {...}
            try:
                a = content.index("{")
                b = content.rindex("}") + 1
                return json.loads(content[a:b])
            except Exception as e:
                self.get_logger().error("No pude parsear el JSON del plan: " + str(e))
                self.get_logger().error("Contenido recibido: " + str(content))
                return None

    # ----------------------- capacidades del robot -----------------------
    def speak(self, text):
        if not text:
            return
        self.get_logger().info("Diciendo: " + text)
        self.pub_tts.publish(String(data=text))
        # damos tiempo aproximado a que termine de hablar para no encimar acciones
        wait = min(15.0, 0.07 * len(text) + 1.5)
        end = time.monotonic() + wait
        while rclpy.ok() and time.monotonic() < end:
            rclpy.spin_once(self, timeout_sec=0.05)

    def navigate_to(self, location):
        key = _norm(location)
        if key not in LOCATIONS_NORM:
            # el LLM a veces escribe variantes/typos ("cucina"->"cocina"); buscamos el mas parecido
            match = difflib.get_close_matches(key, list(LOCATIONS_NORM.keys()), n=1, cutoff=0.6)
            if match:
                self.get_logger().info("Lugar '%s' no exacto; lo interpreto como '%s'" % (location, match[0]))
                key = match[0]
            else:
                self.speak("No conozco el lugar " + str(location))
                return False
        x, y = LOCATIONS_NORM[key]
        nombre = SPOKEN_NAME.get(key, key)
        goal = PoseStamped()
        goal.header.frame_id = "map"
        goal.header.stamp = self.get_clock().now().to_msg()
        goal.pose.position.x = float(x)
        goal.pose.position.y = float(y)
        goal.pose.orientation.w = 1.0
        self.nav_done = False
        self.nav_success = False
        self.pub_goal.publish(goal)
        self.get_logger().info("Navegando a %s (%.2f, %.2f)..." % (location, x, y))
        start = time.monotonic()
        while rclpy.ok() and not self.nav_done:
            rclpy.spin_once(self, timeout_sec=0.1)
            if time.monotonic() - start > NAV_TIMEOUT:
                self.get_logger().warn("Tiempo agotado navegando a " + location)
                self.speak("No pude llegar a " + nombre)
                return False
        if self.nav_success:
            self.get_logger().info("Llegue a " + location)
            self.speak("Ya llegue a " + nombre)
        else:
            self.get_logger().warn("No pude llegar a " + location)
            self.speak("No pude llegar a " + nombre)
        return self.nav_success

    def move_arm(self, pose=None):
        # Manda al brazo una pose de articulaciones (por defecto, la pose de "mirar").
        pose = pose if pose is not None else ARM_VIEW_POSE
        if not self.arm_ac.wait_for_server(timeout_sec=5.0):
            self.get_logger().warn("No aparecio el controlador del brazo (" + ARM_ACTION + ")")
            return False
        goal = FollowJointTrajectory.Goal()
        goal.trajectory = JointTrajectory()
        goal.trajectory.joint_names = ARM_JOINTS
        pt = JointTrajectoryPoint()
        pt.positions = [float(a) for a in pose]
        sec = int(ARM_MOVE_TIME)
        pt.time_from_start = Duration(sec=sec, nanosec=int((ARM_MOVE_TIME - sec) * 1e9))
        goal.trajectory.points = [pt]

        self.get_logger().info("Moviendo el brazo a la pose de vista: " + str(pose))
        send_future = self.arm_ac.send_goal_async(goal)
        rclpy.spin_until_future_complete(self, send_future)
        gh = send_future.result()
        if gh is None or not gh.accepted:
            self.get_logger().warn("El controlador rechazo la pose del brazo")
            return False
        res_future = gh.get_result_async()
        rclpy.spin_until_future_complete(self, res_future)
        result = res_future.result().result
        ok = (result.error_code == 0)
        if not ok:
            self.get_logger().warn("move_arm termino con error_code=" + str(result.error_code))
        # pequena espera para que la imagen de la camara se estabilice
        end = time.monotonic() + ARM_SETTLE
        while rclpy.ok() and time.monotonic() < end:
            rclpy.spin_once(self, timeout_sec=0.05)
        return ok

    def _matches(self, target, det_name):
        t = _norm(target)
        n = _norm(det_name)
        if t == n:
            return True
        if difflib.get_close_matches(t, [n], n=1, cutoff=0.85):
            return True
        # contra la traduccion al espanol (ej: target="silla" vs det="chair")
        es_words = _norm(coco_to_es(det_name)).split()   # "una silla" -> ["una","silla"]
        if t in es_words:
            return True
        # alias: en la sim una "silla" puede salir como bench/couch, etc.
        aliases = [_norm(a) for a in OBJECT_ALIASES.get(t, [])]
        return n in aliases

    def _collect(self, target, window):
        # Recolecta detecciones durante 'window' segundos. Para presencia ACUMULA
        # (mas robusto si la confianza rebota). Para CONTAR toma el maximo numero
        # visto en un solo cuadro (asi no contamos el mismo objeto varias veces).
        # 'target' debe venir YA normalizado a clase COCO. Devuelve:
        #   names           -> lista de nombres vistos (>= MIN_DET_CONF)
        #   best_count_per  -> nombre -> max num en un cuadro
        #   best_target_cnt -> max num de detecciones que casan el target en un cuadro
        seen = {}
        best_count_per = {}
        best_target_cnt = 0
        self.latest_detections = []
        end = time.monotonic() + window
        while rclpy.ok() and time.monotonic() < end:
            rclpy.spin_once(self, timeout_sec=0.05)
            frame_counts = {}
            target_in_frame = 0
            for d in self.latest_detections:
                try:
                    c = float(d.get("conf", 0.0))
                    n = d.get("name", "")
                except Exception:
                    continue
                if not n or c < MIN_DET_CONF:
                    continue
                seen[n] = max(seen.get(n, 0.0), c)
                frame_counts[n] = frame_counts.get(n, 0) + 1
                if target and self._matches(target, n):
                    target_in_frame += 1
            for k, v in frame_counts.items():
                best_count_per[k] = max(best_count_per.get(k, 0), v)
            best_target_cnt = max(best_target_cnt, target_in_frame)
        return list(seen.keys()), best_count_per, best_target_cnt

    def detect_object(self, target=""):
        # Mira desde donde esta (sin girar) y narra el resultado.
        if target:
            target = TARGET_CANON.get(_norm(target), target)
        names, best_count_per, best_target_cnt = self._collect(target, DETECT_WINDOW)

        # Sin objetivo: describe TODO lo que ve, con cantidades.
        if not target:
            if names:
                partes = [cantidad_es(n, best_count_per.get(n, 1)) for n in sorted(names)]
                self.speak("Veo " + ", ".join(partes))
            else:
                self.speak("No veo objetos que reconozca")
            return True

        # Con objetivo: ¿cuantos vio del objeto pedido?
        if best_target_cnt > 0:
            self.get_logger().info("Objeto '%s' detectado x%d" % (target, best_target_cnt))
            self.speak("Si, veo " + cantidad_es(target, best_target_cnt))
            return True
        else:
            self.get_logger().info("Objeto '%s' NO detectado. Veo: %s" % (target, names))
            self.speak("No veo " + coco_to_es(target))
            return False

    def _rotate(self, angle_rad, w=SCAN_ROT_SPEED):
        # Gira en el lugar 'angle_rad' (signo = sentido) en lazo abierto por /cmd_vel.
        if abs(angle_rad) < 1e-3:
            return
        wz = w if angle_rad > 0 else -w
        dur = abs(angle_rad) / w
        tw = Twist()
        tw.angular.z = float(wz)
        end = time.monotonic() + dur
        while rclpy.ok() and time.monotonic() < end:
            self.pub_cmd.publish(tw)
            rclpy.spin_once(self, timeout_sec=0.05)
        # detener (varias veces por si se pierde algun mensaje)
        stop = Twist()
        for _ in range(5):
            self.pub_cmd.publish(stop)
            rclpy.spin_once(self, timeout_sec=0.02)

    def find_object(self, target, location=""):
        # Busca un objeto en un area: navega (si se da lugar), pone el brazo en pose
        # de vista, y si no lo ve de frente GIRA en pasos hasta encontrarlo o dar la vuelta.
        if not target:
            self.speak("No se que objeto buscar")
            return True
        target = TARGET_CANON.get(_norm(target), target)
        obj_es = coco_to_es(target)

        # 1) ir al area si se especifico
        if location:
            if not self.navigate_to(location):
                return False     # navigate_to ya narro el fallo; cortar plan

        # 2) pose de vista
        self.move_arm()

        # 3) mirada inicial al frente
        self.speak("Buscando " + obj_es)
        _, _, cnt = self._collect(target, SCAN_LOOK_WINDOW)
        if cnt > 0:
            self.speak("Si, encontre " + cantidad_es(target, cnt))
            return True

        # 4) escaneo: girar en pasos y volver a mirar
        step = math.radians(SCAN_STEP_DEG)
        for i in range(SCAN_STEPS):
            self.get_logger().info("No lo vi; giro %d grados y vuelvo a mirar" % int(SCAN_STEP_DEG))
            self._rotate(step)
            _, _, cnt = self._collect(target, SCAN_LOOK_WINDOW)
            if cnt > 0:
                self.speak("Si, encontre " + cantidad_es(target, cnt))
                return True

        self.speak("Busque alrededor pero no encontre " + obj_es)
        return True   # no encontrarlo no es un fallo que deba abortar el plan

    def execute_action(self, step):
        action = step.get("action")
        if action == "navigate_to":
            return self.navigate_to(step.get("location", ""))
        elif action == "say":
            self.speak(step.get("text", ""))
            return True
        elif action == "move_arm":
            return self.move_arm()
        elif action == "detect_object":
            # devuelve True aunque no encuentre el objeto: "no verlo" es una respuesta
            # valida, no un fallo que deba abortar el plan.
            self.detect_object(step.get("object", ""))
            return True
        elif action == "find_object":
            # busca girando en el lugar (y navega antes si se da 'location')
            return self.find_object(step.get("object", ""), step.get("location", ""))
        # TODO (siguiente etapa): 'grasp', 'release'
        else:
            self.get_logger().warn("Accion desconocida: " + str(action))
            return False

    def execute_plan(self, result):
        if not result.get("feasible", False):
            self.speak(result.get("speech", "No puedo hacer eso."))
            return
        self.speak(result.get("speech", ""))
        for step in result.get("plan", []):
            if not self.execute_action(step):
                # navigate_to ya avisa por voz su propio fracaso; aqui solo cortamos el plan
                self.get_logger().warn("Plan interrumpido: una accion fallo")
                break

    # ----------------------- bucle principal -----------------------
    def spin(self):
        self.get_logger().info("Listo. Esperando instrucciones por voz...")
        while rclpy.ok():
            if self.new_instruction:
                self.new_instruction = False
                instr = self.instruction
                self.get_logger().info("Instruccion: " + instr)
                result = self.plan_with_ollama(instr)
                if result is None or not isinstance(result, dict):
                    self.speak("Tuve un problema entendiendo la orden.")
                else:
                    self.get_logger().info("Plan: " + json.dumps(result, ensure_ascii=False))
                    self.execute_plan(result)
                self.get_logger().info("Esperando nueva instruccion...")
            rclpy.spin_once(self, timeout_sec=0.1)


def main(args=None):
    rclpy.init(args=args)
    node = SmPlannerNode()
    node.spin()
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()