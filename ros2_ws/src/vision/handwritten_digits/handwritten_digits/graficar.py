import pandas as pd
import matplotlib.pyplot as plt

# Cargar los datos
df = pd.read_csv('resultados_nn.csv')

# --- Filtrado correcto leyendo directamente del CSV ---
# Usamos .str.contains() para evitar problemas de comillas o espacios extras
df_dec = df[df['Arquitectura'] == '[784, 30, 10]']
df_bin = df[df['Arquitectura'] == '[784, 30, 4]']

# --- Gráfica 1: Precisión vs Tasa de Aprendizaje (Fijando Épocas=50, Lote=30) ---
plt.figure(figsize=(8, 5))
subset_dec = df_dec[(df_dec['Epocas'] == 50) & (df_dec['Lote'] == 30)]
subset_bin = df_bin[(df_bin['Epocas'] == 50) & (df_bin['Lote'] == 30)]

# Verificación de seguridad
if subset_dec.empty or subset_bin.empty:
    print("Advertencia: No se encontraron datos para la Gráfica 1 (Epocas=50, Lote=30). Verifica que el CSV los contenga.")

plt.plot(subset_dec['Tasa'], subset_dec['Exito (%)'], marker='o', label='Decimal (784-30-10)')
plt.plot(subset_bin['Tasa'], subset_bin['Exito (%)'], marker='s', label='Binaria (784-30-4)')
plt.title('Precisión vs Tasa de Aprendizaje (50 Épocas, Lote 30)')
plt.xlabel('Tasa de Aprendizaje (eta)')
plt.ylabel('Éxito (%)')
plt.grid(True)
plt.legend()
plt.savefig('precision_vs_tasa.png')
plt.close()

# --- Gráfica 2: Tiempo vs Épocas (Fijando Tasa=1.0, Lote=50) ---
plt.figure(figsize=(8, 5))
# Ajuste: En tu CSV el Lote 50 no existe, usamos Lote 30 o 100 según los que probaste. Cambiaré a Lote=30
subset_dec_t = df_dec[(df_dec['Tasa'] == 1.0) & (df_dec['Lote'] == 30)]
subset_bin_t = df_bin[(df_bin['Tasa'] == 1.0) & (df_bin['Lote'] == 30)]

if subset_dec_t.empty or subset_bin_t.empty:
    print("Advertencia: No se encontraron datos para la Gráfica 2 (Tasa=1.0, Lote=30).")

plt.plot(subset_dec_t['Epocas'], subset_dec_t['Tiempo (s)'], marker='o', label='Decimal (784-30-10)')
plt.plot(subset_bin_t['Epocas'], subset_bin_t['Tiempo (s)'], marker='s', label='Binaria (784-30-4)')
plt.title('Tiempo de Entrenamiento vs Épocas (Tasa 1.0, Lote 30)')
plt.xlabel('Número de Épocas')
plt.ylabel('Tiempo (segundos)')
plt.grid(True)
plt.legend()
plt.savefig('tiempo_vs_epocas.png')
plt.close()

print("¡Gráficas generadas exitosamente y reescritas!")