#!/usr/bin/env python3
#
# MOBILE ROBOTS - FI-UNAM, 2026-2
# AUTOMATED EXPERIMENTS FOR 10-CLASS DIGIT CLASSIFICATION
#
# This script runs automated experiments with different neural network configurations
# for handwritten digit recognition using traditional 10-class approach.
#

import numpy as np
import json
import time
from datetime import datetime
import os

NAME = "Galicia Rioja Angel Daniel"

class FCNeuralNetwork:
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
            prediction = np.argmax(activations[-1])
            actual = np.argmax(y)
            if prediction == actual:
                correct += 1
        return correct / len(test_data)

def load_data():
    """Load handwritten digits data"""
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
                y = np.zeros((10, 1), dtype=np.float32)
                y[digit, 0] = 1.0
                all_data.append((x, y))

    # Split into training and test (80-20)
    np.random.shuffle(all_data)
    split_idx = int(0.8 * len(all_data))
    training_data = all_data[:split_idx]
    test_data = all_data[split_idx:]

    return training_data, test_data

def evaluate_metrics(nn, test_data):
    """Evaluate comprehensive metrics"""
    predictions = []
    actuals = []

    for x, y in test_data:
        activations, _ = nn.feedforward(x)
        pred = np.argmax(activations[-1])
        actual = np.argmax(y)
        predictions.append(pred)
        actuals.append(actual)

    # Calculate metrics
    accuracy = np.mean(np.array(predictions) == np.array(actuals))

    # Per-class metrics
    precision_per_class = []
    recall_per_class = []
    f1_per_class = []

    for class_id in range(10):
        tp = sum(1 for p, a in zip(predictions, actuals) if p == class_id and a == class_id)
        fp = sum(1 for p, a in zip(predictions, actuals) if p == class_id and a != class_id)
        fn = sum(1 for p, a in zip(predictions, actuals) if p != class_id and a == class_id)

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
    """Run automated experiments with different configurations"""
    print("Loading data...")
    training_data, test_data = load_data()
    print(f"Training samples: {len(training_data)}")
    print(f"Test samples: {len(test_data)}")

    # Experiment configurations as per practice requirements
    configurations = [
        # Base architecture: 784-100-10
        {"name": "Base_0.5_lr_3_epochs_5_batch", "layers": [784, 100, 10], "learning_rate": 0.5, "epochs": 3, "batch_size": 5},
        {"name": "Base_0.5_lr_10_epochs_5_batch", "layers": [784, 100, 10], "learning_rate": 0.5, "epochs": 10, "batch_size": 5},
        {"name": "Base_0.5_lr_50_epochs_5_batch", "layers": [784, 100, 10], "learning_rate": 0.5, "epochs": 50, "batch_size": 5},
        {"name": "Base_0.5_lr_100_epochs_5_batch", "layers": [784, 100, 10], "learning_rate": 0.5, "epochs": 100, "batch_size": 5},

        {"name": "Base_1.0_lr_3_epochs_10_batch", "layers": [784, 100, 10], "learning_rate": 1.0, "epochs": 3, "batch_size": 10},
        {"name": "Base_1.0_lr_10_epochs_10_batch", "layers": [784, 100, 10], "learning_rate": 1.0, "epochs": 10, "batch_size": 10},
        {"name": "Base_1.0_lr_50_epochs_10_batch", "layers": [784, 100, 10], "learning_rate": 1.0, "epochs": 50, "batch_size": 10},
        {"name": "Base_1.0_lr_100_epochs_10_batch", "layers": [784, 100, 10], "learning_rate": 1.0, "epochs": 100, "batch_size": 10},

        {"name": "Base_3.0_lr_3_epochs_30_batch", "layers": [784, 100, 10], "learning_rate": 3.0, "epochs": 3, "batch_size": 30},
        {"name": "Base_3.0_lr_10_epochs_30_batch", "layers": [784, 100, 10], "learning_rate": 3.0, "epochs": 10, "batch_size": 30},
        {"name": "Base_3.0_lr_50_epochs_30_batch", "layers": [784, 100, 10], "learning_rate": 3.0, "epochs": 50, "batch_size": 30},
        {"name": "Base_3.0_lr_100_epochs_30_batch", "layers": [784, 100, 10], "learning_rate": 3.0, "epochs": 100, "batch_size": 30},

        {"name": "Base_10.0_lr_3_epochs_100_batch", "layers": [784, 100, 10], "learning_rate": 10.0, "epochs": 3, "batch_size": 100},
        {"name": "Base_10.0_lr_10_epochs_100_batch", "layers": [784, 100, 10], "learning_rate": 10.0, "epochs": 10, "batch_size": 100},
        {"name": "Base_10.0_lr_50_epochs_100_batch", "layers": [784, 100, 10], "learning_rate": 10.0, "epochs": 50, "batch_size": 100},
        {"name": "Base_10.0_lr_100_epochs_100_batch", "layers": [784, 100, 10], "learning_rate": 10.0, "epochs": 100, "batch_size": 100},

        # Alternative architecture: 784-50-25-10
        {"name": "Alt_0.5_lr_3_epochs_5_batch", "layers": [784, 50, 25, 10], "learning_rate": 0.5, "epochs": 3, "batch_size": 5},
        {"name": "Alt_0.5_lr_10_epochs_5_batch", "layers": [784, 50, 25, 10], "learning_rate": 0.5, "epochs": 10, "batch_size": 5},
        {"name": "Alt_0.5_lr_50_epochs_5_batch", "layers": [784, 50, 25, 10], "learning_rate": 0.5, "epochs": 50, "batch_size": 5},
        {"name": "Alt_0.5_lr_100_epochs_5_batch", "layers": [784, 50, 25, 10], "learning_rate": 0.5, "epochs": 100, "batch_size": 5},

        {"name": "Alt_1.0_lr_3_epochs_10_batch", "layers": [784, 50, 25, 10], "learning_rate": 1.0, "epochs": 3, "batch_size": 10},
        {"name": "Alt_1.0_lr_10_epochs_10_batch", "layers": [784, 50, 25, 10], "learning_rate": 1.0, "epochs": 10, "batch_size": 10},
        {"name": "Alt_1.0_lr_50_epochs_10_batch", "layers": [784, 50, 25, 10], "learning_rate": 1.0, "epochs": 50, "batch_size": 10},
        {"name": "Alt_1.0_lr_100_epochs_10_batch", "layers": [784, 50, 25, 10], "learning_rate": 1.0, "epochs": 100, "batch_size": 10},

        {"name": "Alt_3.0_lr_3_epochs_30_batch", "layers": [784, 50, 25, 10], "learning_rate": 3.0, "epochs": 3, "batch_size": 30},
        {"name": "Alt_3.0_lr_10_epochs_30_batch", "layers": [784, 50, 25, 10], "learning_rate": 3.0, "epochs": 10, "batch_size": 30},
        {"name": "Alt_3.0_lr_50_epochs_30_batch", "layers": [784, 50, 25, 10], "learning_rate": 3.0, "epochs": 50, "batch_size": 30},
        {"name": "Alt_3.0_lr_100_epochs_30_batch", "layers": [784, 50, 25, 10], "learning_rate": 3.0, "epochs": 100, "batch_size": 30},

        {"name": "Alt_10.0_lr_3_epochs_100_batch", "layers": [784, 50, 25, 10], "learning_rate": 10.0, "epochs": 3, "batch_size": 100},
        {"name": "Alt_10.0_lr_10_epochs_100_batch", "layers": [784, 50, 25, 10], "learning_rate": 10.0, "epochs": 10, "batch_size": 100},
        {"name": "Alt_10.0_lr_50_epochs_100_batch", "layers": [784, 50, 25, 10], "learning_rate": 10.0, "epochs": 50, "batch_size": 100},
        {"name": "Alt_10.0_lr_100_epochs_100_batch", "layers": [784, 50, 25, 10], "learning_rate": 10.0, "epochs": 100, "batch_size": 100},
    ]

    results = []

    for i, config in enumerate(configurations):
        print(f"\n🔄 Running experiment {i+1}/{len(configurations)}: {config['name']}")

        # Run multiple trials (at least 100 evaluations as per requirements)
        accuracies = []
        training_times = []

        for trial in range(100):  # Run 100 trials as per practice requirements
            nn = FCNeuralNetwork(config['layers'], config['learning_rate'])
            training_time = nn.train_by_SGD(training_data, config['epochs'], config['batch_size'], config['learning_rate'])
            accuracy = nn.evaluate(test_data)

            accuracies.append(accuracy)
            training_times.append(training_time)

        # Average results
        avg_accuracy = np.mean(accuracies)
        avg_training_time = np.mean(training_times)

        # Get detailed metrics from last trial
        nn = FCNeuralNetwork(config['layers'], config['learning_rate'])
        nn.train_by_SGD(training_data, config['epochs'], config['batch_size'], config['learning_rate'])
        metrics = evaluate_metrics(nn, test_data)

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
    """Generate comprehensive Markdown report"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"automated_experiments_report_{timestamp}.md"

    with open(filename, 'w', encoding='utf-8') as f:
        f.write("# PRÁCTICA 3: REDES NEURONALES PARA RECONOCIMIENTO DE DÍGITOS\n\n")
        f.write("**Estudiante:** Galicia Rioja Angel Daniel\n")
        f.write(f"**Fecha:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        f.write("## RESUMEN EJECUTIVO\n\n")
        f.write("Este reporte presenta los resultados de experimentos automatizados con una red neuronal ")
        f.write("completamente conectada para el reconocimiento de dígitos escritos a mano. ")
        f.write("Se probaron diferentes configuraciones de parámetros para evaluar su impacto ")
        f.write("en el desempeño del sistema.\n\n")

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

            f.write("\n**Precisión por clase:**\n")
            for i, (p, r, f1) in enumerate(zip(metrics['precision_per_class'],
                                              metrics['recall_per_class'],
                                              metrics['f1_per_class'])):
                f.write(f"- Clase {i}: Precisión={p:.3f}, Recall={r:.3f}, F1={f1:.3f}\n")
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

        f.write("### Análisis de Parámetros\n\n")

        # Analyze learning rate impact
        lr_groups = {}
        for result in results:
            lr = result['config']['learning_rate']
            if lr not in lr_groups:
                lr_groups[lr] = []
            lr_groups[lr].append(result['metrics']['accuracy'])

        f.write("**Impacto de la tasa de aprendizaje:**\n")
        for lr, accuracies in lr_groups.items():
            avg_acc = np.mean(accuracies)
            f.write(f"- Tasa {lr}: Precisión promedio = {avg_acc:.3f}\n")
        f.write("\n")

        # Analyze batch size impact
        batch_groups = {}
        for result in results:
            bs = result['config']['batch_size']
            if bs not in batch_groups:
                batch_groups[bs] = []
            batch_groups[bs].append(result['metrics']['accuracy'])

        f.write("**Impacto del tamaño del lote:**\n")
        for bs, accuracies in batch_groups.items():
            avg_acc = np.mean(accuracies)
            f.write(f"- Tamaño {bs}: Precisión promedio = {avg_acc:.3f}\n")
        f.write("\n")

        # Analyze epochs impact
        epoch_groups = {}
        for result in results:
            ep = result['config']['epochs']
            if ep not in epoch_groups:
                epoch_groups[ep] = []
            epoch_groups[ep].append(result['metrics']['accuracy'])

        f.write("**Impacto del número de épocas:**\n")
        for ep, accuracies in epoch_groups.items():
            avg_acc = np.mean(accuracies)
            f.write(f"- Épocas {ep}: Precisión promedio = {avg_acc:.3f}\n")
        f.write("\n")

        f.write("---\n\n")
        f.write("*Reporte generado automáticamente por el sistema de experimentación*\n")

    print(f"📄 Report generated: {filename}")

    # Save results to JSON
    json_filename = f"automated_experiments_results_{timestamp}.json"
    with open(json_filename, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"💾 Results saved to: {json_filename}")

if __name__ == "__main__":
    print("PRACTICE 3 - AUTOMATED EXPERIMENTS FOR 10-CLASS DIGIT CLASSIFICATION")
    print("=" * 70)

    results = run_experiments()
    generate_report(results)

    print("\n🎉 All experiments completed successfully!")
