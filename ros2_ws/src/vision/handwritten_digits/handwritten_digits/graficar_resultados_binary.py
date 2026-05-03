import pandas as pd
import matplotlib.pyplot as plt

def main():
    print("Generando gráficas a partir de nn_binary_results.csv...")
    
    # Cargar los datos
    try:
        df = pd.read_csv('nn_binary_training_results.csv')
    except FileNotFoundError:
        print("Error: No se encontró el archivo 'nn_binary_results.csv'")
        return

    # Crear una etiqueta combinada para cada configuración (LR, Épocas, Batch)
    df['Config'] = 'LR:' + df['Learning_Rate'].astype(str) + '\nEp:' + df['Epochs'].astype(str) + '\nBS:' + df['Batch_Size'].astype(str)

    # Ordenar por Porcentaje de Éxito de menor a mayor para mejor visualización
    df = df.sort_values('Porcentaje_Exito', ascending=True)

    # Gráfica: Comparación de Porcentaje de Éxito en Top 5 (Binario)
    plt.figure(figsize=(10, 6))
    bars = plt.bar(df['Config'], df['Porcentaje_Exito'], color='mediumseagreen')

    plt.title('Porcentaje de Éxito - Top 5 Configuraciones (Arquitectura Binaria)', fontsize=14)
    plt.xlabel('Configuración (Learning Rate, Épocas, Batch Size)', fontsize=12)
    plt.ylabel('Porcentaje de Éxito (%)', fontsize=12)
    
    # Ajustamos el límite Y para que las diferencias entre 85% y 87% sean notorias
    plt.ylim(80, 90) 
    plt.grid(axis='y', linestyle='--', alpha=0.7)

    # Añadir el valor exacto sobre cada barra
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval + 0.1, f'{yval:.2f}%', ha='center', va='bottom', fontsize=11, fontweight='bold')

    plt.tight_layout()
    plt.savefig('grafica_top5_binario.png', dpi=300)
    print("-> Guardada: grafica_top5_binario.png")

if __name__ == '__main__':
    main()