#!/usr/bin/env python3

import os
import json
import pickle
import random
import datetime
from collections import deque

import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, models

# ---------------- RUTAS Y ARCHIVOS ----------------
BASE_PATH = "Blackjack"
os.makedirs(BASE_PATH, exist_ok=True)

MODEL_KERAS = os.path.join(BASE_PATH, "blackjack_dqn_model.keras")
MODEL_H5 = os.path.join(BASE_PATH, "blackjack_dqn_model.h5")
EPSILON_FILE = os.path.join(BASE_PATH, "blackjack_epsilon.json")
MEMORY_FILE = os.path.join(BASE_PATH, "blackjack_memory.pkl")
META_FILE = os.path.join(BASE_PATH, "blackjack_meta.json")

print("Fecha:", datetime.datetime.now().isoformat())
print("GPU disponible:", tf.config.list_physical_devices('GPU'))
print("Rutas de guardado:")
print(" - model (.keras):", MODEL_KERAS)
print(" - model (.h5):", MODEL_H5)
print(" - epsilon:", EPSILON_FILE)
print(" - memory:", MEMORY_FILE)
print(" - meta:", META_FILE)
print("--------------------------------------------------")

# ---------------- ENTORNO (simple) ----------------
class BlackjackEnv:
    def __init__(self):
        self.deck = [1,2,3,4,5,6,7,8,9,10,10,10,10] * 4
        self.reset()

    def draw_card(self):
        return random.choice(self.deck)

    def reset(self):
        self.player_hand = [self.draw_card(), self.draw_card()]
        self.dealer_hand = [self.draw_card(), self.draw_card()]
        return self.get_state()

    def get_state(self):
        player_sum = sum(self.player_hand)
        usable_ace = 1 if (1 in self.player_hand and player_sum + 10 <= 21) else 0
        if usable_ace:
            player_sum += 10
        dealer_card = self.dealer_hand[0]
        return np.array([player_sum, dealer_card, usable_ace], dtype=np.float32)

    def step(self, action):
        # action: 0 = stick, 1 = hit
        if action == 1:
            self.player_hand.append(self.draw_card())
            player_sum = sum(self.player_hand)
            usable_ace = 1 if (1 in self.player_hand and player_sum + 10 <= 21) else 0
            if usable_ace:
                player_sum += 10
            if player_sum > 21:
                return self.get_state(), -1.0, True
            return self.get_state(), 0.0, False
        else:
            player_sum = sum(self.player_hand)
            if 1 in self.player_hand and player_sum + 10 <= 21:
                player_sum += 10
            dealer_sum = sum(self.dealer_hand)
            while dealer_sum < 17:
                self.dealer_hand.append(self.draw_card())
                dealer_sum = sum(self.dealer_hand)
                if 1 in self.dealer_hand and dealer_sum + 10 <= 21:
                    dealer_sum += 10
            if dealer_sum > 21 or player_sum > dealer_sum:
                return self.get_state(), 1.0, True
            elif player_sum < dealer_sum:
                return self.get_state(), -1.0, True
            else:
                return self.get_state(), 0.0, True

# ---------------- AGENTE DQN ----------------
class DQNAgent:
    def __init__(self,
                 state_size=3,
                 action_size=2,
                 memory_size=50000,
                 min_replay_size=6000,
                 gamma=0.99,
                 learning_rate=5e-4,
                 epsilon=1.0,
                 epsilon_min=0.001,
                 epsilon_decay=0.995,
                 batch_size=64,
                 target_update_freq=1000):
        self.state_size = state_size
        self.action_size = action_size
        self.memory = deque(maxlen=memory_size)
        self.memory_maxlen = memory_size
        self.min_replay_size = min_replay_size

        self.gamma = gamma
        self.learning_rate = learning_rate

        self.epsilon = epsilon
        self.epsilon_min = epsilon_min
        self.epsilon_decay = epsilon_decay

        self.batch_size = batch_size
        self.target_update_freq = target_update_freq

        # modelos online / target
        self.model = self._build_model()
        self.target_model = self._build_model()
        self.update_target_model()

        self.step_count = 0

    def _build_model(self):
        model = models.Sequential([
            layers.Input(shape=(self.state_size,)),
            layers.Dense(128, activation='relu'),
            layers.Dense(128, activation='relu'),
            layers.Dense(self.action_size, activation='linear')
        ])
        model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=self.learning_rate),
                      loss='mse')
        return model

    def update_target_model(self):
        self.target_model.set_weights(self.model.get_weights())

    def remember(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, float(done)))

    def act(self, state):
        if np.random.rand() <= self.epsilon:
            return random.randrange(self.action_size)
        q = self.model.predict(np.array([state]), verbose=0)[0]
        return int(np.argmax(q))

    def replay_step(self):
        """Realiza UNA actualización de la red con un minibatch.
           Devuelve loss o None si no hay suficiente memoria."""
        if len(self.memory) < self.min_replay_size:
            return None

        minibatch = random.sample(self.memory, self.batch_size)
        states = np.array([m[0] for m in minibatch], dtype=np.float32)
        actions = np.array([m[1] for m in minibatch], dtype=np.int32)
        rewards = np.array([m[2] for m in minibatch], dtype=np.float32)
        next_states = np.array([m[3] for m in minibatch], dtype=np.float32)
        dones = np.array([m[4] for m in minibatch], dtype=np.float32)

        # Double DQN:
        next_q_online = self.model.predict(next_states, verbose=0)
        next_actions = np.argmax(next_q_online, axis=1)
        next_q_target = self.target_model.predict(next_states, verbose=0)
        max_next_q = next_q_target[np.arange(self.batch_size), next_actions]

        targets = rewards + (1.0 - dones) * self.gamma * max_next_q

        q_values = self.model.predict(states, verbose=0)
        q_values[np.arange(self.batch_size), actions] = targets

        loss = self.model.train_on_batch(states, q_values)

        # decaimiento epsilon (fuera de entrenamiento múltiple se podría hacer una vez por episodio)
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay
            if self.epsilon < self.epsilon_min:
                self.epsilon = self.epsilon_min

        # contadores y actualización target
        self.step_count += 1
        if self.step_count % self.target_update_freq == 0:
            self.update_target_model()

        return float(loss)

    # wrapper que permite repetir el replay varias veces
    def replay(self, train_repeats=1):
        last_loss = None
        for _ in range(train_repeats):
            loss = self.replay_step()
            if loss is not None:
                last_loss = loss
        return last_loss

    # Guardado / carga
    def save_all(self, model_keras_path, model_h5_path, epsilon_path, memory_path, meta_path):
        try:
            self.model.save(model_keras_path)
            self.model.save(model_h5_path)
        except Exception as e:
            print("Error guardando modelo:", e)

        try:
            with open(epsilon_path, 'w') as f:
                json.dump({"epsilon": float(self.epsilon)}, f)
        except Exception as e:
            print("Error guardando epsilon:", e)

        try:
            with open(memory_path, 'wb') as f:
                pickle.dump(list(self.memory), f)
        except Exception as e:
            print("Error guardando memory:", e)

        try:
            meta = {
                "step_count": int(self.step_count),
                "memory_len": len(self.memory),
                "gamma": float(self.gamma),
                "learning_rate": float(self.learning_rate),
                "batch_size": int(self.batch_size)
            }
            with open(meta_path, 'w') as f:
                json.dump(meta, f)
        except Exception as e:
            print("Error guardando meta:", e)

    def load_all(self, model_keras_path, epsilon_path, memory_path):
        loaded = {"model": False, "epsilon": False, "memory": False}
        # modelo
        if os.path.exists(model_keras_path):
            try:
                print("Cargando modelo desde:", model_keras_path)
                self.model = tf.keras.models.load_model(model_keras_path)
                self.target_model = self._build_model()
                self.target_model.set_weights(self.model.get_weights())
                loaded["model"] = True
            except Exception as e:
                print("Error al cargar modelo:", e)
        # epsilon
        if os.path.exists(epsilon_path):
            try:
                with open(epsilon_path, 'r') as f:
                    data = json.load(f)
                    self.epsilon = float(data.get("epsilon", self.epsilon))
                loaded["epsilon"] = True
            except Exception as e:
                print("Error al cargar epsilon:", e)
        # memoria
        if os.path.exists(memory_path):
            try:
                with open(memory_path, 'rb') as f:
                    mem_list = pickle.load(f)
                    self.memory = deque(mem_list, maxlen=self.memory_maxlen)
                loaded["memory"] = True
                print(f"✅ Memoria cargada: {len(self.memory)} experiencias")
            except Exception as e:
                print("Error al cargar memory:", e)
        return loaded

# ---------------- ENTRENAMIENTO ----------------
def train(episodes=30000,
          batch_size=64,
          min_replay_size=6000,
          train_repeats=1,
          save_every_episodes=500,
          initial_load=True,
          seed=42):

    random.seed(seed)
    np.random.seed(seed)
    tf.random.set_seed(seed)

    env = BlackjackEnv()
    agent = DQNAgent(batch_size=batch_size, min_replay_size=min_replay_size)

    if initial_load:
        loaded = agent.load_all(MODEL_KERAS, EPSILON_FILE, MEMORY_FILE)
        if any(loaded.values()):
            print("Se cargó parcial/totalmente el progreso previo:", loaded)
        else:
            print("No se cargó nada previo, empezando desde cero.")

    wins = losses = draws = 0
    last_print_time = datetime.datetime.now()

    for e in range(1, episodes + 1):
        state = env.reset()
        done = False
        total_reward = 0.0

        while not done:
            action = agent.act(state)
            next_state, reward, done = env.step(action)
            agent.remember(state, action, reward, next_state, done)
            state = next_state
            total_reward += reward

        # contar resultado
        if total_reward > 0:
            wins += 1
        elif total_reward < 0:
            losses += 1
        else:
            draws += 1

        # entrenar
        loss = agent.replay(train_repeats)

        # reporte
        if e % 50 == 0 or e == 1 or e == episodes:
            total_games = wins + losses + draws
            win_rate = (wins / total_games * 100) if total_games > 0 else 0.0
            print(f"Episodio {e}/{episodes} | WinRate: {win_rate:.2f}% | Wins: {wins} | Losses: {losses} | Draws: {draws} | Epsilon: {agent.epsilon:.4f} | Mem: {len(agent.memory)} | Loss: {loss}")

        # salvado periódico
        if e % save_every_episodes == 0 or e == episodes:
            print(f"[{datetime.datetime.now().isoformat()}] Guardando progreso en {BASE_PATH} ...")
            agent.save_all(MODEL_KERAS, MODEL_H5, EPSILON_FILE, MEMORY_FILE, META_FILE)
            print("Guardado completado.")

    # guardado final
    print("Entrenamiento finalizado. Guardando todo...")
    agent.save_all(MODEL_KERAS, MODEL_H5, EPSILON_FILE, MEMORY_FILE, META_FILE)
    print("¡Guardado completado!")

if __name__ == "__main__":
    # Parámetros que puedes ajustar
    EPISODES = 30000        
    BATCH_SIZE = 64
    MIN_REPLAY_SIZE = 6000
    TRAIN_REPEATS = 1       # 1 significa 1 actualización por episodio; subir a 4/8 para aprender más por episodio
    SAVE_EVERY = 500

    train(episodes=EPISODES,
          batch_size=BATCH_SIZE,
          min_replay_size=MIN_REPLAY_SIZE,
          train_repeats=TRAIN_REPEATS,
          save_every_episodes=SAVE_EVERY,
          initial_load=True,
          seed=42)
