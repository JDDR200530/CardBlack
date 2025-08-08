# ai_agent.py
import numpy as np
from tensorflow.keras.models import load_model
import os

MODEL_PATH = "policy_blackjack.h5"

def procesar_estado_para_red(state):
    # state: (player_sum, dealer_card, usable_ace)
    # Normalizamos al mismo esquema usado en entrenamiento
    player_sum = (state[0] - 4.0) / (21.0 - 4.0)
    dealer_card = (state[1] - 1.0) / (10.0 - 1.0)
    usable = 1.0 if state[2] else 0.0
    return np.array([player_sum, dealer_card, usable], dtype=np.float32)

class AIAgent:
    def __init__(self, model_path=MODEL_PATH):
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Modelo no encontrado en {model_path}. Entrena y guarda el modelo primero.")
        self.model = load_model(model_path)

    def action(self, state, greedy=True):
        """
        state: (player_sum, dealer_card, usable_ace)
        greedy True -> toma la acción con mayor probabilidad.
        greedy False -> samplea según las probabilidades.
        Retorna: 0 = stick (plantarse), 1 = hit (pedir carta)
        """
        s = procesar_estado_para_red(state).reshape(1, -1)
        logits = self.model.predict(s, verbose=0)[0]
        exps = np.exp(logits - np.max(logits))
        probs = exps / np.sum(exps)
        if greedy:
            return int(np.argmax(probs))
        else:
            return int(np.random.choice(len(probs), p=probs))
