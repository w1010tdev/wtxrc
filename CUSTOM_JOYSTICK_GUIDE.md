# 自定义虚拟摇杆功能指南

## 概述

wtxrc 现在支持两种虚拟摇杆模式：

1. **Xbox 360 模式**（默认）：标准的 6 轴控制器（2个摇杆 + 2个扳机）
2. **自定义多轴摇杆模式**：可配置 1-32 个轴，适用于飞行模拟等需要更多控制轴的场景

## 功能特性

### 自定义摇杆模式

- ✅ 支持 1-32 个可配置的轴
- ✅ 每个轴可独立绑定到陀螺仪或拖动条
- ✅ 支持轴反转（正负方向对调）
- ✅ 独立的峰值、死区和陀螺仪范围设置
- ✅ 适用于飞行模拟、太空模拟等多轴控制场景

### 轴映射配置

每个轴可以配置：
- **输入源**：未绑定、陀螺仪或拖动条
- **源选择**：选择具体的陀螺仪轴（gamma/beta/alpha）或拖动条
- **峰值**：轴的最大输出值（0.1-1.0）
- **死区**：忽略小幅输入变化的阈值（0-0.5）
- **陀螺仪范围**：转动多少度达到满输出（1-180度）
- **反转**：反转轴的方向（仅自定义模式）

## 系统要求

### Windows
- **Xbox 360 模式**：
  - ViGEmBus 驱动：https://github.com/ViGEm/ViGEmBus/releases
  - Python 包：`pip install vgamepad`

- **自定义模式**：
  - vJoy 驱动：https://sourceforge.net/projects/vjoystick/
  - Python 包：`pip install pyvjoy`

### Linux
- **Xbox 360 模式**：
  - Python 包：`pip install python-uinput`
  - 加载内核模块：`sudo modprobe uinput`

- **自定义模式**：
  - Python 包：`pip install python-uinput`
  - 加载内核模块：`sudo modprobe uinput`

## 配置方法

### 方法一：通过配置文件（config/config.py）

```python
JOYSTICK_CONFIG = {
    # 摇杆类型: "xbox360" 或 "custom"
    "type": "custom",
    
    # 自定义摇杆配置（仅在 type="custom" 时使用）
    "custom": {
        # 轴的数量（1-32）
        "axis_count": 8,
        
        # 轴映射配置
        "axis_mapping": {
            0: {
                "source_type": "gyro",    # "none", "gyro", "slider"
                "source_id": "gamma",     # 陀螺仪轴或拖动条ID
                "peak_value": 1.0,        # 峰值
                "deadzone": 0.05,         # 死区
                "gyro_range": 90.0,       # 陀螺仪范围（度）
                "invert": False           # 是否反转
            },
            1: {
                "source_type": "gyro",
                "source_id": "beta",
                "peak_value": 1.0,
                "deadzone": 0.05,
                "gyro_range": 90.0,
                "invert": False
            },
            # ... 更多轴配置
        }
    }
}
```

### 方法二：通过 Web 界面

1. 在驾驶模式下，点击 **⚙️ 驾驶配置** 按钮
2. 在对话框顶部选择 **摇杆类型**：
   - 选择 **"自定义多轴摇杆"**
3. 设置 **轴数量**（1-32）
4. 为每个轴配置：
   - **输入源**：选择未绑定、陀螺仪或拖动条
   - **源选择**：选择具体的陀螺仪轴或拖动条
   - **峰值**：调整最大输出强度
   - **死区**：设置死区阈值
   - **陀螺仪范围**：设置陀螺仪归一化范围
   - **反转**：根据需要反转轴方向
5. 点击 **保存** 并 **重启服务器**

## 使用场景示例

### 飞行模拟器

配置 6 个轴用于飞行控制：
- 轴 0：副翼（横滚） - 绑定到陀螺仪 gamma
- 轴 1：升降舵（俯仰） - 绑定到陀螺仪 beta
- 轴 2：方向舵（偏航） - 绑定到陀螺仪 alpha
- 轴 3：油门 - 绑定到拖动条 1
- 轴 4：襟翼 - 绑定到拖动条 2
- 轴 5：刹车 - 绑定到拖动条 3

### 太空模拟器

配置 12 个轴用于六自由度控制：
- 轴 0-2：平移（X/Y/Z）
- 轴 3-5：旋转（Roll/Pitch/Yaw）
- 轴 6-11：其他控制（引擎、武器等）

## 调试和测试

### 检查虚拟摇杆状态

1. 启用调试模式：在 `config/config.py` 中设置 `DEBUG = True`
2. 查看控制台输出，确认：
   - 虚拟摇杆初始化成功
   - 轴映射正确
   - 输入值正确传递到相应轴

### Windows 测试工具
- 使用 Windows 自带的"设置 USB 游戏控制器"查看虚拟摇杆
- 或使用第三方工具如 JoyTest

### Linux 测试工具
```bash
# 查看输入设备
ls /dev/input/

# 使用 evtest 测试
sudo evtest /dev/input/eventX
```

## 常见问题

### Q: 如何在 Xbox 360 和自定义模式之间切换？
A: 修改 `config/config.py` 中的 `JOYSTICK_CONFIG.type`，或在 Web 界面的驾驶配置中切换，然后重启服务器。

### Q: 自定义摇杆最多支持多少个轴？
A: Windows (vJoy) 支持最多 8 个轴，Linux (uinput) 支持最多 20 个轴（取决于可用的轴代码）。

### Q: 为什么虚拟摇杆初始化失败？
A: 
- **Windows**: 确保已安装 vJoy 驱动和 pyvjoy 包
- **Linux**: 确保已加载 uinput 模块并有适当权限

### Q: 可以同时使用陀螺仪和拖动条吗？
A: 是的！每个轴可以独立配置不同的输入源。

### Q: 轴反转功能有什么用？
A: 某些游戏可能需要反向的轴输入（例如反向俯仰），使用反转功能可以不用修改游戏设置就能调整。

## 技术细节

### 轴值范围
- 输入范围：-1.0 到 1.0
- Windows (vJoy)：映射到 1-32768
- Linux (uinput)：映射到 -32767 到 32767

### 支持的陀螺仪轴
- **gamma**：Y轴左右倾斜（设备向左右倾斜）
- **beta**：X轴前后倾斜（设备向前后倾斜）
- **alpha**：Z轴旋转（设备平面内旋转，0-360度）

## 更新日志

### v1.0 - 自定义摇杆功能
- ✅ 新增自定义多轴摇杆支持
- ✅ 支持 1-32 个可配置轴
- ✅ 新增轴反转功能
- ✅ Web 界面配置支持
- ✅ 同时支持 Xbox 360 和自定义模式
