# W-Touch Remote Configuration File
# 
# This file contains configuration settings for the W-Touch Remote application.
# You can switch between different modes and customize behavior here.

# Mode Selection
# - "custom_keys": Custom button layout mode (default)
# - "driving": Driving simulator mode with gyroscope support
MODE = "custom_keys"

# Server Configuration
SERVER_HOST = "0.0.0.0"
SERVER_PORT = 5000

# Driving Mode Settings
DRIVING_CONFIG = {
    # Gyroscope sensitivity multiplier
    "gyro_sensitivity": 1.0,
    # Dead zone for gyroscope (degrees)
    "gyro_deadzone": 2.0,
    # Maximum steering angle (degrees)
    "max_steering_angle": 45.0,
    # Update rate for gyroscope data (Hz)
    "gyro_update_rate": 60,
}

# Joystick Settings (for driving mode)
JOYSTICK_CONFIG = {
    # Virtual joystick name
    "name": "W-Touch Virtual Joystick",
    # Axis range
    "axis_min": -32767,
    "axis_max": 32767,
}

# Supported Modifier Keys
MODIFIER_KEYS = ["ctrl", "shift", "alt", "cmd", "win"]

# Supported Special Keys
SPECIAL_KEYS = [
    "enter", "esc", "space", "tab", "backspace", "delete",
    "up", "down", "left", "right",
    "home", "end", "pageup", "pagedown",
    "f1", "f2", "f3", "f4", "f5", "f6", "f7", "f8", "f9", "f10", "f11", "f12",
    "insert", "pause", "printscreen", "numlock", "scrolllock", "capslock",
]
