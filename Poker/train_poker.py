from holdem_env import HoldemEnv
from poker_agent import PolicyAgent, HeuristicAgent, RandomAgent
from neural_agent import NeuralPokerAgent
import random

def entrenar_auto_juego(n_manos=1000, usar_neural=False):
    env = HoldemEnv(n_players=4)
    
    # Elegir tipo de agente
    if usar_neural:
        print("🧠 Usando NeuralPokerAgent (Red Neuronal Profunda)")
        agente_entrenable = NeuralPokerAgent(input_size=20, hidden_sizes=[256, 128, 64])
        # Intentar cargar modelo previo
        agente_entrenable.load_model("poker_holdem_dqn.pth")
    else:
        print("📚 Usando PolicyAgent (Aprendizaje básico)")
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
            if usar_neural:
                agente_entrenable.print_stats()

    # Guardar modelo si es neural
    if usar_neural:
        agente_entrenable.save_model("poker_holdem_dqn.pth")
        print("💾 Modelo neural guardado")

    return agente_entrenable


if __name__ == "__main__":
    print("🎰 Entrenamiento de Poker - CardBlack")
    print("1. Entrenamiento básico (PolicyAgent)")
    print("2. Entrenamiento neural (DQN)")
    
    try:
        opcion = input("Selecciona opción (1-2): ").strip()
        usar_neural = (opcion == "2")
        
        agente = entrenar_auto_juego(n_manos=500, usar_neural=usar_neural)
        print("✅ Entrenamiento finalizado")
        
        if usar_neural:
            print("🧠 Red neuronal entrenada y guardada")
    except Exception as e:
        print(f"❌ Error: {e}")
