import pygame, sys, time, os, threading
from holdem_env import HoldemEnv
from poker_agent import HeuristicAgent, PolicyAgent, card_to_name, RandomAgent  # según tengas

RUTA_CARTAS = r"E:\Sistemas\CardBlack\CardBlack\cards"

pygame.init()
ANCHO, ALTO = 1200, 800
pantalla = pygame.display.set_mode((ANCHO, ALTO))
pygame.display.set_caption("Texas Hold'em - Pygame")
clock = pygame.time.Clock()
FONT = pygame.font.SysFont("Arial", 20)
FONT_L = pygame.font.SysFont("Arial", 28, bold=True)

BG = (6, 100, 40)
CARD_W, CARD_H = 90, 140

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

def create_rounded_card_image(img, radius=12):
    rounded_surf = pygame.Surface((CARD_W, CARD_H), pygame.SRCALPHA)  # soporte transparencia
    rect = pygame.Rect(0, 0, CARD_W, CARD_H)
    # Dibujar fondo blanco con bordes redondeados
    pygame.draw.rect(rounded_surf, (255, 255, 255, 255), rect, border_radius=radius)
    # Pintar la imagen original dentro, respetando los bordes redondeados
    rounded_surf.blit(img, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    return rounded_surf

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

    img = create_rounded_card_image(img, radius=12)
    cache[key] = img
    return img

def text(t,x,y,clr=(255,255,255), font=FONT):
    pantalla.blit(font.render(t, True, clr), (x,y))

class HoldemUI:
    def __init__(self, n_players=4):  # 4 jugadores: 1 humano + 3 bots
        self.n = n_players
        self.env = HoldemEnv(n_players=self.n)
        self.stacks = [1000 for _ in range(self.n)]
        self.agent = PolicyAgent()
        self.bots = [HeuristicAgent() for _ in range(self.n-1)]
        self.human_index = 0
        self.reset_hand()
        self.mode = "menu"
        self.auto_ai = False
        self.ai_thread = None

        # Posiciones para 4 jugadores (abajo-centro humano)
        self.posiciones_jugadores = {
            0: (ANCHO//2, ALTO - 150),      # Humano abajo-centro
            1: (ANCHO//2, 80),              # Bot arriba-centro
            2: (ANCHO - 200, ALTO - 325),   # Bot derecha-centro
            3: (200, ALTO - 325),            # Bot izquierda-centro
        }

    def reset_hand(self):
        self.env.reset()
        self.msg = "Nueva mano: presiona 'New Hand'."
        self.selected = None
        self.running = False

    def new_hand(self, mode="human"):
        self.mode = mode
        self.env.reset()
        self.msg = "Mano iniciada"
        self.running = True
        if mode == "ai_vs_ai":
            if self.ai_thread is None or not self.ai_thread.is_alive():
                self.auto_ai = True
                self.ai_thread = threading.Thread(target=self.run_ai_vs_ai, daemon=True)
                self.ai_thread.start()

    def draw_table(self):
        pantalla.fill(BG)
        cx, cy = ANCHO//2, ALTO//2 - 30
        text(f"Pot: {self.env.pot}", cx-40, cy-120, (255,255,200), FONT_L)
        board = self.env.board
        startx = cx - ((len(board)* (CARD_W+10))//2)
        for i,c in enumerate(board):
            img = get_card_image(c)
            pantalla.blit(img, (startx + i*(CARD_W+10), cy - CARD_H//2))

        seat_w = CARD_W + 20
        seat_h = CARD_H // 2

        for i in range(self.n):
            x, y = self.posiciones_jugadores.get(i, (50 + i*150, ALTO - 150))

            rect = pygame.Rect(int(x - seat_w/2), int(y - seat_h/2), seat_w, seat_h)

            color_rect = (80, 80, 80)
            if self.running and self.env.current_player == i:
                color_rect = (200, 100, 100)
            pygame.draw.rect(pantalla, color_rect, rect, border_radius=8)

            name = "Tú" if i == self.human_index else f"Bot {i}"
            text(name, rect.x + 6, rect.y + 4)
            text(f"${self.stacks[i]}", rect.x + 6, rect.y + 24)

            # Dibujar cartas
            for j, card in enumerate(self.env.hands[i]):
                if i == self.human_index or self.env.round_stage == "showdown" or not self.running or self.mode != "human":
                    img = get_card_image(card)
                else:
                    back = pygame.Surface((CARD_W, CARD_H), pygame.SRCALPHA)
                    back.fill((30, 30, 120))
                    pygame.draw.rect(back, (0, 0, 0), back.get_rect(), 2, border_radius=12)
                    img = back

                px = rect.x + j * (CARD_W // 2)
                py = rect.y - CARD_H - 10 if y > ALTO//2 else rect.y + seat_h + 10
                pantalla.blit(img, (px, py))

        text(self.msg, 20, ALTO - 60)
        text(f"Etapa: {self.env.round_stage}", 20, ALTO - 90)

    def human_action(self, action):
        if not self.running:
            self.msg = "Inicia una nueva mano primero"
            return
        cur = self.env.current_player
        if cur != self.human_index:
            self.msg = "No es tu turno"
            return
        try:
            obs, reward, done, info = self.env.step(cur, action)
        except Exception as e:
            self.msg = str(e)
            return

        self.msg = info.get("msg", "")
        if done:
            if "winners" in info:
                self.msg = f"Ganadores: {info['winners']}"
            elif "winner" in info:
                self.msg = f"Ganador: {info['winner']}"
            self.running = False
        else:
            nextp = self.env.current_player
            if self.mode == "human" and nextp != self.human_index:
                time.sleep(0.15)
                self.bot_act(nextp)

    def bot_act(self, bot_index):
        if not self.running:
            return
        obs = self.env._get_obs(bot_index)
        act = HeuristicAgent().action(obs)
        try:
            obs, reward, done, info = self.env.step(bot_index, act)
        except Exception as e:
            self.msg = str(e)
            return

        self.msg = info.get("msg", "")
        if done:
            if "winners" in info:
                self.msg = f"Ganadores: {info['winners']}"
            self.running = False
        else:
            nextp = self.env.current_player
            if self.mode == "human" and nextp != self.human_index:
                time.sleep(0.05)
                self.bot_act(nextp)

    def run_ai_vs_ai(self):
        while self.auto_ai:
            self.new_hand(mode="ai_vs_ai")
            while self.running:
                cur = self.env.current_player
                act = HeuristicAgent().action(self.env._get_obs(cur))
                _, _, done, _ = self.env.step(cur, act)
                if done:
                    self.running = False
                    break
                time.sleep(0.02)
            time.sleep(0.2)
            self.auto_ai = False

    def draw(self):
        self.draw_table()

# Botones
ui = HoldemUI(n_players=4)  # 4 jugadores: 1 humano + 3 bots
btn_new = pygame.Rect(900, 600, 220, 42)
btn_ai = pygame.Rect(900, 660, 220, 42)
btn_bet = pygame.Rect(100, 680, 140, 40)
btn_call = pygame.Rect(260, 680, 140, 40)
btn_fold = pygame.Rect(420, 680, 140, 40)

def draw_buttons():
    pygame.draw.rect(pantalla, (200,200,200), btn_new)
    pantalla.blit(FONT.render("New Hand (Human)", True, (0,0,0)), (btn_new.x+8, btn_new.y+10))
    pygame.draw.rect(pantalla, (180,180,240), btn_ai)
    pantalla.blit(FONT.render("New Hand (AI vs AI)", True, (0,0,0)), (btn_ai.x+8, btn_ai.y+10))
    pygame.draw.rect(pantalla, (200,180,180), btn_bet)
    pantalla.blit(FONT.render("Bet (1)", True, (0,0,0)), (btn_bet.x+8, btn_bet.y+10))
    pygame.draw.rect(pantalla, (200,200,160), btn_call)
    pantalla.blit(FONT.render("Call/Check", True, (0,0,0)), (btn_call.x+8, btn_call.y+10))
    pygame.draw.rect(pantalla, (220,180,200), btn_fold)
    pantalla.blit(FONT.render("Fold", True, (0,0,0)), (btn_fold.x+8, btn_fold.y+10))

def main_loop():
    running = True
    while running:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                ui.auto_ai = False
                running = False
            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                mx,my = e.pos
                if btn_new.collidepoint(mx,my):
                    ui.new_hand(mode="human")
                elif btn_ai.collidepoint(mx,my):
                    ui.auto_ai = True
                    if ui.ai_thread is None or not ui.ai_thread.is_alive():
                        ui.ai_thread = threading.Thread(target=ui.run_ai_vs_ai, daemon=True)
                        ui.ai_thread.start()
                elif btn_bet.collidepoint(mx,my):
                    ui.human_action(2)
                elif btn_call.collidepoint(mx,my):
                    ui.human_action(1)
                elif btn_fold.collidepoint(mx,my):
                    ui.human_action(0)
            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_n:
                    ui.new_hand(mode="human")
                if e.key == pygame.K_a:
                    ui.auto_ai = True
                    if ui.ai_thread is None or not ui.ai_thread.is_alive():
                        ui.ai_thread = threading.Thread(target=ui.run_ai_vs_ai, daemon=True)
                        ui.ai_thread.start()

        ui.draw()
        draw_buttons()
        pygame.display.flip()
        clock.tick(30)
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main_loop()
