# main_menu.py
import tkinter as tk
from tkinter import messagebox, ttk
import os
import sys
import subprocess
import pygame
from PIL import Image, ImageTk
import threading

# Configuración de rutas (MODIFICA ESTAS RUTAS SEGÚN TU ESTRUCTURA)
RUTA_BLACKJACK = os.path.join(r"/home/togg/Documentos/CardBlack/Blackjack/blackjack_gui.py")
RUTA_POKER = os.path.join(r"/home/togg/Documentos/CardBlack/Poker/holdem_pygame_app.py")

# Ruta de la música (coloca un archivo .mp3 o .wav en la misma carpeta)
RUTA_MUSICA = "casino_music.mp3"  # Cambia por tu archivo de música

class MenuJuegos:
    def __init__(self):
        self.ventana = tk.Tk()
        self.setup_window()
        self.setup_audio()
        self.crear_widgets()
        self.iniciar_musica()
        
    def setup_window(self):
        self.ventana.title("🎰 Casino Games Menu 🎰")
        self.ventana.geometry("600x700")
        self.ventana.configure(bg="#0F2027")
        self.ventana.resizable(False, False)
        
        # Centrar ventana
        self.ventana.update_idletasks()
        ancho = self.ventana.winfo_width()
        alto = self.ventana.winfo_height()
        pos_x = (self.ventana.winfo_screenwidth() // 2) - (ancho // 2)
        pos_y = (self.ventana.winfo_screenheight() // 2) - (alto // 2)
        self.ventana.geometry(f"{ancho}x{alto}+{pos_x}+{pos_y}")
        
    def setup_audio(self):
        try:
            pygame.mixer.init()
            self.musica_cargada = False
            self.volumen = 0.3  # Volumen inicial (30%)
            if os.path.exists(RUTA_MUSICA):
                pygame.mixer.music.load(RUTA_MUSICA)
                self.musica_cargada = True
        except:
            self.musica_cargada = False
            print("No se pudo inicializar el audio")
    
    def iniciar_musica(self):
        if self.musica_cargada:
            try:
                pygame.mixer.music.set_volume(self.volumen)
                pygame.mixer.music.play(-1)  # Loop infinito
            except:
                pass
    
    def cambiar_volumen(self, valor):
        self.volumen = float(valor) / 100
        if self.musica_cargada:
            pygame.mixer.music.set_volume(self.volumen)
    
    def toggle_musica(self):
        if self.musica_cargada:
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.pause()
                self.btn_musica.config(text="🔇")
            else:
                pygame.mixer.music.unpause()
                self.btn_musica.config(text="🎵")
    
    def crear_widgets(self):
        # Frame principal con gradiente simulado
        main_frame = tk.Frame(self.ventana, bg="#0F2027")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Título principal con efecto de sombra
        title_frame = tk.Frame(main_frame, bg="#0F2027")
        title_frame.pack(pady=(0, 30))
        
        # Sombra del título
        shadow_title = tk.Label(title_frame,
                               text="🎰 CASINO ROYALE 🎰",
                               font=("Arial", 28, "bold"),
                               fg="#1a1a1a",
                               bg="#0F2027")
        shadow_title.pack()
        shadow_title.place(x=2, y=2)
        
        # Título principal
        main_title = tk.Label(title_frame,
                             text="🎰 CASINO ROYALE 🎰",
                             font=("Arial", 28, "bold"),
                             fg="#FFD700",
                             bg="#0F2027")
        main_title.pack()
        
        # Subtítulo
        subtitle = tk.Label(main_frame,
                           text="Selecciona tu juego favorito",
                           font=("Arial", 16, "italic"),
                           fg="#C0C0C0",
                           bg="#0F2027")
        subtitle.pack(pady=(0, 40))
        
        # Frame para los botones de juego
        games_frame = tk.Frame(main_frame, bg="#0F2027")
        games_frame.pack(pady=20)
        
        # Botón de Blackjack mejorado
        blackjack_frame = tk.Frame(games_frame, bg="#1a472a", relief="raised", bd=3)
        blackjack_frame.pack(pady=15, padx=20, fill="x")
        
        tk.Label(blackjack_frame, text="♠♣", font=("Arial", 24), 
                fg="#FFD700", bg="#1a472a").pack(pady=(10, 5))
        
        self.btn_blackjack = tk.Button(blackjack_frame,
                                      text="🃏 BLACKJACK 🃏",
                                      font=("Arial", 18, "bold"),
                                      width=25,
                                      height=2,
                                      bg="#2E8B57",
                                      fg="white",
                                      activebackground="#3CB371",
                                      activeforeground="white",
                                      relief="raised",
                                      bd=3,
                                      cursor="hand2",
                                      command=self.jugar_blackjack)
        self.btn_blackjack.pack(pady=(5, 15))
        
        # Botón de Poker mejorado
        poker_frame = tk.Frame(games_frame, bg="#4a1a1a", relief="raised", bd=3)
        poker_frame.pack(pady=15, padx=20, fill="x")
        
        tk.Label(poker_frame, text="♥♦", font=("Arial", 24), 
                fg="#FFD700", bg="#4a1a1a").pack(pady=(10, 5))
        
        self.btn_poker = tk.Button(poker_frame,
                                  text="🎲 Poker Game 🎲",
                                  font=("Arial", 18, "bold"),
                                  width=25,
                                  height=2,
                                  bg="#8B0000",
                                  fg="white",
                                  activebackground="#CD5C5C",
                                  activeforeground="white",
                                  relief="raised",
                                  bd=3,
                                  cursor="hand2",
                                  command=self.jugar_poker)
        self.btn_poker.pack(pady=(5, 15))
        
        # Frame para controles de audio
        audio_frame = tk.LabelFrame(main_frame, 
                                   text="🎵 Control de Audio 🎵",
                                   font=("Arial", 12, "bold"),
                                   fg="#FFD700",
                                   bg="#0F2027",
                                   labelanchor="n")
        audio_frame.pack(pady=30, padx=20, fill="x")
        
        # Control de volumen
        volume_frame = tk.Frame(audio_frame, bg="#0F2027")
        volume_frame.pack(pady=10)
        
        tk.Label(volume_frame, text="Volumen:", 
                font=("Arial", 10), fg="white", bg="#0F2027").pack(side="left", padx=(10, 5))
        
        self.volume_var = tk.DoubleVar(value=30)
        self.volume_scale = tk.Scale(volume_frame,
                                    from_=0, to=100,
                                    orient="horizontal",
                                    variable=self.volume_var,
                                    command=self.cambiar_volumen,
                                    bg="#0F2027",
                                    fg="white",
                                    activebackground="#FFD700",
                                    highlightbackground="#0F2027",
                                    length=200)
        self.volume_scale.pack(side="left", padx=5)
        
        # Botón para pausar/reanudar música
        self.btn_musica = tk.Button(volume_frame,
                                   text="🎵" if self.musica_cargada else "🔇",
                                   font=("Arial", 16),
                                   bg="#4169E1",
                                   fg="white",
                                   activebackground="#6495ED",
                                   relief="raised",
                                   bd=2,
                                   cursor="hand2",
                                   command=self.toggle_musica)
        self.btn_musica.pack(side="left", padx=(10, 5))
        
        # Frame para botón de salir
        exit_frame = tk.Frame(main_frame, bg="#0F2027")
        exit_frame.pack(pady=(30, 10))
        
        self.btn_salir = tk.Button(exit_frame,
                                  text="🚪 SALIR",
                                  font=("Arial", 14, "bold"),
                                  width=15,
                                  height=2,
                                  bg="#696969",
                                  fg="white",
                                  activebackground="#A9A9A9",
                                  activeforeground="black",
                                  relief="raised",
                                  bd=3,
                                  cursor="hand2",
                                  command=self.salir)
        self.btn_salir.pack()
        
        # Footer
        footer = tk.Label(main_frame,
                         text="© 2025 Casino Games - ¡Que tengas suerte! 🍀",
                         font=("Arial", 10, "italic"),
                         fg="#808080",
                         bg="#0F2027")
        footer.pack(side="bottom", pady=10)
        
        # Efectos hover para los botones
        self.setup_hover_effects()
    
    def setup_hover_effects(self):
        def on_enter_blackjack(e):
            self.btn_blackjack.config(bg="#3CB371", relief="raised", bd=5)
        
        def on_leave_blackjack(e):
            self.btn_blackjack.config(bg="#2E8B57", relief="raised", bd=3)
        
        def on_enter_poker(e):
            self.btn_poker.config(bg="#CD5C5C", relief="raised", bd=5)
        
        def on_leave_poker(e):
            self.btn_poker.config(bg="#8B0000", relief="raised", bd=3)
        
        def on_enter_salir(e):
            self.btn_salir.config(bg="#A9A9A9", fg="black")
        
        def on_leave_salir(e):
            self.btn_salir.config(bg="#696969", fg="white")
        
        self.btn_blackjack.bind("<Enter>", on_enter_blackjack)
        self.btn_blackjack.bind("<Leave>", on_leave_blackjack)
        self.btn_poker.bind("<Enter>", on_enter_poker)
        self.btn_poker.bind("<Leave>", on_leave_poker)
        self.btn_salir.bind("<Enter>", on_enter_salir)
        self.btn_salir.bind("<Leave>", on_leave_salir)
    
    def jugar_blackjack(self):
        try:
            messagebox.showinfo("🃏 Blackjack", "¡Iniciando Blackjack! 🎲")
            
            if os.path.exists(RUTA_BLACKJACK):
                subprocess.Popen([sys.executable, RUTA_BLACKJACK])
            else:
                messagebox.showerror("❌ Error", 
                                   f"No se encontró el archivo de Blackjack en:\n{RUTA_BLACKJACK}")
                
        except Exception as e:
            messagebox.showerror("❌ Error", f"No se pudo iniciar Blackjack:\n{str(e)}")
    
    def jugar_poker(self):
        try:
            messagebox.showinfo("🎲 Poker", "¡Iniciando Texas Hold'em! ♠♥♦♣")
            
            if os.path.exists(RUTA_POKER):
                subprocess.Popen([sys.executable, RUTA_POKER])
            else:
                messagebox.showerror("❌ Error", 
                                   f"No se encontró el archivo de Poker en:\n{RUTA_POKER}")
                
        except Exception as e:
            messagebox.showerror("❌ Error", f"No se pudo iniciar Poker:\n{str(e)}")
    
    def salir(self):
        if self.musica_cargada:
            pygame.mixer.music.stop()
            pygame.mixer.quit()
        self.ventana.destroy()
    
    def ejecutar(self):
        # Configurar el cierre de la ventana
        self.ventana.protocol("WM_DELETE_WINDOW", self.salir)
        self.ventana.mainloop()

# Ejecutar la aplicación
if __name__ == "__main__":
    try:
        menu = MenuJuegos()
        menu.ejecutar()
    except Exception as e:
        print(f"Error al iniciar la aplicación: {e}")