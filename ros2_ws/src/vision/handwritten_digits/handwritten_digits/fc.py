#
# MOBILE ROBOTS - FI-UNAM, 2026-2
# EXPERIMENTO AUTOMATICO DE HIPERPARAMETROS
# Autor: Francisco Vera Diaz
#
# ─────────────────────────────────────────────

# ─────────────────────────────────────────────
MODO = "0-9"       # Salida 10 neuronas  →  genera resultados_experimento_0-9.csv
# MODO = "binario" # Salida 4 bits (BCD) →  genera resultados_binario.csv
# ─────────────────────────────────────────────

import random
import numpy
import os
import csv
import time

NAME = "Francisco Vera Diaz"

# ═════════════════════════════════════════════
#  RED NEURONAL (compartida por ambos modos)
# ═════════════════════════════════════════════
class FCNeuralNetwork(object):
    def __init__(self, layers, weights=None, biases=None):
        self.biases  = [numpy.random.randn(y, 1) for y in layers[1:]] if biases  is None else biases
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
        nabla_w[-1] = delta * y[-2].T
        nabla_b[-1] = delta
        for i in range(2, len(self.weights) + 1):
            delta = numpy.dot(self.weights[-i+1].T, delta) * (y[-i] * (1 - y[-i]))
            nabla_w[-i] = delta * y[-i-1].T
            nabla_b[-i] = delta
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

    def classify(self, x):
        return self.feedforward(x)[-1]


# ═════════════════════════════════════════════
#  CARGA DE DATASET
# ═════════════════════════════════════════════
def load_dataset(folder, modo):
    print(f"Cargando dataset (modo: {modo}) desde: {folder}")
    training_x, training_t, testing_x, testing_t = [], [], [], []

    if modo == "0-9":
        # ── Salida: 10 neuronas (one-hot) ────
        labels = [
            [1,0,0,0,0,0,0,0,0,0], [0,1,0,0,0,0,0,0,0,0], [0,0,1,0,0,0,0,0,0,0],
            [0,0,0,1,0,0,0,0,0,0], [0,0,0,0,1,0,0,0,0,0], [0,0,0,0,0,1,0,0,0,0],
            [0,0,0,0,0,0,1,0,0,0], [0,0,0,0,0,0,0,1,0,0], [0,0,0,0,0,0,0,0,1,0],
            [0,0,0,0,0,0,0,0,0,1]
        ]
        n_salidas = 10
    else:
        # ── Salida: 4 bits BCD (binario) ─────
        labels = [
            [0,0,0,0], [0,0,0,1], [0,0,1,0], [0,0,1,1], [0,1,0,0],
            [0,1,0,1], [0,1,1,0], [0,1,1,1], [1,0,0,0], [1,0,0,1]
        ]
        n_salidas = 4

    for i in range(10):
        path   = os.path.join(folder, "data" + str(i))
        f_data = [c / 255.0 for c in open(path, "rb").read(784000)]
        images = [numpy.asarray(f_data[784*j:784*(j+1)]).reshape([784, 1]) for j in range(1000)]
        label  = numpy.asarray(labels[i]).reshape([n_salidas, 1])
        training_x += images[0:500]
        training_t += [label] * 500
        testing_x  += images[500:1000]
        testing_t  += [label] * 500

    print(f"Dataset listo: {len(training_x)} entrenamiento | {len(testing_x)} prueba")
    return training_x, training_t, testing_x, testing_t


# ═════════════════════════════════════════════
#  EVALUACION: 100 muestras aleatorias
# ═════════════════════════════════════════════
def evaluate(nn, testing_x, testing_t, n_tests=100):
    indices = random.sample(range(len(testing_x)), n_tests)
    correct = 0
    for idx in indices:
        img, label = testing_x[idx], testing_t[idx]
        y = nn.classify(img)
        if numpy.linalg.norm(label - y) < 0.5:
            correct += 1
    return correct / n_tests * 100.0


# ═════════════════════════════════════════════
#  CONFIGURACION POR MODO
# ═════════════════════════════════════════════
def get_config(modo):
    if modo == "0-9":
        arch_list  = [[784, 30, 10], [784, 64, 10], [784, 30, 20, 10]]
        arch_names = {
            str([784, 30, 10]):     "784-30-10",
            str([784, 64, 10]):     "784-64-10",
            str([784, 30, 20, 10]): "784-30-20-10",
        }
        default_arch = [784, 30, 10]
        output_csv   = "resultados_experimento_0-9.csv"
        # ── Mejor combinacion modo 0-9 ───────
        mejor = {
            "variable":      "MEJOR_COMBINACION",
            "valor":         "lr=10.0, ep=100, batch=10, arch=784-30-10",
            "epochs":        100,
            "batch_size":    10,
            "learning_rate": 10.0,
            "architecture":  [784, 30, 10],
        }
    else:
        arch_list  = [[784, 30, 4], [784, 64, 4], [784, 30, 20, 4]]
        arch_names = {
            str([784, 30, 4]):      "784-30-4",
            str([784, 64, 4]):      "784-64-4",
            str([784, 30, 20, 4]):  "784-30-20-4",
        }
        default_arch = [784, 30, 4]
        output_csv   = "resultados_binario.csv"
        # ── Mejor combinacion modo binario ───
        mejor = {
            "variable":      "MEJOR_COMBINACION",
            "valor":         "lr=10.0, ep=100, batch=5, arch=784-30-4",
            "epochs":        100,
            "batch_size":    5,
            "learning_rate": 10.0,
            "architecture":  [784, 30, 4],
        }

    return arch_list, arch_names, default_arch, output_csv, mejor


# ═════════════════════════════════════════════
#  EXPERIMENTO PRINCIPAL
# ═════════════════════════════════════════════
def run_experiments(dataset_folder, modo):

    arch_list, arch_names, DEFAULT_ARCH, output_csv, mejor = get_config(modo)

    # ── Hiperparametros a probar ─────────────
    learning_rates = [0.5, 1.0, 3.0, 10.0]
    epochs_list    = [3, 10, 50, 100]
    batch_sizes    = [5, 10, 30, 100]

    DEFAULT_LR     = 1.0
    DEFAULT_EPOCHS = 10
    DEFAULT_BATCH  = 30

    experiments = []

    # 1. Variar learning rate
    for lr in learning_rates:
        experiments.append({
            "variable":      "learning_rate",
            "valor":         lr,
            "epochs":        DEFAULT_EPOCHS,
            "batch_size":    DEFAULT_BATCH,
            "learning_rate": lr,
            "architecture":  DEFAULT_ARCH,
        })

    # 2. Variar epocas (omite el default que ya esta en LR)
    for ep in epochs_list:
        if ep != DEFAULT_EPOCHS:
            experiments.append({
                "variable":      "epochs",
                "valor":         ep,
                "epochs":        ep,
                "batch_size":    DEFAULT_BATCH,
                "learning_rate": DEFAULT_LR,
                "architecture":  DEFAULT_ARCH,
            })

    # 3. Variar batch size (omite el default)
    for bs in batch_sizes:
        if bs != DEFAULT_BATCH:
            experiments.append({
                "variable":      "batch_size",
                "valor":         bs,
                "epochs":        DEFAULT_EPOCHS,
                "batch_size":    bs,
                "learning_rate": DEFAULT_LR,
                "architecture":  DEFAULT_ARCH,
            })

    # 4. Variar arquitectura (omite la default)
    for arch in arch_list:
        if arch != DEFAULT_ARCH:
            experiments.append({
                "variable":      "architecture",
                "valor":         arch_names[str(arch)],
                "epochs":        DEFAULT_EPOCHS,
                "batch_size":    DEFAULT_BATCH,
                "learning_rate": DEFAULT_LR,
                "architecture":  arch,
            })

    # 5. Mejor combinacion encontrada
    experiments.append(mejor)

    # ── Cargar dataset ───────────────────────
    training_x, training_t, testing_x, testing_t = load_dataset(dataset_folder, modo)

    # ── CSV ──────────────────────────────────
    fieldnames = [
        "experimento_num", "variable_modificada", "valor_variable",
        "learning_rate", "epochs", "batch_size", "architecture",
        "tiempo_entrenamiento_seg", "porcentaje_exito", "n_tests"
    ]

    total = len(experiments)
    print(f"\nMODO: {modo}  |  Total experimentos: {total}  |  CSV: {output_csv}")
    print("=" * 70)

    with open(output_csv, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for num, exp in enumerate(experiments, start=1):
            arch     = exp["architecture"]
            lr       = exp["learning_rate"]
            ep       = exp["epochs"]
            bs       = exp["batch_size"]
            var      = exp["variable"]
            val      = exp["valor"]
            arch_str = arch_names[str(arch)]

            print(f"\n[{num}/{total}] {var} = {val}"
                  f"  |  arch={arch_str}, lr={lr}, epochs={ep}, batch={bs}")

            nn = FCNeuralNetwork(arch)
            t0 = time.time()
            nn.train_by_SGD(training_x, training_t, ep, bs, lr)
            t1 = time.time()
            elapsed = round(t1 - t0, 2)

            pct = evaluate(nn, testing_x, testing_t, n_tests=100)
            print(f"  → Tiempo: {elapsed}s  |  Exito: {pct:.1f}%")

            writer.writerow({
                "experimento_num":          num,
                "variable_modificada":      var,
                "valor_variable":           val,
                "learning_rate":            lr,
                "epochs":                   ep,
                "batch_size":               bs,
                "architecture":             arch_str,
                "tiempo_entrenamiento_seg": elapsed,
                "porcentaje_exito":         round(pct, 2),
                "n_tests":                  100,
            })
            csvfile.flush()

    print("\n" + "=" * 70)
    print(f"Experimentos finalizados. Resultados guardados en: {output_csv}")


# ═════════════════════════════════════════════
#  MAIN
# ═════════════════════════════════════════════
if __name__ == "__main__":
    dataset_folder = os.path.join("..", "dataset")
    run_experiments(dataset_folder, MODO)
