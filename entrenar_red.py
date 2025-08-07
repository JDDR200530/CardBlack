import gymnasium as gym
import numpy as np
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
from tensorflow.keras.optimizers import Adam
import random

env = gym.make("Blackjack-v1", sab=True)

# Modelo de red neuronal simple
model = Sequential([
    Dense(32, input_shape=(3,), activation='relu'),
    Dense(32, activation='relu'),
    Dense(2, activation='softmax')  # 2 acciones: hit o stick
])
model.compile(optimizer=Adam(learning_rate=0.001), loss='categorical_crossentropy')

# Convertimos un estado a un vector
def procesar_estado(state):
    # (player sum, dealer card, usable ace)
    return np.array([state[0], state[1], int(state[2])])

# Entrenamiento básico con política epsilon-greedy
episodes = 10000
datos = []

for episode in range(episodes):
    state, _ = env.reset()
    done = False
    while not done:
        s = procesar_estado(state)
        if random.random() < 0.1:
            action = env.action_space.sample()
        else:
            probs = model.predict(np.array([s]), verbose=0)[0]
            action = np.argmax(probs)

        next_state, reward, terminated, truncated, _ = env.step(action)
        done = terminated or truncated

        datos.append((s, action, reward))
        state = next_state

# Entrenamiento supervisado basado en recompensas
X = []
y = []

for estado, accion, recompensa in datos:
    X.append(estado)
    y.append([1, 0] if accion == 0 else [0, 1])  # hit = [1, 0], stick = [0, 1]

X = np.array(X)
y = np.array(y)

model.fit(X, y, epochs=10, verbose=1)

# Guardar el modelo
model.save("modelo_blackjack.h5")
print("Modelo guardado como modelo_blackjack.h5")
