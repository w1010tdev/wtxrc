from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import json
import os
import sys
import multiprocessing
from overlay import run_overlay
import input_manager
import signal
import time

# 将配置目录加入路径以便导入
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config import config

app = Flask(__name__, template_folder="../templates", static_folder="../static")
app.config['SECRET_KEY'] = 'secret!'
CORS(app)  # 启用CORS
socketio = SocketIO(app, cors_allowed_origins="*")

# IPC Queue for Overlay
overlay_queue = multiprocessing.Queue()
overlay_process = None

# Store connected devices and their roles
connected_devices = {}
main_device_sid = None

# Virtual joystick instance
virtual_joystick = None
slider_values = {}  # 存储拖动条当前值

# 向后兼容常量：旧配置（没有axis_config）使用的陀螺仪范围
LEGACY_GYRO_RANGE = 45.0

CONFIG_PATH = os.path.join(os.path.dirname(__file__), '../config/buttons.json')

def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"buttons": []}

def save_config(data):
    # Ensure directory exists
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/config')
def get_config():
    button_config = load_config()
    # 从 config.py 加载模式和其它设置
    button_config['mode'] = config.MODE
    button_config['modifier_keys'] = config.MODIFIER_KEYS
    button_config['special_keys'] = config.SPECIAL_KEYS
    
    # 加载摇杆配置（优先使用 buttons.json 中的用户配置，否则使用 config.py 的默认值）
    if 'joystick_type' not in button_config and hasattr(config, 'JOYSTICK_CONFIG'):
        button_config['joystick_type'] = config.JOYSTICK_CONFIG.get('type', 'xbox360')
    if 'custom_joystick' not in button_config and hasattr(config, 'JOYSTICK_CONFIG'):
        if button_config.get('joystick_type') == 'custom':
            button_config['custom_joystick'] = config.JOYSTICK_CONFIG.get('custom', {})
    
    # 优先使用 buttons.json 中的 driving_config，如果没有则使用 config.py 中的默认值
    if config.MODE == 'driving':
        if 'driving_config' not in button_config:
            button_config['driving_config'] = config.DRIVING_CONFIG
            
    return jsonify(button_config)

@app.route('/api/update_button', methods=['POST'])
def update_button():
    """Update a single button's configuration"""
    data = request.json
    btn_id = data.get('id')
    current_config = load_config()
    
    for i, btn in enumerate(current_config['buttons']):
        if btn['id'] == btn_id:
            # Update the button with new data
            current_config['buttons'][i].update(data)
            break
    else:
        # 未找到按钮 -> 添加它
        current_config['buttons'].append(data)
    
    save_config(current_config)
    return jsonify({'status': 'success'})

@app.route('/api/add_button', methods=['POST'])
def add_button():
    """添加一个新按钮"""
    data = request.json
    current_config = load_config()
    
    # Generate unique ID
    existing_ids = [btn['id'] for btn in current_config['buttons']]
    new_id = f"btn{len(existing_ids) + 1}"
    while new_id in existing_ids:
        new_id = f"btn{len(existing_ids) + int(new_id[-1]) + 1}"
    
    data['id'] = new_id
    current_config['buttons'].append(data)
    save_config(current_config)
    return jsonify({'status': 'success', 'id': new_id})

@app.route('/api/delete_button', methods=['POST'])
def delete_button():
    """Delete a button"""
    data = request.json
    btn_id = data.get('id')
    current_config = load_config()
    
    current_config['buttons'] = [btn for btn in current_config['buttons'] if btn['id'] != btn_id]
    save_config(current_config)
    return jsonify({'status': 'success'})

@app.route('/api/update_driving_config', methods=['POST'])
def update_driving_config():
    """更新驾驶模式配置（陀螺仪轴映射和拖动条，或自定义摇杆配置）"""
    try:
        if config.DEBUG:
            print("[CONFIG] 收到驾驶配置更新请求")
            print(f"[CONFIG] 请求方法: {request.method}")
            print(f"[CONFIG] 请求头: {dict(request.headers)}")
        
        data = request.json
        if config.DEBUG:
            print(f"[CONFIG] 请求数据: {data}")
        
        # 保存到buttons.json中
        current_config = load_config()
        
        # 检查是否包含摇杆类型配置
        if data and 'joystick_type' in data:
            current_config['joystick_type'] = data['joystick_type']
            if config.DEBUG:
                print(f"[CONFIG] 摇杆类型: {data['joystick_type']}")
            
            # 如果是自定义摇杆，保存自定义配置
            if data['joystick_type'] == 'custom' and 'custom_joystick' in data:
                current_config['custom_joystick'] = data['custom_joystick']
                if config.DEBUG:
                    print(f"[CONFIG] 自定义摇杆配置: {data['custom_joystick']}")
        
        # 如果包含 Xbox 360 的驾驶配置
        if data and 'driving_config' in data:
            driving_config = data['driving_config']
            current_config['driving_config'] = driving_config
            if config.DEBUG:
                print(f"[CONFIG] 驾驶配置内容: {driving_config}")
        
        save_config(current_config)
        
        if config.DEBUG:
            print("[CONFIG] 驾驶配置保存成功")
        
        response = jsonify({'status': 'success', 'message': '配置已保存，请重启服务器以应用更改'})
        if config.DEBUG:
            print(f"[CONFIG] 返回响应: {response.get_json()}")
        return response
    except Exception as e:
        if config.DEBUG:
            print(f"[CONFIG] 保存配置时发生错误: {e}")
            import traceback
            traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)}), 500
        
    except Exception as e:
        print(f"[CONFIG] 错误: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@socketio.on('connect')
def handle_connect():
    global connected_devices
    sid = request.sid
    connected_devices[sid] = {'role': None, 'is_main': False}
    
    # In driving mode, ask if this should be the main device
    if config.MODE == 'driving':
        emit('ask_main_device', {'current_main': main_device_sid is not None})

@socketio.on('disconnect')
def handle_disconnect():
    global connected_devices, main_device_sid
    sid = request.sid
    if sid in connected_devices:
        if connected_devices[sid].get('is_main'):
            main_device_sid = None
        del connected_devices[sid]

@socketio.on('set_main_device')
def handle_set_main_device(data):
    global main_device_sid, connected_devices
    sid = request.sid
    is_main = data.get('is_main', False)
    
    if is_main:
        # 从之前的主设备移除主设备状态
        if main_device_sid and main_device_sid in connected_devices:
            connected_devices[main_device_sid]['is_main'] = False
            socketio.emit('main_status_changed', {'is_main': False}, to=main_device_sid)
        
        main_device_sid = sid
        connected_devices[sid]['is_main'] = True
        emit('main_status_changed', {'is_main': True})
    else:
        if main_device_sid == sid:
            main_device_sid = None
        connected_devices[sid]['is_main'] = False
        emit('main_status_changed', {'is_main': False})

@socketio.on('gyro_data')
def handle_gyro_data(data):
    """处理来自主设备的驾驶模式陀螺仪数据"""
    global main_device_sid, virtual_joystick
    sid = request.sid
    
    # 仅接受来自主设备的陀螺仪数据
    if sid != main_device_sid:
        return
    
    alpha = data.get('alpha', 0)  # Z-axis rotation
    beta = data.get('beta', 0)    # X-axis rotation (front-back tilt)
    gamma = data.get('gamma', 0)  # Y-axis rotation (left-right tilt)
    
    if config.DEBUG:
        print(f"[GYRO] 收到陀螺仪数据: alpha={alpha:.2f}, beta={beta:.2f}, gamma={gamma:.2f}")
    
    # 发送到 overlay 进程用于显示（overlay 进程会显示陀螺仪数值，但不处理轴映射）
    overlay_queue.put({
        'cmd': 'GYRO',
        'alpha': alpha,
        'beta': beta,
        'gamma': gamma
    })
    
    # 应用陀螺仪数据到虚拟手柄（如果已初始化）
    if virtual_joystick and virtual_joystick.initialized:
        button_config = load_config()
        
        # 检查是否使用自定义摇杆模式（优先使用 buttons.json，否则使用 config.py）
        joystick_type = button_config.get('joystick_type', config.JOYSTICK_CONFIG.get('type', 'xbox360'))
        
        if joystick_type == 'custom':
            # 使用自定义摇杆的轴映射（优先使用 buttons.json）
            custom_config = button_config.get('custom_joystick', config.JOYSTICK_CONFIG.get('custom', {}))
            axis_mapping = custom_config.get('axis_mapping', {})
            
            gyro_values = {'alpha': alpha, 'beta': beta, 'gamma': gamma}
            for axis_index, axis_cfg in axis_mapping.items():
                if isinstance(axis_index, str):
                    axis_index = int(axis_index)
                
                if axis_cfg.get('source_type') == 'gyro' and axis_cfg.get('source_id'):
                    gyro_axis = axis_cfg['source_id']
                    if gyro_axis in gyro_values:
                        gyro_range = axis_cfg.get('gyro_range', 90.0)
                        raw_value = normalize_gyro_value(gyro_values[gyro_axis], gyro_axis, gyro_range)
                        
                        # 应用死区
                        value = apply_deadzone(raw_value, axis_cfg.get('deadzone', 0.05))
                        # 应用峰值限制
                        value = apply_peak_value(value, axis_cfg.get('peak_value', 1.0))
                        # 应用反转
                        if axis_cfg.get('invert', False):
                            value = -value
                        
                        if config.DEBUG:
                            print(f"[GYRO] 自定义摇杆: 映射 {gyro_axis}({gyro_values[gyro_axis]:.2f}) -> 轴{axis_index}({value:.2f})")
                        virtual_joystick.set_axis(axis_index, value)
        else:
            # 使用 Xbox 360 模式的轴配置
            axis_config = button_config.get('driving_config', {}).get('axis_config', {})
            
            # 如果没有新的轴配置，回退到旧的 gyro_axis_mapping
            if not axis_config:
                gyro_mapping = button_config.get('driving_config', {}).get('gyro_axis_mapping', {})
                if not gyro_mapping:
                    gyro_mapping = config.DRIVING_CONFIG.get('gyro_axis_mapping', {})
                
                # 使用旧的映射方式（使用 LEGACY_GYRO_RANGE 保持向后兼容）
                gyro_values = {'alpha': alpha, 'beta': beta, 'gamma': gamma}
                for gyro_axis, gamepad_axis in gyro_mapping.items():
                    if gamepad_axis and gyro_axis in gyro_values:
                        value = normalize_gyro_value(gyro_values[gyro_axis], gyro_axis, LEGACY_GYRO_RANGE)
                        if config.DEBUG:
                            print(f"[GYRO] 映射 {gyro_axis}({gyro_values[gyro_axis]:.2f}) -> {gamepad_axis}({value:.2f})")
                        virtual_joystick.set_axis(gamepad_axis, value)
            else:
                # 使用新的统一轴配置
                gyro_values = {'alpha': alpha, 'beta': beta, 'gamma': gamma}
                for gamepad_axis, axis_cfg in axis_config.items():
                    if axis_cfg.get('source_type') == 'gyro' and axis_cfg.get('source_id'):
                        gyro_axis = axis_cfg['source_id']
                        if gyro_axis in gyro_values:
                            gyro_range = axis_cfg.get('gyro_range', 45.0)  # 获取陀螺仪范围，默认45度
                            raw_value = normalize_gyro_value(gyro_values[gyro_axis], gyro_axis, gyro_range)
                            # 应用死区
                            value = apply_deadzone(raw_value, axis_cfg.get('deadzone', 0.05))
                            # 应用峰值限制
                            value = apply_peak_value(value, axis_cfg.get('peak_value', 1.0))
                            if config.DEBUG:
                                print(f"[GYRO] 映射 {gyro_axis}({gyro_values[gyro_axis]:.2f}) -> {gamepad_axis}({value:.2f}) [range={gyro_range}, deadzone={axis_cfg.get('deadzone', 0.05)}, peak={axis_cfg.get('peak_value', 1.0)}]")
                            virtual_joystick.set_axis(gamepad_axis, value)
                    elif axis_cfg.get('source_type') == 'none':
                        # 当轴配置为 none 时，显式将该轴重置为 0，避免保留上一次的陀螺仪值
                        if config.DEBUG:
                            print(f"[GYRO] 轴 {gamepad_axis} 的 source_type=none，重置为 0")
                        virtual_joystick.set_axis(gamepad_axis, 0.0)
    else:
        if config.DEBUG:
            print("[GYRO] 警告: 虚拟摇杆未初始化")

@socketio.on('button_down')
def handle_button_down(data):
    btn_id = data.get('id')
    label = data.get('label')
    # Show overlay
    overlay_queue.put({'cmd': 'SHOW', 'text': f"Holding: {label}"})

@socketio.on('button_up')
def handle_button_up(data):
    btn_id = data.get('id')
    print(f"Button released: {btn_id}")
    
    # Hide overlay
    overlay_queue.put({'cmd': 'HIDE'})
    
    # Execute keys
    button_config = load_config()
    btn = next((b for b in button_config['buttons'] if b['id'] == btn_id), None)
    if btn:
        input_manager.execute_combination(btn.get('keys', []))

@socketio.on('hide_overlay')
def handle_hide_overlay():
    """处理隐藏overlay的请求"""
    print("Hiding overlay")
    overlay_queue.put({'cmd': 'HIDE'})

@socketio.on('slider_value')
def handle_slider_value(data):
    """处理拖动条值的更新"""
    global virtual_joystick, slider_values
    slider_id = data.get('id')
    value = data.get('value', 0.0)  # -1.0 到 1.0
    
    if config.DEBUG:
        print(f"[SLIDER] 收到拖动条数据: id={slider_id}, value={value:.3f}")
    
    # 保存当前值
    slider_values[slider_id] = value
    
    # 应用到虚拟手柄（如果已初始化）
    if virtual_joystick and virtual_joystick.initialized:
        if config.DEBUG:
            print("[SLIDER] 虚拟摇杆已初始化，应用拖动条值")
        button_config = load_config()
        buttons = button_config.get('buttons', [])
        
        # 找到滑块的展示标签/autoCenter 信息（如果存在）
        slider_btn = next((b for b in buttons if b.get('id') == slider_id and b.get('type') == 'slider'), None)
        slider_label = slider_btn.get('label') if slider_btn else slider_id
        slider_auto_center = bool(slider_btn.get('autoCenter')) if slider_btn else False
        
        # 显示 overlay（实时显示正在操作的滑块）
        try:
            overlay_queue.put({'cmd': 'SHOW', 'text': f"{slider_label}: {value:.2f}"})
        except Exception:
            pass
        
        # 检查是否使用自定义摇杆模式（优先使用 buttons.json，否则使用 config.py）
        joystick_type = button_config.get('joystick_type', config.JOYSTICK_CONFIG.get('type', 'xbox360'))
        
        if joystick_type == 'custom':
            # 使用自定义摇杆的轴映射（优先使用 buttons.json）
            custom_config = button_config.get('custom_joystick', config.JOYSTICK_CONFIG.get('custom', {}))
            axis_mapping = custom_config.get('axis_mapping', {})
            
            for axis_index, axis_cfg in axis_mapping.items():
                if isinstance(axis_index, str):
                    axis_index = int(axis_index)
                
                if axis_cfg.get('source_type') == 'slider' and axis_cfg.get('source_id') == slider_id:
                    # 应用死区
                    processed_value = apply_deadzone(value, axis_cfg.get('deadzone', 0.05))
                    # 应用峰值限制
                    processed_value = apply_peak_value(processed_value, axis_cfg.get('peak_value', 1.0))
                    # 应用反转
                    if axis_cfg.get('invert', False):
                        processed_value = -processed_value
                    
                    if config.DEBUG:
                        print(f"[SLIDER] 自定义摇杆: 应用到轴{axis_index} = {processed_value:.3f}")
                    virtual_joystick.set_axis(axis_index, processed_value)
                    break
        else:
            # 使用 Xbox 360 模式的轴配置
            axis_config = button_config.get('driving_config', {}).get('axis_config', {})
            
            # 如果没有新的轴配置，回退到旧方式
            if not axis_config:
                if config.DEBUG:
                    print("[SLIDER] 警告: 找不到按钮新版配置")
                slider = next((b for b in buttons if b.get('id') == slider_id and b.get('type') == 'slider'), None)
                
                if slider and slider.get('axis'):
                    axis = slider['axis']
                    if config.DEBUG:
                        print(f"[SLIDER] 应用到轴: {axis} = {value:.3f}")
                    virtual_joystick.set_axis(axis, value)
                else:
                    if config.DEBUG:
                        print(f"[SLIDER] 警告: 找不到拖动条 {slider_id} 的配置或轴映射")
            else:
                if config.DEBUG:
                    print("[SLIDER] 使用新版统一轴配置应用拖动条值")
                    print(f"[SLIDER] axis_config: {axis_config}")
                    print(f"[SLIDER] 查找 slider_id: {slider_id}")
                # 使用新的统一轴配置
                for gamepad_axis, axis_cfg in axis_config.items():
                    if config.DEBUG:
                        print(f"[SLIDER] 检查轴 {gamepad_axis}: {axis_cfg}")
                    if axis_cfg.get('source_type') == 'slider' and axis_cfg.get('source_id') == slider_id:
                        # 应用死区
                        processed_value = apply_deadzone(value, axis_cfg.get('deadzone', 0.05))
                        # 应用峰值限制
                        processed_value = apply_peak_value(processed_value, axis_cfg.get('peak_value', 1.0))
                        if config.DEBUG:
                            print(f"[SLIDER] 应用到轴: {gamepad_axis} = {processed_value:.3f} [原始={value:.3f}, deadzone={axis_cfg.get('deadzone', 0.05)}, peak={axis_cfg.get('peak_value', 1.0)}]")
                        virtual_joystick.set_axis(gamepad_axis, processed_value)
                        break
        
        # 如果滑块设置为自动归中并且回到默认值，则隐藏 overlay
        try:
            default_val = 0.5 if (slider_btn and slider_btn.get('rangeMode') == 'unipolar') else 0.0
            if slider_auto_center and abs(value - default_val) < 1e-3:
                try:
                    overlay_queue.put({'cmd': 'HIDE'})
                except Exception:
                    pass
        except Exception:
            pass
    else:
        if config.DEBUG:
            print("[SLIDER] 警告: 虚拟摇杆未初始化")

@socketio.on('save_layout')
def handle_save_layout(data):
    """Save the current button layout."""
    print("Saving Layout...")
    current_config = load_config()
    current_config['buttons'] = data
    save_config(current_config)
    emit('layout_saved', {'status': 'success'})

def normalize_gyro_value(gyro_value, gyro_axis, gyro_range=45.0):
    """将陀螺仪值归一化到 -1.0 到 1.0 范围
    
    Args:
        gyro_value: 陀螺仪原始值（度）
        gyro_axis: 陀螺仪轴名称 ('alpha', 'beta', 'gamma')
        gyro_range: 归一化范围（度），表示转动多少度达到满输出
    
    Returns:
        归一化后的值，范围 [-1.0, 1.0]
    """
    if gyro_axis == 'alpha':  # Z轴旋转，范围 0 到 360
        # 转换为 -180 到 180
        normalized = gyro_value if gyro_value <= 180 else gyro_value - 360
        return max(-1.0, min(1.0, normalized / gyro_range))
    else:  # gamma (左右倾斜) 和 beta (前后倾斜)
        return max(-1.0, min(1.0, gyro_value / gyro_range))


def apply_deadzone(value, deadzone):
    """应用死区到输入值"""
    # 使用 <= 来处理边界情况，确保在死区阈值处的连续性
    if abs(value) <= deadzone:
        return 0.0
    # 防止除以零
    if deadzone >= 1.0:
        return 0.0
    # 移除死区后重新映射到完整范围
    if value > 0:
        return (value - deadzone) / (1.0 - deadzone)
    else:
        return (value + deadzone) / (1.0 - deadzone)

def apply_peak_value(value, peak_value):
    """应用峰值限制到输入值"""
    return value * peak_value

def init_virtual_joystick():
    """初始化驾驶模式的虚拟摇杆"""
    global virtual_joystick
    if config.DEBUG:
        print(f"[INIT] 当前模式: {config.MODE}")
    if config.MODE == 'driving':
        try:
            from joystick_manager import VirtualJoystick
            # 加载配置（优先使用 buttons.json，否则使用 config.py）
            button_config = load_config()
            joystick_config = None
            
            # 从 buttons.json 构建摇杆配置
            if 'joystick_type' in button_config:
                joystick_config = {
                    'type': button_config['joystick_type'],
                    'name': button_config.get('joystick_name', 'wtxrc Custom Joystick')
                }
                if button_config['joystick_type'] == 'custom' and 'custom_joystick' in button_config:
                    joystick_config['custom'] = button_config['custom_joystick']
            
            # 传递配置到 VirtualJoystick（会自动回退到 config.py 如果 joystick_config 为 None）
            virtual_joystick = VirtualJoystick(joystick_config=joystick_config)
            if virtual_joystick.initialized:
                if config.DEBUG:
                    print("[INIT] ✅ 虚拟摇杆已成功初始化")
            else:
                print("[INIT] ⚠️ 警告: 虚拟摇杆初始化失败")
        except Exception as e:
            print(f"[INIT] ❌ 错误: 虚拟摇杆初始化异常 - {e}")
            import traceback
            traceback.print_exc()
    else:
        if config.DEBUG:
            print(f"[INIT] 非驾驶模式，跳过虚拟摇杆初始化")

def start_overlay():
    global overlay_process
    overlay_process = multiprocessing.Process(target=run_overlay, args=(overlay_queue,))
    overlay_process.daemon = True
    overlay_process.start()


def shutdown_server(grace_period: float = 2.0):
    """Attempt to gracefully shutdown background resources."""
    global overlay_process, virtual_joystick
    try:
        if config.DEBUG:
            print("[SHUTDOWN] 开始优雅关闭流程")

        # 请求 overlay 进程退出
        try:
            overlay_queue.put({'cmd': 'quit'})
        except Exception:
            pass

        # 等待 overlay 进程结束
        if overlay_process is not None:
            if config.DEBUG:
                print(f"[SHUTDOWN] 等待 overlay 进程退出 (pid={getattr(overlay_process, 'pid', None)})")
            overlay_process.join(timeout=grace_period)
            if overlay_process.is_alive():
                if config.DEBUG:
                    print("[SHUTDOWN] overlay 进程未在超时内退出，尝试终止")
                try:
                    overlay_process.terminate()
                except Exception:
                    pass
                overlay_process.join(timeout=1.0)

        # 关闭虚拟摇杆
        try:
            if virtual_joystick is not None:
                if config.DEBUG:
                    print("[SHUTDOWN] 关闭虚拟摇杆")
                virtual_joystick.close()
        except Exception:
            pass

        # 停止监视器（如果存在）
        try:
            from joystick_monitor import stop_monitor
            stop_monitor()
        except Exception:
            pass

        if config.DEBUG:
            print("[SHUTDOWN] 清理完成")
    except Exception as e:
        print(f"[SHUTDOWN] 清理时发生错误: {e}")


def _signal_handler(sig, frame):
    # Called on SIGINT/SIGTERM
    try:
        print(f"[SIGNAL] 收到信号 {sig}, 触发退出")
        shutdown_server()
    finally:
        # 使用强制退出以确保没有残留线程阻塞
        try:
            time.sleep(0.1)
        except Exception:
            pass
        os._exit(0)

if __name__ == '__main__':
    # Initialize virtual joystick for driving mode
    init_virtual_joystick()
    
    # Start overlay
    start_overlay()
    print(
    "Server started. Access the web interface at http://<your-device-ip>:5000",
    "For Example: http://localhost:5000",
    )
    # Start server
    # host='0.0.0.0' so it is accessible from other devices
    # Register signal handlers so Ctrl+C triggers cleanup
    try:
        signal.signal(signal.SIGINT, _signal_handler)
    except Exception:
        pass
    try:
        signal.signal(signal.SIGTERM, _signal_handler)
    except Exception:
        pass

    try:
        socketio.run(app, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)
    except KeyboardInterrupt:
        # In some environments KeyboardInterrupt may be raised instead of signal handler
        print("[MAIN] KeyboardInterrupt caught, shutting down...")
        shutdown_server()
    finally:
        # Ensure cleanup on exit
        shutdown_server()
