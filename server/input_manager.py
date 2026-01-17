import time
import threading

# Try to import pynput, but handle cases where it's not available
try:
    from pynput.keyboard import Key, Controller
    keyboard = Controller()
    HAS_PYNPUT = True
except ImportError as e:
    print(f"Warning: pynput not available: {e}")
    HAS_PYNPUT = False
    keyboard = None
    Key = None

# Key mapping dictionary for easier maintenance (only populated if pynput is available)
KEY_MAP = {}
if HAS_PYNPUT:
    KEY_MAP = {
        # Modifier keys
        'ctrl': Key.ctrl,
        'ctrl_l': Key.ctrl_l,
        'ctrl_r': Key.ctrl_r,
        'shift': Key.shift,
        'shift_l': Key.shift_l,
        'shift_r': Key.shift_r,
        'alt': Key.alt,
        'alt_l': Key.alt_l,
        'alt_r': Key.alt_r,
        'alt_gr': Key.alt_gr,
        'cmd': Key.cmd,
        'cmd_l': Key.cmd_l,
        'cmd_r': Key.cmd_r,
        'win': Key.cmd,  # Alias for Windows key
        
        # Navigation keys
        'enter': Key.enter,
        'return': Key.enter,
        'esc': Key.esc,
        'escape': Key.esc,
        'space': Key.space,
        'tab': Key.tab,
        'backspace': Key.backspace,
        'delete': Key.delete,
        'insert': Key.insert,
        'home': Key.home,
        'end': Key.end,
        'pageup': Key.page_up,
        'page_up': Key.page_up,
        'pagedown': Key.page_down,
        'page_down': Key.page_down,
        
        # Arrow keys
        'up': Key.up,
        'down': Key.down,
        'left': Key.left,
        'right': Key.right,
        
        # Function keys
        'f1': Key.f1,
        'f2': Key.f2,
        'f3': Key.f3,
        'f4': Key.f4,
        'f5': Key.f5,
        'f6': Key.f6,
        'f7': Key.f7,
        'f8': Key.f8,
        'f9': Key.f9,
        'f10': Key.f10,
        'f11': Key.f11,
        'f12': Key.f12,
        
        # Lock keys
        'capslock': Key.caps_lock,
        'caps_lock': Key.caps_lock,
        'numlock': Key.num_lock,
        'num_lock': Key.num_lock,
        'scrolllock': Key.scroll_lock,
        'scroll_lock': Key.scroll_lock,
        
        # Other keys
        'pause': Key.pause,
        'print_screen': Key.print_screen,
        'printscreen': Key.print_screen,
        'menu': Key.menu,
    }

def parse_key(k):
    """Parse a key string and return the corresponding pynput Key or character."""
    k = k.lower().strip()
    
    # Check if it's a special key
    if k in KEY_MAP:
        return KEY_MAP[k]
    
    # If it's a single character, return it as-is
    if len(k) == 1:
        return k
    
    # Unknown key, return as-is
    return k

def execute_combination(keys):
    """
    依次按下按键、保持，然后按相反顺序释放。
    或者一次性按下所有按键再全部释放。
    """
    if not HAS_PYNPUT:
        print(f"[Simulated] Executing: {keys}")
        return
    
    parsed_keys = [parse_key(k) for k in keys]
    
    print(f"Executing: {keys}")
    
    # Press all
    for k in parsed_keys:
        keyboard.press(k)
    
    time.sleep(0.1) # Short hold
    
    # Release all
    for k in parsed_keys:
        keyboard.release(k)
