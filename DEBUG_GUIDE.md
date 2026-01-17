# 调试和测试指南

## 🔍 后端日志说明

### 启动时日志
```
[INIT] 当前模式: driving
[INIT] ✅ 虚拟摇杆已成功初始化
```
或
```
[INIT] ⚠️ 警告: 虚拟摇杆初始化失败
[INIT] ❌ 错误: 虚拟摇杆初始化异常 - [错误详情]
```

### 陀螺仪数据日志
```
[GYRO] 收到陀螺仪数据: alpha=15.23, beta=-5.67, gamma=8.90
[GYRO] 映射 gamma(8.90) -> left_x(0.20)
[GYRO] 映射 beta(-5.67) -> left_y(-0.06)
```
如果虚拟摇杆未初始化：
```
[GYRO] 警告: 虚拟摇杆未初始化
```

### 拖动条数据日志
```
[SLIDER] 收到拖动条数据: id=btn3, value=0.756
[SLIDER] 应用到轴: right_x = 0.756
```
如果配置有问题：
```
[SLIDER] 警告: 找不到拖动条 btn3 的配置或轴映射
[SLIDER] 警告: 虚拟摇杆未初始化
```

### 覆盖层日志
```
[覆盖层] Holding: 跳跃
[覆盖层] 收到GYRO消息（已由主进程处理）
[覆盖层] 隐藏
```

---

## 🔧 问题诊断

### 问题1：虚拟摇杆初始化失败

**症状：**
```
[INIT] ⚠️ 警告: 虚拟摇杆初始化失败
```

**可能原因：**
1. Windows: ViGEmBus 驱动未安装
2. Linux: uinput 模块未加载或权限不足
3. vgamepad 或 python-uinput 包未安装

**解决方法：**
- Windows: 安装 [ViGEmBus](https://github.com/ViGEm/ViGEmBus/releases)
- Linux: 
  ```bash
  sudo modprobe uinput
  sudo usermod -a -G input $USER
  pip install python-uinput
  ```

### 问题2：陀螺仪数据无响应

**检查清单：**
1. 确认设备已设为主设备（手机上应显示"主设备 - 陀螺仪已激活"）
2. 检查日志是否有 `[GYRO] 收到陀螺仪数据`
3. 确认驾驶配置中的轴映射已设置
4. 确认虚拟摇杆已初始化

**测试步骤：**
1. 打开控制台（F12）查看前端日志
2. 倾斜手机，应该看到控制台输出陀螺仪数据
3. 后端终端应该显示 `[GYRO]` 日志

### 问题3：拖动条无响应

**检查清单：**
1. 确认拖动条类型正确（type: 'slider'）
2. 确认拖动条已绑定到Xbox轴（检查 `axis` 属性）
3. 检查日志是否有 `[SLIDER] 收到拖动条数据`
4. 确认虚拟摇杆已初始化

**调试方法：**
1. 编辑模式下双击拖动条，查看配置
2. 确认"绑定到 Xbox 轴"已选择
3. 保存后重启服务器
4. 拖动滑块，查看后端日志

---

## 🧪 测试步骤

### 测试1：陀螺仪轴映射

1. 启动服务器：
   ```bash
   python server/app.py
   ```

2. 观察启动日志：
   ```
   [INIT] 当前模式: driving
   [INIT] ✅ 虚拟摇杆已成功初始化
   ```

3. 手机访问网页，设为主设备

4. 倾斜手机，观察后端日志：
   ```
   [GYRO] 收到陀螺仪数据: alpha=0.00, beta=-10.23, gamma=15.67
   [GYRO] 映射 gamma(15.67) -> left_x(0.35)
   [GYRO] 映射 beta(-10.23) -> left_y(-0.11)
   ```

5. 打开游戏或手柄测试工具，验证虚拟手柄轴是否移动

### 测试2：拖动条功能

1. 进入编辑模式，点击"+ 添加拖动条"

2. 配置拖动条：
   - 标签：油门
   - 方向：竖向
   - 绑定到 Xbox 轴：右扳机
   - 自动归中：关闭

3. 保存并退出编辑模式

4. 拖动滑块，观察后端日志：
   ```
   [SLIDER] 收到拖动条数据: id=btn5, value=0.823
   [SLIDER] 应用到轴: right_trigger = 0.823
   ```

5. 在游戏中验证右扳机是否响应

### 测试3：横向/竖向拖动条

1. 添加横向拖动条
   - 应自动设置为 200x60 尺寸

2. 切换为竖向
   - 应自动调整为 60x200 尺寸

3. 验证拖动条外观：
   - 横向：长条，滑块从左到右移动
   - 竖向：长条，滑块从下到上移动

---

## 📊 性能监控

### 启用详细日志

在 [joystick_manager.py](server/joystick_manager.py) 的 `set_axis` 方法中，取消注释：
```python
print(f"[JOYSTICK] 设置轴 {axis_name} = {value:.3f}")
```

这将输出每次轴更新的详细信息（会产生大量日志）。

### 日志级别

- **启动信息**: `[INIT]` - 服务器启动时的初始化信息
- **陀螺仪**: `[GYRO]` - 陀螺仪数据接收和处理
- **拖动条**: `[SLIDER]` - 拖动条值更新
- **摇杆**: `[JOYSTICK]` - 虚拟摇杆轴设置（详细模式）
- **覆盖层**: `[覆盖层]` - 覆盖层显示状态

---

## 🐛 常见问题

### Q: 拖动条值跳动不稳定
**A:** 这可能是由于：
1. 触摸事件处理频率过高
2. 网络延迟
3. 可以在前端添加节流（throttle）来优化

### Q: 陀螺仪反应迟钝
**A:** 调整配置：
- 增加 `gyro_sensitivity`（默认 1.0）
- 减小 `gyro_deadzone`（默认 2.0）

### Q: 虚拟手柄在游戏中不工作
**A:** 
1. 确认虚拟手柄驱动正确安装
2. 使用手柄测试工具验证虚拟手柄是否被识别
3. Windows: 检查设备管理器中的 "Xbox 360 Controller for Windows"
4. 某些游戏需要重启才能识别新手柄

---

## 📝 代码逻辑说明

### 陀螺仪处理流程

```
手机陀螺仪 -> WebSocket -> handle_gyro_data() 
    -> normalize_gyro_value() 
    -> virtual_joystick.set_axis() 
    -> 虚拟手柄驱动
```

**关键点：**
- overlay 中的 GYRO 处理已废弃，现在统一在 app.py 中处理
- 支持自定义轴映射（通过驾驶配置界面）
- 归一化范围：gamma/beta: -1.0~1.0, alpha: 0~360 -> -1.0~1.0

### 拖动条处理流程

```
前端拖动 -> handleSliderMove() 
    -> WebSocket slider_value 
    -> handle_slider_value() 
    -> virtual_joystick.set_axis() 
    -> 虚拟手柄驱动
```

**关键点：**
- 拖动条配置存储在 `buttons` 数组中（type: 'slider'）
- 轴映射从拖动条的 `axis` 属性读取
- 支持自动归中功能（释放后自动回到 0.0）
- 值范围：-1.0（左/下）到 1.0（右/上）

---

## 🎮 推荐配置示例

### 赛车游戏
```javascript
// 陀螺仪轴映射
gamma -> left_x  // 转向
beta -> (不映射)
alpha -> (不映射)

// 拖动条
拖动条1 (竖向): right_trigger (油门), 不自动归中
拖动条2 (竖向): left_trigger (刹车), 自动归中
```

### 飞行模拟
```javascript
// 陀螺仪轴映射
gamma -> left_x   // 滚转
beta -> left_y    // 俯仰
alpha -> right_x  // 偏航

// 拖动条
拖动条1 (竖向): right_trigger (油门), 不自动归中
```
