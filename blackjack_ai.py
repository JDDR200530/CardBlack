# blackjack_ai.py

import random
import pickle

class BlackjackAI:
    def __init__(self, epsilon=0.1, alpha=0.1, gamma=0.9):
        self.q_table = {}
        self.epsilon = epsilon
        self.alpha = alpha
        self.gamma = gamma

    def choose_action(self, state):
        # Conversión completa a tupla incluyendo elementos anidados
        state = tuple(tuple(s) if isinstance(s, list) else s for s in state)
        
        if random.random() < self.epsilon or ((state, 1) not in self.q_table and (state, 0) not in self.q_table):
            return random.choice([0,1])
        return max([0,1], key=lambda a: self.q_table.get((state, a), 0))

    def learn(self, state, action, reward, next_state, done):
        # Conversión recursiva a tuplas
        state = tuple(tuple(s) if isinstance(s, list) else s for s in state)
        next_state = tuple(tuple(s) if isinstance(s, list) else s for s in next_state)
        
        # Resto del método igual
        current_q = self.q_table.get((state, action), 0.0)
        future_q = 0 if done else max(self.q_table.get((next_state, a), 0.0) for a in [0, 1])
        target = reward + self.gamma * future_q
        self.q_table[(state, action)] = current_q + self.alpha * (target - current_q)

    def save(self, filename='modelo_blackjack.pkl'):
        with open(filename, 'wb') as f:
            pickle.dump(self.q_table, f)

    def load(self, filename='modelo_blackjack.pkl'):
        try:
            with open(filename, 'rb') as f:
                self.q_table = pickle.load(f)
        except FileNotFoundError:
            self.q_table = {}