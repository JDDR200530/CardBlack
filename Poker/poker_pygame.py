# poker_pygame.py
import pygame, sys, time
from kuhn_env import KuhnEnv
from poker_agent import RandomAgent, PolicyAgent, obs_to_vector
import threading

# ---------- Config ----------
ANCHO, ALTO = 900, 520
BG = (20, 120, 60)
WHITE = (255,255,255)
DARK = (30,30,30)
BTN = (220,220,220)
FPS = 30

pygame.init()
pantalla = pygame.display.set_mode((ANCHO, ALTO))
pygame.display.set_caption("Kuhn Poker - Pygame")
clock = pygame.time.Clock()
FONT = pygame.font.SysFont("Arial", 20)
FONT_LARGE = pygame.font.SysFont("Arial", 26, bold=True)

# ---------- Helpers UI ----------
def draw_text(surf, txt, x, y, font=FONT, color=WHITE):
    surf.blit(font.render(txt, True, color), (x,y))

def draw_button(surf, rect, text):
    pygame.draw.rect(surf, BTN, rect, border_radius=6)
    pygame.draw.rect(surf, DARK, rect, 2, border_radius=6)
    tx = rect[0] + (rect[2]-FONT.size(text)[0])//2
    ty = rect[1] + (rect[3]-FONT.size(text)[1])//2
    draw_text(surf, text, tx, ty, FONT, DARK)

# Mapeo visual cartas
CARD_NAME = {1:'J',2:'Q',3:'K'}

# ---------- UI Class ----------
class PokerUI:
    def __init__(self):
        self.env = KuhnEnv()
        self.mode = "menu"  # menu, human_vs_ai, ai_vs_ai
        self.agent = PolicyAgent()  # intenta cargar modelo
        self.opponent = RandomAgent()
        self.reset_game_state()
        self.ai_autoplay = False
        self.ai_thread = None
        self.results = [0,0,0]  # p0 wins, p1 wins, ties

    def reset_game_state(self):
        obs, _ = self.env.reset()
        self.obs = obs
        self.history = []
        self.done = False
        self.reward = (0,0)
        self.turn = self.env.current_player
        self.msg = "Pulsa 'Nueva Ronda' para empezar."

    def new_round(self, mode):
        self.mode = mode
        self.reset_game_state()
        self.msg = "Ronda iniciada."
        # Si ai_vs_ai y queremos que empiece la carrera automática:
        if mode == "ai_vs_ai":
            # lanzar hilo para autoplay
            if self.ai_thread is None or not self.ai_thread.is_alive():
                self.ai_autoplay = True
                self.ai_thread = threading.Thread(target=self.run_ai_vs_ai, daemon=True)
                self.ai_thread.start()

    def step_action(self, action):
        if self.done:
            return
        obs_next, reward, done, _ = self.env.step(action)
        self.obs = obs_next
        self.history = list(self.env.history)
        self.turn = self.env.current_player if not done else None
        self.done = done
        self.reward = reward
        if done:
            self.msg = f"Ronda finalizada. Recompensa: {reward}"
            # actualizar contador resultados (perspectiva simple)
            if reward[0] > 0:
                self.results[0]+=1
            elif reward[1] > 0:
                self.results[1]+=1
            else:
                self.results[2]+=1

    def human_play_step(self, action):
        # asume humano es jugador 0
        if self.mode != "human_vs_ai":
            return
        # solo permitir acción si es turno humano (player 0)
        if self.env.current_player != 0 or self.done:
            return
        self.step_action(action)
        # si el turno pasa a la IA y no terminal, que la IA responda
        if not self.done and self.env.current_player == 1:
            ai_act = self.agent.action(self.env._get_obs(1), greedy=True)
            time.sleep(0.15)
            self.step_action(ai_act)

    def ai_vs_ai_step(self):
        # single hand: both AIs play according to policy/opponent
        self.reset_game_state()
        while not self.done:
            cur = self.env.current_player
            if cur == 0:
                act = self.agent.action(self.env._get_obs(0), greedy=True)
            else:
                act = self.opponent.action(self.env._get_obs(1))
            self.step_action(act)
            time.sleep(0.05)

    def run_ai_vs_ai(self):
        # autocorrer hands hasta que se desactive
        rounds = 0
        while self.ai_autoplay and rounds < 1000:
            self.reset_game_state()
            while not self.done and self.ai_autoplay:
                cur = self.env.current_player
                if cur == 0:
                    act = self.agent.action(self.env._get_obs(0), greedy=True)
                else:
                    act = self.opponent.action(self.env._get_obs(1))
                self.step_action(act)
                time.sleep(0.01)
            rounds += 1
            time.sleep(0.02)
        self.ai_autoplay = False

    def stop_ai_autoplay(self):
        self.ai_autoplay = False

    def draw(self, surf):
        surf.fill(BG)
        draw_text(surf, "Kuhn Poker - Interfaz", 20, 10, FONT_LARGE)
        draw_text(surf, f"Modo: {self.mode}", 20, 50)
        draw_text(surf, f"Historial: {self.history}", 20, 80)
        draw_text(surf, f"Turno: {self.env.current_player if not self.done else '—'}", 20, 110)
        draw_text(surf, f"Cartas (p0,p1): {CARD_NAME[self.env.player_cards[0]]} , {CARD_NAME[self.env.player_cards[1]]}", 20, 140)
        draw_text(surf, f"Recompensa actual: {self.reward}", 20, 170)
        draw_text(surf, f"Resultados acumulados (p0,p1,empates): {self.results}", 20, 200)
        draw_text(surf, "Instrucciones:", 20, 240)
        draw_text(surf, "- En Human vs IA: actúa solo si es tu turno (jugador 0).", 20, 270)
        draw_text(surf, "- Acciones: Pass/Check (0) o Bet (1).", 20, 300)

# ---------- Botones ----------
ui = PokerUI()
btn_new_h = (650, 50, 220, 40)
btn_new_ai = (650, 110, 220, 40)
btn_step = (650, 170, 100, 40)
btn_bet = (650, 250, 100, 40)
btn_pass = (770, 250, 100, 40)
btn_stop = (650, 310, 220, 40)
btn_exit = (650, 370, 220, 40)

# ---------- Main loop ----------
def main_loop():
    running = True
    while running:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                ui.stop_ai_autoplay()
                running = False
            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                mx,my = e.pos
                if pygame.Rect(btn_new_h).collidepoint(mx,my):
                    ui.new_round(mode="human_vs_ai")
                elif pygame.Rect(btn_new_ai).collidepoint(mx,my):
                    ui.new_round(mode="ai_vs_ai")
                elif pygame.Rect(btn_step).collidepoint(mx,my):
                    if ui.mode == "ai_vs_ai":
                        ui.ai_vs_ai_step()
                    elif ui.mode == "human_vs_ai":
                        # forzar que IA responda si es su turno
                        if not ui.done and ui.env.current_player == 1:
                            ai_act = ui.agent.action(ui.env._get_obs(1), greedy=True)
                            ui.step_action(ai_act)
                elif pygame.Rect(btn_bet).collidepoint(mx,my):
                    if ui.mode == "human_vs_ai":
                        ui.human_play_step(1)
                elif pygame.Rect(btn_pass).collidepoint(mx,my):
                    if ui.mode == "human_vs_ai":
                        ui.human_play_step(0)
                elif pygame.Rect(btn_stop).collidepoint(mx,my):
                    ui.stop_ai_autoplay()
                elif pygame.Rect(btn_exit).collidepoint(mx,my):
                    ui.stop_ai_autoplay()
                    running = False

        ui.draw(pantalla)
        # dibujar botones
        draw_button(pantalla, btn_new_h, "Nueva: Humano vs IA")
        draw_button(pantalla, btn_new_ai, "Nueva: IA vs IA")
        draw_button(pantalla, btn_step, "Step (AI)")
        draw_button(pantalla, btn_bet, "Bet (1)")
        draw_button(pantalla, btn_pass, "Pass (0)")
        draw_button(pantalla, btn_stop, "Detener autoplay IA")
        draw_button(pantalla, btn_exit, "Salir")

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main_loop()
