# 快速开始：自定义虚拟摇杆

## 示例 1：基本的飞行摇杆配置（4 轴）

### 场景
使用手机/平板作为飞行模拟器的控制器，配置 4 个轴：
- 轴 0：副翼控制（左右倾斜设备）
- 轴 1：升降舵控制（前后倾斜设备）
- 轴 2：油门（使用拖动条）
- 轴 3：方向舵（使用拖动条）

### 步骤

1. **安装依赖**（Windows）：
   ```bash
   # 下载并安装 vJoy 驱动
   # https://sourceforge.net/projects/vjoystick/
   
   # 安装 Python 包
   pip install pyvjoy
   ```

2. **修改 config/config.py**：
   ```python
   MODE = "driving"
   
   JOYSTICK_CONFIG = {
       "type": "custom",
       "name": "Flight Stick",
       "custom": {
           "axis_count": 4,
           "axis_mapping": {
               0: {
                   "source_type": "gyro",
                   "source_id": "gamma",
                   "peak_value": 1.0,
                   "deadzone": 0.05,
                   "gyro_range": 45.0,
                   "invert": False
               },
               1: {
                   "source_type": "gyro",
                   "source_id": "beta",
                   "peak_value": 1.0,
                   "deadzone": 0.05,
                   "gyro_range": 45.0,
                   "invert": False
               },
               2: {
                   "source_type": "slider",
                   "source_id": "slider_throttle",
                   "peak_value": 1.0,
                   "deadzone": 0.02,
                   "gyro_range": 90.0,
                   "invert": False
               },
               3: {
                   "source_type": "slider",
                   "source_id": "slider_rudder",
                   "peak_value": 1.0,
                   "deadzone": 0.02,
                   "gyro_range": 90.0,
                   "invert": False
               }
           }
       }
   }
   ```

3. **启动服务器**：
   ```bash
   python server/app.py
   ```

4. **在 Web 界面添加拖动条**：
   - 点击"编辑"按钮
   - 点击"+ 添加拖动条"
   - 创建两个拖动条：
     - ID: `slider_throttle`，标签: "油门"，方向: 竖向
     - ID: `slider_rudder`，标签: "方向舵"，方向: 竖向

5. **测试**：
   - 设为主设备
   - 倾斜设备测试副翼和升降舵
   - 拖动条控制油门和方向舵

## 示例 2：使用 Web 界面配置

1. **启动服务器**（使用默认配置）：
   ```bash
   python server/app.py
   ```

2. **在 Web 界面配置**：
   - 连接到服务器
   - 点击"⚙️ 驾驶配置"
   - 在对话框顶部选择"自定义多轴摇杆"
   - 设置轴数量为 4
   - 为每个轴配置：
     
     | 轴索引 | 输入源 | 源选择 | 峰值 | 死区 | 陀螺仪范围 | 反转 |
     |--------|--------|--------|------|------|------------|------|
     | 轴 0   | 陀螺仪 | Gamma  | 1.0  | 0.05 | 45         | ❌   |
     | 轴 1   | 陀螺仪 | Beta   | 1.0  | 0.05 | 45         | ❌   |
     | 轴 2   | 拖动条 | 油门   | 1.0  | 0.02 | 90         | ❌   |
     | 轴 3   | 拖动条 | 方向舵 | 1.0  | 0.02 | 90         | ❌   |

3. **保存并重启服务器**

## 示例 3：太空模拟器（6 自由度，12 轴）

```python
JOYSTICK_CONFIG = {
    "type": "custom",
    "name": "6DOF Space Controller",
    "custom": {
        "axis_count": 12,
        "axis_mapping": {
            # 平移控制
            0: {"source_type": "slider", "source_id": "translate_x", ...},
            1: {"source_type": "slider", "source_id": "translate_y", ...},
            2: {"source_type": "slider", "source_id": "translate_z", ...},
            
            # 旋转控制
            3: {"source_type": "gyro", "source_id": "gamma", ...},  # Roll
            4: {"source_type": "gyro", "source_id": "beta", ...},   # Pitch
            5: {"source_type": "gyro", "source_id": "alpha", ...},  # Yaw
            
            # 引擎控制
            6: {"source_type": "slider", "source_id": "main_engine", ...},
            7: {"source_type": "slider", "source_id": "strafe_left", ...},
            8: {"source_type": "slider", "source_id": "strafe_right", ...},
            
            # 其他控制
            9: {"source_type": "none", ...},
            10: {"source_type": "none", ...},
            11: {"source_type": "none", ...}
        }
    }
}
```

## 常见配置技巧

### 1. 轴反转
如果游戏中的轴方向与你的习惯相反，使用反转功能：
```python
"invert": True  # 将正值变为负值，负值变为正值
```

### 2. 调整灵敏度
通过 `peak_value` 调整轴的灵敏度：
```python
"peak_value": 0.5  # 50% 灵敏度
"peak_value": 1.0  # 100% 灵敏度（默认）
```

### 3. 减少漂移
增加死区值来减少轴漂移：
```python
"deadzone": 0.1  # 10% 死区，忽略小于此值的输入
```

### 4. 陀螺仪范围
根据你的控制习惯调整陀螺仪范围：
```python
"gyro_range": 30.0   # 转动 30 度即达到最大值（高灵敏度）
"gyro_range": 90.0   # 转动 90 度即达到最大值（默认）
"gyro_range": 180.0  # 转动 180 度即达到最大值（低灵敏度）
```

## 调试提示

### 查看虚拟摇杆是否创建成功
**Windows:**
- 打开"设置" → "设备" → "蓝牙和其他设备"
- 或者运行 `joy.cpl` 查看游戏控制器

**Linux:**
```bash
# 查看输入设备
ls /dev/input/

# 实时监控
sudo evtest /dev/input/eventX
```

### 启用调试日志
在 `config/config.py` 中：
```python
DEBUG = True
```

查看控制台输出以了解轴值变化。

## 故障排除

### 问题：虚拟摇杆未创建
**检查项：**
- ✅ 是否安装了相应的驱动（vJoy 或 ViGEmBus）
- ✅ 是否安装了 Python 包（pyvjoy 或 vgamepad）
- ✅ 是否重启了服务器
- ✅ 查看控制台是否有错误消息

### 问题：轴没有响应
**检查项：**
- ✅ 确认配置中的 `source_id` 与拖动条的 ID 匹配
- ✅ 确认设备已设为主设备（陀螺仪输入）
- ✅ 检查死区设置是否过大
- ✅ 启用调试模式查看轴值

### 问题：轴方向相反
**解决方案：**
- 在配置中设置 `"invert": True`

## 更多帮助

- 详细文档：[CUSTOM_JOYSTICK_GUIDE.md](CUSTOM_JOYSTICK_GUIDE.md)
- 实现细节：[IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)
- 问题反馈：提交 GitHub Issue
