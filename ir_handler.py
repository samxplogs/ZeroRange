#!/usr/bin/env python3
"""
IR Handler for ZeroRange
Challenges IR avec récepteur FLIRC USB
"""

import time
import logging
from typing import Tuple, Optional, Dict
from flirc_handler import FlircHandler

logger = logging.getLogger(__name__)


class IRHandler:
    """Handles IR challenges using FLIRC USB receiver"""

    def __init__(self, lcd, flirc: Optional[FlircHandler] = None):
        """
        Initialize IR handler

        Args:
            lcd: Instance de LCDManager
            flirc: Instance de FlircHandler (created if None)
        """
        self.lcd = lcd
        self.flirc = flirc

        # Initialize FLIRC if not provided
        if self.flirc is None:
            try:
                self.flirc = FlircHandler()
            except Exception as e:
                logger.error(f"Failed to initialize FLIRC: {e}")
                raise

        # Store last received signals for challenges
        self.last_signal: Optional[Dict] = None
        self.signal_history = []

        logger.info("IR handler initialized")

    def wait_for_ir(self, timeout: int) -> Tuple[bool, Optional[Dict], int]:
        """
        Wait for IR signal detection with countdown

        Args:
            timeout: Maximum time to wait in seconds

        Returns:
            tuple: (success, event_info, time_taken)
        """
        start_time = time.time()

        while True:
            elapsed = int(time.time() - start_time)
            remaining = timeout - elapsed

            # Update countdown on LCD line 1
            self.lcd.write_line(1, f"L/R:Skip [{remaining}s]")

            # Try to receive IR signal (1 second window)
            received, event_info = self.flirc.receive_ir(timeout=1)

            if received and event_info:
                self.last_signal = event_info
                self.signal_history.append(event_info)
                logger.info(f"IR signal received in {elapsed}s: {event_info}")
                return (True, event_info, elapsed)

            # Check for skip button (BTN4 or BTN5)
            if self.lcd.button_pressed(4) or self.lcd.button_pressed(5):
                btn = 4 if self.lcd.button_pressed(4) else 5
                self.lcd.wait_button_release(btn)
                logger.info(f"Challenge skipped after {elapsed}s")
                return (False, None, elapsed)

            # Check timeout
            if elapsed >= timeout:
                logger.info(f"Timeout after {timeout}s")
                return (False, None, timeout)

    def challenge_1_detect(self) -> int:
        """
        Challenge 1: Detect IR Signal
        Receive any IR signal from a remote control

        Returns:
            int: Points earned (10 or 0)
        """
        logger.info("Starting IR Challenge 1: Detect IR Signal")

        # Display challenge screen
        self.lcd.clear()
        self.lcd.write_line(0, "IR Ch1:Detect")

        # Wait for IR signal (60 second timeout)
        success, event_info, time_taken = self.wait_for_ir(60)

        if success:
            # Display signal info briefly
            self.lcd.clear()
            keycode = event_info.get('keycode', 'Unknown')[:16]
            self.lcd.write_line(0, f"Key:{keycode}")

            protocol = event_info.get('protocol', '?')[:16]
            self.lcd.write_line(1, f"Proto:{protocol}")
            time.sleep(3)

            # Success screen
            self.lcd.clear()
            self.lcd.write_line(0, "SOLVED! +10pts")
            self.lcd.write_line(1, "L:Back")

            logger.info(f"IR Challenge 1 completed in {time_taken}s")

            # Wait for user to press Back button
            while True:
                if self.lcd.button_pressed(5):
                    self.lcd.wait_button_release(5)
                    return 10
                time.sleep(0.1)
        else:
            # Fail screen
            self.lcd.clear()
            self.lcd.write_line(0, "NO IR SIGNAL")
            self.lcd.write_line(1, "1:Retry L:Back")

            logger.info("IR Challenge 1 failed")

            # Wait for button press
            while True:
                if self.lcd.button_pressed(1):
                    self.lcd.wait_button_release(1)
                    return self.challenge_1_detect()  # Retry
                elif self.lcd.button_pressed(5):
                    self.lcd.wait_button_release(5)
                    return 0  # Back to menu

                time.sleep(0.1)

    def challenge_2_replay(self) -> int:
        """
        Challenge 2: Capture & Replay
        Record an IR signal, then verify the same signal is sent again
        (tests the Flipper Zero's IR emulation capabilities)

        Returns:
            int: Points earned (10 or 0)
        """
        logger.info("Starting IR Challenge 2: Capture & Replay")

        # Step 1: Capture original signal
        self.lcd.clear()
        self.lcd.write_line(0, "IR Ch2 [1/2]")
        self.lcd.write_line(1, "Press any IR btn")
        time.sleep(2)

        self.lcd.write_line(0, "Recording...")
        self.signal_history.clear()

        success, original_info, time_taken = self.wait_for_ir(45)

        if not success:
            # Failed to capture
            self.lcd.clear()
            self.lcd.write_line(0, "NO IR SIGNAL")
            self.lcd.write_line(1, "1:Retry L:Back")

            while True:
                if self.lcd.button_pressed(1):
                    self.lcd.wait_button_release(1)
                    return self.challenge_2_replay()
                elif self.lcd.button_pressed(5):
                    self.lcd.wait_button_release(5)
                    return 0

                time.sleep(0.1)

        # Signal captured - show what we got
        original_key = original_info.get('keycode', 'Unknown')
        self.lcd.clear()
        self.lcd.write_line(0, "Captured!")
        self.lcd.write_line(1, f"Key:{original_key[:12]}")
        time.sleep(2)

        # Step 2: Ask user to replay the same signal
        self.lcd.clear()
        self.lcd.write_line(0, "IR Ch2 [2/2]")
        self.lcd.write_line(1, "Send SAME signal")
        time.sleep(2)

        self.lcd.write_line(0, "Waiting replay..")

        success, replay_info, time_taken = self.wait_for_ir(45)

        if not success:
            self.lcd.clear()
            self.lcd.write_line(0, "NO SIGNAL")
            self.lcd.write_line(1, "1:Retry L:Back")

            while True:
                if self.lcd.button_pressed(1):
                    self.lcd.wait_button_release(1)
                    return self.challenge_2_replay()
                elif self.lcd.button_pressed(5):
                    self.lcd.wait_button_release(5)
                    return 0

                time.sleep(0.1)

        # Compare signals
        original_scancode = original_info.get('scancode', '')
        replay_scancode = replay_info.get('scancode', '')
        original_keycode = original_info.get('keycode', '')
        replay_keycode = replay_info.get('keycode', '')

        match = (original_scancode == replay_scancode) or (original_keycode == replay_keycode)

        if match:
            # Success!
            self.lcd.clear()
            self.lcd.write_line(0, "SOLVED! +10pts")
            self.lcd.write_line(1, "Signal matched!")

            time.sleep(2)
            self.lcd.write_line(1, "L:Back")

            logger.info("IR Challenge 2 completed - signals match")

            while True:
                if self.lcd.button_pressed(5):
                    self.lcd.wait_button_release(5)
                    return 10
                time.sleep(0.1)
        else:
            # Signals don't match
            self.lcd.clear()
            self.lcd.write_line(0, "MISMATCH!")
            self.lcd.write_line(1, "1:Retry L:Back")

            logger.info(f"IR Challenge 2 failed - mismatch: {original_keycode} vs {replay_keycode}")

            while True:
                if self.lcd.button_pressed(1):
                    self.lcd.wait_button_release(1)
                    return self.challenge_2_replay()
                elif self.lcd.button_pressed(5):
                    self.lcd.wait_button_release(5)
                    return 0

                time.sleep(0.1)

    def challenge_3_protocol(self) -> int:
        """
        Challenge 3: Protocol Identification
        Send IR signals using different protocols and have them identified

        Returns:
            int: Points earned (10 or 0)
        """
        logger.info("Starting IR Challenge 3: Protocol Identification")

        # Display challenge
        self.lcd.clear()
        self.lcd.write_line(0, "IR Ch3:Protocol")
        self.lcd.write_line(1, "Send 3 signals")
        time.sleep(2)

        protocols_detected = set()
        signals_needed = 3

        for i in range(signals_needed):
            self.lcd.clear()
            self.lcd.write_line(0, f"Signal {i+1}/{signals_needed}")

            success, event_info, time_taken = self.wait_for_ir(40)

            if not success:
                self.lcd.clear()
                self.lcd.write_line(0, "NO SIGNAL")
                self.lcd.write_line(1, "1:Retry L:Back")

                while True:
                    if self.lcd.button_pressed(1):
                        self.lcd.wait_button_release(1)
                        return self.challenge_3_protocol()
                    elif self.lcd.button_pressed(5):
                        self.lcd.wait_button_release(5)
                        return 0

                    time.sleep(0.1)

            # Show what we detected
            protocol = event_info.get('protocol', 'Unknown')
            protocols_detected.add(protocol)

            self.lcd.clear()
            self.lcd.write_line(0, f"Proto:{protocol[:10]}")
            self.lcd.write_line(1, f"Got {len(protocols_detected)} type(s)")
            time.sleep(2)

        # Display results
        self.lcd.clear()
        proto_list = ','.join(list(protocols_detected)[:3])
        self.lcd.write_line(0, f"Found:{proto_list[:16]}")

        # Success if we received all 3 signals (protocol detection is best-effort)
        self.lcd.clear()
        self.lcd.write_line(0, "SOLVED! +10pts")
        self.lcd.write_line(1, f"{len(protocols_detected)} protocol(s)")

        time.sleep(2)
        self.lcd.write_line(1, "L:Back")

        logger.info(f"IR Challenge 3 completed: {protocols_detected}")

        while True:
            if self.lcd.button_pressed(5):
                self.lcd.wait_button_release(5)
                return 10
            time.sleep(0.1)

    def get_status(self) -> Dict:
        """Get current IR handler status"""
        return {
            'flirc_status': self.flirc.get_status(),
            'signals_received': len(self.signal_history),
            'last_signal': self.last_signal
        }

    def close(self):
        """Clean up resources"""
        if self.flirc:
            self.flirc.cleanup()
        logger.info("IR handler closed")


# Test code
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format='[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s'
    )

    print("Testing IR handler...")
    print("Note: This requires LCD and FLIRC USB hardware")

    try:
        # Test with mock LCD
        class MockLCD:
            def clear(self):
                print("[LCD] Clear")

            def write_line(self, line, text):
                print(f"[LCD L{line}] {text}")

            def button_pressed(self, btn):
                return False

            def wait_button_release(self, btn):
                pass

        lcd = MockLCD()

        # Test with simulated FLIRC
        flirc = FlircHandler(simulation_mode=True)
        handler = IRHandler(lcd, flirc)

        print(f"\nStatus: {handler.get_status()}")

        print("\nTesting IR detection (simulated)...")
        # This would run the challenge in real scenario

        handler.close()
        print("\nIR handler test complete!")

    except Exception as e:
        print(f"Error: {e}")
        print("Make sure you're running on Raspberry Pi with FLIRC connected")
