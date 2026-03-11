#!/usr/bin/env python3
"""
FLIRC USB IR Receiver Handler for ZeroRange
Low-level interface for FLIRC USB IR receiver via evdev/ir-keytable
"""

import subprocess
import time
import logging
import threading
from typing import Optional, Dict, Tuple, Callable

logger = logging.getLogger(__name__)


class FlircHandler:
    """Handles FLIRC USB IR receiver hardware interface"""

    def __init__(self, simulation_mode: bool = False):
        """
        Initialize FLIRC handler

        Args:
            simulation_mode: If True, simulate responses without hardware
        """
        self.simulation_mode = simulation_mode
        self.device_connected = False
        self.device_path: Optional[str] = None
        self.rc_device: Optional[str] = None

        # IR event tracking
        self.last_event: Optional[Dict] = None
        self.last_keycode: Optional[str] = None
        self.last_protocol: Optional[str] = None
        self.event_callback: Optional[Callable] = None
        self._listening = False
        self._listen_thread: Optional[threading.Thread] = None

        if not simulation_mode:
            self.device_connected = self._detect_device()
        else:
            logger.info("FLIRC running in simulation mode")
            self.device_connected = True

        if self.device_connected:
            logger.info("FLIRC handler initialized")
        else:
            logger.warning("FLIRC not detected")

    def _detect_device(self) -> bool:
        """
        Detect FLIRC USB device

        Returns:
            bool: True if FLIRC is found
        """
        # Method 1: Check via ir-keytable (v4l-utils)
        try:
            result = subprocess.run(
                ['ir-keytable'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0 and 'flirc' in result.stdout.lower():
                # Parse device info
                for line in result.stdout.split('\n'):
                    if '/dev/input/event' in line:
                        self.device_path = line.strip().split()[-1]
                    if 'Name' in line and 'flirc' in line.lower():
                        logger.info(f"FLIRC detected: {line.strip()}")

                # Find rc device
                for line in result.stdout.split('\n'):
                    if '/sys/class/rc/rc' in line:
                        self.rc_device = line.strip().split('/')[-1]

                return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        # Method 2: Check via flirc_util
        try:
            result = subprocess.run(
                ['flirc_util', 'version'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                logger.info(f"FLIRC util detected: {result.stdout.strip()}")
                # Find the input device via evdev
                self._find_evdev_device()
                return self.device_path is not None
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        # Method 3: Scan /dev/input for FLIRC
        try:
            from evdev import InputDevice, list_devices
            for dev_path in list_devices():
                try:
                    dev = InputDevice(dev_path)
                    if 'flirc' in dev.name.lower():
                        self.device_path = dev_path
                        logger.info(f"FLIRC found at {dev_path}: {dev.name}")
                        dev.close()
                        return True
                    dev.close()
                except Exception:
                    continue
        except ImportError:
            logger.warning("python-evdev not installed")

        logger.warning("FLIRC USB receiver not found")
        return False

    def _find_evdev_device(self):
        """Find the FLIRC evdev input device path"""
        try:
            from evdev import InputDevice, list_devices
            for dev_path in list_devices():
                try:
                    dev = InputDevice(dev_path)
                    if 'flirc' in dev.name.lower():
                        self.device_path = dev_path
                        dev.close()
                        return
                    dev.close()
                except Exception:
                    continue
        except ImportError:
            pass

    def is_connected(self) -> bool:
        """Check if FLIRC is connected"""
        if self.simulation_mode:
            return True
        return self._detect_device()

    def receive_ir(self, timeout: int = 30) -> Tuple[bool, Optional[Dict]]:
        """
        Wait for a single IR signal reception

        Args:
            timeout: Maximum time to wait in seconds

        Returns:
            tuple: (received, event_info)
        """
        if self.simulation_mode:
            logger.info(f"[SIM] Waiting for IR signal ({timeout}s timeout)")
            time.sleep(min(timeout, 3))
            event_info = {
                'keycode': 'KEY_POWER',
                'scancode': '0x1234',
                'protocol': 'NEC',
                'timestamp': time.time()
            }
            self.last_event = event_info
            self.last_keycode = event_info['keycode']
            self.last_protocol = event_info['protocol']
            return (True, event_info)

        # Try ir-keytable test mode first (most reliable with FLIRC)
        event_info = self._receive_via_irkeytable(timeout)
        if event_info:
            self.last_event = event_info
            self.last_keycode = event_info.get('keycode')
            self.last_protocol = event_info.get('protocol')
            return (True, event_info)

        # Fallback to evdev
        event_info = self._receive_via_evdev(timeout)
        if event_info:
            self.last_event = event_info
            self.last_keycode = event_info.get('keycode')
            self.last_protocol = event_info.get('protocol')
            return (True, event_info)

        return (False, None)

    def _receive_via_irkeytable(self, timeout: int) -> Optional[Dict]:
        """Receive IR signal via ir-keytable test mode"""
        if not self.rc_device:
            return None

        try:
            # ir-keytable -t -s rc0 -- test mode, shows raw scancodes
            result = subprocess.run(
                ['ir-keytable', '-t', '-s', self.rc_device],
                capture_output=True,
                text=True,
                timeout=timeout
            )

            if result.stdout:
                return self._parse_irkeytable_output(result.stdout)

        except subprocess.TimeoutExpired as e:
            # Check if we got partial output before timeout
            if e.stdout:
                output = e.stdout.decode() if isinstance(e.stdout, bytes) else e.stdout
                return self._parse_irkeytable_output(output)
        except Exception as e:
            logger.error(f"ir-keytable error: {e}")

        return None

    def _parse_irkeytable_output(self, output: str) -> Optional[Dict]:
        """Parse ir-keytable test output for IR events"""
        for line in output.strip().split('\n'):
            line = line.strip()
            if not line:
                continue

            event_info = {
                'raw_line': line,
                'timestamp': time.time()
            }

            # Parse protocol/scancode from ir-keytable output
            # Format: "1234.567890: lirc protocol(nec): scancode = 0x1234"
            if 'protocol' in line.lower():
                parts = line.split('protocol')
                if len(parts) > 1:
                    proto_part = parts[1].strip('():= ')
                    # Extract protocol name
                    proto = proto_part.split(')')[0].split(':')[0].strip('(')
                    event_info['protocol'] = proto.upper()

            if 'scancode' in line.lower():
                parts = line.lower().split('scancode')
                if len(parts) > 1:
                    scancode = parts[1].strip(' =:').split()[0]
                    event_info['scancode'] = scancode

            if 'key' in line.lower():
                parts = line.lower().split('key')
                if len(parts) > 1:
                    keycode = parts[1].strip(' =:').split()[0]
                    event_info['keycode'] = f"KEY_{keycode.upper()}"

            if event_info.get('scancode') or event_info.get('keycode'):
                return event_info

        return None

    def _receive_via_evdev(self, timeout: int) -> Optional[Dict]:
        """Receive IR signal via evdev input device"""
        if not self.device_path:
            return None

        try:
            from evdev import InputDevice, categorize, ecodes
            import select

            dev = InputDevice(self.device_path)
            start_time = time.time()

            while time.time() - start_time < timeout:
                r, _, _ = select.select([dev], [], [], 1.0)
                if r:
                    for event in dev.read():
                        if event.type == ecodes.EV_KEY:
                            key_event = categorize(event)
                            if key_event.keystate == 1:  # Key press
                                event_info = {
                                    'keycode': key_event.keycode if isinstance(key_event.keycode, str) else key_event.keycode[0],
                                    'scancode': hex(event.code),
                                    'protocol': 'Unknown',
                                    'timestamp': event.timestamp()
                                }
                                dev.close()
                                return event_info

            dev.close()
        except ImportError:
            logger.error("python-evdev not installed")
        except Exception as e:
            logger.error(f"evdev error: {e}")

        return None

    def start_listening(self, callback: Optional[Callable] = None):
        """
        Start listening for IR events in background

        Args:
            callback: Function called with event_info dict on each IR reception
        """
        if self._listening:
            logger.warning("Already listening")
            return

        self.event_callback = callback
        self._listening = True
        self._listen_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._listen_thread.start()
        logger.info("IR listener started")

    def _listen_loop(self):
        """Background listening loop"""
        while self._listening:
            received, event_info = self.receive_ir(timeout=2)
            if received and event_info:
                self.last_event = event_info
                self.last_keycode = event_info.get('keycode')
                self.last_protocol = event_info.get('protocol')

                if self.event_callback:
                    self.event_callback(event_info)

    def stop_listening(self):
        """Stop background listening"""
        self._listening = False
        if self._listen_thread:
            self._listen_thread.join(timeout=3)
        logger.info("IR listener stopped")

    def get_protocol_info(self) -> Optional[str]:
        """
        Get the IR protocol of the last received signal

        Returns:
            str: Protocol name (NEC, RC5, RC6, Sony, etc.) or None
        """
        if self.simulation_mode:
            return "NEC"

        if not self.rc_device:
            return self.last_protocol

        # Query ir-keytable for protocol info
        try:
            result = subprocess.run(
                ['ir-keytable', '-s', self.rc_device, '-p', 'all'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'protocol' in line.lower():
                        return line.strip()
        except Exception:
            pass

        return self.last_protocol

    def get_status(self) -> Dict:
        """Get current FLIRC handler status"""
        return {
            'connected': self.device_connected,
            'simulation_mode': self.simulation_mode,
            'device_path': self.device_path,
            'rc_device': self.rc_device,
            'listening': self._listening,
            'last_keycode': self.last_keycode,
            'last_protocol': self.last_protocol
        }

    def cleanup(self):
        """Clean up resources"""
        self.stop_listening()
        logger.info("FLIRC handler cleaned up")


# Test code
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format='[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s'
    )

    print("Testing FLIRC handler...")

    # Test in simulation mode first
    handler = FlircHandler(simulation_mode=True)

    print(f"\nStatus: {handler.get_status()}")

    print("\nTesting IR reception (simulated)...")
    received, info = handler.receive_ir(timeout=5)
    print(f"Received: {received}")
    print(f"Info: {info}")

    print(f"\nProtocol: {handler.get_protocol_info()}")

    handler.cleanup()
    print("\nFLIRC handler test complete!")
