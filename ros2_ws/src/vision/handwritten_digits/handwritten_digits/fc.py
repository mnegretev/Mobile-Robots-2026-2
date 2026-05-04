#
# MOBILE ROBOTS - 2026-2
# TRAINING A NEURAL NETWORK
#
# Instructions:
# Complete the code to train a fully connected neural network for
# handwritten digit recognition.
#
import sys
import random
import numpy
import os
import time
import cv2
from itertools import product

NAME = "JESUS ALEXIS PEREZ LEON"

# ##############################################################################
# CONFIGURA(COMENTAR Y DESCOMENTAR) SEGUN LO QUE SE REQUIERA PROBAR
# parametros (EPOCA, LOTE, TASA DE APRENDIZAJE)
epochs        = 50
batch_size    = 5
learning_rate = 0.5

# ARQUITECTURA

ARCH = [784, 30,  10]            # una capa oculta   — one-hot
#ARCH = [784, 100, 50, 10]      # dos capas ocultas — one-hot
#ARCH = [784, 30,  4]           # una capa oculta   — binario
#ARCH = [784, 100, 50, 4]       # dos capas ocultas — binario

# ELEJIR CLASIFICACION DECIMAL O BINARIA
ENCODING = "onehot"
#ENCODING = "binary"
# ##############################################################################


class FCNeuralNetwork(object):
    def __init__(self, layers, weights=None, biases=None):
        self.biases  = [numpy.random.randn(y,1) for y in layers[1:]]                    if biases  is None else biases
        self.weights = [numpy.random.randn(y,x) for x,y in zip(layers[:-1],layers[1:])] if weights is None else weights

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
                nabla_magnitude = self.update_with_batch(batch, eta)
                sys.stdout.write("\rGradient magnitude: %f            " % nabla_magnitude)
                sys.stdout.flush()
            print("Epoch: " + str(j))
    ### END OF CLASS


def load_dataset(folder, encoding):
    print("Loading dataset from " + folder + "  [encoding=" + encoding + "]")
    training_x, training_t, testing_x, testing_t = [], [], [], []

    if encoding == "onehot":
        # Salida: 10 neuronas, solo una activa
        labels = [
            [1,0,0,0,0,0,0,0,0,0], [0,1,0,0,0,0,0,0,0,0], [0,0,1,0,0,0,0,0,0,0],
            [0,0,0,1,0,0,0,0,0,0], [0,0,0,0,1,0,0,0,0,0], [0,0,0,0,0,1,0,0,0,0],
            [0,0,0,0,0,0,1,0,0,0], [0,0,0,0,0,0,0,1,0,0], [0,0,0,0,0,0,0,0,1,0],
            [0,0,0,0,0,0,0,0,0,1]
        ]
        label_size = 10
    else:  # binary
        # Salida: 4 neuronas con el valor binario del digito
        labels = [
            [0,0,0,0], [0,0,0,1], [0,0,1,0], [0,0,1,1],
            [0,1,0,0], [0,1,0,1], [0,1,1,0], [0,1,1,1],
            [1,0,0,0], [1,0,0,1]
        ]
        label_size = 4

    for i in range(10):
        f_data = [c / 255.0 for c in open(os.path.join(folder, "data" + str(i)), "rb").read(784000)]
        images = [numpy.asarray(f_data[784*j:784*(j+1)]).reshape([784,1]) for j in range(1000)]
        label  = numpy.asarray(labels[i]).reshape([label_size, 1])
        training_x += images[0:len(images)//2]
        training_t += [label for _ in range(len(images)//2)]
        testing_x  += images[len(images)//2:len(images)]
        testing_t  += [label for _ in range(len(images)//2)]

    return training_x, training_t, testing_x, testing_t


def classify(y, label, encoding):
    """Devuelve True si la salida y coincide con label segun la codificacion."""
    if encoding == "onehot":
        # Neurona con mayor activacion == indice esperado
        return numpy.argmax(y) == numpy.argmax(label)
    else:  # binary
        # Cada bit de salida se redondea; todos deben coincidir
        y_bits = numpy.round(y).astype(int)
        t_bits = label.astype(int)
        return numpy.array_equal(y_bits, t_bits)


def main():
    # Validar que arquitectura y codificacion sean congruentes
    output_size = ARCH[-1]
    expected_output = 10 if ENCODING == "onehot" else 4
    if output_size != expected_output:
        print("ERROR: La arquitectura termina en %d neuronas pero la codificacion '%s' requiere %d."
              % (output_size, ENCODING, expected_output))
        print("Revisa el bloque de CONFIGURACION al inicio del archivo.")
        return

    print("TRAINING A NEURAL NETWORK - " + NAME)
    print("Arquitectura : " + str(ARCH))
    print("Codificacion : " + ENCODING)
    print("Epochs=%d  |  Batch=%d  |  LR=%.1f\n" % (epochs, batch_size, learning_rate))

    dataset_folder = os.path.join("../dataset")
    training_x, training_t, testing_x, testing_t = load_dataset(dataset_folder, ENCODING)

    nn = FCNeuralNetwork(ARCH)
    nn.train_by_SGD(training_x, training_t, epochs, batch_size, learning_rate)

    print("\nPress key to test network or ESC to exit...")
    numpy.set_printoptions(formatter={'float_kind': "{:.3f}".format})
    cmd = cv2.waitKey(0)
    while cmd != 27:
        rand_i = numpy.random.randint(0, len(testing_x))
        img, label = testing_x[rand_i], testing_t[rand_i]
        y = nn.feedforward(img)[-1]

        print("\nNN output       : " + str(y.T))
        print("Expected output : " + str(label.T))

        if ENCODING == "binary":
            print("Bits redondeados: " + str(numpy.round(y).astype(int).T))

        print("Correctly classified: " + str(classify(y, label, ENCODING)))
        cv2.imshow("Digit", numpy.reshape(numpy.asarray(img, dtype="float32"), (28, 28, 1)))
        cmd = cv2.waitKey(0)


if __name__ == '__main__':
    main()