# blackjack_pygame.py
import pygame
import sys
import time
from blackjack_game import BlackjackGame
from ai_agent import AIAgent

# ---------- Config ----------
FPS = 30
ANCHO, ALTO = 1000, 700
BG_COLOR = (8, 120, 60)   # verde casino
CARD_BG = (250, 250, 250)
CARD_BORDER = (0, 0, 0)
TEXT_COLOR = (20, 20, 20)
BUTTON_COLOR = (230, 230, 230)
BUTTON_BORDER = (10, 10, 10)

MODEL_PATH = "policy_blackjack.h5"

# ---------- Inicializar Pygame ----------
pygame.init()
pantalla = pygame.display.set_mode((ANCHO, ALTO))
pygame.display.set_caption("Blackjack - Pygame + IA")
reloj = pygame.time.Clock()
FUENTE = pygame.font.SysFont("Arial", 22)
FUENTE_TIT = pygame.font.SysFont("Arial", 28, bold=True)

# ---------- Funciones auxiliares ----------
def dibujar_texto(superficie, texto, x, y, fuente=FUENTE, color=(255,255,255)):
    txt = fuente.render(texto, True, color)
    superficie.blit(txt, (x, y))

def dibujar_tarjeta(superficie, x, y, carta=None, ancho=100, alto=145):
    if carta is None:
        # Dibujar el reverso de la carta
        if GameUI.instance and GameUI.instance.juego.reverso_img:
            superficie.blit(GameUI.instance.juego.reverso_img, (x, y))
        else:
            # Fallback si la imagen del reverso no está disponible
            pygame.draw.rect(superficie, (40, 120, 200), (x, y, ancho, alto), border_radius=6)
    else:
        # Obtener la imagen de la carta del caché del juego
        imagen = GameUI.instance.juego.imagenes_cache.get(carta)
        if imagen:
            superficie.blit(imagen, (x, y))
        else:
            # Fallback si la imagen no está disponible
            pygame.draw.rect(superficie, CARD_BG, (x, y, ancho, alto), border_radius=6)
            pygame.draw.rect(superficie, CARD_BORDER, (x, y, ancho, alto), 2, border_radius=6)
            texto = carta_a_texto(carta)
            txt = FUENTE.render(texto, True, TEXT_COLOR)
            superficie.blit(txt, (x + 8, y + 8))

def dibujar_boton(superficie, rect, texto):
    pygame.draw.rect(superficie, BUTTON_COLOR, rect, border_radius=6)
    pygame.draw.rect(superficie, BUTTON_BORDER, rect, 2, border_radius=6)
    txt = FUENTE.render(texto, True, TEXT_COLOR)
    tx = rect[0] + (rect[2]-txt.get_width())//2
    ty = rect[1] + (rect[3]-txt.get_height())//2
    superficie.blit(txt, (tx, ty))

def carta_a_texto(carta):
    valor, palo = carta
    nombres = {'A':'A', 'J':'J', 'Q':'Q', 'K':'K'}
    if valor in nombres:
        v_texto = nombres[valor]
    else:
        v_texto = valor
    simbolos = {"Corazones":"♥", "Diamantes":"♦", "Trebol":"♣", "Copas":"♠"}
    p_texto = simbolos.get(palo, palo)
    return f"{v_texto}{p_texto}"

# ---------- Clase principal del juego UI ----------
class GameUI:
    instance = None
    
    def __init__(self):
        GameUI.instance = self
        self.juego = BlackjackGame()
        self.reset_all()
        # Intentamos cargar agente IA
        self.agent = None
        try:
            self.agent = AIAgent(MODEL_PATH)
            print("Agente cargado:", MODEL_PATH)
        except Exception as e:
            print("No se pudo cargar agente:", e)
            self.agent = None

    def reset_all(self):
        self.juego.reset_game()
        self.baraja = self.juego.baraja
        self.jugador = self.juego.player_cards
        self.dealer = self.juego.dealer_cards
        self.ia = []
        self.mensaje = ""
        self.mode = "menu"  # menu, play_human, play_ai, duel
        self.game_over = True
        self.show_ai_recommendation = False

    def start_new_round(self, mode):
        self.juego.reset_game()
        self.jugador.clear()
        self.dealer.clear()
        self.ia.clear()
        # repartir 2 cartas jugador y dealer
        for _ in range(2):
            c, _ = self.juego.repartir_carta()
            self.jugador.append(c)
        for _ in range(2):
            c, _ = self.juego.repartir_carta()
            self.dealer.append(c)
        if mode == "duel":
            for _ in range(2):
                c, _ = self.juego.repartir_carta()
                self.ia.append(c)
        self.mensaje = ""
        self.mode = mode
        self.player_turn = True
        self.game_over = False

    def player_hit(self):
        if self.game_over or not self.player_turn:
            return
        c, _ = self.juego.repartir_carta()
        self.jugador.append(c)
        if self.juego.calcular_mano(self.jugador) > 21:
            self.mensaje = "Te pasaste. (Jugador)"
            self.player_turn = False
            self.resolve_round()

    def player_stand(self):
        if self.game_over:
            return
        self.player_turn = False
        if self.mode == "duel":
            self.ia_play()
        else:
            self.resolve_round()

    def ia_play(self, greedy=True):
        if not self.ia:
            return
        while True:
            puntaje = self.juego.calcular_mano(self.ia)
            dealer_val = self.dealer[0] if self.dealer else None
            estado = (
                puntaje,
                self.juego.valor_carta(dealer_val) if dealer_val else 10,
                any(c[0] == 'A' for c in self.ia) and puntaje <= 21
            )
            if self.agent is None:
                if puntaje < 17:
                    c, _ = self.juego.repartir_carta()
                    self.ia.append(c)
                    if self.juego.calcular_mano(self.ia) > 21:
                        break
                else:
                    break
            else:
                accion = self.agent.action(estado, greedy=greedy)
                if accion == 1:
                    c, _ = self.juego.repartir_carta()
                    self.ia.append(c)
                    if self.juego.calcular_mano(self.ia) > 21:
                        break
                else:
                    break
        self.resolve_round()

    def resolve_round(self):
        while self.juego.calcular_mano(self.dealer) < 17:
            c, _ = self.juego.repartir_carta()
            self.dealer.append(c)

        puntaje_jugador = self.juego.calcular_mano(self.jugador)
        puntaje_dealer = self.juego.calcular_mano(self.dealer)
        puntaje_ia = self.juego.calcular_mano(self.ia) if self.ia else None

        resultados = []
        if puntaje_jugador > 21:
            resultados.append(("Jugador", -1))
        elif puntaje_dealer > 21 or puntaje_jugador > puntaje_dealer:
            resultados.append(("Jugador", 1))
        elif puntaje_jugador == puntaje_dealer:
            resultados.append(("Jugador", 0))
        else:
            resultados.append(("Jugador", -1))

        if self.ia:
            if puntaje_ia > 21:
                resultados.append(("IA", -1))
            elif puntaje_dealer > 21 or puntaje_ia > puntaje_dealer:
                resultados.append(("IA", 1))
            elif puntaje_ia == puntaje_dealer:
                resultados.append(("IA", 0))
            else:
                resultados.append(("IA", -1))

        partes = []
        for nombre, res in resultados:
            if res > 0:
                partes.append(f"{nombre}: Gana")
            elif res < 0:
                partes.append(f"{nombre}: Pierde")
            else:
                partes.append(f"{nombre}: Empate")
        self.mensaje = " | ".join(partes)
        self.game_over = True

    def ask_ai_recommendation(self):
        if self.agent is None or self.game_over:
            return None
        estado = (
            self.juego.calcular_mano(self.jugador),
            self.juego.valor_carta(self.dealer[0]) if self.dealer else 10,
            any(c[0] == 'A' for c in self.jugador) and self.juego.calcular_mano(self.jugador) <= 21
        )
        return self.agent.action(estado, greedy=True)

# ---------- Loop principal ----------
def main_loop():
    ui = GameUI()

    btn_new_h = (750, 60, 250, 40)
    btn_new_ai = (750, 110, 250, 40)
    btn_duel = (750, 170, 250, 40)
    btn_hit = (750, 250, 100, 45)
    btn_stand = (860, 250, 120, 45)
    btn_advice = (750, 320, 250, 40)
    btn_quit = (750, 380, 250, 40)
    btn_see_ai = (750, 440, 250, 40)

    while True:
        pantalla.fill(BG_COLOR)

        for evt in pygame.event.get():
            if evt.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if evt.type == pygame.MOUSEBUTTONDOWN and evt.button == 1:
                mx, my = evt.pos
                if pygame.Rect(btn_new_h).collidepoint(mx, my):
                    ui.start_new_round(mode="play_human")
                if pygame.Rect(btn_new_ai).collidepoint(mx, my):
                    ui.start_new_round(mode="play_ai")
                    if ui.ia == []:
                        ui.ia = ui.jugador
                        ui.jugador = []
                    ui.ia_play(greedy=True)
                if pygame.Rect(btn_duel).collidepoint(mx, my):
                    ui.start_new_round(mode="duel")
                if pygame.Rect(btn_hit).collidepoint(mx, my):
                    if ui.mode in ("play_human", "duel") and not ui.game_over:
                        ui.player_hit()
                if pygame.Rect(btn_stand).collidepoint(mx, my):
                    if ui.mode in ("play_human", "duel") and not ui.game_over:
                        ui.player_stand()
                if pygame.Rect(btn_advice).collidepoint(mx, my):
                    ui.show_ai_recommendation = not ui.show_ai_recommendation
                if pygame.Rect(btn_see_ai).collidepoint(mx, my):
                    if ui.agent is not None:
                        wins = ties = losses = 0
                        rounds = 100
                        for _ in range(rounds):
                            ui.juego.reset_game()
                            jugador = []
                            dealer = []
                            for _ in range(2):
                                c, _ = ui.juego.repartir_carta()
                                jugador.append(c)
                            for _ in range(2):
                                c, _ = ui.juego.repartir_carta()
                                dealer.append(c)
                            ia_hand = jugador.copy()
                            while ui.juego.calcular_mano(ia_hand) < 17:
                                c, _ = ui.juego.repartir_carta()
                                ia_hand.append(c)
                            while ui.juego.calcular_mano(dealer) < 17:
                                c, _ = ui.juego.repartir_carta()
                                dealer.append(c)
                            if ui.juego.calcular_mano(ia_hand) > 21:
                                losses += 1
                            elif ui.juego.calcular_mano(dealer) > 21 or ui.juego.calcular_mano(ia_hand) > ui.juego.calcular_mano(dealer):
                                wins += 1
                            elif ui.juego.calcular_mano(ia_hand) == ui.juego.calcular_mano(dealer):
                                ties += 1
                            else:
                                losses += 1
                        ui.mensaje = f"IA {rounds} partidas -> V:{wins} E:{ties} D:{losses}"
                    else:
                        ui.mensaje = "No hay modelo IA cargado."
                if pygame.Rect(btn_quit).collidepoint(mx, my):
                    pygame.quit()
                    sys.exit()

        # Mostrar texto y cartas
        dibujar_texto(pantalla, "Blackjack - Interfaz Pygame (H/Tips/IA)", 20, 10, FUENTE_TIT)
        
        # Dealer
        dibujar_texto(pantalla, "Dealer:", 20, 60)
        if ui.dealer:
            if not ui.game_over and ui.mode in ("play_human", "duel"):
                dibujar_tarjeta(pantalla, 20, 90, ui.dealer[0])
                dibujar_tarjeta(pantalla, 130, 90) # Llama a dibujar_tarjeta sin carta para el reverso
            else:
                x = 20
                for c in ui.dealer:
                    dibujar_tarjeta(pantalla, x, 90, c)
                    x += 110
                dibujar_texto(pantalla, f"Total dealer: {ui.juego.calcular_mano(ui.dealer)}", 20, 245)

        # Jugador
        dibujar_texto(pantalla, "Jugador (tú):", 20, 280)
        x = 20
        if ui.jugador:
            for c in ui.jugador:
                dibujar_tarjeta(pantalla, x, 310, c)
                x += 110
            dibujar_texto(pantalla, f"Total jugador: {ui.juego.calcular_mano(ui.jugador)}", 20, 465)
        else:
            dibujar_texto(pantalla, "Mano vacía", 20, 310)

        # IA
        dibujar_texto(pantalla, "IA:", 20, 500)
        x = 20
        if ui.ia:
            for c in ui.ia:
                dibujar_tarjeta(pantalla, x, 530, c)
                x += 110
            dibujar_texto(pantalla, f"Total IA: {ui.juego.calcular_mano(ui.ia)}", 20, 685)
        else:
            dibujar_texto(pantalla, "IA no participa en esta ronda", 20, 530)

        # Mensaje resultado
        dibujar_texto(pantalla, "Mensaje: " + (ui.mensaje or "—"), 360, 60, FUENTE)

        # Botones
        dibujar_boton(pantalla, btn_new_h, "Nueva: Humano vs Dealer")
        dibujar_boton(pantalla, btn_new_ai, "IA juega (ver)")
        dibujar_boton(pantalla, btn_duel, "Duelo: Humano vs IA")
        dibujar_boton(pantalla, btn_hit, "Pedir (H)")
        dibujar_boton(pantalla, btn_stand, "Plantarse (S)")
        dibujar_boton(pantalla, btn_advice, "Consejo IA: " + ("ON" if ui.show_ai_recommendation else "OFF"))
        dibujar_boton(pantalla, btn_see_ai, "Evaluar IA 100 partidas")
        dibujar_boton(pantalla, btn_quit, "Salir")

        # Mostrar consejo IA
        if ui.show_ai_recommendation and ui.agent and ui.jugador and not ui.game_over:
            rec = ui.ask_ai_recommendation()
            if rec is not None:
                texto = "IA recomienda: PEDIR" if rec == 1 else "IA recomienda: PLANTARSE"
                dibujar_texto(pantalla, texto, 360, 100, FUENTE, color=(255, 240, 120))


        # Atajos teclado (con retraso)
        keys = pygame.key.get_pressed()
        if keys[pygame.K_h] and not ui.game_over and ui.mode in ("play_human", "duel"):
            ui.player_hit()
            time.sleep(0.2)
        if keys[pygame.K_s] and not ui.game_over and ui.mode in ("play_human", "duel"):
            ui.player_stand()
            time.sleep(0.2)

        pygame.display.flip()
        reloj.tick(FPS)

if __name__ == "__main__":
    main_loop()