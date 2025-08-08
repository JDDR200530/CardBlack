# train_policy.py
import gymnasium as gym
import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, Model
import os

# --- Hiperparámetros ---
EPISODES = 80000       # Reduce si tu PC es lento (ej: 30000)
BATCH_SIZE = 1024      # pasos acumulados antes de aplicar gradiente
GAMMA = 0.99
LR = 0.001
MODEL_PATH = "policy_blackjack.h5"
SEED = 42

np.random.seed(SEED)
tf.random.set_seed(SEED)

# --- Entorno ---
env = gym.make("Blackjack-v1", sab=True)  # sab=True: acciones estándar (stick/hit)
obs_space = 3   # (player_sum, dealer_card, usable_ace)
n_actions = env.action_space.n  # 2 (stick=0, hit=1)

# --- Preprocesado del estado ---
def procesar_estado(state):
    # Normalizamos a rangos aproximados para ayudar al entrenamiento
    player_sum = (state[0] - 4.0) / (21.0 - 4.0)     # player sum 4..21
    dealer_card = (state[1] - 1.0) / (10.0 - 1.0)    # dealer card 1..10
    usable = 1.0 if state[2] else 0.0
    return np.array([player_sum, dealer_card, usable], dtype=np.float32)

# --- Modelo (policy network) ---
inputs = layers.Input(shape=(obs_space,))
x = layers.Dense(64, activation="relu")(inputs)
x = layers.Dense(64, activation="relu")(x)
logits = layers.Dense(n_actions, activation=None)(x)
model = Model(inputs=inputs, outputs=logits)
optimizer = tf.keras.optimizers.Adam(learning_rate=LR)

# --- Utilidades ---
def sample_action(logits):
    probs = tf.nn.softmax(logits).numpy()
    return np.random.choice(len(probs), p=probs)

def discount_rewards(rewards, gamma):
    discounted = np.zeros_like(rewards, dtype=np.float32)
    running = 0.0
    for t in reversed(range(len(rewards))):
        running = rewards[t] + gamma * running
        discounted[t] = running
    # normalizar para estabilidad
    mean = discounted.mean()
    std = discounted.std() + 1e-8
    return (discounted - mean) / std

# --- Entrenamiento (REINFORCE, actualizaciones por lotes) ---
states_batch = []
actions_batch = []
rewards_batch = []
episode = 0
steps = 0

print("Iniciando entrenamiento REINFORCE...")

while episode < EPISODES:
    state, _ = env.reset()
    done = False
    ep_states = []
    ep_actions = []
    ep_rewards = []

    while not done:
        s = procesar_estado(state)
        logits = model(np.array([s]))[0]
        action = sample_action(logits)

        next_state, reward, terminated, truncated, _ = env.step(int(action))
        done = terminated or truncated

        ep_states.append(s)
        ep_actions.append(action)
        ep_rewards.append(reward)

        state = next_state
        steps += 1

    # episodio terminado -> calcular retornos descontados normalizados
    discounted = discount_rewards(ep_rewards, GAMMA)

    states_batch.extend(ep_states)
    actions_batch.extend(ep_actions)
    rewards_batch.extend(discounted)

    episode += 1

    # actualizar por lotes
    if len(states_batch) >= BATCH_SIZE:
        states_arr = np.vstack(states_batch)
        actions_arr = np.array(actions_batch, dtype=np.int32)
        returns_arr = np.array(rewards_batch, dtype=np.float32)

        with tf.GradientTape() as tape:
            logits = model(states_arr)                    # (N, n_actions)
            logp = tf.nn.log_softmax(logits)
            indices = tf.range(len(actions_arr))
            chosen_logp = tf.gather_nd(logp, tf.stack([indices, actions_arr], axis=1))
            loss = -tf.reduce_mean(chosen_logp * returns_arr)

        grads = tape.gradient(loss, model.trainable_variables)
        optimizer.apply_gradients(zip(grads, model.trainable_variables))

        # limpiar batch
        states_batch = []
        actions_batch = []
        rewards_batch = []

    if episode % 5000 == 0:
        print(f"Episodio {episode}/{EPISODES} - pasos totales {steps}")

# Guardar modelo final
model.save(MODEL_PATH)
print("Entrenamiento completado. Modelo guardado en", MODEL_PATH)
