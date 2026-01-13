import tkinter as tk
from threading import Thread
import queue
import time

class OverlayApp:
    def __init__(self, msg_queue):
        self.msg_queue = msg_queue
        self.root = tk.Tk()
        self.root.overrideredirect(True) # Remove border
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.7) # Transparency
        self.root.configure(bg='black')
        
        # Center of screen roughly, or specific spot
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        w = 400
        h = 100
        x = (screen_width - w) // 2
        y = (screen_height - h) // 4 # Top quarter
        
        self.root.geometry(f"{w}x{h}+{x}+{y}")
        
        self.label = tk.Label(self.root, text="", font=("Helvetica", 24, "bold"), fg="white", bg="black")
        self.label.pack(expand=True, fill='both')
        
        self.root.withdraw() # Start hidden
        
        self.root.after(100, self.check_queue)
        self.root.mainloop()

    def check_queue(self):
        try:
            msg = self.msg_queue.get_nowait()
            cmd = msg.get('cmd')
            if cmd == 'SHOW':
                text = msg.get('text', '')
                self.label.config(text=text)
                self.root.deiconify()
            elif cmd == 'HIDE':
                self.root.withdraw()
            elif cmd == 'quit':
                self.root.destroy()
                return
        except queue.Empty:
            pass
        self.root.after(50, self.check_queue)

def run_overlay(msg_queue):
    OverlayApp(msg_queue)
