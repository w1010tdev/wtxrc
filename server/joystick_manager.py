"""
wtxrc 的虚拟摇杆管理器。

该模块为驾驶模式提供虚拟摇杆功能。
It uses vgamepad on Windows or uinput on Linux to create a virtual game controller.
支持两种模式：
1. Xbox 360 模式：标准 6 轴摇杆
2. 自定义模式：可配置多轴摇杆（适用于飞行模拟等场景）
"""

import platform
import threading
import sys
import os

# 导入监视器
sys.path.insert(0, os.path.dirname(__file__))
try:
    from config import config
    HAS_CONFIG = True
except:
    HAS_CONFIG = False
    config = None

try:
    from joystick_monitor import get_monitor, start_monitor
    HAS_MONITOR = True
except ImportError:
    HAS_MONITOR = False
    print("Warning: joystick_monitor not available")


class CustomVirtualJoystick:
    """自定义多轴虚拟摇杆，支持可配置的轴数量。"""
    
    # Linux uinput axis codes mapping (class constant, lazily initialized when uinput is available)
    UINPUT_AXIS_CODES = None
    _axis_codes_lock = threading.Lock()  # Thread-safe initialization
    
    def __init__(self, axis_count=8, name="Custom Virtual Joystick"):
        """
        初始化自定义虚拟摇杆。
        
        Args:
            axis_count: 轴的数量（1-32）
            name: 摇杆名称
        """
        self.system = platform.system()
        self.axis_count = min(32, max(1, axis_count))  # 限制在 1-32 之间
        self.name = name
        self.gamepad = None
        self.initialized = False
        self.axis_values = [0.0] * self.axis_count  # 存储所有轴的当前值
        self._init_gamepad()
    
    def _init_gamepad(self):
        """根据平台初始化虚拟摇杆。"""
        if self.system == 'Windows':
            try:
                import pyvjoy
                # 使用 vJoy 来创建自定义多轴摇杆
                # 注意：需要安装 vJoy 驱动和 pyvjoy
                self.gamepad = pyvjoy.VJoyDevice(1)  # 使用第一个 vJoy 设备
                self.initialized = True
                print(f"自定义虚拟摇杆已初始化 (Windows, {self.axis_count} 轴)")
            except ImportError:
                print("pyvjoy 未安装。请安装 vJoy 驱动和 pyvjoy:")
                print("1. 从 https://sourceforge.net/projects/vjoystick/ 下载并安装 vJoy")
                print("2. pip install pyvjoy")
            except Exception as e:
                print(f"在 Windows 上初始化自定义虚拟摇杆失败：{e}")
        elif self.system == 'Linux':
            try:
                import uinput
                # Initialize class constant on first use (thread-safe)
                if CustomVirtualJoystick.UINPUT_AXIS_CODES is None:
                    with CustomVirtualJoystick._axis_codes_lock:
                        # Double-check after acquiring lock
                        if CustomVirtualJoystick.UINPUT_AXIS_CODES is None:
                            CustomVirtualJoystick.UINPUT_AXIS_CODES = [
                                uinput.ABS_X, uinput.ABS_Y, uinput.ABS_Z,
                                uinput.ABS_RX, uinput.ABS_RY, uinput.ABS_RZ,
                                uinput.ABS_THROTTLE, uinput.ABS_RUDDER,
                                uinput.ABS_WHEEL, uinput.ABS_GAS, uinput.ABS_BRAKE,
                                uinput.ABS_HAT0X, uinput.ABS_HAT0Y, uinput.ABS_HAT1X,
                                uinput.ABS_HAT1Y, uinput.ABS_HAT2X, uinput.ABS_HAT2Y,
                                uinput.ABS_HAT3X, uinput.ABS_HAT3Y, uinput.ABS_PRESSURE,
                            ]
                
                # 创建包含指定数量轴的 uinput 设备
                events = []
                for i in range(min(self.axis_count, len(CustomVirtualJoystick.UINPUT_AXIS_CODES))):
                    events.append(CustomVirtualJoystick.UINPUT_AXIS_CODES[i] + (-32767, 32767, 0, 0))
                
                self.gamepad = uinput.Device(events, name=self.name)
                self.initialized = True
                print(f"自定义虚拟摇杆已初始化 (Linux, {self.axis_count} 轴)")
            except ImportError:
                print("python-uinput 未安装。请使用以下命令安装：pip install python-uinput")
            except PermissionError:
                print("权限被拒绝。请使用 sudo 运行或添加 uinput 权限。")
                print("可能需要执行：sudo modprobe uinput")
            except Exception as e:
                print(f"在 Linux 上初始化自定义虚拟摇杆失败：{e}")
        else:
            print(f"自定义虚拟摇杆在 {self.system} 上不受支持")
    
    def set_axis(self, axis_index, value):
        """
        设置指定轴的值。
        
        Args:
            axis_index: 轴索引（0-based）
            value: 轴值，范围 -1.0 到 1.0
        """
        if not self.initialized:
            return
        
        if axis_index < 0 or axis_index >= self.axis_count:
            return
        
        # 限制值范围
        value = max(-1.0, min(1.0, value))
        self.axis_values[axis_index] = value
        
        if self.system == 'Windows':
            try:
                import pyvjoy
                # pyvjoy 使用 1-32768 的范围
                # 将 -1.0~1.0 映射到 1~32768
                int_value = int((value + 1.0) * 16383.5 + 1)
                int_value = max(1, min(32768, int_value))
                
                # vJoy 支持最多 8 个轴（从 X 开始顺序映射）
                if axis_index < 8:
                    self.gamepad.set_axis(pyvjoy.HID_USAGE_X + axis_index, int_value)
            except Exception as e:
                if config and config.DEBUG:
                    print(f"设置 Windows 自定义摇杆轴失败：{e}")
        elif self.system == 'Linux':
            try:
                import uinput
                # 将 -1.0~1.0 映射到 -32767~32767
                int_value = int(value * 32767)
                
                if axis_index < len(CustomVirtualJoystick.UINPUT_AXIS_CODES):
                    self.gamepad.emit(CustomVirtualJoystick.UINPUT_AXIS_CODES[axis_index], int_value, syn=True)
            except Exception as e:
                if config and config.DEBUG:
                    print(f"设置 Linux 自定义摇杆轴失败：{e}")
    
    def reset(self):
        """将所有轴重置为中性位置。"""
        for i in range(self.axis_count):
            self.set_axis(i, 0.0)
    
    def close(self):
        """清理资源。"""
        if self.initialized:
            self.reset()
            if self.system == 'Linux' and self.gamepad:
                self.gamepad.destroy()
            self.gamepad = None
            self.initialized = False


class VirtualJoystick:
    """Virtual joystick abstraction layer. 支持 Xbox 360 和自定义多轴模式。"""
    
    def __init__(self, joystick_config=None):
        """
        初始化虚拟摇杆。
        
        Args:
            joystick_config: 摇杆配置字典（来自 buttons.json），如果为 None 则使用 config.py 的默认值
                           格式: {'type': 'xbox360'|'custom', 'custom': {'axis_count': 8, ...}}
        """
        self.system = platform.system()
        self.gamepad = None
        self.initialized = False
        self.joystick_type = "xbox360"  # 默认使用 Xbox 360
        self.custom_joystick = None  # 自定义摇杆实例
        
        # 优先使用传入的配置（来自 buttons.json），否则使用 config.py 作为后备
        if joystick_config:
            self.joystick_type = joystick_config.get('type', 'xbox360')
            self._joystick_config = joystick_config
        elif HAS_CONFIG and hasattr(config, 'JOYSTICK_CONFIG'):
            self.joystick_type = config.JOYSTICK_CONFIG.get('type', 'xbox360')
            self._joystick_config = config.JOYSTICK_CONFIG
        else:
            self._joystick_config = {'type': 'xbox360'}
        
        self._init_gamepad()
        
        # 启动监视器（如果配置允许）
        if HAS_CONFIG and HAS_MONITOR and hasattr(config, 'SHOW_JOYSTICK_MONITOR'):
            if config.SHOW_JOYSTICK_MONITOR:
                start_monitor()
    
    def _init_gamepad(self):
        """Initialize the virtual gamepad based on the platform and configuration."""
        if self.joystick_type == "custom":
            # 使用自定义多轴摇杆
            custom_config = self._joystick_config.get('custom', {})
            axis_count = custom_config.get('axis_count', 8)
            name = self._joystick_config.get('name', 'wtxrc Custom Joystick')
            
            self.custom_joystick = CustomVirtualJoystick(axis_count=axis_count, name=name)
            self.initialized = self.custom_joystick.initialized
            if self.initialized:
                print(f"使用自定义虚拟摇杆模式（{axis_count} 轴）")
            return
        
        # 使用标准 Xbox 360 模式
        if self.system == 'Windows':
            try:
                import vgamepad as vg
                self.gamepad = vg.VX360Gamepad()
                self.initialized = True
                print("Virtual Xbox 360 gamepad initialized (Windows)")
            except ImportError:
                print("vgamepad not installed. Install with: pip install vgamepad")
                print("Also requires ViGEmBus driver: https://github.com/ViGEm/ViGEmBus/releases")
            except Exception as e:
                print(f"在 Windows 上初始化虚拟手柄失败：{e}")
        elif self.system == 'Linux':
            try:
                import uinput
            except ImportError:
                print("python-uinput not installed. Install with: pip install python-uinput")
                return
                
            try:
                self.gamepad = uinput.Device([
                    uinput.ABS_X + (0, 32767, 0, 0),
                    uinput.ABS_Y + (0, 32767, 0, 0),
                    uinput.ABS_RX + (0, 32767, 0, 0),
                    uinput.ABS_RY + (0, 32767, 0, 0),
                    uinput.BTN_A,
                    uinput.BTN_B,
                    uinput.BTN_X,
                    uinput.BTN_Y,
                ])
                self.initialized = True
                print("Virtual gamepad initialized (Linux)")
            except PermissionError:
                print("权限被拒绝。请使用 sudo 运行或添加 uinput 权限。")
                print("You may need to: sudo modprobe uinput")
                print("或者将自己加入 input 组：sudo usermod -a -G input $USER")
            except OSError as e:
                print(f"创建 uinput 设备失败：{e}")
                print("Make sure uinput kernel module is loaded: sudo modprobe uinput")
            except Exception as e:
                print(f"在 Linux 上初始化虚拟手柄失败：{e}")
        else:
            print(f"Virtual joystick not supported on {self.system}")
    
    def set_steering(self, value):
        """
        Set the steering axis value.
        
        Args:
            value: Float from -1.0 (full left) to 1.0 (full right)
        """
        if not self.initialized:
            return
        
        # Clamp value
        value = max(-1.0, min(1.0, value))
        
        if self.system == 'Windows':
            # vgamepad uses -1.0 to 1.0 range
            self.gamepad.left_joystick_float(x_value_float=value, y_value_float=0.0)
            self.gamepad.update()
        elif self.system == 'Linux':
            # uinput uses integer range
            int_value = int((value + 1.0) * 16383.5)  # Map to 0-32767
            self.gamepad.emit(uinput.ABS_X, int_value, syn=True)
    
    def set_axis(self, axis_name, value):
        """
        Set a specific gamepad axis value.
        
        Args:
            axis_name: 对于 Xbox 360 模式："left_x", "left_y", "right_x", "right_y", "left_trigger", "right_trigger"
                      对于自定义模式：轴索引（整数）或字符串形式的索引（如 "0", "1", "2" 等）
            value: Float from -1.0 to 1.0 (for joysticks) or 0.0 to 1.0 (for triggers)
        """
        if not self.initialized:
            return
        
        # 处理自定义摇杆模式
        if self.joystick_type == "custom" and self.custom_joystick:
            # 将轴名称转换为索引
            if isinstance(axis_name, int):
                axis_index = axis_name
            elif isinstance(axis_name, str) and axis_name.isdigit():
                axis_index = int(axis_name)
            else:
                # 如果是字符串但不是数字，可能是从 Xbox 映射过来的
                # 尝试映射到索引
                axis_map = {
                    'left_x': 0,
                    'left_y': 1,
                    'right_x': 2,
                    'right_y': 3,
                    'left_trigger': 4,
                    'right_trigger': 5
                }
                axis_index = axis_map.get(axis_name, None)
                if axis_index is None:
                    if config and config.DEBUG:
                        print(f"未知的自定义摇杆轴名称：{axis_name}")
                    return
            
            # 设置自定义摇杆的轴
            self.custom_joystick.set_axis(axis_index, value)
            return
        
        # Xbox 360 模式的原有逻辑
        # Clamp value
        if 'trigger' in str(axis_name):
            value = max(0.0, min(1.0, value))
        else:
            value = max(-1.0, min(1.0, value))
        
        # 更新监视器
        if HAS_MONITOR:
            try:
                from joystick_monitor import update_axis
                update_axis(axis_name, value)
            except:
                pass
        
        if self.system == 'Windows':
            if axis_name == 'left_x':
                current_y = getattr(self, '_left_y', 0.0)
                self.gamepad.left_joystick_float(x_value_float=value, y_value_float=current_y)
                self._left_x = value
            elif axis_name == 'left_y':
                current_x = getattr(self, '_left_x', 0.0)
                self.gamepad.left_joystick_float(x_value_float=current_x, y_value_float=value)
                self._left_y = value
            elif axis_name == 'right_x':
                current_y = getattr(self, '_right_y', 0.0)
                self.gamepad.right_joystick_float(x_value_float=value, y_value_float=current_y)
                self._right_x = value
            elif axis_name == 'right_y':
                current_x = getattr(self, '_right_x', 0.0)
                self.gamepad.right_joystick_float(x_value_float=current_x, y_value_float=value)
                self._right_y = value
            elif axis_name == 'left_trigger':
                self.gamepad.left_trigger_float(value_float=value)
            elif axis_name == 'right_trigger':
                self.gamepad.right_trigger_float(value_float=value)
            self.gamepad.update()
        elif self.system == 'Linux':
            import uinput
            axis_map = {
                'left_x': uinput.ABS_X,
                'left_y': uinput.ABS_Y,
                'right_x': uinput.ABS_RX,
                'right_y': uinput.ABS_RY,
            }
            if axis_name in axis_map:
                int_value = int((value + 1.0) * 16383.5)  # Map -1.0~1.0 to 0-32767
                self.gamepad.emit(axis_map[axis_name], int_value, syn=True)
    
    def set_throttle(self, value):
        """
        Set the throttle value.
        
        Args:
            value: Float from 0.0 (no throttle) to 1.0 (full throttle)
        """
        if not self.initialized:
            return
        
        # Clamp value
        value = max(0.0, min(1.0, value))
        
        if self.system == 'Windows':
            # Map to right trigger (0.0 to 1.0)
            self.gamepad.right_trigger_float(value_float=value)
            self.gamepad.update()
        elif self.system == 'Linux':
            int_value = int(value * 32767)
            self.gamepad.emit(uinput.ABS_RY, int_value, syn=True)
    
    def set_brake(self, value):
        """
        Set the brake value.
        
        Args:
            value: Float from 0.0 (no brake) to 1.0 (full brake)
        """
        if not self.initialized:
            return
        
        # Clamp value
        value = max(0.0, min(1.0, value))
        
        if self.system == 'Windows':
            # Map to left trigger (0.0 to 1.0)
            self.gamepad.left_trigger_float(value_float=value)
            self.gamepad.update()
        elif self.system == 'Linux':
            int_value = int(value * 32767)
            self.gamepad.emit(uinput.ABS_RX, int_value, syn=True)
    
    def press_button(self, button):
        """Press a gamepad button."""
        if not self.initialized:
            return
        
        if self.system == 'Windows':
            import vgamepad as vg
            button_map = {
                'a': vg.XUSB_BUTTON.XUSB_GAMEPAD_A,
                'b': vg.XUSB_BUTTON.XUSB_GAMEPAD_B,
                'x': vg.XUSB_BUTTON.XUSB_GAMEPAD_X,
                'y': vg.XUSB_BUTTON.XUSB_GAMEPAD_Y,
            }
            if button.lower() in button_map:
                self.gamepad.press_button(button=button_map[button.lower()])
                self.gamepad.update()
        elif self.system == 'Linux':
            import uinput
            button_map = {
                'a': uinput.BTN_A,
                'b': uinput.BTN_B,
                'x': uinput.BTN_X,
                'y': uinput.BTN_Y,
            }
            if button.lower() in button_map:
                self.gamepad.emit(button_map[button.lower()], 1, syn=True)
    
    def release_button(self, button):
        """Release a gamepad button."""
        if not self.initialized:
            return
        
        if self.system == 'Windows':
            import vgamepad as vg
            button_map = {
                'a': vg.XUSB_BUTTON.XUSB_GAMEPAD_A,
                'b': vg.XUSB_BUTTON.XUSB_GAMEPAD_B,
                'x': vg.XUSB_BUTTON.XUSB_GAMEPAD_X,
                'y': vg.XUSB_BUTTON.XUSB_GAMEPAD_Y,
            }
            if button.lower() in button_map:
                self.gamepad.release_button(button=button_map[button.lower()])
                self.gamepad.update()
        elif self.system == 'Linux':
            import uinput
            button_map = {
                'a': uinput.BTN_A,
                'b': uinput.BTN_B,
                'x': uinput.BTN_X,
                'y': uinput.BTN_Y,
            }
            if button.lower() in button_map:
                self.gamepad.emit(button_map[button.lower()], 0, syn=True)
    
    def reset(self):
        """Reset all inputs to neutral."""
        if not self.initialized:
            return
        
        if self.joystick_type == "custom" and self.custom_joystick:
            self.custom_joystick.reset()
            return
        
        if self.system == 'Windows':
            self.gamepad.reset()
            self.gamepad.update()
        elif self.system == 'Linux':
            import uinput
            self.gamepad.emit(uinput.ABS_X, 16383, syn=False)
            self.gamepad.emit(uinput.ABS_Y, 16383, syn=False)
            self.gamepad.emit(uinput.ABS_RX, 0, syn=False)
            self.gamepad.emit(uinput.ABS_RY, 0, syn=True)
    
    def close(self):
        """Clean up resources."""
        if self.initialized:
            self.reset()
            if self.joystick_type == "custom" and self.custom_joystick:
                self.custom_joystick.close()
                self.custom_joystick = None
            elif self.system == 'Linux' and self.gamepad:
                self.gamepad.destroy()
            self.gamepad = None
            self.initialized = False


class GyroProcessor:
    """Process gyroscope data and convert to steering input."""
    
    def __init__(self, sensitivity=1.0, deadzone=2.0, max_angle=45.0):
        self.sensitivity = sensitivity
        self.deadzone = deadzone
        self.max_angle = max_angle
        self.calibration_offset = 0.0
    
    def calibrate(self, current_gamma):
        """Set current position as center."""
        self.calibration_offset = current_gamma
    
    def process(self, gamma):
        """
        Convert gyroscope gamma (left-right tilt) to steering value.
        
        Args:
            gamma: Device tilt in degrees (-90 to 90)
        
        Returns:
            Steering value from -1.0 to 1.0
        """
        # Apply calibration offset
        adjusted = gamma - self.calibration_offset
        
        # Apply deadzone
        if abs(adjusted) < self.deadzone:
            return 0.0
        
        # Remove deadzone from calculation
        if adjusted > 0:
            adjusted -= self.deadzone
        else:
            adjusted += self.deadzone
        
        # Normalize to -1.0 to 1.0 range
        effective_max = self.max_angle - self.deadzone
        steering = (adjusted / effective_max) * self.sensitivity
        
        # Clamp output
        return max(-1.0, min(1.0, steering))
