import pandas as pd
import matplotlib.pyplot as plt

def main():
    print("Generando gráficas a partir de nn_training_results.csv...")
    
    # Cargar los datos
    try:
        df = pd.read_csv('nn_training_results.csv')
    except FileNotFoundError:
        print("Error: No se encontró el archivo 'nn_training_results.csv'")
        return

    # ---------------------------------------------------------
    # Gráfica 1: Evolución del Porcentaje de Éxito vs Épocas
    # Fijamos el Batch Size en 10 (un valor intermedio muy estable)
    # ---------------------------------------------------------
    plt.figure(figsize=(10, 6))
    batch_fijo = 10
    df_batch = df[df['Batch_Size'] == batch_fijo]
    
    for lr in df_batch['Learning_Rate'].unique():
        datos_lr = df_batch[df_batch['Learning_Rate'] == lr].sort_values('Epochs')
        plt.plot(datos_lr['Epochs'], datos_lr['Porcentaje_Exito'], marker='o', linewidth=2, label=f'LR = {lr}')
        
    plt.title(f'Evolución de Precisión vs Épocas (Batch Size = {batch_fijo})', fontsize=14)
    plt.xlabel('Número de Épocas', fontsize=12)
    plt.ylabel('Porcentaje de Éxito (%)', fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend(title="Tasa de Aprendizaje ($\eta$)")
    plt.tight_layout()
    plt.savefig('grafica_exito_vs_epocas.png', dpi=300)
    print("-> Guardada: grafica_exito_vs_epocas.png")

    # ---------------------------------------------------------
    # Gráfica 2: Tiempo de Entrenamiento vs Tamaño del Lote
    # Fijamos las épocas en 100 para ver el impacto máximo del tiempo
    # ---------------------------------------------------------
    plt.figure(figsize=(10, 6))
    epocas_fijas = 100
    df_epocas = df[df['Epochs'] == epocas_fijas]
    
    # Como el tiempo no cambia significativamente por el LR, tomamos el promedio por lote
    tiempo_promedio = df_epocas.groupby('Batch_Size')['Tiempo_Entrenamiento_s'].mean()
    
    bars = plt.bar([str(x) for x in tiempo_promedio.index], tiempo_promedio.values, color='steelblue')
    plt.title(f'Tiempo Promedio de Entrenamiento vs Tamaño de Lote (Épocas = {epocas_fijas})', fontsize=14)
    plt.xlabel('Tamaño de Lote (Batch Size)', fontsize=12)
    plt.ylabel('Tiempo Total de Entrenamiento (segundos)', fontsize=12)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Añadir los valores arriba de las barras
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval + 0.5, f'{yval:.1f}s', ha='center', va='bottom', fontsize=10)

    plt.tight_layout()
    plt.savefig('grafica_tiempo_vs_lote.png', dpi=300)
    print("-> Guardada: grafica_tiempo_vs_lote.png")

    # ---------------------------------------------------------
    # Tabla: Extraer el Top 5 de mejores configuraciones
    # ---------------------------------------------------------
    print("\n--- TOP 5 MEJORES CONFIGURACIONES (ONE-HOT) ---")
    top5 = df.sort_values(by=['Porcentaje_Exito', 'Tiempo_Entrenamiento_s'], ascending=[False, True]).head(5)
    # Formatear e imprimir en consola
    print(top5[['Learning_Rate', 'Epochs', 'Batch_Size', 'Tiempo_Entrenamiento_s', 'Porcentaje_Exito']].to_string(index=False))

if __name__ == '__main__':
    main()