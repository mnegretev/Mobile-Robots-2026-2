"""
speech2text.faster_whisper_asr
===============================
Speech recognition node using Faster Whisper.

Improvements over original:
- Subscribes to /tts_query to detect when the robot is speaking.
- Ignores audio for TTS_MUTE_SECONDS after the robot speaks,
  preventing the microphone from picking up the robot's own voice.
"""

import time
import wave

import numpy
import pyaudio
import rclpy
from faster_whisper import WhisperModel
from rclpy.duration import Duration
from rclpy.node import Node
from std_msgs.msg import String


# ---------------------------------------------------------------------------
# Audio parameters
# ---------------------------------------------------------------------------

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100
WAVE_OUTPUT_FILENAME = "/dev/shm/recorder_audio.wav"

# Power threshold to detect speech vs silence.
PWR_THRESHOLD = 0.1

# How many consecutive silent chunks end a recording.
SILENCE_CHUNKS = 20

# Seconds to ignore microphone after the robot finishes speaking.
TTS_MUTE_SECONDS = 1.5


# ---------------------------------------------------------------------------
# Node
# ---------------------------------------------------------------------------

class FasterWhisperNode(Node):
    """
    Listens to the microphone, transcribes speech via Faster Whisper,
    and publishes the result to /sp_rec/recognized.

    Subscribes to /tts_query to mute the microphone while the robot speaks.
    """

    def __init__(self) -> None:
        super().__init__("faster_whisper_node")

        # Timestamp of the last TTS message received.
        self._tts_last_time: float = 0.0

        # -- Publishers --
        self.pub_recognized = self.create_publisher(String, "/sp_rec/recognized", 1)

        # -- Subscribers --
        self.tts_sub = self.create_subscription(
            String,
            "/tts_query",
            self._on_tts,
            10,
        )

        self.get_logger().info("Speech2Text node initialized.")

    def _on_tts(self, msg: String) -> None:
        """Record the time the robot started speaking."""
        self.get_logger().info(f"[TTS detected] Muting microphone for {TTS_MUTE_SECONDS}s.")
        self._tts_last_time = time.time()

    def _is_muted(self) -> bool:
        """Return True if we are still within the mute window."""
        return (time.time() - self._tts_last_time) < TTS_MUTE_SECONDS

    def spin(self) -> None:
        self.get_logger().info("Loading Faster Whisper model (small, cpu, int8)...")
        model = WhisperModel("small", device="cpu", compute_type="int8")
        self.get_logger().info("Whisper model loaded.")

        # Force PulseAudio to use the physical microphone, not the monitor
        import subprocess
        subprocess.run([
            "pactl", "set-default-source",
            "alsa_input.pci-0000_00_1f.3.analog-stereo"
        ], check=False)

        p = pyaudio.PyAudio()
        stream = p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK,
        )
        self.get_logger().info("Using physical microphone via PulseAudio.")
        self.get_logger().info("Microphone stream open. Listening...")

        while rclpy.ok():

            # -- Step 1: Wait for speech above power threshold --
            self.get_logger().info("Waiting for speech...")
            pwr = 0.0
            last_chunk = None
            while pwr < PWR_THRESHOLD and rclpy.ok():
                data = stream.read(CHUNK)

                # If robot just spoke, drain audio and reset
                if self._is_muted():
                    pwr = 0.0
                    continue

                arr = numpy.frombuffer(data, dtype=numpy.int16) / 32768.0
                pwr = numpy.mean(arr ** 2)
                last_chunk = data

            if not rclpy.ok():
                break

            # -- Step 2: Record until silence --
            self.get_logger().info("Speech detected. Recording...")
            frames = [last_chunk]
            silence_counter = 0

            while silence_counter < SILENCE_CHUNKS and rclpy.ok():
                data = stream.read(CHUNK)
                frames.append(data)
                arr = numpy.frombuffer(data, dtype=numpy.int16) / 32768.0
                pwr = numpy.mean(arr ** 2)
                if pwr < PWR_THRESHOLD:
                    silence_counter += 1
                else:
                    silence_counter = 0

            self.get_logger().info("Recording stopped.")

            # -- Step 3: Save WAV --
            wf = wave.open(WAVE_OUTPUT_FILENAME, "wb")
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(p.get_sample_size(FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(b"".join(frames))
            wf.close()

            # -- Step 4: Transcribe --
            segments, info = model.transcribe(
                WAVE_OUTPUT_FILENAME, beam_size=5, language="es"
            )
            self.get_logger().info(
                f"Detected language '{info.language}' "
                f"(confidence {info.language_probability:.2f})"
            )

            for segment in segments:
                text = segment.text.strip()
                self.get_logger().info(f"[Transcription] '{text}'")
                self.pub_recognized.publish(String(data=text))
                break  # Only publish the first segment

            rclpy.spin_once(self, timeout_sec=0)
            self.get_clock().sleep_for(Duration(seconds=0.005))

        stream.stop_stream()
        stream.close()
        p.terminate()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main(args=None) -> None:
    rclpy.init(args=args)
    node = FasterWhisperNode()
    try:
        node.spin()
    except KeyboardInterrupt:
        node.get_logger().info("Shutting down Speech2Text node.")
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
