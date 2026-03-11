#!/usr/bin/env python3
"""
RFID Handler for ZeroRange
Challenges RFID 125kHz avec Proxmark3
"""

import time
import logging
from typing import Tuple, Optional
from proxmark_handler import ProxmarkHandler

logger = logging.getLogger(__name__)


class RFIDHandler:
    """Handles RFID 125kHz challenges"""

    def __init__(self, lcd, proxmark: ProxmarkHandler):
        """
        Initialize RFID handler

        Args:
            lcd: Instance de LCDManager
            proxmark: Instance de ProxmarkHandler
        """
        self.lcd = lcd
        self.proxmark = proxmark
        logger.info("RFID handler initialized")

    def wait_for_rfid(self, timeout: int) -> Tuple[bool, Optional[dict], int]:
        """
        Wait for RFID tag detection with countdown

        Args:
            timeout: Maximum time to wait in seconds

        Returns:
            tuple: (success, tag_info, time_taken)
        """
        start_time = time.time()

        while True:
            elapsed = int(time.time() - start_time)
            remaining = timeout - elapsed

            # Update countdown on LCD line 1
            countdown_text = f"L/R:Skip [{remaining}s]"
            self.lcd.write_line(1, countdown_text)

            # Check for RFID tag
            tag_info = self.proxmark.rfid_scan()
            if tag_info:
                logger.info(f"RFID tag found: {tag_info} in {elapsed}s")
                return (True, tag_info, elapsed)

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

            time.sleep(0.5)

    def challenge_1_detect(self) -> int:
        """
        Challenge 1: Detect & Read
        Detect any RFID 125kHz tag with Proxmark

        Returns:
            int: Points earned (10 or 0)
        """
        logger.info("Starting RFID Challenge 1: Detect & Read")

        # Display challenge screen
        self.lcd.clear()
        self.lcd.write_line(0, "RFID Ch1:Detect")

        # Wait for RFID tag (60 second timeout)
        success, tag_info, time_taken = self.wait_for_rfid(60)

        if success:
            # Display tag info
            self.lcd.clear()
            tag_type = tag_info.get('type', 'Unknown')[:16]
            self.lcd.write_line(0, f"Type:{tag_type}")

            tag_id = tag_info.get('id', 'N/A')[:16]
            self.lcd.write_line(1, f"ID:{tag_id}")
            time.sleep(3)

            # Success screen
            self.lcd.clear()
            self.lcd.write_line(0, "SOLVED! +10pts")
            self.lcd.write_line(1, "L:Back")

            logger.info(f"RFID Challenge 1 completed in {time_taken}s")

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

            logger.info("RFID Challenge 1 failed")

            # Wait for button press
            while True:
                if self.lcd.button_pressed(1):
                    self.lcd.wait_button_release(1)
                    return self.challenge_1_detect()  # Retry
                elif self.lcd.button_pressed(5):
                    self.lcd.wait_button_release(5)
                    return 0  # Back to menu

                time.sleep(0.1)

    def challenge_2_clone(self) -> int:
        """
        Challenge 2: Clone Tag
        Read a RFID tag and clone it to T5577

        Returns:
            int: Points earned (10 or 0)
        """
        logger.info("Starting RFID Challenge 2: Clone Tag")

        # Step 1: Read the original tag
        self.lcd.clear()
        self.lcd.write_line(0, "RFID Ch2:Clone1")

        success, tag_info, time_taken = self.wait_for_rfid(45)

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

        # Save tag info
        target_id = tag_info.get('id', '')
        tag_type = tag_info.get('type', 'Unknown')

        # Display saved info
        self.lcd.clear()
        self.lcd.write_line(0, "ID saved!")
        self.lcd.write_line(1, target_id[:16])
        time.sleep(2)

        # Instruction to clone
        self.lcd.clear()
        self.lcd.write_line(0, "Place T5577...")
        self.lcd.write_line(1, "for cloning")
        time.sleep(3)

        # Attempt to clone to T5577
        self.lcd.clear()
        self.lcd.write_line(0, "Cloning...")
        self.lcd.write_line(1, "Please wait...")

        clone_success = self.proxmark.rfid_clone_to_t5577(target_id, tag_type)

        if clone_success:
            self.lcd.write_line(1, "Clone OK!")
            time.sleep(2)

            # Step 2: Verify the clone
            self.lcd.clear()
            self.lcd.write_line(0, "RFID Ch2:Clone2")
            self.lcd.write_line(1, "Read cloned tag")

            success2, tag_info2, time_taken2 = self.wait_for_rfid(45)

            if not success2:
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
            verify_id = tag_info2.get('id', '')

            if verify_id.upper() == target_id.upper():
                # Success!
                self.lcd.clear()
                self.lcd.write_line(0, "SOLVED! +10pts")
                self.lcd.write_line(1, "L:Back")

                logger.info(f"RFID Challenge 2 completed")

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

                logger.info(f"RFID Challenge 2 failed: Wrong ID")

                while True:
                    if self.lcd.button_pressed(1):
                        self.lcd.wait_button_release(1)
                        return self.challenge_2_clone()
                    elif self.lcd.button_pressed(5):
                        self.lcd.wait_button_release(5)
                        return 0

                    time.sleep(0.1)
        else:
            # Clone failed
            self.lcd.clear()
            self.lcd.write_line(0, "Clone failed")
            self.lcd.write_line(1, "1:Retry L:Back")

            while True:
                if self.lcd.button_pressed(1):
                    self.lcd.wait_button_release(1)
                    return self.challenge_2_clone()
                elif self.lcd.button_pressed(5):
                    self.lcd.wait_button_release(5)
                    return 0

                time.sleep(0.1)

    def challenge_3_simulate(self) -> int:
        """
        Challenge 3: Simulate Tag
        Use Proxmark to simulate an EM410x tag

        Returns:
            int: Points earned (10 or 0)
        """
        logger.info("Starting RFID Challenge 3: Simulate Tag")

        # Step 1: Read a tag to get its ID
        self.lcd.clear()
        self.lcd.write_line(0, "RFID Ch3:Sim 1")
        self.lcd.write_line(1, "Read tag...")

        success, tag_info, time_taken = self.wait_for_rfid(60)

        if not success:
            self.lcd.clear()
            self.lcd.write_line(0, "TIMEOUT")
            self.lcd.write_line(1, "1:Retry L:Back")

            while True:
                if self.lcd.button_pressed(1):
                    self.lcd.wait_button_release(1)
                    return self.challenge_3_simulate()
                elif self.lcd.button_pressed(5):
                    self.lcd.wait_button_release(5)
                    return 0

                time.sleep(0.1)

        target_id = tag_info.get('id', '')
        tag_type = tag_info.get('type', '')

        # Save ID
        self.lcd.clear()
        self.lcd.write_line(0, "ID saved!")
        self.lcd.write_line(1, target_id[:16])
        time.sleep(2)

        # Step 2: Start simulation
        self.lcd.clear()
        self.lcd.write_line(0, "Simulating...")
        self.lcd.write_line(1, "Remove tag now")

        # Only support EM410x simulation for now
        if tag_type.lower() != "em410x":
            self.lcd.clear()
            self.lcd.write_line(0, "Not EM410x!")
            self.lcd.write_line(1, "Need EM410x")
            time.sleep(3)
            return 0

        # Start simulation in background
        sim_success = self.proxmark.rfid_simulate_em410x(target_id)

        if sim_success:
            self.lcd.clear()
            self.lcd.write_line(0, "SOLVED! +10pts")
            self.lcd.write_line(1, "L:Back")

            logger.info(f"RFID Challenge 3 completed")

            # Wait for user to press Back button
            while True:
                if self.lcd.button_pressed(5):
                    self.lcd.wait_button_release(5)
                    return 10
                time.sleep(0.1)
        else:
            self.lcd.clear()
            self.lcd.write_line(0, "Sim failed")
            self.lcd.write_line(1, "1:Retry L:Back")

            logger.info("RFID Challenge 3 failed")

            while True:
                if self.lcd.button_pressed(1):
                    self.lcd.wait_button_release(1)
                    return self.challenge_3_simulate()
                elif self.lcd.button_pressed(5):
                    self.lcd.wait_button_release(5)
                    return 0

                time.sleep(0.1)


# Test code
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format='[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s'
    )

    print("Testing RFID handler...")
    print("Note: This requires LCD and Proxmark hardware")

    try:
        from lcd_manager import LCDManager

        lcd = LCDManager()
        pm = ProxmarkHandler()
        handler = RFIDHandler(lcd, pm)

        print("\nTesting RFID detection...")
        print("Place an RFID 125kHz tag near the Proxmark (10 second timeout)")

        success, tag_info, time_taken = handler.wait_for_rfid(10)

        if success:
            print(f"SUCCESS! Tag detected in {time_taken}s:")
            for key, value in tag_info.items():
                print(f"  {key}: {value}")
        else:
            print(f"TIMEOUT or SKIP after {time_taken}s")

        lcd.close()

    except Exception as e:
        print(f"Error: {e}")
        print("Make sure you're running on Raspberry Pi with hardware connected")
