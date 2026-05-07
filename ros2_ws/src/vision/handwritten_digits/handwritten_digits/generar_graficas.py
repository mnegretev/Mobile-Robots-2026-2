import pandas as pd
import matplotlib.pyplot as plt

# Cargar los datos
df_onehot = pd.read_csv('resultados_p3.csv')
df_binario = pd.read_csv('resultados_p3_binario.csv')

# --- GRÁFICA 1: Épocas vs Porcentaje de Éxito (Comparativa) ---
# Filtramos para una tasa de aprendizaje de 10.0 y lote de 10 (tus mejores parámetros)
lr_fijo = 10.0
lote_fijo = 10

data_oh = df_onehot[(df_onehot['Tasa_Aprendizaje'] == lr_fijo) & (df_onehot['Lote'] == lote_fijo)]
data_bin = df_binario[(df_binario['Tasa_Aprendizaje'] == lr_fijo) & (df_binario['Lote'] == lote_fijo)]

plt.figure(figsize=(8, 5))
plt.plot(data_oh['Epocas'], data_oh['Exito_Porcentaje'], marker='o', linestyle='-', label='One-Hot (10 neuronas)')
plt.plot(data_bin['Epocas'], data_bin['Exito_Porcentaje'], marker='s', linestyle='--', label='Binario (4 neuronas)')

plt.title('Comparativa de Aprendizaje: One-Hot vs Binario\n(Tasa de Aprendizaje: 10.0, Lote: 10)')
plt.xlabel('Número de Épocas')
plt.ylabel('Porcentaje de Éxito (%)')
plt.grid(True, linestyle=':', alpha=0.7)
plt.legend()
plt.tight_layout()
plt.savefig('grafica_exito_vs_epocas.png', dpi=300)
plt.close()

# --- GRÁFICA 2: Tamaño de Lote vs Tiempo de Entrenamiento ---
# Promediamos el tiempo para cada tamaño de lote en el experimento One-Hot
tiempo_por_lote = df_onehot.groupby('Lote')['Tiempo_Segundos'].mean()

plt.figure(figsize=(8, 5))
tiempo_por_lote.plot(kind='bar', color='steelblue', edgecolor='black')
plt.title('Impacto del Tamaño de Lote en el Tiempo de Entrenamiento Promedio')
plt.xlabel('Tamaño del Lote (Batch Size)')
plt.ylabel('Tiempo Promedio (Segundos)')
plt.xticks(rotation=0)
plt.grid(axis='y', linestyle=':', alpha=0.7)
plt.tight_layout()
plt.savefig('grafica_tiempo_vs_lote.png', dpi=300)
plt.close()

print("Gráficas generadas exitosamente: 'grafica_exito_vs_epocas.png' y 'grafica_tiempo_vs_lote.png'")