# play_cli.py
import gymnasium as gym
from ai_agent import AIAgent
import sys

def mostrar_estado(state):
    # Estado: (player_sum, dealer_card, usable_ace)
    print("Estado -> Suma jugador:", state[0], "| Carta visible dealer:", state[1], "| As usable:", state[2])

def human_play_mode(agent=None):
    env = gym.make("Blackjack-v1", sab=True)
    state, _ = env.reset()
    done = False

    print("\nComienza la partida (modo humano). Usa 'h' pedir, 's' plantarse, 'a' pedir consejo IA, 'q' salir.")
    while not done:
        mostrar_estado(state)
        cmd = input("Acción (h/s/a/q): ").lower().strip()
        if cmd == "q":
            print("Saliendo al menú.")
            return
        if cmd == "a":
            if agent is None:
                print("No hay agente cargado para consejos.")
                continue
            sug = agent.action(state, greedy=True)
            print("IA recomienda:", "Pedir carta (hit)" if sug == 1 else "Plantarse (stick)")
            continue
        if cmd == "h":
            action = 1
        else:
            action = 0

        next_state, reward, terminated, truncated, _ = env.step(action)
        done = terminated or truncated
        state = next_state

    if reward > 0:
        print("¡Ganaste!")
    elif reward < 0:
        print("Perdiste.")
    else:
        print("Empate.")

def ai_play_mode(greedy=True, episodes=5):
    env = gym.make("Blackjack-v1", sab=True)
    agent = AIAgent()
    for e in range(episodes):
        state, _ = env.reset()
        done = False
        print(f"\n--- Partida IA {e+1} ---")
        while not done:
            act = agent.action(state, greedy=greedy)
            print("Estado:", state, "| Acción IA:", "Pedir" if act == 1 else "Plantarse")
            state, reward, terminated, truncated, _ = env.step(act)
            done = terminated or truncated
        print("Resultado:", "Victoria" if reward>0 else "Derrota" if reward<0 else "Empate")

def ai_vs_ai(episodes=100):
    env = gym.make("Blackjack-v1", sab=True)
    agent = AIAgent()
    wins = ties = losses = 0
    for _ in range(episodes):
        state, _ = env.reset()
        done = False
        while not done:
            act = agent.action(state, greedy=True)
            state, reward, terminated, truncated, _ = env.step(act)
            done = terminated or truncated
        if reward > 0:
            wins += 1
        elif reward < 0:
            losses += 1
        else:
            ties += 1
    print(f"Resultados IA en {episodes} partidas -> Victorias: {wins}, Derrotas: {losses}, Empates: {ties}")

def main():
    print("Menú:")
    print("1 - Jugar (humano). Puedes pedir consejo de la IA durante la partida.")
    print("2 - Ver jugar a la IA (IA como jugador).")
    print("3 - Ejecutar muchas partidas IA (estadísticas).")
    choice = input("Elige modo (1/2/3): ").strip()
    if choice == "1":
        cargar = input("¿Cargar IA para consejos? (s/n): ").strip().lower() == "s"
        agent = AIAgent() if cargar else None
        human_play_mode(agent)
    elif choice == "2":
        ai_play_mode(greedy=True, episodes=5)
    elif choice == "3":
        ai_vs_ai(episodes=200)
    else:
        print("Opción inválida.")

if __name__ == "__main__":
    main()
