import random
import numpy as np

def obs_to_vector(obs):
    """
    Convierte observación del entorno a vector numérico para procesamiento por IA
    
    Args:
        obs: Observación del entorno (puede ser dict, list, o estructura compleja)
    
    Returns:
        np.array: Vector numérico representando el estado
    """
    try:
        if obs is None:
            return np.zeros(10)  # Vector por defecto
        
        # Si obs es un diccionario
        if isinstance(obs, dict):
            vector = []
            
            # Procesar diferentes campos comunes
            if 'hand' in obs:
                hand = obs['hand']
                if hand and len(hand) >= 2:
                    # Convertir cartas a valores numéricos
                    for card in hand[:2]:  # Solo las primeras 2 cartas
                        if isinstance(card, tuple) and len(card) == 2:
                            rank, suit = card
                            vector.extend([rank, hash(suit) % 4])
                        else:
                            vector.extend([0, 0])
                else:
                    vector.extend([0, 0, 0, 0])  # Sin cartas
            
            # Procesar board/cartas comunitarias
            if 'board' in obs:
                board = obs['board'] or []
                board_vector = []
                for card in board[:5]:  # Máximo 5 cartas comunitarias
                    if isinstance(card, tuple) and len(card) == 2:
                        rank, suit = card
                        board_vector.extend([rank, hash(suit) % 4])
                    else:
                        board_vector.extend([0, 0])
                # Completar hasta 10 elementos (5 cartas x 2)
                while len(board_vector) < 10:
                    board_vector.extend([0, 0])
                vector.extend(board_vector[:10])
            
            # Información del pot
            if 'pot' in obs:
                vector.append(obs['pot'])
            else:
                vector.append(0)
            
            # Stack del jugador
            if 'stack' in obs:
                vector.append(obs['stack'])
            else:
                vector.append(1000)  # Stack por defecto
            
            # Apuesta actual
            if 'current_bet' in obs:
                vector.append(obs['current_bet'])
            else:
                vector.append(0)
            
            # Completar si el vector es muy corto
            while len(vector) < 10:
                vector.append(0)
            
            return np.array(vector[:20])  # Límite de 20 características
        
        # Si obs es una lista
        elif isinstance(obs, (list, tuple)):
            vector = []
            for item in obs:
                if isinstance(item, (int, float)):
                    vector.append(item)
                elif isinstance(item, tuple) and len(item) == 2:
                    # Asumir que es una carta (rank, suit)
                    rank, suit = item
                    vector.extend([rank, hash(suit) % 4])
                else:
                    vector.append(hash(str(item)) % 100)
            
            # Normalizar tamaño
            if len(vector) < 10:
                vector.extend([0] * (10 - len(vector)))
            
            return np.array(vector[:20])
        
        # Si obs es un número
        elif isinstance(obs, (int, float)):
            return np.array([obs] + [0] * 9)
        
        # Fallback: convertir a string y hacer hash
        else:
            hash_val = hash(str(obs)) % 1000000
            return np.array([hash_val] + [0] * 9)
    
    except Exception as e:
        print(f"⚠️ Error en obs_to_vector: {e}")
        return np.zeros(10)


class PolicyAgent:
    """Agente que aprende una política basada en experiencia"""
    
    def __init__(self):
        self.policy = {}
        self.learning_rate = 0.1
        self.exploration_rate = 0.15
        self.experience = []
        
    def action(self, state):
        """Selecciona acción basada en política aprendida"""
        try:
            # Convertir estado a clave
            if hasattr(state, '__dict__'):
                key = str(sorted(state.__dict__.items()))
            else:
                key = str(state)
            
            # Exploración vs explotación
            if random.random() < self.exploration_rate:
                return random.choice([0, 1, 2])
            
            # Usar política aprendida
            if key not in self.policy:
                # Política inicial inteligente
                # 0=fold, 1=call, 2=bet
                # Favorece call sobre bet, bet sobre fold
                self.policy[key] = random.choices([0, 1, 2], weights=[0.2, 0.5, 0.3])[0]
            
            return self.policy[key]
            
        except Exception as e:
            print(f"⚠️ Error en PolicyAgent.action: {e}")
            return random.choice([0, 1, 2])

    def update(self, state, action, reward=0, next_state=None):
        """Actualiza política basada en experiencia"""
        try:
            if hasattr(state, '__dict__'):
                key = str(sorted(state.__dict__.items()))
            else:
                key = str(state)
            
            # Almacenar experiencia
            self.experience.append((key, action, reward))
            
            # Actualización simple basada en recompensa
            if reward > 0:
                # Reforzar acción exitosa
                self.policy[key] = action
            elif reward < 0:
                # Penalizar acción fallida
                if random.random() < 0.3:
                    # Explorar acción diferente
                    actions = [0, 1, 2]
                    actions.remove(action)
                    self.policy[key] = random.choice(actions)
            
            # Limpiar experiencia antigua
            if len(self.experience) > 1000:
                self.experience = self.experience[-500:]
                
        except Exception as e:
            print(f"⚠️ Error en PolicyAgent.update: {e}")

    def get_win_rate(self):
        """Calcula tasa de victoria basada en experiencia"""
        if not self.experience:
            return 0.0
        
        wins = sum(1 for _, _, reward in self.experience if reward > 0)
        return wins / len(self.experience)


class HeuristicAgent:
    """Agente que usa heurísticas de poker básicas"""
    
    def __init__(self, aggression=0.3):
        self.aggression = aggression  # Factor de agresividad (0-1)
        self.hands_played = 0
        self.wins = 0
        
    def action(self, state):
        """Selecciona acción usando heurísticas simples"""
        try:
            self.hands_played += 1
            
            # Estrategia heurística básica
            rand = random.random()
            
            # Factor de agresividad dinámico
            current_aggression = self.aggression
            if self.hands_played > 10:
                win_rate = self.wins / self.hands_played
                if win_rate > 0.6:
                    current_aggression += 0.1
                elif win_rate < 0.3:
                    current_aggression -= 0.1
                current_aggression = max(0.1, min(0.8, current_aggression))
            
            # Decisiones ponderadas
            if rand < 0.15:  # 15% fold
                return 0
            elif rand < 0.85 - current_aggression:  # Variable call
                return 1
            else:  # Resto bet/raise
                return 2
                
        except Exception as e:
            print(f"⚠️ Error en HeuristicAgent.action: {e}")
            return 1  # Call por defecto

    def update_result(self, won):
        """Actualiza estadísticas del agente"""
        if won:
            self.wins += 1


class RandomAgent:
    """Agente completamente aleatorio para testing"""
    
    def __init__(self, weights=None):
        # Pesos para fold, call, bet (por defecto equiprobable)
        self.weights = weights or [1, 1, 1]
        self.total_actions = 0
        
    def action(self, state):
        """Selecciona acción aleatoria"""
        try:
            self.total_actions += 1
            return random.choices([0, 1, 2], weights=self.weights)[0]
        except Exception as e:
            print(f"⚠️ Error en RandomAgent.action: {e}")
            return random.choice([0, 1, 2])


class ConservativeAgent:
    """Agente conservador que evita riesgos"""
    
    def __init__(self):
        self.fold_threshold = 0.7
        self.bet_threshold = 0.9
        
    def action(self, state):
        """Estrategia muy conservadora"""
        try:
            rand = random.random()
            
            if rand < self.fold_threshold:
                return 1  # Call/check preferido
            elif rand < self.bet_threshold:
                return 0  # Fold cuando inseguro
            else:
                return 2  # Bet solo cuando muy seguro
                
        except Exception as e:
            print(f"⚠️ Error en ConservativeAgent.action: {e}")
            return 1


class AggressiveAgent:
    """Agente agresivo que apuesta frecuentemente"""
    
    def __init__(self):
        self.aggression = 0.6
        
    def action(self, state):
        """Estrategia agresiva"""
        try:
            rand = random.random()
            
            if rand < 0.1:  # Raramente fold
                return 0
            elif rand < 0.5 - self.aggression:  # Menos calls
                return 1
            else:  # Más bets
                return 2
                
        except Exception as e:
            print(f"⚠️ Error en AggressiveAgent.action: {e}")
            return 2


def create_agent(agent_type="policy", **kwargs):
    """Factory function para crear agentes"""
    agents = {
        "policy": PolicyAgent,
        "heuristic": HeuristicAgent,
        "random": RandomAgent,
        "conservative": ConservativeAgent,
        "aggressive": AggressiveAgent
    }
    
    agent_class = agents.get(agent_type.lower(), PolicyAgent)
    return agent_class(**kwargs)


def test_agents():
    """Función de testing para los agentes"""
    print("🧪 Testing agentes de poker...")
    
    # Crear agentes
    agents = [
        ("Policy", PolicyAgent()),
        ("Heuristic", HeuristicAgent()),
        ("Random", RandomAgent()),
        ("Conservative", ConservativeAgent()),
        ("Aggressive", AggressiveAgent())
    ]
    
    # Test con estado dummy
    dummy_state = {"hand": [(14, "Corazones"), (13, "Copas")], "pot": 100}
    
    print("\n📊 Resultados de 100 acciones por agente:")
    for name, agent in agents:
        actions = [agent.action(dummy_state) for _ in range(100)]
        fold_count = actions.count(0)
        call_count = actions.count(1)
        bet_count = actions.count(2)
        
        print(f"{name:12} - Fold: {fold_count:2}%, Call: {call_count:2}%, Bet: {bet_count:2}%")
    
    # Test obs_to_vector
    print("\n🔧 Test obs_to_vector:")
    test_obs = {
        "hand": [(14, "Corazones"), (13, "Copas")],
        "board": [(10, "Diamantes"), (11, "Trebol")],
        "pot": 150,
        "stack": 2000,
        "current_bet": 50
    }
    
    vector = obs_to_vector(test_obs)
    print(f"Vector resultado: {vector[:10]}... (tamaño: {len(vector)})")
    
    print("✅ Tests completados")


if __name__ == "__main__":
    test_agents()