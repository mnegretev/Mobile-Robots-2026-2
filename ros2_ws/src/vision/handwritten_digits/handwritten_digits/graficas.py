import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv('resultados_practica03.csv')

# Gráfica 1: Precisión vs tasa de aprendizaje para diferentes épocas (batch=30)
for arch in df['architecture'].unique():
    subset = df[(df['architecture']==arch) & (df['batch_size']==30)]
    plt.figure()
    for ep in [3,10,50,100]:
        data = subset[subset['epochs']==ep]
        plt.plot(data['learning_rate'], data['accuracy_%'], marker='o', label=f'épocas={ep}')
    plt.xscale('log')
    plt.xlabel('Tasa de aprendizaje')
    plt.ylabel('Precisión (%)')
    plt.title(f'Precisión - {arch}')
    plt.legend()
    plt.grid(True)
    plt.savefig(f'precision_{arch.replace(" ","_")}.png')
    plt.show()
