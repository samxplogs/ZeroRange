#!/usr/bin/env python3
"""Debug script to capture raw events from iButton reader"""

import sys
from evdev import InputDevice, categorize, ecodes

device_path = "/dev/input/event1"

print(f"Opening device: {device_path}")
print("Place an iButton on the reader now...")
print("Press Ctrl+C to stop\n")

try:
    device = InputDevice(device_path)
    print(f"Device name: {device.name}")
    print(f"Device path: {device.path}")
    print(f"Device capabilities: {device.capabilities(verbose=True)}")
    print("\nListening for events...\n")

    buffer = ""

    for event in device.read_loop():
        if event.type == ecodes.EV_KEY:
            key_event = categorize(event)

            # Show all key events
            print(f"Event: type={event.type}, code={event.code}, value={event.value}, keycode={key_event.keycode}, keystate={key_event.keystate}")

            # Key press (not release)
            if key_event.keystate == 1:
                if event.code == ecodes.KEY_ENTER:
                    print(f"\n==> ENTER pressed! Buffer: '{buffer}'\n")
                    if buffer:
                        print(f"*** iButton ID captured: {buffer} ***\n")
                        buffer = ""
                else:
                    # Try to decode the key
                    try:
                        keycode_str = key_event.keycode
                        if isinstance(keycode_str, list):
                            keycode_str = keycode_str[0]

                        # Extract character from keycode
                        if keycode_str.startswith('KEY_'):
                            char = keycode_str[4:]  # Remove 'KEY_' prefix
                            if len(char) == 1:
                                buffer += char
                                print(f"  -> Added '{char}' to buffer: {buffer}")
                    except Exception as e:
                        print(f"  -> Could not decode: {e}")

except KeyboardInterrupt:
    print("\n\nStopped by user")
except PermissionError:
    print(f"\nERROR: Permission denied to access {device_path}")
    print("Try running with: sudo python3 debug_ibutton_events.py")
    sys.exit(1)
except FileNotFoundError:
    print(f"\nERROR: Device {device_path} not found")
    sys.exit(1)
except Exception as e:
    print(f"\nERROR: {e}")
    sys.exit(1)
