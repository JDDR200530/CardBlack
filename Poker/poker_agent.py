# poker_agent.py
import os, numpy as np

MODEL_DEFAULT = "holdem_policy.h5"

def card_to_name(card):
    r, s = card
    rstr = {14:"A",13:"K",12:"Q",11:"J"}.get(r, str(r))
    return f"{rstr}_{s}"

def obs_to_vector(obs):
    # Minimal encoding: hole ranks + board ranks + stage one-hot + pot
    # hole: 2 ranks -> one-hot 13 each
    ranks = [2,3,4,5,6,7,8,9,10,11,12,13,14]
    idx = {r:i for i,r in enumerate(ranks)}
    vec = []
    hole = obs["hole"]
    for c in hole:
        v = [0]*13
        v[idx[c[0]]] = 1
        vec += v
    board = list(obs["board"])
    # up to 5 cards
    for i in range(5):
        v = [0]*13
        if i < len(board):
            v[idx[board[i][0]]] = 1
        vec += v
    # pot and bets numeric
    vec.append(obs["pot"])
    vec.append(obs["own_bet"] if "own_bet" in obs else 0)
    # stage one-hot
    stages = ["preflop","flop","turn","river","showdown"]
    svec = [1 if obs["stage"]==st else 0 for st in stages]
    vec += svec
    return np.array(vec, dtype=float).reshape(1,-1)

class RandomAgent:
    def __init__(self, seed=None):
        pass
    def action(self, obs, legal=None):
        return int(np.random.choice([0,1,2]))

class HeuristicAgent:
    """
    Very simple heuristics: bet if pair or high card A/K/Q preflop; call if moderate.
    """
    def __init__(self):
        pass

    def action(self, obs, legal=None):
        hole = obs["hole"]
        board = list(obs["board"])
        ranks = [c[0] for c in list(hole) + list(board)]
        # if pair or high ace -> bet
        if hole[0][0] == hole[1][0]:
            return 2
        if any(r >= 14 for r in [hole[0][0], hole[1][0]]):
            return 2
        # if flop present and pair on board -> call
        if len(board) >=3:
            if hole[0][0] in [b[0] for b in board] or hole[1][0] in [b[0] for b in board]:
                return 1
        # else sometimes check
        import random
        return random.choices([0,1,2], weights=[0.2,0.6,0.2])[0]

class PolicyAgent:
    def __init__(self, model_path=MODEL_DEFAULT):
        self.model = None
        if os.path.exists(model_path):
            try:
                from tensorflow.keras.models import load_model
                self.model = load_model(model_path)
            except Exception as e:
                print("PolicyAgent load failed:", e)
                self.model = None

    def action(self, obs, legal=None, greedy=True):
        if self.model is None:
            # fallback heuristic
            return HeuristicAgent().action(obs)
        x = obs_to_vector(obs)
        logits = self.model.predict(x, verbose=0)[0]
        exps = np.exp(logits - logits.max())
        probs = exps / (exps.sum()+1e-8)
        if greedy:
            return int(np.argmax(probs))
        else:
            return int(np.random.choice([0,1,2], p=probs))
