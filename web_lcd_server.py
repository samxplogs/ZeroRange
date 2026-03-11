#!/usr/bin/env python3
"""
Web LCD Server - Synced with physical LCD via shared state files
Reads LCD state from run/lcd_state.json (written by lcd_manager.py)
Writes button presses to run/web_button.json (read by lcd_manager.py)
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import os

app = Flask(__name__)
CORS(app)

SHARED_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'run')
LCD_STATE_FILE = os.path.join(SHARED_DIR, 'lcd_state.json')
WEB_BUTTON_FILE = os.path.join(SHARED_DIR, 'web_button.json')

# Button name to number mapping (matches lcd_manager.py)
BUTTON_MAP = {
    'select': 1,
    'up': 2,
    'down': 3,
    'right': 4,
    'left': 5,
}

os.makedirs(SHARED_DIR, exist_ok=True)


def read_lcd_state():
    """Read current LCD state from shared file"""
    try:
        if os.path.exists(LCD_STATE_FILE):
            with open(LCD_STATE_FILE, 'r') as f:
                return json.load(f)
    except Exception:
        pass
    return {'line1': '', 'line2': ''}


def write_web_button(button_num):
    """Write a button press for zerorange.py to pick up"""
    try:
        tmp = WEB_BUTTON_FILE + '.tmp'
        with open(tmp, 'w') as f:
            json.dump({'button': button_num}, f)
        os.replace(tmp, WEB_BUTTON_FILE)
    except Exception as e:
        print(f"Error writing button: {e}")


@app.route('/api/lcd/state', methods=['GET'])
def get_state():
    """Return current LCD state from physical display"""
    return jsonify(read_lcd_state())


@app.route('/api/lcd/button', methods=['POST'])
def button_press():
    """Send a button press to the physical app via shared file"""
    data = request.get_json()
    button = data.get('button', '')

    button_num = BUTTON_MAP.get(button)
    if button_num:
        write_web_button(button_num)
        print(f"Web button: {button} -> btn {button_num}")

    # Small delay then return current state
    import time
    time.sleep(0.2)

    return jsonify({
        'success': True,
        'state': read_lcd_state()
    })


@app.route('/')
def index():
    """API info page"""
    return jsonify({
        'name': 'ZeroRange LCD API',
        'version': '2.0',
        'endpoints': {
            'GET /api/lcd/state': 'Get current LCD state (synced with physical display)',
            'POST /api/lcd/button': 'Send button press to physical app (body: {button: "up|down|left|right|select"})'
        }
    })


if __name__ == '__main__':
    print("=" * 60)
    print("ZeroRange Web LCD Server v2.0 (synced)")
    print("=" * 60)
    print(f"Shared state: {LCD_STATE_FILE}")
    print(f"Button file:  {WEB_BUTTON_FILE}")
    print("\nAPI server on http://0.0.0.0:5000")
    print("=" * 60)

    app.run(host='0.0.0.0', port=5000, debug=False)
