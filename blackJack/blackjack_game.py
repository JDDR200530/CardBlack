# blackjack_game.py
import random
import os
import pygame

class BlackjackGame:
    def __init__(self, ruta_cartas="E:\Sistemas\CardBlack\CardBlack\cards"):
        # Palos y valores estándar
        self.PALOS = ["Corazones", "Diamantes", "Trebol", "Copas"]
        self.VALORES = ['A'] + [str(i) for i in range(2, 11)] + ['J', 'Q', 'K']

        # Ruta a la carpeta de imágenes
        self.ruta_cartas = ruta_cartas

        # Cache de imágenes y reverso
        self.imagenes_cache = {}
        self.reverso_img = self.cargar_reverso()

        # Inicializar baraja
        self.reset_game()

    def cargar_reverso(self):
        """Carga la imagen del reverso de la carta."""
        try:
            ruta = os.path.join(self.ruta_cartas, "Reverso.png")
            imagen = pygame.image.load(ruta)
            return pygame.transform.scale(imagen, (100, 145))
        except pygame.error:
            # Si falla, crea una superficie en blanco como fallback
            superficie = pygame.Surface((100, 145))
            superficie.fill((40, 120, 200)) # Un color azul para el reverso
            return superficie

    def reset_game(self, multiplicador=4):
        """Crea y mezcla la baraja."""
        self.baraja = [(v, p) for p in self.PALOS for v in self.VALORES] * multiplicador
        random.shuffle(self.baraja)
        self.dealer_cards = []
        self.player_cards = []
        self.game_over = False

    def _formatear_nombre(self, carta):
        """Convierte ('A', 'Corazones') → 'A_Corazones.png'"""
        valor, palo = carta
        return f"{valor}_{palo}"

    def cargar_imagen(self, carta):
        """Carga imagen de carta desde la ruta especificada usando Pygame."""
        nombre_carta = self._formatear_nombre(carta)
        try:
            ruta = os.path.join(self.ruta_cartas, f"{nombre_carta}.png")
            imagen = pygame.image.load(ruta)
            return pygame.transform.scale(imagen, (100, 145))
        except:
            # Si falta la imagen, genera una carta en blanco
            superficie = pygame.Surface((100, 145))
            superficie.fill((255, 255, 255))
            return superficie

    def repartir_carta(self):
        """Reparte una carta con su imagen."""
        carta = self.baraja.pop()
        if carta not in self.imagenes_cache:
            self.imagenes_cache[carta] = self.cargar_imagen(carta)
        return carta, self.imagenes_cache[carta]

    def calcular_mano(self, mano):
        """Calcula el valor de una mano de cartas."""
        return self.valor_mano(mano)

    def valor_carta(self, carta):
        valor, _ = carta
        if valor in ['J', 'Q', 'K']:
            return 10
        if valor == 'A':
            return 11
        return int(valor)

    def valor_mano(self, mano):
        total = sum(self.valor_carta(c) for c in mano)
        ases = sum(1 for c in mano if c[0] == 'A')
        while total > 21 and ases:
            total -= 10
            ases -= 1
        return total

    def determinar_ganador(self):
        player_score = self.valor_mano(self.player_cards)
        dealer_score = self.valor_mano(self.dealer_cards)

        if player_score > 21:
            return "¡Te pasaste! Pierdes"
        elif dealer_score > 21:
            return "¡Dealer se pasó! Ganas"
        elif player_score > dealer_score:
            return "¡Ganaste!"
        elif dealer_score > player_score:
            return "Dealer gana"
        else:
            return "Empate"