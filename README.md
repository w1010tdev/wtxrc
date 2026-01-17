# Remote Game Control

A web-based remote control for your PC input, designed for tablets and phones.

## Features
- **Element Plus UI** - Modern, responsive interface using Element Plus components
- **Visual Layout Editor** - Drag and drop buttons, resize and configure them
- **Custom Key Combinations** - Support for modifier keys (Ctrl, Alt, Shift, etc.) and complex key combinations like Ctrl+Alt+Del
- **Floating Overlay** - PC overlay showing pressed buttons
- **Low Latency** - WebSocket communication for minimal delay
- **Driving Mode** - Use your device's gyroscope to simulate a steering wheel

## Installation

1. Install Python Dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. (Optional) For Driving Mode with virtual joystick:
   - **Windows**: Install ViGEmBus driver from https://github.com/ViGEm/ViGEmBus/releases, then `pip install vgamepad`
   - **Linux**: `pip install python-uinput` (may require sudo)

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

### Mode Selection
Edit `config/config.py` to switch between modes:
- `MODE = "custom_keys"` - Default button layout mode
- `MODE = "driving"` - Driving simulator mode with gyroscope support

### Button Configuration
- Default buttons are in `config/buttons.json`
- In the web interface:
  - Click **EDIT** to enable edit mode
  - **Drag** buttons to reposition them
  - **Double-click** a button to open the configuration dialog where you can:
    - Set the button label
    - Configure key combinations with modifier keys
    - Change the button color and size
  - Click **ADD** to create new buttons
  - Click **SAVE** to persist changes

### Modifier Keys
The following modifier keys are supported:
- `ctrl`, `ctrl_l`, `ctrl_r` - Control keys
- `shift`, `shift_l`, `shift_r` - Shift keys
- `alt`, `alt_l`, `alt_r`, `alt_gr` - Alt keys
- `cmd`, `cmd_l`, `cmd_r`, `win` - Command/Windows keys

### Driving Mode
When in driving mode:
1. Connect your device
2. You'll be asked if you want to set it as the main device
3. The main device's gyroscope will control steering
4. Tilt your device left/right to steer

## Technical Details

### Touch/Pointer Handling
The application uses Pointer Events API for unified touch and mouse handling, properly tracking which button is being pressed even when dragging across multiple buttons.

### Gyroscope API
Uses the DeviceOrientation API with proper permission handling for iOS 13+ devices.
