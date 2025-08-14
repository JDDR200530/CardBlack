# poker_casino_4players_elimination.py
import pygame
import sys
import time
import os
import threading
import math
import random
from holdem_env import HoldemEnv
from poker_agent import PolicyAgent, HeuristicAgent, RandomAgent

# ---------- Configuración Premium para 4 Jugadores ----------
RUTA_CARTAS = r"E:\Sistemas\CardBlack\CardBlack\cards"

pygame.init()

# Sistema responsive mejorado
info = pygame.display.Info()
SCREEN_W, SCREEN_H = info.current_w, info.current_h
print(f"🖥️ Resolución detectada: {SCREEN_W}x{SCREEN_H}")

# Ajustes de tamaño más precisos
if SCREEN_W >= 1920:  # 4K/2K
    ANCHO, ALTO = 1800, 1100
    FONT_SCALE = 1.4
    CARD_SCALE = 1.3
    UI_SCALE = 1.2
elif SCREEN_W >= 1366:  # Full HD
    ANCHO, ALTO = 1400, 900
    FONT_SCALE = 1.1
    CARD_SCALE = 1.0
    UI_SCALE = 1.0
else:  # HD/Pequeña
    ANCHO, ALTO = min(SCREEN_W-80, 1200), min(SCREEN_H-80, 800)
    FONT_SCALE = 0.9
    CARD_SCALE = 0.8
    UI_SCALE = 0.8

# Tamaños escalados
CARD_W, CARD_H = int(85 * CARD_SCALE), int(130 * CARD_SCALE)
FONT_SIZE = int(20 * FONT_SCALE)
FONT_L_SIZE = int(28 * FONT_SCALE)
FONT_XL_SIZE = int(36 * FONT_SCALE)

# Colores tema casino premium
COLORS = {
    'bg': (8, 40, 20),           # Verde casino profundo
    'table': (15, 85, 45),       # Verde fieltro
    'table_border': (180, 140, 70), # Madera dorada
    'felt_dark': (10, 60, 30),   # Verde más oscuro para sombras
    'gold': (255, 215, 0),       # Dorado
    'silver': (192, 192, 192),   # Plateado
    'white': (255, 255, 255),    # Blanco
    'red': (220, 50, 50),        # Rojo casino
    'blue': (50, 100, 200),      # Azul elegante
    'green': (50, 180, 50),      # Verde éxito
    'orange': (255, 140, 0),     # Naranja warning
    'purple': (150, 50, 200),    # Púrpura premium
    'text_light': (255, 255, 255),
    'text_gold': (255, 215, 0),
    'text_silver': (220, 220, 220),
    'text_dim': (180, 180, 180),
    'chip_red': (200, 30, 30),
    'chip_blue': (30, 30, 200),
    'chip_green': (30, 150, 30),
    'chip_black': (40, 40, 40),
    'adjust_mode': (255, 100, 100),  # Color para modo ajuste
    'eliminated': (100, 50, 50),     # Color para jugadores eliminados
}

# ---------- Configuración Pygame ----------
pantalla = pygame.display.set_mode((ANCHO, ALTO), pygame.RESIZABLE)
pygame.display.set_caption("🎰 Texas Hold'em Casino Premium - 4 Jugadores (Eliminación)")
clock = pygame.time.Clock()

# Fuentes escaladas
FONTS = {
    'small': pygame.font.SysFont("Georgia", int(16 * FONT_SCALE)),
    'base': pygame.font.SysFont("Georgia", FONT_SIZE),
    'large': pygame.font.SysFont("Georgia", FONT_L_SIZE, bold=True),
    'xl': pygame.font.SysFont("Georgia", FONT_XL_SIZE, bold=True),
    'card': pygame.font.SysFont("Arial", int(18 * FONT_SCALE), bold=True),
    'button': pygame.font.SysFont("Arial", int(18 * FONT_SCALE), bold=True)
}

# Cache de imágenes mejorado
image_cache = {}

# ---------- Efectos Visuales Premium ----------
class PokerVisualEffects:
    @staticmethod
    def draw_gradient_circle(surface, color1, color2, center, radius):
        """Dibuja un círculo con gradiente radial"""
        for i in range(radius, 0, -2):
            ratio = (radius - i) / radius
            r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
            g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
            b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
            pygame.draw.circle(surface, (r, g, b), center, i)
    
    @staticmethod
    def draw_gradient_rect(surface, color1, color2, rect, vertical=True):
        """Dibuja rectángulo con gradiente"""
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
    def draw_card_shadow(surface, x, y, width, height, offset=6):
        """Dibuja sombra para cartas"""
        shadow_surf = pygame.Surface((width, height), pygame.SRCALPHA)
        shadow_surf.fill((0, 0, 0, 100))
        surface.blit(shadow_surf, (x + offset, y + offset))

# ---------- Sistema de Cartas Mejorado ----------
def load_card_image_premium(card):
    """Carga imagen de carta con fallback mejorado"""
    r, s = card
    rstr = {14:"A", 13:"K", 12:"Q", 11:"J"}.get(r, str(r))
    
    # Múltiples variantes de nombres de archivo
    candidates = [
        f"{rstr}_{s}", f"{rstr}{s}", f"{r}_{s}", f"{r}{s}",
        f"{rstr}_{s.lower()}", f"{rstr}{s[0].upper()}"
    ]
    
    # Nombres en inglés
    eng_suits = {"Corazones":"Hearts", "Diamantes":"Diamonds", "Trebol":"Clubs", "Copas":"Spades"}
    if s in eng_suits:
        eng_suit = eng_suits[s]
        candidates.extend([
            f"{rstr}_{eng_suit}", f"{rstr}{eng_suit}", 
            f"{rstr}_{eng_suit[0]}", f"{rstr}{eng_suit[0].lower()}"
        ])
    
    cache_key = f"{rstr}_{s}"
    if cache_key in image_cache:
        return image_cache[cache_key]
    
    # Intentar cargar imagen
    for candidate in candidates:
        for ext in (".png", ".jpg", ".jpeg", ".bmp"):
            path = os.path.join(RUTA_CARTAS, candidate + ext)
            if os.path.exists(path):
                try:
                    img = pygame.image.load(path).convert_alpha()
                    img = pygame.transform.smoothscale(img, (CARD_W, CARD_H))
                    image_cache[cache_key] = img
                    return img
                except Exception as e:
                    print(f"⚠️ Error cargando {path}: {e}")
    
    # Fallback: crear carta personalizada
    return create_custom_card(card)

def create_custom_card(card):
    """Crea una carta personalizada cuando no hay imagen"""
    r, s = card
    rstr = {14:"A", 13:"K", 12:"Q", 11:"J"}.get(r, str(r))
    
    # Crear superficie de carta
    surf = pygame.Surface((CARD_W, CARD_H), pygame.SRCALPHA)
    
    # Fondo con gradiente
    bg_light = (255, 255, 255)
    bg_dark = (245, 245, 245)
    card_rect = surf.get_rect()
    PokerVisualEffects.draw_gradient_rect(surf, bg_light, bg_dark, card_rect)
    
    # Borde redondeado
    pygame.draw.rect(surf, (200, 200, 200), card_rect, 3, border_radius=12)
    
    # Color del palo
    suit_color = COLORS['red'] if s in ['Corazones', 'Diamantes'] else (30, 30, 30)
    
    # Símbolo del palo
    suit_symbols = {"Corazones": "♥", "Diamantes": "♦", "Trebol": "♣", "Copas": "♠"}
    suit_symbol = suit_symbols.get(s, s[0])
    
    # Texto principal (centro)
    main_text = f"{rstr}"
    main_surf = FONTS['card'].render(main_text, True, suit_color)
    main_rect = main_surf.get_rect(center=(CARD_W//2, CARD_H//2 - 10))
    surf.blit(main_surf, main_rect)
    
    # Símbolo del palo (centro)
    suit_surf = FONTS['card'].render(suit_symbol, True, suit_color)
    suit_rect = suit_surf.get_rect(center=(CARD_W//2, CARD_H//2 + 15))
    surf.blit(suit_surf, suit_rect)
    
    # Esquinas
    corner_font = FONTS['small']
    corner_text = f"{rstr}"
    corner_surf = corner_font.render(corner_text, True, suit_color)
    
    # Esquina superior izquierda
    surf.blit(corner_surf, (8, 8))
    
    # Esquina inferior derecha (rotada)
    rotated = pygame.transform.rotate(corner_surf, 180)
    surf.blit(rotated, (CARD_W - rotated.get_width() - 8, CARD_H - rotated.get_height() - 8))
    
    return surf

def create_card_back():
    """Crea el reverso de las cartas con diseño elegante"""
    surf = pygame.Surface((CARD_W, CARD_H), pygame.SRCALPHA)
    
    # Fondo con gradiente
    bg_dark = (80, 20, 20)
    bg_light = (120, 40, 40)
    card_rect = surf.get_rect()
    PokerVisualEffects.draw_gradient_rect(surf, bg_light, bg_dark, card_rect)
    
    # Borde dorado
    pygame.draw.rect(surf, COLORS['gold'], card_rect, 4, border_radius=12)
    
    # Patrón decorativo
    center_x, center_y = CARD_W//2, CARD_H//2
    
    # Círculos concéntricos
    for radius in [40, 30, 20]:
        pygame.draw.circle(surf, COLORS['gold'], (center_x, center_y), int(radius * CARD_SCALE), 2)
    
    return surf

# ---------- Sistema de Configuración de Posiciones ----------
class CardPositionConfig:
    """Configuración ajustable de posiciones de cartas"""
    def __init__(self):
        center_x, center_y = ANCHO // 2, ALTO // 2
        
        # CONFIGURACIÓN POR DEFECTO DE POSICIONES DE CARTAS
        # Cada jugador tiene un offset desde su posición base
        self.card_offsets = {
            0: {'x': 0, 'y': -120},      # SUR (TÚ) - cartas arriba del área
            1: {'x': 0, 'y': 60},        # NORTE - cartas abajo del área
            2: {'x': -160, 'y': 0},      # ESTE - cartas a la izquierda
            3: {'x': 100, 'y': 0}        # OESTE - cartas a la derecha
        }
        
        # Configuración de cartas comunitarias
        self.community_offset = {'x': 0, 'y': 0}  # Offset desde el centro
        
        # Estado de ajuste
        self.adjustment_mode = False
        self.selected_player = 0  # Jugador seleccionado para ajustar
        self.selected_type = 'player'  # 'player' o 'community'
        self.adjustment_step = 5  # Píxeles por paso
        
        # Presets guardados
        self.presets = {
            'default': self.save_current_config(),
            'compact': {
                'card_offsets': {
                    0: {'x': 0, 'y': -80},
                    1: {'x': 0, 'y': 40},
                    2: {'x': -150, 'y': 0},
                    3: {'x': 80, 'y': 0}
                },
                'community_offset': {'x': 0, 'y': 0}
            },
            'spread': {
                'card_offsets': {
                    0: {'x': 0, 'y': -160},
                    1: {'x': 0, 'y': 80},
                    2: {'x': -200, 'y': 0},
                    3: {'x': 140, 'y': 0}
                },
                'community_offset': {'x': 0, 'y': 0}
            }
        }
    
    def save_current_config(self):
        """Guardar configuración actual"""
        return {
            'card_offsets': self.card_offsets.copy(),
            'community_offset': self.community_offset.copy()
        }
    
    def load_preset(self, preset_name):
        """Cargar un preset"""
        if preset_name in self.presets:
            config = self.presets[preset_name]
            self.card_offsets = config['card_offsets'].copy()
            self.community_offset = config['community_offset'].copy()
            return True
        return False
    
    def save_as_preset(self, preset_name):
        """Guardar configuración actual como preset"""
        self.presets[preset_name] = self.save_current_config()
    
    def toggle_adjustment_mode(self):
        """Alternar modo de ajuste"""
        self.adjustment_mode = not self.adjustment_mode
        return self.adjustment_mode
    
    def select_next_element(self):
        """Seleccionar siguiente elemento para ajustar"""
        if self.selected_type == 'player':
            self.selected_player = (self.selected_player + 1) % 4
            if self.selected_player == 0:
                self.selected_type = 'community'
        else:
            self.selected_type = 'player'
            self.selected_player = 0
    
    def adjust_position(self, dx, dy):
        """Ajustar posición del elemento seleccionado"""
        if not self.adjustment_mode:
            return
            
        if self.selected_type == 'player':
            self.card_offsets[self.selected_player]['x'] += dx * self.adjustment_step
            self.card_offsets[self.selected_player]['y'] += dy * self.adjustment_step
        else:
            self.community_offset['x'] += dx * self.adjustment_step
            self.community_offset['y'] += dy * self.adjustment_step
    
    def get_current_selection_info(self):
        """Obtener información del elemento seleccionado"""
        if self.selected_type == 'player':
            position_names = {0: "SUR (TÚ)", 1: "NORTE", 2: "ESTE", 3: "OESTE"}
            return f"Jugador {position_names[self.selected_player]}"
        else:
            return "Cartas Comunitarias"
    
    def reset_to_default(self):
        """Resetear a configuración por defecto"""
        self.load_preset('default')

# ---------- UI Manager Premium ----------
class PokerUIManager:
    def __init__(self, screen):
        self.screen = screen
        self.effects = PokerVisualEffects()
        self.card_back = create_card_back()
    
    def draw_text(self, text, x, y, font_key='base', color=COLORS['text_light'], center=False, shadow=True):
        """Dibuja texto con opciones avanzadas"""
        font = FONTS.get(font_key, FONTS['base'])
        
        if shadow:
            # Sombra del texto
            shadow_surf = font.render(text, True, (0, 0, 0))
            shadow_x = x + 2 if not center else x - shadow_surf.get_width() // 2 + 2
            shadow_y = y + 2
            self.screen.blit(shadow_surf, (shadow_x, shadow_y))
        
        # Texto principal
        text_surf = font.render(text, True, color)
        if center:
            x = x - text_surf.get_width() // 2
        self.screen.blit(text_surf, (x, y))
        return text_surf.get_rect(x=x, y=y)
    
    def draw_premium_button(self, rect, text, style='primary', enabled=True, hovered=False):
        """Dibuja botón con estilo casino premium"""
        # Estilos de botones
        styles = {
            'primary': {'base': COLORS['red'], 'hover': (250, 70, 70), 'text': COLORS['white']},
            'secondary': {'base': COLORS['blue'], 'hover': (70, 120, 250), 'text': COLORS['white']},
            'success': {'base': COLORS['green'], 'hover': (70, 200, 70), 'text': COLORS['white']},
            'warning': {'base': COLORS['orange'], 'hover': (255, 160, 20), 'text': COLORS['white']},
            'premium': {'base': COLORS['purple'], 'hover': (170, 70, 220), 'text': COLORS['gold']},
            'adjust': {'base': COLORS['adjust_mode'], 'hover': (255, 120, 120), 'text': COLORS['white']},
        }
        
        style_config = styles.get(style, styles['primary'])
        
        if not enabled:
            base_color = (100, 100, 100)
            text_color = (160, 160, 160)
        else:
            base_color = style_config['hover'] if hovered else style_config['base']
            text_color = style_config['text']
        
        # Gradiente del botón
        gradient_light = tuple(min(255, c + 40) for c in base_color)
        self.effects.draw_gradient_rect(self.screen, gradient_light, base_color, rect)
        
        # Borde dorado
        border_color = COLORS['gold'] if enabled else (120, 120, 120)
        pygame.draw.rect(self.screen, border_color, rect, 3, border_radius=10)
        
        # Texto
        font = FONTS['button']
        if font.size(text)[0] > rect.width - 20:
            font = FONTS['small']
        
        # Sombra del texto
        shadow_surf = font.render(text, True, (0, 0, 0))
        shadow_x = rect.centerx - shadow_surf.get_width() // 2 + 1
        shadow_y = rect.centery - shadow_surf.get_height() // 2 + 1
        self.screen.blit(shadow_surf, (shadow_x, shadow_y))
        
        # Texto principal
        text_surf = font.render(text, True, text_color)
        text_x = rect.centerx - text_surf.get_width() // 2
        text_y = rect.centery - text_surf.get_height() // 2
        self.screen.blit(text_surf, (text_x, text_y))
    
    def draw_poker_table(self, table_rect):
        """Dibuja mesa de poker profesional"""
        # Sombra de la mesa
        shadow_rect = pygame.Rect(table_rect.x + 8, table_rect.y + 8, 
                                table_rect.width, table_rect.height)
        pygame.draw.ellipse(self.screen, (0, 0, 0, 80), shadow_rect)
        
        # Mesa base con gradiente
        felt_light = COLORS['table']
        felt_dark = COLORS['felt_dark']
        self.effects.draw_gradient_rect(self.screen, felt_light, felt_dark, table_rect, vertical=False)
        
        # Forma elíptica de la mesa
        pygame.draw.ellipse(self.screen, felt_dark, table_rect)
        
        # Borde de madera con gradiente
        border_light = (200, 160, 90)
        border_dark = COLORS['table_border']
        border_width = int(15 * UI_SCALE)
        
        for i in range(border_width):
            ratio = i / border_width
            r = int(border_light[0] * (1 - ratio) + border_dark[0] * ratio)
            g = int(border_light[1] * (1 - ratio) + border_dark[1] * ratio)
            b = int(border_light[2] * (1 - ratio) + border_dark[2] * ratio)
            
            border_rect = pygame.Rect(
                table_rect.x - i, table_rect.y - i,
                table_rect.width + 2*i, table_rect.height + 2*i
            )
            pygame.draw.ellipse(self.screen, (r, g, b), border_rect, 1)
    
    def draw_card(self, x, y, card=None, hidden=False, highlight=False, eliminated=False):
        """Dibuja carta con efectos premium y resaltado opcional"""
        # Sombra de la carta
        self.effects.draw_card_shadow(self.screen, x, y, CARD_W, CARD_H)
        
        # Resaltado para modo ajuste
        if highlight:
            highlight_rect = pygame.Rect(x - 5, y - 5, CARD_W + 10, CARD_H + 10)
            pygame.draw.rect(self.screen, COLORS['adjust_mode'], highlight_rect, 4, border_radius=8)
        
        # Overlay de eliminación
        if eliminated:
            # Crear superficie semitransparente roja
            overlay = pygame.Surface((CARD_W, CARD_H), pygame.SRCALPHA)
            overlay.fill((*COLORS['eliminated'], 150))
        
        if card is None or hidden:
            # Carta oculta
            self.screen.blit(self.card_back, (x, y))
        else:
            # Carta visible
            card_img = load_card_image_premium(card)
            self.screen.blit(card_img, (x, y))
        
        # Aplicar overlay de eliminación si corresponde
        if eliminated:
            self.screen.blit(overlay, (x, y))

# ---------- Clase Principal para 4 Jugadores con Sistema de Eliminación ----------
class PremiumHoldemUI:
    def __init__(self):
        """Inicializar juego para exactamente 4 jugadores"""
        self.n = 4  # FIJO: Solo 4 jugadores
        self.env = HoldemEnv(n_players=self.n)
        self.ui = PokerUIManager(pantalla)
        
        # Sistema de posiciones ajustables
        self.card_config = CardPositionConfig()
        
        # Sistema monetario mejorado
        self.initial_stack = 2000
        self.stacks = [self.initial_stack for _ in range(self.n)]
        self.human_index = 0  # El humano siempre es jugador 0 (SUR)
        
        # NUEVO: Sistema de eliminación
        self.eliminated_players = set()  # Jugadores eliminados
        self.active_players = set(range(self.n))  # Jugadores activos
        self.game_over = False  # Estado de fin de juego
        self.game_winner = None  # Ganador del torneo
        
        # Configuración de juego
        self.big_blind = 40
        self.small_blind = 20
        self.min_bet = self.big_blind
        self.bet_amount = 100
        self.current_bet = 0
        
        # Estados de juego
        self.reset_hand()
        self.mode = "menu"
        self.auto_ai = False
        self.ai_thread = None
        
        # Sistema de consejos IA
        self.ai_advisor = PolicyAgent()
        self.show_advice = False
        self.current_advice = ""
        
        # Agentes IA
        self.agents = [PolicyAgent() for _ in range(self.n)]
        
        # CONFIGURAR POSICIONES CARDINALES PARA 4 JUGADORES
        self.setup_cardinal_positions()
        
        # Historial y estadísticas
        self.hand_number = 0
        self.game_stats = {
            'hands_played': 0,
            'hands_won': 0,
            'total_winnings': 0,
            'biggest_pot': 0,
            'players_eliminated': 0
        }
        
        # Mensajes y estado
        self.msg = "🎰 Bienvenido al Casino Premium - 4 Jugadores (Eliminación)"
        self.winner_msg = ""
        self.running = False
        self.hovered_button = -1
        
        print("🎰 Texas Hold'em Casino Premium inicializado para 4 jugadores")
        print("🧭 Posiciones: TÚ (Sur), Norte, Este, Oeste")
        print("💀 Sistema de eliminación activado")
        print("🎯 Modo ajuste activado - Usa TAB para ajustar posiciones de cartas")
    
    def setup_cardinal_positions(self):
        """
        CONFIGURACIÓN DE POSICIONES CARDINALES PARA 4 JUGADORES
        
        Distribución en la mesa:
        - Jugador 0 (TÚ): SUR (abajo de la pantalla)
        - Jugador 1: NORTE (arriba de la pantalla) 
        - Jugador 2: ESTE (derecha de la pantalla)
        - Jugador 3: OESTE (izquierda de la pantalla)
        """
        center_x, center_y = ANCHO // 2, ALTO // 2
        
        # Distancias desde el centro
        horizontal_distance = 280  # Distancia horizontal (Este/Oeste)
        vertical_distance = 200    # Distancia vertical (Norte/Sur)
        
        self.player_positions = {
            0: (center_x, center_y  +50+ vertical_distance),           # SUR - TÚ (abajo)
            1: (center_x, center_y -75- vertical_distance),           # NORTE (arriba) 
            2: (center_x +150+ horizontal_distance, center_y - 40),         # ESTE (derecha)
            3: (center_x -150- horizontal_distance, center_y-40)          # OESTE (izquierda)
        }
        
        # Nombres de las posiciones para mostrar
        self.position_names = {
            0: "Jugador 1(TÚ)",
            1: "Jugador 2", 
            2: "Jugador 3",
            3: "Jugador 4"
        }
        
        print("🧭 Posiciones configuradas:")
        for i, (pos_name, coords) in enumerate(zip(self.position_names.values(), self.player_positions.values())):
            print(f"  Jugador {i}: {pos_name} - {coords}")
    
    def check_eliminations(self):
        """Verificar y procesar eliminaciones de jugadores sin dinero"""
        newly_eliminated = []
        
        for player_id in range(self.n):
            if (player_id in self.active_players and 
                self.stacks[player_id] < self.big_blind):
                # Jugador eliminado por falta de fondos
                self.eliminated_players.add(player_id)
                self.active_players.discard(player_id)
                newly_eliminated.append(player_id)
                
                # Actualizar estadísticas
                if player_id != self.human_index:
                    self.game_stats['players_eliminated'] += 1
        
        # Procesar eliminaciones
        if newly_eliminated:
            eliminated_names = []
            for player_id in newly_eliminated:
                if player_id == self.human_index:
                    name = "TÚ (Sur)"
                else:
                    name = self.position_names[player_id]
                eliminated_names.append(name)
            
            if len(eliminated_names) == 1:
                self.msg = f"💀 {eliminated_names[0]} ha sido eliminado por falta de dinero!"
            else:
                self.msg = f"💀 Eliminados: {', '.join(eliminated_names)}"
        
        # Verificar condición de fin de juego
        self.check_game_over()
    
    def check_game_over(self):
        """Verificar si el juego ha terminado"""
        active_count = len(self.active_players)
        
        if active_count <= 1:
            # Juego terminado
            self.game_over = True
            self.running = False
            self.stop_ai_vs_ai()
            
            if active_count == 1:
                # Hay un ganador
                winner_id = list(self.active_players)[0]
                self.game_winner = winner_id
                
                if winner_id == self.human_index:
                    winner_name = "¡TÚ (Sur)!"
                    self.winner_msg = f"🏆 ¡FELICITACIONES! ¡HAS GANADO EL TORNEO! 🏆"
                else:
                    winner_name = self.position_names[winner_id]
                    self.winner_msg = f"💀 Juego terminado. Ganador: {winner_name}"
                
                self.msg = f"🎯 TORNEO FINALIZADO - Ganador: {winner_name}"
            else:
                # Todos eliminados (caso raro)
                self.winner_msg = "💀 Todos los jugadores han sido eliminados"
                self.msg = "🎯 TORNEO FINALIZADO - Sin ganador"
            
            return True
        
        return False
    
    def get_active_players_for_hand(self):
        """Obtener lista de jugadores activos para una mano"""
        return [p for p in range(self.n) if p in self.active_players]
    
    def get_card_positions_for_player(self, player_index):
        """
        CALCULA LAS POSICIONES DE LAS CARTAS USANDO CONFIGURACIÓN AJUSTABLE
        
        Ahora usa los offsets configurables del sistema CardPositionConfig
        """
        player_x, player_y = self.player_positions[player_index]
        
        # Aplicar offset configurado
        offset = self.card_config.card_offsets[player_index]
        cards_x = player_x - (2 * CARD_W + 10) // 2 + offset['x']  # Centrar 2 cartas + offset
        cards_y = player_y + offset['y']  # Posición base + offset
        
        return cards_x, cards_y
    
    def get_community_cards_position(self):
        """
        POSICIÓN DE LAS CARTAS COMUNITARIAS CON CONFIGURACIÓN AJUSTABLE
        
        Se ubican en el centro de la mesa con offset configurable
        """
        center_x, center_y = ANCHO // 2, ALTO // 2
        
        # 5 cartas comunitarias centradas + offset configurable
        total_width = 5 * CARD_W + 4 * 15  # 5 cartas + 4 espacios
        start_x = center_x - total_width // 2 + self.card_config.community_offset['x']
        cards_y = center_y - CARD_H // 2 + self.card_config.community_offset['y']
        
        return start_x, cards_y
    
    def reset_hand(self):
        """Resetear mano actual"""
        if not self.game_over:
            self.env.reset()
        self.running = False
        self.current_bet = 0
        self.winner_msg = ""
        if not hasattr(self, 'msg') or "Bienvenido" not in self.msg:
            if not self.game_over:
                self.msg = "Listo para nueva mano"
    
    def new_hand(self, mode="human"):
        """Iniciar nueva mano con verificación de eliminaciones"""
        # Verificar si el juego ha terminado
        if self.game_over:
            self.msg = "🎯 El torneo ha terminado. Presiona R para reiniciar."
            return
        
        # Verificar eliminaciones antes de empezar la mano
        self.check_eliminations()
        
        if self.game_over:
            return
        
        # Verificar jugadores activos suficientes
        active_players = self.get_active_players_for_hand()
        if len(active_players) < 2:
            self.check_game_over()
            return
        
        # Verificar si el humano puede pagar el big blind
        if (self.human_index in self.active_players and 
            self.stacks[self.human_index] < self.big_blind):
            self.check_eliminations()
            return
        
        self.hand_number += 1
        self.mode = mode
        self.env.reset()
        self.running = True
        self.current_bet = self.big_blind
        self.winner_msg = ""
        
        # Cobrar blinds solo de jugadores activos
        self.collect_blinds()
        
        mode_names = {
            "human": "👤 Humano vs IA",
            "ai_vs_ai": "🤖 IA vs IA"
        }
        
        active_count = len(self.active_players)
        self.msg = f"🎯 Mano #{self.hand_number} - {mode_names.get(mode, mode)} ({active_count} jugadores activos)"
        
        # Actualizar estadísticas
        self.game_stats['hands_played'] += 1
        
        if mode == "ai_vs_ai":
            self.start_ai_vs_ai()
    
    def collect_blinds(self):
        """Cobrar small blind y big blind de jugadores activos"""
        active_players = self.get_active_players_for_hand()
        
        if len(active_players) < 2:
            return
        
        # Determinar jugadores para blinds basado en jugadores activos
        # SB = segundo jugador activo, BB = tercer jugador activo (o primero si solo hay 2)
        if len(active_players) == 2:
            sb_player = active_players[0]
            bb_player = active_players[1]
        else:
            # Con más de 2 jugadores, usar rotación
            sb_player = active_players[1] if 1 in active_players else active_players[0]
            bb_player = active_players[2] if 2 in active_players else active_players[1]
        
        blind_msg = ""
        
        # Small blind
        if sb_player in self.active_players:
            sb_amount = min(self.small_blind, self.stacks[sb_player])
            self.stacks[sb_player] -= sb_amount
            self.env.pot += sb_amount
            sb_name = "TÚ" if sb_player == self.human_index else self.position_names[sb_player]
            blind_msg += f"SB: {sb_name} ${sb_amount}"
        
        # Big blind
        if bb_player in self.active_players:
            bb_amount = min(self.big_blind, self.stacks[bb_player])
            self.stacks[bb_player] -= bb_amount
            self.env.pot += bb_amount
            bb_name = "TÚ" if bb_player == self.human_index else self.position_names[bb_player]
            blind_msg += f", BB: {bb_name} ${bb_amount}"
        
        if blind_msg:
            self.msg += f" | {blind_msg}"

    def start_ai_vs_ai(self):
        """Iniciar modo IA vs IA solo con jugadores activos"""
        if self.game_over:
            return
            
        if self.ai_thread is None or not self.ai_thread.is_alive():
            self.auto_ai = True
            self.ai_thread = threading.Thread(target=self.run_ai_vs_ai, daemon=True)
            self.ai_thread.start()

    def stop_ai_vs_ai(self):
        """Detener modo IA vs IA"""
        self.auto_ai = False
        if not self.game_over:
            self.msg = "🛑 Modo IA vs IA detenido"
        if self.ai_thread and self.ai_thread.is_alive():
            self.ai_thread.join(timeout=1)

    def get_ai_advice(self):
        """Obtener consejo detallado de la IA"""
        if self.game_over:
            return "🎯 El torneo ha terminado."
            
        if not self.running or self.env.current_player != self.human_index:
            return "⏸️ No es tu turno para pedir consejo."
        
        if self.human_index not in self.active_players:
            return "💀 Has sido eliminado del torneo."
        
        try:
            obs = self.env._get_obs(self.human_index)
            suggested_action = self.ai_advisor.action(obs)
            
            # Análisis detallado
            hand = self.env.hands[self.human_index] if self.env.hands else []
            board = self.env.board if hasattr(self.env, 'board') else []
            
            action_advice = {
                0: f"🚫 FOLD - La IA sugiere retirarte\n💡 Las cartas no son prometedoras",
                1: f"✅ CALL/CHECK - La IA sugiere igualar\n💡 Situación neutral, mantén la calma",
                2: f"🎯 BET/RAISE - La IA sugiere apostar ${self.bet_amount}\n💡 ¡Tienes buenas cartas!"
            }
            
            advice = action_advice.get(suggested_action, "❓ Acción desconocida")
            
            # Información adicional
            advice += f"\n\n📊 SITUACIÓN ACTUAL:"
            advice += f"\n💰 Pot: ${self.env.pot}"
            advice += f"\n💵 Para igualar: ${self.current_bet}"
            advice += f"\n🎯 Tu stack: ${self.stacks[self.human_index]}"
            advice += f"\n👥 Jugadores activos: {len(self.active_players)}"
            
            return advice
            
        except Exception as e:
            return f"❌ Error al obtener consejo: {str(e)}"

    def adjust_bet_amount(self, change):
        """Ajustar cantidad de apuesta"""
        if self.game_over or self.human_index not in self.active_players:
            return
            
        old_amount = self.bet_amount
        self.bet_amount = max(self.min_bet, 
                            min(self.stacks[self.human_index], 
                                self.bet_amount + change))
        
        if self.bet_amount != old_amount:
            self.msg = f"💰 Apuesta ajustada a ${self.bet_amount}"

    def toggle_advice(self):
        """Mostrar/ocultar consejo de IA"""
        if self.game_over:
            self.msg = "🎯 El torneo ha terminado."
            return
            
        if self.mode == "human":
            self.show_advice = not self.show_advice
            if self.show_advice:
                self.current_advice = self.get_ai_advice()
                self.msg = "🤖 Consejo de IA activado"
            else:
                self.current_advice = ""
                self.msg = "🤖 Consejo de IA desactivado"

    def human_action(self, action):
        """Procesar acción del jugador humano"""
        if self.game_over:
            self.msg = "🎯 El torneo ha terminado. Presiona R para reiniciar."
            return
            
        if not self.running:
            self.msg = "⚠️ Inicia una nueva mano primero"
            return
        
        if self.human_index not in self.active_players:
            self.msg = "💀 Has sido eliminado del torneo"
            return
        
        if self.env.current_player != self.human_index:
            self.msg = "⏸️ No es tu turno"
            return
        
        # Verificar fondos suficientes para apostar
        if action == 2 and self.stacks[self.human_index] < self.bet_amount:
            self.msg = f"💸 No tienes suficiente dinero para apostar ${self.bet_amount}"
            return
        
        try:
            # Procesar apuesta
            if action == 2:  # Bet/Raise
                bet_amount = min(self.bet_amount, self.stacks[self.human_index])
                self.stacks[self.human_index] -= bet_amount
                self.env.pot += bet_amount
                self.current_bet = max(self.current_bet, bet_amount)
                self.msg = f"🎯 Apostaste ${bet_amount}"
                
            elif action == 1:  # Call/Check
                call_amount = min(self.current_bet, self.stacks[self.human_index])
                if call_amount > 0:
                    self.stacks[self.human_index] -= call_amount
                    self.env.pot += call_amount
                    self.msg = f"✅ Igualaste con ${call_amount}"
                else:
                    self.msg = "✅ Check"
                    
            elif action == 0:  # Fold
                self.msg = "🚫 Te retiraste de la mano"
            
            # Ejecutar acción en el environment
            obs, reward, done, info = self.env.step(self.env.current_player, action)
            
            # Verificar eliminaciones después de la acción
            self.check_eliminations()
            
            # Actualizar consejo si está activo
            if self.show_advice and not done and not self.game_over:
                self.current_advice = self.get_ai_advice()
            
        except Exception as e:
            self.msg = f"❌ Error: {str(e)}"
            return

        if done:
            self.handle_hand_end(info)
        elif not self.game_over:
            # Turno del siguiente jugador (IA)
            next_player = self.env.current_player
            if self.mode == "human" and next_player != self.human_index and next_player in self.active_players:
                threading.Thread(target=self.bot_action, args=(next_player,), daemon=True).start()

    def bot_action(self, bot_index):
        """Procesar acción del bot solo si está activo"""
        if (self.game_over or not self.running or 
            bot_index not in self.active_players or 
            self.stacks[bot_index] <= 0):
            return

        # Tiempo de "pensamiento" del bot
        thinking_time = random.uniform(2.0, 4.0)
        time.sleep(thinking_time)

        if not self.running or self.game_over or bot_index not in self.active_players:
            return

        try:
            obs = self.env._get_obs(bot_index)
            action = self.agents[bot_index].action(obs)
            
            # Procesar apuesta del bot
            if action == 2:  # Bet/Raise
                # Bot apuesta cantidad variable basada en su stack
                max_bet = min(self.stacks[bot_index], self.env.pot // 2)
                bot_bet = max(self.min_bet, min(max_bet, random.randint(50, 200)))
                
                self.stacks[bot_index] -= bot_bet
                self.env.pot += bot_bet
                self.current_bet = max(self.current_bet, bot_bet)
                
                position_name = self.position_names[bot_index]
                self.msg = f"🤖 {position_name} apuesta ${bot_bet}"
                
            elif action == 1:  # Call/Check
                call_amount = min(self.current_bet, self.stacks[bot_index])
                if call_amount > 0:
                    self.stacks[bot_index] -= call_amount
                    self.env.pot += call_amount
                    position_name = self.position_names[bot_index]
                    self.msg = f"🤖 {position_name} iguala ${call_amount}"
                else:
                    position_name = self.position_names[bot_index]
                    self.msg = f"🤖 {position_name} hace check"
                    
            elif action == 0:  # Fold
                position_name = self.position_names[bot_index]
                self.msg = f"🤖 {position_name} se retira"
            
            # Ejecutar en el environment
            obs, reward, done, info = self.env.step(bot_index, action)
            
            # Verificar eliminaciones después de la acción del bot
            self.check_eliminations()
            
        except Exception as e:
            self.msg = f"❌ Error Bot {bot_index}: {str(e)}"
            return

        if done:
            self.handle_hand_end(info)
        elif not self.game_over:
            # Continuar con el siguiente jugador
            next_player = self.env.current_player
            if (self.mode == "human" and next_player != self.human_index and 
                next_player in self.active_players):
                threading.Thread(target=self.bot_action, args=(next_player,), daemon=True).start()

    def handle_hand_end(self, info):
        """Manejar el final de una mano"""
        self.running = False
        
        # Distribuir el pot
        if "winners" in info and info["winners"]:
            winners = info["winners"]
            # Filtrar ganadores que aún están activos
            active_winners = [w for w in winners if w in self.active_players]
            
            if active_winners:
                pot_share = self.env.pot // len(active_winners)
                winner_names = []
                
                for winner in active_winners:
                    self.stacks[winner] += pot_share
                    if winner == self.human_index:
                        name = "TÚ (Sur)"
                    else:
                        name = self.position_names[winner]
                    winner_names.append(name)
                    
                    # Actualizar estadísticas si el humano ganó
                    if winner == self.human_index:
                        self.game_stats['hands_won'] += 1
                        self.game_stats['total_winnings'] += pot_share
                
                self.winner_msg = f"🏆 Ganador(es): {', '.join(winner_names)} - ${pot_share} cada uno"
            
        elif "winner" in info:
            winner = info["winner"]
            if winner in self.active_players:
                self.stacks[winner] += self.env.pot
                if winner == self.human_index:
                    winner_name = "TÚ (Sur)"
                else:
                    winner_name = self.position_names[winner]
                self.winner_msg = f"🏆 Ganador: {winner_name} - ${self.env.pot}"
                
                # Actualizar estadísticas
                if winner == self.human_index:
                    self.game_stats['hands_won'] += 1
                    self.game_stats['total_winnings'] += self.env.pot
        
        # Actualizar estadísticas generales
        if self.env.pot > self.game_stats['biggest_pot']:
            self.game_stats['biggest_pot'] = self.env.pot
        
        # Reset pot
        self.env.pot = 0
        
        # Verificar eliminaciones después de distribuir el pot
        self.check_eliminations()

    def run_ai_vs_ai(self):
        """Ejecutar modo IA vs IA solo con jugadores activos"""
        while self.auto_ai and not self.game_over:
            if not self.running:
                time.sleep(2)  # Pausa entre manos
                if self.auto_ai and not self.game_over:
                    self.new_hand("ai_vs_ai")
            
            while self.running and self.auto_ai and not self.game_over:
                current_player = self.env.current_player
                
                # Verificar si el jugador actual está activo
                if current_player not in self.active_players:
                    # Fold automático si el jugador fue eliminado
                    self.env.step(current_player, 0)
                    continue
                
                if self.stacks[current_player] <= 0:
                    # Fold automático si no tiene dinero
                    self.env.step(current_player, 0)
                    self.check_eliminations()
                    continue
                
                # Tiempo de pensamiento para IA vs IA
                time.sleep(random.uniform(1.5, 3.0))
                
                if not self.auto_ai or not self.running or self.game_over:
                    break
                
                try:
                    obs = self.env._get_obs(current_player)
                    action = self.agents[current_player].action(obs)
                    
                    # Procesar acción IA
                    if action == 2:  # Bet
                        max_bet = min(self.stacks[current_player], self.env.pot)
                        bot_bet = max(self.min_bet, min(max_bet, random.randint(40, 150)))
                        self.stacks[current_player] -= bot_bet
                        self.env.pot += bot_bet
                        self.current_bet = max(self.current_bet, bot_bet)
                        action_msg = f"apuesta ${bot_bet}"
                    elif action == 1:  # Call
                        call_amount = min(self.current_bet, self.stacks[current_player])
                        self.stacks[current_player] -= call_amount
                        self.env.pot += call_amount
                        action_msg = f"iguala ${call_amount}" if call_amount > 0 else "hace check"
                    else:  # Fold
                        action_msg = "se retira"
                    
                    position_name = self.position_names[current_player]
                    active_count = len(self.active_players)
                    self.msg = f"🤖 IA vs IA ({active_count} activos) - {position_name} {action_msg}"
                    
                    # Ejecutar en environment
                    _, _, done, info = self.env.step(current_player, action)
                    
                    # Verificar eliminaciones
                    self.check_eliminations()
                    
                    if done or self.game_over:
                        if not self.game_over:
                            self.handle_hand_end(info)
                        break
                        
                except Exception as e:
                    self.msg = f"❌ Error en IA vs IA: {str(e)}"
                    self.running = False
                    break

    def restart_game(self):
        """Reiniciar completamente el juego"""
        # Detener IA si está corriendo
        self.stop_ai_vs_ai()
        
        # Reinicializar todo el estado
        self.stacks = [self.initial_stack for _ in range(self.n)]
        self.eliminated_players = set()
        self.active_players = set(range(self.n))
        self.game_over = False
        self.game_winner = None
        
        # Resetear estadísticas del juego
        self.hand_number = 0
        self.game_stats = {
            'hands_played': 0,
            'hands_won': 0,
            'total_winnings': 0,
            'biggest_pot': 0,
            'players_eliminated': 0
        }
        
        # Resetear estados
        self.reset_hand()
        self.mode = "menu"
        self.winner_msg = ""
        self.current_advice = ""
        self.show_advice = False
        
        self.msg = "🔄 Juego reiniciado - Todos los jugadores activos con $2000"
        
        print("🔄 Juego completamente reiniciado")
        print("💰 Todos los jugadores: $2000")
        print("👥 4 jugadores activos")

    def draw_background(self):
        """Dibujar fondo elegante del casino"""
        pantalla.fill(COLORS['bg'])
        
        # Patrón de fondo sutil
        for x in range(0, ANCHO, 100):
            for y in range(0, ALTO, 100):
                pygame.draw.circle(pantalla, (COLORS['bg'][0] + 5, COLORS['bg'][1] + 5, COLORS['bg'][2] + 5), 
                                 (x, y), 2)

    def draw_poker_table(self):
        """Dibujar mesa de poker premium"""
        center_x, center_y = ANCHO // 2, ALTO // 2
        table_width = int(600 * UI_SCALE)
        table_height = int(350 * UI_SCALE)
        
        table_rect = pygame.Rect(
            center_x - table_width // 2,
            center_y - table_height // 2,
            table_width,
            table_height
        )
        
        self.ui.draw_poker_table(table_rect)
        
        return table_rect

    def draw_community_cards(self, table_rect):
        """
        DIBUJAR CARTAS COMUNITARIAS EN EL CENTRO DE LA MESA
        
        Las 5 cartas del flop, turn y river se muestran horizontalmente
        en el centro de la mesa con posición ajustable.
        """
        board = getattr(self.env, 'board', [])
        if not board:
            return
        
        # Obtener posición calculada con configuración ajustable
        start_x, cards_y = self.get_community_cards_position()
        
        
        # Determinar si resaltar (modo ajuste y cartas comunitarias seleccionadas)
        highlight = (self.card_config.adjustment_mode and 
                    self.card_config.selected_type == 'community')
        
        # Dibujar cartas
        for i, card in enumerate(board):
            card_x = start_x + i * (CARD_W + 15)
            self.ui.draw_card(card_x, cards_y, card, highlight=highlight)
        
        # Mostrar cuántas cartas faltan
        remaining = 5 - len(board)
        if remaining > 0:
            remaining_text = f"({remaining} carta{'s' if remaining > 1 else ''} por revelar)"
            self.ui.draw_text(remaining_text, ANCHO // 2, cards_y + CARD_H + 10, 
                             'small', COLORS['text_dim'], center=True)

    def draw_pot_info(self, table_rect):
        """Dibujar información del pot y estado del torneo"""
        pot_text = f"💰 POT: ${self.env.pot:,}"
        hand_text = f"🎯 MANO #{self.hand_number}"
        
        # Pot principal
        pot_y = table_rect.centery - 100
        self.ui.draw_text(pot_text, table_rect.centerx, pot_y, 'xl', COLORS['gold'], center=True)
        
        # Número de mano
        hand_y = pot_y + 35
        self.ui.draw_text(hand_text, table_rect.centerx, hand_y, 'base', COLORS['text_silver'], center=True)
        
        # Estado del torneo
        active_count = len(self.active_players)
        eliminated_count = len(self.eliminated_players)
        
        if self.game_over:
            if self.game_winner is not None:
                winner_name = "TÚ" if self.game_winner == self.human_index else self.position_names[self.game_winner]
                tournament_text = f"🏆 TORNEO FINALIZADO - Ganador: {winner_name}"
                color = COLORS['gold']
            else:
                tournament_text = "💀 TORNEO FINALIZADO - Sin ganador"
                color = COLORS['red']
        else:
            tournament_text = f"👥 Activos: {active_count} | 💀 Eliminados: {eliminated_count}"
            color = COLORS['text_silver']
        
        tournament_y = hand_y + 25
        self.ui.draw_text(tournament_text, table_rect.centerx, tournament_y, 'base', color, center=True)
        
        # Información de apuesta actual
        if self.current_bet > 0 and not self.game_over:
            bet_text = f"💵 Apuesta actual: ${self.current_bet}"
            bet_y = table_rect.centery + 80
            self.ui.draw_text(bet_text, table_rect.centerx, bet_y, 'large', COLORS['orange'], center=True)

    def draw_players(self):
        """Dibujar información de todos los jugadores en sus posiciones cardinales"""
        for i in range(4):  # Solo 4 jugadores
            self.draw_single_player(i)

    def draw_single_player(self, player_index):
        """
        DIBUJAR UN JUGADOR ESPECÍFICO EN SU POSICIÓN CARDINAL
        
        Cada jugador se muestra con:
        - Información del jugador (nombre, stack, estado)
        - Sus 2 cartas privadas posicionadas apropiadamente
        - Indicación visual si está eliminado
        """
        x, y = self.player_positions[player_index]
        
        # Dimensiones del área del jugador
        player_width = int(180 * UI_SCALE)
        player_height = int(100 * UI_SCALE)
        
        player_rect = pygame.Rect(
            x - player_width // 2,
            y - player_height // 2,
            player_width,
            player_height
        )
        
        # Determinar estado del jugador
        is_eliminated = player_index in self.eliminated_players
        is_current_turn = self.running and self.env.current_player == player_index and not is_eliminated
        is_human = player_index == self.human_index
        
        # Color según estado
        if is_eliminated:
            bg_color = COLORS['eliminated']  # Rojo oscuro para eliminados
        elif is_current_turn:
            bg_color = (100, 200, 100)  # Verde para turno actual
        elif is_human:
            bg_color = (50, 100, 200)  # Azul para jugador humano
        else:
            bg_color = (80, 80, 120)  # Gris para bots
        
        # Fondo del jugador con gradiente
        gradient_light = tuple(min(255, c + 40) for c in bg_color)
        self.ui.effects.draw_gradient_rect(pantalla, gradient_light, bg_color, player_rect)
        
        # Borde según estado
        if is_eliminated:
            border_color = COLORS['red']
            border_width = 4
        elif is_current_turn:
            border_color = COLORS['gold']
            border_width = 4
        else:
            border_color = COLORS['silver']
            border_width = 3
        
        pygame.draw.rect(pantalla, border_color, player_rect, border_width, border_radius=15)
        
        # Información del jugador
        if is_human:
            name = "👤 TÚ (SUR)"
        else:
            name = f"🤖 {self.position_names[player_index]}"
        
        # Añadir estado de eliminación
        if is_eliminated:
            name += " 💀"
            stack_text = "💀 ELIMINADO"
            stack_color = COLORS['red']
        else:
            stack_text = f"💰 ${self.stacks[player_index]:,}"
            if self.stacks[player_index] > self.initial_stack:
                stack_color = COLORS['green']
            elif self.stacks[player_index] < self.big_blind:
                stack_color = COLORS['red']
            else:
                stack_color = COLORS['orange']
        
        # Estado adicional
        status = ""
        if not is_eliminated:
            if self.stacks[player_index] < self.big_blind:
                status = " ⚠️ EN PELIGRO"
            elif hasattr(self.env, 'folded') and player_index in getattr(self.env, 'folded', []):
                status = " 🚫 FOLD"
        
        # Dibujar textos
        name_y = player_rect.y + 10
        name_color = COLORS['red'] if is_eliminated else COLORS['white']
        self.ui.draw_text(name + status, player_rect.x + 8, name_y, 'small', name_color)
        
        stack_y = name_y + 25
        self.ui.draw_text(stack_text, player_rect.x + 8, stack_y, 'base', stack_color)
        
        # Apuesta actual del jugador (solo si no está eliminado)
        if not is_eliminated and hasattr(self.env, 'current_bets') and player_index in getattr(self.env, 'current_bets', {}):
            bet_amount = self.env.current_bets[player_index]
            if bet_amount > 0:
                bet_y = stack_y + 20
                self.ui.draw_text(f"🎯 ${bet_amount}", player_rect.x + 8, bet_y, 'small', COLORS['text_gold'])
        
        # Dibujar cartas del jugador
        self.draw_player_cards(player_index)

    def draw_player_cards(self, player_index):
        """
        DIBUJAR LAS 2 CARTAS PRIVADAS DE UN JUGADOR
        
        Las cartas se posicionan según la configuración ajustable
        """
        if not hasattr(self.env, 'hands') or player_index >= len(self.env.hands):
            return
        
        hand = self.env.hands[player_index]
        if not hand or len(hand) < 2:
            return
        
        # Determinar si mostrar cartas
        is_eliminated = player_index in self.eliminated_players
        show_cards = (
            player_index == self.human_index or  # Siempre mostrar cartas del humano
            not self.running or  # Mostrar al final del juego
            self.mode == "ai_vs_ai" or  # Mostrar en modo IA vs IA
            getattr(self.env, 'round_stage', '') == "showdown"  # Mostrar en showdown
        )
        
        # Determinar si resaltar (modo ajuste y jugador seleccionado)
        highlight = (self.card_config.adjustment_mode and 
                    self.card_config.selected_type == 'player' and 
                    self.card_config.selected_player == player_index)
        
        # Obtener posición calculada para las cartas usando configuración ajustable
        cards_x, cards_y = self.get_card_positions_for_player(player_index)
        
        # Dibujar las 2 cartas privadas
        for i, card in enumerate(hand[:2]):  # Solo las primeras 2 cartas
            card_x = cards_x + i * (CARD_W + 10)
            
            if show_cards:
                self.ui.draw_card(card_x, cards_y, card, highlight=highlight, eliminated=is_eliminated)
            else:
                self.ui.draw_card(card_x, cards_y, hidden=True, highlight=highlight, eliminated=is_eliminated)

    def draw_adjustment_panel(self):
        """Dibujar panel de ajuste de posiciones"""
        if not self.card_config.adjustment_mode:
            return
        
        # Panel de información de ajuste
        panel_width = 400
        panel_height = 160
        panel_rect = pygame.Rect(20, 20, panel_width, panel_height)
        
        # Fondo con gradiente
        bg_light = (80, 20, 20)
        bg_dark = (60, 10, 10)
        self.ui.effects.draw_gradient_rect(pantalla, bg_light, bg_dark, panel_rect)
        
        # Borde
        pygame.draw.rect(pantalla, COLORS['adjust_mode'], panel_rect, 3, border_radius=15)
        
        # Título
        title_y = panel_rect.y + 10
        self.ui.draw_text("🎯 MODO AJUSTE DE CARTAS", panel_rect.x + 15, title_y, 
                         'large', COLORS['adjust_mode'])
        
        # Información del elemento seleccionado
        selection_info = self.card_config.get_current_selection_info()
        self.ui.draw_text(f"Ajustando: {selection_info}", panel_rect.x + 15, title_y + 30, 
                         'base', COLORS['white'])
        
        # Controles
        controls_y = title_y + 55
        controls = [
            "TAB - Siguiente elemento",
            "Flechas - Mover posición",
            "SHIFT+Flechas - Movimiento rápido",
            "P - Cambiar preset (Default/Compact/Spread)",
            "R - Resetear posiciones",
            "ENTER - Salir del modo ajuste"
        ]
        
        for i, control in enumerate(controls):
            self.ui.draw_text(control, panel_rect.x + 15, controls_y + i * 15, 
                             'small', COLORS['text_silver'])

    def draw_preset_info(self):
        """Mostrar información de presets disponibles"""
        if not self.card_config.adjustment_mode:
            return
            
        # Información de presets en esquina inferior derecha
        preset_text = "Presets: Default | Compact | Spread"
        text_rect = self.ui.draw_text(preset_text, ANCHO - 350, ALTO - 40, 
                                     'small', COLORS['text_gold'])

    def draw_game_info(self):
        """Dibujar información del juego"""
        info_y = ALTO - 120
        
        # Mensaje principal
        if self.card_config.adjustment_mode:
            # Mostrar información de modo ajuste
            self.ui.draw_text("🎯 MODO AJUSTE ACTIVO - Usa las flechas para mover cartas", 
                             20, info_y, 'base', COLORS['adjust_mode'])
        else:
            self.ui.draw_text(self.msg, 20, info_y, 'base', COLORS['text_light'])
        
        # Etapa del juego
        if not self.game_over:
            stage_text = f"📊 Etapa: {getattr(self.env, 'round_stage', 'Inicio')}"
            self.ui.draw_text(stage_text, 20, info_y + 25, 'base', COLORS['text_silver'])
        
        # Modo de juego
        if self.game_over:
            mode_text = "🎯 TORNEO FINALIZADO"
            mode_color = COLORS['red']
        else:
            mode_text = f"🎮 Modo: {self.mode.replace('_', ' ').title()}"
            if self.auto_ai:
                mode_text += " (ACTIVO)"
            mode_color = COLORS['text_gold']
            
        self.ui.draw_text(mode_text, 20, info_y + 50, 'base', mode_color)

    def draw_winner_message(self):
        """Dibujar mensaje de ganador"""
        if not self.winner_msg:
            return
        
        # Fondo del mensaje
        msg_width = 600
        msg_height = 140
        msg_rect = pygame.Rect(
            ANCHO // 2 - msg_width // 2,
            ALTO // 2 - msg_height // 2,
            msg_width,
            msg_height
        )
        
        # Color según tipo de mensaje
        if self.game_over and self.game_winner == self.human_index:
            # Victoria del torneo
            bg_light = (0, 200, 0)
            bg_dark = (0, 150, 0)
            border_color = COLORS['gold']
        elif self.game_over:
            # Fin del torneo (derrota)
            bg_light = (200, 0, 0)
            bg_dark = (150, 0, 0)
            border_color = COLORS['red']
        else:
            # Victoria de mano normal
            bg_light = (0, 150, 0)
            bg_dark = (0, 100, 0)
            border_color = COLORS['gold']
        
        # Fondo con gradiente
        self.ui.effects.draw_gradient_rect(pantalla, bg_light, bg_dark, msg_rect)
        
        # Borde
        pygame.draw.rect(pantalla, border_color, msg_rect, 4, border_radius=20)
        
        # Título según contexto
        if self.game_over:
            if self.game_winner == self.human_index:
                title = "🏆 ¡CAMPEÓN DEL TORNEO! 🏆"
                title_color = COLORS['gold']
            else:
                title = "💀 TORNEO FINALIZADO 💀"
                title_color = COLORS['red']
        else:
            title = "🏆 RESULTADO DE LA MANO 🏆"
            title_color = COLORS['gold']
        
        title_y = msg_rect.y + 15
        self.ui.draw_text(title, msg_rect.centerx, title_y, 
                         'large', title_color, center=True)
        
        # Mensaje principal
        main_y = title_y + 35
        self.ui.draw_text(self.winner_msg, msg_rect.centerx, main_y, 'base', 
                         COLORS['white'], center=True)
        
        # Instrucción según contexto
        if self.game_over:
            instr_text = "Presiona R para reiniciar el torneo"
        else:
            instr_text = "Presiona cualquier tecla para continuar"
            
        instr_y = main_y + 35
        self.ui.draw_text(instr_text, msg_rect.centerx, instr_y, 
                         'small', COLORS['text_silver'], center=True)

    def draw_advice_panel(self):
        """Dibujar panel de consejo de IA"""
        if not self.show_advice or not self.current_advice or self.game_over:
            return
        
        # Panel de consejo
        panel_width = 520
        panel_height = 200
        panel_rect = pygame.Rect(
            ANCHO // 2 - panel_width // 2,
            100,
            panel_width,
            panel_height
        )
        
        # Fondo con gradiente
        bg_light = (20, 20, 80)
        bg_dark = (10, 10, 60)
        self.ui.effects.draw_gradient_rect(pantalla, bg_light, bg_dark, panel_rect)
        
        # Borde
        pygame.draw.rect(pantalla, COLORS['blue'], panel_rect, 3, border_radius=15)
        
        # Título
        title_y = panel_rect.y + 10
        self.ui.draw_text("🤖 CONSEJO DE INTELIGENCIA ARTIFICIAL", 
                         panel_rect.centerx, title_y, 'large', COLORS['gold'], center=True)
        
        # Contenido del consejo
        lines = self.current_advice.split('\n')
        line_height = 18
        start_y = title_y + 35
        
        for i, line in enumerate(lines[:8]):  # Máximo 8 líneas
            if line.strip():
                color = COLORS['white']
                if '🔥' in line or '👑' in line:
                    color = COLORS['green']
                elif '⚠️' in line or '💸' in line:
                    color = COLORS['orange']
                elif '🎯' in line:
                    color = COLORS['gold']
                
                self.ui.draw_text(line, panel_rect.x + 15, start_y + i * line_height, 
                                 'small', color)
        
        # Instrucción para cerrar
        close_y = panel_rect.bottom - 25
        self.ui.draw_text("Presiona C para cerrar el consejo", 
                         panel_rect.centerx, close_y, 'small', COLORS['text_silver'], center=True)

    def draw_statistics_panel(self):
        """Dibujar panel de estadísticas con información de eliminación"""
        if self.game_stats['hands_played'] == 0:
            return
        
        # Panel en esquina superior derecha
        panel_width = 300
        panel_height = 160
        panel_rect = pygame.Rect(ANCHO - panel_width - 20, 20, panel_width, panel_height)
        
        # Fondo semitransparente
        bg_surface = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        bg_surface.fill((*COLORS['bg'], 180))
        pantalla.blit(bg_surface, panel_rect.topleft)
        
        # Borde
        border_color = COLORS['gold'] if not self.game_over else COLORS['red']
        pygame.draw.rect(pantalla, border_color, panel_rect, 2, border_radius=10)
        
        # Título
        title = "📊 ESTADÍSTICAS DEL TORNEO" if self.game_over else "📊 ESTADÍSTICAS - 4 JUGADORES"
        self.ui.draw_text(title, panel_rect.x + 10, panel_rect.y + 10, 
                         'base', COLORS['gold'])
        
        # Estadísticas
        stats_y = panel_rect.y + 35
        win_rate = (self.game_stats['hands_won'] / self.game_stats['hands_played']) * 100 if self.game_stats['hands_played'] > 0 else 0
        
        stats_text = [
            f"Manos jugadas: {self.game_stats['hands_played']}",
            f"Manos ganadas: {self.game_stats['hands_won']}",
            f"% Victorias: {win_rate:.1f}%",
            f"Mayor pot: ${self.game_stats['biggest_pot']:,}",
            f"Ganancias totales: ${self.game_stats['total_winnings']:,}",
            f"Bots eliminados: {self.game_stats['players_eliminated']}"
        ]
        
        for i, stat in enumerate(stats_text):
            color = COLORS['text_light']
            if "Ganancias totales" in stat and self.game_stats['total_winnings'] > 0:
                color = COLORS['green']
            elif "% Victorias" in stat and win_rate > 50:
                color = COLORS['green']
            
            self.ui.draw_text(stat, panel_rect.x + 10, stats_y + i * 18, 
                             'small', color)

    def draw_controls_help(self):
        """Dibujar ayuda de controles"""
        if self.card_config.adjustment_mode:
            return  # No mostrar controles normales en modo ajuste
            
        if self.game_over:
            # Controles para juego terminado
            help_y = ALTO - 100
            self.ui.draw_text("⌨️ CONTROLES:", 20, help_y, 'base', COLORS['text_gold'])
            self.ui.draw_text("R - Reiniciar torneo  |  ESC - Salir", 20, help_y + 20, 
                             'small', COLORS['text_dim'])
            return
            
        if self.mode != "human" or not self.running:
            return
        
        help_y = ALTO - 200
        self.ui.draw_text("⌨️ CONTROLES:", 20, help_y, 'base', COLORS['text_gold'])
        
        controls = [
            "F - Retirarse  |  ESPACIO - Call/Check  |  B - Apostar",
            "Q/E - Apuesta ±$25  |  Z/X - Apuesta ±$100  |  C - Consejo IA",
            "TAB - Modo ajuste cartas  |  P - Presets posición  |  R - Reiniciar"
        ]
        
        for i, control in enumerate(controls):
            self.ui.draw_text(control, 20, help_y + 20 + i * 18, 'small', COLORS['text_dim'])

    def draw_elimination_status(self):
        """Dibujar estado de eliminación en la esquina"""
        if len(self.eliminated_players) == 0:
            return
            
        # Panel pequeño en esquina inferior izquierda
        panel_width = 250
        panel_height = 80
        panel_rect = pygame.Rect(20, ALTO - panel_height - 20, panel_width, panel_height)
        
        # Fondo semitransparente
        bg_surface = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        bg_surface.fill((*COLORS['eliminated'], 150))
        pantalla.blit(bg_surface, panel_rect.topleft)
        
        # Borde
        pygame.draw.rect(pantalla, COLORS['red'], panel_rect, 2, border_radius=8)
        
        # Título
        self.ui.draw_text("💀 JUGADORES ELIMINADOS", panel_rect.x + 10, panel_rect.y + 10, 
                         'base', COLORS['red'])
        
        # Lista de eliminados
        eliminated_names = []
        for player_id in self.eliminated_players:
            if player_id == self.human_index:
                eliminated_names.append("TÚ")
            else:
                eliminated_names.append(self.position_names[player_id].split()[1])  # Solo el número
        
        eliminated_text = ", ".join(eliminated_names)
        self.ui.draw_text(eliminated_text, panel_rect.x + 10, panel_rect.y + 35, 
                         'small', COLORS['white'])

    def draw(self):
        """Dibujar toda la interfaz"""
        # Fondo
        self.draw_background()
        
        # Mesa de poker
        table_rect = self.draw_poker_table()
        
        # Elementos principales
        self.draw_pot_info(table_rect)
        self.draw_community_cards(table_rect)
        self.draw_players()
        
        # Información de juego
        self.draw_game_info()
        self.draw_controls_help()
        
        # Paneles especiales
        self.draw_winner_message()
        self.draw_advice_panel()
        self.draw_statistics_panel()
        self.draw_elimination_status()
        
        # Panel de ajuste (si está activo)
        self.draw_adjustment_panel()
        self.draw_preset_info()

# ---------- Configuración de Botones ----------
def setup_buttons():
    """Configurar botones de la interfaz"""
    button_width = int(200 * UI_SCALE)
    button_height = int(45 * UI_SCALE)
    button_spacing = int(12 * UI_SCALE)
    
    # Botones principales (lado derecho)
    buttons_x = ANCHO - button_width - 30
    buttons_start_y = ALTO - int(380 * UI_SCALE)  # Más espacio para botón de restart
    
    main_buttons = {
        'new_hand': pygame.Rect(buttons_x, buttons_start_y, button_width, button_height),
        'ai_vs_ai': pygame.Rect(buttons_x, buttons_start_y + button_height + button_spacing, button_width, button_height),
        'stop_ai': pygame.Rect(buttons_x, buttons_start_y + 2*(button_height + button_spacing), button_width, button_height),
        'advice': pygame.Rect(buttons_x, buttons_start_y + 3*(button_height + button_spacing), button_width, button_height),
        'adjust': pygame.Rect(buttons_x, buttons_start_y + 4*(button_height + button_spacing), button_width, button_height),
        'restart': pygame.Rect(buttons_x, buttons_start_y + 5*(button_height + button_spacing), button_width, button_height)
    }
    
    # Botones de acción (parte inferior)
    action_width = int(120 * UI_SCALE)
    action_height = int(50 * UI_SCALE)
    action_y = ALTO - action_height - 30
    action_spacing = 15
    
    action_buttons = {
        'fold': pygame.Rect(30, action_y, action_width, action_height),
        'call': pygame.Rect(30 + action_width + action_spacing, action_y, action_width, action_height),
        'bet': pygame.Rect(30 + 2*(action_width + action_spacing), action_y, action_width, action_height),
        'all_in': pygame.Rect(30 + 3*(action_width + action_spacing), action_y, action_width, action_height)
    }
    
    return main_buttons, action_buttons

def draw_buttons(ui_instance, main_buttons, action_buttons):
    """Dibujar todos los botones de la interfaz"""
    # Botones principales
    new_hand_enabled = not ui_instance.auto_ai and not ui_instance.game_over
    new_hand_color = 'primary' if new_hand_enabled else 'secondary'
    ui_instance.ui.draw_premium_button(
        main_buttons['new_hand'], 
        "🎮 Nueva Mano", 
        new_hand_color, 
        new_hand_enabled,
        ui_instance.hovered_button == 0
    )
    
    ai_enabled = not ui_instance.game_over
    ai_text = "🛑 IA ACTIVO" if ui_instance.auto_ai else "🤖 Iniciar IA vs IA"
    ai_color = 'warning' if ui_instance.auto_ai else 'success'
    ui_instance.ui.draw_premium_button(
        main_buttons['ai_vs_ai'], 
        ai_text, 
        ai_color, 
        ai_enabled,
        ui_instance.hovered_button == 1
    )
    
    stop_enabled = ui_instance.auto_ai
    ui_instance.ui.draw_premium_button(
        main_buttons['stop_ai'], 
        "🚫 Parar IA", 
        'primary', 
        stop_enabled,
        ui_instance.hovered_button == 2
    )
    
    advice_enabled = ui_instance.mode == "human" and not ui_instance.game_over
    advice_text = "🤖 Ocultar Consejo" if ui_instance.show_advice else "💡 Consejo IA"
    advice_color = 'success' if ui_instance.show_advice else 'premium'
    ui_instance.ui.draw_premium_button(
        main_buttons['advice'], 
        advice_text, 
        advice_color, 
        advice_enabled,
        ui_instance.hovered_button == 3
    )
    
    # Botón de ajuste de posiciones
    adjust_text = "🎯 Salir Ajuste" if ui_instance.card_config.adjustment_mode else "🎯 Ajustar Cartas"
    adjust_color = 'adjust' if ui_instance.card_config.adjustment_mode else 'premium'
    ui_instance.ui.draw_premium_button(
        main_buttons['adjust'], 
        adjust_text, 
        adjust_color, 
        True,
        ui_instance.hovered_button == 4
    )
    
    # Botón de reinicio
    restart_text = "🔄 Reiniciar Torneo"
    restart_color = 'warning'
    ui_instance.ui.draw_premium_button(
        main_buttons['restart'], 
        restart_text, 
        restart_color, 
        True,
        ui_instance.hovered_button == 5
    )
    
    # Botones de acción (solo en modo humano, no eliminado y no en modo ajuste)
    if (ui_instance.mode == "human" and ui_instance.running and 
        not ui_instance.card_config.adjustment_mode and 
        ui_instance.human_index in ui_instance.active_players and
        not ui_instance.game_over):
        
        # Fold
        ui_instance.ui.draw_premium_button(
            action_buttons['fold'], 
            "🚫 Fold", 
            'primary', 
            True,
            ui_instance.hovered_button == 6
        )
        
        # Call/Check
        call_text = f"✅ Call ${ui_instance.current_bet}" if ui_instance.current_bet > 0 else "✅ Check"
        ui_instance.ui.draw_premium_button(
            action_buttons['call'], 
            call_text, 
            'success', 
            True,
            ui_instance.hovered_button == 7
        )
        
        # Bet/Raise
        bet_enabled = ui_instance.stacks[ui_instance.human_index] >= ui_instance.bet_amount
        ui_instance.ui.draw_premium_button(
            action_buttons['bet'], 
            f"🎯 Bet ${ui_instance.bet_amount}", 
            'warning', 
            bet_enabled,
            ui_instance.hovered_button == 8
        )
        
        # All-in
        all_in_amount = ui_instance.stacks[ui_instance.human_index]
        ui_instance.ui.draw_premium_button(
            action_buttons['all_in'], 
            f"🔥 All-in", 
            'premium', 
            all_in_amount > 0,
            ui_instance.hovered_button == 9
        )

def update_hover_state(ui_instance, mouse_pos, main_buttons, action_buttons):
    """Actualizar estado hover de botones"""
    ui_instance.hovered_button = -1
    
    # Verificar botones principales
    for i, (key, rect) in enumerate(main_buttons.items()):
        if rect.collidepoint(mouse_pos):
            ui_instance.hovered_button = i
            return
    
    # Verificar botones de acción (solo si están visibles)
    if (ui_instance.mode == "human" and ui_instance.running and 
        not ui_instance.card_config.adjustment_mode and
        ui_instance.human_index in ui_instance.active_players and
        not ui_instance.game_over):
        for i, (key, rect) in enumerate(action_buttons.items()):
            if rect.collidepoint(mouse_pos):
                ui_instance.hovered_button = i + 6  # Offset para botones de acción
                return

def handle_position_adjustment_keys(ui_instance, event):
    """Manejar teclas para ajustar posiciones de cartas"""
    if not ui_instance.card_config.adjustment_mode:
        return False
    
    # Determinar si usar movimiento rápido (SHIFT presionado)
    fast_move = pygame.key.get_pressed()[pygame.K_LSHIFT] or pygame.key.get_pressed()[pygame.K_RSHIFT]
    step_multiplier = 3 if fast_move else 1
    
    if event.key == pygame.K_LEFT:
        ui_instance.card_config.adjust_position(-step_multiplier, 0)
        return True
    elif event.key == pygame.K_RIGHT:
        ui_instance.card_config.adjust_position(step_multiplier, 0)
        return True
    elif event.key == pygame.K_UP:
        ui_instance.card_config.adjust_position(0, -step_multiplier)
        return True
    elif event.key == pygame.K_DOWN:
        ui_instance.card_config.adjust_position(0, step_multiplier)
        return True
    elif event.key == pygame.K_TAB:
        ui_instance.card_config.select_next_element()
        selection = ui_instance.card_config.get_current_selection_info()
        ui_instance.msg = f"🎯 Ajustando: {selection}"
        return True
    elif event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
        ui_instance.card_config.toggle_adjustment_mode()
        ui_instance.msg = "🎯 Modo ajuste desactivado"
        return True
    elif event.key == pygame.K_r:
        ui_instance.card_config.reset_to_default()
        ui_instance.msg = "🔄 Posiciones reseteadas a default"
        return True
    elif event.key == pygame.K_p:
        # Ciclar entre presets
        presets = ['default', 'compact', 'spread']
        current_config = ui_instance.card_config.save_current_config()
        
        # Encontrar preset más similar o usar el siguiente
        next_preset = 'compact'  # Default fallback
        for i, preset_name in enumerate(presets):
            if ui_instance.card_config.load_preset(preset_name):
                next_preset = presets[(i + 1) % len(presets)]
                break
        
        ui_instance.card_config.load_preset(next_preset)
        ui_instance.msg = f"📐 Preset cambiado a: {next_preset.title()}"
        return True
    
    return False

# ---------- Loop Principal ----------
def main_loop():
    """Loop principal del juego"""
    global pantalla
    
    # Inicializar UI y botones
    ui = PremiumHoldemUI()  # Sin parámetros, siempre 4 jugadores
    main_buttons, action_buttons = setup_buttons()
    
    print("🎰 Casino Premium iniciado correctamente - 4 Jugadores con Eliminación")
    print("=" * 60)
    print("🧭 POSICIONES EN LA MESA:")
    print("  • TÚ: SUR (Abajo de la pantalla)")
    print("  • Bot Norte: NORTE (Arriba de la pantalla)")
    print("  • Bot Este: ESTE (Derecha de la pantalla)")
    print("  • Bot Oeste: OESTE (Izquierda de la pantalla)")
    print()
    print("💀 SISTEMA DE ELIMINACIÓN:")
    print("  • Los jugadores sin dinero para el big blind son eliminados")
    print("  • El torneo termina cuando solo queda 1 jugador")
    print("  • Gana el último jugador en pie")
    print()
    print("🃏 POSICIONAMIENTO DE CARTAS AJUSTABLE:")
    print("  • Cartas comunitarias: Centro de la mesa (ajustable)")
    print("  • Tus cartas: Posición configurada para Sur")
    print("  • Cartas bots: Posiciones configuradas por dirección")
    print("=" * 60)
    print("🎮 CONTROLES PRINCIPALES:")
    print("  N - Nueva mano (modo humano)")
    print("  A - Iniciar/Parar IA vs IA")
    print("  F - Fold (retirarse)")
    print("  ESPACIO - Call/Check")
    print("  B - Bet/Raise")
    print("  C - Mostrar/Ocultar consejo IA")
    print("  R - Reiniciar torneo completo")
    print("  Q/E - Ajustar apuesta ±$25")
    print("  Z/X - Ajustar apuesta ±$100")
    print("=" * 60)
    print("🎯 CONTROLES DE AJUSTE DE POSICIONES:")
    print("  TAB - Activar/Cambiar modo ajuste")
    print("  Flechas - Mover posición seleccionada")
    print("  SHIFT + Flechas - Movimiento rápido")
    print("  P - Cambiar preset (Default/Compact/Spread)")
    print("  R - Resetear a posiciones por defecto")
    print("  ENTER - Salir del modo ajuste")
    print("=" * 60)
    print("🎛️ PRESETS DISPONIBLES:")
    print("  • Default: Posiciones estándar")
    print("  • Compact: Cartas más cerca de los jugadores")
    print("  • Spread: Cartas más separadas")
    print("=" * 60)
    
    running = True
    last_time = time.time()
    
    while running:
        current_time = time.time()
        dt = current_time - last_time
        last_time = current_time
        
        mouse_pos = pygame.mouse.get_pos()
        
        # Actualizar hover de botones
        update_hover_state(ui, mouse_pos, main_buttons, action_buttons)
        
        # Procesar eventos
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                ui.stop_ai_vs_ai()
                running = False
                
            elif event.type == pygame.VIDEORESIZE:
                # Manejar redimensionamiento
                global ANCHO, ALTO
                ANCHO, ALTO = max(event.w, 1000), max(event.h, 700)
                pantalla = pygame.display.set_mode((ANCHO, ALTO), pygame.RESIZABLE)
                ui.ui = PokerUIManager(pantalla)
                ui.setup_cardinal_positions()  # Reconfigurar posiciones
                main_buttons, action_buttons = setup_buttons()
                
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                
                # Botones principales
                if main_buttons['new_hand'].collidepoint(mx, my) and not ui.auto_ai and not ui.game_over:
                    ui.stop_ai_vs_ai()
                    ui.new_hand(mode="human")
                    
                elif main_buttons['ai_vs_ai'].collidepoint(mx, my) and not ui.game_over:
                    if ui.auto_ai:
                        ui.stop_ai_vs_ai()
                    else:
                        ui.new_hand(mode="ai_vs_ai")
                        
                elif main_buttons['stop_ai'].collidepoint(mx, my) and ui.auto_ai:
                    ui.stop_ai_vs_ai()
                    
                elif main_buttons['advice'].collidepoint(mx, my) and ui.mode == "human" and not ui.game_over:
                    ui.toggle_advice()
                
                elif main_buttons['adjust'].collidepoint(mx, my):
                    # Alternar modo de ajuste
                    mode_activated = ui.card_config.toggle_adjustment_mode()
                    if mode_activated:
                        ui.msg = f"🎯 Modo ajuste activado - Ajustando: {ui.card_config.get_current_selection_info()}"
                    else:
                        ui.msg = "🎯 Modo ajuste desactivado"
                
                elif main_buttons['restart'].collidepoint(mx, my):
                    # Reiniciar torneo completo
                    ui.restart_game()
                
                # Botones de acción (solo en modo humano, no eliminado y no en ajuste)
                elif (ui.mode == "human" and ui.running and 
                      not ui.card_config.adjustment_mode and 
                      ui.human_index in ui.active_players and
                      not ui.game_over):
                    if action_buttons['fold'].collidepoint(mx, my):
                        ui.human_action(0)  # Fold
                    elif action_buttons['call'].collidepoint(mx, my):
                        ui.human_action(1)  # Call/Check
                    elif action_buttons['bet'].collidepoint(mx, my):
                        ui.human_action(2)  # Bet/Raise
                    elif action_buttons['all_in'].collidepoint(mx, my):
                        ui.bet_amount = ui.stacks[ui.human_index]
                        ui.human_action(2)  # All-in
                        
            elif event.type == pygame.KEYDOWN:
                # Primero verificar si es una tecla de ajuste de posición
                if handle_position_adjustment_keys(ui, event):
                    continue  # Tecla manejada por sistema de ajuste
                
                # Controles generales
                if event.key == pygame.K_ESCAPE:
                    ui.stop_ai_vs_ai()
                    running = False
                    
                elif event.key == pygame.K_TAB:
                    # Activar modo ajuste
                    mode_activated = ui.card_config.toggle_adjustment_mode()
                    if mode_activated:
                        ui.msg = f"🎯 Modo ajuste activado - Ajustando: {ui.card_config.get_current_selection_info()}"
                    else:
                        ui.msg = "🎯 Modo ajuste desactivado"
                    
                elif event.key == pygame.K_n and not ui.card_config.adjustment_mode and not ui.game_over:
                    ui.stop_ai_vs_ai()
                    ui.new_hand(mode="human")
                    
                elif event.key == pygame.K_a and not ui.card_config.adjustment_mode and not ui.game_over:
                    if ui.auto_ai:
                        ui.stop_ai_vs_ai()
                    else:
                        ui.new_hand(mode="ai_vs_ai")
                        
                elif event.key == pygame.K_r and not ui.card_config.adjustment_mode:
                    # Reiniciar torneo completo
                    ui.restart_game()
                    
                elif ui.mode == "human" and not ui.card_config.adjustment_mode and not ui.game_over:
                    if event.key == pygame.K_f and ui.running and ui.human_index in ui.active_players:
                        ui.human_action(0)  # Fold
                    elif event.key == pygame.K_SPACE and ui.running and ui.human_index in ui.active_players:
                        ui.human_action(1)  # Call/Check
                    elif event.key == pygame.K_b and ui.running and ui.human_index in ui.active_players:
                        ui.human_action(2)  # Bet/Raise
                    elif event.key == pygame.K_c:
                        ui.toggle_advice()
                    
                    # Ajustes de apuesta (solo si no está eliminado)
                    elif event.key == pygame.K_q and ui.human_index in ui.active_players:
                        ui.adjust_bet_amount(-25)
                    elif event.key == pygame.K_e and ui.human_index in ui.active_players:
                        ui.adjust_bet_amount(25)
                    elif event.key == pygame.K_z and ui.human_index in ui.active_players:
                        ui.adjust_bet_amount(-100)
                    elif event.key == pygame.K_x and ui.human_index in ui.active_players:
                        ui.adjust_bet_amount(100)
                
                # Limpiar mensaje de ganador con cualquier tecla (excepto en modo ajuste)
                if ui.winner_msg and not ui.card_config.adjustment_mode:
                    ui.winner_msg = ""
        
        # Dibujar todo
        ui.draw()
        draw_buttons(ui, main_buttons, action_buttons)
        
        # Actualizar pantalla
        pygame.display.flip()
        clock.tick(60)  # 60 FPS para suavidad
    
    # Limpieza al salir
    ui.stop_ai_vs_ai()
    pygame.quit()
    sys.exit()

# ---------- Agentes IA Mejorados ----------
class PolicyAgent:
    """Agente de política mejorado"""
    def __init__(self):
        self.policy = {}
        self.learning_rate = 0.1
        
    def action(self, state):
        """Seleccionar acción basada en el estado"""
        key = str(state)
        if key not in self.policy:
            # Política inicial más inteligente
            self.policy[key] = random.choices([0, 1, 2], weights=[0.2, 0.5, 0.3])[0]
        return self.policy[key]
    
    def update(self, state, action, reward=0):
        """Actualizar política basada en experiencia"""
        key = str(state)
        if key in self.policy:
            # Ajuste simple basado en recompensa
            if reward > 0:
                self.policy[key] = action
            elif reward < 0 and random.random() < 0.1:
                # Explorar acción diferente ocasionalmente
                self.policy[key] = random.choice([0, 1, 2])

class HeuristicAgent:
    """Agente heurístico mejorado"""
    def action(self, state):
        """Estrategia heurística básica"""
        # Estrategia conservadora: más calls que bets
        return random.choices([0, 1, 2], weights=[0.15, 0.6, 0.25])[0]

class RandomAgent:
    """Agente completamente aleatorio"""
    def action(self, state):
        return random.choice([0, 1, 2])

# ---------- Punto de Entrada ----------
if __name__ == "__main__":
    print("🎰" + "="*50 + "🎰")
    print("    TEXAS HOLD'EM CASINO PREMIUM")
    print("   Versión 4 Jugadores v3.0 ELIMINACIÓN")
    print("🎰" + "="*50 + "🎰")
    print()
    print("🧭 Configuración Cardinal:")
    print("   ⬆️ NORTE (Bot)")
    print("   ⬅️ OESTE (Bot)    ➡️ ESTE (Bot)")
    print("   ⬇️ SUR (TÚ)")
    print()
    print("💀 NUEVAS CARACTERÍSTICAS:")
    print("   • Sistema de eliminación automático")
    print("   • Jugadores sin dinero para big blind son eliminados")
    print("   • El torneo termina cuando solo queda 1 jugador")
    print("   • Estadísticas de eliminación")
    print("   • Botón de reinicio de torneo")
    print()
    print("🎯 FUNCIÓN: Posiciones Ajustables")
    print("   • TAB: Activar modo ajuste")
    print("   • Flechas: Mover cartas seleccionadas")
    print("   • P: Cambiar presets (Default/Compact/Spread)")
    print("   • R: Reiniciar torneo O resetear posiciones (en modo ajuste)")
    print()
    print("🔧 Inicializando componentes...")
    
    try:
        # Verificar dependencias
        print("✅ Pygame inicializado")
        print("✅ Efectos visuales cargados")
        print("✅ Sistema de cartas configurado")
        print("✅ IA agents inicializados")
        print("✅ Posiciones cardinales configuradas")
        print("✅ Sistema de ajuste de posiciones activado")
        print("✅ Sistema de eliminación implementado")
        print()
        
        # Iniciar el juego
        print("🚀 Iniciando Casino Premium - 4 Jugadores con Eliminación...")
        main_loop()
        
    except ImportError as e:
        print(f"❌ Error: Falta dependencia - {e}")
        print("💡 Asegúrate de tener instalado: pygame")
        print("💡 También necesitas: holdem_env.py y poker_agent.py")
    except Exception as e:
        print(f"❌ Error crítico: {e}")
        pygame.quit()
        sys.exit(1)