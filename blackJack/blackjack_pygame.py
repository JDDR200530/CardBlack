# blackjack_pygame_casino_style.py
import pygame
import sys
import time
import math
from blackjack_game import BlackjackGame
from ai_agent import AIAgent

# ---------- Config Mejorado ----------
FPS = 60
MIN_WIDTH, MIN_HEIGHT = 1000, 700

# Colores estilo casino elegante
BG_COLOR = (0, 50, 25)  # Verde casino más oscuro
FELT_COLOR = (15, 85, 45)  # Verde fieltro
GOLD_COLOR = (255, 215, 0)
SILVER_COLOR = (192, 192, 192)
WOOD_COLOR = (101, 67, 33)
CARD_BG = (255, 255, 255)
CARD_SHADOW = (0, 0, 0, 50)
TEXT_LIGHT = (255, 255, 255)
TEXT_GOLD = (255, 215, 0)
TEXT_RED = (255, 100, 100)
TEXT_GREEN = (100, 255, 100)

# Botones estilo casino
BUTTON_PRIMARY = (180, 30, 30)  # Rojo casino
BUTTON_PRIMARY_HOVER = (220, 40, 40)
BUTTON_SECONDARY = (30, 100, 180)  # Azul elegante
BUTTON_SECONDARY_HOVER = (40, 120, 220)
BUTTON_SUCCESS = (50, 150, 50)  # Verde éxito
BUTTON_SUCCESS_HOVER = (70, 170, 70)
BUTTON_DISABLED = (60, 60, 60)
BUTTON_BORDER = (255, 215, 0)  # Bordes dorados

MODEL_PATH = "policy_blackjack.h5"

# ---------- Inicializar Pygame ----------
pygame.init()

# Obtener el tamaño de la pantalla
info = pygame.display.Info()
SCREEN_WIDTH = min(info.current_w - 50, 1600)
SCREEN_HEIGHT = min(info.current_h - 50, 1000)

# Asegurar tamaño mínimo
SCREEN_WIDTH = max(SCREEN_WIDTH, MIN_WIDTH)
SCREEN_HEIGHT = max(SCREEN_HEIGHT, MIN_HEIGHT)

# Variables globales
pantalla = None
reloj = None

def initialize_pygame():
    global pantalla, reloj
    pantalla = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption("🎰 Casino Blackjack - Premium Edition")
    reloj = pygame.time.Clock()

# Fuentes más elegantes
def get_scaled_fonts(width):
    base_size = max(18, width // 45)
    title_size = max(28, width // 35)
    subtitle_size = max(22, width // 40)
    small_size = max(14, width // 60)
    return {
        'base': pygame.font.SysFont("Georgia", base_size),
        'title': pygame.font.SysFont("Georgia", title_size, bold=True),
        'subtitle': pygame.font.SysFont("Georgia", subtitle_size, bold=True),
        'small': pygame.font.SysFont("Arial", small_size),
        'card': pygame.font.SysFont("Arial", max(16, width // 50), bold=True)
    }

# ---------- Clase para efectos visuales ----------
class VisualEffects:
    @staticmethod
    def draw_gradient_rect(surface, color1, color2, rect, vertical=True):
        """Dibuja un rectángulo con gradiente"""
        if vertical:
            for y in range(rect.height):
                ratio = y / rect.height
                r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
                g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
                b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
                pygame.draw.line(surface, (r, g, b), 
                               (rect.x, rect.y + y), (rect.x + rect.width, rect.y + y))
        else:
            for x in range(rect.width):
                ratio = x / rect.width
                r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
                g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
                b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
                pygame.draw.line(surface, (r, g, b), 
                               (rect.x + x, rect.y), (rect.x + x, rect.y + rect.height))

    @staticmethod
    def draw_card_shadow(surface, x, y, width, height, offset=5):
        """Dibuja sombra para las cartas"""
        shadow_surf = pygame.Surface((width, height), pygame.SRCALPHA)
        shadow_surf.fill((0, 0, 0, 80))
        surface.blit(shadow_surf, (x + offset, y + offset))

    @staticmethod
    def draw_casino_border(surface, rect, width=3):
        """Dibuja borde estilo casino con efecto dorado"""
        # Borde exterior dorado
        pygame.draw.rect(surface, GOLD_COLOR, rect, width)
        # Borde interior más oscuro
        inner_rect = pygame.Rect(rect.x + width, rect.y + width, 
                                rect.width - 2*width, rect.height - 2*width)
        pygame.draw.rect(surface, WOOD_COLOR, inner_rect, max(1, width//2))

# ---------- Layout responsivo mejorado ----------
class CasinoLayout:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.update_layout()
    
    def update_layout(self):
        # Márgenes más generosos
        self.margin = max(20, self.width // 50)
        self.padding = max(15, self.width // 60)
        
        # Mesa de juego (área principal)
        self.table_margin = self.margin * 2
        self.table_rect = pygame.Rect(
            self.table_margin, 
            self.table_margin * 3, 
            self.width - self.table_margin * 2, 
            self.height - self.table_margin * 5
        )
        
        # Cartas más grandes y elegantes
        self.card_width = max(90, self.width // 12)
        self.card_height = int(self.card_width * 1.4)
        self.card_spacing = max(10, self.card_width // 8)
        
        # Áreas de juego
        self.dealer_area = pygame.Rect(
            self.table_rect.x + self.padding,
            self.table_rect.y + self.padding,
            self.table_rect.width - 2 * self.padding,
            self.table_rect.height // 3
        )
        
        self.player_area = pygame.Rect(
            self.table_rect.x + self.padding,
            self.table_rect.y + self.table_rect.height * 2//3,
            self.table_rect.width - 2 * self.padding,
            self.table_rect.height // 3
        )
        
        self.ai_area = pygame.Rect(
            self.table_rect.x + self.padding,
            self.table_rect.y + self.table_rect.height // 3 + self.padding,
            self.table_rect.width - 2 * self.padding,
            self.table_rect.height // 3 - 2 * self.padding
        )
        
        # Panel de control (lateral derecho)
        self.control_panel_width = max(280, self.width // 5)
        self.control_panel = pygame.Rect(
            self.width - self.control_panel_width - self.margin,
            self.margin,
            self.control_panel_width,
            self.height - 2 * self.margin
        )
        
        # Ajustar mesa para dejar espacio al panel
        self.table_rect.width = self.width - self.control_panel_width - self.table_margin * 3
        
        # Botones en el panel de control
        self.button_width = self.control_panel_width - 2 * self.padding
        self.button_height = max(50, self.height // 15)
        self.button_spacing = max(12, self.height // 60)
        
        # Área de información
        self.info_area = pygame.Rect(
            self.margin,
            self.margin,
            self.table_rect.width,
            self.table_margin * 2
        )
        
    def get_card_positions_centered(self, num_cards, area_rect):
        """Calcula posiciones de cartas centradas en un área"""
        if num_cards == 0:
            return []
            
        total_width = num_cards * self.card_width + (num_cards - 1) * self.card_spacing
        start_x = area_rect.centerx - total_width // 2
        card_y = area_rect.centery - self.card_height // 2
        
        positions = []
        for i in range(num_cards):
            x = start_x + i * (self.card_width + self.card_spacing)
            positions.append((x, card_y))
        return positions
    
    def get_button_rect(self, index):
        """Calcula rectángulo de botón en el panel de control"""
        y = (self.control_panel.y + self.padding + 
             index * (self.button_height + self.button_spacing))
        return pygame.Rect(
            self.control_panel.x + self.padding,
            y,
            self.button_width,
            self.button_height
        )

# ---------- UI Manager mejorado ----------
class CasinoUIManager:
    def __init__(self, screen, layout):
        self.screen = screen
        self.layout = layout
        self.fonts = get_scaled_fonts(screen.get_width())
        self.hovered_button = -1
        self.effects = VisualEffects()
        
    def update_fonts(self):
        self.fonts = get_scaled_fonts(self.screen.get_width())
    
    def draw_background(self):
        """Dibuja el fondo estilo casino"""
        # Fondo base
        self.screen.fill(BG_COLOR)
        
        # Mesa de fieltro con gradiente
        felt_light = (20, 100, 50)
        felt_dark = (10, 70, 35)
        self.effects.draw_gradient_rect(
            self.screen, felt_light, felt_dark, self.layout.table_rect
        )
        
        # Borde de la mesa
        self.effects.draw_casino_border(self.screen, self.layout.table_rect, 5)
        
        # Panel de control con gradiente
        panel_light = (40, 40, 40)
        panel_dark = (20, 20, 20)
        self.effects.draw_gradient_rect(
            self.screen, panel_light, panel_dark, self.layout.control_panel
        )
        self.effects.draw_casino_border(self.screen, self.layout.control_panel, 3)
    
    def draw_text(self, text, x, y, font_key='base', color=TEXT_LIGHT, center=False, shadow=False):
        """Dibuja texto con opciones mejoradas"""
        font = self.fonts.get(font_key, self.fonts['base'])
        
        if shadow:
            # Sombra del texto
            shadow_surf = font.render(text, True, (0, 0, 0))
            shadow_x = x + 2 if not center else x - shadow_surf.get_width() // 2 + 2
            shadow_y = y + 2
            self.screen.blit(shadow_surf, (shadow_x, shadow_y))
        
        # Texto principal
        txt = font.render(text, True, color)
        if center:
            x = x - txt.get_width() // 2
        self.screen.blit(txt, (x, y))
        return txt.get_rect(x=x, y=y)

    def draw_card(self, x, y, carta=None, hidden=False):
        """Dibuja carta con efectos mejorados"""
        # Sombra de la carta
        self.effects.draw_card_shadow(self.screen, x, y, 
                                    self.layout.card_width, self.layout.card_height)
        
        if carta is None or hidden:
            # Reverso de carta con patrón elegante
            card_rect = pygame.Rect(x, y, self.layout.card_width, self.layout.card_height)
            
            # Fondo del reverso
            back_color1 = (120, 30, 30)
            back_color2 = (80, 20, 20)
            self.effects.draw_gradient_rect(self.screen, back_color1, back_color2, card_rect)
            
            # Borde dorado
            pygame.draw.rect(self.screen, GOLD_COLOR, card_rect, 3, border_radius=12)
            
            # Patrón decorativo
            center_x, center_y = card_rect.center
            for i in range(3):
                for j in range(4):
                    dot_x = center_x - 20 + i * 20
                    dot_y = center_y - 30 + j * 20
                    pygame.draw.circle(self.screen, GOLD_COLOR, (dot_x, dot_y), 3)
        else:
            # Carta visible
            card_rect = pygame.Rect(x, y, self.layout.card_width, self.layout.card_height)
            
            # Fondo blanco con gradiente sutil
            white_light = (255, 255, 255)
            white_shadow = (245, 245, 245)
            self.effects.draw_gradient_rect(self.screen, white_light, white_shadow, card_rect)
            
            # Borde
            pygame.draw.rect(self.screen, (200, 200, 200), card_rect, 2, border_radius=12)
            
            # Obtener imagen de cache si existe
            if hasattr(GameUI.instance, 'juego'):
                imagen = GameUI.instance.juego.imagenes_cache.get(carta)
                if imagen:
                    img = pygame.transform.scale(imagen, 
                                               (self.layout.card_width-4, self.layout.card_height-4))
                    self.screen.blit(img, (x+2, y+2))
                    return
            
            # Fallback: dibujar carta con texto
            valor, palo = carta
            texto = self.carta_a_texto_elegante(carta)
            
            # Color del palo
            color_carta = (220, 20, 20) if palo in ['Corazones', 'Diamantes'] else (20, 20, 20)
            
            # Texto principal (centro)
            font = self.fonts['card']
            txt = font.render(texto, True, color_carta)
            text_x = x + (self.layout.card_width - txt.get_width()) // 2
            text_y = y + (self.layout.card_height - txt.get_height()) // 2
            self.screen.blit(txt, (text_x, text_y))
            
            # Valores en las esquinas
            small_font = self.fonts['small']
            corner_txt = small_font.render(texto, True, color_carta)
            
            # Esquina superior izquierda
            self.screen.blit(corner_txt, (x + 8, y + 8))
            
            # Esquina inferior derecha (rotado)
            rotated = pygame.transform.rotate(corner_txt, 180)
            rot_x = x + self.layout.card_width - rotated.get_width() - 8
            rot_y = y + self.layout.card_height - rotated.get_height() - 8
            self.screen.blit(rotated, (rot_x, rot_y))

    def draw_elegant_button(self, rect, texto, button_type='primary', enabled=True, hovered=False):
        """Dibuja botón con estilo casino elegante"""
        # Colores según tipo
        if not enabled:
            base_color = BUTTON_DISABLED
            hover_color = BUTTON_DISABLED
            text_color = (120, 120, 120)
        elif button_type == 'primary':
            base_color = BUTTON_PRIMARY
            hover_color = BUTTON_PRIMARY_HOVER
            text_color = TEXT_LIGHT
        elif button_type == 'secondary':
            base_color = BUTTON_SECONDARY
            hover_color = BUTTON_SECONDARY_HOVER
            text_color = TEXT_LIGHT
        elif button_type == 'success':
            base_color = BUTTON_SUCCESS
            hover_color = BUTTON_SUCCESS_HOVER
            text_color = TEXT_LIGHT
        else:
            base_color = BUTTON_PRIMARY
            hover_color = BUTTON_PRIMARY_HOVER
            text_color = TEXT_LIGHT
        
        # Color final
        color = hover_color if (hovered and enabled) else base_color
        
        # Gradiente del botón
        gradient_light = tuple(min(255, c + 30) for c in color)
        self.effects.draw_gradient_rect(self.screen, gradient_light, color, rect)
        
        # Borde dorado
        border_color = BUTTON_BORDER if enabled else (100, 100, 100)
        pygame.draw.rect(self.screen, border_color, rect, 2, border_radius=8)
        
        # Efecto de profundidad
        if hovered and enabled:
            inner_rect = pygame.Rect(rect.x + 2, rect.y + 2, rect.width - 4, rect.height - 4)
            pygame.draw.rect(self.screen, (255, 255, 255, 30), inner_rect, 1, border_radius=6)
        
        # Texto del botón con sombra
        font = self.fonts['base']
        # Ajustar fuente si el texto es muy largo
        if font.size(texto)[0] > rect.width - 20:
            font = self.fonts['small']
            
        # Sombra del texto
        shadow_txt = font.render(texto, True, (0, 0, 0))
        shadow_x = rect.centerx - shadow_txt.get_width() // 2 + 1
        shadow_y = rect.centery - shadow_txt.get_height() // 2 + 1
        self.screen.blit(shadow_txt, (shadow_x, shadow_y))
        
        # Texto principal
        txt = font.render(texto, True, text_color)
        tx = rect.centerx - txt.get_width() // 2
        ty = rect.centery - txt.get_height() // 2
        self.screen.blit(txt, (tx, ty))
        
        return rect

    def carta_a_texto_elegante(self, carta):
        """Convierte carta a texto con símbolos Unicode elegantes"""
        valor, palo = carta
        nombres = {'A': 'A', 'J': 'J', 'Q': 'Q', 'K': 'K'}
        v_texto = nombres.get(valor, str(valor))
        
        # Símbolos Unicode más elegantes
        simbolos = {
            "Corazones": "♥",
            "Diamantes": "♦", 
            "Trebol": "♣",
            "Copas": "♠"
        }
        p_texto = simbolos.get(palo, palo[0])
        
        return f"{v_texto}\n{p_texto}"

    def update_hover(self, mouse_pos, button_rects):
        """Actualiza estado hover de botones"""
        self.hovered_button = -1
        for i, rect in enumerate(button_rects):
            if rect.collidepoint(mouse_pos):
                self.hovered_button = i
                break

# ---------- Clase principal mejorada ----------
class GameUI:
    instance = None
    
    def __init__(self, screen):
        GameUI.instance = self
        self.screen = screen
        self.layout = CasinoLayout(screen.get_width(), screen.get_height())
        self.ui_manager = CasinoUIManager(screen, self.layout)
        self.juego = BlackjackGame()
        self.reset_all()
        
        # Botones reorganizados y categorizados
        self.buttons = [
            ("🎮 Nueva Partida", self.start_human_game, 'primary'),
            ("🤖 IA vs Dealer", self.start_ai_game, 'secondary'),
            ("⚔️ Duelo H vs IA", self.start_duel_game, 'secondary'),
            ("", None, None),  # Separador
            ("🃏 Pedir Carta [H]", self.player_hit, 'success'),
            ("✋ Plantarse [S]", self.player_stand, 'primary'),
            ("💡 Consejo IA", self.toggle_advice, 'secondary'),
            ("", None, None),  # Separador
            ("📊 Evaluar IA", self.evaluate_ai, 'secondary'),
            ("🚪 Salir", self.quit_game, 'primary')
        ]
        
        # Cargar agente IA
        self.agent = None
        try:
            self.agent = AIAgent(MODEL_PATH)
            print("🤖 Agente IA cargado exitosamente")
        except Exception as e:
            print(f"❌ Error cargando agente: {e}")

    def handle_resize(self, new_size):
        """Maneja el redimensionamiento de ventana"""
        self.layout = CasinoLayout(new_size[0], new_size[1])
        self.ui_manager = CasinoUIManager(self.screen, self.layout)
        self.ui_manager.update_fonts()

    def reset_all(self):
        """Resetea el estado del juego"""
        self.juego.reset_game()
        self.baraja = self.juego.baraja
        self.jugador = self.juego.player_cards
        self.dealer = self.juego.dealer_cards
        self.ia = []
        self.mensaje = "🎰 Bienvenido al Casino Blackjack Premium"
        self.mode = "menu"
        self.game_over = True
        self.show_ai_recommendation = False
        self.player_turn = False

    # Métodos de botones (sin cambios en lógica)
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
            self.mensaje = f"📈 IA evaluada: {wins}W-{ties}T-{losses}L de {rounds} partidas"
        else:
            self.mensaje = "❌ No hay modelo IA disponible"
            
    def quit_game(self):
        pygame.quit()
        sys.exit()

    def start_new_round(self, mode):
        """Inicia nueva ronda"""
        self.juego.reset_game()
        self.jugador.clear()
        self.dealer.clear()
        self.ia.clear()
        
        # Repartir cartas iniciales
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
        
        mode_names = {
            "play_human": "🎮 Humano vs Dealer",
            "play_ai": "🤖 IA vs Dealer", 
            "duel": "⚔️ Duelo Humano vs IA"
        }
        self.mensaje = f"🎯 {mode_names.get(mode, mode)} - ¡Buena suerte!"
        self.mode = mode
        self.player_turn = True
        self.game_over = False

    def player_hit(self):
        """Jugador pide carta"""
        if self.game_over or not self.player_turn or self.mode not in ("play_human", "duel"):
            return
        c, _ = self.juego.repartir_carta()
        self.jugador.append(c)
        if self.juego.calcular_mano(self.jugador) > 21:
            self.mensaje = "💥 ¡Te pasaste! Jugador eliminado"
            self.player_turn = False
            self.resolve_round()

    def player_stand(self):
        """Jugador se planta"""
        if self.game_over or not self.player_turn:
            return
        self.player_turn = False
        if self.mode == "duel":
            self.ia_play()
        else:
            self.resolve_round()

    def ia_play(self, greedy=True):
        """IA juega su turno"""
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
                # Estrategia básica
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
        """Resuelve la ronda"""
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
            resultados.append("👤 Jugador: 💥 Eliminado")
        elif puntaje_dealer > 21:
            resultados.append("👤 Jugador: 🎉 Victoria")
        elif puntaje_jugador > puntaje_dealer:
            resultados.append("👤 Jugador: 🎉 Victoria")
        elif puntaje_jugador == puntaje_dealer:
            resultados.append("👤 Jugador: 🤝 Empate")
        else:
            resultados.append("👤 Jugador: 😞 Derrota")

        # Evaluar IA
        if self.ia:
            if puntaje_ia > 21:
                resultados.append("🤖 IA: 💥 Eliminada")
            elif puntaje_dealer > 21:
                resultados.append("🤖 IA: 🎉 Victoria")
            elif puntaje_ia > puntaje_dealer:
                resultados.append("🤖 IA: 🎉 Victoria")
            elif puntaje_ia == puntaje_dealer:
                resultados.append("🤖 IA: 🤝 Empate")
            else:
                resultados.append("🤖 IA: 😞 Derrota")

        self.mensaje = " | ".join(resultados)
        self.game_over = True

    def ask_ai_recommendation(self):
        """Obtiene recomendación de la IA"""
        if self.agent is None or self.game_over or not self.jugador:
            return None
        estado = (
            self.juego.calcular_mano(self.jugador),
            self.juego.valor_carta(self.dealer[0]) if self.dealer else 10,
            any(c[0] == 'A' for c in self.jugador) and self.juego.calcular_mano(self.jugador) <= 21
        )
        return self.agent.action(estado, greedy=True)

    def draw(self):
        """Dibuja toda la interfaz"""
        # Fondo elegante
        self.ui_manager.draw_background()
        
        # Título principal
        title_y = self.layout.margin
        self.ui_manager.draw_text(
            "♠ CASINO BLACKJACK PREMIUM ♠", 
            self.layout.width // 2, 
            title_y, 
            'title', 
            TEXT_GOLD, 
            center=True, 
            shadow=True
        )
        
        # Información del juego en el área de info
        info_y = self.layout.info_area.y + self.layout.padding
        mensaje_rect = self.ui_manager.draw_text(
            self.mensaje, 
            self.layout.info_area.x + self.layout.padding, 
            info_y, 
            'subtitle', 
            TEXT_LIGHT,
            shadow=True
        )
        
        # Consejo de IA si está activo
        if (self.show_ai_recommendation and self.agent and self.jugador and 
            not self.game_over and self.player_turn):
            rec = self.ask_ai_recommendation()
            if rec is not None:
                consejo = "💡 IA recomienda: 🃏 PEDIR CARTA" if rec == 1 else "💡 IA recomienda: ✋ PLANTARSE"
                advice_y = mensaje_rect.bottom + self.layout.padding
                # Fondo destacado para el consejo
                advice_bg = pygame.Rect(
                    self.layout.info_area.x + self.layout.padding - 10,
                    advice_y - 5,
                    600,
                    35
                )
                pygame.draw.rect(self.screen, (255, 215, 0, 40), advice_bg, border_radius=8)
                pygame.draw.rect(self.screen, GOLD_COLOR, advice_bg, 2, border_radius=8)
                
                self.ui_manager.draw_text(
                    consejo, 
                    self.layout.info_area.x + self.layout.padding, 
                    advice_y, 
                    'base', 
                    TEXT_GOLD,
                    shadow=True
                )
        
        # Área del DEALER
        dealer_title_y = self.layout.dealer_area.y + 10
        self.ui_manager.draw_text(
            "🎩 DEALER", 
            self.layout.dealer_area.x + 20, 
            dealer_title_y, 
            'subtitle', 
            TEXT_GOLD,
            shadow=True
        )
        
        if self.dealer:
            positions = self.layout.get_card_positions_centered(len(self.dealer), self.layout.dealer_area)
            if not self.game_over and self.mode in ("play_human", "duel"):
                # Mostrar solo primera carta del dealer
                if positions:
                    self.ui_manager.draw_card(positions[0][0], positions[0][1], self.dealer[0])
                if len(positions) > 1:
                    self.ui_manager.draw_card(positions[1][0], positions[1][1], None, hidden=True)
                
                # Total oculto
                total_text = "Total: ??"
                total_color = TEXT_LIGHT
            else:
                # Mostrar todas las cartas
                for i, (x, y) in enumerate(positions):
                    if i < len(self.dealer):
                        self.ui_manager.draw_card(x, y, self.dealer[i])
                
                total_dealer = self.juego.calcular_mano(self.dealer)
                total_text = f"Total: {total_dealer}"
                if total_dealer > 21:
                    total_color = TEXT_RED
                elif total_dealer == 21:
                    total_color = TEXT_GOLD
                else:
                    total_color = TEXT_LIGHT
                    
            # Mostrar total del dealer
            total_x = self.layout.dealer_area.centerx
            total_y = self.layout.dealer_area.bottom - 40
            self.ui_manager.draw_text(
                total_text, 
                total_x, 
                total_y, 
                'base', 
                total_color, 
                center=True,
                shadow=True
            )
        
        # Área del JUGADOR
        player_title_y = self.layout.player_area.y + 10
        self.ui_manager.draw_text(
            "👤 JUGADOR", 
            self.layout.player_area.x + 20, 
            player_title_y, 
            'subtitle', 
            TEXT_GOLD,
            shadow=True
        )
        
        if self.jugador:
            positions = self.layout.get_card_positions_centered(len(self.jugador), self.layout.player_area)
            for i, (x, y) in enumerate(positions):
                if i < len(self.jugador):
                    self.ui_manager.draw_card(x, y, self.jugador[i])
            
            total_jugador = self.juego.calcular_mano(self.jugador)
            total_text = f"Total: {total_jugador}"
            
            if total_jugador > 21:
                total_color = TEXT_RED
            elif total_jugador == 21:
                total_color = TEXT_GOLD
            else:
                total_color = TEXT_GREEN
                
            # Mostrar total del jugador
            total_x = self.layout.player_area.centerx
            total_y = self.layout.player_area.bottom - 40
            self.ui_manager.draw_text(
                total_text, 
                total_x, 
                total_y, 
                'base', 
                total_color, 
                center=True,
                shadow=True
            )
        else:
            # Sin cartas
            self.ui_manager.draw_text(
                "Sin cartas", 
                self.layout.player_area.centerx, 
                self.layout.player_area.centery, 
                'base', 
                (150, 150, 150), 
                center=True
            )
        
        # Área de la IA (solo si participa)
        if self.ia or self.mode in ("play_ai", "duel"):
            ai_title_y = self.layout.ai_area.y + 10
            self.ui_manager.draw_text(
                "🤖 INTELIGENCIA ARTIFICIAL", 
                self.layout.ai_area.x + 20, 
                ai_title_y, 
                'subtitle', 
                TEXT_GOLD,
                shadow=True
            )
            
            if self.ia:
                positions = self.layout.get_card_positions_centered(len(self.ia), self.layout.ai_area)
                for i, (x, y) in enumerate(positions):
                    if i < len(self.ia):
                        self.ui_manager.draw_card(x, y, self.ia[i])
                
                total_ia = self.juego.calcular_mano(self.ia)
                total_text = f"Total: {total_ia}"
                
                if total_ia > 21:
                    total_color = TEXT_RED
                elif total_ia == 21:
                    total_color = TEXT_GOLD
                else:
                    total_color = TEXT_GREEN
                    
                # Mostrar total de la IA
                total_x = self.layout.ai_area.centerx
                total_y = self.layout.ai_area.bottom - 40
                self.ui_manager.draw_text(
                    total_text, 
                    total_x, 
                    total_y, 
                    'base', 
                    total_color, 
                    center=True,
                    shadow=True
                )
            else:
                self.ui_manager.draw_text(
                    "IA no participando", 
                    self.layout.ai_area.centerx, 
                    self.layout.ai_area.centery, 
                    'base', 
                    (150, 150, 150), 
                    center=True
                )
        
        # Panel de control con botones
        panel_title_y = self.layout.control_panel.y + 15
        self.ui_manager.draw_text(
            "🎮 CONTROLES", 
            self.layout.control_panel.centerx, 
            panel_title_y, 
            'subtitle', 
            TEXT_GOLD, 
            center=True,
            shadow=True
        )
        
        # Dibujar botones
        button_rects = []
        button_index = 0
        
        for i, (texto, callback, button_type) in enumerate(self.buttons):
            if texto == "":  # Separador
                continue
                
            rect = self.layout.get_button_rect(button_index)
            button_rects.append(rect)
            
            # Determinar si está habilitado
            enabled = True
            display_text = texto
            
            if i == 4 or i == 5:  # Hit/Stand
                enabled = not self.game_over and self.player_turn and self.mode in ("play_human", "duel")
            elif i == 6:  # Consejo IA
                status = "ON" if self.show_ai_recommendation else "OFF"
                display_text = f"💡 Consejo: {status}"
                button_type = 'success' if self.show_ai_recommendation else 'secondary'
            
            # Determinar si está siendo hover
            hovered = (self.ui_manager.hovered_button == button_index)
            
            self.ui_manager.draw_elegant_button(
                rect, 
                display_text, 
                button_type, 
                enabled, 
                hovered
            )
            
            button_index += 1
        
        # Información adicional en el panel
        if self.agent:
            info_y = self.layout.control_panel.bottom - 100
            self.ui_manager.draw_text(
                "🤖 IA Disponible", 
                self.layout.control_panel.centerx, 
                info_y, 
                'small', 
                TEXT_GREEN, 
                center=True
            )
        else:
            info_y = self.layout.control_panel.bottom - 100
            self.ui_manager.draw_text(
                "❌ IA No Disponible", 
                self.layout.control_panel.centerx, 
                info_y, 
                'small', 
                TEXT_RED, 
                center=True
            )
        
        # Controles de teclado
        controls_y = info_y + 25
        self.ui_manager.draw_text(
            "⌨️ H: Hit | S: Stand", 
            self.layout.control_panel.centerx, 
            controls_y, 
            'small', 
            (180, 180, 180), 
            center=True
        )
        
        return button_rects

# ---------- Loop principal optimizado ----------
def main_loop():
    """Loop principal del juego"""
    global pantalla
    ui = GameUI(pantalla)
    
    # Variables para FPS y tiempo
    last_time = time.time()
    frame_count = 0
    
    while True:
        current_time = time.time()
        dt = current_time - last_time
        last_time = current_time
        frame_count += 1
        
        # Obtener posición del mouse
        mouse_pos = pygame.mouse.get_pos()
        
        # Procesar eventos
        for evt in pygame.event.get():
            if evt.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                
            elif evt.type == pygame.VIDEORESIZE:
                # Manejar redimensionamiento
                new_size = (max(evt.w, MIN_WIDTH), max(evt.h, MIN_HEIGHT))
                pantalla = pygame.display.set_mode(new_size, pygame.RESIZABLE)
                ui.screen = pantalla
                ui.handle_resize(new_size)
                
            elif evt.type == pygame.MOUSEBUTTONDOWN and evt.button == 1:
                # Click del mouse
                button_rects = ui.draw()  # Obtener posiciones actuales
                button_index = 0
                
                for i, (texto, callback, _) in enumerate(ui.buttons):
                    if texto == "":  # Skip separators
                        continue
                        
                    if button_index < len(button_rects):
                        rect = button_rects[button_index]
                        if rect.collidepoint(mouse_pos) and callback:
                            callback()
                            break
                    button_index += 1
                        
            elif evt.type == pygame.KEYDOWN:
                # Controles de teclado
                if evt.key == pygame.K_h and not ui.game_over and ui.player_turn:
                    ui.player_hit()
                elif evt.key == pygame.K_s and not ui.game_over and ui.player_turn:
                    ui.player_stand()
                elif evt.key == pygame.K_ESCAPE:
                    # ESC para salir
                    pygame.quit()
                    sys.exit()
        
        # Dibujar todo
        button_rects = ui.draw()
        
        # Actualizar hover de botones
        ui.ui_manager.update_hover(mouse_pos, button_rects)
        
        # Actualizar pantalla
        pygame.display.flip()
        reloj.tick(FPS)

# ---------- Punto de entrada ----------
if __name__ == "__main__":
    print("🎰 Iniciando Casino Blackjack Premium...")
    try:
        initialize_pygame()
        print("✅ Pygame inicializado correctamente")
        main_loop()
    except Exception as e:
        print(f"❌ Error crítico: {e}")
        pygame.quit()
        sys.exit(1)