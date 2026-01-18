# 自定义虚拟摇杆功能实现总结

## 概述

本次更新为 wtxrc 项目添加了自定义虚拟摇杆功能，允许用户在 Xbox 360 标准模式和自定义多轴摇杆模式之间选择。自定义模式支持 1-32 个可配置轴，适用于飞行模拟、太空模拟等需要更多控制轴的场景。

## 主要变更

### 1. 后端更改

#### config/config.py
- 在 `JOYSTICK_CONFIG` 中添加了 `type` 字段（"xbox360" 或 "custom"）
- 添加了 `custom` 配置块，包含：
  - `axis_count`: 轴数量（1-32）
  - `axis_mapping`: 轴映射配置字典
    - 每个轴支持配置：`source_type`, `source_id`, `peak_value`, `deadzone`, `gyro_range`, `invert`

#### server/joystick_manager.py
- 新增 `CustomVirtualJoystick` 类：
  - 支持 Windows (pyvjoy) 和 Linux (uinput)
  - 可配置 1-32 个轴
  - 每个轴独立控制
- 修改 `VirtualJoystick` 类：
  - 根据配置自动选择 Xbox 360 或自定义模式
  - `set_axis()` 方法支持轴索引（自定义模式）和轴名称（Xbox 360 模式）
  - `reset()` 和 `close()` 方法支持两种模式

#### server/app.py
- 修改 `/api/config` 端点：
  - 返回摇杆类型和自定义摇杆配置
- 修改 `/api/update_driving_config` 端点：
  - 支持保存摇杆类型和自定义摇杆配置
  - 支持保存 Xbox 360 模式的驾驶配置
- 修改 `handle_gyro_data()` 函数：
  - 根据摇杆类型选择不同的轴映射逻辑
  - 自定义模式使用 `custom.axis_mapping`
  - Xbox 360 模式使用原有的 `axis_config`
- 修改 `handle_slider_value()` 函数：
  - 支持自定义摇杆的轴映射

### 2. 前端更改

#### templates/index.html
- 在驾驶配置对话框中添加摇杆类型选择：
  - Xbox 360 控制器（默认）
  - 自定义多轴摇杆
- 为 Xbox 360 模式保留原有的轴配置表格
- 新增自定义摇杆配置界面：
  - 轴数量输入框（1-32）
  - 自定义轴配置表格
    - 支持配置输入源、源选择、峰值、死区、陀螺仪范围
    - 新增轴反转开关

#### static/js/main.js
- 添加状态变量：
  - `joystickType`: 摇杆类型（'xbox360' 或 'custom'）
  - `customJoystickAxisCount`: 自定义摇杆轴数量
  - `customAxisMapping`: 自定义摇杆轴映射配置
- 添加计算属性：
  - `customAxisConfigList`: 自定义轴配置列表
- 添加函数：
  - `onJoystickTypeChange()`: 摇杆类型改变处理
  - `onCustomAxisCountChange()`: 轴数量改变处理
  - `onCustomAxisSourceTypeChange()`: 自定义轴源类型改变处理
  - `getAvailableSlidersForCustomAxis()`: 获取可用的拖动条（排除已绑定）
- 修改 `loadConfig()`:
  - 加载摇杆类型和自定义摇杆配置
- 修改 `saveDrivingConfig()`:
  - 根据摇杆类型保存不同的配置数据

### 3. 文档更新

#### 新增文件
- `CUSTOM_JOYSTICK_GUIDE.md`: 详细的自定义摇杆功能指南
  - 功能特性说明
  - 系统要求（Windows/Linux）
  - 配置方法（配置文件和 Web 界面）
  - 使用场景示例
  - 调试和测试方法
  - 常见问题解答
  - 技术细节

#### 更新文件
- `README.md`:
  - 在功能列表中添加自定义虚拟摇杆说明
  - 更新安装说明，区分 Xbox 360 和自定义模式的依赖
  - 添加虚拟摇杆配置部分
  - 添加到详细指南的链接

- `requirements.txt`:
  - 添加 pyvjoy 的说明（自定义摇杆模式）
  - 区分 Xbox 360 模式和自定义模式的依赖

## 功能亮点

### 1. 灵活的轴配置
- 每个轴可以独立配置输入源（陀螺仪或拖动条）
- 支持峰值、死区和陀螺仪范围的精细调整
- 自定义模式支持轴反转功能

### 2. 向后兼容
- 保留了原有的 Xbox 360 模式作为默认选项
- 现有配置无需修改即可继续使用
- 配置文件自动迁移

### 3. 友好的用户界面
- Web 界面提供直观的配置选项
- 表格形式展示所有轴的配置
- 实时验证（如防止多个轴绑定同一拖动条）

### 4. 跨平台支持
- Windows: 支持 vgamepad (Xbox 360) 和 pyvjoy (自定义)
- Linux: 统一使用 uinput

## 使用示例

### 配置 8 轴飞行摇杆

```python
# config/config.py
JOYSTICK_CONFIG = {
    "type": "custom",
    "custom": {
        "axis_count": 8,
        "axis_mapping": {
            0: {"source_type": "gyro", "source_id": "gamma", "peak_value": 1.0, "deadzone": 0.05, "gyro_range": 45.0, "invert": False},  # 副翼
            1: {"source_type": "gyro", "source_id": "beta", "peak_value": 1.0, "deadzone": 0.05, "gyro_range": 45.0, "invert": False},   # 升降舵
            2: {"source_type": "slider", "source_id": "slider1", "peak_value": 1.0, "deadzone": 0.05, "gyro_range": 90.0, "invert": False},  # 油门
            3: {"source_type": "slider", "source_id": "slider2", "peak_value": 1.0, "deadzone": 0.05, "gyro_range": 90.0, "invert": False},  # 方向舵
            4: {"source_type": "slider", "source_id": "slider3", "peak_value": 1.0, "deadzone": 0.05, "gyro_range": 90.0, "invert": False},  # 襟翼
            5: {"source_type": "none", "source_id": None, "peak_value": 1.0, "deadzone": 0.05, "gyro_range": 90.0, "invert": False},
            6: {"source_type": "none", "source_id": None, "peak_value": 1.0, "deadzone": 0.05, "gyro_range": 90.0, "invert": False},
            7: {"source_type": "none", "source_id": None, "peak_value": 1.0, "deadzone": 0.05, "gyro_range": 90.0, "invert": False},
        }
    }
}
```

## 测试建议

### 基本功能测试
1. ✅ 验证 Xbox 360 模式仍然正常工作
2. ✅ 验证自定义模式可以创建虚拟摇杆
3. ✅ 验证轴映射正确（陀螺仪和拖动条）
4. ✅ 验证死区和峰值配置生效
5. ✅ 验证轴反转功能

### 界面测试
1. ✅ 验证摇杆类型切换
2. ✅ 验证轴数量调整
3. ✅ 验证配置保存和加载
4. ✅ 验证拖动条绑定限制（一个拖动条不能绑定到多个轴）

### 跨平台测试
1. Windows + vJoy
2. Linux + uinput

## 已知限制

1. **Windows vJoy 限制**: 最多支持 8 个轴
2. **Linux uinput 限制**: 取决于可用的轴代码，通常最多 20 个轴
3. **配置生效**: 修改摇杆类型需要重启服务器
4. **驱动依赖**: 需要安装相应的虚拟摇杆驱动

## 未来改进建议

1. 支持更多轴类型（按钮、POV 帽等）
2. 预设配置模板（飞行、赛车、太空等）
3. 热重载配置（无需重启服务器）
4. 轴校准功能
5. 实时轴状态显示

## 总结

本次更新成功为 wtxrc 添加了强大的自定义虚拟摇杆功能，使其能够应对更多样化的游戏控制需求。通过灵活的轴配置和友好的 Web 界面，用户可以轻松定制适合自己游戏的控制方案。
