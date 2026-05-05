#
# MOBILE ROBOTS - FI-UNAM, 2026-2
# EXPERIMENTS - Actividades 3 y 4
# Isaac Jaciel Zambrano Miranda
#
# Ejecutar desde:
#   ros2_ws/src/vision/handwritten_digits/handwritten_digits/
# Comando:
#   python3 experiments.py
#
import sys
import os
import time
import random
import numpy
import csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Importar clase y dataset del archivo principal
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fc import FCNeuralNetwork, load_dataset

DATASET_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../dataset")
N_TESTS = 100   # pruebas de clasificacion por experimento
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

# -----------------------------------------------------------------------
def run_experiment(arch, epochs, batch_size, lr, training_x, training_t,
                   testing_x, testing_t, n_tests=N_TESTS):
    """Entrena la red y evalua n_tests clasificaciones aleatorias."""
    nn = FCNeuralNetwork(arch)
    t_start = time.time()
    # Suprimir salida del entrenamiento para no saturar la terminal
    _stdout = sys.stdout
    sys.stdout = open(os.devnull, 'w')
    nn.train_by_SGD(training_x, training_t, epochs, batch_size, lr)
    sys.stdout.close()
    sys.stdout = _stdout
    t_train = time.time() - t_start

    indices = random.sample(range(len(testing_x)), n_tests)
    correct = sum(
        1 for i in indices
        if numpy.linalg.norm(testing_t[i] - nn.feedforward(testing_x[i])[-1]) < 0.5
    )
    accuracy = correct / n_tests * 100.0
    return t_train, accuracy

# -----------------------------------------------------------------------
def generate_plots(results, filename):
    groups = [
        ('learning_rate', 'Tasa de aprendizaje'),
        ('epochs',        'Épocas'),
        ('batch_size',    'Tamaño de lote'),
        ('architecture',  'Arquitectura'),
    ]
    fig, axes = plt.subplots(2, 4, figsize=(20, 8))
    fig.suptitle('Experimentos - Red Neuronal FC\nIsaac Jaciel Zambrano Miranda', fontsize=13)

    for col, (param, title) in enumerate(groups):
        subset = [r for r in results if r['param'] == param]
        labels = [str(r['value']) for r in subset]
        accs   = [r['accuracy'] for r in subset]
        times  = [r['time']     for r in subset]

        # Fila 0: exactitud
        ax = axes[0][col]
        bars = ax.bar(labels, accs, color='steelblue', edgecolor='black')
        ax.set_title(title, fontsize=10)
        ax.set_ylim(0, 105)
        if col == 0:
            ax.set_ylabel('Exactitud (%)')
        for bar, v in zip(bars, accs):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                    f'{v:.1f}%', ha='center', fontsize=8)

        # Fila 1: tiempo
        ax = axes[1][col]
        bars = ax.bar(labels, times, color='tomato', edgecolor='black')
        if col == 0:
            ax.set_ylabel('Tiempo de entrenamiento (s)')
        for bar, v in zip(bars, times):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                    f'{v:.1f}s', ha='center', fontsize=8)

    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, filename)
    plt.savefig(path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Grafica guardada: {path}")

# -----------------------------------------------------------------------
def main():
    print("=" * 60)
    print("EXPERIMENTOS - Red Neuronal FC")
    print("Isaac Jaciel Zambrano Miranda")
    print("=" * 60)
    print(f"\nCargando dataset desde: {DATASET_FOLDER}")
    training_x, training_t, testing_x, testing_t = load_dataset(DATASET_FOLDER)

    results = []

    # --- Exp 1: Variar tasa de aprendizaje ---
    print("\n[1/4] Variando tasa de aprendizaje  (epochs=10, batch=30)")
    for lr in [0.5, 1.0, 3.0, 10.0]:
        print(f"  lr={lr:5.1f} ...", end=' ', flush=True)
        t, acc = run_experiment([784,30,10], 10, 30, lr,
                                training_x, training_t, testing_x, testing_t)
        print(f"Tiempo={t:6.1f}s  Exactitud={acc:.1f}%")
        results.append({'param':'learning_rate', 'value':lr, 'time':t, 'accuracy':acc})

    # --- Exp 2: Variar numero de epocas ---
    print("\n[2/4] Variando epocas  (lr=1.0, batch=30)")
    for ep in [3, 10, 50, 100]:
        print(f"  epochs={ep:3d} ...", end=' ', flush=True)
        t, acc = run_experiment([784,30,10], ep, 30, 1.0,
                                training_x, training_t, testing_x, testing_t)
        print(f"Tiempo={t:6.1f}s  Exactitud={acc:.1f}%")
        results.append({'param':'epochs', 'value':ep, 'time':t, 'accuracy':acc})

    # --- Exp 3: Variar tamano de lote ---
    print("\n[3/4] Variando tamano de lote  (lr=1.0, epochs=10)")
    for bs in [5, 10, 30, 100]:
        print(f"  batch={bs:3d} ...", end=' ', flush=True)
        t, acc = run_experiment([784,30,10], 10, bs, 1.0,
                                training_x, training_t, testing_x, testing_t)
        print(f"Tiempo={t:6.1f}s  Exactitud={acc:.1f}%")
        results.append({'param':'batch_size', 'value':bs, 'time':t, 'accuracy':acc})

    # --- Exp 4: Arquitectura diferente ---
    print("\n[4/4] Arquitecturas  (lr=1.0, epochs=10, batch=30)")
    architectures = [
        ([784, 30, 10],     '[784,30,10]'),
        ([784, 64, 32, 10], '[784,64,32,10]'),
    ]
    for arch, arch_label in architectures:
        print(f"  arch={arch_label} ...", end=' ', flush=True)
        t, acc = run_experiment(arch, 10, 30, 1.0,
                                training_x, training_t, testing_x, testing_t)
        print(f"Tiempo={t:6.1f}s  Exactitud={acc:.1f}%")
        results.append({'param':'architecture', 'value':arch_label, 'time':t, 'accuracy':acc})

    # --- Guardar CSV ---
    csv_path = os.path.join(OUTPUT_DIR, 'results.csv')
    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['param','value','time','accuracy'])
        writer.writeheader()
        writer.writerows(results)
    print(f"\nResultados guardados en: {csv_path}")

    # --- Generar graficas ---
    print("\nGenerando graficas...")
    generate_plots(results, 'results_plot.png')

    print("\n¡Experimentos completos!")
    print("Archivos generados:")
    print(f"  - results.csv")
    print(f"  - results_plot.png")

if __name__ == '__main__':
    main()
