#!/usr/bin/env python3
#
# MOBILE ROBOTS - FI-UNAM, 2026-2
# AUTOMATED EXPERIMENTS FOR BINARY LABEL DIGIT CLASSIFICATION
#
# This script runs automated experiments with different neural network configurations
# for handwritten digit recognition using 4-bit binary label representation.
#

import numpy as np
import json
import time
from datetime import datetime
import os

NAME = "Galicia Rioja Angel Daniel"

class FCNeuralNetworkBinary:
    def __init__(self, layers, learning_rate=0.1):
        self.layers = layers
        self.learning_rate = learning_rate
        self.weights = []
        self.biases = []

        # Initialize weights and biases
        for i in range(len(layers) - 1):
            w = np.random.randn(layers[i+1], layers[i]) * np.sqrt(2.0 / layers[i])
            b = np.zeros((layers[i+1], 1))
            self.weights.append(w)
            self.biases.append(b)

    def sigmoid(self, x):
        return 1 / (1 + np.exp(-x))

    def sigmoid_derivative(self, x):
        return x * (1 - x)

    def feedforward(self, x):
        activations = [x]
        zs = []

        for w, b in zip(self.weights, self.biases):
            z = np.dot(w, activations[-1]) + b
            zs.append(z)
            activation = self.sigmoid(z)
            activations.append(activation)

        return activations, zs

    def backpropagate(self, x, y):
        activations, zs = self.feedforward(x)

        # Output layer error
        delta = (activations[-1] - y) * self.sigmoid_derivative(activations[-1])

        # Gradients
        nabla_w = [np.zeros(w.shape) for w in self.weights]
        nabla_b = [np.zeros(b.shape) for b in self.biases]

        # Output layer gradients
        nabla_w[-1] = np.dot(delta, activations[-2].T)
        nabla_b[-1] = delta

        # Hidden layers
        for l in range(2, len(self.layers)):
            delta = np.dot(self.weights[-l+1].T, delta) * self.sigmoid_derivative(activations[-l])
            nabla_w[-l] = np.dot(delta, activations[-l-1].T)
            nabla_b[-l] = delta

        return nabla_w, nabla_b

    def update_with_batch(self, batch, learning_rate):
        nabla_w_total = [np.zeros(w.shape) for w in self.weights]
        nabla_b_total = [np.zeros(b.shape) for b in self.biases]

        for x, y in batch:
            nabla_w, nabla_b = self.backpropagate(x, y)
            nabla_w_total = [nw + dnw for nw, dnw in zip(nabla_w_total, nabla_w)]
            nabla_b_total = [nb + dnb for nb, dnb in zip(nabla_b_total, nabla_b)]

        # Update weights and biases
        self.weights = [w - (learning_rate / len(batch)) * nw
                       for w, nw in zip(self.weights, nabla_w_total)]
        self.biases = [b - (learning_rate / len(batch)) * nb
                      for b, nb in zip(self.biases, nabla_b_total)]

    def train_by_SGD(self, training_data, epochs, batch_size, learning_rate, test_data=None):
        start_time = time.time()

        for epoch in range(epochs):
            np.random.shuffle(training_data)

            # Create mini-batches
            for i in range(0, len(training_data), batch_size):
                batch = training_data[i:i+batch_size]
                self.update_with_batch(batch, learning_rate)

            if test_data:
                accuracy = self.evaluate(test_data)
                print(f"Epoch {epoch+1}/{epochs}: Accuracy = {accuracy:.3f}")

        training_time = time.time() - start_time
        return training_time

    def evaluate(self, test_data):
        correct = 0
        for x, y in test_data:
            activations, _ = self.feedforward(x)
            prediction = np.round(activations[-1]).astype(int)
            actual = y.astype(int).flatten()
            if np.array_equal(prediction.flatten(), actual):
                correct += 1
        return correct / len(test_data)

def digit_to_binary(digit):
    """Convert digit to 4-bit binary representation"""
    binary = [int(b) for b in format(digit, '04b')]
    return np.array(binary).reshape(-1, 1)

def load_data_binary():
    """Load handwritten digits data with binary labels"""
    data_dir = "../dataset"

    # Load all samples from binary digit files
    all_data = []
    for digit in range(10):
        filename = f"data{digit}"
        filepath = os.path.join(data_dir, filename)
        if os.path.exists(filepath):
            raw = np.fromfile(filepath, dtype=np.uint8)
            if raw.size % 784 != 0:
                raise ValueError(f"Unexpected file size for {filepath}: {raw.size}")
            samples = raw.reshape(-1, 784)
            for sample in samples:
                x = sample.reshape(-1, 1).astype(np.float32) / 255.0
                y = digit_to_binary(digit)
                all_data.append((x, y))

    # Split into training and test (80-20)
    np.random.shuffle(all_data)
    split_idx = int(0.8 * len(all_data))
    training_data = all_data[:split_idx]
    test_data = all_data[split_idx:]

    return training_data, test_data

def evaluate_metrics_binary(nn, test_data):
    """Evaluate comprehensive metrics for binary classification"""
    predictions = []
    actuals = []

    for x, y in test_data:
        activations, _ = nn.feedforward(x)
        pred = np.round(activations[-1]).astype(int).flatten()
        actual = y.astype(int).flatten()
        predictions.append(pred)
        actuals.append(actual)

    # Calculate binary accuracy (exact match)
    accuracy = np.mean([np.array_equal(p, a) for p, a in zip(predictions, actuals)])

    # Per-digit metrics (convert back to digit for analysis)
    digit_predictions = [int(''.join(map(str, p)), 2) for p in predictions]
    digit_actuals = [int(''.join(map(str, a)), 2) for a in actuals]

    precision_per_class = []
    recall_per_class = []
    f1_per_class = []

    for class_id in range(10):
        tp = sum(1 for p, a in zip(digit_predictions, digit_actuals) if p == class_id and a == class_id)
        fp = sum(1 for p, a in zip(digit_predictions, digit_actuals) if p == class_id and a != class_id)
        fn = sum(1 for p, a in zip(digit_predictions, digit_actuals) if p != class_id and a == class_id)

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

        precision_per_class.append(precision)
        recall_per_class.append(recall)
        f1_per_class.append(f1)

    macro_precision = np.mean(precision_per_class)
    macro_recall = np.mean(recall_per_class)
    macro_f1 = np.mean(f1_per_class)

    return {
        'accuracy': accuracy,
        'macro_precision': macro_precision,
        'macro_recall': macro_recall,
        'macro_f1': macro_f1,
        'precision_per_class': precision_per_class,
        'recall_per_class': recall_per_class,
        'f1_per_class': f1_per_class
    }

def run_experiments():
    """Run automated experiments with different configurations for binary classification"""
    print("Loading binary data...")
    training_data, test_data = load_data_binary()
    print(f"Training samples: {len(training_data)}")
    print(f"Test samples: {len(test_data)}")

    # Experiment configurations as per practice requirements
    configurations = [
        # Base architecture: 784-100-4
        {"name": "Binary_Base_0.5_lr_3_epochs_5_batch", "layers": [784, 100, 4], "learning_rate": 0.5, "epochs": 3, "batch_size": 5},
        {"name": "Binary_Base_0.5_lr_10_epochs_5_batch", "layers": [784, 100, 4], "learning_rate": 0.5, "epochs": 10, "batch_size": 5},
        {"name": "Binary_Base_0.5_lr_50_epochs_5_batch", "layers": [784, 100, 4], "learning_rate": 0.5, "epochs": 50, "batch_size": 5},
        {"name": "Binary_Base_0.5_lr_100_epochs_5_batch", "layers": [784, 100, 4], "learning_rate": 0.5, "epochs": 100, "batch_size": 5},

        {"name": "Binary_Base_1.0_lr_3_epochs_10_batch", "layers": [784, 100, 4], "learning_rate": 1.0, "epochs": 3, "batch_size": 10},
        {"name": "Binary_Base_1.0_lr_10_epochs_10_batch", "layers": [784, 100, 4], "learning_rate": 1.0, "epochs": 10, "batch_size": 10},
        {"name": "Binary_Base_1.0_lr_50_epochs_10_batch", "layers": [784, 100, 4], "learning_rate": 1.0, "epochs": 50, "batch_size": 10},
        {"name": "Binary_Base_1.0_lr_100_epochs_10_batch", "layers": [784, 100, 4], "learning_rate": 1.0, "epochs": 100, "batch_size": 10},

        {"name": "Binary_Base_3.0_lr_3_epochs_30_batch", "layers": [784, 100, 4], "learning_rate": 3.0, "epochs": 3, "batch_size": 30},
        {"name": "Binary_Base_3.0_lr_10_epochs_30_batch", "layers": [784, 100, 4], "learning_rate": 3.0, "epochs": 10, "batch_size": 30},
        {"name": "Binary_Base_3.0_lr_50_epochs_30_batch", "layers": [784, 100, 4], "learning_rate": 3.0, "epochs": 50, "batch_size": 30},
        {"name": "Binary_Base_3.0_lr_100_epochs_30_batch", "layers": [784, 100, 4], "learning_rate": 3.0, "epochs": 100, "batch_size": 30},

        {"name": "Binary_Base_10.0_lr_3_epochs_100_batch", "layers": [784, 100, 4], "learning_rate": 10.0, "epochs": 3, "batch_size": 100},
        {"name": "Binary_Base_10.0_lr_10_epochs_100_batch", "layers": [784, 100, 4], "learning_rate": 10.0, "epochs": 10, "batch_size": 100},
        {"name": "Binary_Base_10.0_lr_50_epochs_100_batch", "layers": [784, 100, 4], "learning_rate": 10.0, "epochs": 50, "batch_size": 100},
        {"name": "Binary_Base_10.0_lr_100_epochs_100_batch", "layers": [784, 100, 4], "learning_rate": 10.0, "epochs": 100, "batch_size": 100},

        # Alternative architecture: 784-50-25-4
        {"name": "Binary_Alt_0.5_lr_3_epochs_5_batch", "layers": [784, 50, 25, 4], "learning_rate": 0.5, "epochs": 3, "batch_size": 5},
        {"name": "Binary_Alt_0.5_lr_10_epochs_5_batch", "layers": [784, 50, 25, 4], "learning_rate": 0.5, "epochs": 10, "batch_size": 5},
        {"name": "Binary_Alt_0.5_lr_50_epochs_5_batch", "layers": [784, 50, 25, 4], "learning_rate": 0.5, "epochs": 50, "batch_size": 5},
        {"name": "Binary_Alt_0.5_lr_100_epochs_5_batch", "layers": [784, 50, 25, 4], "learning_rate": 0.5, "epochs": 100, "batch_size": 5},

        {"name": "Binary_Alt_1.0_lr_3_epochs_10_batch", "layers": [784, 50, 25, 4], "learning_rate": 1.0, "epochs": 3, "batch_size": 10},
        {"name": "Binary_Alt_1.0_lr_10_epochs_10_batch", "layers": [784, 50, 25, 4], "learning_rate": 1.0, "epochs": 10, "batch_size": 10},
        {"name": "Binary_Alt_1.0_lr_50_epochs_10_batch", "layers": [784, 50, 25, 4], "learning_rate": 1.0, "epochs": 50, "batch_size": 10},
        {"name": "Binary_Alt_1.0_lr_100_epochs_10_batch", "layers": [784, 50, 25, 4], "learning_rate": 1.0, "epochs": 100, "batch_size": 10},

        {"name": "Binary_Alt_3.0_lr_3_epochs_30_batch", "layers": [784, 50, 25, 4], "learning_rate": 3.0, "epochs": 3, "batch_size": 30},
        {"name": "Binary_Alt_3.0_lr_10_epochs_30_batch", "layers": [784, 50, 25, 4], "learning_rate": 3.0, "epochs": 10, "batch_size": 30},
        {"name": "Binary_Alt_3.0_lr_50_epochs_30_batch", "layers": [784, 50, 25, 4], "learning_rate": 3.0, "epochs": 50, "batch_size": 30},
        {"name": "Binary_Alt_3.0_lr_100_epochs_30_batch", "layers": [784, 50, 25, 4], "learning_rate": 3.0, "epochs": 100, "batch_size": 30},

        {"name": "Binary_Alt_10.0_lr_3_epochs_100_batch", "layers": [784, 50, 25, 4], "learning_rate": 10.0, "epochs": 3, "batch_size": 100},
        {"name": "Binary_Alt_10.0_lr_10_epochs_100_batch", "layers": [784, 50, 25, 4], "learning_rate": 10.0, "epochs": 10, "batch_size": 100},
        {"name": "Binary_Alt_10.0_lr_50_epochs_100_batch", "layers": [784, 50, 25, 4], "learning_rate": 10.0, "epochs": 50, "batch_size": 100},
        {"name": "Binary_Alt_10.0_lr_100_epochs_100_batch", "layers": [784, 50, 25, 4], "learning_rate": 10.0, "epochs": 100, "batch_size": 100},
    ]

    results = []

    for i, config in enumerate(configurations):
        print(f"\n🔄 Running binary experiment {i+1}/{len(configurations)}: {config['name']}")

        # Run multiple trials
        accuracies = []
        training_times = []

        for trial in range(100):  # Run 100 trials as per practice requirements
            nn = FCNeuralNetworkBinary(config['layers'], config['learning_rate'])
            training_time = nn.train_by_SGD(training_data, config['epochs'], config['batch_size'], config['learning_rate'])
            accuracy = nn.evaluate(test_data)

            accuracies.append(accuracy)
            training_times.append(training_time)

        # Average results
        avg_accuracy = np.mean(accuracies)
        avg_training_time = np.mean(training_times)

        # Get detailed metrics from last trial
        nn = FCNeuralNetworkBinary(config['layers'], config['learning_rate'])
        nn.train_by_SGD(training_data, config['epochs'], config['batch_size'], config['learning_rate'])
        metrics = evaluate_metrics_binary(nn, test_data)

        result = {
            'config': config,
            'metrics': metrics,
            'training_time': avg_training_time,
            'trials': 100
        }
        results.append(result)

        print(f"✅ Completed: Accuracy = {avg_accuracy:.3f}, Time = {avg_training_time:.1f}s")

    return results

def generate_report(results):
    """Generate comprehensive Markdown report for binary experiments"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"binary_experiments_report_{timestamp}.md"

    with open(filename, 'w', encoding='utf-8') as f:
        f.write("# PRÁCTICA 3: REDES NEURONALES CON ETIQUETAS BINARIAS\n\n")
        f.write("**Estudiante:** Galicia Rioja Angel Daniel\n")
        f.write(f"**Fecha:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        f.write("## RESUMEN EJECUTIVO\n\n")
        f.write("Este reporte presenta los resultados de experimentos con redes neuronales ")
        f.write("utilizando representación binaria de 4 bits para las etiquetas de dígitos (0-9). ")
        f.write("Esta aproximación reduce la dimensionalidad de salida de 10 a 4 neuronas.\n\n")

        f.write("## CONFIGURACIONES PROBADAS\n\n")
        f.write("| Configuración | Arquitectura | Épocas | Tamaño Lote | Tasa Aprendizaje |\n")
        f.write("|---------------|--------------|--------|-------------|------------------|\n")

        for result in results:
            config = result['config']
            arch = '-'.join(map(str, config['layers']))
            f.write(f"| {config['name']} | {arch} | {config['epochs']} | {config['batch_size']} | {config['learning_rate']} |\n")

        f.write("\n## RESULTADOS DETALLADOS\n\n")
        f.write("### Ranking por Precisión\n\n")
        f.write("| Posición | Configuración | Precisión | Precisión Macro | Recall Macro | F1 Macro | Tiempo (s) |\n")
        f.write("|----------|---------------|-----------|-----------------|--------------|-----------|------------|\n")

        # Sort by accuracy
        sorted_results = sorted(results, key=lambda x: x['metrics']['accuracy'], reverse=True)

        for i, result in enumerate(sorted_results):
            config = result['config']
            metrics = result['metrics']
            f.write(f"| {i+1} | {config['name']} | {metrics['accuracy']:.3f} | {metrics['macro_precision']:.3f} | {metrics['macro_recall']:.3f} | {metrics['macro_f1']:.3f} | {result['training_time']:.1f} |\n")

        f.write("\n### Análisis por Configuración\n\n")

        for result in results:
            config = result['config']
            metrics = result['metrics']

            f.write(f"#### {config['name']}\n\n")
            f.write("**Parámetros:**\n")
            f.write(f"- Arquitectura: {config['layers']}\n")
            f.write(f"- Épocas: {config['epochs']}\n")
            f.write(f"- Tamaño de lote: {config['batch_size']}\n")
            f.write(f"- Tasa de aprendizaje: {config['learning_rate']}\n\n")

            f.write("**Métricas de desempeño:**\n")
            f.write(f"- Precisión global: {metrics['accuracy']:.3f}\n")
            f.write(f"- Precisión macro: {metrics['macro_precision']:.3f}\n")
            f.write(f"- Recall macro: {metrics['macro_recall']:.3f}\n")
            f.write(f"- F1 macro: {metrics['macro_f1']:.3f}\n")
            f.write(f"- Tiempo de entrenamiento: {result['training_time']:.1f}s\n")

            f.write("\n**Representación binaria por clase:**\n")
            binary_reps = ['0000', '0001', '0010', '0011', '0100', '0101', '0110', '0111', '1000', '1001']
            for i, (p, r, f1, binary) in enumerate(zip(metrics['precision_per_class'],
                                                      metrics['recall_per_class'],
                                                      metrics['f1_per_class'],
                                                      binary_reps)):
                f.write(f"- Dígito {i} (binario: {binary}): Precisión={p:.3f}, Recall={r:.3f}, F1={f1:.3f}\n")
            f.write("\n")

        f.write("## CONCLUSIONES\n\n")

        # Best configuration
        best_result = max(results, key=lambda x: x['metrics']['accuracy'])
        best_config = best_result['config']
        best_metrics = best_result['metrics']

        f.write("### Mejor Configuración\n\n")
        f.write(f"La configuración con mejor desempeño fue **{best_config['name']}** ")
        f.write(f"con una precisión de {best_metrics['accuracy']:.3f}. ")
        f.write(f"Esta configuración utilizó una arquitectura {best_config['layers']} ")
        f.write(f"con {best_config['epochs']} épocas, tamaño de lote {best_config['batch_size']} ")
        f.write(f"y tasa de aprendizaje {best_config['learning_rate']}.\n\n")

        f.write("### Comparación con Enfoque Tradicional\n\n")
        f.write("El enfoque de etiquetas binarias tiene las siguientes características:\n\n")
        f.write("**Ventajas:**\n")
        f.write("- Reduce la dimensionalidad de salida (4 vs 10 neuronas)\n")
        f.write("- Puede ser más eficiente en términos de parámetros\n")
        f.write("- Representa naturalmente la relación entre dígitos\n\n")

        f.write("**Desventajas:**\n")
        f.write("- Mayor complejidad en la interpretación de errores\n")
        f.write("- Posibles ambigüedades en la clasificación\n")
        f.write("- Menor precisión en algunos casos debido a la compresión\n\n")

        f.write("### Recomendaciones\n\n")
        f.write("Para aplicaciones prácticas, el enfoque tradicional de 10 clases separadas ")
        f.write("generalmente ofrece mejor precisión. El enfoque binario puede ser útil ")
        f.write("en escenarios con restricciones de recursos o cuando se busca una ")
        f.write("representación más compacta.\n\n")

        f.write("---\n\n")
        f.write("*Reporte generado automáticamente por el sistema de experimentación*\n")

    print(f"📄 Report generated: {filename}")

    # Save results to JSON
    json_filename = f"binary_experiments_results_{timestamp}.json"
    with open(json_filename, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"💾 Results saved to: {json_filename}")

if __name__ == "__main__":
    print("PRACTICE 3 - AUTOMATED EXPERIMENTS FOR BINARY LABEL DIGIT CLASSIFICATION")
    print("=" * 75)

    results = run_experiments()
    generate_report(results)

    print("\n🎉 All binary experiments completed successfully!")
