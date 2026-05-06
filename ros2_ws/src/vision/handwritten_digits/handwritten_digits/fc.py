#
# MOBILE ROBOTS - FI-UNAM, 2026-2
# TRAINING A NEURAL NETWORK
#
# Instructions:
# Complete the code to train a fully connected neural network for
# handwritten digit recognition.
#
from time import time

import cv2
import sys
import random
import numpy
import os
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

NAME = "Emmanuel Domínguez Osio"

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
            u = numpy.dot(self.weights[i], y[i]) + self.biases[i]
            x = 1.0 / (1.0 + numpy.exp(-u))
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
        delta = (y[-1] - t)*y[-1]*(1-y[-1])
        nabla_b[-1] = delta
        nabla_w[-1] = numpy.dot(delta, y[-2].T)
        for i in range(2, len(self.weights)+1):
            delta = numpy.dot(self.weights[-i+1].T, delta)*y[-i]*(1-y[-i])
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
    labels = [[1,0,0,0,0,0,0,0,0,0], [0,1,0,0,0,0,0,0,0,0], [0,0,1,0,0,0,0,0,0,0],
                [0,0,0,1,0,0,0,0,0,0], [0,0,0,0,1,0,0,0,0,0], [0,0,0,0,0,1,0,0,0,0],
                [0,0,0,0,0,0,1,0,0,0], [0,0,0,0,0,0,0,1,0,0], [0,0,0,0,0,0,0,0,1,0],
                [0,0,0,0,0,0,0,0,0,1]]
    # labels = [[0,0,0,0], [0,0,0,1], [0,0,1,0], [0,0,1,1], [0,1,0,0],
    #             [0,1,0,1], [0,1,1,0], [0,1,1,1], [1,0,0,0], [1,0,0,1]]
    for i in range(10):
        f_data = [c/255.0 for c in open(os.path.join(folder, "data" + str(i)), "rb").read(784000)]
        images = [numpy.asarray(f_data[784*j:784*(j+1)]).reshape([784,1]) for j in range(1000)]
        label  = numpy.asarray(labels[i]).reshape([10,1])
        # label  = numpy.asarray(labels[i]).reshape([4,1])
        training_x += images[0:len(images)//2]
        training_t += [label for j in range(len(images)//2)]
        testing_x  += images[len(images)//2:len(images)]
        testing_t  += [label for j in range(len(images)//2)]
    return training_x, training_t, testing_x, testing_t

def plot_performance(results):
    """
    Plot the performance (accuracy) of the neural network across different parameter combinations.
    
    Args:
        results (dict): Dictionary containing the following keys:
            - 'epochs': list of epochs values
            - 'batch_size': list of batch size values
            - 'learning_rate': list of learning rate values
            - 'accuracy': list of accuracy values
            - 'training_time': list of training time values
    """
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Neural Network Performance Analysis\n(Handwritten Digit Recognition)', fontsize=16, fontweight='bold')
    
    # Extract unique parameter values
    unique_epochs = sorted(list(set(results['epochs'])))
    unique_batch_sizes = sorted(list(set(results['batch_size'])))
    unique_learning_rates = sorted(list(set(results['learning_rate'])))
    
    # 1. Accuracy vs Epochs (for each learning rate, averaged across batch sizes)
    ax1 = axes[0, 0]
    for lr in unique_learning_rates:
        accuracies = []
        for e in unique_epochs:
            # Average accuracy for this epoch and learning rate across all batch sizes
            batch_accs = [results['accuracy'][i] for i in range(len(results['epochs']))
                        if results['epochs'][i] == e and results['learning_rate'][i] == lr]
            if batch_accs:
                accuracies.append(numpy.mean(batch_accs))
        ax1.plot(unique_epochs, accuracies, marker='o', label=f'LR={lr}', linewidth=2)
    ax1.set_xlabel('Epochs', fontsize=11, fontweight='bold')
    ax1.set_ylabel('Accuracy', fontsize=11, fontweight='bold')
    ax1.set_title('Accuracy vs Epochs (by Learning Rate)', fontsize=12, fontweight='bold')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.set_ylim([0, 1.0])
    
    # 2. Accuracy vs Learning Rate (for each epoch, averaged across batch sizes)
    ax2 = axes[0, 1]
    for e in unique_epochs:
        accuracies = []
        for lr in unique_learning_rates:
            # Average accuracy for this learning rate and epoch across all batch sizes
            batch_accs = [results['accuracy'][i] for i in range(len(results['epochs']))
                        if results['learning_rate'][i] == lr and results['epochs'][i] == e]
            if batch_accs:
                accuracies.append(numpy.mean(batch_accs))
        ax2.plot(unique_learning_rates, accuracies, marker='s', label=f'Epochs={e}', linewidth=2)
    ax2.set_xlabel('Learning Rate', fontsize=11, fontweight='bold')
    ax2.set_ylabel('Accuracy', fontsize=11, fontweight='bold')
    ax2.set_title('Accuracy vs Learning Rate (by Epochs)', fontsize=12, fontweight='bold')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    ax2.set_ylim([0, 1.0])
    
    # 3. Accuracy vs Batch Size (for each epoch, averaged across learning rates)
    ax3 = axes[1, 0]
    for e in unique_epochs:
        accuracies = []
        for bs in unique_batch_sizes:
            # Average accuracy for this batch size and epoch across all learning rates
            lr_accs = [results['accuracy'][i] for i in range(len(results['epochs']))
                    if results['batch_size'][i] == bs and results['epochs'][i] == e]
            if lr_accs:
                accuracies.append(numpy.mean(lr_accs))
        ax3.plot(unique_batch_sizes, accuracies, marker='^', label=f'Epochs={e}', linewidth=2)
    ax3.set_xlabel('Batch Size', fontsize=11, fontweight='bold')
    ax3.set_ylabel('Accuracy', fontsize=11, fontweight='bold')
    ax3.set_title('Accuracy vs Batch Size (by Epochs)', fontsize=12, fontweight='bold')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    ax3.set_ylim([0, 1.0])
    
    # 4. Heatmap of accuracy for different parameter combinations
    ax4 = axes[1, 1]
    # Create a heatmap for the first epoch as an example
    e_idx = 0
    heatmap = numpy.zeros((len(unique_learning_rates), len(unique_batch_sizes)))
    for i, lr in enumerate(unique_learning_rates):
        for j, bs in enumerate(unique_batch_sizes):
            # Find the accuracy for this combination
            acc_vals = [results['accuracy'][k] for k in range(len(results['epochs']))
                        if results['learning_rate'][k] == lr and results['batch_size'][k] == bs 
                        and results['epochs'][k] == unique_epochs[e_idx]]
            heatmap[i, j] = numpy.mean(acc_vals) if acc_vals else 0
    
    im = ax4.imshow(heatmap, cmap='RdYlGn', aspect='auto', vmin=0, vmax=1)
    ax4.set_xticks(range(len(unique_batch_sizes)))
    ax4.set_yticks(range(len(unique_learning_rates)))
    ax4.set_xticklabels(unique_batch_sizes)
    ax4.set_yticklabels(unique_learning_rates)
    ax4.set_xlabel('Batch Size', fontsize=11, fontweight='bold')
    ax4.set_ylabel('Learning Rate', fontsize=11, fontweight='bold')
    ax4.set_title(f'Accuracy Heatmap (Epochs={unique_epochs[e_idx]})', fontsize=12, fontweight='bold')
    
    # Add text annotations to heatmap
    for i in range(len(unique_learning_rates)):
        for j in range(len(unique_batch_sizes)):
            text = ax4.text(j, i, f'{heatmap[i, j]:.2f}',
                        ha="center", va="center", color="black", fontsize=9, fontweight='bold')
    
    # Add colorbar
    cbar = plt.colorbar(im, ax=ax4)
    cbar.set_label('Accuracy', rotation=270, labelpad=20, fontweight='bold')
    
    plt.tight_layout()
    plt.show()
    
    # Print summary statistics
    print("\n" + "="*60)
    print("PERFORMANCE SUMMARY")
    print("="*60)
    max_acc_idx = numpy.argmax(results['accuracy'])
    print(f"\nBest Performance:")
    print(f"  Accuracy: {results['accuracy'][max_acc_idx]:.4f}")
    print(f"  Epochs: {results['epochs'][max_acc_idx]}")
    print(f"  Batch Size: {results['batch_size'][max_acc_idx]}")
    print(f"  Learning Rate: {results['learning_rate'][max_acc_idx]:.2f}")
    print(f"  Training Time: {results['training_time'][max_acc_idx]:.2f}s")
    
    print(f"\nWorst Performance:")
    min_acc_idx = numpy.argmin(results['accuracy'])
    print(f"  Accuracy: {results['accuracy'][min_acc_idx]:.4f}")
    print(f"  Epochs: {results['epochs'][min_acc_idx]}")
    print(f"  Batch Size: {results['batch_size'][min_acc_idx]}")
    print(f"  Learning Rate: {results['learning_rate'][min_acc_idx]:.2f}")
    print(f"  Training Time: {results['training_time'][min_acc_idx]:.2f}s")
    
    print(f"\nAverage Accuracy: {numpy.mean(results['accuracy']):.4f}")
    print(f"Average Training Time: {numpy.mean(results['training_time']):.2f}s")
    print("="*60 + "\n")

def test_network(args=None):
    print("TESTING A NEURAL NETWORK - " + NAME)
    dataset_folder = os.path.join("../dataset")
    
    training_time = 0
    tests = 100
    max_accuracy = 0
    opt_params = []
    t_times = []
    
    # Data collection for plotting
    results = {
        'epochs': [],
        'batch_size': [],
        'learning_rate': [],
        'accuracy': [],
        'training_time': []
    }
    
    epochs        = [3, 10, 50, 100]
    batch_size    = [5, 10, 30, 100]
    learning_rate = [0.5, 1.0, 3.0, 10.0]
    training_x, training_t, testing_x, testing_t = load_dataset(dataset_folder)
    for e in epochs:
        for b in batch_size:
            for l in learning_rate:
                start_time = time()
                print("\nEpochs: %d, Batch size: %d, Learning rate: %f" % (e, b, l))
                nn = FCNeuralNetwork([784,30,10])
                nn.train_by_SGD(training_x, training_t, e, b, l)
                correct = 0
                for i in range(tests):
                    img,label = testing_x[i], testing_t[i]
                    y = nn.feedforward(img)[-1]
                    if numpy.linalg.norm(label - y) < 0.5:
                        correct += 1
                end_time = time()
                training_time = end_time - start_time
                t_times.append(training_time)
                accuracy = correct/tests
                print("\nAccuracy: %f" % accuracy)
                print("Total tests: %d, Correctly classified: %d" % (tests, correct))
                print("Training time: %f s" % training_time)
                
                # Collect data for plotting
                results['epochs'].append(e)
                results['batch_size'].append(b)
                results['learning_rate'].append(l)
                results['accuracy'].append(accuracy)
                results['training_time'].append(training_time)
                
                if accuracy > max_accuracy:
                    max_accuracy = accuracy
                    opt_params = [e, b, l]

    print("\nMaximum accuracy: %f" % max_accuracy)
    print("Average training time: %f s" % (sum(t_times) / len(t_times)))
    print("Optimal parameters: Epochs: %d, Batch size: %d, Learning rate: %f" % tuple(opt_params))
    
    # Plot the results
    plot_performance(results)
    
def main(args=None):
    print("TRAINING A NEURAL NETWORK - " + NAME)
    dataset_folder = os.path.join("../dataset")
    
    epochs        = 50
    batch_size    = 5
    learning_rate = 3.0
    training_x, training_t, testing_x, testing_t = load_dataset(dataset_folder)
    nn = FCNeuralNetwork([784,30,10])
    # nn = FCNeuralNetwork([784,30,4])
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
    main()
    # test_network()
