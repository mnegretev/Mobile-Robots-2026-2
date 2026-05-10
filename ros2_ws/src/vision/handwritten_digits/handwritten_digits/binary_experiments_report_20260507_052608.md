# PRÁCTICA 3: REDES NEURONALES CON ETIQUETAS BINARIAS

**Estudiante:** Galicia Rioja Angel Daniel
**Fecha:** 2026-05-07 05:26:08

## RESUMEN EJECUTIVO

Este reporte presenta los resultados de experimentos con redes neuronales utilizando representación binaria de 4 bits para las etiquetas de dígitos (0-9). Esta aproximación reduce la dimensionalidad de salida de 10 a 4 neuronas.

## CONFIGURACIONES PROBADAS

| Configuración | Arquitectura | Épocas | Tamaño Lote | Tasa Aprendizaje |
|---------------|--------------|--------|-------------|------------------|
| Binary_Base_0.5_lr_3_epochs_5_batch | 784-100-4 | 3 | 5 | 0.5 |
| Binary_Base_0.5_lr_10_epochs_5_batch | 784-100-4 | 10 | 5 | 0.5 |
| Binary_Base_0.5_lr_50_epochs_5_batch | 784-100-4 | 50 | 5 | 0.5 |
| Binary_Base_0.5_lr_100_epochs_5_batch | 784-100-4 | 100 | 5 | 0.5 |
| Binary_Base_1.0_lr_3_epochs_10_batch | 784-100-4 | 3 | 10 | 1.0 |
| Binary_Base_1.0_lr_10_epochs_10_batch | 784-100-4 | 10 | 10 | 1.0 |
| Binary_Base_1.0_lr_50_epochs_10_batch | 784-100-4 | 50 | 10 | 1.0 |
| Binary_Base_1.0_lr_100_epochs_10_batch | 784-100-4 | 100 | 10 | 1.0 |
| Binary_Base_3.0_lr_3_epochs_30_batch | 784-100-4 | 3 | 30 | 3.0 |
| Binary_Base_3.0_lr_10_epochs_30_batch | 784-100-4 | 10 | 30 | 3.0 |
| Binary_Base_3.0_lr_50_epochs_30_batch | 784-100-4 | 50 | 30 | 3.0 |
| Binary_Base_3.0_lr_100_epochs_30_batch | 784-100-4 | 100 | 30 | 3.0 |
| Binary_Base_10.0_lr_3_epochs_100_batch | 784-100-4 | 3 | 100 | 10.0 |
| Binary_Base_10.0_lr_10_epochs_100_batch | 784-100-4 | 10 | 100 | 10.0 |
| Binary_Base_10.0_lr_50_epochs_100_batch | 784-100-4 | 50 | 100 | 10.0 |
| Binary_Base_10.0_lr_100_epochs_100_batch | 784-100-4 | 100 | 100 | 10.0 |
| Binary_Alt_0.5_lr_3_epochs_5_batch | 784-50-25-4 | 3 | 5 | 0.5 |
| Binary_Alt_0.5_lr_10_epochs_5_batch | 784-50-25-4 | 10 | 5 | 0.5 |
| Binary_Alt_0.5_lr_50_epochs_5_batch | 784-50-25-4 | 50 | 5 | 0.5 |
| Binary_Alt_0.5_lr_100_epochs_5_batch | 784-50-25-4 | 100 | 5 | 0.5 |
| Binary_Alt_1.0_lr_3_epochs_10_batch | 784-50-25-4 | 3 | 10 | 1.0 |
| Binary_Alt_1.0_lr_10_epochs_10_batch | 784-50-25-4 | 10 | 10 | 1.0 |
| Binary_Alt_1.0_lr_50_epochs_10_batch | 784-50-25-4 | 50 | 10 | 1.0 |
| Binary_Alt_1.0_lr_100_epochs_10_batch | 784-50-25-4 | 100 | 10 | 1.0 |
| Binary_Alt_3.0_lr_3_epochs_30_batch | 784-50-25-4 | 3 | 30 | 3.0 |
| Binary_Alt_3.0_lr_10_epochs_30_batch | 784-50-25-4 | 10 | 30 | 3.0 |
| Binary_Alt_3.0_lr_50_epochs_30_batch | 784-50-25-4 | 50 | 30 | 3.0 |
| Binary_Alt_3.0_lr_100_epochs_30_batch | 784-50-25-4 | 100 | 30 | 3.0 |
| Binary_Alt_10.0_lr_3_epochs_100_batch | 784-50-25-4 | 3 | 100 | 10.0 |
| Binary_Alt_10.0_lr_10_epochs_100_batch | 784-50-25-4 | 10 | 100 | 10.0 |
| Binary_Alt_10.0_lr_50_epochs_100_batch | 784-50-25-4 | 50 | 100 | 10.0 |
| Binary_Alt_10.0_lr_100_epochs_100_batch | 784-50-25-4 | 100 | 100 | 10.0 |

## RESULTADOS DETALLADOS

### Ranking por Precisión

| Posición | Configuración | Precisión | Precisión Macro | Recall Macro | F1 Macro | Tiempo (s) |
|----------|---------------|-----------|-----------------|--------------|-----------|------------|
| 1 | Binary_Base_0.5_lr_100_epochs_5_batch | 0.937 | 0.940 | 0.937 | 0.938 | 236.6 |
| 2 | Binary_Base_3.0_lr_100_epochs_30_batch | 0.934 | 0.937 | 0.935 | 0.936 | 178.4 |
| 3 | Binary_Base_10.0_lr_100_epochs_100_batch | 0.933 | 0.937 | 0.933 | 0.934 | 176.7 |
| 4 | Binary_Alt_10.0_lr_100_epochs_100_batch | 0.932 | 0.935 | 0.932 | 0.933 | 99.0 |
| 5 | Binary_Base_0.5_lr_50_epochs_5_batch | 0.931 | 0.936 | 0.931 | 0.933 | 117.2 |
| 6 | Binary_Base_1.0_lr_50_epochs_10_batch | 0.931 | 0.936 | 0.931 | 0.933 | 91.1 |
| 7 | Binary_Alt_1.0_lr_100_epochs_10_batch | 0.930 | 0.934 | 0.930 | 0.932 | 102.2 |
| 8 | Binary_Alt_3.0_lr_50_epochs_30_batch | 0.930 | 0.932 | 0.930 | 0.931 | 50.0 |
| 9 | Binary_Alt_10.0_lr_50_epochs_100_batch | 0.930 | 0.933 | 0.930 | 0.931 | 49.5 |
| 10 | Binary_Base_3.0_lr_50_epochs_30_batch | 0.929 | 0.933 | 0.929 | 0.931 | 89.2 |
| 11 | Binary_Alt_0.5_lr_50_epochs_5_batch | 0.929 | 0.931 | 0.929 | 0.930 | 53.1 |
| 12 | Binary_Alt_3.0_lr_100_epochs_30_batch | 0.929 | 0.932 | 0.929 | 0.930 | 99.8 |
| 13 | Binary_Base_1.0_lr_100_epochs_10_batch | 0.927 | 0.932 | 0.927 | 0.929 | 182.6 |
| 14 | Binary_Alt_1.0_lr_10_epochs_10_batch | 0.926 | 0.930 | 0.926 | 0.928 | 10.2 |
| 15 | Binary_Alt_0.5_lr_100_epochs_5_batch | 0.926 | 0.930 | 0.926 | 0.928 | 106.0 |
| 16 | Binary_Alt_1.0_lr_50_epochs_10_batch | 0.924 | 0.929 | 0.924 | 0.926 | 51.1 |
| 17 | Binary_Base_10.0_lr_50_epochs_100_batch | 0.921 | 0.924 | 0.921 | 0.922 | 88.4 |
| 18 | Binary_Base_3.0_lr_10_epochs_30_batch | 0.916 | 0.922 | 0.916 | 0.919 | 17.8 |
| 19 | Binary_Alt_10.0_lr_10_epochs_100_batch | 0.916 | 0.924 | 0.916 | 0.920 | 9.9 |
| 20 | Binary_Base_1.0_lr_10_epochs_10_batch | 0.915 | 0.924 | 0.915 | 0.919 | 20.5 |
| 21 | Binary_Alt_3.0_lr_10_epochs_30_batch | 0.915 | 0.918 | 0.915 | 0.916 | 10.0 |
| 22 | Binary_Base_10.0_lr_10_epochs_100_batch | 0.913 | 0.917 | 0.912 | 0.915 | 17.7 |
| 23 | Binary_Base_0.5_lr_10_epochs_5_batch | 0.906 | 0.917 | 0.907 | 0.911 | 23.7 |
| 24 | Binary_Alt_0.5_lr_10_epochs_5_batch | 0.901 | 0.911 | 0.901 | 0.905 | 10.6 |
| 25 | Binary_Alt_0.5_lr_3_epochs_5_batch | 0.882 | 0.887 | 0.882 | 0.882 | 3.2 |
| 26 | Binary_Base_10.0_lr_3_epochs_100_batch | 0.880 | 0.885 | 0.879 | 0.880 | 5.3 |
| 27 | Binary_Base_3.0_lr_3_epochs_30_batch | 0.877 | 0.885 | 0.877 | 0.879 | 5.4 |
| 28 | Binary_Base_0.5_lr_3_epochs_5_batch | 0.877 | 0.884 | 0.877 | 0.879 | 7.0 |
| 29 | Binary_Alt_3.0_lr_3_epochs_30_batch | 0.877 | 0.884 | 0.877 | 0.879 | 3.0 |
| 30 | Binary_Alt_1.0_lr_3_epochs_10_batch | 0.873 | 0.884 | 0.872 | 0.875 | 3.1 |
| 31 | Binary_Base_1.0_lr_3_epochs_10_batch | 0.864 | 0.874 | 0.864 | 0.865 | 6.3 |
| 32 | Binary_Alt_10.0_lr_3_epochs_100_batch | 0.837 | 0.855 | 0.836 | 0.841 | 3.1 |

### Análisis por Configuración

#### Binary_Base_0.5_lr_3_epochs_5_batch

**Parámetros:**
- Arquitectura: [784, 100, 4]
- Épocas: 3
- Tamaño de lote: 5
- Tasa de aprendizaje: 0.5

**Métricas de desempeño:**
- Precisión global: 0.877
- Precisión macro: 0.884
- Recall macro: 0.877
- F1 macro: 0.879
- Tiempo de entrenamiento: 7.0s

**Representación binaria por clase:**
- Dígito 0 (binario: 0000): Precisión=0.861, Recall=0.944, F1=0.901
- Dígito 1 (binario: 0001): Precisión=0.863, Recall=0.943, F1=0.901
- Dígito 2 (binario: 0010): Precisión=0.872, Recall=0.837, F1=0.854
- Dígito 3 (binario: 0011): Precisión=0.861, Recall=0.852, F1=0.856
- Dígito 4 (binario: 0100): Precisión=0.902, Recall=0.841, F1=0.870
- Dígito 5 (binario: 0101): Precisión=0.827, Recall=0.857, F1=0.842
- Dígito 6 (binario: 0110): Precisión=0.879, Recall=0.949, F1=0.913
- Dígito 7 (binario: 0111): Precisión=0.934, Recall=0.885, F1=0.909
- Dígito 8 (binario: 1000): Precisión=0.939, Recall=0.773, F1=0.848
- Dígito 9 (binario: 1001): Precisión=0.900, Recall=0.887, F1=0.893

#### Binary_Base_0.5_lr_10_epochs_5_batch

**Parámetros:**
- Arquitectura: [784, 100, 4]
- Épocas: 10
- Tamaño de lote: 5
- Tasa de aprendizaje: 0.5

**Métricas de desempeño:**
- Precisión global: 0.906
- Precisión macro: 0.917
- Recall macro: 0.907
- F1 macro: 0.911
- Tiempo de entrenamiento: 23.7s

**Representación binaria por clase:**
- Dígito 0 (binario: 0000): Precisión=0.917, Recall=0.949, F1=0.933
- Dígito 1 (binario: 0001): Precisión=0.958, Recall=0.933, F1=0.945
- Dígito 2 (binario: 0010): Precisión=0.881, Recall=0.903, F1=0.892
- Dígito 3 (binario: 0011): Precisión=0.926, Recall=0.890, F1=0.908
- Dígito 4 (binario: 0100): Precisión=0.931, Recall=0.845, F1=0.886
- Dígito 5 (binario: 0101): Precisión=0.874, Recall=0.884, F1=0.879
- Dígito 6 (binario: 0110): Precisión=0.916, Recall=0.967, F1=0.941
- Dígito 7 (binario: 0111): Precisión=0.871, Recall=0.958, F1=0.913
- Dígito 8 (binario: 1000): Precisión=0.943, Recall=0.828, F1=0.882
- Dígito 9 (binario: 1001): Precisión=0.958, Recall=0.906, F1=0.932

#### Binary_Base_0.5_lr_50_epochs_5_batch

**Parámetros:**
- Arquitectura: [784, 100, 4]
- Épocas: 50
- Tamaño de lote: 5
- Tasa de aprendizaje: 0.5

**Métricas de desempeño:**
- Precisión global: 0.931
- Precisión macro: 0.936
- Recall macro: 0.931
- F1 macro: 0.933
- Tiempo de entrenamiento: 117.2s

**Representación binaria por clase:**
- Dígito 0 (binario: 0000): Precisión=0.931, Recall=0.964, F1=0.948
- Dígito 1 (binario: 0001): Precisión=0.916, Recall=0.954, F1=0.934
- Dígito 2 (binario: 0010): Precisión=0.938, Recall=0.923, F1=0.931
- Dígito 3 (binario: 0011): Precisión=0.932, Recall=0.919, F1=0.926
- Dígito 4 (binario: 0100): Precisión=0.945, Recall=0.908, F1=0.926
- Dígito 5 (binario: 0101): Precisión=0.929, Recall=0.905, F1=0.917
- Dígito 6 (binario: 0110): Precisión=0.954, Recall=0.967, F1=0.961
- Dígito 7 (binario: 0111): Precisión=0.932, Recall=0.932, F1=0.932
- Dígito 8 (binario: 1000): Precisión=0.937, Recall=0.904, F1=0.920
- Dígito 9 (binario: 1001): Precisión=0.945, Recall=0.936, F1=0.941

#### Binary_Base_0.5_lr_100_epochs_5_batch

**Parámetros:**
- Arquitectura: [784, 100, 4]
- Épocas: 100
- Tamaño de lote: 5
- Tasa de aprendizaje: 0.5

**Métricas de desempeño:**
- Precisión global: 0.937
- Precisión macro: 0.940
- Recall macro: 0.937
- F1 macro: 0.938
- Tiempo de entrenamiento: 236.6s

**Representación binaria por clase:**
- Dígito 0 (binario: 0000): Precisión=0.945, Recall=0.959, F1=0.952
- Dígito 1 (binario: 0001): Precisión=0.898, Recall=0.948, F1=0.922
- Dígito 2 (binario: 0010): Precisión=0.938, Recall=0.923, F1=0.931
- Dígito 3 (binario: 0011): Precisión=0.957, Recall=0.957, F1=0.957
- Dígito 4 (binario: 0100): Precisión=0.951, Recall=0.932, F1=0.941
- Dígito 5 (binario: 0101): Precisión=0.929, Recall=0.899, F1=0.914
- Dígito 6 (binario: 0110): Precisión=0.977, Recall=0.967, F1=0.972
- Dígito 7 (binario: 0111): Precisión=0.928, Recall=0.942, F1=0.935
- Dígito 8 (binario: 1000): Precisión=0.928, Recall=0.909, F1=0.918
- Dígito 9 (binario: 1001): Precisión=0.954, Recall=0.926, F1=0.940

#### Binary_Base_1.0_lr_3_epochs_10_batch

**Parámetros:**
- Arquitectura: [784, 100, 4]
- Épocas: 3
- Tamaño de lote: 10
- Tasa de aprendizaje: 1.0

**Métricas de desempeño:**
- Precisión global: 0.864
- Precisión macro: 0.874
- Recall macro: 0.864
- F1 macro: 0.865
- Tiempo de entrenamiento: 6.3s

**Representación binaria por clase:**
- Dígito 0 (binario: 0000): Precisión=0.802, Recall=0.964, F1=0.876
- Dígito 1 (binario: 0001): Precisión=0.828, Recall=0.943, F1=0.882
- Dígito 2 (binario: 0010): Precisión=0.890, Recall=0.821, F1=0.854
- Dígito 3 (binario: 0011): Precisión=0.916, Recall=0.781, F1=0.843
- Dígito 4 (binario: 0100): Precisión=0.807, Recall=0.928, F1=0.863
- Dígito 5 (binario: 0101): Precisión=0.812, Recall=0.889, F1=0.848
- Dígito 6 (binario: 0110): Precisión=0.899, Recall=0.907, F1=0.903
- Dígito 7 (binario: 0111): Precisión=0.905, Recall=0.848, F1=0.876
- Dígito 8 (binario: 1000): Precisión=0.931, Recall=0.747, F1=0.829
- Dígito 9 (binario: 1001): Precisión=0.953, Recall=0.808, F1=0.875

#### Binary_Base_1.0_lr_10_epochs_10_batch

**Parámetros:**
- Arquitectura: [784, 100, 4]
- Épocas: 10
- Tamaño de lote: 10
- Tasa de aprendizaje: 1.0

**Métricas de desempeño:**
- Precisión global: 0.915
- Precisión macro: 0.924
- Recall macro: 0.915
- F1 macro: 0.919
- Tiempo de entrenamiento: 20.5s

**Representación binaria por clase:**
- Dígito 0 (binario: 0000): Precisión=0.922, Recall=0.959, F1=0.940
- Dígito 1 (binario: 0001): Precisión=0.913, Recall=0.923, F1=0.918
- Dígito 2 (binario: 0010): Precisión=0.905, Recall=0.929, F1=0.917
- Dígito 3 (binario: 0011): Precisión=0.908, Recall=0.890, F1=0.899
- Dígito 4 (binario: 0100): Precisión=0.949, Recall=0.899, F1=0.923
- Dígito 5 (binario: 0101): Precisión=0.938, Recall=0.884, F1=0.910
- Dígito 6 (binario: 0110): Precisión=0.941, Recall=0.958, F1=0.949
- Dígito 7 (binario: 0111): Precisión=0.932, Recall=0.927, F1=0.929
- Dígito 8 (binario: 1000): Precisión=0.882, Recall=0.904, F1=0.893
- Dígito 9 (binario: 1001): Precisión=0.947, Recall=0.877, F1=0.910

#### Binary_Base_1.0_lr_50_epochs_10_batch

**Parámetros:**
- Arquitectura: [784, 100, 4]
- Épocas: 50
- Tamaño de lote: 10
- Tasa de aprendizaje: 1.0

**Métricas de desempeño:**
- Precisión global: 0.931
- Precisión macro: 0.936
- Recall macro: 0.931
- F1 macro: 0.933
- Tiempo de entrenamiento: 91.1s

**Representación binaria por clase:**
- Dígito 0 (binario: 0000): Precisión=0.913, Recall=0.954, F1=0.933
- Dígito 1 (binario: 0001): Precisión=0.929, Recall=0.943, F1=0.936
- Dígito 2 (binario: 0010): Precisión=0.958, Recall=0.929, F1=0.943
- Dígito 3 (binario: 0011): Precisión=0.938, Recall=0.933, F1=0.936
- Dígito 4 (binario: 0100): Precisión=0.936, Recall=0.913, F1=0.924
- Dígito 5 (binario: 0101): Precisión=0.925, Recall=0.910, F1=0.917
- Dígito 6 (binario: 0110): Precisión=0.950, Recall=0.972, F1=0.961
- Dígito 7 (binario: 0111): Precisión=0.928, Recall=0.942, F1=0.935
- Dígito 8 (binario: 1000): Precisión=0.916, Recall=0.884, F1=0.900
- Dígito 9 (binario: 1001): Precisión=0.964, Recall=0.926, F1=0.945

#### Binary_Base_1.0_lr_100_epochs_10_batch

**Parámetros:**
- Arquitectura: [784, 100, 4]
- Épocas: 100
- Tamaño de lote: 10
- Tasa de aprendizaje: 1.0

**Métricas de desempeño:**
- Precisión global: 0.927
- Precisión macro: 0.932
- Recall macro: 0.927
- F1 macro: 0.929
- Tiempo de entrenamiento: 182.6s

**Representación binaria por clase:**
- Dígito 0 (binario: 0000): Precisión=0.917, Recall=0.954, F1=0.935
- Dígito 1 (binario: 0001): Precisión=0.906, Recall=0.943, F1=0.924
- Dígito 2 (binario: 0010): Precisión=0.923, Recall=0.918, F1=0.921
- Dígito 3 (binario: 0011): Precisión=0.938, Recall=0.938, F1=0.938
- Dígito 4 (binario: 0100): Precisión=0.950, Recall=0.923, F1=0.936
- Dígito 5 (binario: 0101): Precisión=0.909, Recall=0.899, F1=0.904
- Dígito 6 (binario: 0110): Precisión=0.963, Recall=0.972, F1=0.968
- Dígito 7 (binario: 0111): Precisión=0.932, Recall=0.932, F1=0.932
- Dígito 8 (binario: 1000): Precisión=0.925, Recall=0.874, F1=0.899
- Dígito 9 (binario: 1001): Precisión=0.959, Recall=0.911, F1=0.934

#### Binary_Base_3.0_lr_3_epochs_30_batch

**Parámetros:**
- Arquitectura: [784, 100, 4]
- Épocas: 3
- Tamaño de lote: 30
- Tasa de aprendizaje: 3.0

**Métricas de desempeño:**
- Precisión global: 0.877
- Precisión macro: 0.885
- Recall macro: 0.877
- F1 macro: 0.879
- Tiempo de entrenamiento: 5.4s

**Representación binaria por clase:**
- Dígito 0 (binario: 0000): Precisión=0.894, Recall=0.944, F1=0.919
- Dígito 1 (binario: 0001): Precisión=0.819, Recall=0.959, F1=0.884
- Dígito 2 (binario: 0010): Precisión=0.837, Recall=0.862, F1=0.849
- Dígito 3 (binario: 0011): Precisión=0.853, Recall=0.857, F1=0.855
- Dígito 4 (binario: 0100): Precisión=0.920, Recall=0.836, F1=0.876
- Dígito 5 (binario: 0101): Precisión=0.893, Recall=0.836, F1=0.863
- Dígito 6 (binario: 0110): Precisión=0.884, Recall=0.958, F1=0.920
- Dígito 7 (binario: 0111): Precisión=0.924, Recall=0.832, F1=0.876
- Dígito 8 (binario: 1000): Precisión=0.923, Recall=0.783, F1=0.847
- Dígito 9 (binario: 1001): Precisión=0.901, Recall=0.901, F1=0.901

#### Binary_Base_3.0_lr_10_epochs_30_batch

**Parámetros:**
- Arquitectura: [784, 100, 4]
- Épocas: 10
- Tamaño de lote: 30
- Tasa de aprendizaje: 3.0

**Métricas de desempeño:**
- Precisión global: 0.916
- Precisión macro: 0.922
- Recall macro: 0.916
- F1 macro: 0.919
- Tiempo de entrenamiento: 17.8s

**Representación binaria por clase:**
- Dígito 0 (binario: 0000): Precisión=0.913, Recall=0.964, F1=0.938
- Dígito 1 (binario: 0001): Precisión=0.910, Recall=0.943, F1=0.927
- Dígito 2 (binario: 0010): Precisión=0.929, Recall=0.872, F1=0.900
- Dígito 3 (binario: 0011): Precisión=0.918, Recall=0.910, F1=0.914
- Dígito 4 (binario: 0100): Precisión=0.912, Recall=0.903, F1=0.908
- Dígito 5 (binario: 0101): Precisión=0.881, Recall=0.899, F1=0.890
- Dígito 6 (binario: 0110): Precisión=0.941, Recall=0.963, F1=0.952
- Dígito 7 (binario: 0111): Precisión=0.927, Recall=0.932, F1=0.930
- Dígito 8 (binario: 1000): Precisión=0.945, Recall=0.874, F1=0.908
- Dígito 9 (binario: 1001): Precisión=0.938, Recall=0.901, F1=0.920

#### Binary_Base_3.0_lr_50_epochs_30_batch

**Parámetros:**
- Arquitectura: [784, 100, 4]
- Épocas: 50
- Tamaño de lote: 30
- Tasa de aprendizaje: 3.0

**Métricas de desempeño:**
- Precisión global: 0.929
- Precisión macro: 0.933
- Recall macro: 0.929
- F1 macro: 0.931
- Tiempo de entrenamiento: 89.2s

**Representación binaria por clase:**
- Dígito 0 (binario: 0000): Precisión=0.922, Recall=0.954, F1=0.938
- Dígito 1 (binario: 0001): Precisión=0.906, Recall=0.943, F1=0.924
- Dígito 2 (binario: 0010): Precisión=0.915, Recall=0.934, F1=0.924
- Dígito 3 (binario: 0011): Precisión=0.951, Recall=0.924, F1=0.937
- Dígito 4 (binario: 0100): Precisión=0.959, Recall=0.908, F1=0.933
- Dígito 5 (binario: 0101): Precisión=0.914, Recall=0.905, F1=0.910
- Dígito 6 (binario: 0110): Precisión=0.959, Recall=0.972, F1=0.965
- Dígito 7 (binario: 0111): Precisión=0.908, Recall=0.927, F1=0.917
- Dígito 8 (binario: 1000): Precisión=0.932, Recall=0.899, F1=0.915
- Dígito 9 (binario: 1001): Precisión=0.964, Recall=0.921, F1=0.942

#### Binary_Base_3.0_lr_100_epochs_30_batch

**Parámetros:**
- Arquitectura: [784, 100, 4]
- Épocas: 100
- Tamaño de lote: 30
- Tasa de aprendizaje: 3.0

**Métricas de desempeño:**
- Precisión global: 0.934
- Precisión macro: 0.937
- Recall macro: 0.935
- F1 macro: 0.936
- Tiempo de entrenamiento: 178.4s

**Representación binaria por clase:**
- Dígito 0 (binario: 0000): Precisión=0.917, Recall=0.959, F1=0.938
- Dígito 1 (binario: 0001): Precisión=0.925, Recall=0.948, F1=0.936
- Dígito 2 (binario: 0010): Precisión=0.949, Recall=0.954, F1=0.952
- Dígito 3 (binario: 0011): Precisión=0.932, Recall=0.919, F1=0.926
- Dígito 4 (binario: 0100): Precisión=0.935, Recall=0.908, F1=0.922
- Dígito 5 (binario: 0101): Precisión=0.916, Recall=0.926, F1=0.921
- Dígito 6 (binario: 0110): Precisión=0.954, Recall=0.958, F1=0.956
- Dígito 7 (binario: 0111): Precisión=0.947, Recall=0.937, F1=0.942
- Dígito 8 (binario: 1000): Precisión=0.952, Recall=0.904, F1=0.927
- Dígito 9 (binario: 1001): Precisión=0.945, Recall=0.931, F1=0.938

#### Binary_Base_10.0_lr_3_epochs_100_batch

**Parámetros:**
- Arquitectura: [784, 100, 4]
- Épocas: 3
- Tamaño de lote: 100
- Tasa de aprendizaje: 10.0

**Métricas de desempeño:**
- Precisión global: 0.880
- Precisión macro: 0.885
- Recall macro: 0.879
- F1 macro: 0.880
- Tiempo de entrenamiento: 5.3s

**Representación binaria por clase:**
- Dígito 0 (binario: 0000): Precisión=0.854, Recall=0.949, F1=0.899
- Dígito 1 (binario: 0001): Precisión=0.878, Recall=0.928, F1=0.902
- Dígito 2 (binario: 0010): Precisión=0.804, Recall=0.898, F1=0.848
- Dígito 3 (binario: 0011): Precisión=0.882, Recall=0.852, F1=0.867
- Dígito 4 (binario: 0100): Precisión=0.876, Recall=0.889, F1=0.882
- Dígito 5 (binario: 0101): Precisión=0.876, Recall=0.783, F1=0.827
- Dígito 6 (binario: 0110): Precisión=0.892, Recall=0.958, F1=0.924
- Dígito 7 (binario: 0111): Precisión=0.894, Recall=0.885, F1=0.889
- Dígito 8 (binario: 1000): Precisión=0.941, Recall=0.803, F1=0.866
- Dígito 9 (binario: 1001): Precisión=0.950, Recall=0.847, F1=0.896

#### Binary_Base_10.0_lr_10_epochs_100_batch

**Parámetros:**
- Arquitectura: [784, 100, 4]
- Épocas: 10
- Tamaño de lote: 100
- Tasa de aprendizaje: 10.0

**Métricas de desempeño:**
- Precisión global: 0.913
- Precisión macro: 0.917
- Recall macro: 0.912
- F1 macro: 0.915
- Tiempo de entrenamiento: 17.7s

**Representación binaria por clase:**
- Dígito 0 (binario: 0000): Precisión=0.917, Recall=0.954, F1=0.935
- Dígito 1 (binario: 0001): Precisión=0.933, Recall=0.928, F1=0.930
- Dígito 2 (binario: 0010): Precisión=0.905, Recall=0.878, F1=0.891
- Dígito 3 (binario: 0011): Precisión=0.910, Recall=0.914, F1=0.912
- Dígito 4 (binario: 0100): Precisión=0.901, Recall=0.923, F1=0.912
- Dígito 5 (binario: 0101): Precisión=0.904, Recall=0.894, F1=0.899
- Dígito 6 (binario: 0110): Precisión=0.924, Recall=0.967, F1=0.945
- Dígito 7 (binario: 0111): Precisión=0.931, Recall=0.916, F1=0.923
- Dígito 8 (binario: 1000): Precisión=0.895, Recall=0.864, F1=0.879
- Dígito 9 (binario: 1001): Precisión=0.952, Recall=0.887, F1=0.918

#### Binary_Base_10.0_lr_50_epochs_100_batch

**Parámetros:**
- Arquitectura: [784, 100, 4]
- Épocas: 50
- Tamaño de lote: 100
- Tasa de aprendizaje: 10.0

**Métricas de desempeño:**
- Precisión global: 0.921
- Precisión macro: 0.924
- Recall macro: 0.921
- F1 macro: 0.922
- Tiempo de entrenamiento: 88.4s

**Representación binaria por clase:**
- Dígito 0 (binario: 0000): Precisión=0.900, Recall=0.954, F1=0.926
- Dígito 1 (binario: 0001): Precisión=0.920, Recall=0.943, F1=0.931
- Dígito 2 (binario: 0010): Precisión=0.927, Recall=0.908, F1=0.918
- Dígito 3 (binario: 0011): Precisión=0.938, Recall=0.933, F1=0.936
- Dígito 4 (binario: 0100): Precisión=0.944, Recall=0.899, F1=0.921
- Dígito 5 (binario: 0101): Precisión=0.908, Recall=0.884, F1=0.895
- Dígito 6 (binario: 0110): Precisión=0.929, Recall=0.967, F1=0.948
- Dígito 7 (binario: 0111): Precisión=0.916, Recall=0.916, F1=0.916
- Dígito 8 (binario: 1000): Precisión=0.936, Recall=0.884, F1=0.909
- Dígito 9 (binario: 1001): Precisión=0.925, Recall=0.916, F1=0.921

#### Binary_Base_10.0_lr_100_epochs_100_batch

**Parámetros:**
- Arquitectura: [784, 100, 4]
- Épocas: 100
- Tamaño de lote: 100
- Tasa de aprendizaje: 10.0

**Métricas de desempeño:**
- Precisión global: 0.933
- Precisión macro: 0.937
- Recall macro: 0.933
- F1 macro: 0.934
- Tiempo de entrenamiento: 176.7s

**Representación binaria por clase:**
- Dígito 0 (binario: 0000): Precisión=0.918, Recall=0.970, F1=0.943
- Dígito 1 (binario: 0001): Precisión=0.915, Recall=0.938, F1=0.926
- Dígito 2 (binario: 0010): Precisión=0.938, Recall=0.923, F1=0.931
- Dígito 3 (binario: 0011): Precisión=0.929, Recall=0.933, F1=0.931
- Dígito 4 (binario: 0100): Precisión=0.945, Recall=0.918, F1=0.931
- Dígito 5 (binario: 0101): Precisión=0.915, Recall=0.910, F1=0.912
- Dígito 6 (binario: 0110): Precisión=0.954, Recall=0.972, F1=0.963
- Dígito 7 (binario: 0111): Precisión=0.947, Recall=0.932, F1=0.939
- Dígito 8 (binario: 1000): Precisión=0.942, Recall=0.909, F1=0.925
- Dígito 9 (binario: 1001): Precisión=0.964, Recall=0.921, F1=0.942

#### Binary_Alt_0.5_lr_3_epochs_5_batch

**Parámetros:**
- Arquitectura: [784, 50, 25, 4]
- Épocas: 3
- Tamaño de lote: 5
- Tasa de aprendizaje: 0.5

**Métricas de desempeño:**
- Precisión global: 0.882
- Precisión macro: 0.887
- Recall macro: 0.882
- F1 macro: 0.882
- Tiempo de entrenamiento: 3.2s

**Representación binaria por clase:**
- Dígito 0 (binario: 0000): Precisión=0.824, Recall=0.949, F1=0.882
- Dígito 1 (binario: 0001): Precisión=0.815, Recall=0.954, F1=0.879
- Dígito 2 (binario: 0010): Precisión=0.866, Recall=0.888, F1=0.877
- Dígito 3 (binario: 0011): Precisión=0.874, Recall=0.829, F1=0.851
- Dígito 4 (binario: 0100): Precisión=0.902, Recall=0.894, F1=0.898
- Dígito 5 (binario: 0101): Precisión=0.870, Recall=0.852, F1=0.861
- Dígito 6 (binario: 0110): Precisión=0.915, Recall=0.949, F1=0.932
- Dígito 7 (binario: 0111): Precisión=0.954, Recall=0.864, F1=0.907
- Dígito 8 (binario: 1000): Precisión=0.944, Recall=0.763, F1=0.844
- Dígito 9 (binario: 1001): Precisión=0.909, Recall=0.882, F1=0.895

#### Binary_Alt_0.5_lr_10_epochs_5_batch

**Parámetros:**
- Arquitectura: [784, 50, 25, 4]
- Épocas: 10
- Tamaño de lote: 5
- Tasa de aprendizaje: 0.5

**Métricas de desempeño:**
- Precisión global: 0.901
- Precisión macro: 0.911
- Recall macro: 0.901
- F1 macro: 0.905
- Tiempo de entrenamiento: 10.6s

**Representación binaria por clase:**
- Dígito 0 (binario: 0000): Precisión=0.957, Recall=0.909, F1=0.932
- Dígito 1 (binario: 0001): Precisión=0.901, Recall=0.943, F1=0.922
- Dígito 2 (binario: 0010): Precisión=0.939, Recall=0.857, F1=0.896
- Dígito 3 (binario: 0011): Precisión=0.915, Recall=0.871, F1=0.893
- Dígito 4 (binario: 0100): Precisión=0.917, Recall=0.850, F1=0.882
- Dígito 5 (binario: 0101): Precisión=0.855, Recall=0.905, F1=0.879
- Dígito 6 (binario: 0110): Precisión=0.950, Recall=0.963, F1=0.956
- Dígito 7 (binario: 0111): Precisión=0.898, Recall=0.921, F1=0.910
- Dígito 8 (binario: 1000): Precisión=0.943, Recall=0.828, F1=0.882
- Dígito 9 (binario: 1001): Precisión=0.838, Recall=0.966, F1=0.897

#### Binary_Alt_0.5_lr_50_epochs_5_batch

**Parámetros:**
- Arquitectura: [784, 50, 25, 4]
- Épocas: 50
- Tamaño de lote: 5
- Tasa de aprendizaje: 0.5

**Métricas de desempeño:**
- Precisión global: 0.929
- Precisión macro: 0.931
- Recall macro: 0.929
- F1 macro: 0.930
- Tiempo de entrenamiento: 53.1s

**Representación binaria por clase:**
- Dígito 0 (binario: 0000): Precisión=0.917, Recall=0.954, F1=0.935
- Dígito 1 (binario: 0001): Precisión=0.924, Recall=0.938, F1=0.931
- Dígito 2 (binario: 0010): Precisión=0.913, Recall=0.913, F1=0.913
- Dígito 3 (binario: 0011): Precisión=0.933, Recall=0.929, F1=0.931
- Dígito 4 (binario: 0100): Precisión=0.936, Recall=0.918, F1=0.927
- Dígito 5 (binario: 0101): Precisión=0.940, Recall=0.910, F1=0.925
- Dígito 6 (binario: 0110): Precisión=0.954, Recall=0.972, F1=0.963
- Dígito 7 (binario: 0111): Precisión=0.937, Recall=0.932, F1=0.934
- Dígito 8 (binario: 1000): Precisión=0.927, Recall=0.899, F1=0.913
- Dígito 9 (binario: 1001): Precisión=0.926, Recall=0.921, F1=0.923

#### Binary_Alt_0.5_lr_100_epochs_5_batch

**Parámetros:**
- Arquitectura: [784, 50, 25, 4]
- Épocas: 100
- Tamaño de lote: 5
- Tasa de aprendizaje: 0.5

**Métricas de desempeño:**
- Precisión global: 0.926
- Precisión macro: 0.930
- Recall macro: 0.926
- F1 macro: 0.928
- Tiempo de entrenamiento: 106.0s

**Representación binaria por clase:**
- Dígito 0 (binario: 0000): Precisión=0.926, Recall=0.949, F1=0.937
- Dígito 1 (binario: 0001): Precisión=0.920, Recall=0.943, F1=0.931
- Dígito 2 (binario: 0010): Precisión=0.906, Recall=0.939, F1=0.922
- Dígito 3 (binario: 0011): Precisión=0.941, Recall=0.919, F1=0.930
- Dígito 4 (binario: 0100): Precisión=0.922, Recall=0.908, F1=0.915
- Dígito 5 (binario: 0101): Precisión=0.934, Recall=0.899, F1=0.916
- Dígito 6 (binario: 0110): Precisión=0.963, Recall=0.963, F1=0.963
- Dígito 7 (binario: 0111): Precisión=0.923, Recall=0.942, F1=0.933
- Dígito 8 (binario: 1000): Precisión=0.936, Recall=0.889, F1=0.912
- Dígito 9 (binario: 1001): Precisión=0.934, Recall=0.906, F1=0.920

#### Binary_Alt_1.0_lr_3_epochs_10_batch

**Parámetros:**
- Arquitectura: [784, 50, 25, 4]
- Épocas: 3
- Tamaño de lote: 10
- Tasa de aprendizaje: 1.0

**Métricas de desempeño:**
- Precisión global: 0.873
- Precisión macro: 0.884
- Recall macro: 0.872
- F1 macro: 0.875
- Tiempo de entrenamiento: 3.1s

**Representación binaria por clase:**
- Dígito 0 (binario: 0000): Precisión=0.838, Recall=0.919, F1=0.877
- Dígito 1 (binario: 0001): Precisión=0.966, Recall=0.876, F1=0.919
- Dígito 2 (binario: 0010): Precisión=0.762, Recall=0.883, F1=0.818
- Dígito 3 (binario: 0011): Precisión=0.890, Recall=0.810, F1=0.848
- Dígito 4 (binario: 0100): Precisión=0.825, Recall=0.908, F1=0.864
- Dígito 5 (binario: 0101): Precisión=0.901, Recall=0.820, F1=0.859
- Dígito 6 (binario: 0110): Precisión=0.867, Recall=0.972, F1=0.917
- Dígito 7 (binario: 0111): Precisión=0.888, Recall=0.916, F1=0.902
- Dígito 8 (binario: 1000): Precisión=0.951, Recall=0.783, F1=0.859
- Dígito 9 (binario: 1001): Precisión=0.950, Recall=0.837, F1=0.890

#### Binary_Alt_1.0_lr_10_epochs_10_batch

**Parámetros:**
- Arquitectura: [784, 50, 25, 4]
- Épocas: 10
- Tamaño de lote: 10
- Tasa de aprendizaje: 1.0

**Métricas de desempeño:**
- Precisión global: 0.926
- Precisión macro: 0.930
- Recall macro: 0.926
- F1 macro: 0.928
- Tiempo de entrenamiento: 10.2s

**Representación binaria por clase:**
- Dígito 0 (binario: 0000): Precisión=0.946, Recall=0.970, F1=0.957
- Dígito 1 (binario: 0001): Precisión=0.947, Recall=0.918, F1=0.932
- Dígito 2 (binario: 0010): Precisión=0.900, Recall=0.918, F1=0.909
- Dígito 3 (binario: 0011): Precisión=0.939, Recall=0.881, F1=0.909
- Dígito 4 (binario: 0100): Precisión=0.908, Recall=0.908, F1=0.908
- Dígito 5 (binario: 0101): Precisión=0.915, Recall=0.915, F1=0.915
- Dígito 6 (binario: 0110): Precisión=0.942, Recall=0.977, F1=0.959
- Dígito 7 (binario: 0111): Precisión=0.924, Recall=0.953, F1=0.938
- Dígito 8 (binario: 1000): Precisión=0.937, Recall=0.904, F1=0.920
- Dígito 9 (binario: 1001): Precisión=0.944, Recall=0.921, F1=0.933

#### Binary_Alt_1.0_lr_50_epochs_10_batch

**Parámetros:**
- Arquitectura: [784, 50, 25, 4]
- Épocas: 50
- Tamaño de lote: 10
- Tasa de aprendizaje: 1.0

**Métricas de desempeño:**
- Precisión global: 0.924
- Precisión macro: 0.929
- Recall macro: 0.924
- F1 macro: 0.926
- Tiempo de entrenamiento: 51.1s

**Representación binaria por clase:**
- Dígito 0 (binario: 0000): Precisión=0.925, Recall=0.944, F1=0.935
- Dígito 1 (binario: 0001): Precisión=0.915, Recall=0.948, F1=0.932
- Dígito 2 (binario: 0010): Precisión=0.937, Recall=0.913, F1=0.925
- Dígito 3 (binario: 0011): Precisión=0.909, Recall=0.900, F1=0.904
- Dígito 4 (binario: 0100): Precisión=0.955, Recall=0.918, F1=0.936
- Dígito 5 (binario: 0101): Precisión=0.901, Recall=0.915, F1=0.908
- Dígito 6 (binario: 0110): Precisión=0.942, Recall=0.977, F1=0.959
- Dígito 7 (binario: 0111): Precisión=0.932, Recall=0.927, F1=0.929
- Dígito 8 (binario: 1000): Precisión=0.923, Recall=0.904, F1=0.913
- Dígito 9 (binario: 1001): Precisión=0.953, Recall=0.897, F1=0.924

#### Binary_Alt_1.0_lr_100_epochs_10_batch

**Parámetros:**
- Arquitectura: [784, 50, 25, 4]
- Épocas: 100
- Tamaño de lote: 10
- Tasa de aprendizaje: 1.0

**Métricas de desempeño:**
- Precisión global: 0.930
- Precisión macro: 0.934
- Recall macro: 0.930
- F1 macro: 0.932
- Tiempo de entrenamiento: 102.2s

**Representación binaria por clase:**
- Dígito 0 (binario: 0000): Precisión=0.936, Recall=0.959, F1=0.947
- Dígito 1 (binario: 0001): Precisión=0.924, Recall=0.943, F1=0.934
- Dígito 2 (binario: 0010): Precisión=0.933, Recall=0.918, F1=0.925
- Dígito 3 (binario: 0011): Precisión=0.932, Recall=0.910, F1=0.920
- Dígito 4 (binario: 0100): Precisión=0.927, Recall=0.923, F1=0.925
- Dígito 5 (binario: 0101): Precisión=0.944, Recall=0.889, F1=0.916
- Dígito 6 (binario: 0110): Precisión=0.959, Recall=0.972, F1=0.965
- Dígito 7 (binario: 0111): Precisión=0.918, Recall=0.937, F1=0.927
- Dígito 8 (binario: 1000): Precisión=0.928, Recall=0.914, F1=0.921
- Dígito 9 (binario: 1001): Precisión=0.936, Recall=0.936, F1=0.936

#### Binary_Alt_3.0_lr_3_epochs_30_batch

**Parámetros:**
- Arquitectura: [784, 50, 25, 4]
- Épocas: 3
- Tamaño de lote: 30
- Tasa de aprendizaje: 3.0

**Métricas de desempeño:**
- Precisión global: 0.877
- Precisión macro: 0.884
- Recall macro: 0.877
- F1 macro: 0.879
- Tiempo de entrenamiento: 3.0s

**Representación binaria por clase:**
- Dígito 0 (binario: 0000): Precisión=0.858, Recall=0.954, F1=0.904
- Dígito 1 (binario: 0001): Precisión=0.852, Recall=0.918, F1=0.883
- Dígito 2 (binario: 0010): Precisión=0.907, Recall=0.847, F1=0.876
- Dígito 3 (binario: 0011): Precisión=0.921, Recall=0.776, F1=0.842
- Dígito 4 (binario: 0100): Precisión=0.836, Recall=0.937, F1=0.884
- Dígito 5 (binario: 0101): Precisión=0.859, Recall=0.873, F1=0.866
- Dígito 6 (binario: 0110): Precisión=0.928, Recall=0.902, F1=0.915
- Dígito 7 (binario: 0111): Precisión=0.948, Recall=0.853, F1=0.898
- Dígito 8 (binario: 1000): Precisión=0.849, Recall=0.854, F1=0.851
- Dígito 9 (binario: 1001): Precisión=0.879, Recall=0.857, F1=0.868

#### Binary_Alt_3.0_lr_10_epochs_30_batch

**Parámetros:**
- Arquitectura: [784, 50, 25, 4]
- Épocas: 10
- Tamaño de lote: 30
- Tasa de aprendizaje: 3.0

**Métricas de desempeño:**
- Precisión global: 0.915
- Precisión macro: 0.918
- Recall macro: 0.915
- F1 macro: 0.916
- Tiempo de entrenamiento: 10.0s

**Representación binaria por clase:**
- Dígito 0 (binario: 0000): Precisión=0.901, Recall=0.970, F1=0.934
- Dígito 1 (binario: 0001): Precisión=0.892, Recall=0.938, F1=0.915
- Dígito 2 (binario: 0010): Precisión=0.946, Recall=0.888, F1=0.916
- Dígito 3 (binario: 0011): Precisión=0.913, Recall=0.895, F1=0.904
- Dígito 4 (binario: 0100): Precisión=0.916, Recall=0.899, F1=0.907
- Dígito 5 (binario: 0101): Precisión=0.854, Recall=0.894, F1=0.873
- Dígito 6 (binario: 0110): Precisión=0.962, Recall=0.953, F1=0.958
- Dígito 7 (binario: 0111): Precisión=0.935, Recall=0.911, F1=0.923
- Dígito 8 (binario: 1000): Precisión=0.935, Recall=0.879, F1=0.906
- Dígito 9 (binario: 1001): Precisión=0.926, Recall=0.921, F1=0.923

#### Binary_Alt_3.0_lr_50_epochs_30_batch

**Parámetros:**
- Arquitectura: [784, 50, 25, 4]
- Épocas: 50
- Tamaño de lote: 30
- Tasa de aprendizaje: 3.0

**Métricas de desempeño:**
- Precisión global: 0.930
- Precisión macro: 0.932
- Recall macro: 0.930
- F1 macro: 0.931
- Tiempo de entrenamiento: 50.0s

**Representación binaria por clase:**
- Dígito 0 (binario: 0000): Precisión=0.941, Recall=0.970, F1=0.955
- Dígito 1 (binario: 0001): Precisión=0.915, Recall=0.948, F1=0.932
- Dígito 2 (binario: 0010): Precisión=0.919, Recall=0.929, F1=0.924
- Dígito 3 (binario: 0011): Precisión=0.902, Recall=0.924, F1=0.913
- Dígito 4 (binario: 0100): Precisión=0.937, Recall=0.928, F1=0.932
- Dígito 5 (binario: 0101): Precisión=0.918, Recall=0.894, F1=0.906
- Dígito 6 (binario: 0110): Precisión=0.954, Recall=0.963, F1=0.958
- Dígito 7 (binario: 0111): Precisión=0.947, Recall=0.927, F1=0.937
- Dígito 8 (binario: 1000): Precisión=0.932, Recall=0.894, F1=0.912
- Dígito 9 (binario: 1001): Precisión=0.954, Recall=0.921, F1=0.937

#### Binary_Alt_3.0_lr_100_epochs_30_batch

**Parámetros:**
- Arquitectura: [784, 50, 25, 4]
- Épocas: 100
- Tamaño de lote: 30
- Tasa de aprendizaje: 3.0

**Métricas de desempeño:**
- Precisión global: 0.929
- Precisión macro: 0.932
- Recall macro: 0.929
- F1 macro: 0.930
- Tiempo de entrenamiento: 99.8s

**Representación binaria por clase:**
- Dígito 0 (binario: 0000): Precisión=0.944, Recall=0.939, F1=0.941
- Dígito 1 (binario: 0001): Precisión=0.934, Recall=0.954, F1=0.944
- Dígito 2 (binario: 0010): Precisión=0.892, Recall=0.923, F1=0.907
- Dígito 3 (binario: 0011): Precisión=0.946, Recall=0.914, F1=0.930
- Dígito 4 (binario: 0100): Precisión=0.926, Recall=0.913, F1=0.920
- Dígito 5 (binario: 0101): Precisión=0.921, Recall=0.926, F1=0.923
- Dígito 6 (binario: 0110): Precisión=0.946, Recall=0.972, F1=0.959
- Dígito 7 (binario: 0111): Precisión=0.937, Recall=0.937, F1=0.937
- Dígito 8 (binario: 1000): Precisión=0.931, Recall=0.889, F1=0.910
- Dígito 9 (binario: 1001): Precisión=0.940, Recall=0.921, F1=0.930

#### Binary_Alt_10.0_lr_3_epochs_100_batch

**Parámetros:**
- Arquitectura: [784, 50, 25, 4]
- Épocas: 3
- Tamaño de lote: 100
- Tasa de aprendizaje: 10.0

**Métricas de desempeño:**
- Precisión global: 0.837
- Precisión macro: 0.855
- Recall macro: 0.836
- F1 macro: 0.841
- Tiempo de entrenamiento: 3.1s

**Representación binaria por clase:**
- Dígito 0 (binario: 0000): Precisión=0.931, Recall=0.893, F1=0.912
- Dígito 1 (binario: 0001): Precisión=0.742, Recall=0.933, F1=0.826
- Dígito 2 (binario: 0010): Precisión=0.898, Recall=0.806, F1=0.849
- Dígito 3 (binario: 0011): Precisión=0.878, Recall=0.752, F1=0.810
- Dígito 4 (binario: 0100): Precisión=0.855, Recall=0.797, F1=0.825
- Dígito 5 (binario: 0101): Precisión=0.823, Recall=0.788, F1=0.805
- Dígito 6 (binario: 0110): Precisión=0.919, Recall=0.898, F1=0.908
- Dígito 7 (binario: 0111): Precisión=0.933, Recall=0.728, F1=0.818
- Dígito 8 (binario: 1000): Precisión=0.828, Recall=0.803, F1=0.815
- Dígito 9 (binario: 1001): Precisión=0.742, Recall=0.966, F1=0.839

#### Binary_Alt_10.0_lr_10_epochs_100_batch

**Parámetros:**
- Arquitectura: [784, 50, 25, 4]
- Épocas: 10
- Tamaño de lote: 100
- Tasa de aprendizaje: 10.0

**Métricas de desempeño:**
- Precisión global: 0.916
- Precisión macro: 0.924
- Recall macro: 0.916
- F1 macro: 0.920
- Tiempo de entrenamiento: 9.9s

**Representación binaria por clase:**
- Dígito 0 (binario: 0000): Precisión=0.939, Recall=0.934, F1=0.936
- Dígito 1 (binario: 0001): Precisión=0.963, Recall=0.933, F1=0.948
- Dígito 2 (binario: 0010): Precisión=0.932, Recall=0.903, F1=0.917
- Dígito 3 (binario: 0011): Precisión=0.902, Recall=0.881, F1=0.892
- Dígito 4 (binario: 0100): Precisión=0.909, Recall=0.870, F1=0.889
- Dígito 5 (binario: 0101): Precisión=0.876, Recall=0.931, F1=0.903
- Dígito 6 (binario: 0110): Precisión=0.954, Recall=0.963, F1=0.958
- Dígito 7 (binario: 0111): Precisión=0.918, Recall=0.942, F1=0.930
- Dígito 8 (binario: 1000): Precisión=0.935, Recall=0.879, F1=0.906
- Dígito 9 (binario: 1001): Precisión=0.908, Recall=0.926, F1=0.917

#### Binary_Alt_10.0_lr_50_epochs_100_batch

**Parámetros:**
- Arquitectura: [784, 50, 25, 4]
- Épocas: 50
- Tamaño de lote: 100
- Tasa de aprendizaje: 10.0

**Métricas de desempeño:**
- Precisión global: 0.930
- Precisión macro: 0.933
- Recall macro: 0.930
- F1 macro: 0.931
- Tiempo de entrenamiento: 49.5s

**Representación binaria por clase:**
- Dígito 0 (binario: 0000): Precisión=0.955, Recall=0.964, F1=0.960
- Dígito 1 (binario: 0001): Precisión=0.920, Recall=0.954, F1=0.937
- Dígito 2 (binario: 0010): Precisión=0.931, Recall=0.893, F1=0.911
- Dígito 3 (binario: 0011): Precisión=0.902, Recall=0.924, F1=0.913
- Dígito 4 (binario: 0100): Precisión=0.940, Recall=0.913, F1=0.926
- Dígito 5 (binario: 0101): Precisión=0.940, Recall=0.905, F1=0.922
- Dígito 6 (binario: 0110): Precisión=0.937, Recall=0.967, F1=0.952
- Dígito 7 (binario: 0111): Precisión=0.927, Recall=0.937, F1=0.932
- Dígito 8 (binario: 1000): Precisión=0.929, Recall=0.919, F1=0.924
- Dígito 9 (binario: 1001): Precisión=0.944, Recall=0.921, F1=0.933

#### Binary_Alt_10.0_lr_100_epochs_100_batch

**Parámetros:**
- Arquitectura: [784, 50, 25, 4]
- Épocas: 100
- Tamaño de lote: 100
- Tasa de aprendizaje: 10.0

**Métricas de desempeño:**
- Precisión global: 0.932
- Precisión macro: 0.935
- Recall macro: 0.932
- F1 macro: 0.933
- Tiempo de entrenamiento: 99.0s

**Representación binaria por clase:**
- Dígito 0 (binario: 0000): Precisión=0.945, Recall=0.954, F1=0.949
- Dígito 1 (binario: 0001): Precisión=0.958, Recall=0.948, F1=0.953
- Dígito 2 (binario: 0010): Precisión=0.932, Recall=0.913, F1=0.923
- Dígito 3 (binario: 0011): Precisión=0.918, Recall=0.910, F1=0.914
- Dígito 4 (binario: 0100): Precisión=0.945, Recall=0.918, F1=0.931
- Dígito 5 (binario: 0101): Precisión=0.935, Recall=0.921, F1=0.928
- Dígito 6 (binario: 0110): Precisión=0.945, Recall=0.967, F1=0.956
- Dígito 7 (binario: 0111): Precisión=0.938, Recall=0.948, F1=0.943
- Dígito 8 (binario: 1000): Precisión=0.920, Recall=0.924, F1=0.922
- Dígito 9 (binario: 1001): Precisión=0.912, Recall=0.916, F1=0.914

## GRÁFICOS DE ANÁLISIS

### Precisión vs Tasa de Aprendizaje
![Precisión vs Tasa de Aprendizaje](binary_accuracy_vs_lr.png)

### Precisión vs Número de Épocas
![Precisión vs Épocas](binary_accuracy_vs_epochs.png)

### Precisión vs Tamaño del Lote
![Precisión vs Tamaño del Lote](binary_accuracy_vs_batch_size.png)

### Distribución de Precisión
![Distribución de Precisión](binary_accuracy_boxplot.png)

## CONCLUSIONES

### Mejor Configuración

La configuración con mejor desempeño fue **Binary_Base_0.5_lr_100_epochs_5_batch** con una precisión de 0.937. Esta configuración utilizó una arquitectura [784, 100, 4] con 100 épocas, tamaño de lote 5 y tasa de aprendizaje 0.5.

### Comparación con Enfoque Tradicional

El enfoque de etiquetas binarias tiene las siguientes características:

**Ventajas:**
- Reduce la dimensionalidad de salida (4 vs 10 neuronas)
- Puede ser más eficiente en términos de parámetros
- Representa naturalmente la relación entre dígitos

**Desventajas:**
- Mayor complejidad en la interpretación de errores
- Posibles ambigüedades en la clasificación
- Menor precisión en algunos casos debido a la compresión

### Recomendaciones

Para aplicaciones prácticas, el enfoque tradicional de 10 clases separadas generalmente ofrece mejor precisión. El enfoque binario puede ser útil en escenarios con restricciones de recursos o cuando se busca una representación más compacta.

---

*Reporte generado automáticamente por el sistema de experimentación*
