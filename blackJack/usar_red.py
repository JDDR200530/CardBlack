#usar_red.py
import numpy as np
from tensorflow.keras.models import load_model

# Carga el modelo ya entrenado
model = load_model("modelo_blackjack.h5")

# Simula un estado de ejemplo
# Por ejemplo: [suma_mano_jugador, carta_visible_del_dealer, usable_ace]
estado = np.array([[18, 10, 1]])  # El jugador tiene 18, el dealer muestra 10, tiene un As usable

# Realiza una predicción
accion = model.predict(estado)

# Interpreta el resultado (suponiendo que salida es [hit_prob, stick_prob])
accion_elegida = np.argmax(accion)
print("Acción recomendada:", "Pedir carta (Hit)" if accion_elegida == 0 else "Plantarse (Stick)")
