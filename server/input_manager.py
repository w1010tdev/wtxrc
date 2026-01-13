from pynput.keyboard import Key, Controller
import time
import threading

keyboard = Controller()

def parse_key(k):
    k = k.lower()
    if k == 'ctrl': return Key.ctrl
    if k == 'shift': return Key.shift
    if k == 'alt': return Key.alt
    if k == 'enter': return Key.enter
    if k == 'esc': return Key.esc
    if k == 'space': return Key.space
    if k == 'tab': return Key.tab
    if k == 'backspace': return Key.backspace
    if k == 'up': return Key.up
    if k == 'down': return Key.down
    if k == 'left': return Key.left
    if k == 'right': return Key.right
    # Add more as needed
    return k

def execute_combination(keys):
    """
    Presses keys in order, holds them, then releases in reverse order.
    Or just press all then release all.
    """
    parsed_keys = [parse_key(k) for k in keys]
    
    print(f"Executing: {keys}")
    
    # Press all
    for k in parsed_keys:
        keyboard.press(k)
    
    time.sleep(0.1) # Short hold
    
    # Release all
    for k in parsed_keys:
        keyboard.release(k)
