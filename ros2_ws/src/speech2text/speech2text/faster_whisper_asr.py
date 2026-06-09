#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from faster_whisper import WhisperModel
import sounddevice as sd
import numpy as np
import queue
import threading

class Speech2TextNode(Node):
    def __init__(self):
        super().__init__('faster_whisper_asr')
        self.publisher = self.create_publisher(String, '/sp_rec/recognized', 10)
        self.model = WhisperModel("base",device="cpu", compute_type="int8")
        self.audio_queue = queue.Queue()
        self.sample_rate = 16000
        self.recording = False
        self.get_logger().info('Faster Whisper ASR Node initialized')
        
    def start_recording(self):
        self.recording = True
        self.stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype=np.float32,
            callback=self.audio_callback
        )
        self.stream.start()
        self.get_logger().info('Recording started. Speak into the microphone...')
        
        # Thread for processing audio
        self.processing_thread = threading.Thread(target=self.process_audio)
        self.processing_thread.start()
        
    def audio_callback(self, indata, frames, time, status):
        if status:
            self.get_logger().warn(f'Audio callback status: {status}')
        self.audio_queue.put(indata.copy())
        
    def process_audio(self):
        audio_buffer = []
        while self.recording:
            try:
                audio_chunk = self.audio_queue.get(timeout=0.5)
                audio_buffer.extend(audio_chunk.flatten())
                if len(audio_buffer) >= self.sample_rate * 2:  # 2 seconds of audio
                    audio_array = np.array(audio_buffer, dtype=np.float32)
                    segments, _ = self.model.transcribe(audio_array, beam_size=5,language="es")
                    text = " ".join([seg.text for seg in segments])
                    if text.strip():
                        msg = String()
                        msg.data = text
                        self.publisher.publish(msg)
                        self.get_logger().info(f'Recognized: {text}')
                    audio_buffer = []
            except queue.Empty:
                pass
                
    def __del__(self):
        if hasattr(self, 'stream'):
            self.stream.stop()
            self.stream.close()
        self.recording = False

def main(args=None):
    rclpy.init(args=args)
    node = Speech2TextNode()
    node.start_recording()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
