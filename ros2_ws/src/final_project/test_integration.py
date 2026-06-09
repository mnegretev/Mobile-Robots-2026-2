#!/usr/bin/env python3

"""
Script de prueba para verificar que los nodos funcionan correctamente.
Simula instrucciones de voz para probar la comunicación ASR -> Ollama Planning.
"""

import rclpy
from std_msgs.msg import String
import time
import sys

class TestPublisher:
    def __init__(self):
        rclpy.init()
        self.node = rclpy.create_node('test_publisher')
        self.publisher = self.node.create_publisher(String, '/speech_to_text', 10)
        self.listener = self.node.create_subscription(
            String, 
            '/robot_commands', 
            self.command_callback,
            10
        )
        self.last_command = None
    
    def command_callback(self, msg):
        self.last_command = msg.data
        print(f"✓ Comando recibido: {msg.data}")
    
    def send_test_command(self, command_text, wait_time=3):
        msg = String()
        msg.data = command_text
        print(f"→ Enviando: '{command_text}'")
        self.publisher.publish(msg)
        time.sleep(wait_time)
        if self.last_command:
            return self.last_command
        else:
            print("  ⚠ Sin respuesta de Ollama")
            return None
    
    def cleanup(self):
        self.node.destroy_node()
        rclpy.shutdown()

def main():
    print("=" * 60)
    print("PRUEBA DE INTEGRACIÓN: ASR + Ollama Planning")
    print("=" * 60)
    print()
    print("Asegúrate de que:")
    print("  1. ✓ Ollama está ejecutándose (ollama serve)")
    print("  2. ✓ Nodo ollama_planning está ejecutándose")
    print()
    
    try:
        tester = TestPublisher()
        
        # Esperar a que Ollama responda
        print("Esperando conexión a Ollama...")
        time.sleep(2)
        
        # Pruebas
        test_cases = [
            ("Recoge la taza de la mesa", "pick"),
            ("Muévete a la cocina", "move"),
            ("Vuela hasta el techo", "sorry"),
            ("Cociname un café", "sorry"),
            ("Extender el brazo", "pick"),
        ]
        
        print()
        print("Ejecutando pruebas:")
        print("-" * 60)
        
        for i, (instruction, expected_action) in enumerate(test_cases, 1):
            print(f"\n[Prueba {i}/{len(test_cases)}]")
            response = tester.send_test_command(instruction)
            
            if response:
                if expected_action in response.lower():
                    print(f"  ✓ PASÓ: Se detectó '{expected_action}'")
                else:
                    print(f"  ⚠ PARCIAL: Se esperaba '{expected_action}' en la respuesta")
            
            if i < len(test_cases):
                time.sleep(1)
        
        print()
        print("-" * 60)
        print("Pruebas completadas")
        
    except KeyboardInterrupt:
        print("\n\nInterrumpido por el usuario")
    except Exception as e:
        print(f"\n\nError: {e}")
        sys.exit(1)
    finally:
        tester.cleanup()

if __name__ == '__main__':
    main()
