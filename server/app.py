from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import json
import os
import multiprocessing
from overlay import run_overlay
import input_manager

app = Flask(__name__, template_folder="../templates", static_folder="../static")
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

# IPC Queue for Overlay
overlay_queue = multiprocessing.Queue()
overlay_process = None

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
    return jsonify(load_config())

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
    config = load_config()
    btn = next((b for b in config['buttons'] if b['id'] == btn_id), None)
    if btn:
        input_manager.execute_combination(btn.get('keys', []))

@socketio.on('save_layout')
def handle_save_layout(data):
    # Data should be the new list of buttons
    print("Saving Layout...")
    current_config = load_config()
    current_config['buttons'] = data
    save_config(current_config)
    emit('layout_saved', {'status': 'success'})

def start_overlay():
    global overlay_process
    overlay_process = multiprocessing.Process(target=run_overlay, args=(overlay_queue,))
    overlay_process.daemon = True
    overlay_process.start()

if __name__ == '__main__':
    # Start overlay
    start_overlay()
    print(
    "Server started. Access the web interface at http://<your-device-ip>:5000",
    "For Example: http://localhost:5000",
    )
    # Start server
    # host='0.0.0.0' so it is accessible from other devices
    socketio.run(app, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)
