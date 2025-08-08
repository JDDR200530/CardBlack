# holdem_env.py
import random
from typing import List, Tuple, Dict, Any

RANKS = [2,3,4,5,6,7,8,9,10,11,12,13,14]  # 11=J,12=Q,13=K,14=A
SUITS = ["Corazones","Diamantes","Trebol","Copas"]

def rank_name(r:int):
    if r==14: return "A"
    if r==13: return "K"
    if r==12: return "Q"
    if r==11: return "J"
    return str(r)

class HoldemEnv:
    def __init__(self, n_players:int=4, seed=None):
        assert 2 <= n_players <= 9
        self.n_players = n_players
        self.rng = random.Random(seed)
        self.reset()

    def new_deck(self):
        deck = [(r,s) for r in RANKS for s in SUITS]
        self.rng.shuffle(deck)
        return deck

    def reset(self):
        self.deck = self.new_deck()
        # hole cards per player
        self.hands: List[List[Tuple[int,str]]] = [ [self.deck.pop(), self.deck.pop()] for _ in range(self.n_players) ]
        self.board: List[Tuple[int,str]] = []
        # simple pot/bets: each puts ante 1
        self.pot = 0
        self.stacks = [1000 for _ in range(self.n_players)]
        # For simplicity ante 1 from each active player
        self.active = [True for _ in range(self.n_players)]
        for i in range(self.n_players):
            self.stacks[i] -= 1
            self.pot += 1
        self.bets = [0 for _ in range(self.n_players)]
        self.round_stage = "preflop"  # preflop, flop, turn, river, showdown
        self.current_player = 0  # button mechanics not considered; we start at 0
        self.raises_in_round = 0
        self.terminal = False
        return self._get_state(0)

    def _get_state(self, player:int):
        return {
            "player": player,
            "hole": tuple(self.hands[player]),
            "board": tuple(self.board),
            "pot": self.pot,
            "stacks": tuple(self.stacks),
            "bets": tuple(self.bets),
            "active": tuple(self.active),
            "stage": self.round_stage
        }

    def legal_actions(self, player:int):
        # 0 fold, 1 check/call, 2 bet/raise (fixed)
        if not self.active[player]:
            return []
        return [0,1,2]

    def step(self, player:int, action:int):
        """
        player: who acts; action in {0,1,2}
        Returns: (done_flag, info_dict)
        info_dict contains 'message' and if terminal 'winners' etc.
        """
        if self.terminal:
            return True, {"msg":"Hand already finished"}

        if not self.active[player]:
            return False, {"msg":"Player inactive"}

        if action == 0:  # fold
            self.active[player] = False
            # if only one left, that player wins
            if sum(1 for a in self.active if a) == 1:
                winner = next(i for i,a in enumerate(self.active) if a)
                self.stacks[winner] += self.pot
                self.terminal = True
                return True, {"msg":"folded","winner":winner}
            # else move turn
            self._advance_player()
            return False, {"msg":"fold"}

        if action == 1:  # check/call: we call to match max(bets)
            max_bet = max(self.bets)
            to_call = max_bet - self.bets[player]
            if to_call > self.stacks[player]:
                to_call = self.stacks[player]
            self.stacks[player] -= to_call
            self.bets[player] += to_call
            self.pot += to_call
            # check if betting round finished:
            finished = self._check_betting_round_end()
            if finished:
                progressed = self._progress_stage()
                if progressed:
                    # reset bets for next round
                    self.bets = [0 for _ in range(self.n_players)]
                    self.raises_in_round = 0
                else:
                    # showdown
                    winners = self._resolve_showdown()
                    for w in winners:
                        self.stacks[w] += self.pot // len(winners)
                    self.terminal = True
                    return True, {"msg":"showdown","winners":winners}
            self._advance_player()
            return False, {"msg":"call/check"}

        if action == 2:  # bet/raise fixed size 10
            raise_amt = 10
            amount = min(raise_amt, self.stacks[player])
            self.stacks[player] -= amount
            self.bets[player] += amount
            self.pot += amount
            self.raises_in_round += 1
            self._advance_player()
            return False, {"msg":"bet", "amount":amount}

        return False, {"msg":"unknown"}

    def _advance_player(self):
        # next active player
        for _ in range(self.n_players):
            self.current_player = (self.current_player + 1) % self.n_players
            if self.active[self.current_player]:
                return

    def _check_betting_round_end(self):
        # simplistic: betting round ends when all active players have same bet amount
        active_bets = [self.bets[i] for i in range(self.n_players) if self.active[i]]
        return len(active_bets) > 0 and all(b == active_bets[0] for b in active_bets)

    def _progress_stage(self):
        # progresses and returns True if progressed to next non-showdown stage, False if reaches showdown
        if self.round_stage == "preflop":
            # flop: 3 cards
            self.board += [self.deck.pop(), self.deck.pop(), self.deck.pop()]
            self.round_stage = "flop"
            return True
        elif self.round_stage == "flop":
            self.board.append(self.deck.pop())
            self.round_stage = "turn"
            return True
        elif self.round_stage == "turn":
            self.board.append(self.deck.pop())
            self.round_stage = "river"
            return True
        elif self.round_stage == "river":
            self.round_stage = "showdown"
            return False
        return False

    # --- Hand evaluation (simple but sufficient) ---
    def _rank_hand(self, cards: List[Tuple[int,str]]):
        # returns tuple that compares lexicographically higher = better
        ranks = sorted([c[0] for c in cards], reverse=True)
        suits = [c[1] for c in cards]
        # straight detection
        uniq = sorted(set(ranks), reverse=True)
        straight_high = None
        for i in range(len(uniq)-4+1):
            window = uniq[i:i+5]
            if len(window) >=5 and window[0] - window[-1] == 4:
                straight_high = window[0]
                break
        # flush detection
        for s in SUITS:
            if suits.count(s) >=5:
                # collect top 5 ranks of that suit
                suit_ranks = sorted([c[0] for c in cards if c[1]==s], reverse=True)[:5]
                return (8, suit_ranks)  # treat as flush rank 8
        # counts
        from collections import Counter
        cnt = Counter(ranks)
        common = cnt.most_common()
        # check four of a kind
        if common[0][1] == 4:
            four = common[0][0]
            kicker = max(r for r in ranks if r != four)
            return (7, four, kicker)
        # full house
        if common[0][1] == 3 and len(common) > 1 and common[1][1] >= 2:
            three = common[0][0]
            pair = common[1][0]
            return (6, three, pair)
        if common[0][1] == 3:
            three = common[0][0]
            kickers = sorted([r for r in ranks if r != three], reverse=True)[:2]
            return (3, three, kickers)
        if len(common) >=2 and common[0][1] == 2 and common[1][1] == 2:
            pair1, pair2 = common[0][0], common[1][0]
            kick = max(r for r in ranks if r != pair1 and r != pair2)
            return (2, max(pair1,pair2), min(pair1,pair2), kick)
        if common[0][1] == 2:
            pair = common[0][0]
            kickers = sorted([r for r in ranks if r != pair], reverse=True)[:3]
            return (1, pair, kickers)
        # straight (if found)
        if straight_high is not None:
            return (4, straight_high)
        # high card
        return (0, ranks[:5])

    def _resolve_showdown(self):
        # return list of winners (indices)
        best = None
        winners = []
        for i in range(self.n_players):
            if not self.active[i]:
                continue
            cards = self.hands[i] + self.board
            rank = self._rank_hand(cards)
            if best is None or rank > best:
                best = rank
                winners = [i]
            elif rank == best:
                winners.append(i)
        return winners

    def debug(self):
        print("Stage:", self.round_stage)
        print("Board:", self.board)
        print("Hands:", self.hands)
        print("Active:", self.active)
        print("Pot:", self.pot)
        print("Stacks:", self.stacks)
