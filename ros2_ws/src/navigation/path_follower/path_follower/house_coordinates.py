#!/usr/bin/env python3
# house_coordinates.py

NAV_TARGETS = {
    "dormitorio": {
        "root": [-0.926, 0.674, 0.0471],
        "cama": [-3.85, 2.1, 0.00378],
        "ventana": [-6.3, 1.19, 0.00022],
        "silla": [-5.99, -2.08, 0.00184],
        "pelota": [-3.86, -2.55, 0.00282],
        "cuadro grupo": [-3.99, 0.705, 0.00416],
        "cuadro persona": [-4.15, -0.441, -0.0000896],
        "entrada": [-0.142, 0.519, 0.0329],
        "mesa noche": [-2.04, 3.79, 0.00517],
        "armario": [-1.41, 3.68, 0.00203]
    },
    "sala": {
        "root": [2.79, 0.544, 0.00241],
        "comedor": [1.8, 5.09, 0.0017],
        "gym": [5.64, 3.65, 0.00425],
        "tv": [2.94, -2.67, -0.000328],
        "cuadro persona": [0.954, -3.19, 0.00249],
        "varios cuadros": [5.07, -3.4, 0.00149],
        "aire acondicionado": [0.358, -2.84, -0.00238],
        "zapateria": [6.55, -3.08, 0.00104]
    },
    "cocina": {
        "root": [10.4, -2.91, 0.0049],
        "puerta": [8.16, -3.56, 0.00274],
        "comedor": [10.1, 2.56, 0.0026],
        "refrigerador": [10.2, 0.616, 0.0328],
        "ventana": [11.1, 2.96, 0.00149],
        "cuadro mujer": [10.0, 4.12, -0.00103],
        "cuadro hombre": [8.05, 4.18, 0.202]
    }
}

VALID_ACTIONS = ["ve", "camina", "dirigete", "desplazate", "ir", "navega"]