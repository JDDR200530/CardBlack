from holdem_env import HoldemEnv
from poker_agent import PolicyAgent, HeuristicAgent, RandomAgent
import random

def entrenar_auto_juego(n_manos=1000):
    env = HoldemEnv(n_players=4)
    agente_entrenable = PolicyAgent()
    bots = [HeuristicAgent(), RandomAgent(), HeuristicAgent()]

    for mano in range(n_manos):
        env.reset()
        done = False
        while not done:
            current = env.current_player
            estado = env._get_obs(current)  # Observación o estado actual

            if current == 0:  # Nuestro agente entrenable
                accion = agente_entrenable.action(estado)
            else:
                accion = bots[current-1].action(estado)

            _, _, done, info = env.step(current, accion)

            # Ejemplo básico de actualización: guardamos última acción (puedes mejorar)
            agente_entrenable.update(estado, accion)

        if mano % 100 == 0:
            print(f"Mano {mano} completada")

    return agente_entrenable


if __name__ == "__main__":
    agente = entrenar_auto_juego()
    print("Entrenamiento finalizado")
