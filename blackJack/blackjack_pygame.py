# blackjack_pygame_responsive.py
import pygame
import sys
import time
from blackjack_game import BlackjackGame
from ai_agent import AIAgent

# ---------- Config ----------
FPS = 60
MIN_WIDTH, MIN_HEIGHT = 800, 600
BG_COLOR = (8, 120, 60)   # verde casino
CARD_BG = (250, 250, 250)
CARD_BORDER = (0, 0, 0)
TEXT_COLOR = (20, 20, 20)
BUTTON_COLOR = (230, 230, 230)
BUTTON_BORDER = (10, 10, 10)
BUTTON_HOVER = (200, 200, 200)
RECOMMENDATION_COLOR = (255, 240, 120)

MODEL_PATH = "policy_blackjack.h5"

# ---------- Inicializar Pygame ----------
pygame.init()

# Obtener el tamaño de la pantalla
info = pygame.display.Info()
SCREEN_WIDTH = min(info.current_w - 100, 1400)  # Máximo 1400px
SCREEN_HEIGHT = min(info.current_h - 100, 900)  # Máximo 900px

# Asegurar tamaño mínimo
SCREEN_WIDTH = max(SCREEN_WIDTH, MIN_WIDTH)
SCREEN_HEIGHT = max(SCREEN_HEIGHT, MIN_HEIGHT)

# Variables globales
pantalla = None
reloj = None

def initialize_pygame():
    global pantalla, reloj
    pantalla = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption("Blackjack - Pygame + IA (Responsivo)")
    reloj = pygame.time.Clock()

# Fuentes escalables
def get_scaled_fonts(width):
    base_size = max(16, width // 50)
    title_size = max(20, width // 40)
    return (
        pygame.font.SysFont("Arial", base_size),
        pygame.font.SysFont("Arial", title_size, bold=True)
    )

# ---------- Clase para manejar layout responsivo ----------
class ResponsiveLayout:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.update_layout()
    
    def update_layout(self):
        # Calcular proporciones
        self.margin = max(10, self.width // 80)
        self.card_width = max(70, self.width // 14)
        self.card_height = int(self.card_width * 1.45)
        self.card_spacing = max(5, self.card_width // 10)
        
        # Áreas principales
        self.sidebar_width = max(200, self.width // 4)
        self.game_area_width = self.width - self.sidebar_width - self.margin * 3
        
        # Posiciones de las secciones
        self.dealer_y = self.margin * 3
        self.player_y = self.height // 2 - self.card_height // 2
        self.ai_y = self.height - self.card_height - self.margin * 4
        
        # Sidebar
        self.sidebar_x = self.width - self.sidebar_width - self.margin
        
        # Botones
        self.button_width = self.sidebar_width - self.margin
        self.button_height = max(35, self.height // 18)
        self.button_spacing = max(8, self.height // 80)
        
    def get_card_positions(self, num_cards, y_pos):
        """Calcula posiciones de cartas centradas"""
        total_width = num_cards * self.card_width + (num_cards - 1) * self.card_spacing
        start_x = (self.game_area_width - total_width) // 2 + self.margin
        
        positions = []
        for i in range(num_cards):
            x = start_x + i * (self.card_width + self.card_spacing)
            positions.append((x, y_pos))
        return positions
    
    def get_button_rect(self, index):
        """Calcula rectángulo de botón por índice"""
        y = self.margin + index * (self.button_height + self.button_spacing)
        return pygame.Rect(self.sidebar_x, y, self.button_width, self.button_height)

# ---------- Funciones auxiliares mejoradas ----------
class UIManager:
    def __init__(self, screen, layout):
        self.screen = screen
        self.layout = layout
        self.font, self.title_font = get_scaled_fonts(screen.get_width())
        self.hovered_button = -1
        
    def update_fonts(self):
        self.font, self.title_font = get_scaled_fonts(self.screen.get_width())
    
    def draw_text(self, text, x, y, font=None, color=(255,255,255), center=False):
        if font is None:
            font = self.font
        txt = font.render(text, True, color)
        if center:
            x = x - txt.get_width() // 2
        self.screen.blit(txt, (x, y))
        return txt.get_rect(x=x, y=y)

    def draw_card(self, x, y, carta=None):
        if carta is None:
            # Dibujar el reverso de la carta
            if hasattr(GameUI.instance, 'juego') and hasattr(GameUI.instance.juego, 'reverso_img'):
                img = pygame.transform.scale(GameUI.instance.juego.reverso_img, 
                                           (self.layout.card_width, self.layout.card_height))
                self.screen.blit(img, (x, y))
            else:
                # Fallback con patrón para el reverso
                pygame.draw.rect(self.screen, (40, 120, 200), 
                               (x, y, self.layout.card_width, self.layout.card_height), 
                               border_radius=8)
                # Patrón de líneas para simular reverso
                for i in range(5):
                    pygame.draw.line(self.screen, (20, 80, 160), 
                                   (x + i*15, y), (x + i*15, y + self.layout.card_height), 2)
        else:
            # Obtener imagen de carta del caché
            if hasattr(GameUI.instance, 'juego'):
                imagen = GameUI.instance.juego.imagenes_cache.get(carta)
                if imagen:
                    img = pygame.transform.scale(imagen, (self.layout.card_width, self.layout.card_height))
                    self.screen.blit(img, (x, y))
                    return
            
            # Fallback con texto
            pygame.draw.rect(self.screen, CARD_BG, 
                           (x, y, self.layout.card_width, self.layout.card_height), 
                           border_radius=8)
            pygame.draw.rect(self.screen, CARD_BORDER, 
                           (x, y, self.layout.card_width, self.layout.card_height), 
                           3, border_radius=8)
            
            texto = self.carta_a_texto(carta)
            # Usar fuente más pequeña para las cartas
            card_font = pygame.font.SysFont("Arial", max(12, self.layout.card_width // 6))
            txt = card_font.render(texto, True, TEXT_COLOR)
            
            # Centrar texto en la carta
            text_x = x + (self.layout.card_width - txt.get_width()) // 2
            text_y = y + (self.layout.card_height - txt.get_height()) // 2
            self.screen.blit(txt, (text_x, text_y))

    def draw_button(self, rect, texto, index, enabled=True):
        # Determinar color del botón
        color = BUTTON_COLOR
        if not enabled:
            color = (180, 180, 180)
        elif self.hovered_button == index:
            color = BUTTON_HOVER
            
        pygame.draw.rect(self.screen, color, rect, border_radius=8)
        pygame.draw.rect(self.screen, BUTTON_BORDER, rect, 2, border_radius=8)
        
        # Texto del botón
        text_color = TEXT_COLOR if enabled else (100, 100, 100)
        # Usar fuente más pequeña para botones si es necesario
        button_font = self.font
        if button_font.size(texto)[0] > rect.width - 10:
            button_font = pygame.font.SysFont("Arial", max(10, self.font.get_height() - 4))
            
        txt = button_font.render(texto, True, text_color)
        tx = rect.centerx - txt.get_width() // 2
        ty = rect.centery - txt.get_height() // 2
        self.screen.blit(txt, (tx, ty))
        
        return rect

    def carta_a_texto(self, carta):
        valor, palo = carta
        nombres = {'A':'A', 'J':'J', 'Q':'Q', 'K':'K'}
        v_texto = nombres.get(valor, str(valor))
        simbolos = {"Corazones":"♥", "Diamantes":"♦", "Trebol":"♣", "Copas":"♠"}
        p_texto = simbolos.get(palo, palo)
        return f"{v_texto}{p_texto}"

    def update_hover(self, mouse_pos, button_rects):
        self.hovered_button = -1
        for i, rect in enumerate(button_rects):
            if rect.collidepoint(mouse_pos):
                self.hovered_button = i
                break

# ---------- Clase principal del juego UI mejorada ----------
class GameUI:
    instance = None
    
    def __init__(self, screen):
        GameUI.instance = self
        self.screen = screen
        self.layout = ResponsiveLayout(screen.get_width(), screen.get_height())
        self.ui_manager = UIManager(screen, self.layout)
        self.juego = BlackjackGame()
        self.reset_all()
        
        # Botones
        self.buttons = [
            ("Nueva: Humano vs Dealer", self.start_human_game),
            ("IA juega (observar)", self.start_ai_game),
            ("Duelo: Humano vs IA", self.start_duel_game),
            ("Pedir Carta (H)", self.player_hit),
            ("Plantarse (S)", self.player_stand),
            ("Consejo IA", self.toggle_advice),
            ("Evaluar IA (100 rondas)", self.evaluate_ai),
            ("Salir", self.quit_game)
        ]
        
        # Intentamos cargar agente IA
        self.agent = None
        try:
            self.agent = AIAgent(MODEL_PATH)
            print("Agente cargado:", MODEL_PATH)
        except Exception as e:
            print("No se pudo cargar agente:", e)
            self.agent = None

    def handle_resize(self, new_size):
        self.layout = ResponsiveLayout(new_size[0], new_size[1])
        self.ui_manager = UIManager(self.screen, self.layout)
        self.ui_manager.update_fonts()

    def reset_all(self):
        self.juego.reset_game()
        self.baraja = self.juego.baraja
        self.jugador = self.juego.player_cards
        self.dealer = self.juego.dealer_cards
        self.ia = []
        self.mensaje = "Bienvenido al Blackjack"
        self.mode = "menu"
        self.game_over = True
        self.show_ai_recommendation = False
        self.player_turn = False

    # Métodos de botones
    def start_human_game(self):
        self.start_new_round("play_human")
        
    def start_ai_game(self):
        self.start_new_round("play_ai")
        if not self.ia:
            self.ia = self.jugador.copy()
            self.jugador.clear()
        self.ia_play(greedy=True)
        
    def start_duel_game(self):
        self.start_new_round("duel")
        
    def toggle_advice(self):
        self.show_ai_recommendation = not self.show_ai_recommendation
        
    def evaluate_ai(self):
        if self.agent is not None:
            wins = ties = losses = 0
            rounds = 100
            for _ in range(rounds):
                self.juego.reset_game()
                jugador = []
                dealer = []
                for _ in range(2):
                    c, _ = self.juego.repartir_carta()
                    jugador.append(c)
                for _ in range(2):
                    c, _ = self.juego.repartir_carta()
                    dealer.append(c)
                ia_hand = jugador.copy()
                while self.juego.calcular_mano(ia_hand) < 17:
                    c, _ = self.juego.repartir_carta()
                    ia_hand.append(c)
                while self.juego.calcular_mano(dealer) < 17:
                    c, _ = self.juego.repartir_carta()
                    dealer.append(c)
                if self.juego.calcular_mano(ia_hand) > 21:
                    losses += 1
                elif self.juego.calcular_mano(dealer) > 21 or self.juego.calcular_mano(ia_hand) > self.juego.calcular_mano(dealer):
                    wins += 1
                elif self.juego.calcular_mano(ia_hand) == self.juego.calcular_mano(dealer):
                    ties += 1
                else:
                    losses += 1
            self.mensaje = f"IA evaluada en {rounds} partidas → Victorias:{wins} Empates:{ties} Derrotas:{losses}"
        else:
            self.mensaje = "No hay modelo IA disponible"
            
    def quit_game(self):
        pygame.quit()
        sys.exit()

    def start_new_round(self, mode):
        self.juego.reset_game()
        self.jugador.clear()
        self.dealer.clear()
        self.ia.clear()
        
        # Repartir 2 cartas iniciales
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
        
        self.mensaje = f"Nueva ronda iniciada - Modo: {mode}"
        self.mode = mode
        self.player_turn = True
        self.game_over = False

    def player_hit(self):
        if self.game_over or not self.player_turn or self.mode not in ("play_human", "duel"):
            return
        c, _ = self.juego.repartir_carta()
        self.jugador.append(c)
        if self.juego.calcular_mano(self.jugador) > 21:
            self.mensaje = "¡Te pasaste! (Jugador se quema)"
            self.player_turn = False
            self.resolve_round()

    def player_stand(self):
        if self.game_over or not self.player_turn:
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
                # Estrategia básica simple
                if puntaje < 17:
                    c, _ = self.juego.repartir_carta()
                    self.ia.append(c)
                    if self.juego.calcular_mano(self.ia) > 21:
                        break
                else:
                    break
            else:
                accion = self.agent.action(estado, greedy=greedy)
                if accion == 1:  # Hit
                    c, _ = self.juego.repartir_carta()
                    self.ia.append(c)
                    if self.juego.calcular_mano(self.ia) > 21:
                        break
                else:  # Stand
                    break
        self.resolve_round()

    def resolve_round(self):
        # Dealer juega
        while self.juego.calcular_mano(self.dealer) < 17:
            c, _ = self.juego.repartir_carta()
            self.dealer.append(c)

        puntaje_jugador = self.juego.calcular_mano(self.jugador)
        puntaje_dealer = self.juego.calcular_mano(self.dealer)
        puntaje_ia = self.juego.calcular_mano(self.ia) if self.ia else None

        resultados = []
        
        # Evaluar jugador
        if puntaje_jugador > 21:
            resultados.append("Jugador: Pierde (se quemó)")
        elif puntaje_dealer > 21:
            resultados.append("Jugador: Gana (dealer se quemó)")
        elif puntaje_jugador > puntaje_dealer:
            resultados.append("Jugador: Gana")
        elif puntaje_jugador == puntaje_dealer:
            resultados.append("Jugador: Empate")
        else:
            resultados.append("Jugador: Pierde")

        # Evaluar IA si participa
        if self.ia:
            if puntaje_ia > 21:
                resultados.append("IA: Pierde (se quemó)")
            elif puntaje_dealer > 21:
                resultados.append("IA: Gana (dealer se quemó)")
            elif puntaje_ia > puntaje_dealer:
                resultados.append("IA: Gana")
            elif puntaje_ia == puntaje_dealer:
                resultados.append("IA: Empate")
            else:
                resultados.append("IA: Pierde")

        self.mensaje = " | ".join(resultados)
        self.game_over = True

    def ask_ai_recommendation(self):
        if self.agent is None or self.game_over or not self.jugador:
            return None
        estado = (
            self.juego.calcular_mano(self.jugador),
            self.juego.valor_carta(self.dealer[0]) if self.dealer else 10,
            any(c[0] == 'A' for c in self.jugador) and self.juego.calcular_mano(self.jugador) <= 21
        )
        return self.agent.action(estado, greedy=True)

    def draw(self):
        self.screen.fill(BG_COLOR)
        
        # Título
        title_rect = self.ui_manager.draw_text(
            "♠ BLACKJACK RESPONSIVO ♠", 
            self.layout.width // 2, 
            self.layout.margin, 
            self.ui_manager.title_font, 
            (255, 215, 0), 
            center=True
        )
        
        # Información del juego
        info_y = title_rect.bottom + self.layout.margin
        self.ui_manager.draw_text(f"Mensaje: {self.mensaje}", self.layout.margin, info_y)
        
        # Dibujar cartas del dealer
        dealer_label_y = self.layout.dealer_y
        self.ui_manager.draw_text("🎩 DEALER:", self.layout.margin, dealer_label_y)
        
        if self.dealer:
            positions = self.layout.get_card_positions(len(self.dealer), dealer_label_y + 30)
            if not self.game_over and self.mode in ("play_human", "duel"):
                # Mostrar solo primera carta del dealer
                self.ui_manager.draw_card(positions[0][0], positions[0][1], self.dealer[0])
                if len(positions) > 1:
                    self.ui_manager.draw_card(positions[1][0], positions[1][1])  # Carta oculta
                self.ui_manager.draw_text("Total dealer: ??", self.layout.margin, positions[0][1] + self.layout.card_height + 10)
            else:
                # Mostrar todas las cartas
                for i, (x, y) in enumerate(positions):
                    if i < len(self.dealer):
                        self.ui_manager.draw_card(x, y, self.dealer[i])
                total_dealer = self.juego.calcular_mano(self.dealer)
                self.ui_manager.draw_text(f"Total dealer: {total_dealer}", self.layout.margin, positions[0][1] + self.layout.card_height + 10)
        
        # Dibujar cartas del jugador
        player_label_y = self.layout.player_y
        self.ui_manager.draw_text("👤 JUGADOR:", self.layout.margin, player_label_y)
        
        if self.jugador:
            positions = self.layout.get_card_positions(len(self.jugador), player_label_y + 30)
            for i, (x, y) in enumerate(positions):
                if i < len(self.jugador):
                    self.ui_manager.draw_card(x, y, self.jugador[i])
            total_jugador = self.juego.calcular_mano(self.jugador)
            self.ui_manager.draw_text(f"Total jugador: {total_jugador}", self.layout.margin, positions[0][1] + self.layout.card_height + 10)
        else:
            self.ui_manager.draw_text("Sin cartas", self.layout.margin, player_label_y + 30)
        
        # Dibujar cartas de la IA
        ai_label_y = self.layout.ai_y
        self.ui_manager.draw_text("🤖 IA:", self.layout.margin, ai_label_y)
        
        if self.ia:
            positions = self.layout.get_card_positions(len(self.ia), ai_label_y + 30)
            for i, (x, y) in enumerate(positions):
                if i < len(self.ia):
                    self.ui_manager.draw_card(x, y, self.ia[i])
            total_ia = self.juego.calcular_mano(self.ia)
            self.ui_manager.draw_text(f"Total IA: {total_ia}", self.layout.margin, positions[0][1] + self.layout.card_height + 10)
        else:
            self.ui_manager.draw_text("IA no participa", self.layout.margin, ai_label_y + 30)
        
        # Dibujar botones
        button_rects = []
        for i, (texto, _) in enumerate(self.buttons):
            rect = self.layout.get_button_rect(i)
            button_rects.append(rect)
            
            # Determinar si el botón está habilitado
            enabled = True
            if i == 3 or i == 4:  # Hit/Stand
                enabled = not self.game_over and self.player_turn and self.mode in ("play_human", "duel")
            elif i == 5:  # Consejo IA
                texto = f"Consejo IA: {'ON' if self.show_ai_recommendation else 'OFF'}"
                
            self.ui_manager.draw_button(rect, texto, i, enabled)
        
        # Mostrar consejo de IA
        if (self.show_ai_recommendation and self.agent and self.jugador and 
            not self.game_over and self.player_turn):
            rec = self.ask_ai_recommendation()
            if rec is not None:
                consejo = "🎯 IA recomienda: PEDIR CARTA" if rec == 1 else "🎯 IA recomienda: PLANTARSE"
                # Mostrar en una posición destacada
                advice_y = info_y + 30
                self.ui_manager.draw_text(consejo, self.layout.margin, advice_y, 
                                        color=RECOMMENDATION_COLOR)
        
        return button_rects

# ---------- Loop principal mejorado ----------
def main_loop():
    global pantalla
    ui = GameUI(pantalla)
    last_time = time.time()
    
    while True:
        current_time = time.time()
        dt = current_time - last_time
        last_time = current_time
        
        mouse_pos = pygame.mouse.get_pos()
        
        for evt in pygame.event.get():
            if evt.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                
            elif evt.type == pygame.VIDEORESIZE:
                new_size = (max(evt.w, MIN_WIDTH), max(evt.h, MIN_HEIGHT))
                pantalla = pygame.display.set_mode(new_size, pygame.RESIZABLE)
                ui.screen = pantalla
                ui.handle_resize(new_size)
                
            elif evt.type == pygame.MOUSEBUTTONDOWN and evt.button == 1:
                button_rects = ui.draw()  # Obtener posiciones actuales
                for i, rect in enumerate(button_rects):
                    if rect.collidepoint(mouse_pos):
                        _, callback = ui.buttons[i]
                        callback()
                        break
                        
            elif evt.type == pygame.KEYDOWN:
                if evt.key == pygame.K_h and not ui.game_over and ui.player_turn:
                    ui.player_hit()
                elif evt.key == pygame.K_s and not ui.game_over and ui.player_turn:
                    ui.player_stand()
        
        # Dibujar todo
        button_rects = ui.draw()
        ui.ui_manager.update_hover(mouse_pos, button_rects)
        
        pygame.display.flip()
        reloj.tick(FPS)

if __name__ == "__main__":
    initialize_pygame()
    main_loop()