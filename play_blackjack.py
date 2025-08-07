import gymnasium as gym
import numpy as np
import pickle
import random
from collections import defaultdict

class BlackjackAI:
    def __init__(self, learning_rate=0.1, discount_factor=0.9, exploration_rate=0.0):
        # exploration_rate=0 para jugar sin exploración (usar Q aprendida)
        self.Q = defaultdict(lambda: np.zeros(2))  # dos acciones: 0=stand, 1=hit
        self.alpha = learning_rate
        self.gamma = discount_factor
        self.epsilon = exploration_rate

    def choose_action(self, state):
        if random.uniform(0, 1) < self.epsilon:
            return random.choice([0, 1])
        return int(np.argmax(self.Q[state]))

    def load(self, filename='modelo_blackjack.pkl'):
        with open(filename, 'rb') as f:
            q_dict = pickle.load(f)
            self.Q.update(q_dict)

def main():
    env = gym.make('Blackjack-v1', sab=True, render_mode='human')

    ai = BlackjackAI(exploration_rate=0.0)  # sin exploración para jugar
    ai.load('modelo_blackjack.pkl')

    episodes = 10

    for e in range(episodes):
        state, _ = env.reset()
        done = False
        print(f"\n=== Juego {e + 1} ===")

        while not done:
            action = ai.choose_action(state)
            print(f"Estado: {state} | Acción: {'Pedir carta' if action == 1 else 'Quedarse'}")
            state, reward, terminated, truncated, _ = env.step(action)
            done = terminated or truncated

        resultado = "Victoria" if reward > 0 else "Derrota" if reward < 0 else "Empate"
        print(f"Resultado: {resultado}")

    env.close()

if __name__ == "__main__":
    main()
