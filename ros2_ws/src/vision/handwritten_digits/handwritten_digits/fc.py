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
import csv
import time
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np


NAME = "Guerra Sanchez Juan"

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
            x = 1.0/(1.0 + numpy.exp(-u))
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
        delta = (y[-1] -t) * y[-1] * (1 - y[-1])
        nabla_w[-1] = numpy.dot(delta, y[-2].T)
        nabla_b[-1] = delta
        for i in range(2, len(self.weights) + 1):
            delta = numpy.dot(self.weights[-i+1].T, delta) * (y[-i] * (1 - y[-i]))
            nabla_w[-i] = numpy.dot(delta, y[-i-1].T)
            nabla_b[-i] = delta
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

def save_experiment_results(filename, params, results):
   
    file_exists = False
    try:
        with open(filename, 'r') as f:
            file_exists = True
    except FileNotFoundError:
        pass
    
    row = {
        'arquitectura': params.get('arquitectura', '784-30-10'),
        'tipo_etiqueta': params.get('tipo_etiqueta', 'one_hot'),
        'learning_rate': params.get('learning_rate'),
        'epochs': params.get('epochs'),
        'batch_size': params.get('batch_size'),
        'tiempo_entrenamiento_seg': results.get('tiempo', 0),
        'precision_porcentaje': results.get('precision', 0),
        'aciertos': results.get('aciertos', 0),
        'pruebas_realizadas': results.get('total_pruebas', 100)
    }
    
    with open(filename, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=row.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)
    print(f"Resultados guardados en {filename}")

def load_dataset(folder):
    print("Loading data set from " + folder)
    training_x, training_t, testing_x, testing_t = [],[],[],[]
    labels = [[1,0,0,0,0,0,0,0,0,0], [0,1,0,0,0,0,0,0,0,0], [0,0,1,0,0,0,0,0,0,0],
              [0,0,0,1,0,0,0,0,0,0], [0,0,0,0,1,0,0,0,0,0], [0,0,0,0,0,1,0,0,0,0],
              [0,0,0,0,0,0,1,0,0,0], [0,0,0,0,0,0,0,1,0,0], [0,0,0,0,0,0,0,0,1,0],
              [0,0,0,0,0,0,0,0,0,1]]
    # labels = [[0,0,0,0], [0,0,0,1], [0,0,1,0], [0,0,1,1], [0,1,0,0],
    #           [0,1,0,1], [0,1,1,0], [0,1,1,1], [1,0,0,0], [1,0,0,1]]
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
    
def load_dataset_binary(folder):
    """
    Carga el dataset pero con etiquetas en código binario de 4 bits
    """
    print("Loading data set with BINARY labels from " + folder)
    training_x, training_t, testing_x, testing_t = [],[],[],[]
    
    # Código binario de 4 bits para dígitos 0-9
    labels_binary = [
        [0,0,0,0],  # 0
        [0,0,0,1],  # 1
        [0,0,1,0],  # 2
        [0,0,1,1],  # 3
        [0,1,0,0],  # 4
        [0,1,0,1],  # 5
        [0,1,1,0],  # 6
        [0,1,1,1],  # 7
        [1,0,0,0],  # 8
        [1,0,0,1]   # 9
    ]
    
    for i in range(10):
        f_data = [c/255.0 for c in open(os.path.join(folder, "data" + str(i)), "rb").read(784000)]
        images = [numpy.asarray(f_data[784*j:784*(j+1)]).reshape([784,1]) for j in range(1000)]
        label = numpy.asarray(labels_binary[i]).reshape([4,1])  # 4 bits en lugar de 10
        training_x += images[0:len(images)//2]
        training_t += [label for j in range(len(images)//2)]
        testing_x  += images[len(images)//2:len(images)]
        testing_t  += [label for j in range(len(images)//2)]
    
    return training_x, training_t, testing_x, testing_t

def run_experiment(arquitectura, training_x, training_t, testing_x, testing_t, 
                   epochs, batch_size, learning_rate, tipo_etiqueta="one_hot", 
                   num_pruebas=100):
    """
    Ejecuta un experimento con parámetros específicos y retorna tiempo y precisión
    """
    print(f"\n--- Experimento: LR={learning_rate}, Epochs={epochs}, Batch={batch_size}, Arquitectura={arquitectura} ---")
    
    # Crear y entrenar la red
    nn = FCNeuralNetwork(arquitectura)
    
    start_time = time.time()
    nn.train_by_SGD(training_x, training_t, epochs, batch_size, learning_rate)
    end_time = time.time()
    tiempo = end_time - start_time
    
    # Probar la red con num_pruebas imágenes aleatorias
    aciertos = 0
    for _ in range(num_pruebas):
        rand_i = numpy.random.randint(0, len(testing_x))
        img, label = testing_x[rand_i], testing_t[rand_i]
        y = nn.feedforward(img)[-1]
        
        if tipo_etiqueta == "one_hot":
            # Para one-hot: la posición con mayor valor es la predicción
            pred = numpy.argmax(y)
            real = numpy.argmax(label)
            if pred == real:
                aciertos += 1
        else:
            # Para código binario: redondear valores cercanos a 0 o 1
            pred_bits = (y > 0.5).astype(int).flatten()
            real_bits = label.flatten()
            if numpy.array_equal(pred_bits, real_bits):
                aciertos += 1
    
    precision = (aciertos / num_pruebas) * 100
    print(f"Tiempo: {tiempo:.2f}s, Precisión: {precision:.2f}% ({aciertos}/{num_pruebas})")
    
    return tiempo, precision, aciertos
    
def mostrar_tabla_resultados():
    archivos_necesarios = [
        'tabla1_onehot_lr.csv', 'tabla2_onehot_epocas.csv', 'tabla3_onehot_batch.csv',
        'tabla4_binary_lr.csv', 'tabla5_binary_epocas.csv', 'tabla6_binary_batch.csv'
    ]
    
    for archivo in archivos_necesarios:
        if not os.path.exists(archivo):
            print(f" No se encuentra el archivo {archivo}")
            print("Primero ejecuta los experimentos con python3 fc.py")
            return None
    
    tabla1 = pd.read_csv('tabla1_onehot_lr.csv')
    tabla2 = pd.read_csv('tabla2_onehot_epocas.csv')
    tabla3 = pd.read_csv('tabla3_onehot_batch.csv')
    tabla4 = pd.read_csv('tabla4_binary_lr.csv')
    tabla5 = pd.read_csv('tabla5_binary_epocas.csv')
    tabla6 = pd.read_csv('tabla6_binary_batch.csv')
    
    print("\n" + "="*80)
    print("RESULTADOS DE EXPERIMENTOS - RED NEURONAL")
    print("="*80)
    
    print("\n" + "="*70)
    print("4.1.1. EFECTO DE LA TASA DE APRENDIZAJE (η)")
    print("="*70)
    
    print("\n CUADRO 1: 10 bits (One-Hot)")
    print("-" * 65)
    print(f"{'η':^10} | {'Tiempo (s)':^18} | {'Éxito (%)':^15} | {'Aciertos/100':^15}")
    print("-" * 65)
    for _, row in tabla1.iterrows():
        print(f"{row['eta']:^10} | {row['tiempo_entrenamiento_s']:^18} | {row['exito_porcentaje']:^15} | {row['aciertos/100']:^15}")
    print("-" * 65)
    
    print("\n CUADRO 2: 4 bits (Código Binario)")
    print("-" * 65)
    print(f"{'η':^10} | {'Tiempo (s)':^18} | {'Éxito (%)':^15} | {'Aciertos/100':^15}")
    print("-" * 65)
    for _, row in tabla4.iterrows():
        print(f"{row['eta']:^10} | {row['tiempo_entrenamiento_s']:^18} | {row['exito_porcentaje']:^15} | {row['aciertos/100']:^15}")
    print("-" * 65)
    
    print("\n" + "="*70)
    print("4.1.2. EFECTO DEL NÚMERO DE ÉPOCAS")
    print("="*70)
    
    print("\n CUADRO 3: 10 bits (One-Hot)")
    print("-" * 65)
    print(f"{'Épocas':^10} | {'Tiempo (s)':^18} | {'Éxito (%)':^15} | {'Aciertos/100':^15}")
    print("-" * 65)
    for _, row in tabla2.iterrows():
        print(f"{row['epocas']:^10} | {row['tiempo_entrenamiento_s']:^18} | {row['exito_porcentaje']:^15} | {row['aciertos/100']:^15}")
    print("-" * 65)
    
    print("\n CUADRO 4: 4 bits (Código Binario)")
    print("-" * 65)
    print(f"{'Épocas':^10} | {'Tiempo (s)':^18} | {'Éxito (%)':^15} | {'Aciertos/100':^15}")
    print("-" * 65)
    for _, row in tabla5.iterrows():
        print(f"{row['epocas']:^10} | {row['tiempo_entrenamiento_s']:^18} | {row['exito_porcentaje']:^15} | {row['aciertos/100']:^15}")
    print("-" * 65)
    
    print("\n" + "="*70)
    print("4.1.3. EFECTO DEL TAMAÑO DEL LOTE")
    print("="*70)
    
    print("\n CUADRO 5: 10 bits (One-Hot)")
    print("-" * 65)
    print(f"{'Batch Size':^12} | {'Tiempo (s)':^18} | {'Éxito (%)':^15} | {'Aciertos/100':^15}")
    print("-" * 65)
    for _, row in tabla3.iterrows():
        print(f"{row['batch_size']:^12} | {row['tiempo_entrenamiento_s']:^18} | {row['exito_porcentaje']:^15} | {row['aciertos/100']:^15}")
    print("-" * 65)
    
    print("\n CUADRO 6: 4 bits (Código Binario)")
    print("-" * 65)
    print(f"{'Batch Size':^12} | {'Tiempo (s)':^18} | {'Éxito (%)':^15} | {'Aciertos/100':^15}")
    print("-" * 65)
    for _, row in tabla6.iterrows():
        print(f"{row['batch_size']:^12} | {row['tiempo_entrenamiento_s']:^18} | {row['exito_porcentaje']:^15} | {row['aciertos/100']:^15}")
    print("-" * 65)
    
    return tabla1, tabla2, tabla3, tabla4, tabla5, tabla6

def graficar_resultados(tabla1, tabla2, tabla3, tabla4, tabla5, tabla6):
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, axes = plt.subplots(2, 3, figsize=(16, 10))
    fig.suptitle('Análisis de Rendimiento - Red Neuronal', fontsize=16, fontweight='bold')
    
    ax = axes[0, 0]
    ax.plot(tabla1['eta'], tabla1['exito_porcentaje'], 'bo-', linewidth=2, markersize=8, label='10 bits')
    ax.plot(tabla4['eta'], tabla4['exito_porcentaje'], 'ro-', linewidth=2, markersize=8, label='4 bits')
    ax.set_xlabel('Tasa de Aprendizaje (η)'); ax.set_ylabel('Éxito (%)')
    ax.set_title('Efecto de la Tasa de Aprendizaje'); ax.legend(); ax.grid(True, alpha=0.3); ax.set_xscale('log')
    
    ax = axes[0, 1]
    ax.plot(tabla2['epocas'], tabla2['exito_porcentaje'], 'bo-', linewidth=2, markersize=8, label='10 bits')
    ax.plot(tabla5['epocas'], tabla5['exito_porcentaje'], 'ro-', linewidth=2, markersize=8, label='4 bits')
    ax.set_xlabel('Número de Épocas'); ax.set_ylabel('Éxito (%)')
    ax.set_title('Efecto del Número de Épocas'); ax.legend(); ax.grid(True, alpha=0.3); ax.set_xscale('log')
    
    ax = axes[0, 2]
    ax.plot(tabla3['batch_size'], tabla3['exito_porcentaje'], 'bo-', linewidth=2, markersize=8, label='10 bits')
    ax.plot(tabla6['batch_size'], tabla6['exito_porcentaje'], 'ro-', linewidth=2, markersize=8, label='4 bits')
    ax.set_xlabel('Tamaño de Lote'); ax.set_ylabel('Éxito (%)')
    ax.set_title('Efecto del Batch Size'); ax.legend(); ax.grid(True, alpha=0.3)
    
    ax = axes[1, 0]
    ax.plot(tabla2['epocas'], tabla2['tiempo_entrenamiento_s'], 'bs-', linewidth=2, markersize=8, label='10 bits')
    ax.plot(tabla5['epocas'], tabla5['tiempo_entrenamiento_s'], 'rs-', linewidth=2, markersize=8, label='4 bits')
    ax.set_xlabel('Número de Épocas'); ax.set_ylabel('Tiempo (s)')
    ax.set_title('Tiempo vs Épocas'); ax.legend(); ax.grid(True, alpha=0.3)
    
    ax = axes[1, 1]
    mejor_10bits = max(tabla2['exito_porcentaje'].max(), tabla1['exito_porcentaje'].max(), tabla3['exito_porcentaje'].max())
    mejor_4bits = max(tabla4['exito_porcentaje'].max(), tabla5['exito_porcentaje'].max(), tabla6['exito_porcentaje'].max())
    barras = ax.bar(['10 bits', '4 bits'], [mejor_10bits, mejor_4bits], color=['blue', 'red'], alpha=0.7)
    ax.set_ylabel('Máximo Éxito (%)'); ax.set_title('Mejor Rendimiento'); ax.set_ylim(0, 100)
    for barra, valor in zip(barras, [mejor_10bits, mejor_4bits]):
        ax.text(barra.get_x() + barra.get_width()/2, barra.get_height() + 1, f'{valor:.1f}%', ha='center')
    
    ax = axes[1, 2]
    datos_10bits = [tabla1['exito_porcentaje'].values, tabla2['exito_porcentaje'].values, tabla3['exito_porcentaje'].values]
    datos_4bits = [tabla4['exito_porcentaje'].values, tabla5['exito_porcentaje'].values, tabla6['exito_porcentaje'].values]
    posiciones = [1, 2, 3]
    bp1 = ax.boxplot(datos_10bits, positions=[p-0.2 for p in posiciones], widths=0.3, patch_artist=True, boxprops=dict(facecolor='blue', alpha=0.5))
    bp2 = ax.boxplot(datos_4bits, positions=[p+0.2 for p in posiciones], widths=0.3, patch_artist=True, boxprops=dict(facecolor='red', alpha=0.5))
    ax.set_xticks(posiciones); ax.set_xticklabels(['Learning Rate', 'Épocas', 'Batch Size'])
    ax.set_ylabel('Éxito (%)'); ax.set_title('Distribución de Resultados')
    ax.legend([bp1["boxes"][0], bp2["boxes"][0]], ['10 bits', '4 bits'], loc='upper left')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('graficas_resultados.png', dpi=150, bbox_inches='tight')
    print("\n Gráfica guardada como 'graficas_resultados.png'")
    plt.show()

def analizar_resultados(tabla1, tabla2, tabla3, tabla4, tabla5, tabla6):
    print("\n" + "="*80)
    print("6. ANÁLISIS DE RESULTADOS")
    print("="*80)
    
    print("\n📈 ARQUITECTURA 10 BITS (One-Hot):")
    print("-" * 50)
    print(f"  Mejor η: {tabla1.loc[tabla1['exito_porcentaje'].idxmax(), 'eta']} → {tabla1['exito_porcentaje'].max():.2f}%")
    print(f"  Mejor épocas: {tabla2.loc[tabla2['exito_porcentaje'].idxmax(), 'epocas']} → {tabla2['exito_porcentaje'].max():.2f}%")
    print(f"  Mejor batch: {tabla3.loc[tabla3['exito_porcentaje'].idxmax(), 'batch_size']} → {tabla3['exito_porcentaje'].max():.2f}%")
    print(f"  Máximo global: {max(tabla1['exito_porcentaje'].max(), tabla2['exito_porcentaje'].max(), tabla3['exito_porcentaje'].max()):.2f}%")
    
    print("\n ARQUITECTURA 4 BITS (Código Binario):")
    print("-" * 50)
    print(f"  Mejor η: {tabla4.loc[tabla4['exito_porcentaje'].idxmax(), 'eta']} → {tabla4['exito_porcentaje'].max():.2f}%")
    print(f"  Mejor épocas: {tabla5.loc[tabla5['exito_porcentaje'].idxmax(), 'epocas']} → {tabla5['exito_porcentaje'].max():.2f}%")
    print(f"  Mejor batch: {tabla6.loc[tabla6['exito_porcentaje'].idxmax(), 'batch_size']} → {tabla6['exito_porcentaje'].max():.2f}%")
    print(f"  Máximo global: {max(tabla4['exito_porcentaje'].max(), tabla5['exito_porcentaje'].max(), tabla6['exito_porcentaje'].max()):.2f}%")

def visualizar():
    print("\n" + "="*80)
    print("VISUALIZACIÓN DE RESULTADOS - PRÁCTICA 03")
    print("="*80)
    try:
        resultado = mostrar_tabla_resultados()
        if resultado:
            t1, t2, t3, t4, t5, t6 = resultado
            graficar_resultados(t1, t2, t3, t4, t5, t6)
            analizar_resultados(t1, t2, t3, t4, t5, t6)
            print("\nVISUALIZACIÓN COMPLETA")
    except Exception as e:
        print(f"\n Error: {e}")


def main():
    print("TRAINING A NEURAL NETWORK - " + NAME)
    dataset_folder = os.path.join("../dataset")
    
    training_x, training_t, testing_x, testing_t = load_dataset(dataset_folder)
    training_x_bin, training_t_bin, testing_x_bin, testing_t_bin = load_dataset_binary(dataset_folder)
    
    learning_rates = [0.5, 1.0, 3.0, 10.0]
    epochs_list = [3, 10, 50, 100]
    batch_sizes = [5, 10, 30, 100]
    
    print("\n" + "="*80)
    print("INICIANDO EXPERIMENTOS - 100 PRUEBAS POR CONFIGURACIÓN")
    print("="*80)
    
    # ONE-HOT
    print("\n" + "="*60)
    print("PARTE 1: 10 BITS DE SALIDA")
    print("="*60)
    
    resultados_lr = []
    for lr in learning_rates:
        tiempo, precision, aciertos = run_experiment([784,30,10], training_x, training_t, testing_x, testing_t, 10, 30, lr, "one_hot", 100)
        resultados_lr.append([lr, round(tiempo, 2), round(precision, 2), aciertos])
    with open("tabla1_onehot_lr.csv", 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['eta', 'tiempo_entrenamiento_s', 'exito_porcentaje', 'aciertos/100'])
        writer.writerows(resultados_lr)
    
    resultados_ep = []
    for ep in epochs_list:
        tiempo, precision, aciertos = run_experiment([784,30,10], training_x, training_t, testing_x, testing_t, ep, 30, 1.0, "one_hot", 100)
        resultados_ep.append([ep, round(tiempo, 2), round(precision, 2), aciertos])
    with open("tabla2_onehot_epocas.csv", 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['epocas', 'tiempo_entrenamiento_s', 'exito_porcentaje', 'aciertos/100'])
        writer.writerows(resultados_ep)
    
    resultados_bs = []
    for bs in batch_sizes:
        tiempo, precision, aciertos = run_experiment([784,30,10], training_x, training_t, testing_x, testing_t, 10, bs, 1.0, "one_hot", 100)
        resultados_bs.append([bs, round(tiempo, 2), round(precision, 2), aciertos])
    with open("tabla3_onehot_batch.csv", 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['batch_size', 'tiempo_entrenamiento_s', 'exito_porcentaje', 'aciertos/100'])
        writer.writerows(resultados_bs)
    
    # BINARIO
    print("\n" + "="*60)
    print("PARTE 2: 4 BITS DE SALIDA")
    print("="*60)
    
    resultados_lr_bin = []
    for lr in learning_rates:
        tiempo, precision, aciertos = run_experiment([784,30,4], training_x_bin, training_t_bin, testing_x_bin, testing_t_bin, 10, 30, lr, "binary", 100)
        resultados_lr_bin.append([lr, round(tiempo, 2), round(precision, 2), aciertos])
    with open("tabla4_binary_lr.csv", 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['eta', 'tiempo_entrenamiento_s', 'exito_porcentaje', 'aciertos/100'])
        writer.writerows(resultados_lr_bin)
    
    resultados_ep_bin = []
    for ep in epochs_list:
        tiempo, precision, aciertos = run_experiment([784,30,4], training_x_bin, training_t_bin, testing_x_bin, testing_t_bin, ep, 30, 1.0, "binary", 100)
        resultados_ep_bin.append([ep, round(tiempo, 2), round(precision, 2), aciertos])
    with open("tabla5_binary_epocas.csv", 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['epocas', 'tiempo_entrenamiento_s', 'exito_porcentaje', 'aciertos/100'])
        writer.writerows(resultados_ep_bin)
    
    resultados_bs_bin = []
    for bs in batch_sizes:
        tiempo, precision, aciertos = run_experiment([784,30,4], training_x_bin, training_t_bin, testing_x_bin, testing_t_bin, 10, bs, 1.0, "binary", 100)
        resultados_bs_bin.append([bs, round(tiempo, 2), round(precision, 2), aciertos])
    with open("tabla6_binary_batch.csv", 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['batch_size', 'tiempo_entrenamiento_s', 'exito_porcentaje', 'aciertos/100'])
        writer.writerows(resultados_bs_bin)
    
    print("\n" + "="*80)
    print("EXPERIMENTOS COMPLETADOS")
    print("="*80)

# ============================================================
# PUNTO DE ENTRADA
# ============================================================

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'visualizar':
        visualizar()
    else:
        main()
        visualizar()
