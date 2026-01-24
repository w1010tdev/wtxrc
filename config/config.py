# wtxrc 配置文件
# 
# 本文件包含 wtxrc 的配置项，可用于在不同模式间切换并自定义行为。

# 模式选择
# - "custom_keys": 自定义按键布局（默认）
# - "driving": 驾驶模拟模式，支持陀螺仪
MODE = "driving"

# 调试选项
DEBUG = True  # 是否输出详细日志
SHOW_JOYSTICK_MONITOR = False  # 是否显示虚拟手柄监视器悬浮窗

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
    # 陀螺仪轴映射到 Xbox 手柄轴（旧格式，保留用于向后兼容）
    # 可选的轴: "left_x", "left_y", "right_x", "right_y", "left_trigger", "right_trigger"
    # 可选的陀螺仪轴: "alpha" (Z轴旋转), "beta" (X轴前后倾斜), "gamma" (Y轴左右倾斜)
    "gyro_axis_mapping": {
        "gamma": "left_x",  # 左右倾斜映射到左摇杆X轴（转向）
        "beta": "left_y",   # 前后倾斜映射到左摇杆Y轴（油门/刹车）
        "alpha": None       # Z轴旋转不映射
    },
    # 拖动条配置列表（在前端配置后保存）
    "sliders": [],
    # 统一轴配置（新格式）
    "axis_config": {
        "left_x": {
            "source_type": "gyro",  # none, gyro, slider
            "source_id": "gamma",   # 陀螺仪轴名称或拖动条ID
            "peak_value": 1.0,      # 峰值（最大输出）
            "deadzone": 0.05,       # 死区
            "gyro_range": 90.0      # 陀螺仪归一化范围（度），90度表示转动90度达到满输出
        },
        "left_y": {
            "source_type": "gyro",
            "source_id": "beta",
            "peak_value": 1.0,
            "deadzone": 0.05,
            "gyro_range": 90.0
        },
        "right_x": {
            "source_type": "none",
            "source_id": None,
            "peak_value": 1.0,
            "deadzone": 0.05,
            "gyro_range": 90.0      # 默认90度，用户可根据需要调整
        },
        "right_y": {
            "source_type": "none",
            "source_id": None,
            "peak_value": 1.0,
            "deadzone": 0.05,
            "gyro_range": 90.0
        },
        "left_trigger": {
            "source_type": "none",
            "source_id": None,
            "peak_value": 1.0,
            "deadzone": 0.05,
            "gyro_range": 90.0
        },
        "right_trigger": {
            "source_type": "none",
            "source_id": None,
            "peak_value": 1.0,
            "deadzone": 0.05,
            "gyro_range": 90.0
        }
    }
}

# 虚拟摇杆设置（驾驶模式）

# Joystick Settings (for driving mode)
JOYSTICK_CONFIG = {
    # 摇杆类型: "xbox360" 或 "custom"
    # xbox360: 使用 Xbox 360 控制器（6轴：left_x, left_y, right_x, right_y, left_trigger, right_trigger）
    # custom: 使用自定义多轴摇杆（可配置轴数量，适用于飞行模拟等场景）
    "type": "xbox360",  # "xbox360" or "custom"
    
    # Virtual joystick name
    "name": "wtxrc 虚拟摇杆", 
    
    # Axis range
    "axis_min": -32767,
    "axis_max": 32767,
    
    # 自定义摇杆配置（仅在 type="custom" 时使用）
    "custom": {
        # 轴的数量（1-32）
        "axis_count": 8,
        
        # 轴映射配置：将 gyro/slider 映射到自定义摇杆的轴
        # 键是轴索引（0-based），值是源配置
        "axis_mapping": {
            # 示例：
            # 0: {
            #     "source_type": "gyro",  # "none", "gyro", "slider"
            #     "source_id": "gamma",   # 陀螺仪轴名称或拖动条ID
            #     "peak_value": 1.0,      # 峰值（最大输出）
            #     "deadzone": 0.05,       # 死区
            #     "gyro_range": 90.0,     # 陀螺仪归一化范围（度）
            #     "invert": False         # 是否反转轴
            # },
            0: {
                "source_type": "gyro",
                "source_id": "gamma",
                "peak_value": 1.0,
                "deadzone": 0.05,
                "gyro_range": 90.0,
                "invert": False
            },
            1: {
                "source_type": "gyro",
                "source_id": "beta",
                "peak_value": 1.0,
                "deadzone": 0.05,
                "gyro_range": 90.0,
                "invert": False
            },
            2: {
                "source_type": "none",
                "source_id": None,
                "peak_value": 1.0,
                "deadzone": 0.05,
                "gyro_range": 90.0,
                "invert": False
            }
        }
    }
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
