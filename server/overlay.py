try:
    import tkinter as tk
    HAS_TKINTER = True
except ImportError:
    HAS_TKINTER = False
    print("Warning: tkinter not available, overlay will be disabled")

from threading import Thread
import queue
import time
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

class OverlayApp:
    def __init__(self, msg_queue):
        self.msg_queue = msg_queue
        self.joystick = None
        self.gyro_processor = None
        
        # Note: Joystick is now managed by main process, overlay only displays
        
        # Run GUI mode if tkinter is available, otherwise headless
        if HAS_TKINTER:
            self.run_gui()
        else:
            self.run_headless()
    
    def run_gui(self):
        """Run overlay in GUI mode with tkinter window."""
        import threading
        
        def gui_thread():
            self.root = tk.Tk()
            self.root.title("WTXRC Overlay")
            self.root.geometry("400x100")
            self.root.attributes("-topmost", True)
            self.root.attributes("-alpha", 0.8)
            self.root.overrideredirect(True)  # Remove window borders
            
            # Position the window higher up on screen
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            x = (screen_width - 400) // 2
            y = (screen_height - 100) // 4  # Position at 1/4 of screen height
            self.root.geometry(f"400x100+{x}+{y}")
            
            # Create label for text display
            self.label = tk.Label(self.root, text="", font=("Arial", 24), bg="black", fg="white")
            self.label.pack(expand=True, fill=tk.BOTH)
            
            # Start hidden
            self.root.withdraw()
            
            # Start checking queue
            self.root.after(50, self.check_queue)
            
            # Start the GUI event loop
            self.root.mainloop()
        
        # Start GUI in a separate thread
        gui_thread = threading.Thread(target=gui_thread, daemon=True)
        gui_thread.start()
        
        # Keep the process alive
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            if hasattr(self, 'root'):
                self.root.quit()
    
    def run_headless(self):
        """Run overlay in headless mode (no GUI, just process messages)."""
        import threading
        self.running = True
        
        def process_loop():
            while self.running:
                try:
                    msg = self.msg_queue.get(timeout=0.1)
                    cmd = msg.get('cmd')
                    if cmd == 'SHOW':
                        text = msg.get('text', '')
                        print(f"[覆盖层] {text}")
                    elif cmd == 'GYRO':
                        # 注意：此处的GYRO处理已经被app.py接管
                        # 这里保留是为了向后兼容，但实际上不再使用
                        # app.py会直接处理陀螺仪数据并应用到虚拟摇杆
                        print(f"[覆盖层] 收到GYRO消息（已由主进程处理）")
                    elif cmd == 'HIDE':
                        print(f"[覆盖层] 隐藏")
                    elif cmd == 'quit':
                        self.running = False
                        return
                except queue.Empty:
                    pass
        
        process_loop()

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
            elif cmd == 'GYRO':
                # 注意：此处的GYRO处理已经被app.py接管
                # 这里保留是为了向后兼容，但实际上不再使用
                # app.py会直接处理陀螺仪数据并应用到虚拟摇杆
                pass
            elif cmd == 'quit':
                self.root.destroy()
                return
        except queue.Empty:
            pass
        self.root.after(50, self.check_queue)

def run_overlay(msg_queue):
    OverlayApp(msg_queue)
