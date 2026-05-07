#
# MOBILE ROBOTS - FI-UNAM, 2026-2
# TRAINING A NEURAL NETWORK - ACTIVIDAD 5: ETIQUETAS BINARIAS
#
# Cambios respecto a la actividad 4:
# - Las etiquetas son código binario de 4 bits (en lugar de one-hot de 10)
# - La arquitectura de salida es [..., 4] en lugar de [..., 10]
# - El criterio de clasificación usa umbral 0.5 bit a bit (no argmax)
#
import sys
import random
import time
import numpy
import os
import csv

NAME = "Iván Daniel Romero Velázquez"

class FCNeuralNetwork(object):
    def __init__(self, layers, weights=None, biases=None):
        self.biases  = [numpy.random.randn(y,1) for y in layers[1:]]                    if biases  is None else biases
        self.weights = [numpy.random.randn(y,x) for x,y in zip(layers[:-1],layers[1:])] if weights is None else weights

    def feedforward(self, x):
        y = []
        #
        # TODO:
        # Calculate the output of each layer given the input x
        # Return an array y containg the output of each layer.
        # Remember that input x is considered as the layer zero
        # You can do the following steps:
        #
        # append x to y
        # FOR i = [0,..,L-1):
        #   u = dot product (W[i], x) + B[i]
        #   x = 1.0 / (1.0 + exp(-u)) The output of the i-th layer is the input of the next one
        #   append x to y
        #
        a = x
        y.append(a)
        for w, b in zip(self.weights, self.biases):
            u = numpy.dot(w, a) + b
            a = 1.0 / (1.0 + numpy.exp(-u))
            y.append(a)
        return y

    def backpropagate(self, x, t):
        y = self.feedforward(x)
        nabla_b = [numpy.zeros(b.shape) for b in self.biases]
        nabla_w = [numpy.zeros(w.shape) for w in self.weights]
        # TODO:
        # Return a tuple [nabla_w, nabla_b] containing the gradient of cost function J with respect to
        # each weight and bias of all the network. The gradient is calculated assuming only one training
        # example: the input 'x' and the corresponding target 't'.
        # nabla_w and nabla_b should have the same dimensions as the corresponding
        # self.weights and self.biases
        # You can calculate the gradient following these steps:
        #
        # Calculate delta for the output layer L: delta=(y[-1]-t)*y[-1]*(1-y[-1])
        # nabla_b of output layer = delta
        # nabla_w of output layer = delta*y[-2].T where y[-2].T is the transpose of the ouput vector of layer L-1
        # FOR all layers i=[2,L):
        #     delta = (W[-i+1].T * delta)*y[-i]*(1 - y[-i])
        #     where 'W[-i+1].T' is the transpose of the matrix of weights of layer -i+1 and 'y[-i]' is the output of layer -i
        #     nabla_b[-i] = delta
        #     nabla_w[-i] = delta*y[-i-1].T
        #
        delta = (y[-1] - t) * y[-1] * (1.0 - y[-1])
        nabla_b[-1] = delta
        nabla_w[-1] = numpy.dot(delta, y[-2].T)
        num_layers = len(self.weights) + 1
        for i in range(2, num_layers):
            delta = numpy.dot(self.weights[-i+1].T, delta) * y[-i] * (1.0 - y[-i])
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

    def train_by_SGD(self, training_x, training_t, epochs, batch_size, eta, verbose=True):
        training_data = list(zip(training_x, training_t))
        for j in range(epochs):
            random.shuffle(training_data)
            batches = [training_data[k:k+batch_size] for k in range(0, len(training_data), batch_size)]
            for batch in batches:
                nabla_magnitude = self.update_with_batch(batch, eta)
                if verbose:
                    sys.stdout.write("\rGradient magnitude: %f   Epoch: %d/%d   " % (nabla_magnitude, j+1, epochs))
                    sys.stdout.flush()
        if verbose:
            print("\nTraining complete.")
    #
    ### END OF CLASS
    #


def load_dataset(folder):
    """
    Carga el dataset con etiquetas en código binario de 4 bits.
    Dígito -> código binario:
      0 -> [0,0,0,0]   5 -> [0,1,0,1]
      1 -> [0,0,0,1]   6 -> [0,1,1,0]
      2 -> [0,0,1,0]   7 -> [0,1,1,1]
      3 -> [0,0,1,1]   8 -> [1,0,0,0]
      4 -> [0,1,0,0]   9 -> [1,0,0,1]
    """
    print("Loading dataset from " + folder)
    training_x, training_t, testing_x, testing_t = [], [], [], []

    # Etiquetas en código binario de 4 bits
    # labels = [[1,0,0,0,0,0,0,0,0,0], ..., [0,0,0,0,0,0,0,0,0,1]]  (actividad 4)
    labels = [
        [0,0,0,0],  # 0
        [0,0,0,1],  # 1
        [0,0,1,0],  # 2
        [0,0,1,1],  # 3
        [0,1,0,0],  # 4
        [0,1,0,1],  # 5
        [0,1,1,0],  # 6
        [0,1,1,1],  # 7
        [1,0,0,0],  # 8
        [1,0,0,1],  # 9
    ]

    for i in range(10):
        f_data = [c/255.0 for c in open(os.path.join(folder, "data" + str(i)), "rb").read(784000)]
        images = [numpy.asarray(f_data[784*j:784*(j+1)]).reshape([784,1]) for j in range(1000)]
        label  = numpy.asarray(labels[i]).reshape([4,1])   # 4 bits, no 10
        training_x += images[0:500]
        training_t += [label] * 500
        testing_x  += images[500:1000]
        testing_t  += [label] * 500

    return training_x, training_t, testing_x, testing_t


def decode_binary(output_vector, threshold=0.5):
    """
    Convierte la salida continua de 4 neuronas a bits discretos (0 o 1)
    aplicando un umbral, y decodifica el número entero correspondiente.
    Ej: [0,1,0,1] -> 5
    """
    bits = (output_vector.flatten() >= threshold).astype(int)
    value = 0
    for b in bits:
        value = (value << 1) | int(b)
    return bits, value


def evaluate(nn, testing_x, testing_t, n_tests=100, threshold=0.5):
    """
    Evalúa n_tests muestras aleatorias.
    Criterio binario: decodifica bits y compara el número entero resultante.
    """
    indices = random.sample(range(len(testing_x)), n_tests)
    correct = 0
    for i in indices:
        output = nn.feedforward(testing_x[i])[-1]
        _, pred     = decode_binary(output,          threshold)
        _, expected = decode_binary(testing_t[i],    threshold)
        if pred == expected:
            correct += 1
    return (correct / n_tests) * 100.0


def run_experiment(architecture, epochs, batch_size, eta,
                   training_x, training_t, testing_x, testing_t,
                   n_tests=100):
    nn = FCNeuralNetwork(architecture)
    t_start = time.time()
    nn.train_by_SGD(training_x, training_t, epochs, batch_size, eta, verbose=False)
    t_end = time.time()
    accuracy = evaluate(nn, testing_x, testing_t, n_tests)
    return {
        "architecture" : str(architecture),
        "epochs"       : epochs,
        "batch_size"   : batch_size,
        "learning_rate": eta,
        "train_time_s" : round(t_end - t_start, 2),
        "accuracy_pct" : round(accuracy, 1)
    }


def print_result(r):
    print(f"  Arq:{r['architecture']}  ep:{r['epochs']:3d}  bs:{r['batch_size']:3d}  "
          f"lr:{r['learning_rate']:4.1f}  |  t={r['train_time_s']:6.1f}s  "
          f"acc={r['accuracy_pct']:5.1f}%")


def save_csv(results, filename="resultados_actividad5.csv"):
    keys = ["architecture","epochs","batch_size","learning_rate","train_time_s","accuracy_pct"]
    with open(filename, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(results)
    print(f"\nResultados guardados en '{filename}'")


def main():
    print("TRAINING A NEURAL NETWORK (ETIQUETAS BINARIAS) - " + NAME)
    dataset_folder = os.path.join("../dataset")
    training_x, training_t, testing_x, testing_t = load_dataset(dataset_folder)


    print("\n--- ACTIVIDAD 5: DEMO (100 pruebas automaticas) ---")
    nn = FCNeuralNetwork([784, 30, 4])
    nn.train_by_SGD(training_x, training_t, epochs=3, batch_size=50,
                    eta=1.0, verbose=True)

    print("Realizando 100 pruebas de clasificacion...")
    correct = 0
    indices = random.sample(range(len(testing_x)), 100)
    for i in indices:
        output = nn.feedforward(testing_x[i])[-1]
        _, pred     = decode_binary(output)
        _, expected = decode_binary(testing_t[i])
        if pred == expected:
            correct += 1

    print(f"Resultados actividad 5 demo (epochs=3, batch=50, lr=1.0, arq=[784,30,4]):")
    print(f"  Correctas : {correct}/100")
    print(f"  Porcentaje: {correct}%")


    # ACTIVIDAD 4 y 5 todas las combinaciones de hiperparámetros
    # 4 lr x 4 epochs x 4 batch_size = 64 combinaciones por arquitectura
    # 2 arquitecturas = 128 experimentos en total

    print("\n========== EXPERIMENTOS ACTIVIDAD 5 ==========")

    learning_rates = [0.5, 1.0, 3.0, 10.0]
    epochs_list    = [3, 10, 50, 100]
    batch_sizes    = [5, 10, 30, 100]
    architectures  = [
        [784, 30, 4],       # arquitectura original con salida binaria
        [784, 64, 32, 4]    # arquitectura alternativa con salida binaria
    ]
    N_TESTS  = 100
    results  = []
    total    = len(architectures) * len(learning_rates) * len(epochs_list) * len(batch_sizes)
    counter  = 0

    for arch in architectures:
        print(f"\n--- Arquitectura: {arch} ---")
        for ep in epochs_list:
            for bs in batch_sizes:
                for lr in learning_rates:
                    counter += 1
                    print(f"  [{counter}/{total}] ep={ep:3d} bs={bs:3d} lr={lr:4.1f} ... ",
                          end="", flush=True)
                    r = run_experiment(arch, ep, bs, lr,
                                       training_x, training_t,
                                       testing_x, testing_t,
                                       n_tests=N_TESTS)
                    print(f"t={r['train_time_s']:6.1f}s  acc={r['accuracy_pct']:5.1f}%")
                    results.append(r)

    save_csv(results)

    best = max(results, key=lambda r: r["accuracy_pct"])
    print("\n--- MEJOR CONFIGURACION ---")
    print_result(best)


if __name__ == '__main__':
    main()
