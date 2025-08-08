#main_menu.py

import tkinter as tk
from tkinter import messagebox

# Función cuando se selecciona Blackjack
def jugar_blackjack():
    messagebox.showinfo("Juego", "Has seleccionado Blackjack.")
    # Aquí puedes importar o ejecutar tu lógica del juego de Blackjack
    # ejemplo: import blackjack_juego

# Función cuando se selecciona Poker
def jugar_poker():
    messagebox.showinfo("Juego", "Has seleccionado Poker.")
    # Aquí puedes importar o ejecutar tu lógica del juego de Poker
    # ejemplo: import poker_juego

# Crear ventana principal
ventana = tk.Tk()
ventana.title("Menú de Juegos")
ventana.geometry("400x300")
ventana.configure(bg="darkgreen")

# Título
titulo = tk.Label(ventana, text="Selecciona un juego", font=("Arial", 20), fg="white", bg="darkgreen")
titulo.pack(pady=30)

# Botón de Blackjack
btn_blackjack = tk.Button(ventana, text="Jugar Blackjack", font=("Arial", 14), width=20, command=jugar_blackjack)
btn_blackjack.pack(pady=10)

# Botón de Poker
btn_poker = tk.Button(ventana, text="Jugar Poker", font=("Arial", 14), width=20, command=jugar_poker)
btn_poker.pack(pady=10)

# Botón para salir
btn_salir = tk.Button(ventana, text="Salir", font=("Arial", 12), width=10, command=ventana.destroy)
btn_salir.pack(pady=30)

# Ejecutar ventana
ventana.mainloop()
