import pygame, sys, time, os, threading
from holdem_env import HoldemEnv
from poker_agent import PolicyAgent, HeuristicAgent, RandomAgent

RUTA_CARTAS = r"E:\Sistemas\CardBlack\CardBlack\cards"

pygame.init()

# Sistema responsive - detectar tamaño de pantalla
info = pygame.display.Info()
SCREEN_W, SCREEN_H = info.current_w, info.current_h
print(f"Resolución detectada: {SCREEN_W}x{SCREEN_H}")

# Ajustar tamaño según la pantalla
if SCREEN_W >= 1920:  # Pantalla grande
    ANCHO, ALTO = 1600, 1000
    FONT_SIZE, FONT_L_SIZE = 24, 32
    CARD_SCALE = 1.2
elif SCREEN_W >= 1366:  # Pantalla mediana
    ANCHO, ALTO = 1200, 800
    FONT_SIZE, FONT_L_SIZE = 20, 28
    CARD_SCALE = 1.0
else:  # Pantalla pequeña
    ANCHO, ALTO = min(SCREEN_W-100, 1024), min(SCREEN_H-100, 768)
    FONT_SIZE, FONT_L_SIZE = 18, 24
    CARD_SCALE = 0.8

# Ajustar el tamaño de las cartas según la escala
CARD_W, CARD_H = int(90 * CARD_SCALE), int(140 * CARD_SCALE)

pantalla = pygame.display.set_mode((ANCHO, ALTO))
pygame.display.set_caption("Texas Hold'em - Pygame")
clock = pygame.time.Clock()
FONT = pygame.font.SysFont("Arial", FONT_SIZE)
FONT_L = pygame.font.SysFont("Arial", FONT_L_SIZE, bold=True)
FONT_XL = pygame.font.SysFont("Arial", int(FONT_L_SIZE * 1.5), bold=True)

BG = (6, 100, 40)

cache = {}

def try_load_image(names):
    for nm in names:
        for ext in (".png", ".jpg", ".bmp"):
            path = os.path.join(RUTA_CARTAS, nm + ext)
            if os.path.exists(path):
                try:
                    img = pygame.image.load(path).convert_alpha()
                    img = pygame.transform.smoothscale(img, (CARD_W, CARD_H))
                    return img
                except Exception as e:
                    print("Error loading:", path, e)
    return None

def get_card_image(card):
    r, s = card
    rstr = {14:"A",13:"K",12:"Q",11:"J"}.get(r, str(r))
    candidates = [
        f"{rstr}_{s}", f"{rstr}{s}", f"{r}_{s}", f"{r}{s}",
        f"{rstr}_{s.lower()}", f"{rstr}{s[0]}"
    ]
    eng = {"Corazones":"Hearts","Diamantes":"Diamonds","Trebol":"Clubs","Copas":"Spades"}
    if s in eng:
        candidates += [f"{rstr}_{eng[s]}", f"{rstr}{eng[s]}", f"{rstr}{eng[s][0]}"]
    key = f"{rstr}_{s}"
    if key in cache:
        return cache[key]
    img = try_load_image(candidates)
    if img is None:
        surf = pygame.Surface((CARD_W, CARD_H), pygame.SRCALPHA)
        surf.fill((250,250,250))
        pygame.draw.rect(surf, (0,0,0), surf.get_rect(), 2, border_radius=12)
        t = FONT.render(rstr, True, (0,0,0))
        surf.blit(t, (8,8))
        cache[key] = surf
        return surf
    cache[key] = img
    return img

def text(t,x,y,clr=(255,255,255), font=FONT):
    pantalla.blit(font.render(t, True, clr), (x,y))

def draw_button(rect, text_str, color, text_color=(0,0,0), font=FONT):
    pygame.draw.rect(pantalla, color, rect, border_radius=8)
    pygame.draw.rect(pantalla, (0,0,0), rect, 2, border_radius=8)
    text_surf = font.render(text_str, True, text_color)
    text_rect = text_surf.get_rect(center=rect.center)
    pantalla.blit(text_surf, text_rect)

class HoldemUI:
    def __init__(self, n_players=4):
        self.n = n_players
        self.env = HoldemEnv(n_players=self.n)
        self.stacks = [1000 for _ in range(self.n)]  # Stack inicial de $1000
        self.human_index = 0
        self.reset_hand()
        self.mode = "menu"
        self.auto_ai = False
        self.ai_thread = None
        self.bet_amount = 50  # Cantidad de apuesta por defecto
        self.game_history = []  # Historial de partidas
        
        # Sistema de apuestas mejorado
        self.current_bet = 0
        self.min_bet = 10
        self.big_blind = 20
        self.small_blind = 10
        
        # Sistema de consejos de IA
        self.ai_advisor = PolicyAgent()  # IA consejera independiente
        self.show_advice = False
        self.current_advice = ""

        # Agentes de IA
        self.agents = [PolicyAgent() for _ in range(self.n)]

        # Posiciones adaptativas según el tamaño de pantalla
        self.setup_positions()

        self.msg = ""
        self.running = False
        self.winner_msg = ""
        self.hand_number = 0

    def setup_positions(self):
        """Configurar posiciones de jugadores según tamaño de pantalla"""
        center_x, center_y = ANCHO//2, ALTO//2
        
        if self.n == 4:
            self.posiciones_jugadores = {
                0: (center_x, ALTO - int(30 * CARD_SCALE)),           # Humano abajo-centro
                1: (center_x, int(80 * CARD_SCALE)),                   # Bot arriba-centro
                2: (ANCHO - int(200 * CARD_SCALE), center_y),          # Bot derecha-centro
                3: (int(200 * CARD_SCALE), center_y),                  # Bot izquierda-centro
            }
        else:
            # Distribuir en círculo para más jugadores
            import math
            for i in range(self.n):
                angle = (2 * math.pi * i) / self.n - math.pi/2
                radius = min(ANCHO, ALTO) // 3
                x = center_x + int(radius * math.cos(angle))
                y = center_y + int(radius * math.sin(angle))
                self.posiciones_jugadores[i] = (x, y)

    def reset_hand(self):
        self.env.reset()
        self.msg = "Nueva mano: presiona 'New Hand'."
        self.running = False
        self.current_bet = 0
        self.winner_msg = ""

    def new_hand(self, mode="human"):
        # Verificar que los jugadores tengan dinero suficiente
        active_players = [i for i in range(self.n) if self.stacks[i] >= self.big_blind]
        if len(active_players) < 2:
            self.msg = "¡Juego terminado! No hay suficientes jugadores con dinero."
            return
            
        self.hand_number += 1
        self.mode = mode
        self.env.reset()
        self.running = True
        self.current_bet = self.big_blind
        self.winner_msg = ""
        self.msg = f"Mano #{self.hand_number} iniciada"
        
        # Cobrar blinds
        self.collect_blinds()
        
        if mode == "ai_vs_ai":
            if self.ai_thread is None or not self.ai_thread.is_alive():
                self.auto_ai = True
                self.ai_thread = threading.Thread(target=self.run_ai_vs_ai, daemon=True)
                self.ai_thread.start()

    def collect_blinds(self):
        """Cobrar small blind y big blind"""
        if self.n >= 2:
            # Small blind (jugador 1)
            sb_amount = min(self.small_blind, self.stacks[1])
            self.stacks[1] -= sb_amount
            # Big blind (jugador 2 o 0 si solo hay 2 jugadores)
            bb_player = 2 if self.n > 2 else 0
            bb_amount = min(self.big_blind, self.stacks[bb_player])
            self.stacks[bb_player] -= bb_amount
            self.env.pot += sb_amount + bb_amount

    def new_hand_internal(self):
        """Método interno para iniciar mano sin threading"""
        self.mode = "ai_vs_ai"
        self.env.reset()
        self.running = True
        self.msg = f"Mano #{self.hand_number} iniciada (IA vs IA)"
        self.collect_blinds()

    def stop_ai_vs_ai(self):
        """Método para parar el modo IA vs IA"""
        self.auto_ai = False
        self.msg = "Modo IA vs IA detenido"
        if self.ai_thread and self.ai_thread.is_alive():
            self.ai_thread.join(timeout=1)

    def get_ai_advice(self):
        """Obtener consejo de la IA para el jugador humano"""
        if not self.running or self.env.current_player != self.human_index:
            return "No es tu turno para pedir consejo."
        
        try:
            obs = self.env._get_obs(self.human_index)
            suggested_action = self.ai_advisor.action(obs)
            
            # Convertir la acción sugerida a texto descriptivo
            action_names = {
                0: "FOLD - La IA sugiere retirarse. Las cartas no son prometedoras.",
                1: "CALL/CHECK - La IA sugiere igualar o hacer check. Situación neutral.",
                2: f"BET/RAISE - La IA sugiere apostar ${self.bet_amount}. ¡Buena mano!"
            }
            
            # Análisis adicional basado en las cartas
            hand_strength = self.analyze_hand_strength()
            advice = action_names.get(suggested_action, "Acción desconocida")
            advice += f"\n\nAnálisis: {hand_strength}"
            advice += f"\nPot actual: ${self.env.pot}"
            advice += f"\nApuesta para igualar: ${self.current_bet}"
            
            return advice
        except Exception as e:
            return f"Error al obtener consejo: {str(e)}"
    
    def analyze_hand_strength(self):
        """Analizar la fuerza de la mano del jugador"""
        try:
            hand = self.env.hands[self.human_index]
            board = self.env.board
            
            # Análisis básico de la mano
            if len(hand) != 2:
                return "Mano incompleta"
            
            card1, card2 = hand
            rank1, suit1 = card1
            rank2, suit2 = card2
            
            analysis = []
            
            # Pares en la mano
            if rank1 == rank2:
                if rank1 >= 10:
                    analysis.append("¡Par alto en mano!")
                else:
                    analysis.append("Par bajo en mano")
            
            # Cartas altas
            high_cards = [r for r in [rank1, rank2] if r >= 10]
            if len(high_cards) == 2:
                analysis.append("Dos cartas altas")
            elif len(high_cards) == 1:
                analysis.append("Una carta alta")
            
            # Suited
            if suit1 == suit2:
                analysis.append("Cartas del mismo palo")
            
            # Conectores
            if abs(rank1 - rank2) == 1:
                analysis.append("Cartas conectadas")
            elif abs(rank1 - rank2) <= 4:
                analysis.append("Semi-conectadas")
            
            # Análisis del board si hay cartas comunitarias
            if board:
                analysis.append(f"{len(board)} carta(s) comunitaria(s) en mesa")
            
            return " | ".join(analysis) if analysis else "Mano neutra"
            
        except Exception:
            return "No se puede analizar la mano"

    def adjust_bet_amount(self, change):
        """Ajustar cantidad de apuesta"""
        self.bet_amount = max(self.min_bet, min(self.stacks[self.human_index], self.bet_amount + change))
    
    def toggle_advice(self):
        """Mostrar/ocultar consejo de IA"""
        if self.mode == "human":
            self.show_advice = not self.show_advice
            if self.show_advice:
                self.current_advice = self.get_ai_advice()
            else:
                self.current_advice = ""

    def draw_table(self):
        pantalla.fill(BG)
        
        # Mesa central
        cx, cy = ANCHO//2, ALTO//2
        table_rect = pygame.Rect(cx - int(300 * CARD_SCALE), cy - int(200 * CARD_SCALE), 
                                int(600 * CARD_SCALE), int(400 * CARD_SCALE))
        pygame.draw.ellipse(pantalla, (0, 80, 0), table_rect)
        pygame.draw.ellipse(pantalla, (255, 255, 255), table_rect, 3)
        
        # Información del pot y mano
        pot_text = f"POT: ${self.env.pot}"
        hand_text = f"Mano #{self.hand_number}"
        text(pot_text, cx - len(pot_text) * FONT_L_SIZE//4, cy - int(160 * CARD_SCALE), (255,255,100), FONT_XL)
        text(hand_text, cx - len(hand_text) * FONT_SIZE//4, cy - int(130 * CARD_SCALE), (200,200,200), FONT)
        
        # Cartas comunitarias
        board = self.env.board
        if board:
            total_width = len(board) * (CARD_W + 10) - 10
            startx = cx - total_width // 2
            for i, c in enumerate(board):
                img = get_card_image(c)
                pantalla.blit(img, (startx + i*(CARD_W+10), cy - CARD_H//2))

        # Información de apuesta actual
        if self.current_bet > 0:
            bet_text = f"Apuesta actual: ${self.current_bet}"
            text(bet_text, cx - len(bet_text) * FONT_SIZE//4, cy + int(100 * CARD_SCALE), (255,200,200), FONT)

        self.draw_players()
        self.draw_game_info()

    def draw_players(self):
        """Dibujar información de jugadores"""
        seat_w = int((CARD_W + 40) * CARD_SCALE)
        seat_h = int(80 * CARD_SCALE)

        for i in range(self.n):
            x, y = self.posiciones_jugadores.get(i, (50 + i*150, ALTO - 150))
            
            # Rectángulo del jugador
            rect = pygame.Rect(int(x - seat_w/2), int(y - seat_h/2), seat_w, seat_h)
            
            # Color según estado
            if self.stacks[i] <= 0:
                color_rect = (60, 60, 60)  # Sin dinero
            elif self.running and self.env.current_player == i:
                color_rect = (200, 100, 100)  # Turno actual
            else:
                color_rect = (80, 120, 80)  # Normal
            
            pygame.draw.rect(pantalla, color_rect, rect, border_radius=12)
            pygame.draw.rect(pantalla, (255, 255, 255), rect, 2, border_radius=12)

            # Información del jugador
            name = "TÚ" if i == self.human_index else f"BOT {i}"
            stack_text = f"${self.stacks[i]}"
            
            # Estado del jugador
            status = ""
            if self.stacks[i] <= 0:
                status = " (SIN DINERO)"
            elif hasattr(self.env, 'folded') and i in self.env.folded:
                status = " (FOLD)"
            
            text(name + status, rect.x + 8, rect.y + 8, (255,255,255), FONT)
            text(stack_text, rect.x + 8, rect.y + 28, (255,255,200), FONT)
            
            # Mostrar apuesta actual del jugador si la hay
            if hasattr(self.env, 'current_bets') and i in self.env.current_bets:
                bet_text = f"Apuesta: ${self.env.current_bets[i]}"
                text(bet_text, rect.x + 8, rect.y + 48, (200,255,200), pygame.font.SysFont("Arial", FONT_SIZE-2))

            # Cartas del jugador
            self.draw_player_cards(i, rect, y)

    def draw_player_cards(self, player_i, rect, y_pos):
        """Dibujar cartas de un jugador"""
        for j, card in enumerate(self.env.hands[player_i]):
            # Lógica para mostrar cartas:
            # - Siempre mostrar cartas del humano
            # - Mostrar cartas de bots solo en showdown o cuando el juego no está corriendo
            # - En modo IA vs IA, mostrar todas las cartas
            mostrar_carta = (
                player_i == self.human_index or 
                self.env.round_stage == "showdown" or
                not self.running or
                self.mode == "ai_vs_ai"
            )
            
            if mostrar_carta:
                img = get_card_image(card)
            else:
                # Carta boca abajo
                back = pygame.Surface((CARD_W, CARD_H))
                back.fill((30, 30, 120))
                pygame.draw.rect(back, (200, 200, 200), back.get_rect(), 2, border_radius=8)
                pattern_surf = pygame.Surface((20, 20))
                pattern_surf.fill((50, 50, 150))
                for px in range(0, CARD_W, 25):
                    for py in range(0, CARD_H, 25):
                        back.blit(pattern_surf, (px, py))
                img = back

            # Posición de la carta
            card_x = rect.x + j * (CARD_W // 2 + 5)
            card_y = rect.y - CARD_H - 15 if y_pos > ALTO//2 else rect.y + rect.height + 15
            pantalla.blit(img, (card_x, card_y))

    def draw_game_info(self):
        """Dibujar información del juego"""
        info_y = 20
        text(self.msg, 20, ALTO - 80, (255,255,255), FONT)
        text(f"Etapa: {self.env.round_stage}", 20, ALTO - 60, (200,200,255), FONT)
        
        if self.winner_msg:
            # Mensaje de ganador destacado
            winner_rect = pygame.Rect(ANCHO//2 - 200, ALTO//2 - 50, 400, 100)
            pygame.draw.rect(pantalla, (0, 100, 0), winner_rect, border_radius=15)
            pygame.draw.rect(pantalla, (255, 255, 255), winner_rect, 3, border_radius=15)
            text("🏆 " + self.winner_msg, winner_rect.x + 20, winner_rect.y + 20, (255,255,255), FONT_L)
            text("Presiona cualquier tecla para continuar", winner_rect.x + 20, winner_rect.y + 50, (200,255,200), FONT)
        
        # Indicador de modo IA vs IA
        if self.auto_ai:
            text("🤖 MODO: IA vs IA ACTIVO", 20, 20, (255, 255, 0), FONT_L)
        
        # Información de apuestas para el jugador humano
        if self.mode == "human" and self.running:
            bet_info = f"Apuesta seleccionada: ${self.bet_amount} (±10: Q/E, ±50: Z/D) | Consejo: C"
            text(bet_info, 20, ALTO - 120, (255,200,255), FONT)
        
        # Mostrar consejo de IA si está activado
        if self.show_advice and self.current_advice and self.mode == "human":
            # Fondo para el consejo
            advice_rect = pygame.Rect(ANCHO//2 - 250, 100, 500, 150)
            pygame.draw.rect(pantalla, (0, 0, 80), advice_rect, border_radius=10)
            pygame.draw.rect(pantalla, (255, 255, 255), advice_rect, 2, border_radius=10)
            
            # Título del consejo
            text("🤖 CONSEJO DE IA:", advice_rect.x + 10, advice_rect.y + 10, (255, 255, 100), FONT_L)
            
            # Dividir el consejo en líneas
            lines = self.current_advice.split('\n')
            for i, line in enumerate(lines[:6]):  # Máximo 6 líneas
                text(line, advice_rect.x + 10, advice_rect.y + 35 + i * 18, (255, 255, 255), FONT)
            
            # Instrucción para cerrar
            text("Presiona C para cerrar", advice_rect.x + 10, advice_rect.y + 125, (200, 200, 255), FONT)

    def human_action(self, action):
        if not self.running:
            self.msg = "Inicia una nueva mano primero"
            return
        
        cur = self.env.current_player
        if cur != self.human_index:
            self.msg = "No es tu turno"
            return
        
        # Verificar si el jugador tiene dinero suficiente
        if action == 2 and self.stacks[self.human_index] < self.bet_amount:  # Bet/Raise
            self.msg = f"No tienes suficiente dinero para apostar ${self.bet_amount}"
            return
        
        try:
            # Procesar la apuesta antes del step del environment
            if action == 2:  # Bet/Raise
                bet_amount = min(self.bet_amount, self.stacks[self.human_index])
                self.stacks[self.human_index] -= bet_amount
                self.env.pot += bet_amount
                self.current_bet = max(self.current_bet, bet_amount)
                self.msg = f"Apostaste ${bet_amount}"
            elif action == 1:  # Call
                call_amount = min(self.current_bet, self.stacks[self.human_index])
                if call_amount > 0:
                    self.stacks[self.human_index] -= call_amount
                    self.env.pot += call_amount
                    self.msg = f"Igualaste con ${call_amount}"
                else:
                    self.msg = "Check"
            elif action == 0:  # Fold
                self.msg = "Te retiraste"
            
            obs, reward, done, info = self.env.step(cur, action)
            
        except Exception as e:
            self.msg = f"Error: {str(e)}"
            return

        if done:
            self.handle_hand_end(info)
        else:
            nextp = self.env.current_player
            if self.mode == "human" and nextp != self.human_index:
                threading.Thread(target=self.bot_act, args=(nextp,), daemon=True).start()

    def bot_act(self, bot_index):
        if not self.running or self.stacks[bot_index] <= 0:
            return

        time.sleep(5.0)  # 5 segundos de pensamiento

        obs = self.env._get_obs(bot_index)
        act = self.agents[bot_index].action(obs)
        
        try:
            # Procesar apuesta del bot
            if act == 2:  # Bet/Raise
                bot_bet = min(50, self.stacks[bot_index])  # Bot apuesta $50 o lo que tenga
                self.stacks[bot_index] -= bot_bet
                self.env.pot += bot_bet
                self.current_bet = max(self.current_bet, bot_bet)
                self.msg = f"Bot {bot_index} apuesta ${bot_bet}"
            elif act == 1:  # Call
                call_amount = min(self.current_bet, self.stacks[bot_index])
                if call_amount > 0:
                    self.stacks[bot_index] -= call_amount
                    self.env.pot += call_amount
                    self.msg = f"Bot {bot_index} iguala con ${call_amount}"
                else:
                    self.msg = f"Bot {bot_index} hace check"
            elif act == 0:  # Fold
                self.msg = f"Bot {bot_index} se retira"
            
            obs, reward, done, info = self.env.step(bot_index, act)
            
        except Exception as e:
            self.msg = f"Error Bot {bot_index}: {str(e)}"
            return

        if done:
            self.handle_hand_end(info)
        else:
            nextp = self.env.current_player
            if self.mode == "human" and nextp != self.human_index:
                threading.Thread(target=self.bot_act, args=(nextp,), daemon=True).start()

    def handle_hand_end(self, info):
        """Manejar el final de una mano"""
        self.running = False
        
        # Determinar ganadores y distribuir el pot
        if "winners" in info:
            winners = info["winners"]
            pot_share = self.env.pot // len(winners)
            for winner in winners:
                self.stacks[winner] += pot_share
            self.winner_msg = f"Ganadores: {[f'Jugador {w}' if w != self.human_index else 'TÚ' for w in winners]} - ${pot_share} c/u"
        elif "winner" in info:
            winner = info["winner"]
            self.stacks[winner] += self.env.pot
            winner_name = "TÚ" if winner == self.human_index else f"Bot {winner}"
            self.winner_msg = f"Ganador: {winner_name} - ${self.env.pot}"
        
        # Guardar en historial
        self.game_history.append({
            'hand': self.hand_number,
            'winner': info.get("winner", info.get("winners", "Empate")),
            'pot': self.env.pot
        })
        
        # Reset pot
        self.env.pot = 0

    def run_ai_vs_ai(self):
        while self.auto_ai:
            if not self.running:
                self.new_hand_internal()
            
            while self.running and self.auto_ai:
                cur = self.env.current_player
                if self.stacks[cur] <= 0:  # Skip si no tiene dinero
                    self.env.step(cur, 0)  # Fold automático
                    continue
                    
                time.sleep(5.0)  # 5 segundos de pensamiento IA vs IA
                
                try:
                    obs = self.env._get_obs(cur)
                    act = self.agents[cur].action(obs)
                    
                    # Procesar apuesta de IA
                    if act == 2:  # Bet
                        bot_bet = min(50, self.stacks[cur])
                        self.stacks[cur] -= bot_bet
                        self.env.pot += bot_bet
                        self.current_bet = max(self.current_bet, bot_bet)
                    elif act == 1:  # Call
                        call_amount = min(self.current_bet, self.stacks[cur])
                        self.stacks[cur] -= call_amount
                        self.env.pot += call_amount
                    
                    _, _, done, info = self.env.step(cur, act)
                    
                    action_names = ["fold", "call/check", "bet/raise"]
                    self.msg = f"Bot {cur} hace {action_names[act]}"
                    
                    if done:
                        self.handle_hand_end(info)
                        break
                        
                except Exception as e:
                    self.msg = f"Error en IA vs IA: {str(e)}"
                    self.running = False
                    break
            
            if self.auto_ai:
                time.sleep(3)  # Pausa entre manos

    def draw(self):
        self.draw_table()

# Configurar botones adaptativos
ui = HoldemUI(n_players=4)

# Botones principales - adaptados al tamaño de pantalla
button_width = int(180 * CARD_SCALE)
button_height = int(35 * CARD_SCALE)
button_spacing = int(10 * CARD_SCALE)
buttons_start_y = ALTO - int(200 * CARD_SCALE)

btn_new = pygame.Rect(ANCHO - button_width - 20, buttons_start_y, button_width, button_height)
btn_ai = pygame.Rect(ANCHO - button_width - 20, buttons_start_y + button_height + button_spacing, button_width, button_height)
btn_stop_ai = pygame.Rect(ANCHO - button_width - 20, buttons_start_y + 2*(button_height + button_spacing), button_width, button_height)

# Botones de acción - adaptados
action_button_width = int(100 * CARD_SCALE)
action_button_height = int(40 * CARD_SCALE)
action_y = ALTO - int(60 * CARD_SCALE)

btn_fold = pygame.Rect(20, action_y, action_button_width, action_button_height)
btn_call = pygame.Rect(20 + action_button_width + 10, action_y, action_button_width, action_button_height)
btn_bet = pygame.Rect(20 + 2*(action_button_width + 10), action_y, action_button_width, action_button_height)
btn_all_in = pygame.Rect(20 + 3*(action_button_width + 10), action_y, action_button_width, action_button_height)
btn_advice = pygame.Rect(20 + 4*(action_button_width + 10), action_y, action_button_width, action_button_height)

def draw_buttons():
    # Botones de control del juego
    new_color = (200,200,200) if not ui.auto_ai else (150,150,150)
    draw_button(btn_new, "Nueva Mano", new_color, font=FONT)
    
    ai_color = (100, 240, 100) if ui.auto_ai else (180, 180, 240)
    ai_text = "IA ACTIVO" if ui.auto_ai else "Iniciar IA vs IA"
    draw_button(btn_ai, ai_text, ai_color, font=FONT)
    
    stop_color = (240, 100, 100) if ui.auto_ai else (150, 150, 150)
    draw_button(btn_stop_ai, "Parar IA", stop_color, font=FONT)
    
    # Botones de acción (solo en modo humano)
    if ui.mode == "human" and ui.running:
        draw_button(btn_fold, "Fold", (220,100,100), font=FONT)
        
        call_text = f"Call ${ui.current_bet}" if ui.current_bet > 0 else "Check"
        draw_button(btn_call, call_text, (100,200,100), font=FONT)
        
        draw_button(btn_bet, f"Bet ${ui.bet_amount}", (200,200,100), font=FONT)
        
        all_in_amount = ui.stacks[ui.human_index]
        draw_button(btn_all_in, f"All-in", (255,150,50), font=FONT)
        
        # Botón de consejo
        advice_color = (100, 255, 100) if ui.show_advice else (100, 100, 255)
        advice_text = "Ocultar" if ui.show_advice else "Consejo"
        draw_button(btn_advice, advice_text, advice_color, font=FONT)

def main_loop():
    running = True
    while running:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                ui.auto_ai = False
                running = False
            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                mx, my = e.pos
                if btn_new.collidepoint(mx,my):
                    ui.stop_ai_vs_ai()
                    ui.new_hand(mode="human")
                elif btn_ai.collidepoint(mx,my):
                    if not ui.auto_ai:
                        ui.auto_ai = True
                        ui.ai_thread = threading.Thread(target=ui.run_ai_vs_ai, daemon=True)
                        ui.ai_thread.start()
                elif btn_stop_ai.collidepoint(mx,my):
                    ui.stop_ai_vs_ai()
                elif ui.mode == "human" and ui.running:
                    if btn_fold.collidepoint(mx,my):
                        ui.human_action(0)
                    elif btn_call.collidepoint(mx,my):
                        ui.human_action(1)
                    elif btn_bet.collidepoint(mx,my):
                        ui.human_action(2)
                    elif btn_all_in.collidepoint(mx,my):
                        ui.bet_amount = ui.stacks[ui.human_index]
                        ui.human_action(2)
                    elif btn_advice.collidepoint(mx,my):
                        ui.toggle_advice()
            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_n:
                    ui.stop_ai_vs_ai()
                    ui.new_hand(mode="human")
                elif e.key == pygame.K_a:
                    if not ui.auto_ai:
                        ui.auto_ai = True
                        ui.ai_thread = threading.Thread(target=ui.run_ai_vs_ai, daemon=True)
                        ui.ai_thread.start()
                elif e.key == pygame.K_s:
                    ui.stop_ai_vs_ai()
                elif ui.mode == "human":
                    # Controles de apuesta
                    if e.key == pygame.K_q:
                        ui.adjust_bet_amount(-10)
                    elif e.key == pygame.K_e:
                        ui.adjust_bet_amount(10)
                    elif e.key == pygame.K_z:  # Cambié A por Z para evitar conflicto
                        ui.adjust_bet_amount(-50)
                    elif e.key == pygame.K_d:
                        ui.adjust_bet_amount(50)
                    elif e.key == pygame.K_SPACE and ui.running:
                        ui.human_action(1)  # Call/Check con espacio
                    elif e.key == pygame.K_f and ui.running:
                        ui.human_action(0)  # Fold con F
                    elif e.key == pygame.K_b and ui.running:
                        ui.human_action(2)  # Bet con B
                    elif e.key == pygame.K_c:
                        ui.toggle_advice()  # Consejo con C
                # Limpiar mensaje de ganador
                if ui.winner_msg:
                    ui.winner_msg = ""

        ui.draw()
        draw_buttons()
        pygame.display.flip()
        clock.tick(60)  # Aumentar FPS para mejor responsividad
    
    # Cleanup al salir
    ui.auto_ai = False
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    print("=== TEXAS HOLD'EM POKER ===")
    print(f"Resolución: {ANCHO}x{ALTO}")
    print("Controles:")
    print("  N - Nueva mano")
    print("  A - Iniciar IA vs IA")  
    print("  S - Parar IA vs IA")
    print("  F - Retirarse")
    print("  ESPACIO - Call/Check")
    print("  B - Apostar")
    print("  C - Pedir consejo a la IA")
    print("  Q/E - Ajustar apuesta ±$10")
    print("  Z/D - Ajustar apuesta ±$50")
    print("")
    print("NUEVAS CARACTERÍSTICAS:")
    print("  🤖 Consejo de IA disponible en modo humano")
    print("  👁️ Cartas de bots ocultas hasta el final")
    print("  ⏱️ Tiempo de pensamiento: 5 segundos")
    print("========================")
    main_loop()