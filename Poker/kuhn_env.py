# kuhn_env.py
import random
from typing import Tuple, Dict, Any

class KuhnEnv:
    """
    Entorno simple de Kuhn Poker para 2 jugadores.
    Cartas codificadas 1..3 (1=J,2=Q,3=K).
    Acciones: 0 = pass/check, 1 = bet (o call/fold según contexto).
    Observación para current player: (mi_carta, historial_tuple)
    Step devuelve: obs_next (o None si terminal), reward_tuple (r0,r1), done, info
    """
    def __init__(self, seed=None):
        self.cards = [1,2,3]
        self.reset(seed=seed)

    def reset(self, seed=None) -> Tuple[Tuple[int, tuple], Dict[str,Any]]:
        if seed is not None:
            random.seed(seed)
        deck = self.cards.copy()
        random.shuffle(deck)
        self.player_cards = [deck.pop(), deck.pop()]
        self.history = []  # acciones en orden
        self.current_player = 0  # jugador 0 empieza
        self.terminal = False
        self.pot = 2  # each antes pone 1
        self.extra = 0
        obs = self._get_obs(self.current_player)
        return obs, {}

    def _get_obs(self, player:int):
        return (self.player_cards[player], tuple(self.history))

    def legal_actions(self):
        return [0,1]

    def step(self, action:int):
        if self.terminal:
            raise RuntimeError("Step en entorno terminado.")
        if action not in (0,1):
            raise ValueError("Acción inválida.")
        self.history.append(action)

        done = False
        reward = (0.0, 0.0)
        h = self.history

        # reglas de terminación de Kuhn (versión estándar mínima)
        # 1) if history == [0,0] -> showdown
        if len(h) == 2 and h[0] == 0 and h[1] == 0:
            done = True
            reward = self._showdown(extra=0)
        # 2) if h == [1,0] -> bettor wins (other folded)
        elif len(h) == 2 and h[0] == 1 and h[1] == 0:
            done = True
            # el que apostó gana +1 (net)
            reward = (1.0, -1.0)
        # 3) if h == [1,1] -> call, showdown with extra bet
        elif len(h) == 2 and h[0] == 1 and h[1] == 1:
            done = True
            reward = self._showdown(extra=1)
        # 4) if h == [0,1,0] -> player0 folded to bet -> player1 wins
        elif len(h) == 3 and h == [0,1,0]:
            done = True
            reward = (-1.0, 1.0)
        # 5) if h == [0,1,1] -> player0 called after facing bet -> showdown with extra
        elif len(h) == 3 and h == [0,1,1]:
            done = True
            reward = self._showdown(extra=1)
        else:
            # cambia de turno
            self.current_player = 1 - self.current_player

        self.terminal = done
        obs = self._get_obs(self.current_player) if not done else None
        return obs, reward, done, {}

    def _showdown(self, extra=0):
        # quien tiene mayor carta gana; extra representa apuesta adicional
        p0 = self.player_cards[0]
        p1 = self.player_cards[1]
        if p0 > p1:
            return (1.0 + extra, -1.0 - extra)
        elif p1 > p0:
            return (-1.0 - extra, 1.0 + extra)
        else:
            return (0.0, 0.0)

    def render(self):
        names = {1:'J',2:'Q',3:'K'}
        print("Cards:", [names[c] for c in self.player_cards], "Hist:", self.history, "Turn:", self.current_player)
