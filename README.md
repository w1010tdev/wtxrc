# Remote Game Control

A web-based remote control for your PC input, designed for tablets.

## Fetures
- Visual Layout Editor (Drag and drop buttons).
- Custom Key Combinations.
- Floating Overlay on PC showing pressed buttons.
- Low Latency WebSocket communication.

## Installation

1. Install Python Dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Run the server:
   ```bash
   python server/app.py
   ```
   *Note: You might need to run as Administrator for the key simulation to work in some full-screen games.*

2. Find your PC's IP address (e.g., `ipconfig` in terminal).
3. Open the browser on your tablet/phone and go to:
   `http://<YOUR_PC_IP>:5000`

## Configuration
- Default buttons are in `config/buttons.json`.
- You can move buttons in the web interface by clicking "Enable Edit Mode" and dragging them.
- Click "Save Layout" to persist changes.
