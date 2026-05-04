#
# MOBILE ROBOTS - 2026-2
# TRAINING A NEURAL NETWORK
#
# Instructions:
# Complete the code to train a fully connected neural network for
# handwritten digit recognition.
#
# Etiquetas en codigo binario de 4 bits.
# La salida de la red es un vector de 4 neuronas que representa
# el digito en binario (ej: 5 -> [0,1,0,1]).
# Se repiten los experimentos de la actividad 4 con las nuevas etiquetas
# y arquitecturas congruentes (salida de 4 neuronas en lugar de 10).
#

#
#SCRIPT INDEPENDIENTE PARA RELIZAR LOS EXPERIMENTOS PARA CLASIFICACION DE NUMEROSCON CODIFICACION BINARIA
#

import sys
import random
import numpy
import os
import time
import csv
from itertools import product

NAME = "JESUS ALEXIS PEREZ LEON"


class FCNeuralNetwork(object):
    def __init__(self, layers, weights=None, biases=None):
        self.biases  = [numpy.random.randn(y, 1) for y in layers[1:]]                      if biases  is None else biases
        self.weights = [numpy.random.randn(y, x) for x, y in zip(layers[:-1], layers[1:])] if weights is None else weights

    def feedforward(self, x):
        y = [x]
        for i in range(len(self.weights)):
            u = numpy.dot(self.weights[i], x) + self.biases[i]
            x = 1.0 / (1.0 + numpy.exp(-u))
            y.append(x)
        return y

    def backpropagate(self, x, t):
        y = self.feedforward(x)
        nabla_b = [numpy.zeros(b.shape) for b in self.biases]
        nabla_w = [numpy.zeros(w.shape) for w in self.weights]
        delta = (y[-1] - t) * y[-1] * (1 - y[-1])
        nabla_b[-1] = delta
        nabla_w[-1] = numpy.dot(delta, y[-2].T)
        for i in range(2, len(self.weights) + 1):
            delta = numpy.dot(self.weights[-i+1].T, delta) * y[-i] * (1 - y[-i])
            nabla_b[-i] = delta
            nabla_w[-i] = numpy.dot(delta, y[-i-1].T)
        return nabla_w, nabla_b

    def update_with_batch(self, batch, eta):
        batch_nabla_b = [numpy.zeros(b.shape) for b in self.biases]
        batch_nabla_w = [numpy.zeros(w.shape) for w in self.weights]
        M = len(batch)
        mag_nabla = 0
        for x, t in batch:
            nabla_w, nabla_b = self.backpropagate(x, t)
            for j in range(len(nabla_w)):
                batch_nabla_w[j] += nabla_w[j] / M
                batch_nabla_b[j] += nabla_b[j] / M
        for j in range(len(nabla_b)):
            self.weights[j] = self.weights[j] - eta * batch_nabla_w[j]
            self.biases[j]  = self.biases[j]  - eta * batch_nabla_b[j]
            mag_nabla += numpy.linalg.norm(batch_nabla_w[j]) + numpy.linalg.norm(batch_nabla_b[j])
        return mag_nabla

    def train_by_SGD(self, training_x, training_t, epochs, batch_size, eta):
        training_data = list(zip(training_x, training_t))
        for j in range(epochs):
            random.shuffle(training_data)
            batches = [training_data[k:k+batch_size] for k in range(0, len(training_data), batch_size)]
            for batch in batches:
                self.update_with_batch(batch, eta)

    def evaluate(self, testing_x, testing_t, n_samples=100):
        """
        Evalua la red en n_samples muestras aleatorias.
        Criterio para codificacion BINARIA: se redondea cada neurona de salida
        al bit mas cercano (0 o 1) y se compara el vector completo con el target.
        Un ejemplo es correcto solo si TODOS los bits coinciden.
        """
        indices = random.sample(range(len(testing_x)), n_samples)
        correct = 0
        for i in indices:
            y      = self.feedforward(testing_x[i])[-1]
            y_bits = numpy.round(y).astype(int)   # umbral en 0.5 por bit
            t_bits = testing_t[i].astype(int)
            if numpy.array_equal(y_bits, t_bits):
                correct += 1
        return 100.0 * correct / n_samples


# 
#  Etiquetas = codigo binario de 4 bits
# 
def load_dataset(folder):
    print("Cargando dataset desde: " + folder)
    training_x, training_t, testing_x, testing_t = [], [], [], []

    # CAMBIO clave respecto a act. 4:
    # cada digito i se representa con su valor binario en 4 bits
    # 0->[0,0,0,0]  1->[0,0,0,1]  2->[0,0,1,0]  3->[0,0,1,1]
    # 4->[0,1,0,0]  5->[0,1,0,1]  6->[0,1,1,0]  7->[0,1,1,1]
    # 8->[1,0,0,0]  9->[1,0,0,1]
    labels = [
        [0,0,0,0], [0,0,0,1], [0,0,1,0], [0,0,1,1],
        [0,1,0,0], [0,1,0,1], [0,1,1,0], [0,1,1,1],
        [1,0,0,0], [1,0,0,1]
    ]

    for i in range(10):
        f_data = [c / 255.0 for c in open(os.path.join(folder, "data" + str(i)), "rb").read(784000)]
        images = [numpy.asarray(f_data[784*j:784*(j+1)]).reshape([784, 1]) for j in range(1000)]
        label  = numpy.asarray(labels[i]).reshape([4, 1])   # shape (4,1) en lugar de (10,1)
        training_x += images[0:len(images)//2]
        training_t += [label for _ in range(len(images)//2)]
        testing_x  += images[len(images)//2:len(images)]
        testing_t  += [label for _ in range(len(images)//2)]

    return training_x, training_t, testing_x, testing_t


# 
#  Experimentos
def run_experiments(training_x, training_t, testing_x, testing_t):

    learning_rates = [0.5, 1.0, 3.0, 10.0]
    epochs_list    = [3, 10, 50, 100]
    batch_sizes    = [5, 10, 30, 100]

    # CAMBIO: arquitecturas terminan en 4 neuronas (salida binaria de 4 bits)
    architectures = {
        "784-30-4"     : [784, 30, 4],
        "784-100-50-4" : [784, 100, 50, 4],
    }

    N_TEST_SAMPLES = 100
    results = []
    total   = len(learning_rates) * len(epochs_list) * len(batch_sizes) * len(architectures)
    done    = 0

    print("\n" + "="*70)
    print(f"  INICIANDO {total} EXPERIMENTOS  (etiquetas binarias de 4 bits)")
    print("="*70 + "\n")

    for arch_name, arch_layers in architectures.items():
        print(f"\n{'─'*70}")
        print(f"  ARQUITECTURA: {arch_name}")
        print(f"{'─'*70}")

        for lr, epochs, batch_size in product(learning_rates, epochs_list, batch_sizes):
            done += 1
            label_exp = f"lr={lr:<4} | epochs={epochs:<3} | batch={batch_size:<3}"
            sys.stdout.write(f"\r  [{done:>3}/{total}] {arch_name} | {label_exp}  -> entrenando...   ")
            sys.stdout.flush()

            nn = FCNeuralNetwork(arch_layers)
            t_start = time.time()
            nn.train_by_SGD(training_x, training_t, epochs, batch_size, lr)
            train_time = time.time() - t_start

            accuracy = nn.evaluate(testing_x, testing_t, n_samples=N_TEST_SAMPLES)

            sys.stdout.write(f"\r  [{done:>3}/{total}] {arch_name} | {label_exp}  -> {train_time:6.1f}s  acc={accuracy:5.1f}%\n")
            sys.stdout.flush()

            results.append({
                "arquitectura" : arch_name,
                "learning_rate": lr,
                "epochs"       : epochs,
                "batch_size"   : batch_size,
                "tiempo_s"     : round(train_time, 2),
                "precision_pct": round(accuracy, 1),
            })

    return results


# 
#  Guardar resultados
# 
def save_results(results, out_folder="."):
    csv_path = os.path.join(out_folder, "resultados_binario.csv")
    txt_path = os.path.join(out_folder, "resumen_binario.txt")

    fieldnames = ["arquitectura", "learning_rate", "epochs", "batch_size", "tiempo_s", "precision_pct"]
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    lines = []
    lines.append("=" * 70)
    lines.append(f"  RESUMEN EXPERIMENTOS (ETIQUETAS BINARIAS) - {NAME}")
    lines.append("=" * 70)

    architectures = list(dict.fromkeys(r["arquitectura"] for r in results))
    for arch in architectures:
        arch_results = [r for r in results if r["arquitectura"] == arch]
        lines.append(f"\n{'─'*70}")
        lines.append(f"  ARQUITECTURA: {arch}  ({len(arch_results)} experimentos)")
        lines.append(f"{'─'*70}")
        lines.append(f"  {'LR':<6} {'Epochs':<8} {'Batch':<7} {'Tiempo(s)':<12} {'Precision(%)'}")
        lines.append(f"  {'─'*6} {'─'*7} {'─'*6} {'─'*11} {'─'*12}")
        for r in sorted(arch_results, key=lambda x: -x["precision_pct"]):
            lines.append(
                f"  {r['learning_rate']:<6} {r['epochs']:<8} {r['batch_size']:<7} "
                f"{r['tiempo_s']:<12} {r['precision_pct']}"
            )
        top3 = sorted(arch_results, key=lambda x: -x["precision_pct"])[:3]
        lines.append(f"\n  TOP 3 para {arch}:")
        for i, r in enumerate(top3, 1):
            lines.append(
                f"    {i}. lr={r['learning_rate']}, epochs={r['epochs']}, "
                f"batch={r['batch_size']}  ->  {r['precision_pct']}%  ({r['tiempo_s']}s)"
            )

    best = max(results, key=lambda x: x["precision_pct"])
    lines.append(f"\n{'='*70}")
    lines.append("  MEJOR CONFIGURACION GLOBAL:")
    lines.append(
        f"  Arquitectura={best['arquitectura']} | lr={best['learning_rate']} | "
        f"epochs={best['epochs']} | batch={best['batch_size']}"
    )
    lines.append(f"  Precision: {best['precision_pct']}%   Tiempo: {best['tiempo_s']}s")
    lines.append("=" * 70)

    with open(txt_path, "w") as f:
        f.write("\n".join(lines))

    print("\n")
    print("\n".join(lines))
    print(f"\nResultados guardados en:\n  {csv_path}\n  {txt_path}")

    return csv_path, txt_path


def main():
    print("EXPERIMENTOS ACT. 5 - ETIQUETAS BINARIAS")
    print(f"Alumno: {NAME}\n")

    dataset_folder = os.path.join("../dataset")
    training_x, training_t, testing_x, testing_t = load_dataset(dataset_folder)

    results = run_experiments(training_x, training_t, testing_x, testing_t)

    out_folder = os.path.dirname(os.path.abspath(__file__))
    save_results(results, out_folder)


if __name__ == "__main__":
    main()