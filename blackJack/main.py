#main.py

import tkinter as tk
from gui_blackjack import BlackjackGUI


def main():
    root = tk.Tk()
    app = BlackjackGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()