import random

class PolicyAgent:
    def __init__(self):
        # Política simple como diccionario de estados a acciones
        self.policy = {}

    def action(self, state):
        # Usamos str(state) para clave simple (mejorar según tu estructura)
        key = str(state)
        if key not in self.policy:
            # Acción aleatoria inicial (fold=0, call=1, bet=2)
            self.policy[key] = random.choice([0,1,2])
        return self.policy[key]

    def update(self, state, action):
        # Aquí iría lógica para mejorar la política, por ejemplo RL (simplificado)
        key = str(state)
        self.policy[key] = action


class HeuristicAgent:
    def action(self, state):
        # Lógica heurística simple: si puede, hace call, sino fold
        # Aquí solo un ejemplo: devuelve call (1)
        return 1

class RandomAgent:
    def action(self, state):
        return random.choice([0,1,2])
