#
# MOBILE ROBOTS - FI-UNAM, 2026-2
# EXPERIMENTS - Actividad 5: etiquetas binarias
# Isaac Jaciel Zambrano Miranda
#
# Ejecutar desde:
#   ros2_ws/src/vision/handwritten_digits/handwritten_digits/
# Comando:
#   python3 experiments_binary.py
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

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fc import FCNeuralNetwork

DATASET_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../dataset")
N_TESTS = 100
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

# -----------------------------------------------------------------------
def load_dataset_binary(folder):
    """Dataset con etiquetas en codigo binario de 4 bits (actividad 5)."""
    print("Loading dataset (binary labels) from " + folder)
    training_x, training_t, testing_x, testing_t = [], [], [], []
    labels = [
        [0,0,0,0], [0,0,0,1], [0,0,1,0], [0,0,1,1],
        [0,1,0,0], [0,1,0,1], [0,1,1,0], [0,1,1,1],
        [1,0,0,0], [1,0,0,1]
    ]
    for i in range(10):
        f_data = [c/255.0 for c in open(os.path.join(folder, "data" + str(i)), "rb").read(784000)]
        images = [numpy.asarray(f_data[784*j:784*(j+1)]).reshape([784,1]) for j in range(1000)]
        label  = numpy.asarray(labels[i]).reshape([4,1])
        training_x += images[0:len(images)//2]
        training_t += [label for _ in range(len(images)//2)]
        testing_x  += images[len(images)//2:len(images)]
        testing_t  += [label for _ in range(len(images)//2)]
    return training_x, training_t, testing_x, testing_t

# -----------------------------------------------------------------------
def run_experiment_binary(arch, epochs, batch_size, lr,
                          training_x, training_t, testing_x, testing_t):
    nn = FCNeuralNetwork(arch)
    t_start = time.time()
    _stdout = sys.stdout
    sys.stdout = open(os.devnull, 'w')
    nn.train_by_SGD(training_x, training_t, epochs, batch_size, lr)
    sys.stdout.close()
    sys.stdout = _stdout
    t_train = time.time() - t_start

    indices = random.sample(range(len(testing_x)), N_TESTS)
    correct = sum(
        1 for i in indices
        if numpy.linalg.norm(testing_t[i] - nn.feedforward(testing_x[i])[-1]) < 0.5
    )
    accuracy = correct / N_TESTS * 100.0
    return t_train, accuracy

# -----------------------------------------------------------------------
def generate_plots_binary(results, filename):
    groups = [
        ('learning_rate', 'Tasa de aprendizaje'),
        ('epochs',        'Épocas'),
        ('batch_size',    'Tamaño de lote'),
        ('architecture',  'Arquitectura'),
    ]
    fig, axes = plt.subplots(2, 4, figsize=(20, 8))
    fig.suptitle('Experimentos - Red Neuronal FC (Etiquetas Binarias)\nIsaac Jaciel Zambrano Miranda',
                 fontsize=13)

    for col, (param, title) in enumerate(groups):
        subset = [r for r in results if r['param'] == param]
        labels = [str(r['value']) for r in subset]
        accs   = [r['accuracy']  for r in subset]
        times  = [r['time']      for r in subset]

        ax = axes[0][col]
        bars = ax.bar(labels, accs, color='mediumseagreen', edgecolor='black')
        ax.set_title(title, fontsize=10)
        ax.set_ylim(0, 105)
        if col == 0:
            ax.set_ylabel('Exactitud (%)')
        for bar, v in zip(bars, accs):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                    f'{v:.1f}%', ha='center', fontsize=8)

        ax = axes[1][col]
        bars = ax.bar(labels, times, color='darkorange', edgecolor='black')
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
    print("EXPERIMENTOS BINARIOS - Actividad 5")
    print("Isaac Jaciel Zambrano Miranda")
    print("=" * 60)
    training_x, training_t, testing_x, testing_t = load_dataset_binary(DATASET_FOLDER)

    results = []

    print("\n[1/4] Variando tasa de aprendizaje  (arch=[784,30,4], epochs=10, batch=30)")
    for lr in [0.5, 1.0, 3.0, 10.0]:
        print(f"  lr={lr:5.1f} ...", end=' ', flush=True)
        t, acc = run_experiment_binary([784,30,4], 10, 30, lr,
                                       training_x, training_t, testing_x, testing_t)
        print(f"Tiempo={t:6.1f}s  Exactitud={acc:.1f}%")
        results.append({'param':'learning_rate', 'value':lr, 'time':t, 'accuracy':acc})

    print("\n[2/4] Variando epocas  (arch=[784,30,4], lr=1.0, batch=30)")
    for ep in [3, 10, 50, 100]:
        print(f"  epochs={ep:3d} ...", end=' ', flush=True)
        t, acc = run_experiment_binary([784,30,4], ep, 30, 1.0,
                                       training_x, training_t, testing_x, testing_t)
        print(f"Tiempo={t:6.1f}s  Exactitud={acc:.1f}%")
        results.append({'param':'epochs', 'value':ep, 'time':t, 'accuracy':acc})

    print("\n[3/4] Variando tamano de lote  (arch=[784,30,4], lr=1.0, epochs=10)")
    for bs in [5, 10, 30, 100]:
        print(f"  batch={bs:3d} ...", end=' ', flush=True)
        t, acc = run_experiment_binary([784,30,4], 10, bs, 1.0,
                                       training_x, training_t, testing_x, testing_t)
        print(f"Tiempo={t:6.1f}s  Exactitud={acc:.1f}%")
        results.append({'param':'batch_size', 'value':bs, 'time':t, 'accuracy':acc})

    print("\n[4/4] Arquitecturas  (lr=1.0, epochs=10, batch=30)")
    architectures = [
        ([784, 30, 4],     '[784,30,4]'),
        ([784, 64, 32, 4], '[784,64,32,4]'),
    ]
    for arch, arch_label in architectures:
        print(f"  arch={arch_label} ...", end=' ', flush=True)
        t, acc = run_experiment_binary(arch, 10, 30, 1.0,
                                       training_x, training_t, testing_x, testing_t)
        print(f"Tiempo={t:6.1f}s  Exactitud={acc:.1f}%")
        results.append({'param':'architecture', 'value':arch_label, 'time':t, 'accuracy':acc})

    csv_path = os.path.join(OUTPUT_DIR, 'results_binary.csv')
    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['param','value','time','accuracy'])
        writer.writeheader()
        writer.writerows(results)
    print(f"\nResultados guardados en: {csv_path}")

    print("\nGenerando graficas...")
    generate_plots_binary(results, 'results_binary_plot.png')

    print("\n¡Experimentos binarios completos!")
    print("Archivos generados:")
    print(f"  - results_binary.csv")
    print(f"  - results_binary_plot.png")

if __name__ == '__main__':
    main()
