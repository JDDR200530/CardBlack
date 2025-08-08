#gui_blackjack.py

import tkinter as tk
from blackjack_game import BlackjackGame

class BlackjackGUI:
    def __init__(self, root):
        self.root = root
        self.game = BlackjackGame()
        self.setup_ui()
        self.nueva_partida()

    def setup_ui(self):
        self.root.title("Blackjack")
        self.root.configure(bg="green")
        self.root.geometry("900x700")

        # Frames para la interfaz
        self.dealer_frame = tk.Frame(self.root, bg="green")
        self.dealer_frame.pack(pady=20)
        
        self.dealer_score_label = tk.Label(self.root, text="Dealer: ?", 
                                       font=("Arial", 16), bg="green", fg="white")
        self.dealer_score_label.pack()

        self.jugador_frame = tk.Frame(self.root, bg="green")
        self.jugador_frame.pack(pady=50)

        self.player_score_label = tk.Label(self.root, text="Jugador: 0", 
                                        font=("Arial", 16), bg="green", fg="white")
        self.player_score_label.pack()

        self.button_frame = tk.Frame(self.root, bg="green")
        self.button_frame.pack(pady=20)

        self.message_label = tk.Label(self.root, text="", 
                                   font=("Arial", 14), bg="green", fg="yellow")
        self.message_label.pack()

        # Botones
        self.btn_nueva = tk.Button(self.button_frame, text="Nueva Partida", 
                                 command=self.nueva_partida, font=("Arial", 14), 
                                 bg="white", width=15)
        self.btn_nueva.grid(row=0, column=0, padx=10)

        self.btn_pedir = tk.Button(self.button_frame, text="Pedir Carta", 
                                  command=self.pedir_carta, font=("Arial", 14), 
                                  bg="white", width=15, state=tk.DISABLED)
        self.btn_pedir.grid(row=0, column=1, padx=10)

        self.btn_plantarse = tk.Button(self.button_frame, text="Plantarse", 
                                      command=self.plantarse, font=("Arial", 14), 
                                      bg="white", width=15, state=tk.DISABLED)
        self.btn_plantarse.grid(row=0, column=2, padx=10)

    def limpiar_interface(self):
        for widget in self.dealer_frame.winfo_children():
            widget.destroy()
        for widget in self.jugador_frame.winfo_children():
            widget.destroy()
        self.message_label.config(text="")

    def repartir_cartas_iniciales(self):
        # Repartir al jugador
        for _ in range(2):
            carta, imagen = self.game.repartir_carta()
            self.game.player_cards.append(carta)
            tk.Label(self.jugador_frame, image=imagen, bg="green").pack(side=tk.LEFT, padx=5)
        
        # Repartir al dealer
        for i in range(2):
            carta_d, imagen_d = self.game.repartir_carta()
            self.game.dealer_cards.append((carta_d, imagen_d))
            if i == 0:  # Primera carta visible
                label = tk.Label(self.dealer_frame, image=imagen_d, bg="green")
            else:  # Segunda carta oculta
                label = tk.Label(self.dealer_frame, image=self.game.cargar_imagen("Atras"), bg="green")
            label.pack(side=tk.LEFT, padx=5)

    def actualizar_puntuaciones(self):
        player_score = self.game.calcular_mano(self.game.player_cards)
        self.player_score_label.config(text=f"Jugador: {player_score}")
        
        if self.game.game_over:
            dealer_score = self.game.calcular_mano([c[0] for c in self.game.dealer_cards])
            self.dealer_score_label.config(text=f"Dealer: {dealer_score}")
        else:
            visible_score = self.game.calcular_mano([self.game.dealer_cards[0][0]])
            self.dealer_score_label.config(text=f"Dealer: ? + {visible_score}")

    def habilitar_botones_juego(self):
        self.btn_pedir.config(state=tk.NORMAL)
        self.btn_plantarse.config(state=tk.NORMAL)

    def deshabilitar_botones_juego(self):
        self.btn_pedir.config(state=tk.DISABLED)
        self.btn_plantarse.config(state=tk.DISABLED)

    def revelar_carta_dealer(self):
        if len(self.game.dealer_cards) > 1:
            carta, imagen = self.game.dealer_cards[1]
            for widget in self.dealer_frame.winfo_children():
                if isinstance(widget, tk.Label):
                    if widget.cget("image") == str(self.game.cargar_imagen("Atras")):
                        widget.config(image=imagen)
                        break
        self.actualizar_puntuaciones()

    def pedir_carta(self):
        carta, imagen = self.game.repartir_carta()
        self.game.player_cards.append(carta)
        tk.Label(self.jugador_frame, image=imagen, bg="green").pack(side=tk.LEFT, padx=5)
        self.actualizar_puntuaciones()
        
        if self.game.calcular_mano(self.game.player_cards) > 21:
            self.plantarse()

    def plantarse(self):
        self.game.game_over = True
        self.revelar_carta_dealer()
        
        # Turno del dealer
        while self.game.calcular_mano([c[0] for c in self.game.dealer_cards]) < 17:
            carta, imagen = self.game.repartir_carta()
            self.game.dealer_cards.append((carta, imagen))
            tk.Label(self.dealer_frame, image=imagen, bg="green").pack(side=tk.LEFT, padx=5)
            self.root.update()
            self.root.after(500)  # Pequeña pausa
        
        # Mostrar resultado
        resultado = self.game.determinar_ganador()
        self.message_label.config(text=resultado)
        self.deshabilitar_botones_juego()

    def nueva_partida(self):
        self.game.reset_game()
        self.limpiar_interface()
        self.repartir_cartas_iniciales()
        self.actualizar_puntuaciones()
        self.habilitar_botones_juego()