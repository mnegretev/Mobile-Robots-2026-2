## Parámetros de suavizado (descenso de gradiente)

| Caso | w1 | w2 | steps | Observación |
|---|---:|---:|---:|---|
| Poco suavizado | 0.05 | 0.95 | 200 | Se mantiene muy cercano a la ruta A*; suavizado apenas visible. |
| Demasiado suavizado (no funcional) | 0.99 | 0.01 | 50000 | La suavidad domina; puede cortar esquinas/deformarse y perder validez. |
| Satisfactorio | 0.90 | 0.10 | 10000 | Compromiso entre suavidad y fidelidad; trayectoria continua y estable. |

### Discusión breve (w1 vs w2)
En el gradiente, **w1** pondera la suavidad (penaliza cambios bruscos/curvatura) y **w2** pondera la fidelidad a la ruta original **Q**. Al aumentar **w1** y disminuir **w2**, la trayectoria **P** se vuelve más suave pero se aleja de **Q**; si se exagera, puede volverse no funcional (p. ej., recortar demasiado o comportarse extraño). Al disminuir **w1** o aumentar **w2**, **P** se pega a **Q** y el suavizado es mínimo. El parámetro **steps** controla cuántas iteraciones se permiten: más pasos puede mejorar la convergencia, pero también acentuar el sobre-suavizado si **w1** domina.
