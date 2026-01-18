"""
Xbox手柄监视器 - 显示虚拟手柄各轴的实时状态
"""

try:
    import tkinter as tk
    from tkinter import Canvas
    HAS_TKINTER = True
except ImportError:
    HAS_TKINTER = False
    print("Warning: tkinter not available, joystick monitor will be disabled")

import threading
import time


class JoystickMonitor:
    """Xbox 手柄状态监视器窗口"""
    
    def __init__(self):
        if not HAS_TKINTER:
            print("[Monitor] tkinter 不可用，监视器已禁用")
            self.enabled = False
            return
        
        self.enabled = True
        self.running = False
        
        # 轴状态 (-1.0 到 1.0)
        self.axes = {
            'left_x': 0.0,
            'left_y': 0.0,
            'right_x': 0.0,
            'right_y': 0.0,
            'left_trigger': 0.0,   # 0.0 到 1.0
            'right_trigger': 0.0,  # 0.0 到 1.0
        }
        
        self.lock = threading.Lock()
        self.root = None
        self.canvas = None
    
    def update_axis(self, axis_name, value):
        """更新轴值"""
        if not self.enabled:
            return
        
        with self.lock:
            if axis_name in self.axes:
                # Trigger 值从 0 到 1
                if 'trigger' in axis_name:
                    self.axes[axis_name] = max(0.0, min(1.0, value))
                else:
                    # 摇杆值从 -1 到 1
                    self.axes[axis_name] = max(-1.0, min(1.0, value))
    
    def start(self):
        """启动监视器窗口（在单独线程中运行）"""
        if not self.enabled or self.running:
            return
        
        self.running = True
        monitor_thread = threading.Thread(target=self._run_window, daemon=True)
        monitor_thread.start()
    
    def stop(self):
        """停止监视器"""
        self.running = False
        if self.root:
            try:
                self.root.quit()
            except:
                pass
    
    def _run_window(self):
        """运行 tkinter 窗口主循环"""
        try:
            self.root = tk.Tk()
            self.root.title("Xbox Monitor")
            
            # 透明悬浮窗设置
            self.root.overrideredirect(True)  # 无边框
            self.root.attributes("-topmost", True)  # 置顶
            self.root.attributes("-alpha", 0.85)  # 透明度 85%
            self.root.configure(bg='#1a1a1a')
            
            # 窗口尺寸 - 更小巧
            width = 380
            height = 200
            
            # 位置在右上角
            screen_width = self.root.winfo_screenwidth()
            x = screen_width - width - 20  # 距离右边20px
            y = 20  # 距离顶部20px
            
            self.root.geometry(f"{width}x{height}+{x}+{y}")
            
            # 简洁的标题栏（用于拖动窗口）
            title_frame = tk.Frame(self.root, bg='#2a2a2a', height=25)
            title_frame.pack(fill='x')
            title_frame.pack_propagate(False)
            
            title_label = tk.Label(
                title_frame,
                text="🎮 Xbox Monitor",
                font=("Arial", 9, "bold"),
                bg='#2a2a2a',
                fg='#00dd00'
            )
            title_label.pack(side='left', padx=8)
            
            # 关闭按钮
            close_btn = tk.Label(
                title_frame,
                text="×",
                font=("Arial", 12, "bold"),
                bg='#2a2a2a',
                fg='#888888',
                cursor='hand2'
            )
            close_btn.pack(side='right', padx=8)
            close_btn.bind('<Button-1>', lambda e: self.stop())
            close_btn.bind('<Enter>', lambda e: close_btn.config(fg='#ff4444'))
            close_btn.bind('<Leave>', lambda e: close_btn.config(fg='#888888'))
            
            # 绑定拖动事件
            title_frame.bind('<Button-1>', self._start_drag)
            title_frame.bind('<B1-Motion>', self._on_drag)
            title_label.bind('<Button-1>', self._start_drag)
            title_label.bind('<B1-Motion>', self._on_drag)
            
            # Canvas - 更紧凑
            self.canvas = Canvas(
                self.root,
                width=width,
                height=height - 25,
                bg='#1a1a1a',
                highlightthickness=0
            )
            self.canvas.pack()
            
            # 启动更新循环
            self._update_display()
            
            self.root.mainloop()
        except Exception as e:
            print(f"[Monitor] 窗口运行异常: {e}")
    
    def _start_drag(self, event):
        """开始拖动"""
        self._drag_x = event.x
        self._drag_y = event.y
    
    def _on_drag(self, event):
        """拖动窗口"""
        x = self.root.winfo_x() + event.x - self._drag_x
        y = self.root.winfo_y() + event.y - self._drag_y
        self.root.geometry(f"+{x}+{y}")
    
    def _update_display(self):
        """更新显示"""
        if not self.running or not self.canvas:
            return
        
        try:
            self.canvas.delete("all")
            
            with self.lock:
                # 绘制左摇杆 - 更小
                self._draw_joystick(65, 90, 50, self.axes['left_x'], self.axes['left_y'], "左摇杆")
                
                # 绘制右摇杆 - 更小
                self._draw_joystick(195, 90, 50, self.axes['right_x'], self.axes['right_y'], "右摇杆")
                
                # 绘制左扳机 - 更简洁
                self._draw_trigger(310, 30, 25, 120, self.axes['left_trigger'], "LT")
                
                # 绘制右扳机 - 更简洁
                self._draw_trigger(345, 30, 25, 120, self.axes['right_trigger'], "RT")
            
            # 每 50ms 更新一次
            self.root.after(50, self._update_display)
        except Exception as e:
            if self.running:
                print(f"[Monitor] 更新显示异常: {e}")
    
    def _draw_joystick(self, center_x, center_y, radius, x_val, y_val, label):
        """绘制摇杆
        
        Args:
            center_x, center_y: 圆心坐标
            radius: 半径
            x_val, y_val: 轴值 (-1.0 到 1.0)
            label: 标签
        """
        # 绘制外圈（灰色）
        self.canvas.create_oval(
            center_x - radius, center_y - radius,
            center_x + radius, center_y + radius,
            outline='#444444',
            width=1,
            fill='#252525'
        )
        
        # 绘制中心十字线
        self.canvas.create_line(
            center_x - radius, center_y,
            center_x + radius, center_y,
            fill='#333333',
            width=1
        )
        self.canvas.create_line(
            center_x, center_y - radius,
            center_x, center_y + radius,
            fill='#333333',
            width=1
        )
        
        # 计算圆点位置
        knob_radius = 6
        knob_x = center_x + x_val * (radius - knob_radius)
        knob_y = center_y - y_val * (radius - knob_radius)  # Y轴反转
        
        # 绘制连接线
        if abs(x_val) > 0.05 or abs(y_val) > 0.05:
            self.canvas.create_line(
                center_x, center_y,
                knob_x, knob_y,
                fill='#00bb00',
                width=1
            )
        
        # 绘制圆点
        color = '#00ff00' if (abs(x_val) > 0.05 or abs(y_val) > 0.05) else '#555555'
        self.canvas.create_oval(
            knob_x - knob_radius, knob_y - knob_radius,
            knob_x + knob_radius, knob_y + knob_radius,
            fill=color,
            outline='#ffffff',
            width=1
        )
        
        # 绘制标签 - 更小的字体
        self.canvas.create_text(
            center_x, center_y + radius + 12,
            text=label,
            fill='#999999',
            font=("Arial", 8)
        )
        
        # 绘制数值 - 更紧凑
        self.canvas.create_text(
            center_x, center_y + radius + 24,
            text=f"{x_val:+.2f} {y_val:+.2f}",
            fill='#666666',
            font=("Consolas", 7)
        )
    
    def _draw_trigger(self, x, y, width, height, value, label):
        """绘制扳机
        
        Args:
            x, y: 左上角坐标
            width, height: 宽高
            value: 扳机值 (0.0 到 1.0)
            label: 标签
        """
        # 绘制背景框
        self.canvas.create_rectangle(
            x, y,
            x + width, y + height,
            outline='#444444',
            width=1,
            fill='#252525'
        )
        
        # 绘制填充（从下往上）
        if value > 0.01:
            fill_height = value * height
            fill_y = y + height - fill_height
            
            # 颜色渐变效果
            if value < 0.5:
                color = '#00bb00'
            elif value < 0.8:
                color = '#ddaa00'
            else:
                color = '#ff4400'
            
            self.canvas.create_rectangle(
                x + 1, fill_y,
                x + width - 1, y + height - 1,
                fill=color,
                outline=''
            )
        
        # 绘制刻度线 - 更简洁
        for i in range(3):
            tick_y = y + height - (i * height / 2)
            self.canvas.create_line(
                x, tick_y,
                x + 4, tick_y,
                fill='#555555',
                width=1
            )
        
        # 绘制标签
        self.canvas.create_text(
            x + width / 2, y - 8,
            text=label,
            fill='#999999',
            font=("Arial", 8)
        )
        
        # 绘制数值
        self.canvas.create_text(
            x + width / 2, y + height + 10,
            text=f"{value:.2f}",
            fill='#666666',
            font=("Consolas", 7)
        )


# 全局监视器实例
_monitor = None


def get_monitor():
    """获取全局监视器实例"""
    global _monitor
    if _monitor is None:
        _monitor = JoystickMonitor()
    return _monitor


def start_monitor():
    """启动监视器"""
    monitor = get_monitor()
    if monitor.enabled:
        monitor.start()
        print("[Monitor] Xbox 手柄监视器已启动")


def stop_monitor():
    """停止监视器"""
    monitor = get_monitor()
    monitor.stop()


def update_axis(axis_name, value):
    """更新轴值"""
    monitor = get_monitor()
    monitor.update_axis(axis_name, value)


if __name__ == "__main__":
    # 测试
    import random
    
    start_monitor()
    print("监视器测试中... (按 Ctrl+C 退出)")
    
    try:
        while True:
            # 模拟随机轴值
            update_axis('left_x', random.uniform(-1, 1))
            update_axis('left_y', random.uniform(-1, 1))
            update_axis('right_x', random.uniform(-1, 1))
            update_axis('right_y', random.uniform(-1, 1))
            update_axis('left_trigger', random.uniform(0, 1))
            update_axis('right_trigger', random.uniform(0, 1))
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\n停止测试")
        stop_monitor()
