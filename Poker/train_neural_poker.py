#!/usr/bin/env python3
"""
Script de entrenamiento avanzado para el agente neural de poker
Integra la red neuronal profunda con el entorno de poker existente
"""

import sys
import os
import time
import matplotlib.pyplot as plt
import numpy as np

# Importar módulos del proyecto
from holdem_env import HoldemEnv
from kuhn_env import KuhnEnv
from neural_agent import NeuralPokerAgent, PokerNeuralTrainer
from poker_agent import HeuristicAgent, RandomAgent, ConservativeAgent, AggressiveAgent


def entrenar_neural_holdem(n_episodios=2000, n_jugadores=4, guardar_cada=200):
    """
    Entrenamiento del agente neural en Texas Hold'em
    """
    print("🎰" + "="*60 + "🎰")
    print("    ENTRENAMIENTO NEURAL - TEXAS HOLD'EM")
    print("🎰" + "="*60 + "🎰")
    
    # Crear entorno
    env = HoldemEnv(n_players=n_jugadores)
    print(f"🎮 Entorno creado: {n_jugadores} jugadores")
    
    # Crear agente neural
    agent = NeuralPokerAgent(
        input_size=20,  # Tamaño correcto que genera obs_to_vector_enhanced
        hidden_sizes=[512, 256, 128, 64],
        learning_rate=0.0005,
        epsilon=0.9,
        epsilon_decay=0.9995,
        epsilon_min=0.05,
        batch_size=64,
        memory_size=50000
    )
    
    # Crear oponentes variados
    oponentes = [
        HeuristicAgent(aggression=0.3),
        RandomAgent(weights=[0.2, 0.5, 0.3]),
        ConservativeAgent()
    ]
    print(f"🤖 Oponentes creados: {len(oponentes)} bots")
    
    # Crear entrenador
    trainer = PokerNeuralTrainer(env, agent, oponentes)
    
    # Intentar cargar modelo previo
    if agent.load_model("poker_holdem_dqn.pth"):
        print("📂 Modelo previo cargado, continuando entrenamiento...")
    else:
        print("🆕 Iniciando entrenamiento desde cero...")
    
    # Entrenar
    print(f"🚀 Iniciando entrenamiento por {n_episodios} episodios...")
    start_time = time.time()
    
    historia_recompensas = []
    
    for episodio in range(n_episodios):
        recompensa = trainer.train_episode()
        historia_recompensas.append(recompensa)
        
        # Progreso cada cierto número de episodios
        if episodio % 50 == 0:
            avg_reward = np.mean(historia_recompensas[-50:]) if historia_recompensas else 0
            elapsed = time.time() - start_time
            print(f"📈 Episodio {episodio:4d} | Recompensa avg: {avg_reward:6.2f} | "
                  f"Epsilon: {agent.epsilon:.3f} | Tiempo: {elapsed:.1f}s")
        
        # Guardar modelo periódicamente
        if episodio % guardar_cada == 0 and episodio > 0:
            agent.save_model(f"poker_holdem_dqn_ep{episodio}.pth")
    
    # Guardar modelo final
    agent.save_model("poker_holdem_dqn_final.pth")
    
    # Estadísticas finales
    tiempo_total = time.time() - start_time
    agent.print_stats()
    print(f"\n⏱️ Tiempo total de entrenamiento: {tiempo_total:.1f} segundos")
    print(f"⚡ Episodios por segundo: {n_episodios/tiempo_total:.2f}")
    
    return agent, historia_recompensas


def entrenar_neural_kuhn(n_episodios=5000):
    """
    Entrenamiento rápido en Kuhn Poker (más simple)
    """
    print("🎯" + "="*50 + "🎯")
    print("    ENTRENAMIENTO NEURAL - KUHN POKER")
    print("🎯" + "="*50 + "🎯")
    
    # Crear entorno simple
    env = KuhnEnv()
    
    # Crear agente neural más pequeño para Kuhn
    agent = NeuralPokerAgent(
        input_size=20,
        hidden_sizes=[128, 64, 32],
        learning_rate=0.001,
        epsilon=0.8,
        epsilon_decay=0.999,
        batch_size=32,
        memory_size=10000
    )
    
    # Oponente simple para Kuhn
    oponente = RandomAgent()
    
    print("🚀 Iniciando entrenamiento Kuhn...")
    start_time = time.time()
    
    historia_recompensas = []
    
    for episodio in range(n_episodios):
        try:
            obs, _ = env.reset()
            total_reward = 0
            done = False
            
            while not done:
                current_player = env.current_player
                
                if current_player == 0:  # Agente neural
                    action = agent.action(obs)
                    prev_obs = obs
                else:  # Oponente
                    action = oponente.action(obs)
                
                next_obs, rewards, done, info = env.step(action)
                
                if current_player == 0:
                    reward = rewards[0] if isinstance(rewards, tuple) else 0
                    agent.update(prev_obs, action, reward, next_obs, done)
                    total_reward += reward
                
                obs = next_obs
            
            historia_recompensas.append(total_reward)
            
            # Progreso
            if episodio % 500 == 0:
                avg_reward = np.mean(historia_recompensas[-500:])
                print(f"📈 Episodio {episodio:4d} | Recompensa avg: {avg_reward:6.2f} | "
                      f"Epsilon: {agent.epsilon:.3f}")
        
        except Exception as e:
            print(f"⚠️ Error en episodio {episodio}: {e}")
            continue
    
    # Guardar modelo
    agent.save_model("poker_kuhn_dqn.pth")
    
    tiempo_total = time.time() - start_time
    print(f"\n⏱️ Entrenamiento Kuhn completado en {tiempo_total:.1f}s")
    
    return agent, historia_recompensas


def evaluar_agente(agente, n_partidas=100, env_type="holdem"):
    """
    Evaluar el rendimiento del agente entrenado
    """
    print(f"\n🧪 Evaluando agente en {n_partidas} partidas ({env_type})...")
    
    # Crear entorno
    if env_type == "holdem":
        env = HoldemEnv(n_players=4)
        oponentes = [HeuristicAgent(), RandomAgent(), ConservativeAgent()]
    else:
        env = KuhnEnv()
        oponentes = [RandomAgent()]
    
    # Desactivar exploración para evaluación
    epsilon_original = agente.epsilon
    agente.epsilon = 0.0  # Solo explotación
    
    victorias = 0
    recompensas = []
    
    for partida in range(n_partidas):
        try:
            obs, _ = env.reset()
            total_reward = 0
            done = False
            
            while not done:
                current_player = env.current_player
                
                if current_player == 0:  # Nuestro agente
                    action = agente.action(obs)
                else:  # Oponentes
                    if env_type == "holdem" and current_player - 1 < len(oponentes):
                        action = oponentes[current_player - 1].action(obs)
                    else:
                        action = random.choice([0, 1, 2])
                
                obs, rewards, done, info = env.step(current_player, action)
                
                if current_player == 0:
                    reward = rewards[0] if isinstance(rewards, (list, tuple)) else 0
                    total_reward += reward
            
            recompensas.append(total_reward)
            if total_reward > 0:
                victorias += 1
        
        except Exception as e:
            print(f"⚠️ Error en evaluación partida {partida}: {e}")
            continue
    
    # Restaurar epsilon
    agente.epsilon = epsilon_original
    
    # Resultados
    tasa_victoria = (victorias / n_partidas) * 100
    recompensa_promedio = np.mean(recompensas)
    
    print(f"📊 Resultados de evaluación:")
    print(f"   🏆 Victorias: {victorias}/{n_partidas} ({tasa_victoria:.1f}%)")
    print(f"   💰 Recompensa promedio: {recompensa_promedio:.2f}")
    print(f"   📈 Recompensa máxima: {max(recompensas):.2f}")
    print(f"   📉 Recompensa mínima: {min(recompensas):.2f}")
    
    return tasa_victoria, recompensa_promedio


def graficar_progreso(historia_recompensas, titulo="Progreso de Entrenamiento"):
    """
    Crear gráfico del progreso de entrenamiento
    """
    try:
        plt.figure(figsize=(12, 6))
        
        # Suavizar curva con media móvil
        window = min(50, len(historia_recompensas) // 10)
        if window > 1:
            recompensas_suaves = np.convolve(historia_recompensas, 
                                           np.ones(window)/window, mode='valid')
            plt.plot(recompensas_suaves, label=f'Media móvil ({window} episodios)', linewidth=2)
        
        plt.plot(historia_recompensas, alpha=0.3, label='Recompensas por episodio')
        plt.axhline(y=0, color='r', linestyle='--', alpha=0.5, label='Break-even')
        
        plt.title(titulo)
        plt.xlabel('Episodio')
        plt.ylabel('Recompensa')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # Guardar gráfico
        plt.savefig('entrenamiento_progreso.png', dpi=150, bbox_inches='tight')
        plt.show()
        
        print("📊 Gráfico guardado como 'entrenamiento_progreso.png'")
    
    except Exception as e:
        print(f"⚠️ Error creando gráfico: {e}")


def main():
    """
    Función principal de entrenamiento
    """
    print("🧠" + "="*70 + "🧠")
    print("    ENTRENAMIENTO DE RED NEURONAL PARA POKER")
    print("             CardBlack Neural Poker AI")
    print("🧠" + "="*70 + "🧠")
    
    # Verificar dependencias
    try:
        import torch
        print(f"✅ PyTorch {torch.__version__} detectado")
        print(f"🔥 CUDA disponible: {torch.cuda.is_available()}")
    except ImportError:
        print("❌ PyTorch no instalado. Instala con: pip install torch")
        return
    
    # Menú de opciones
    print("\n🎯 Opciones de entrenamiento:")
    print("1. 🎰 Entrenar en Texas Hold'em (complejo, lento)")
    print("2. 🎯 Entrenar en Kuhn Poker (simple, rápido)")
    print("3. 🧪 Solo probar agente neural")
    print("4. 📊 Evaluar modelo existente")
    
    try:
        opcion = input("\n👉 Selecciona una opción (1-4): ").strip()
        
        if opcion == "1":
            # Entrenamiento Hold'em
            agente, historia = entrenar_neural_holdem(n_episodios=1000)
            graficar_progreso(historia, "Entrenamiento Texas Hold'em")
            evaluar_agente(agente, n_partidas=50, env_type="holdem")
        
        elif opcion == "2":
            # Entrenamiento Kuhn
            agente, historia = entrenar_neural_kuhn(n_episodios=3000)
            graficar_progreso(historia, "Entrenamiento Kuhn Poker")
            evaluar_agente(agente, n_partidas=100, env_type="kuhn")
        
        elif opcion == "3":
            # Solo testing
            from neural_agent import test_neural_agent
            test_neural_agent()
        
        elif opcion == "4":
            # Evaluar modelo existente
            agente = NeuralPokerAgent()
            if agente.load_model("poker_holdem_dqn_final.pth"):
                evaluar_agente(agente, n_partidas=100, env_type="holdem")
            elif agente.load_model("poker_kuhn_dqn.pth"):
                evaluar_agente(agente, n_partidas=200, env_type="kuhn")
            else:
                print("❌ No se encontró modelo entrenado")
        
        else:
            print("❌ Opción inválida")
    
    except KeyboardInterrupt:
        print("\n⏹️ Entrenamiento interrumpido por el usuario")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n🎉 Proceso completado!")


def entrenamiento_comparativo():
    """
    Comparar rendimiento entre diferentes agentes
    """
    print("⚔️ BATALLA DE AGENTES ⚔️")
    
    # Crear agentes
    agentes = {
        "Neural": NeuralPokerAgent(),
        "Heuristic": HeuristicAgent(),
        "Random": RandomAgent(),
        "Conservative": ConservativeAgent(),
        "Aggressive": AggressiveAgent()
    }
    
    # Cargar modelo neural si existe
    agentes["Neural"].load_model("poker_holdem_dqn_final.pth")
    agentes["Neural"].epsilon = 0.0  # Sin exploración para evaluación
    
    # Crear entorno
    env = HoldemEnv(n_players=4)
    
    resultados = {nombre: [] for nombre in agentes.keys()}
    n_partidas = 100
    
    print(f"🎮 Simulando {n_partidas} partidas...")
    
    for partida in range(n_partidas):
        try:
            obs, _ = env.reset()
            done = False
            
            while not done:
                current_player = env.current_player
                
                # Seleccionar agente para el jugador actual
                if current_player == 0:
                    agente_actual = agentes["Neural"]
                elif current_player == 1:
                    agente_actual = agentes["Heuristic"]
                elif current_player == 2:
                    agente_actual = agentes["Random"]
                else:
                    agente_actual = agentes["Conservative"]
                
                action = agente_actual.action(obs)
                obs, rewards, done, info = env.step(current_player, action)
            
            # Registrar resultados
            nombres_agentes = ["Neural", "Heuristic", "Random", "Conservative"]
            for i, nombre in enumerate(nombres_agentes):
                if i < len(rewards):
                    resultados[nombre].append(rewards[i])
        
        except Exception as e:
            print(f"⚠️ Error en partida {partida}: {e}")
            continue
    
    # Mostrar resultados
    print("\n🏆 RESULTADOS FINALES:")
    for nombre, recompensas in resultados.items():
        if recompensas:
            promedio = np.mean(recompensas)
            victorias = sum(1 for r in recompensas if r > 0)
            tasa_victoria = (victorias / len(recompensas)) * 100
            print(f"   {nombre:12} | Promedio: {promedio:6.2f} | Victorias: {tasa_victoria:5.1f}%")


if __name__ == "__main__":
    # Verificar si se ejecuta directamente
    if len(sys.argv) > 1:
        if sys.argv[1] == "compare":
            entrenamiento_comparativo()
        elif sys.argv[1] == "kuhn":
            entrenar_neural_kuhn()
        elif sys.argv[1] == "holdem":
            entrenar_neural_holdem()
        else:
            print("Opciones: python train_neural_poker.py [compare|kuhn|holdem]")
    else:
        main()
