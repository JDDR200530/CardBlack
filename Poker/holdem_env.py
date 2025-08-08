import random
from typing import Tuple, Dict, Any, List

RANKS = [2,3,4,5,6,7,8,9,10,11,12,13,14]  # 11=J,12=Q,13=K,14=A
SUITS = ["Corazones","Diamantes","Trebol","Copas"]

def rank_name(r:int):
    if r==14: return "A"
    if r==13: return "K"
    if r==12: return "Q"
    if r==11: return "J"
    return str(r)

class HoldemEnv:
    """
    Entorno Heads-up Texas Hold'em simplificado para N jugadores.
    """
    def __init__(self, n_players=2, seed=None):
        assert n_players >= 2, "Se necesitan al menos 2 jugadores"
        self.n_players = n_players
        self.rng = random.Random(seed)
        self.deck = []
        self.reset()

    def new_deck(self):
        self.deck = [(r,s) for r in RANKS for s in SUITS]
        self.rng.shuffle(self.deck)

    def reset(self) -> Tuple[Dict[str,Any], Dict]:
        self.new_deck()
        # Repartir cartas ocultas
        self.hands = [ [self.deck.pop(), self.deck.pop()] for _ in range(self.n_players) ]
        self.board: List[Tuple[int,str]] = []
        self.pot = 0
        self.bets = [0]*self.n_players  # apuestas actuales por jugador
        self.current_player = 0
        self.round_stage = "preflop"  # preflop, flop, turn, river, showdown
        self.terminal = False
        self.last_aggressive = -1
        self.max_raises_in_round = 2
        self.raises_this_round = 0

        # Ante simple: todos ponen 1 ficha
        self.bets = [1]*self.n_players
        self.pot = self.n_players  # suma de antes
        return self._get_obs(self.current_player), {}

    def _get_obs(self, player:int):
        return {
            "hole": tuple(self.hands[player]),
            "board": tuple(self.board),
            "pot": self.pot,
            "own_bet": self.bets[player],
            "opp_bets": tuple(self.bets[:player] + self.bets[player+1:]),
            "stage": self.round_stage,
            "to_act": player
        }

    def legal_actions(self):
        return [0,1,2]  # fold, check/call, bet/raise

    def step(self, player:int, action:int):
        if self.terminal:
            raise RuntimeError("Mano terminada.")

        if player != self.current_player:
            raise RuntimeError("No es turno del jugador.")

        if action not in (0,1,2):
            raise ValueError("Acción inválida.")

        if action == 0:  # fold
            self.terminal = True
            winner = [i for i in range(self.n_players) if i != player]
            # Si sólo queda un ganador (quedan los demás sin fold), sumamos pot a ganador
            # Aquí asumimos ganador es el siguiente jugador no fold
            winner = winner[0] if winner else None
            reward = [0]*self.n_players
            if winner is not None:
                reward[winner] = self.pot - self.bets[winner]
                reward[player] = -reward[winner]
            return None, tuple(reward), True, {"winner": winner}

        # check/call
        max_bet = max(self.bets)
        if action == 1:
            diff = max_bet - self.bets[player]
            self.bets[player] += diff
            self.pot += diff
            self._advance_turn_or_stage()
            if self.round_stage == "showdown":
                self.terminal = True
                rewards = self._showdown_rewards()
                return None, rewards, True, {"winners": self._get_winners()}
            return self._get_obs(self.current_player), (0,)*self.n_players, False, {}

        # bet/raise
        if action == 2:
            if self.raises_this_round >= self.max_raises_in_round:
                # no permite más raises, tratar como call
                diff = max_bet - self.bets[player]
                self.bets[player] += diff
                self.pot += diff
                self._advance_turn_or_stage()
                if self.round_stage == "showdown":
                    self.terminal = True
                    rewards = self._showdown_rewards()
                    return None, rewards, True, {"winners": self._get_winners()}
                return self._get_obs(self.current_player), (0,)*self.n_players, False, {}

            self.bets[player] += 1  # apuesta fija
            self.pot += 1
            self.raises_this_round += 1
            self.last_aggressive = player
            self._advance_turn()
            return self._get_obs(self.current_player), (0,)*self.n_players, False, {}

    def _advance_turn(self):
        # Busca siguiente jugador que no haya fold (para demo asumimos ninguno fold)
        self.current_player = (self.current_player + 1) % self.n_players

    def _advance_turn_or_stage(self):
        # Si todas las apuestas iguales y se terminó ronda, avanzar stage
        if len(set(self.bets)) == 1:
            self.raises_this_round = 0
            self.last_aggressive = -1
            if self.round_stage == "preflop":
                self.board += [self.deck.pop() for _ in range(3)]
                self.round_stage = "flop"
            elif self.round_stage == "flop":
                self.board.append(self.deck.pop())
                self.round_stage = "turn"
            elif self.round_stage == "turn":
                self.board.append(self.deck.pop())
                self.round_stage = "river"
            elif self.round_stage == "river":
                self.round_stage = "showdown"
        self._advance_turn()

    def _hand_rank(self, cards):
        ranks = sorted([c[0] for c in cards], reverse=True)
        counts = {r:ranks.count(r) for r in set(ranks)}
        cnts = sorted(counts.items(), key=lambda x:(x[1],x[0]), reverse=True)
        if cnts[0][1] == 3:
            return (4, cnts[0][0])
        if len(cnts) >= 2 and cnts[0][1]==2 and cnts[1][1]==2:
            return (3, cnts[0][0], cnts[1][0])
        if cnts[0][1] == 2:
            kickers = [r for r in ranks if r != cnts[0][0]]
            return (2, cnts[0][0], kickers)
        return (1, ranks)

    def _showdown_rewards(self):
        hands_ranks = []
        for i in range(self.n_players):
            cards = self.hands[i] + self.board
            hands_ranks.append(self._hand_rank(cards))
        winner_rank = max(hands_ranks)
        winners = [i for i,rnk in enumerate(hands_ranks) if rnk == winner_rank]
        reward = [0]*self.n_players
        share = self.pot // len(winners)
        for w in winners:
            reward[w] = share
        for i in range(self.n_players):
            if i not in winners:
                reward[i] = -self.bets[i]
        return tuple(reward)

    def _get_winners(self):
        hands_ranks = []
        for i in range(self.n_players):
            cards = self.hands[i] + self.board
            hands_ranks.append(self._hand_rank(cards))
        winner_rank = max(hands_ranks)
        winners = [i for i,rnk in enumerate(hands_ranks) if rnk == winner_rank]
        return winners

    def hands_to_cards(self, player:int):
        return list(self.hands[player])
