"""
wtxrc 的虚拟摇杆管理器。

该模块为驾驶模式提供虚拟摇杆功能。
It uses vgamepad on Windows or uinput on Linux to create a virtual game controller.
"""

import platform
import threading

class VirtualJoystick:
    """Virtual joystick abstraction layer."""
    
    def __init__(self):
        self.system = platform.system()
        self.gamepad = None
        self.initialized = False
        self._init_gamepad()
    
    def _init_gamepad(self):
        """Initialize the virtual gamepad based on the platform."""
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
            if self.system == 'Linux' and self.gamepad:
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
