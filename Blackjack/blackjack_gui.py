import pygame
import os
import random
import numpy as np
import tensorflow as tf
import json

# ==== CONFIGURACIÓN ====
ANCHO = 1000
ALTO = 600
FPS = 30
RUTA_CARTAS = "/home/togg/Documentos/CardBlack/cards"
MODEL_PATH = "/home/togg/Documentos/CardBlack/Blackjack/blackjack_dqn_model.keras"
SAVE_STATS_PATH = "/home/togg/Documentos/CardBlack/Blackjack/blackjack_stats.json"

# Colores
ROJO = (255, 80, 80)
VERDE_OSCURO = (20, 120, 20)
BLANCO = (255, 255, 255)
AZUL = (70, 130, 180)
NEGRO = (0, 0, 0)
GRIS = (40, 40, 40)
GRIS_CLARO = (180, 180, 180)
DORADO = (255, 200, 50)

# ==== CARGAR MODELO ====
model = tf.keras.models.load_model(MODEL_PATH)

# ==== CLASE ENTORNO BLACKJACK ====
class BlackjackEnv:
    def __init__(self):
        self.reset()
        self.stats = {"wins": 0, "losses": 0, "draws": 0}
        self.load_stats()

    def reset(self):
        self.deck = self.crear_mazo()
        random.shuffle(self.deck)
        self.ai_hand = [self.deck.pop(), self.deck.pop()]
        self.dealer_hand = [self.deck.pop(), self.deck.pop()]
        self.done = False
        self.winner = None
        return self.get_state()

    def crear_mazo(self):
        palos = ["Copas", "Corazones", "Diamantes", "Trebol"]
        numeros = ["A"] + [str(n) for n in range(2, 11)] + ["J", "Q", "K"]
        return [(n, p) for p in palos for n in numeros]

    def get_hand_sum(self, hand):
        valores = [10 if c[0] in ["J", "Q", "K"] else 1 if c[0] == "A" else int(c[0]) for c in hand]
        total = sum(valores)
        if 1 in valores and total + 10 <= 21:
            total += 10
        return total

    def get_state(self):
        ai_sum = self.get_hand_sum(self.ai_hand)
        dealer_card = 10 if self.dealer_hand[0][0] in ["J", "Q", "K"] else 1 if self.dealer_hand[0][0] == "A" else int(self.dealer_hand[0][0])
        usable_ace = 1 if any(c[0] == "A" for c in self.ai_hand) and ai_sum + 10 <= 21 else 0
        return np.array([ai_sum, dealer_card, usable_ace], dtype=np.float32)

    def step(self, action):
        if action == 1:  # Pedir carta
            self.ai_hand.append(self.deck.pop())
            if self.get_hand_sum(self.ai_hand) > 21:
                self.done = True
                self.winner = "dealer"
        else:  # Plantarse
            self.done = True
            self.turno_dealer()

    def turno_dealer(self):
        while self.get_hand_sum(self.dealer_hand) < 17:
            self.dealer_hand.append(self.deck.pop())
        self.resolver_ganador()

    def resolver_ganador(self):
        ai_sum = self.get_hand_sum(self.ai_hand)
        dealer_sum = self.get_hand_sum(self.dealer_hand)

        if ai_sum > 21:
            self.winner = "dealer"
        elif dealer_sum > 21 or ai_sum > dealer_sum:
            self.winner = "ia"
        elif ai_sum < dealer_sum:
            self.winner = "dealer"
        else:
            self.winner = "draw"

        if self.winner == "ia":
            self.stats["wins"] += 1
        elif self.winner == "dealer":
            self.stats["losses"] += 1
        else:
            self.stats["draws"] += 1

    def load_stats(self):
        try:
            with open(SAVE_STATS_PATH, 'r') as f:
                saved = json.load(f)
                self.stats = saved.get("ia_stats", self.stats)
        except:
            pass

    def save_stats(self):
        try:
            with open(SAVE_STATS_PATH, 'w') as f:
                json.dump({"ia_stats": self.stats}, f, indent=2)
        except:
            pass

# ==== FUNCIONES PYGAME ====
def cargar_cartas():
    cartas = {}
    for archivo in os.listdir(RUTA_CARTAS):
        if archivo.endswith(".png"):
            nombre = archivo.replace(".png", "")
            img = pygame.image.load(os.path.join(RUTA_CARTAS, archivo))
            img = pygame.transform.smoothscale(img, (70, 100))
            cartas[nombre] = img
    return cartas

def mostrar_mano(pantalla, cartas_img, mano, x, y, ocultar_primera=False, etiqueta=None):
    for i, carta in enumerate(mano):
        if i == 0 and ocultar_primera:
            img = cartas_img["Reverso"]
        else:
            img = cartas_img.get(f"{carta[0]}_{carta[1]}", cartas_img["Reverso"])
        pantalla.blit(img, (x + i * 75, y))
    if etiqueta:
        fuente = pygame.font.Font(None, 28)
        suma = env.get_hand_sum(mano)
        texto = fuente.render(f"{etiqueta}: {suma}", True, BLANCO)
        pantalla.blit(texto, (x, y + 105))

def dibujar_boton(pantalla, texto, x, y, ancho, alto, color_fondo, color_texto, hover=False):
    fuente = pygame.font.Font(None, 28)
    rect = pygame.Rect(x, y, ancho, alto)
    color = tuple(min(255, c + 25) for c in color_fondo) if hover else color_fondo
    pygame.draw.rect(pantalla, color, rect, border_radius=12)
    pygame.draw.rect(pantalla, DORADO, rect, 2, border_radius=12)
    texto_render = fuente.render(texto, True, color_texto)
    pantalla.blit(texto_render, (x + (ancho - texto_render.get_width()) // 2,
                                  y + (alto - texto_render.get_height()) // 2))
    return rect

def mostrar_resultado(pantalla, ganador):
    if ganador:
        fuente = pygame.font.Font(None, 48)
        if ganador == "ia":
            texto = "¡Gana la IA!"
            color = AZUL
        elif ganador == "dealer":
            texto = "Gana el Dealer"
            color = ROJO
        else:
            texto = "Empate"
            color = GRIS_CLARO

        render = fuente.render(texto, True, color)
        # Rectángulo de fondo para contraste
        rect_fondo = pygame.Rect(0, 0, render.get_width() + 40, render.get_height() + 20)
        rect_fondo.center = (ANCHO // 2, ALTO // 2 + 150)
        pygame.draw.rect(pantalla, NEGRO, rect_fondo, border_radius=10)
        pygame.draw.rect(pantalla, DORADO, rect_fondo, 3, border_radius=10)
        # Texto centrado
        pantalla.blit(render, (rect_fondo.x + 20, rect_fondo.y + 10))

def mostrar_estadisticas(pantalla, env, mouse_pos):
    fuente = pygame.font.Font(None, 30)
    pygame.draw.rect(pantalla, (30, 30, 30), (800, 0, 200, ALTO))
    pygame.draw.rect(pantalla, DORADO, (800, 0, 200, ALTO), 3, border_radius=5)

    titulo = fuente.render("Estadísticas", True, BLANCO)
    pantalla.blit(titulo, (820, 20))
    pygame.draw.line(pantalla, GRIS_CLARO, (810, 55), (990, 55), 1)

    y = 70
    for label, val, color in [
        ("Victorias", env.stats["wins"], AZUL),
        ("Derrotas", env.stats["losses"], ROJO),
        ("Empates", env.stats["draws"], GRIS_CLARO)
    ]:
        txt = fuente.render(f"{label}: {val}", True, color)
        pantalla.blit(txt, (820, y))
        y += 35

    total = env.stats["wins"] + env.stats["losses"] + env.stats["draws"]
    win_rate = (env.stats["wins"] / total * 100) if total else 0
    pantalla.blit(fuente.render(f"Win Rate: {win_rate:.1f}%", True, DORADO), (820, y + 10))

    boton_siguiente = dibujar_boton(
        pantalla, "Siguiente Ronda", 810, y + 50, 180, 40, AZUL, BLANCO,
        hover=pygame.Rect(810, y + 50, 180, 40).collidepoint(mouse_pos)
    )
    boton_nueva = dibujar_boton(
        pantalla, "Nueva Partida", 810, y + 100, 180, 40, ROJO, BLANCO,
        hover=pygame.Rect(810, y + 100, 180, 40).collidepoint(mouse_pos)
    )
    return boton_siguiente, boton_nueva

# ==== LOOP PRINCIPAL ====
def main():
    pygame.init()
    pantalla = pygame.display.set_mode((ANCHO, ALTO))
    pygame.display.set_caption("Blackjack: IA vs Dealer")
    clock = pygame.time.Clock()

    cartas_img = cargar_cartas()
    global env
    env = BlackjackEnv()

    corriendo = True
    jugando = True
    turno = "ia"
    ultimo_movimiento = pygame.time.get_ticks()
    delay_ms = 800

    while corriendo:
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                corriendo = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if boton_siguiente_stats and boton_siguiente_stats.collidepoint(mouse_pos):
                    env.reset()
                    jugando = True
                    turno = "ia"
                    ultimo_movimiento = pygame.time.get_ticks()
                if boton_nueva_stats and boton_nueva_stats.collidepoint(mouse_pos):
                    env.stats = {"wins": 0, "losses": 0, "draws": 0}
                    env.reset()
                    jugando = True
                    turno = "ia"
                    ultimo_movimiento = pygame.time.get_ticks()

        pantalla.fill(VERDE_OSCURO)

        if jugando and not env.done and turno == "ia":
            if pygame.time.get_ticks() - ultimo_movimiento > delay_ms:
                state = np.array([env.get_state()])
                q_values = model.predict(state, verbose=0)
                env.step(np.argmax(q_values[0]))
                ultimo_movimiento = pygame.time.get_ticks()
                if env.done:
                    jugando = False

        mostrar_mano(pantalla, cartas_img, env.dealer_hand, 50, 50,
                     ocultar_primera=not env.done, etiqueta="Dealer")
        mostrar_mano(pantalla, cartas_img, env.ai_hand, 50, 250, etiqueta="IA")

        if env.done:
            mostrar_resultado(pantalla, env.winner)

        boton_siguiente_stats, boton_nueva_stats = mostrar_estadisticas(pantalla, env, mouse_pos)

        pygame.display.flip()
        clock.tick(FPS)

    env.save_stats()
    pygame.quit()

if __name__ == "__main__":
    main()
