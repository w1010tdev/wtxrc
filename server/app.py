from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import json
import os
import sys
import multiprocessing
from overlay import run_overlay
import input_manager

# 将配置目录加入路径以便导入
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config import config

app = Flask(__name__, template_folder="../templates", static_folder="../static")
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

# IPC Queue for Overlay
overlay_queue = multiprocessing.Queue()
overlay_process = None

# Store connected devices and their roles
connected_devices = {}
main_device_sid = None

# Virtual joystick instance
virtual_joystick = None
slider_values = {}  # 存储拖动条当前值

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
    if config.MODE == 'driving':
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
    """更新驾驶模式配置（陀螺仪轴映射和拖动条）"""
    data = request.json
    # 保存到config.py中需要重启服务器
    # 这里我们保存到buttons.json中
    current_config = load_config()
    current_config['driving_config'] = data.get('driving_config', {})
    save_config(current_config)
    return jsonify({'status': 'success', 'message': '配置已保存，请重启服务器以应用更改'})

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
    
    # 发送到 overlay 进程用于显示（可选）
    overlay_queue.put({
        'cmd': 'GYRO',
        'alpha': alpha,
        'beta': beta,
        'gamma': gamma
    })
    
    # 应用陀螺仪数据到虚拟手柄（如果已初始化）
    if virtual_joystick and virtual_joystick.initialized:
        button_config = load_config()
        axis_config = button_config.get('driving_config', {}).get('axis_config', {})
        
        # 如果没有新的轴配置，回退到旧的 gyro_axis_mapping
        if not axis_config:
            gyro_mapping = button_config.get('driving_config', {}).get('gyro_axis_mapping', {})
            if not gyro_mapping:
                gyro_mapping = config.DRIVING_CONFIG.get('gyro_axis_mapping', {})
            
            # 使用旧的映射方式
            gyro_values = {'alpha': alpha, 'beta': beta, 'gamma': gamma}
            for gyro_axis, gamepad_axis in gyro_mapping.items():
                if gamepad_axis and gyro_axis in gyro_values:
                    value = normalize_gyro_value(gyro_values[gyro_axis], gyro_axis)
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
                        raw_value = normalize_gyro_value(gyro_values[gyro_axis], gyro_axis)
                        # 应用死区
                        value = apply_deadzone(raw_value, axis_cfg.get('deadzone', 0.05))
                        # 应用峰值限制
                        value = apply_peak_value(value, axis_cfg.get('peak_value', 1.0))
                        if config.DEBUG:
                            print(f"[GYRO] 映射 {gyro_axis}({gyro_values[gyro_axis]:.2f}) -> {gamepad_axis}({value:.2f}) [deadzone={axis_cfg.get('deadzone', 0.05)}, peak={axis_cfg.get('peak_value', 1.0)}]")
                        virtual_joystick.set_axis(gamepad_axis, value)
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
        button_config = load_config()
        axis_config = button_config.get('driving_config', {}).get('axis_config', {})
        
        # 如果没有新的轴配置，回退到旧方式
        if not axis_config:
            buttons = button_config.get('buttons', [])
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
            # 使用新的统一轴配置
            for gamepad_axis, axis_cfg in axis_config.items():
                if axis_cfg.get('source_type') == 'slider' and axis_cfg.get('source_id') == slider_id:
                    # 应用死区
                    processed_value = apply_deadzone(value, axis_cfg.get('deadzone', 0.05))
                    # 应用峰值限制
                    processed_value = apply_peak_value(processed_value, axis_cfg.get('peak_value', 1.0))
                    if config.DEBUG:
                        print(f"[SLIDER] 应用到轴: {gamepad_axis} = {processed_value:.3f} [原始={value:.3f}, deadzone={axis_cfg.get('deadzone', 0.05)}, peak={axis_cfg.get('peak_value', 1.0)}]")
                    virtual_joystick.set_axis(gamepad_axis, processed_value)
                    break
    else:
        if config.DEBUG:
            print("[SLIDER] 警告: 虚拟摇杆未初始化")

@socketio.on('save_layout')
def handle_save_layout(data):
    # Data should be the new list of buttons
    print("Saving Layout...")
    current_config = load_config()
    current_config['buttons'] = data
    save_config(current_config)
    emit('layout_saved', {'status': 'success'})

def normalize_gyro_value(gyro_value, gyro_axis):
    """将陀螺仪值归一化到 -1.0 到 1.0 范围"""
    # 这里可以根据实际情况调整归一化逻辑
    if gyro_axis == 'gamma':  # 左右倾斜，范围大约 -90 到 90
        return max(-1.0, min(1.0, gyro_value / 45.0))
    elif gyro_axis == 'beta':  # 前后倾斜，范围大约 -180 到 180
        return max(-1.0, min(1.0, gyro_value / 90.0))
    elif gyro_axis == 'alpha':  # Z轴旋转，范围 0 到 360
        # 转换为 -180 到 180
        normalized = gyro_value if gyro_value <= 180 else gyro_value - 360
        return max(-1.0, min(1.0, normalized / 180.0))
    return 0.0

def apply_deadzone(value, deadzone):
    """应用死区到输入值"""
    if abs(value) < deadzone:
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
            virtual_joystick = VirtualJoystick()
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
    socketio.run(app, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)
