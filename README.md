# wtxrc — 远程游戏控制

基于 Web 的 PC 输入远程控制，针对平板和手机进行了优化。

## 功能
- **Element Plus 界面** — 现代且响应式的 UI 组件
- **可视化布局编辑器** — 拖拽按钮、调整大小并配置按键映射
- **自定义按键组合** — 支持修饰键（Ctrl、Alt、Shift 等）与复杂组合（例如 Ctrl+Alt+Del）
- **悬浮覆盖层** — 在 PC 上显示当前被按下的按键
- **低延迟** — 使用 WebSocket 以尽可能降低延迟
- **驾驶模式** — 使用设备陀螺仪模拟方向盘

## 安装

1. 安装 Python 依赖：
   ```bash
   pip install -r requirements.txt
   ```

2. （可选）驾驶模式需要虚拟摇杆：
   - **Windows**：从 https://github.com/ViGEm/ViGEmBus/releases 安装 ViGEmBus 驱动，然后 `pip install vgamepad`
   - **Linux**：`pip install python-uinput`（可能需要 sudo 权限）

## 使用方法

1. 启动服务器：
   ```bash
   python server/app.py
   ```
   *注：在某些全屏游戏中模拟按键需要以管理员权限运行。*

2. 查询电脑的 IP 地址（例如在终端运行 `ipconfig`）。
3. 在平板/手机浏览器中打开：
   `http://<YOUR_PC_IP>:5000`

## 配置

### 模式选择
编辑 `config/config.py` 切换模式：
- `MODE = "custom_keys"` — 默认的按键布局模式
- `MODE = "driving"` — 支持陀螺仪的驾驶模拟模式

### 按钮配置
- 默认按钮在 `config/buttons.json`
- 在网页界面中：
  - 点击 **编辑** 进入编辑模式
  - **拖拽** 按钮以重新布局
  - **双击** 按钮打开配置对话框，可在其中：
    - 设置按钮标签
    - 配置按键组合与修饰键
    - 修改按钮颜色和大小
  - 点击 **添加** 创建新按钮
  - 点击 **保存** 持久化更改

### 修饰键
支持以下修饰键：
- `ctrl`, `ctrl_l`, `ctrl_r` — Control 键
- `shift`, `shift_l`, `shift_r` — Shift 键
- `alt`, `alt_l`, `alt_r`, `alt_gr` — Alt 键
- `cmd`, `cmd_l`, `cmd_r`, `win` — 命令/Windows 键

### 驾驶模式
在驾驶模式下：
1. 将设备连接到电脑
2. 系统会询问是否将该设备设为主设备
3. 主设备的陀螺仪数据将用于转向控制
4. 左右倾斜设备即可转向

## 技术细节

### 触控/指针处理
使用 Pointer Events API 统一触摸与鼠标事件，即使在拖动跨越多个按钮时也能正确跟踪按下的按钮。

### 陀螺仪 API
使用 DeviceOrientation API，并包含对 iOS 13+ 的权限处理说明。
