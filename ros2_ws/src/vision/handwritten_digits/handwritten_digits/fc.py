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
import itertools

NAME = "Alan Michel Carrasco Meza"

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
        y.append(x)
        for i in range(len(self.weights)):
            u = numpy.dot(self.weights[i], x) + self.biases[i]
            x = 1/(1 + numpy.exp(-u))
            y.append(x)
        
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
        delta = (y[-1] - t) * y[-1]*(1-y[-1])
        nabla_b[-1] = delta
        nabla_w[-1] = delta * y[-2].T

        for i in range(2, len(self.weights) + 1):
            delta = numpy.dot(self.weights[-i+1].T, delta) * y[-i]*(1-y[-i])
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
    # labels = [[1,0,0,0,0,0,0,0,0,0], [0,1,0,0,0,0,0,0,0,0], [0,0,1,0,0,0,0,0,0,0],
    #          [0,0,0,1,0,0,0,0,0,0], [0,0,0,0,1,0,0,0,0,0], [0,0,0,0,0,1,0,0,0,0],
    #          [0,0,0,0,0,0,1,0,0,0], [0,0,0,0,0,0,0,1,0,0], [0,0,0,0,0,0,0,0,1,0],
    #          [0,0,0,0,0,0,0,0,0,1]]
    labels = [[0,0,0,0], [0,0,0,1], [0,0,1,0], [0,0,1,1], [0,1,0,0],
              [0,1,0,1], [0,1,1,0], [0,1,1,1], [1,0,0,0], [1,0,0,1]]
    for i in range(10):
        f_data = [c/255.0 for c in open(os.path.join(folder, "data" + str(i)), "rb").read(784000)]
        images = [numpy.asarray(f_data[784*j:784*(j+1)]).reshape([784,1]) for j in range(1000)]
        # label  = numpy.asarray(labels[i]).reshape([10,1])
        label  = numpy.asarray(labels[i]).reshape([4,1])
        training_x += images[0:len(images)//2]
        training_t += [label for j in range(len(images)//2)]
        testing_x  += images[len(images)//2:len(images)]
        testing_t  += [label for j in range(len(images)//2)]
    return training_x, training_t, testing_x, testing_t

def evaluate(nn, testing_x, testing_t, n_samples = 100):
    # Randomly sample n_samples from the test set and return accuracy (0-100)
    indices = random.sample(range(len(testing_x)), min(n_samples, len(testing_x)))
    correct = sum(
        1 for i in indices
        if numpy.linalg.norm(testing_t[i] - nn.feedforward(testing_x[i])[-1]) < 0.5
    )
    return 100.0 * correct / len(indices)

def run_experiments():
    # Automatically trains the network with every combination of the parameters
    # and saves results to the 'experiment_results.csv'
    learning_rates = [0.5, 1.0, 3.0, 10.0]
    epochs_list = [3, 10, 50, 100]
    batch_sizes = [5, 10, 30, 100]
    architecture = [784, 30, 4] # change to [784, 30, 4] for binary encoding
    n_test_samples = 650
    output_csv = 'experiment_results_4bits.csv'
    dataset_folder = os.path.join('../dataset')

    training_x, training_t, testing_x, testing_t = load_dataset(dataset_folder)

    combinations = list(itertools.product(learning_rates, epochs_list, batch_sizes))
    total = len(combinations)
    results = []

    # Silence the terminal output from every batch from train_by_SGD
    class _Silent:
        def write(self, *a): pass
        def flush(self): pass
    
    for idx, (lr, epochs, batch_size) in enumerate(combinations, 1):
        sys.stdout.write("[%3d/%d]  lr=%-5s  epochs=%-4d  batch=%-4d" % (idx, total, lr, epochs, batch_size))
        sys.stdout.flush()

        nn = FCNeuralNetwork(architecture)

        real_stdout, sys.stdout = sys.stdout, _Silent()
        t0 = time.time()
        nn.train_by_SGD(training_x, training_t, epochs, batch_size, lr)
        elapsed = round(time.time() - t0, 2)
        sys.stdout = real_stdout

        accuracy = round(evaluate(nn, testing_x, testing_t, n_test_samples), 1)
        print(" -> time=%8.2f[s]  accuaracy=%5.1f%%" % (elapsed, accuracy))

        results.append({
            "learning_rate": lr,
            "epochs": epochs,
            "batch_size": batch_size,
            "training_time_s": elapsed,
            "accuracy_pct": accuracy,
        })

    # Save to CSV
    fieldnames = ["learning_rate", "epochs", "batch_size", "training_time_s", "accuracy_pct"]
    with open(output_csv, "w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    
    print("\nResults saved to '%s'" % output_csv)

    best = max(results, key=lambda r: r["accuracy_pct"])
    fastest = min(results, key=lambda r: r["training_time_s"])
    print("\n===== SUMMARY =====")
    print(" Best accuracy: %.1f%%  (lr=%s, epoch=%d, batch=%d)"
          % (best["accuracy_pct"], best["learning_rate"], best["epochs"], best["batch_size"]))
    print(" Fastest train: %.2f[s] (lr=%s, epochs=%d, batch=%d)"
          % (fastest["training_time_s"], fastest["learning_rate"], fastest["epochs"], fastest["batch_size"]))
    print("==========\n")

def main(args=None):
    print("TRAINING A NEURAL NETWORK - " + NAME)
    dataset_folder = os.path.join("../dataset")
    
    epochs        = 3
    batch_size    = 50
    learning_rate = 1.0
    training_x, training_t, testing_x, testing_t = load_dataset(dataset_folder)
    # nn = FCNeuralNetwork([784,30,10])
    nn = FCNeuralNetwork([784,30,4])
    nn.train_by_SGD(training_x, training_t, epochs, batch_size, learning_rate)

    print("\nPress key to test network or ESC to exit...")
    numpy.set_printoptions(formatter={'float_kind':"{:.3f}".format})
    cmd = cv2.waitKey(0)
    while cmd != 27:
        rand_i = numpy.random.randint(0, len(testing_x))
        img,label = testing_x[rand_i], testing_t[rand_i]
        y = nn.feedforward(img)[-1]
        print("\nNN output: " + str(y.T))
        print("Expected output  : "   + str(label.T))
        print("Correctly classified: "   + str(numpy.linalg.norm(label - y) < 0.5))
        cv2.imshow("Digit", numpy.reshape(numpy.asarray(img, dtype="float32"), (28,28,1)))
        cmd = cv2.waitKey(0)

if __name__ == '__main__':
    if '--experiment' in sys.argv:
        run_experiments()
    else:
        main()
