#
# MOBILE ROBOTS - FI-UNAM, 2026-2
# PRACTICA 03 - EXPERIMENTOS AUTOMATIZADOS
#
# Actividades 4 y 5:
#   - Variacion de hiperparametros (lr, epochs, batch_size)
#   - Etiquetas one-hot vs codigo binario
#   - Registro de tiempo de entrenamiento y porcentaje de exito
#
import random
import numpy
import os
import time
import csv
from itertools import product as cartesian_product

NAME = "Allan Jair Jerónimo Zambrano"

# =============================================================================
# CLASE RED NEURONAL (sin cambios respecto a fc.py)
# =============================================================================
class FCNeuralNetwork(object):
    def __init__(self, layers, weights=None, biases=None):
        self.biases  = [numpy.random.randn(y, 1) for y in layers[1:]] \
                       if biases  is None else biases
        self.weights = [numpy.random.randn(y, x) for x, y in zip(layers[:-1], layers[1:])] \
                       if weights is None else weights

    def feedforward(self, x):
        y = [x]
        for i in range(len(self.weights)):
            u = numpy.dot(self.weights[i], y[i]) + self.biases[i]
            y.append(1.0 / (1.0 + numpy.exp(-u)))
        return y

    def backpropagate(self, x, t):
        y = self.feedforward(x)
        nabla_b = [numpy.zeros(b.shape) for b in self.biases]
        nabla_w = [numpy.zeros(w.shape) for w in self.weights]
        delta = (y[-1] - t) * y[-1] * (1 - y[-1])
        nabla_b[-1] = delta
        nabla_w[-1] = numpy.dot(delta, y[-2].T)
        for i in range(2, len(self.weights) + 1):
            delta = numpy.dot(self.weights[-i + 1].T, delta) * y[-i] * (1 - y[-i])
            nabla_b[-i] = delta
            nabla_w[-i] = numpy.dot(delta, y[-i - 1].T)
        return nabla_w, nabla_b

    def update_with_batch(self, batch, eta):
        batch_nabla_b = [numpy.zeros(b.shape) for b in self.biases]
        batch_nabla_w = [numpy.zeros(w.shape) for w in self.weights]
        M = len(batch)
        for x, t in batch:
            nabla_w, nabla_b = self.backpropagate(x, t)
            for j in range(len(nabla_w)):
                batch_nabla_w[j] += nabla_w[j] / M
                batch_nabla_b[j] += nabla_b[j] / M
        for j in range(len(self.biases)):
            self.weights[j] -= eta * batch_nabla_w[j]
            self.biases[j]  -= eta * batch_nabla_b[j]

    def train_by_SGD(self, training_x, training_t, epochs, batch_size, eta):
        training_data = list(zip(training_x, training_t))
        for j in range(epochs):
            random.shuffle(training_data)
            batches = [training_data[k:k + batch_size]
                       for k in range(0, len(training_data), batch_size)]
            for batch in batches:
                self.update_with_batch(batch, eta)
            print(f"  Epoca {j + 1}/{epochs} completada", end="\r")
        print()


# =============================================================================
# CARGA DE DATOS - ACTIVIDAD 4: etiquetas one-hot (10 neuronas de salida)
# =============================================================================
def load_dataset_onehot(folder):
    """Etiquetas one-hot: digito i -> vector de 10 elementos con 1 en posicion i."""
    labels_onehot = [
        [1,0,0,0,0,0,0,0,0,0], [0,1,0,0,0,0,0,0,0,0],
        [0,0,1,0,0,0,0,0,0,0], [0,0,0,1,0,0,0,0,0,0],
        [0,0,0,0,1,0,0,0,0,0], [0,0,0,0,0,1,0,0,0,0],
        [0,0,0,0,0,0,1,0,0,0], [0,0,0,0,0,0,0,1,0,0],
        [0,0,0,0,0,0,0,0,1,0], [0,0,0,0,0,0,0,0,0,1],
    ]
    return _load(folder, labels_onehot, out_dim=10)


# =============================================================================
# CARGA DE DATOS - ACTIVIDAD 5: etiquetas en codigo binario (4 neuronas)
# =============================================================================
def load_dataset_binary(folder):
    """
    Etiquetas en codigo binario de 4 bits:
      0->[0,0,0,0]  1->[0,0,0,1]  2->[0,0,1,0]  3->[0,0,1,1]
      4->[0,1,0,0]  5->[0,1,0,1]  6->[0,1,1,0]  7->[0,1,1,1]
      8->[1,0,0,0]  9->[1,0,0,1]
    """
    labels_binary = [
        [0,0,0,0], [0,0,0,1], [0,0,1,0], [0,0,1,1],
        [0,1,0,0], [0,1,0,1], [0,1,1,0], [0,1,1,1],
        [1,0,0,0], [1,0,0,1],
    ]
    return _load(folder, labels_binary, out_dim=4)


def _load(folder, labels_list, out_dim):
    training_x, training_t, testing_x, testing_t = [], [], [], []
    for i in range(10):
        path = os.path.join(folder, "data" + str(i))
        f_data = [c / 255.0 for c in open(path, "rb").read(784000)]
        images = [numpy.asarray(f_data[784*j:784*(j+1)]).reshape([784, 1])
                  for j in range(1000)]
        label  = numpy.asarray(labels_list[i]).reshape([out_dim, 1])
        training_x += images[:500]
        training_t += [label] * 500
        testing_x  += images[500:]
        testing_t  += [label] * 500
    return training_x, training_t, testing_x, testing_t


# =============================================================================
# CLASIFICACION
# =============================================================================
def classify_onehot(nn, x):
    """Para one-hot: la neurona con mayor activacion gana."""
    output = nn.feedforward(x)[-1]
    return int(numpy.argmax(output))

def classify_binary(nn, x):
    """Para binario: se umbraliza cada neurona en 0.5."""
    output = nn.feedforward(x)[-1]
    bits   = (output >= 0.5).astype(int).flatten()
    # Convertir bits a entero: [b3,b2,b1,b0] -> numero
    return int(bits[0]*8 + bits[1]*4 + bits[2]*2 + bits[3])

def get_true_label_onehot(t):
    return int(numpy.argmax(t))

def get_true_label_binary(t):
    bits = t.flatten().astype(int)
    return int(bits[0]*8 + bits[1]*4 + bits[2]*2 + bits[3])


# =============================================================================
# EVALUACION: 100 muestras aleatorias
# =============================================================================
def evaluate(nn, testing_x, testing_t, n_tests, classify_fn, label_fn):
    """Realiza n_tests clasificaciones aleatorias. Retorna porcentaje de exito."""
    successes = 0
    indices   = random.sample(range(len(testing_x)), min(n_tests, len(testing_x)))
    for idx in indices:
        x, t      = testing_x[idx], testing_t[idx]
        predicted = classify_fn(nn, x)
        expected  = label_fn(t)
        if predicted == expected:
            successes += 1
    return 100.0 * successes / n_tests


# =============================================================================
# EXPERIMENTO INDIVIDUAL
# =============================================================================
def run_experiment(dataset_folder, encoding, layers,
                   epochs, batch_size, lr, n_tests=100):
    """
    Entrena una red y la evalua.
    Retorna dict con tiempo de entrenamiento y porcentaje de exito.
    """
    if encoding == "onehot":
        tr_x, tr_t, te_x, te_t = load_dataset_onehot(dataset_folder)
        classify_fn = classify_onehot
        label_fn    = get_true_label_onehot
    else:  # binary
        tr_x, tr_t, te_x, te_t = load_dataset_binary(dataset_folder)
        classify_fn = classify_binary
        label_fn    = get_true_label_binary

    nn = FCNeuralNetwork(layers)

    t0 = time.time()
    nn.train_by_SGD(tr_x, tr_t, epochs, batch_size, lr)
    train_time = time.time() - t0

    success_pct = evaluate(nn, te_x, te_t, n_tests, classify_fn, label_fn)
    return {"train_time_s": round(train_time, 2),
            "success_pct":  round(success_pct, 1)}


# =============================================================================
# SUITE COMPLETA DE EXPERIMENTOS
# =============================================================================
def run_all_experiments(dataset_folder, output_csv="resultados.csv"):
    # --- Grilla de hiperparametros ---
    learning_rates = [0.5, 1.0, 3.0, 10.0]
    epochs_list    = [3, 10, 50, 100]
    batch_sizes    = [5, 10, 30, 100]
    N_TESTS        = 100

    # Configuraciones a probar
    experiments = [
        # (encoding,  layers,         descripcion)
        ("onehot", [784, 30, 10], "one-hot [784-30-10]"),
        ("onehot", [784, 50, 10], "one-hot [784-50-10]"),   # arquitectura alternativa
        ("binary", [784, 30,  4], "binario [784-30-4]"),
        ("binary", [784, 50,  4], "binario [784-50-4]"),    # arquitectura alternativa
    ]

    # Cabecera del CSV
    fieldnames = ["encoding", "arquitectura", "learning_rate",
                  "epochs", "batch_size", "tiempo_entrenamiento_s",
                  "porcentaje_exito"]

    results = []
    total = len(experiments) * len(learning_rates) * len(epochs_list) * len(batch_sizes)
    count = 0

    print(f"\n{'='*65}")
    print(f"  EXPERIMENTOS - {NAME}")
    print(f"  Total de combinaciones: {total}")
    print(f"{'='*65}\n")

    for (enc, layers, desc) in experiments:
        for lr, ep, bs in cartesian_product(learning_rates, epochs_list, batch_sizes):
            count += 1
            print(f"[{count:>3}/{total}] {desc} | lr={lr:<5} ep={ep:<4} bs={bs:<4}", end=" | ")

            result = run_experiment(
                dataset_folder, enc, layers,
                epochs=ep, batch_size=bs, lr=lr, n_tests=N_TESTS
            )
            row = {
                "encoding":               enc,
                "arquitectura":           str(layers),
                "learning_rate":          lr,
                "epochs":                 ep,
                "batch_size":             bs,
                "tiempo_entrenamiento_s": result["train_time_s"],
                "porcentaje_exito":       result["success_pct"],
            }
            results.append(row)
            print(f"Tiempo: {result['train_time_s']:>7.2f}s | "
                  f"Exito: {result['success_pct']:>5.1f}%")

    # Guardar CSV
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"\n✔  Resultados guardados en: {output_csv}")
    print_summary(results)
    return results


# =============================================================================
# RESUMEN RAPIDO
# =============================================================================
def print_summary(results):
    print(f"\n{'='*65}")
    print("  RESUMEN: Top 5 configuraciones por porcentaje de exito")
    print(f"{'='*65}")
    top5 = sorted(results, key=lambda r: -r["porcentaje_exito"])[:5]
    for i, r in enumerate(top5, 1):
        print(f"  {i}. {r['arquitectura']} ({r['encoding']}) "
              f"lr={r['learning_rate']} ep={r['epochs']} bs={r['batch_size']} "
              f"-> {r['porcentaje_exito']}% en {r['tiempo_entrenamiento_s']}s")

    print(f"\n{'='*65}")
    print("  RESUMEN: Top 5 configuraciones por tiempo de entrenamiento")
    print(f"{'='*65}")
    top5t = sorted(results, key=lambda r: r["tiempo_entrenamiento_s"])[:5]
    for i, r in enumerate(top5t, 1):
        print(f"  {i}. {r['arquitectura']} ({r['encoding']}) "
              f"lr={r['learning_rate']} ep={r['epochs']} bs={r['batch_size']} "
              f"-> {r['tiempo_entrenamiento_s']}s ({r['porcentaje_exito']}% exito)")


# =============================================================================
# EXPERIMENTO RAPIDO (modo prueba con pocos parametros)
# =============================================================================
def run_quick_test(dataset_folder):
    """
    Prueba rapida con un subconjunto de parametros.
    Util para verificar que todo funciona antes de la suite completa.
    """
    print("\n--- PRUEBA RAPIDA ---")
    configs = [
        ("onehot", [784, 30, 10], 3,  50, 1.0),
        ("binary", [784, 30,  4], 3,  50, 1.0),
    ]
    for enc, layers, ep, bs, lr in configs:
        print(f"\nConfig: {layers} | {enc} | lr={lr} | ep={ep} | bs={bs}")
        r = run_experiment(dataset_folder, enc, layers, ep, bs, lr, n_tests=100)
        print(f"  Tiempo: {r['train_time_s']}s | Exito: {r['success_pct']}%")


# =============================================================================
# MAIN
# =============================================================================
if __name__ == "__main__":
    import sys

    DATASET_FOLDER = os.path.join("..", "dataset")  # ajustar si es necesario
    OUTPUT_CSV     = "resultados_experimentos.csv"

    if not os.path.isdir(DATASET_FOLDER):
        print(f"[ERROR] No se encontro el dataset en: {DATASET_FOLDER}")
        print("        Ajusta la variable DATASET_FOLDER en este script.")
        sys.exit(1)

    # Modo de ejecucion:
    #   python3 experiments.py quick  -> prueba rapida (2 configs)
    #   python3 experiments.py full   -> suite completa (256 configs)
    mode = sys.argv[1] if len(sys.argv) > 1 else "quick"

    if mode == "full":
        run_all_experiments(DATASET_FOLDER, OUTPUT_CSV)
    else:
        run_quick_test(DATASET_FOLDER)
