#!/usr/bin/env python3
"""
iButton USB Reader for ZeroRange
Reads iButton IDs from USB HID keyboard emulation device
"""

import time
import logging
import threading
from typing import Optional, Callable
from evdev import InputDevice, categorize, ecodes

logger = logging.getLogger(__name__)


class IButtonUSBReader:
    """Reads iButton IDs from USB HID device"""

    # HID scancode to character mapping (US keyboard layout)
    SCANCODE_MAP = {
        ecodes.KEY_0: '0', ecodes.KEY_1: '1', ecodes.KEY_2: '2', ecodes.KEY_3: '3',
        ecodes.KEY_4: '4', ecodes.KEY_5: '5', ecodes.KEY_6: '6', ecodes.KEY_7: '7',
        ecodes.KEY_8: '8', ecodes.KEY_9: '9',
        ecodes.KEY_A: 'A', ecodes.KEY_B: 'B', ecodes.KEY_C: 'C', ecodes.KEY_D: 'D',
        ecodes.KEY_E: 'E', ecodes.KEY_F: 'F',
    }

    def __init__(self, device_path: str = "/dev/input/event0"):
        """
        Initialize USB iButton reader

        Args:
            device_path: Path to input device (usually /dev/input/eventX)
        """
        self.device_path = device_path
        self.device: Optional[InputDevice] = None
        self.buffer = ""
        self.last_id: Optional[str] = None
        self.callback: Optional[Callable] = None
        self.running = False
        self.thread: Optional[threading.Thread] = None

        try:
            self.device = InputDevice(device_path)
            logger.info(f"iButton USB reader initialized on {device_path}")
            logger.info(f"Device: {self.device.name}")
        except Exception as e:
            logger.error(f"Failed to open device {device_path}: {e}")
            raise

    def _process_scancode(self, scancode: int) -> Optional[str]:
        """
        Convert scancode to character

        Args:
            scancode: Key scancode from input event

        Returns:
            str: Character or None
        """
        return self.SCANCODE_MAP.get(scancode)

    def _parse_ibutton_id(self, raw_data: str) -> Optional[str]:
        """
        Parse and validate iButton ID from raw data

        Args:
            raw_data: Raw string received from USB reader

        Returns:
            str: Formatted iButton ID (01-XXXXXXXXXXXX) or None if invalid
        """
        # Remove any whitespace
        cleaned = raw_data.strip().upper()

        # iButton IDs are typically 16 hex characters (8 bytes)
        # Format: Family Code (2 hex) + Serial Number (12 hex) + CRC (2 hex)
        if len(cleaned) == 16 and all(c in '0123456789ABCDEF' for c in cleaned):
            # Format as 01-XXXXXXXXXXXX (family-serial-crc)
            return f"{cleaned[:2]}-{cleaned[2:]}"
        elif len(cleaned) == 14 and all(c in '0123456789ABCDEF' for c in cleaned):
            # Some readers might not include family code
            return f"01-{cleaned}"
        else:
            logger.warning(f"Invalid iButton ID format: {cleaned}")
            return None

    def _read_loop(self):
        """Main reading loop (runs in background thread)"""
        logger.info("USB reader loop started")

        try:
            for event in self.device.read_loop():
                if not self.running:
                    break

                # Only process key press events
                if event.type == ecodes.EV_KEY:
                    key_event = categorize(event)

                    # Key press (not release)
                    if key_event.keystate == 1:
                        if event.code == ecodes.KEY_ENTER:
                            # Enter pressed - end of ID
                            if self.buffer:
                                ibutton_id = self._parse_ibutton_id(self.buffer)
                                if ibutton_id:
                                    logger.info(f"iButton detected: {ibutton_id}")
                                    self.last_id = ibutton_id

                                    # Call callback if registered
                                    if self.callback:
                                        self.callback(ibutton_id)

                                self.buffer = ""
                        else:
                            # Regular key - add to buffer
                            char = self._process_scancode(event.code)
                            if char:
                                self.buffer += char

        except Exception as e:
            if self.running:
                logger.error(f"Error in read loop: {e}")

        logger.info("USB reader loop stopped")

    def start(self, callback: Optional[Callable] = None):
        """
        Start reading iButton IDs in background

        Args:
            callback: Function to call when iButton is detected
        """
        if self.running:
            logger.warning("Reader already running")
            return

        self.callback = callback
        self.running = True
        self.thread = threading.Thread(target=self._read_loop, daemon=True)
        self.thread.start()
        logger.info("USB reader started")

    def stop(self):
        """Stop reading"""
        if not self.running:
            return

        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
        logger.info("USB reader stopped")

    def read_blocking(self, timeout: int = 30) -> Optional[str]:
        """
        Read one iButton ID (blocking)

        Args:
            timeout: Maximum time to wait in seconds

        Returns:
            str: iButton ID or None if timeout
        """
        self.last_id = None
        self.start()

        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.last_id:
                result = self.last_id
                self.stop()
                return result
            time.sleep(0.1)

        self.stop()
        return None

    def close(self):
        """Close the device"""
        self.stop()
        if self.device:
            self.device.close()
            logger.info("USB reader closed")


# Test code
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format='[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s'
    )

    print("=" * 60)
    print("iButton USB Reader Test")
    print("=" * 60)

    # Try to find the iButton reader device
    import glob
    devices = glob.glob('/dev/input/event*')

    print(f"\nAvailable input devices: {len(devices)}")
    for dev_path in devices:
        try:
            device = InputDevice(dev_path)
            print(f"  {dev_path}: {device.name}")
            device.close()
        except Exception as e:
            print(f"  {dev_path}: Error - {e}")

    # Test with event0 (adjust if needed)
    device_path = "/dev/input/event0"
    print(f"\nTesting with: {device_path}")
    print("Place an iButton on the reader (30 second timeout)...")

    try:
        reader = IButtonUSBReader(device_path)
        ibutton_id = reader.read_blocking(timeout=30)

        if ibutton_id:
            print(f"\n✓ SUCCESS! iButton detected: {ibutton_id}")
        else:
            print("\n✗ TIMEOUT - No iButton detected")

        reader.close()

    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        print("\nMake sure:")
        print("  1. USB iButton reader is connected")
        print("  2. You have permission to access /dev/input/event*")
        print("  3. Run as root or add user to 'input' group")
