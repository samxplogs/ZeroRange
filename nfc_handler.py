#!/usr/bin/env python3
"""
NFC Handler for ZeroRange
Challenges NFC avec Proxmark3
"""

import time
import logging
from typing import Tuple, Optional
from proxmark_handler import ProxmarkHandler

logger = logging.getLogger(__name__)


class NFCHandler:
    """Handles NFC challenges"""

    def __init__(self, lcd, proxmark: ProxmarkHandler):
        """
        Initialize NFC handler

        Args:
            lcd: Instance de LCDManager
            proxmark: Instance de ProxmarkHandler
        """
        self.lcd = lcd
        self.proxmark = proxmark
        logger.info("NFC handler initialized")

    def wait_for_nfc(self, timeout: int) -> Tuple[bool, Optional[dict], int]:
        """
        Wait for NFC card detection with countdown

        Args:
            timeout: Maximum time to wait in seconds

        Returns:
            tuple: (success, card_info, time_taken)
        """
        start_time = time.time()

        while True:
            elapsed = int(time.time() - start_time)
            remaining = timeout - elapsed

            # Update countdown on LCD line 1
            countdown_text = f"L/R:Skip [{remaining}s]"
            self.lcd.write_line(1, countdown_text)

            # Check for NFC card
            card_info = self.proxmark.nfc_scan()
            if card_info:
                logger.info(f"NFC card found: {card_info} in {elapsed}s")
                return (True, card_info, elapsed)

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
        Detect any NFC card with Proxmark

        Returns:
            int: Points earned (10 or 0)
        """
        logger.info("Starting NFC Challenge 1: Detect & Read")

        # Display challenge screen
        self.lcd.clear()
        self.lcd.write_line(0, "NFC Ch1:Detect")

        # Wait for NFC card (60 second timeout)
        success, card_info, time_taken = self.wait_for_nfc(60)

        if success:
            # Display card info briefly
            self.lcd.clear()
            card_type = card_info.get('type', 'Unknown')[:16]
            self.lcd.write_line(0, f"Type:{card_type}")

            uid = card_info.get('uid', 'N/A')[:16]
            self.lcd.write_line(1, f"UID:{uid}")
            time.sleep(3)

            # Success screen
            self.lcd.clear()
            self.lcd.write_line(0, "SOLVED! +10pts")
            self.lcd.write_line(1, "L:Back")

            logger.info(f"NFC Challenge 1 completed in {time_taken}s")

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

            logger.info("NFC Challenge 1 failed")

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
        Challenge 2: Clone Card
        Read a NFC card and dump its data

        Returns:
            int: Points earned (10 or 0)
        """
        logger.info("Starting NFC Challenge 2: Clone Card")

        # Step 1: Read the original card
        self.lcd.clear()
        self.lcd.write_line(0, "NFC Ch2:Clone 1")

        success, card_info, time_taken = self.wait_for_nfc(45)

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

        # Save UID
        target_uid = card_info.get('uid', '')
        card_type = card_info.get('type', 'Unknown')

        # Display saved info
        self.lcd.clear()
        self.lcd.write_line(0, "UID saved!")
        self.lcd.write_line(1, target_uid[:16])
        time.sleep(2)

        # Check if it's a MIFARE Classic for dump
        if "MIFARE Classic" in card_type:
            self.lcd.clear()
            self.lcd.write_line(0, "Dumping data...")
            self.lcd.write_line(1, "Please wait...")

            dump = self.proxmark.nfc_dump_mifare()

            if dump:
                self.lcd.write_line(1, f"{len(dump)} blocks OK")
                time.sleep(2)
            else:
                self.lcd.write_line(1, "Dump failed")
                time.sleep(2)

        # Step 2: Verify with another read
        self.lcd.clear()
        self.lcd.write_line(0, "NFC Ch2:Clone 2")
        self.lcd.write_line(1, "Read again...")

        success2, card_info2, time_taken2 = self.wait_for_nfc(45)

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

        # Validate UIDs match
        verify_uid = card_info2.get('uid', '')

        if verify_uid.upper() == target_uid.upper():
            # Success!
            self.lcd.clear()
            self.lcd.write_line(0, "SOLVED! +10pts")
            self.lcd.write_line(1, "L:Back")

            logger.info(f"NFC Challenge 2 completed")

            # Wait for user to press Back button
            while True:
                if self.lcd.button_pressed(5):
                    self.lcd.wait_button_release(5)
                    return 10
                time.sleep(0.1)
        else:
            # Wrong card
            self.lcd.clear()
            self.lcd.write_line(0, "WRONG CARD")
            self.lcd.write_line(1, "1:Retry L:Back")

            logger.info(f"NFC Challenge 2 failed: Wrong UID")

            while True:
                if self.lcd.button_pressed(1):
                    self.lcd.wait_button_release(1)
                    return self.challenge_2_clone()
                elif self.lcd.button_pressed(5):
                    self.lcd.wait_button_release(5)
                    return 0

                time.sleep(0.1)

    def challenge_3_mifare_attack(self) -> int:
        """
        Challenge 3: MIFARE Attack
        Use Proxmark to perform a MIFARE nested attack

        Returns:
            int: Points earned (10 or 0)
        """
        logger.info("Starting NFC Challenge 3: MIFARE Attack")

        # Display challenge
        self.lcd.clear()
        self.lcd.write_line(0, "NFC Ch3:Attack")
        self.lcd.write_line(1, "Place MIFARE...")

        # Wait for MIFARE Classic card
        success, card_info, time_taken = self.wait_for_nfc(60)

        if not success:
            self.lcd.clear()
            self.lcd.write_line(0, "TIMEOUT")
            self.lcd.write_line(1, "1:Retry L:Back")

            while True:
                if self.lcd.button_pressed(1):
                    self.lcd.wait_button_release(1)
                    return self.challenge_3_mifare_attack()
                elif self.lcd.button_pressed(5):
                    self.lcd.wait_button_release(5)
                    return 0

                time.sleep(0.1)

        card_type = card_info.get('type', '')

        if "MIFARE Classic" not in card_type:
            self.lcd.clear()
            self.lcd.write_line(0, "Not MIFARE!")
            self.lcd.write_line(1, "Need Classic")
            time.sleep(3)
            return 0

        # Perform nested attack
        self.lcd.clear()
        self.lcd.write_line(0, "Attacking...")
        self.lcd.write_line(1, "Please wait...")

        # Simulated attack (dans la réalité, utiliser hf mf nested)
        time.sleep(5)

        # Try to dump with found keys
        dump = self.proxmark.nfc_dump_mifare()

        if dump and len(dump) > 0:
            # Success!
            self.lcd.clear()
            self.lcd.write_line(0, "SOLVED! +10pts")
            self.lcd.write_line(1, "L:Back")

            logger.info(f"NFC Challenge 3 completed")

            # Wait for user to press Back button
            while True:
                if self.lcd.button_pressed(5):
                    self.lcd.wait_button_release(5)
                    return 10
                time.sleep(0.1)
        else:
            # Failed
            self.lcd.clear()
            self.lcd.write_line(0, "Attack failed")
            self.lcd.write_line(1, "1:Retry L:Back")

            logger.info("NFC Challenge 3 failed")

            while True:
                if self.lcd.button_pressed(1):
                    self.lcd.wait_button_release(1)
                    return self.challenge_3_mifare_attack()
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

    print("Testing NFC handler...")
    print("Note: This requires LCD and Proxmark hardware")

    try:
        from lcd_manager import LCDManager

        lcd = LCDManager()
        pm = ProxmarkHandler()
        handler = NFCHandler(lcd, pm)

        print("\nTesting NFC detection...")
        print("Place an NFC card near the Proxmark (10 second timeout)")

        success, card_info, time_taken = handler.wait_for_nfc(10)

        if success:
            print(f"SUCCESS! Card detected in {time_taken}s:")
            for key, value in card_info.items():
                print(f"  {key}: {value}")
        else:
            print(f"TIMEOUT or SKIP after {time_taken}s")

        lcd.close()

    except Exception as e:
        print(f"Error: {e}")
        print("Make sure you're running on Raspberry Pi with hardware connected")
