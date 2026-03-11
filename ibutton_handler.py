"""
iButton Handler for ZeroRange
Manages iButton detection and challenge logic via USB reader
"""

import os
import time
import random
import logging
from typing import Tuple, Optional
from ibutton_usb_reader import IButtonUSBReader

logger = logging.getLogger(__name__)


class iButtonHandler:
    """Handles iButton detection and challenge logic"""

    def __init__(self, lcd, usb_device: str = "/dev/input/event1"):
        """
        Initialize iButton handler

        Args:
            lcd: Instance of LCDManager
            usb_device: Path to USB input device (default: /dev/input/event1)
        """
        self.lcd = lcd
        self.usb_device = usb_device
        self.reader: Optional[IButtonUSBReader] = None
        self.last_detected_id: Optional[str] = None

        try:
            self.reader = IButtonUSBReader(usb_device)
            # Start reader immediately and keep it running
            self.reader.start(callback=self._on_ibutton_detected)
            logger.info(f"iButton USB handler initialized on {usb_device}")
            logger.info("USB reader started in background")
        except Exception as e:
            logger.error(f"Failed to initialize USB reader: {e}")
            raise RuntimeError(f"USB iButton reader not available: {e}")

    def read_ibutton(self) -> Optional[str]:
        """
        Read iButton ID from USB reader (non-blocking check)

        Returns:
            str: iButton ID (format: 01-XXXXXXXXXXXX) or None if not found
        """
        return self.last_detected_id

    def _on_ibutton_detected(self, ibutton_id: str):
        """Callback when iButton is detected"""
        self.last_detected_id = ibutton_id
        logger.debug(f"Callback: iButton detected {ibutton_id}")

    def wait_for_ibutton(self, timeout: int) -> Tuple[bool, Optional[str], int]:
        """
        Wait for iButton detection with countdown

        Args:
            timeout: Maximum time to wait in seconds

        Returns:
            tuple: (success, ibutton_id, time_taken)
                success: True if iButton detected, False if timeout/skip
                ibutton_id: iButton ID string or None
                time_taken: Elapsed time in seconds
        """
        start_time = time.time()
        self.last_detected_id = None

        # Reader is already running in background, just wait for detection
        while True:
            elapsed = int(time.time() - start_time)
            remaining = timeout - elapsed

            # Update countdown on LCD line 1
            countdown_text = f"L/R:Skip [{remaining}s]"
            self.lcd.write_line(1, countdown_text)

            # Check if iButton was detected
            if self.last_detected_id:
                detected_id = self.last_detected_id
                self.last_detected_id = None  # Reset for next time
                logger.info(f"iButton found: {detected_id} in {elapsed}s")
                return (True, detected_id, elapsed)

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

            time.sleep(0.2)  # Poll every 200ms

    def wait_ibutton_removed(self, timeout: int = 10) -> bool:
        """
        Wait a moment (USB readers don't need removal detection)

        Args:
            timeout: Maximum time to wait in seconds

        Returns:
            bool: Always True (USB readers detect once)
        """
        # USB readers send ID once, no need to wait for removal
        time.sleep(0.5)
        self.last_detected_id = None
        logger.debug("Ready for next iButton")
        return True

    def close(self):
        """Clean up USB reader resources"""
        if self.reader:
            self.reader.close()
            logger.info("iButton handler closed")

    def generate_random_id(self) -> str:
        """
        Generate random iButton ID

        Returns:
            str: Random ID in format "01-XXXXXXXXXXXX"
        """
        # Generate 6 random bytes (12 hex chars)
        random_bytes = [random.randint(0, 255) for _ in range(6)]
        hex_string = ''.join(f'{b:02X}' for b in random_bytes)

        return f"01-{hex_string}"

    def challenge_1_touch(self) -> int:
        """
        Challenge 1: Touch & Read
        Detect any iButton at the probe

        Returns:
            int: Points earned (10 or 0)
        """
        logger.info("Starting Challenge 1: Touch & Read")

        # Display challenge screen
        self.lcd.clear()
        self.lcd.write_line(0, "Ch1:Touch iBtn")

        # Wait for iButton (60 second timeout)
        success, ibutton_id, time_taken = self.wait_for_ibutton(60)

        if success:
            # Success screen
            self.lcd.clear()
            self.lcd.write_line(0, "SOLVED! +10pts")
            self.lcd.write_line(1, "L:Back")

            logger.info(f"Challenge 1 completed in {time_taken}s")

            # Wait for user to press Back button
            while True:
                if self.lcd.button_pressed(5):
                    self.lcd.wait_button_release(5)
                    return 10
                time.sleep(0.1)
        else:
            # Fail screen
            self.lcd.clear()
            self.lcd.write_line(0, "TIMEOUT")
            self.lcd.write_line(1, "1:Retry L:Back")

            logger.info("Challenge 1 failed")

            # Wait for button press
            while True:
                if self.lcd.button_pressed(1):
                    self.lcd.wait_button_release(1)
                    return self.challenge_1_touch()  # Retry
                elif self.lcd.button_pressed(5):
                    self.lcd.wait_button_release(5)
                    return 0  # Back to menu

                time.sleep(0.1)

    def challenge_2_clone(self) -> int:
        """
        Challenge 2: Clone iButton
        Read a physical key then emulate it

        Returns:
            int: Points earned (15 or 0)
        """
        logger.info("Starting Challenge 2: Clone iButton")

        # Step 1: Read the original key
        self.lcd.clear()
        self.lcd.write_line(0, "Ch2:Clone Step1")

        success, target_id, time_taken = self.wait_for_ibutton(45)

        if not success:
            # Failed to read original
            self.lcd.clear()
            self.lcd.write_line(0, "FAILED")
            self.lcd.write_line(1, "1:Retry L:Back")

            while True:
                if self.lcd.button_pressed(1):
                    self.lcd.wait_button_release(1)
                    return self.challenge_2_clone()
                elif self.lcd.button_pressed(5):
                    self.lcd.wait_button_release(5)
                    return 0

                time.sleep(0.1)

        # Display saved ID briefly
        self.lcd.clear()
        self.lcd.write_line(0, "ID saved!")
        self.lcd.write_line(1, "Remove key...")
        time.sleep(2)

        # Wait for iButton to be removed
        if not self.wait_ibutton_removed(10):
            self.lcd.write_line(1, "Still detected!")
            time.sleep(2)

        # Step 2: Emulate the key
        self.lcd.clear()
        self.lcd.write_line(0, "Ch2:Clone Step2")

        success, emulated_id, time_taken_2 = self.wait_for_ibutton(45)

        total_time = time_taken + time_taken_2

        if not success:
            # Timeout on emulation
            self.lcd.clear()
            self.lcd.write_line(0, "TIMEOUT")
            self.lcd.write_line(1, "1:Retry L:Back")

            while True:
                if self.lcd.button_pressed(1):
                    self.lcd.wait_button_release(1)
                    return self.challenge_2_clone()
                elif self.lcd.button_pressed(5):
                    self.lcd.wait_button_release(5)
                    return 0

                time.sleep(0.1)

        # Validate IDs match
        if emulated_id.upper() == target_id.upper():
            # Success!
            self.lcd.clear()
            self.lcd.write_line(0, "SOLVED! +10pts")
            self.lcd.write_line(1, "L:Back")

            logger.info(f"Challenge 2 completed in {total_time}s")

            # Wait for user to press Back button
            while True:
                if self.lcd.button_pressed(5):
                    self.lcd.wait_button_release(5)
                    return 10
                time.sleep(0.1)
        else:
            # Wrong ID
            self.lcd.clear()
            self.lcd.write_line(0, "WRONG ID")
            self.lcd.write_line(1, "1:Retry L:Back")

            logger.info(f"Challenge 2 failed: Wrong ID (expected {target_id}, got {emulated_id})")

            while True:
                if self.lcd.button_pressed(1):
                    self.lcd.wait_button_release(1)
                    return self.challenge_2_clone()
                elif self.lcd.button_pressed(5):
                    self.lcd.wait_button_release(5)
                    return 0

                time.sleep(0.1)

    def challenge_3_emulate(self) -> int:
        """
        Challenge 3: Emulate Specific ID
        Emulate a specific predefined ID

        Returns:
            int: Points earned (10 or 0)
        """
        logger.info("Starting Challenge 3: Emulate Specific")

        # Fixed target ID for challenge 3
        # Note: USB reader reads bytes in reverse order (little-endian)
        # Physical iButton to program: 01 CA FE 11 11 11 11 D4
        # USB reader detects as: 01 11 11 11 11 FE CA D4
        target_id_usb = "01-11111111FECAD4"  # What USB reader sees
        target_id_display = "01CAFE11111111D4"  # What user should program (no dash for LCD)
        logger.info(f"Target ID (USB): {target_id_usb}")
        logger.info(f"Target ID (Display): {target_id_display}")

        # Display challenge with target ID (what user should program)
        self.lcd.clear()
        self.lcd.write_line(0, target_id_display)

        # Wait for emulated iButton (120 second timeout)
        start_time = time.time()
        timeout = 120
        self.last_detected_id = None

        # Reader is already running in background, just wait for detection
        while True:
            elapsed = int(time.time() - start_time)
            remaining = timeout - elapsed

            # Update countdown
            self.lcd.write_line(1, f"L/R:Skip [{remaining}s]")

            # Check for iButton
            detected_id = self.last_detected_id
            if detected_id:
                # Validate ID (case-insensitive) - compare with USB format
                if detected_id.upper() == target_id_usb.upper():
                    # Success!
                    self.lcd.clear()
                    self.lcd.write_line(0, "SOLVED! +10pts")
                    self.lcd.write_line(1, "L:Back")

                    logger.info(f"Challenge 3 completed in {elapsed}s")

                    # Wait for user to press Back button
                    while True:
                        if self.lcd.button_pressed(5):
                            self.lcd.wait_button_release(5)
                            return 10
                        time.sleep(0.1)
                else:
                    # Wrong ID, show and continue
                    self.lcd.write_line(1, "Wrong, retry...")
                    time.sleep(1)
                    logger.debug(f"Wrong ID detected: {detected_id}")

                    # Reset for next attempt
                    self.last_detected_id = None

            # Check for skip (BTN4 or BTN5)
            if self.lcd.button_pressed(4) or self.lcd.button_pressed(5):
                btn = 4 if self.lcd.button_pressed(4) else 5
                self.lcd.wait_button_release(btn)

                # Confirm skip
                self.lcd.clear()
                self.lcd.write_line(0, "SKIPPED")
                self.lcd.write_line(1, "1:Retry L:Back")

                logger.info("Challenge 3 skipped")

                while True:
                    if self.lcd.button_pressed(1):
                        self.lcd.wait_button_release(1)
                        return self.challenge_3_emulate()
                    elif self.lcd.button_pressed(5):
                        self.lcd.wait_button_release(5)
                        return 0

                    time.sleep(0.1)

            # Check timeout
            if elapsed >= timeout:
                self.lcd.clear()
                self.lcd.write_line(0, "TIMEOUT")
                self.lcd.write_line(1, "1:Retry L:Back")

                logger.info("Challenge 3 timeout")

                while True:
                    if self.lcd.button_pressed(1):
                        self.lcd.wait_button_release(1)
                        return self.challenge_3_emulate()
                    elif self.lcd.button_pressed(5):
                        self.lcd.wait_button_release(5)
                        return 0

                    time.sleep(0.1)

            time.sleep(0.2)


# Test code for standalone testing
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format='[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s'
    )

    print("Testing iButton handler...")
    print("Note: This requires LCD and 1-Wire hardware")

    try:
        from lcd_manager import LCDManager

        lcd = LCDManager()
        handler = iButtonHandler(lcd)

        print("\nTesting iButton detection...")
        print("Touch an iButton to the probe (10 second timeout)")

        success, ibutton_id, time_taken = handler.wait_for_ibutton(10)

        if success:
            print(f"SUCCESS! Detected: {ibutton_id} in {time_taken}s")
        else:
            print(f"TIMEOUT or SKIP after {time_taken}s")

        print("\nGenerating random ID:")
        print(handler.generate_random_id())

        lcd.close()

    except Exception as e:
        print(f"Error: {e}")
        print("Make sure you're running on Raspberry Pi with hardware connected")
