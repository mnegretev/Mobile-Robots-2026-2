#
# MOBILE ROBOTS - FI-UNAM, 2026-2
# TRAINING A NEURAL NETWORK (BINARY CLASSIFICATION)
#
# Oscar Saldivar Pantoja
#
import cv2
import sys
import random
import numpy
import os
import time
import csv

NAME = "Oscar Saldivar Pantoja"

class FCNeuralNetwork(object):
    def __init__(self, layers, weights=None, biases=None):
        self.biases =[numpy.random.randn(y,1) for y in layers[1:]] if biases == None else biases
        self.weights=[numpy.random.randn(y,x) for x,y in zip(layers[:-1],layers[1:])] if weights==None else weights
        
    def feedforward(self, x):
        y = []
        y.append(x)
        for b, w in zip(self.biases, self.weights):
            u = numpy.dot(w, x) + b
            x = 1.0 / (1.0 + numpy.exp(-u))
            y.append(x)
        return y

    def backpropagate(self, x, t):
        y = self.feedforward(x)
        nabla_b = [numpy.zeros(b.shape) for b in self.biases]
        nabla_w = [numpy.zeros(w.shape) for w in self.weights]
        
        delta = (y[-1] - t) * y[-1] * (1 - y[-1])
        nabla_b[-1] = delta
        nabla_w[-1] = numpy.dot(delta, y[-2].transpose())
        
        for i in range(2, len(y)):
            delta = numpy.dot(self.weights[-i+1].transpose(), delta) * y[-i] * (1 - y[-i])
            nabla_b[-i] = delta
            nabla_w[-i] = numpy.dot(delta, y[-i-1].transpose())
        
        return nabla_w, nabla_b

    def update_with_batch(self, batch, eta):
        batch_nabla_b = [numpy.zeros(b.shape) for b in self.biases]
        batch_nabla_w = [numpy.zeros(w.shape) for w in self.weights]
        M = len(batch)
        mag_nabla = 0
        for x,t in batch:
            nabla_w, nabla_b = self.backpropagate(x,t)
            for j in range(len(nabla_w)):
                batch_nabla_w[j] += nabla_w[j]/M
                batch_nabla_b[j] += nabla_b[j]/M
        for j in range(len(nabla_b)):
            self.weights[j] = self.weights[j] - eta*batch_nabla_w[j]
            self.biases[j]  = self.biases[j]  - eta*batch_nabla_b[j]
            mag_nabla += numpy.linalg.norm(batch_nabla_w[j]) + numpy.linalg.norm(batch_nabla_b[j])
        return mag_nabla

    def train_by_SGD(self, training_x, training_t, epochs, batch_size, eta):
        training_data = list(zip(training_x, training_t))
        for j in range(epochs):
            random.shuffle(training_data)
            batches = [training_data[k:k+batch_size] for k in range(0,len(training_data), batch_size)]
            for batch in batches:
                nabla_magnitude = self.update_with_batch(batch, eta)
                sys.stdout.write("\rGradient magnitude: %f            " % (nabla_magnitude))
                sys.stdout.flush()
            print("Epoch: " + str(j))

def load_dataset(folder):
    print("Loading data set from " + folder)
    training_x, training_t, testing_x, testing_t = [],[],[],[]
    
    # PUNTO 5: Etiquetas en código binario (4 bits)
    # Representan los dígitos del 0 al 9 en binario
    labels = [[0,0,0,0], [0,0,0,1], [0,0,1,0], [0,0,1,1], [0,1,0,0],
              [0,1,0,1], [0,1,1,0], [0,1,1,1], [1,0,0,0], [1,0,0,1]]
    
    for i in range(10):
        f_data = [c/255.0 for c in open(os.path.join(folder, "data" + str(i)), "rb").read(784000)]
        images = [numpy.asarray(f_data[784*j:784*(j+1)]).reshape([784,1]) for j in range(1000)]
        
        # AJUSTE: El label ahora es un vector de dimensión 4
        label = numpy.asarray(labels[i]).reshape([4,1])
        
        training_x += images[0:len(images)//2]
        training_t += [label for j in range(len(images)//2)]
        testing_x  += images[len(images)//2:len(images)]
        testing_t  += [label for j in range(len(images)//2)]
    return training_x, training_t, testing_x, testing_t

def main(args=None):
    print("TRAINING A NEURAL NETWORK (BINARY MODE) - " + NAME)
    dataset_folder = os.path.join("../dataset")
    training_x, training_t, testing_x, testing_t = load_dataset(dataset_folder)

    # Parámetros para las pruebas de desempeño
    learning_rates = [0.5, 1.0, 3.0, 10.0]
    epochs_list    = [3, 10, 50, 100]
    batch_sizes    = [5, 10, 30, 100]

    filename = "resultados_binarios.csv"

    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Learning Rate", "Epochs", "Batch Size", "Training Time (s)", "Success Rate (%)"])

        for eta in learning_rates:
            for ep in epochs_list:
                for bs in batch_sizes:
                    print(f"\nEntrenando Binario: eta={eta}, epochs={ep}, batch={bs}")
                    
                    # AJUSTE: Arquitectura con 4 neuronas de salida[cite: 2]
                    nn = FCNeuralNetwork([784, 30, 4])
                    
                    start_time = time.time()
                    nn.train_by_SGD(training_x, training_t, ep, bs, eta)
                    end_time = time.time()
                    training_time = end_time - start_time

                    # 100 pruebas de clasificación[cite: 2]
                    successes = 0
                    for _ in range(100):
                        rand_i = numpy.random.randint(0, len(testing_x))
                        img, label = testing_x[rand_i], testing_t[rand_i]
                        y = nn.feedforward(img)[-1]
                        
                        # Clasificación binaria: umbral de 0.5 para cada bit
                        prediction = (y > 0.5).astype(int)
                        if numpy.array_equal(prediction, label):
                            successes += 1
                    
                    writer.writerow([eta, ep, bs, f"{training_time:.2f}", successes])
                    print(f" -> Tiempo: {training_time:.2f}s, Éxito: {successes}%")

    print(f"\nPruebas binarias completadas. Datos en {filename}")

if __name__ == '__main__':
    main()