#
# MOBILE ROBOTS - FI-UNAM, 2026-2
# TRAINING A NEURAL NETWORK
#
# Instructions:
# Complete the code to train a fully connected neural network for
# handwritten digit recognition.
#
import cv2
import sys
import random
import numpy
import os
import time
import csv

NAME = "Gonzalez Fernandez Jonathan Uriel"

class FCNeuralNetwork(object):
    def __init__(self, layers, weights=None, biases=None):
        #
        # The list 'layers' indicates the number of neurons in each layer.
        # Remember that the first layer indicates the input dimension. 
        # All weights and biases are initialized with random values. In each layer (except the first one)
        # we have a matrix of weights where row j contains all the weights of the j-th neuron in that layer,
        # and a vector of biases.
        #
        self.biases =[numpy.random.randn(y,1) for y in layers[1:]] if biases == None else biases
        self.weights=[numpy.random.randn(y,x) for x,y in zip(layers[:-1],layers[1:])] if weights==None else weights
        
    def feedforward(self, x):
        y = []
        y.append(x) # Paso inicial: guardar la entrada como la capa 0
        for i in range(len(self.weights)):
            # Cálculo de la entrada ponderada (u)
            u = numpy.dot(self.weights[i], x) + self.biases[i]
            # Activación sigmoide
            x = 1.0 / (1.0 + numpy.exp(-u))
            # Guardar la activación de esta capa
            y.append(x)
        
        return y

    def backpropagate(self, x, t):
        y = self.feedforward(x)
        nabla_b = [numpy.zeros(b.shape) for b in self.biases]
        nabla_w = [numpy.zeros(w.shape) for w in self.weights]
        
        # 1. Cálculo de delta para la capa de salida (L)
        delta = (y[-1] - t) * y[-1] * (1 - y[-1])
        nabla_b[-1] = delta
        nabla_w[-1] = numpy.dot(delta, y[-2].T) # Nota: el producto externo
        
        # 2. Bucle para las capas ocultas (retropropagación)
        for i in range(2, len(self.weights) + 1):
            # Delta de la capa oculta
            delta = numpy.dot(self.weights[-i+1].T, delta) * y[-i] * (1 - y[-i])
            nabla_b[-i] = delta
            nabla_w[-i] = numpy.dot(delta, y[-i-1].T)
        
        return nabla_w, nabla_b

    def update_with_batch(self, batch, eta):
        #
        # This function exectutes gradient descend for the subset of examples
        # given by 'batch' with learning rate 'eta'
        # 'batch' is a list of training examples [(x,t), ..., (x,t)]
        # Function returns the magnitude of calculated gradient 
        #
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
        #
        # This function implements the Stochastic Gradient Descend
        #
        training_data = list(zip(training_x, training_t))
        for j in range(epochs):
            random.shuffle(training_data)
            batches = [training_data[k:k+batch_size] for k in range(0,len(training_data), batch_size)]
            for batch in batches:
                nabla_magnitude = self.update_with_batch(batch, eta)
                sys.stdout.write("\rGradient magnitude: %f            " % (nabla_magnitude))
                sys.stdout.flush()
            print("Epoch: " + str(j))
    #
    ### END OF CLASS
    #


def load_dataset(folder):
    print("Loading data set from " + folder)
    training_x, training_t, testing_x, testing_t = [],[],[],[]
    
    # ETIQUETAS BINARIAS (Descomentadas)
    labels = [[0,0,0,0], [0,0,0,1], [0,0,1,0], [0,0,1,1], [0,1,0,0],
              [0,1,0,1], [0,1,1,0], [0,1,1,1], [1,0,0,0], [1,0,0,1]]
              
    for i in range(10):
        f_data = [c/255.0 for c in open(os.path.join(folder, "data" + str(i)), "rb").read(784000)]
        images = [numpy.asarray(f_data[784*j:784*(j+1)]).reshape([784,1]) for j in range(1000)]
        
        # EL TAMAÑO AHORA ES 4, NO 10
        label  = numpy.asarray(labels[i]).reshape([4,1])
        
        training_x += images[0:len(images)//2]
        training_t += [label for j in range(len(images)//2)]
        testing_x  += images[len(images)//2:len(images)]
        testing_t  += [label for j in range(len(images)//2)]
    return training_x, training_t, testing_x, testing_t

def main(args=None):
    print("INICIANDO AUTOMATIZACIÓN DE EXPERIMENTOS (BINARIO) - " + NAME)
    dataset_folder = os.path.join("../dataset")
    training_x, training_t, testing_x, testing_t = load_dataset(dataset_folder)
    
    learning_rates = [0.5, 1.0, 3.0, 10.0]
    epochs_list    = [3, 10, 50, 100]
    batch_sizes    = [5, 10, 30, 100]

    # NUEVO ARCHIVO CSV PARA NO BORRAR EL ANTERIOR
    with open('resultados_p3_binario.csv', mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Tasa_Aprendizaje', 'Epocas', 'Lote', 'Tiempo_Segundos', 'Exito_Porcentaje'])

        for lr in learning_rates:
            for ep in epochs_list:
                for bs in batch_sizes:
                    print(f"\n[+] Entrenando Binario: LR={lr} | Epocas={ep} | Lote={bs}")
                    
                    # NUEVA ARQUITECTURA: 4 NEURONAS DE SALIDA
                    nn = FCNeuralNetwork([784, 30, 4])
                    
                    start_time = time.time()
                    nn.train_by_SGD(training_x, training_t, ep, bs, lr)
                    end_time = time.time()
                    train_time = end_time - start_time
                    
                    correct_classifications = 0
                    total_tests = len(testing_x)
                    
                    for i in range(total_tests):
                        img, label = testing_x[i], testing_t[i]
                        y = nn.feedforward(img)[-1]
                        
                        # NUEVA EVALUACIÓN: Distancia entre vectores < 0.5
                        if numpy.linalg.norm(label - y) < 0.5:
                            correct_classifications += 1
                            
                    success_rate = (correct_classifications / total_tests) * 100.0
                    print(f"-> Tiempo: {train_time:.2f} s | Éxito: {success_rate:.2f}%")
                    
                    writer.writerow([lr, ep, bs, round(train_time, 2), round(success_rate, 2)])
                    file.flush()

    print("\nExperimentos BINARIOS finalizados. Revisa 'resultados_p3_binario.csv'.")

if __name__ == '__main__':
    main()
