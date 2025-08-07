import tkinter as tk
from PIL import Image, ImageTk
import random
import os

# Configuración de la ventana principal
root = tk.Tk()
root.title("Blackjack")
root.configure(bg="green")
root.geometry("800x600")

# Ruta a las imágenes de cartas
CARTAS_DIR = "cards"

# Crear baraja completa sin repetir
PALOS = ["Corazones", "Diamantes", "Trebol", "Copas"]
VALORES = ['A'] + [str(i) for i in range(2, 11)] + ['J', 'Q', 'K']

# Crear baraja completa como lista de strings: "A_corazones", "4_picas", etc.
baraja_completa = [f"{valor}_{palo}" for valor in VALORES for palo in PALOS]

# Cargar imágenes
def cargar_imagen(nombre_carta):
    ruta = os.path.join(CARTAS_DIR, f"{nombre_carta}.png")
    imagen = Image.open(ruta).resize((80, 120))  # ajusta tamaño si es necesario
    return ImageTk.PhotoImage(imagen)

# Cargar la imagen del reverso
reverso_img = cargar_imagen("Atras")


# Diccionario para guardar imágenes cargadas y no recargarlas
imagenes_cache = {}

# Función para obtener carta única y su imagen
def repartir_carta():
    carta = random.choice(baraja)
    baraja.remove(carta)
    if carta not in imagenes_cache:
        imagenes_cache[carta] = cargar_imagen(carta)
    return carta, imagenes_cache[carta]

# Frames para el dealer (norte) y el jugador (sur)
dealer_frame = tk.Frame(root, bg="green")
dealer_frame.pack(pady=20)

jugador_frame = tk.Frame(root, bg="green")
jugador_frame.pack(side=tk.BOTTOM, pady=20)

# Función para iniciar una nueva partida
def nueva_partida():
    global baraja
    baraja = baraja_completa.copy()
    random.shuffle(baraja)

    # Limpiar cartas anteriores
    for widget in dealer_frame.winfo_children():
        widget.destroy()
    for widget in jugador_frame.winfo_children():
        widget.destroy()

    # Repartir dos cartas al jugador y una al dealer
    for _ in range(2):
        carta, imagen = repartir_carta()
        tk.Label(jugador_frame, image=imagen, bg="green").pack(side=tk.LEFT, padx=5)

    # Carta visible del dealer
    carta_d, imagen_d = repartir_carta()
    tk.Label(dealer_frame, image=imagen_d, bg="green").pack(side=tk.LEFT, padx=5)

    # Carta oculta del dealer (reverso)
    tk.Label(dealer_frame, image=reverso_img, bg="green").pack(side=tk.LEFT, padx=5)

# Botón para nueva partida
btn_nueva = tk.Button(root, text="Nueva Partida", command=nueva_partida, font=("Arial", 14), bg="white")
btn_nueva.pack(pady=10)

# Iniciar la ventana principal
root.mainloop()
