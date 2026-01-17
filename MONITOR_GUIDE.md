# 调试和监视器使用说明

## 🔧 配置选项

在 `config/config.py` 中添加了两个新配置：

```python
# 调试选项
DEBUG = True  # 是否输出详细日志
SHOW_JOYSTICK_MONITOR = True  # 是否显示虚拟手柄监视器悬浮窗
```

### DEBUG - 调试日志

**启用时 (True)：**
- 显示所有陀螺仪数据接收日志
- 显示所有拖动条值更新日志
- 显示轴映射详细信息
- 显示初始化过程日志

**禁用时 (False)：**
- 仅显示错误和警告信息
- 服务器运行更简洁

### SHOW_JOYSTICK_MONITOR - 手柄监视器

**启用时 (True)：**
- 启动时自动弹出手柄监视器窗口
- 实时显示虚拟手柄各轴状态
- 可视化所有输入

**禁用时 (False)：**
- 不显示监视器窗口
- 节省系统资源

---

## 🎮 手柄监视器界面

监视器窗口布局：

```
┌─────────────────────────────────────────┐
│       🎮 Xbox 手柄状态监视器            │
├─────────────────────────────────────────┤
│                                          │
│    ┌─────┐          ┌─────┐      ║  ║  │
│    │  ●  │          │  ●  │      ║▓▓║  │
│    └─────┘          └─────┘      ║▓▓║  │
│    左摇杆          右摇杆        LT RT  │
│  X:+0.50 Y:-0.30  X:0.00 Y:0.00  0.80   │
│                                    0.00  │
└─────────────────────────────────────────┘
```

### 显示元素

**1. 左摇杆 (Left Stick)**
- 圆形区域显示 left_x 和 left_y
- 绿点位置表示当前摇杆位置
- 中心十字线辅助定位
- 实时数值显示在下方

**2. 右摇杆 (Right Stick)**  
- 圆形区域显示 right_x 和 right_y
- 与左摇杆相同的显示方式

**3. 左扳机 (LT - Left Trigger)**
- 竖向条形显示 left_trigger (0.0-1.0)
- 填充从下往上
- 颜色随值变化：
  - 绿色：0.0-0.5
  - 橙色：0.5-0.8
  - 红色：0.8-1.0

**4. 右扳机 (RT - Right Trigger)**
- 竖向条形显示 right_trigger (0.0-1.0)
- 与左扳机相同的显示方式

### 更新频率

- 20 FPS (每 50ms 更新一次)
- 实时响应，延迟极低

---

## 📊 日志输出示例

### DEBUG = True 时

```
[INIT] 当前模式: driving
[INIT] ✅ 虚拟摇杆已成功初始化
[Monitor] Xbox 手柄监视器已启动
Server started. Access the web interface at http://<your-device-ip>:5000
For Example: http://localhost:5000

[GYRO] 收到陀螺仪数据: alpha=0.00, beta=-10.23, gamma=15.67
[GYRO] 映射 gamma(15.67) -> left_x(0.35)
[GYRO] 映射 beta(-10.23) -> left_y(-0.11)

[SLIDER] 收到拖动条数据: id=btn5, value=0.823
[SLIDER] 应用到轴: right_trigger = 0.823
```

### DEBUG = False 时

```
[INIT] ⚠️ 警告: 虚拟摇杆初始化失败
Server started. Access the web interface at http://<your-device-ip>:5000
For Example: http://localhost:5000
```

只显示关键信息和错误。

---

## 🚀 使用流程

### 开发/调试模式

```python
# config/config.py
MODE = "driving"
DEBUG = True
SHOW_JOYSTICK_MONITOR = True
```

启动服务器：
```bash
python server/app.py
```

你会看到：
1. ✅ 详细的初始化日志
2. 🎮 手柄监视器窗口自动弹出
3. 📝 所有输入的详细日志
4. 👀 实时可视化手柄状态

### 生产模式

```python
# config/config.py
MODE = "driving"
DEBUG = False
SHOW_JOYSTICK_MONITOR = False
```

启动服务器：
```bash
python server/app.py
```

你会看到：
1. ✅ 简洁的启动信息
2. ❌ 无监视器窗口
3. 🔇 无调试日志
4. ⚡ 更少的性能开销

---

## 🎯 测试手柄监视器

### 方法1：使用真实输入

1. 配置启用监视器
2. 启动服务器
3. 手机设为主设备
4. 倾斜手机观察左摇杆移动
5. 拖动拖动条观察扳机填充

### 方法2：独立测试

直接运行监视器脚本：
```bash
python server/joystick_monitor.py
```

会显示随机模拟的手柄输入，用于测试监视器界面。

---

## 🐛 故障排除

### 监视器不显示

**检查：**
1. `SHOW_JOYSTICK_MONITOR = True`
2. tkinter 已安装 (Python 标准库通常自带)
3. 查看终端是否有 `[Monitor]` 相关错误

**Windows 安装 tkinter：**
```bash
# 通常已包含在 Python 安装中
# 如果缺失，重新安装 Python 并勾选 tcl/tk
```

**Linux 安装 tkinter：**
```bash
sudo apt-get install python3-tk
```

### 监视器卡顿

**原因：**
- 系统资源不足
- 其他程序占用 GUI 资源

**解决：**
- 关闭其他程序
- 或者设置 `SHOW_JOYSTICK_MONITOR = False`

### 日志太多

**解决：**
设置 `DEBUG = False` 关闭详细日志。

---

## 💡 使用建议

### 开发阶段
✅ `DEBUG = True`  
✅ `SHOW_JOYSTICK_MONITOR = True`

**优点：**
- 能看到所有数据流
- 快速定位问题
- 直观的可视化反馈

### 日常使用
❌ `DEBUG = False`  
❌ `SHOW_JOYSTICK_MONITOR = False`

**优点：**
- 更简洁的输出
- 更少的性能开销
- 不会分散注意力

### 演示/录制
❌ `DEBUG = False`  
✅ `SHOW_JOYSTICK_MONITOR = True`

**优点：**
- 展示手柄状态
- 无杂乱日志
- 专业的视觉效果

---

## 🎨 监视器自定义

如果想修改监视器外观，编辑 `server/joystick_monitor.py`：

**修改窗口大小：**
```python
width = 500  # 宽度
height = 280  # 高度
```

**修改颜色主题：**
```python
bg='#1e1e1e'  # 背景色（深灰）
fg='#00ff00'  # 文字色（绿色）
```

**修改更新频率：**
```python
self.root.after(50, self._update_display)  # 50ms = 20 FPS
```

改为：
```python
self.root.after(16, self._update_display)  # 16ms = 60 FPS
```

---

## 📋 快速配置表

| 场景 | DEBUG | SHOW_JOYSTICK_MONITOR |
|------|-------|----------------------|
| 🔧 开发调试 | ✅ True | ✅ True |
| 🎮 日常游戏 | ❌ False | ❌ False |
| 🎬 录制演示 | ❌ False | ✅ True |
| 🧪 功能测试 | ✅ True | ✅ True |
| 🚀 生产环境 | ❌ False | ❌ False |

---

## 🔍 性能影响

**DEBUG = True：**
- CPU: +1-2%（日志输出）
- 内存: 可忽略

**SHOW_JOYSTICK_MONITOR = True：**
- CPU: +3-5%（GUI 渲染 @ 20 FPS）
- 内存: +10-20 MB（tkinter 窗口）

**同时启用：**
- CPU: +4-7%
- 内存: +10-20 MB

对于现代电脑来说，影响微乎其微。
