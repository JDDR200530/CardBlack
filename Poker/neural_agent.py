import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
import numpy as np
import random
from collections import deque
import pickle
import os

class PokerDQN(nn.Module):
    """
    Red Neuronal Profunda para Poker usando Deep Q-Network (DQN)
    
    Arquitectura:
    - Input: Vector de estado del juego (cartas, pot, apuestas, etc.)
    - Hidden layers: Capas densas con dropout y normalización
    - Output: Q-values para cada acción (fold, call, bet)
    """
    
    def __init__(self, input_size=20, hidden_sizes=[512, 256, 128], output_size=3, dropout_rate=0.2):
        super(PokerDQN, self).__init__()
        
        # Arquitectura de la red
        self.layers = nn.ModuleList()
        
        # Capa de entrada
        prev_size = input_size
        
        # Capas ocultas
        for hidden_size in hidden_sizes:
            self.layers.append(nn.Linear(prev_size, hidden_size))
            self.layers.append(nn.BatchNorm1d(hidden_size))
            self.layers.append(nn.Dropout(dropout_rate))
            prev_size = hidden_size
        
        # Capa de salida
        self.output_layer = nn.Linear(prev_size, output_size)
        
        # Inicialización de pesos
        self._init_weights()
    
    def _init_weights(self):
        """Inicialización Xavier/Glorot para mejor convergencia"""
        for layer in self.layers:
            if isinstance(layer, nn.Linear):
                nn.init.xavier_uniform_(layer.weight)
                nn.init.constant_(layer.bias, 0.01)
        
        nn.init.xavier_uniform_(self.output_layer.weight)
        nn.init.constant_(self.output_layer.bias, 0.01)
    
    def forward(self, x):
        """Forward pass de la red"""
        # Asegurar que x sea un tensor 2D
        if len(x.shape) == 1:
            x = x.unsqueeze(0)
        
        # Pasar por capas ocultas
        for i in range(0, len(self.layers), 3):  # Cada 3 elementos: Linear, BatchNorm, Dropout
            x = self.layers[i](x)  # Linear
            if x.shape[0] > 1:  # BatchNorm solo funciona con batch_size > 1
                x = self.layers[i+1](x)  # BatchNorm
            x = F.relu(x)
            x = self.layers[i+2](x)  # Dropout
        
        # Capa de salida
        x = self.output_layer(x)
        return x


class ExperienceReplay:
    """Buffer de experiencia para DQN"""
    
    def __init__(self, capacity=10000):
        self.buffer = deque(maxlen=capacity)
    
    def push(self, state, action, reward, next_state, done):
        """Agregar experiencia al buffer"""
        self.buffer.append((state, action, reward, next_state, done))
    
    def sample(self, batch_size):
        """Muestrear batch aleatorio de experiencias"""
        batch = random.sample(self.buffer, min(batch_size, len(self.buffer)))
        
        states = torch.FloatTensor([e[0] for e in batch])
        actions = torch.LongTensor([e[1] for e in batch])
        rewards = torch.FloatTensor([e[2] for e in batch])
        next_states = torch.FloatTensor([e[3] for e in batch])
        dones = torch.BoolTensor([e[4] for e in batch])
        
        return states, actions, rewards, next_states, dones
    
    def __len__(self):
        return len(self.buffer)


class NeuralPokerAgent:
    """
    Agente de Poker con Red Neuronal Profunda usando DQN
    
    Características:
    - Deep Q-Network con experience replay
    - Epsilon-greedy exploration
    - Target network para estabilidad
    - Guardado/carga de modelos
    """
    
    def __init__(self, 
                 input_size=20, 
                 hidden_sizes=[512, 256, 128],
                 learning_rate=0.001,
                 epsilon=1.0,
                 epsilon_decay=0.995,
                 epsilon_min=0.05,
                 gamma=0.95,
                 batch_size=32,
                 target_update_freq=100,
                 memory_size=10000):
        
        # Configuración del dispositivo (GPU si está disponible)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"🧠 NeuralPokerAgent usando: {self.device}")
        
        # Redes neuronales
        self.q_network = PokerDQN(input_size, hidden_sizes, 3).to(self.device)
        self.target_network = PokerDQN(input_size, hidden_sizes, 3).to(self.device)
        
        # Copiar pesos iniciales a target network
        self.target_network.load_state_dict(self.q_network.state_dict())
        
        # Optimizador
        self.optimizer = optim.Adam(self.q_network.parameters(), lr=learning_rate)
        
        # Hiperparámetros
        self.epsilon = epsilon
        self.epsilon_decay = epsilon_decay
        self.epsilon_min = epsilon_min
        self.gamma = gamma
        self.batch_size = batch_size
        self.target_update_freq = target_update_freq
        
        # Experience replay
        self.memory = ExperienceReplay(memory_size)
        
        # Contadores
        self.steps = 0
        self.episodes = 0
        self.losses = []
        self.rewards_history = []
        
        # Estadísticas
        self.total_hands = 0
        self.wins = 0
        self.total_reward = 0
    
    def obs_to_vector_enhanced(self, obs):
        """
        Versión mejorada de obs_to_vector con más características y mejor normalización
        """
        try:
            if obs is None:
                return np.zeros(20, dtype=np.float32)
            
            vector = []
            
            # Si obs es un diccionario (HoldemEnv)
            if isinstance(obs, dict):
                # Cartas en mano (hole cards) - 4 elementos
                if 'hole' in obs and obs['hole']:
                    for card in obs['hole'][:2]:
                        if isinstance(card, tuple) and len(card) == 2:
                            rank, suit = card
                            # Normalizar rank de manera más efectiva
                            vector.append((rank - 2) / 12.0)  # 0-1 para ranks 2-14
                            # Suit como valor normalizado
                            suit_val = ['Corazones', 'Diamantes', 'Trebol', 'Copas'].index(suit) if suit in ['Corazones', 'Diamantes', 'Trebol', 'Copas'] else 0
                            vector.append(suit_val / 3.0)
                        else:
                            vector.extend([0, 0])
                else:
                    vector.extend([0, 0, 0, 0])  # 2 cartas x 2 elementos
                
                # Cartas comunitarias (board) - 10 elementos máximo
                if 'board' in obs and obs['board']:
                    board_cards = list(obs['board'])[:5]  # Máximo 5 cartas
                    for card in board_cards:
                        if isinstance(card, tuple) and len(card) == 2:
                            rank, suit = card
                            vector.append((rank - 2) / 12.0)
                            suit_val = ['Corazones', 'Diamantes', 'Trebol', 'Copas'].index(suit) if suit in ['Corazones', 'Diamantes', 'Trebol', 'Copas'] else 0
                            vector.append(suit_val / 3.0)
                        else:
                            vector.extend([0, 0])
                    
                    # Completar hasta 5 cartas
                    cards_to_add = 5 - len(board_cards)
                    vector.extend([0, 0] * cards_to_add)
                else:
                    vector.extend([0] * 10)  # 5 cartas x 2 elementos
                
                # Información del pot - 1 elemento (mejor normalización)
                pot = obs.get('pot', 0)
                vector.append(min(pot / 500.0, 2.0))  # Permitir valores hasta 2x
                
                # Apuesta propia - 1 elemento
                own_bet = obs.get('own_bet', 0)
                vector.append(min(own_bet / 50.0, 2.0))
                
                # Apuestas de oponentes - 3 elementos
                opp_bets = obs.get('opp_bets', [])
                for i in range(3):
                    if i < len(opp_bets):
                        vector.append(min(opp_bets[i] / 50.0, 2.0))
                    else:
                        vector.append(0)
                
                # Stage del juego - 1 elemento
                stage = obs.get('stage', 'preflop')
                stage_map = {'preflop': 0.0, 'flop': 0.33, 'turn': 0.66, 'river': 1.0}
                vector.append(stage_map.get(stage, 0.0))
            
            # Si obs es una tupla (KuhnEnv)
            elif isinstance(obs, tuple) and len(obs) == 2:
                card, history = obs
                # Carta normalizada
                vector.append((card - 1) / 2.0)  # Kuhn: 1-3 -> 0-1
                
                # Historia de acciones (últimas 10)
                for i in range(10):
                    if i < len(history):
                        vector.append(float(history[i]))
                    else:
                        vector.append(0.0)
                
                # Completar hasta 20
                while len(vector) < 20:
                    vector.append(0.0)
            
            else:
                # Fallback: usar obs_to_vector original
                try:
                    from poker_agent import obs_to_vector
                    original_vector = obs_to_vector(obs)
                    # Asegurar que sea del tamaño correcto
                    if len(original_vector) >= 20:
                        return original_vector[:20].astype(np.float32)
                    else:
                        padded = np.zeros(20, dtype=np.float32)
                        padded[:len(original_vector)] = original_vector
                        return padded
                except:
                    return np.zeros(20, dtype=np.float32)
            
            # Asegurar tamaño fijo de exactamente 20
            if len(vector) > 20:
                vector = vector[:20]
            elif len(vector) < 20:
                vector.extend([0.0] * (20 - len(vector)))
            
            # Convertir a numpy array con tipo correcto
            result = np.array(vector, dtype=np.float32)
            
            # Verificar que no hay NaN o infinitos
            if np.any(np.isnan(result)) or np.any(np.isinf(result)):
                print(f"⚠️ Vector contiene NaN o infinitos, usando vector cero")
                return np.zeros(20, dtype=np.float32)
            
            return result
        
        except Exception as e:
            print(f"⚠️ Error en obs_to_vector_enhanced: {e}")
            return np.zeros(20, dtype=np.float32)
    
    def action(self, state):
        """
        Seleccionar acción usando epsilon-greedy con red neuronal
        """
        try:
            # Convertir estado a vector
            state_vector = self.obs_to_vector_enhanced(state)
            
            # Epsilon-greedy exploration
            if random.random() < self.epsilon:
                return random.choice([0, 1, 2])  # Exploración aleatoria
            
            # Usar red neuronal para seleccionar acción
            with torch.no_grad():
                state_tensor = torch.FloatTensor(state_vector).to(self.device)
                q_values = self.q_network(state_tensor)
                action = q_values.argmax().item()
            
            return action
        
        except Exception as e:
            print(f"⚠️ Error en NeuralPokerAgent.action: {e}")
            return random.choice([0, 1, 2])
    
    def update(self, state, action, reward, next_state=None, done=False):
        """
        Actualizar el agente con nueva experiencia
        """
        try:
            # Convertir estados a vectores
            state_vector = self.obs_to_vector_enhanced(state)
            next_state_vector = self.obs_to_vector_enhanced(next_state) if next_state else np.zeros(20)
            
            # Agregar experiencia al buffer
            self.memory.push(state_vector, action, reward, next_state_vector, done)
            
            # Actualizar estadísticas
            self.total_reward += reward
            if done:
                self.episodes += 1
                self.rewards_history.append(self.total_reward)
                if reward > 0:
                    self.wins += 1
                self.total_reward = 0
            
            # Entrenar si hay suficientes experiencias
            if len(self.memory) >= self.batch_size:
                self._train_step()
            
            # Actualizar target network periódicamente
            self.steps += 1
            if self.steps % self.target_update_freq == 0:
                self.target_network.load_state_dict(self.q_network.state_dict())
            
            # Decay epsilon
            if self.epsilon > self.epsilon_min:
                self.epsilon *= self.epsilon_decay
        
        except Exception as e:
            print(f"⚠️ Error en NeuralPokerAgent.update: {e}")
    
    def _train_step(self):
        """
        Paso de entrenamiento usando experience replay
        """
        try:
            # Muestrear batch de experiencias
            states, actions, rewards, next_states, dones = self.memory.sample(self.batch_size)
            
            # Mover a dispositivo
            states = states.to(self.device)
            actions = actions.to(self.device)
            rewards = rewards.to(self.device)
            next_states = next_states.to(self.device)
            dones = dones.to(self.device)
            
            # Q-values actuales
            current_q_values = self.q_network(states).gather(1, actions.unsqueeze(1))
            
            # Q-values del siguiente estado usando target network
            with torch.no_grad():
                next_q_values = self.target_network(next_states).max(1)[0]
                target_q_values = rewards + (self.gamma * next_q_values * ~dones)
            
            # Calcular pérdida
            loss = F.mse_loss(current_q_values.squeeze(), target_q_values)
            
            # Backpropagation
            self.optimizer.zero_grad()
            loss.backward()
            
            # Gradient clipping para estabilidad
            torch.nn.utils.clip_grad_norm_(self.q_network.parameters(), max_norm=1.0)
            
            self.optimizer.step()
            
            # Guardar pérdida para monitoreo
            self.losses.append(loss.item())
        
        except Exception as e:
            print(f"⚠️ Error en _train_step: {e}")
    
    def save_model(self, filepath="poker_dqn_model.pth"):
        """
        Guardar modelo entrenado
        """
        try:
            checkpoint = {
                'q_network_state_dict': self.q_network.state_dict(),
                'target_network_state_dict': self.target_network.state_dict(),
                'optimizer_state_dict': self.optimizer.state_dict(),
                'epsilon': self.epsilon,
                'steps': self.steps,
                'episodes': self.episodes,
                'losses': self.losses,
                'rewards_history': self.rewards_history,
                'wins': self.wins,
                'total_hands': self.total_hands
            }
            torch.save(checkpoint, filepath)
            print(f"✅ Modelo guardado en: {filepath}")
        
        except Exception as e:
            print(f"⚠️ Error guardando modelo: {e}")
    
    def load_model(self, filepath="poker_dqn_model.pth"):
        """
        Cargar modelo previamente entrenado
        """
        try:
            if os.path.exists(filepath):
                checkpoint = torch.load(filepath, map_location=self.device)
                
                self.q_network.load_state_dict(checkpoint['q_network_state_dict'])
                self.target_network.load_state_dict(checkpoint['target_network_state_dict'])
                self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
                
                self.epsilon = checkpoint.get('epsilon', self.epsilon)
                self.steps = checkpoint.get('steps', 0)
                self.episodes = checkpoint.get('episodes', 0)
                self.losses = checkpoint.get('losses', [])
                self.rewards_history = checkpoint.get('rewards_history', [])
                self.wins = checkpoint.get('wins', 0)
                self.total_hands = checkpoint.get('total_hands', 0)
                
                print(f"✅ Modelo cargado desde: {filepath}")
                print(f"📊 Episodios: {self.episodes}, Epsilon: {self.epsilon:.3f}")
                return True
            else:
                print(f"⚠️ Archivo no encontrado: {filepath}")
                return False
        
        except Exception as e:
            print(f"⚠️ Error cargando modelo: {e}")
            return False
    
    def get_stats(self):
        """
        Obtener estadísticas del agente
        """
        win_rate = (self.wins / max(self.episodes, 1)) * 100
        avg_loss = np.mean(self.losses[-100:]) if self.losses else 0
        avg_reward = np.mean(self.rewards_history[-100:]) if self.rewards_history else 0
        
        return {
            'episodes': self.episodes,
            'win_rate': win_rate,
            'epsilon': self.epsilon,
            'avg_loss': avg_loss,
            'avg_reward': avg_reward,
            'total_steps': self.steps,
            'memory_size': len(self.memory)
        }
    
    def print_stats(self):
        """
        Imprimir estadísticas del entrenamiento
        """
        stats = self.get_stats()
        print(f"\n📊 Estadísticas del Agente Neural:")
        print(f"   🎮 Episodios: {stats['episodes']}")
        print(f"   🏆 Tasa de victoria: {stats['win_rate']:.1f}%")
        print(f"   🎯 Epsilon: {stats['epsilon']:.3f}")
        print(f"   📉 Pérdida promedio: {stats['avg_loss']:.4f}")
        print(f"   💰 Recompensa promedio: {stats['avg_reward']:.2f}")
        print(f"   👣 Pasos totales: {stats['total_steps']}")
        print(f"   🧠 Experiencias en memoria: {stats['memory_size']}")


class PokerNeuralTrainer:
    """
    Entrenador especializado para el agente neural de poker
    """
    
    def __init__(self, env, agent, opponents=None):
        self.env = env
        self.agent = agent
        self.opponents = opponents or []
        self.training_history = []
    
    def train_episode(self):
        """
        Entrenar un episodio completo
        """
        try:
            obs, _ = self.env.reset()
            total_reward = 0
            done = False
            step_count = 0
            
            while not done and step_count < 100:  # Límite de seguridad
                current_player = self.env.current_player
                
                # Obtener acción
                if current_player == 0:  # Nuestro agente neural
                    action = self.agent.action(obs)
                    prev_obs = obs
                else:  # Oponentes
                    if current_player - 1 < len(self.opponents):
                        action = self.opponents[current_player - 1].action(obs)
                    else:
                        action = random.choice([0, 1, 2])  # Fallback aleatorio
                
                # Ejecutar acción
                next_obs, rewards, done, info = self.env.step(current_player, action)
                
                # Actualizar agente si es su turno
                if current_player == 0:
                    reward = rewards[0] if isinstance(rewards, (list, tuple)) else 0
                    self.agent.update(prev_obs, action, reward, next_obs, done)
                    total_reward += reward
                
                obs = next_obs
                step_count += 1
            
            return total_reward
        
        except Exception as e:
            print(f"⚠️ Error en train_episode: {e}")
            return 0
    
    def train(self, n_episodes=1000, save_freq=100, print_freq=50):
        """
        Entrenar el agente por múltiples episodios
        """
        print(f"🚀 Iniciando entrenamiento neural por {n_episodes} episodios...")
        
        for episode in range(n_episodes):
            reward = self.train_episode()
            self.training_history.append(reward)
            
            # Imprimir progreso
            if episode % print_freq == 0:
                self.agent.print_stats()
                avg_reward = np.mean(self.training_history[-print_freq:])
                print(f"📈 Episodio {episode}: Recompensa promedio últimos {print_freq}: {avg_reward:.2f}")
            
            # Guardar modelo periódicamente
            if episode % save_freq == 0 and episode > 0:
                self.agent.save_model(f"poker_dqn_episode_{episode}.pth")
        
        print("✅ Entrenamiento completado!")
        self.agent.save_model("poker_dqn_final.pth")
        return self.training_history


def test_neural_agent():
    """
    Función de prueba para el agente neural
    """
    print("🧪 Probando NeuralPokerAgent...")
    
    try:
        # Crear agente con configuración más pequeña
        print("🔧 Creando agente neural...")
        agent = NeuralPokerAgent(input_size=20, hidden_sizes=[64, 32])
        
        # Test con estado dummy simple
        dummy_state = {
            "hole": [(14, "Corazones"), (13, "Copas")],
            "board": [],
            "pot": 150,
            "own_bet": 25,
            "opp_bets": [25, 0],
            "stage": "preflop"
        }
        
        print("🔧 Test obs_to_vector_enhanced:")
        vector = agent.obs_to_vector_enhanced(dummy_state)
        print(f"✅ Vector creado exitosamente - Tamaño: {len(vector)}")
        print(f"   Primeros 5 elementos: {vector[:5]}")
        
        print("🎯 Test action selection:")
        action_names = ["Fold", "Call", "Bet"]
        for i in range(3):
            action = agent.action(dummy_state)
            print(f"   Acción {i+1}: {action} ({action_names[action]})")
        
        print("✅ Tests completados exitosamente!")
        
    except Exception as e:
        print(f"❌ Error en test: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_neural_agent()