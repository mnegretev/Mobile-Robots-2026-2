import pyaudio
import wave
import time
import sys
import select
import numpy
from faster_whisper import WhisperModel
import rclpy
from rclpy.node import Node
from rclpy.duration import Duration
from std_msgs.msg import String, Bool

# ============================ CONFIG ============================
# True  -> PUSH TO TALK: presiona ENTER y habla. A prueba de balas:
#          sin alucinaciones, sin eco. (recomendado para destrabarte)
# False -> MANOS LIBRES: escucha sola, con filtros anti-alucinacion
#          y anti-eco. Usalo cuando todo el flujo ya funcione.
PUSH_TO_TALK = True

# Si vad_filter te da error (faster_whisper viejo / falta onnxruntime),
# pon esto en False.
USE_VAD = True

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100
WAVE_OUTPUT_FILENAME = "/dev/shm/recorder_audio.wav"

PWR_THRESHOLD = 0.02            # energia para considerar que hay voz
MIN_TRIGGER_CHUNKS = 4          # chunks ruidosos seguidos para EMPEZAR a grabar (evita picos)
SILENCE_CHUNKS_TO_STOP = 25     # chunks de silencio seguidos para DEJAR de grabar (~0.6 s)
TTS_COOLDOWN = 0.8              # s que ignoramos el micro despues de que el robot hablo

MIN_CHARS = 3                   # textos mas cortos que esto se descartan
MAX_NO_SPEECH_PROB = 0.6        # si el segmento "no es voz" con prob mayor, se descarta
# Frases que Whisper suele alucinar sobre silencio/ruido (en minusculas):
HALLUCINATION_DENYLIST = [
    "subtitulos", "amara.org", "gracias por ver",
    "suscribete", "www.", ".com", "gracias por su atencion",
]
# ================================================================


class FasterWhisperNode(Node):
    def __init__(self):
        super().__init__("faster_whisper_node")
        self.get_logger().info("INITIALIZING FASTER WHISPER NODE (PTT=%s)" % PUSH_TO_TALK)
        self.model_size = "small"
        self.pub_recognized = self.create_publisher(String, '/sp_rec/recognized', 1)

        # anti-eco: escuchamos si el robot esta hablando
        self.tts_speaking = False
        self.last_tts_end = 0.0
        self.sub_speaking = self.create_subscription(
            Bool, '/tts_speaking', self.callback_speaking, 10)

    def callback_speaking(self, msg):
        self.tts_speaking = msg.data
        if not msg.data:
            self.last_tts_end = time.time()

    def muted(self):
        return self.tts_speaking or (time.time() - self.last_tts_end) < TTS_COOLDOWN

    def power(self, data):
        arr = numpy.frombuffer(data, dtype=numpy.int16) / 32768.0
        return numpy.mean(arr ** 2)

    def flush_stream(self, stream):
        # Tira el audio acumulado (lo que entro mientras transcribiamos o
        # mientras el robot hablaba) para no procesar eco viejo.
        try:
            while stream.get_read_available() >= CHUNK:
                stream.read(CHUNK, exception_on_overflow=False)
        except Exception:
            pass

    def drain_stdin(self):
        # Vacia cualquier ENTER que haya quedado en el buffer de la terminal
        # (p.ej. si presionaste ENTER de mas mientras el robot hablaba/transcribia),
        # para que el siguiente readline() espere un ENTER NUEVO de verdad.
        try:
            while select.select([sys.stdin], [], [], 0.0)[0]:
                sys.stdin.readline()
        except Exception:
            pass

    def record_until_silence(self, stream, wait_for_speech=False, respect_mute=True,
                             start_timeout=8.0):
        frames = []
        speech_started = not wait_for_speech
        no_audio = 0
        t0 = time.time()
        while no_audio < SILENCE_CHUNKS_TO_STOP and rclpy.ok():
            rclpy.spin_once(self, timeout_sec=0)
            # En push-to-talk NO respetamos el mute: tu decides cuando hablar.
            if respect_mute and self.muted():   # el robot hablo -> era eco, abortar
                return None
            data = stream.read(CHUNK, exception_on_overflow=False)
            frames.append(data)
            if self.power(data) >= PWR_THRESHOLD:
                speech_started = True
                no_audio = 0
            elif speech_started:        # solo contamos silencio despues de que empezo el habla
                no_audio += 1
            # Si presionaste ENTER pero nunca empezaste a hablar, no te cuelgues:
            # suelta el turno tras 'start_timeout' segundos.
            if not speech_started and (time.time() - t0) > start_timeout:
                return None
        return frames

    def wait_for_speech_handsfree(self, stream):
        # Espera voz sostenida, ignorando al robot. Devuelve los frames o None.
        loud = 0
        pending = []
        while rclpy.ok():
            rclpy.spin_once(self, timeout_sec=0)
            data = stream.read(CHUNK, exception_on_overflow=False)
            if self.muted():
                loud = 0
                pending = []
                continue
            if self.power(data) >= PWR_THRESHOLD:
                loud += 1
                pending.append(data)
                if loud >= MIN_TRIGGER_CHUNKS:
                    extra = self.record_until_silence(stream, wait_for_speech=False)
                    return pending + extra if extra is not None else None
            else:
                loud = 0
                pending = []
        return None

    def save_wav(self, p, frames):
        wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
        wf.close()

    def transcribe_and_publish(self, model):
        kwargs = dict(beam_size=5, language="es", condition_on_previous_text=False)
        if USE_VAD:
            kwargs["vad_filter"] = True
            kwargs["vad_parameters"] = dict(min_silence_duration_ms=500)
        segments, info = model.transcribe(WAVE_OUTPUT_FILENAME, **kwargs)
        for segment in segments:
            text = segment.text.strip()
            low = text.lower()
            self.get_logger().info("Raw: '%s' (no_speech=%.2f)" % (text, segment.no_speech_prob))
            if len(text) < MIN_CHARS:
                self.get_logger().info("  -> descartado: muy corto")
            elif segment.no_speech_prob > MAX_NO_SPEECH_PROB:
                self.get_logger().info("  -> descartado: no parece voz")
            elif any(bad in low for bad in HALLUCINATION_DENYLIST):
                self.get_logger().info("  -> descartado: alucinacion conocida")
            elif self.muted():
                self.get_logger().info("  -> descartado: el robot esta hablando")
            else:
                self.get_logger().info("  -> PUBLICANDO: " + text)
                self.pub_recognized.publish(String(data=text))
            return  # solo el primer segmento

    def spin(self):
        self.get_logger().info("Creating Faster Whisper model: " + self.model_size)
        model = WhisperModel(self.model_size, device="cpu", compute_type="int8")
        self.get_logger().info("Model ready.")
        p = pyaudio.PyAudio()
        stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE,
                        input=True, frames_per_buffer=CHUNK)

        while rclpy.ok():
            if PUSH_TO_TALK:
                self.drain_stdin()                       # tira ENTERs viejos del buffer
                print("\n>>> Presiona ENTER y habla...", flush=True)
                try:
                    sys.stdin.readline()                 # espera UN ENTER nuevo
                except Exception:
                    break
                print("    grabando... (habla ahora)", flush=True)
                self.flush_stream(stream)
                # respect_mute=False: en push-to-talk tu controlas el tiempo,
                # no abortamos por el cooldown del TTS.
                frames = self.record_until_silence(
                    stream, wait_for_speech=True, respect_mute=False)
            else:
                self.flush_stream(stream)
                frames = self.wait_for_speech_handsfree(stream)

            if not frames:
                continue
            self.save_wav(p, frames)
            self.transcribe_and_publish(model)
            rclpy.spin_once(self, timeout_sec=0)
            self.get_clock().sleep_for(Duration(seconds=0.005))

        stream.stop_stream()
        stream.close()
        p.terminate()


def main(args=None):
    rclpy.init(args=args)
    node = FasterWhisperNode()
    node.spin()
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()