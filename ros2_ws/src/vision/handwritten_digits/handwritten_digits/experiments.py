import sys
import time
import csv
import numpy as np
from fc import FCNeuralNetwork, load_dataset

# Parámetros a probar
learning_rates = [0.5, 1.0, 3.0, 10.0]
epochs_list = [3, 10, 50, 100]
batch_sizes = [5, 10, 30, 100]

NUM_TESTS = 100   # imágenes de prueba por configuración

def onehot_to_binary(onehot):
    """Convierte etiqueta one-hot (10,1) a código binario de 4 bits"""
    idx = np.argmax(onehot)
    bits = [(idx >> k) & 1 for k in range(4)]
    return np.array(bits).reshape(4,1)

def run_experiments(arch_name, output_neurons, training_x, training_t, testing_x, testing_t):
    results = []
    for lr in learning_rates:
        for ep in epochs_list:
            for bs in batch_sizes:
                print(f"\n--- {arch_name} | lr={lr} | ép={ep} | batch={bs} ---")
                nn = FCNeuralNetwork([784, 30, output_neurons])
                start = time.time()
                nn.train_by_SGD(training_x, training_t, ep, bs, lr)
                elapsed = time.time() - start

                # Evaluar en NUM_TESTS imágenes aleatorias
                correct = 0
                for _ in range(NUM_TESTS):
                    idx = np.random.randint(0, len(testing_x))
                    img = testing_x[idx]
                    label = testing_t[idx]
                    out = nn.feedforward(img)[-1]
                    if output_neurons == 10:
                        if np.argmax(out) == np.argmax(label):
                            correct += 1
                    else:
                        pred = (out > 0.5).astype(int).flatten()
                        true = label.flatten()
                        if np.array_equal(pred, true):
                            correct += 1
                acc = correct / NUM_TESTS * 100.0
                results.append({
                    'architecture': arch_name,
                    'learning_rate': lr,
                    'epochs': ep,
                    'batch_size': bs,
                    'time_sec': elapsed,
                    'accuracy_%': acc
                })
                print(f"  Tiempo: {elapsed:.2f}s, Precisión: {acc:.1f}%")
    return results

def main():
    train_x, train_t_10, test_x, test_t_10 = load_dataset("../dataset")
    print(f"Entrenamiento: {len(train_x)} muestras, Prueba: {len(test_x)} muestras")

    # Convertir a binario
    train_t_4 = [onehot_to_binary(t) for t in train_t_10]
    test_t_4 = [onehot_to_binary(t) for t in test_t_10]

    # Ejecutar experimentos
    results_10 = run_experiments("One-hot (10 salidas)", 10, train_x, train_t_10, test_x, test_t_10)
    results_4  = run_experiments("Binario (4 salidas)", 4, train_x, train_t_4, test_x, test_t_4)

    # Guardar CSV
    with open('resultados_practica03.csv', 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['architecture','learning_rate','epochs','batch_size','time_sec','accuracy_%'])
        writer.writeheader()
        writer.writerows(results_10)
        writer.writerows(results_4)

if __name__ == '__main__':
    main()
