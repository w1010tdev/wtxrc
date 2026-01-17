# wtxrc 配置文件
# 
# 本文件包含 wtxrc 的配置项，可用于在不同模式间切换并自定义行为。

# 模式选择
# - "custom_keys": 自定义按键布局（默认）
# - "driving": 驾驶模拟模式，支持陀螺仪
MODE = "custom_keys"

# 服务器配置
SERVER_HOST = "0.0.0.0"
SERVER_PORT = 5000

# 驾驶模式设置
DRIVING_CONFIG = {
    # 陀螺仪灵敏度倍数
    "gyro_sensitivity": 1.0,
    # 陀螺仪死区（度）
    "gyro_deadzone": 2.0,
    # 最大转向角（度）
    "max_steering_angle": 45.0,
    # 陀螺仪数据更新频率（Hz）
    "gyro_update_rate": 60,
}

# 虚拟摇杆设置（驾驶模式）

# Joystick Settings (for driving mode)
JOYSTICK_CONFIG = {
    # Virtual joystick name
    "name": "wtxrc 虚拟摇杆", 
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
