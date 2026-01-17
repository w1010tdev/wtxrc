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
        
        # Try to initialize joystick for driving mode
        try:
            from joystick_manager import VirtualJoystick, GyroProcessor
            from config import config
            if config.MODE == 'driving':
                self.joystick = VirtualJoystick()
                self.gyro_processor = GyroProcessor(
                    sensitivity=config.DRIVING_CONFIG.get('gyro_sensitivity', 1.0),
                    deadzone=config.DRIVING_CONFIG.get('gyro_deadzone', 2.0),
                    max_angle=config.DRIVING_CONFIG.get('max_steering_angle', 45.0)
                )
        except Exception as e:
            print(f"Joystick initialization skipped: {e}")
        
        if not HAS_TKINTER:
            # Run without GUI, just process messages
            self.run_headless()
            return
            
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
                        if self.joystick and self.gyro_processor:
                            gamma = msg.get('gamma', 0)
                            steering = self.gyro_processor.process(gamma)
                            self.joystick.set_steering(steering)
                    elif cmd == 'quit':
                        if self.joystick:
                            self.joystick.close()
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
                # Process gyroscope data for driving mode
                if self.joystick and self.gyro_processor:
                    gamma = msg.get('gamma', 0)
                    steering = self.gyro_processor.process(gamma)
                    self.joystick.set_steering(steering)
                    
                    # Optionally show steering value
                    # self.label.config(text=f"Steering: {steering:.2f}")
                    # self.root.deiconify()
            elif cmd == 'quit':
                if self.joystick:
                    self.joystick.close()
                self.root.destroy()
                return
        except queue.Empty:
            pass
        self.root.after(50, self.check_queue)

def run_overlay(msg_queue):
    OverlayApp(msg_queue)
