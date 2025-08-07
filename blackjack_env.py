# blackjack_env.py
import random

class BlackjackEnv:
    def __init__(self):
        self.deck = [i for i in range(1, 14)] * 4
        self.player = []
        self.dealer = []
        self.reset()

    def draw_card(self):
        return self.deck.pop(random.randint(0, len(self.deck) - 1))

    def card_value(self, card):
        return min(card, 10)

    def sum_hand(self, hand):
        total = sum(self.card_value(c) for c in hand)
        if 1 in hand and total + 10 <= 21:
            return total + 10
        return total

    def is_bust(self, hand):
        return self.sum_hand(hand) > 21

    def reset(self):
        self.deck = [i for i in range(1, 14)] * 4
        random.shuffle(self.deck)
        self.player = [self.draw_card(), self.draw_card()]
        self.dealer = [self.draw_card()]
        return self.player, self.dealer

    def step(self, action):
        if action == 1:  # 1 = hit, 0 = stand
            self.player.append(self.draw_card())
            if self.is_bust(self.player):
                return (self.player, self.dealer), -1, True, {}
            return (self.player, self.dealer), 0, False, {}
        else:
            while self.sum_hand(self.dealer) < 17:
                self.dealer.append(self.draw_card())
        
        player_score = self.sum_hand(self.player)
        dealer_score = self.sum_hand(self.dealer)
        
        if player_score > 21:
            reward = -1
        elif dealer_score > 21 or player_score > dealer_score:
            reward = 1
        elif player_score == dealer_score:
            reward = 0
        else:
            reward = -1
        
        return (self.player, self.dealer), reward, True, {}

    def get_winner(self):
        player_score = self.sum_hand(self.player)
        dealer_score = self.sum_hand(self.dealer)
        if self.is_bust(self.player):
            return "Dealer gana"
        elif self.is_bust(self.dealer):
            return "Jugador gana"
        elif player_score > dealer_score:
            return "Jugador gana"
        elif dealer_score > player_score:
            return "Dealer gana"
        else:
            return "Empate"
