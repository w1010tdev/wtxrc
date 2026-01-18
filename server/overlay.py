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
        
        # Always run in headless mode for server environment
        self.run_headless()
    
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
