import gymnasium as gym
import numpy as np
import random
import pickle
from collections import defaultdict

# --- Esta función reemplaza el lambda ---
def default_action_value():
    return np.zeros(2)  # 0: stick, 1: hit

class BlackjackAI:
    def __init__(self, learning_rate=0.1, discount_factor=0.9, exploration_rate=1.0):
        self.Q = defaultdict(default_action_value)
        self.alpha = learning_rate
        self.gamma = discount_factor
        self.epsilon = exploration_rate
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.999995

    def choose_action(self, state):
        if random.uniform(0, 1) < self.epsilon:
            return random.choice([0, 1])  # Explora
        return np.argmax(self.Q[state])  # Explota

    def learn(self, state, action, reward, next_state, done):
        old_value = self.Q[state][action]
        future_max = np.max(self.Q[next_state]) if not done else 0
        self.Q[state][action] = old_value + self.alpha * (reward + self.gamma * future_max - old_value)
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

def train(agent, env, episodes=100000):
    for episode in range(episodes):
        state, _ = env.reset()
        state = tuple(state)
        done = False

        while not done:
            action = agent.choose_action(state)
            next_state, reward, terminated, truncated, _ = env.step(action)
            done = terminated or truncated
            next_state = tuple(next_state)

            agent.learn(state, action, reward, next_state, done)
            state = next_state

        if episode % 10000 == 0:
            print(f"Episode {episode}, epsilon={agent.epsilon:.4f}")

    # Guarda el modelo
    with open("modelo_blackjack.pkl", "wb") as f:
        pickle.dump(dict(agent.Q), f)

# --- Entrenamiento ---
if __name__ == "__main__":
    env = gym.make("Blackjack-v1", sab=True)  # sab=True para acciones estándar
    ai = BlackjackAI()
    train(ai, env, episodes=100000)
