# main_menu.py
import tkinter as tk
from tkinter import messagebox
import os
import sys
import subprocess

# Configuración de rutas (MODIFICA ESTAS RUTAS SEGÚN TU ESTRUCTURA)
RUTA_BLACKJACK = os.path.join(r"E:\Sistemas\CardBlack\CardBlack\blackjack\blackjack_pygame.py")

RUTA_POKER = os.path.join(r"E:\Sistemas\CardBlack\CardBlack\Poker\holdem_pygame_app.py")


def jugar_blackjack():
    try:
        messagebox.showinfo("Blackjack", "Iniciando juego de Blackjack...")
        
        # Opción 1: Importar directamente (si es un módulo)
        # from blackjack_juego import main as blackjack_main
        # blackjack_main()
        
        # Opción 2: Ejecutar como script externo (recomendado)
        if os.path.exists(RUTA_BLACKJACK):
            subprocess.Popen([sys.executable, RUTA_BLACKJACK])
        else:
            messagebox.showerror("Error", f"No se encontró el archivo de Blackjack en:\n{RUTA_BLACKJACK}")
            
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo iniciar Blackjack:\n{str(e)}")

def jugar_poker():
    try:
        messagebox.showinfo("Poker", "Iniciando juego de Poker...")
        
        # Opción 1: Importar directamente
        # from poker_juego import main as poker_main
        # poker_main()
        
        # Opción 2: Ejecutar como script externo
        if os.path.exists(RUTA_POKER):
            subprocess.Popen([sys.executable, RUTA_POKER])
        else:
            messagebox.showerror("Error", f"No se encontró el archivo de Poker en:\n{RUTA_POKER}")
            
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo iniciar Poker:\n{str(e)}")

# Crear ventana principal
ventana = tk.Tk()
ventana.title("Menú de Juegos")
ventana.geometry("400x300")
ventana.configure(bg="darkgreen")

# Título
titulo = tk.Label(ventana, 
                 text="Selecciona un juego", 
                 font=("Arial", 20), 
                 fg="white", 
                 bg="darkgreen")
titulo.pack(pady=30)

# Botón de Blackjack
btn_blackjack = tk.Button(ventana, 
                         text="Jugar Blackjack", 
                         font=("Arial", 14), 
                         width=20,
                         bg="navy",
                         fg="white",
                         activebackground="blue",
                         command=jugar_blackjack)
btn_blackjack.pack(pady=10)

# Botón de Poker
btn_poker = tk.Button(ventana, 
                     text="Jugar Poker", 
                     font=("Arial", 14), 
                     width=20,
                     bg="maroon",
                     fg="white",
                     activebackground="red",
                     command=jugar_poker)
btn_poker.pack(pady=10)

# Botón para salir
btn_salir = tk.Button(ventana, 
                     text="Salir", 
                     font=("Arial", 12), 
                     width=10,
                     bg="gray",
                     fg="white",
                     command=ventana.destroy)
btn_salir.pack(pady=30)

# Ejecutar ventana
ventana.mainloop()