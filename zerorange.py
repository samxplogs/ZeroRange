#!/usr/bin/env python3
"""
ZeroRange - Flipper Zero Training System
Main application with state machine and menu navigation

Phase 1: iButton challenges only
"""

import time
import logging
import sys
import signal
import socket
from typing import Optional


def get_ip_address():
    """Get the current IP address of the device"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "No IP"

from lcd_manager import LCDManager
from ibutton_handler import iButtonHandler
from proxmark_handler import ProxmarkHandler
from nfc_handler import NFCHandler
from rfid_handler import RFIDHandler
from hackrf_handler import HackRFHandler
from subghz_handler import SubGHZHandler
from flirc_handler import FlircHandler
from ir_handler import IRHandler
from database import Database

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
    handlers=[
        logging.FileHandler('logs/zerorange.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


# State definitions
class State:
    HOME_SCREEN = "HOME_SCREEN"
    MAIN_MENU = "MAIN_MENU"
    IBUTTON_MENU = "IBUTTON_MENU"
    NFC_MENU = "NFC_MENU"
    RFID_MENU = "RFID_MENU"
    SUBGHZ_MENU = "SUBGHZ_MENU"
    IR_MENU = "IR_MENU"
    CHALLENGE_ACTIVE = "CHALLENGE_ACTIVE"
    SUCCESS_SCREEN = "SUCCESS_SCREEN"
    FAIL_SCREEN = "FAIL_SCREEN"
    SETTINGS = "SETTINGS"
    STATS_SCREEN = "STATS_SCREEN"
    RESET_CONFIRM = "RESET_CONFIRM"
    ABOUT_SCREEN = "ABOUT_SCREEN"


class ZeroRange:
    """Main application class"""

    def __init__(self):
        """Initialize ZeroRange application"""
        self.lcd: Optional[LCDManager] = None
        self.ibutton: Optional[iButtonHandler] = None
        self.proxmark: Optional[ProxmarkHandler] = None
        self.nfc: Optional[NFCHandler] = None
        self.rfid: Optional[RFIDHandler] = None
        self.hackrf: Optional[HackRFHandler] = None
        self.subghz: Optional[SubGHZHandler] = None
        self.flirc: Optional[FlircHandler] = None
        self.ir: Optional[IRHandler] = None
        self.db: Optional[Database] = None

        self.current_state = State.HOME_SCREEN
        self.current_score = 0

        # Menu navigation
        self.selected_menu_item = 0  # 0=iButton, 1=NFC, 2=RFID, 3=SubGHZ, 4=IR, 5=Settings
        self.menu_items = ["iButton", "NFC", "RFID", "SubGHZ", "IR", "Settings"]

        # Sub-menu navigation (challenges 0-2)
        self.selected_ibutton_challenge = 0
        self.selected_nfc_challenge = 0
        self.selected_rfid_challenge = 0
        self.selected_subghz_challenge = 0
        self.selected_ir_challenge = 0

        # Register signal handlers for clean shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.cleanup()
        sys.exit(0)

    def init_system(self):
        """Initialize all system components"""
        try:
            logger.info("Initializing ZeroRange...")

            # Initialize LCD
            logger.info("Initializing LCD...")
            self.lcd = LCDManager()

            # Show startup screen
            self.lcd.clear()
            self.lcd.write_line(0, "ZeroRange v1.0")
            self.lcd.write_line(1, "Initializing...")
            time.sleep(1)

            # Initialize database
            logger.info("Initializing database...")
            self.db = Database("scores.db")
            self.current_score = self.db.get_total_score()

            # Initialize iButton handler
            logger.info("Initializing iButton handler...")
            try:
                self.ibutton = iButtonHandler(self.lcd)
            except Exception as e:
                logger.warning(f"iButton handler initialization failed: {e}")
                logger.warning("iButton challenges will be unavailable")
                self.ibutton = None

            # Initialize Proxmark handler
            logger.info("Initializing Proxmark...")
            try:
                self.proxmark = ProxmarkHandler()

                # Initialize NFC handler
                self.nfc = NFCHandler(self.lcd, self.proxmark)

                # Initialize RFID handler
                self.rfid = RFIDHandler(self.lcd, self.proxmark)

                logger.info("Proxmark, NFC, and RFID handlers initialized")
            except Exception as e:
                logger.warning(f"Proxmark initialization failed: {e}")
                logger.warning("NFC and RFID challenges will not be available")
                self.proxmark = None
                self.nfc = None
                self.rfid = None

            # Initialize HackRF/SubGHZ handler
            logger.info("Initializing HackRF/SubGHZ...")
            try:
                self.hackrf = HackRFHandler()
                self.subghz = SubGHZHandler(self.lcd, self.hackrf)
                logger.info("HackRF and SubGHZ handlers initialized")
            except Exception as e:
                logger.warning(f"HackRF initialization failed: {e}")
                logger.warning("SubGHZ challenges will not be available")
                self.hackrf = None
                self.subghz = None

            # Initialize FLIRC/IR handler
            logger.info("Initializing FLIRC/IR...")
            try:
                self.flirc = FlircHandler()
                self.ir = IRHandler(self.lcd, self.flirc)
                logger.info("FLIRC and IR handlers initialized")
            except Exception as e:
                logger.warning(f"FLIRC initialization failed: {e}")
                logger.warning("IR challenges will not be available")
                self.flirc = None
                self.ir = None

            self.lcd.clear()
            self.lcd.write_line(0, "ZeroRange v1.0")
            self.lcd.write_line(1, "Ready!          ")  # Pad with spaces to clear
            time.sleep(1)

            logger.info(f"Initialization complete. Current score: {self.current_score}/150")

        except Exception as e:
            logger.error(f"Failed to initialize system: {e}")
            if self.lcd:
                self.lcd.clear()
                self.lcd.write_line(0, "INIT FAILED!")
                self.lcd.write_line(1, "Check logs")
                time.sleep(5)
            raise

    def display_home_screen(self):
        """Display home screen with name and IP address"""
        self.lcd.clear()
        ip_addr = get_ip_address()
        self.lcd.write_line(0, "ZeroRange V1")
        self.lcd.write_line(1, ip_addr)

    def handle_home_screen(self):
        """Handle home screen - any button press goes to main menu"""
        # Any button press goes to main menu
        for btn in [1, 2, 3, 4, 5]:
            if self.lcd.button_pressed(btn):
                self.lcd.wait_button_release(btn)
                logger.info("Entering main menu from home screen")
                self.current_state = State.MAIN_MENU
                return

    def display_main_menu(self):
        """Display main menu screen with navigation"""
        self.lcd.clear()

        # Show current selection with arrow
        menu_text = self.menu_items[self.selected_menu_item]
        score_text = f"{self.current_score}/150"
        self.lcd.write_line(0, f">{menu_text:<9}{score_text:>6}")
        self.lcd.write_line(1, "U/D SEL=Go L=Bk")

    def handle_main_menu(self):
        """Handle main menu button input with UP/DOWN navigation"""
        # UP button - navigate up
        if self.lcd.button_pressed(2):
            self.lcd.wait_button_release(2)
            self.selected_menu_item = (self.selected_menu_item - 1) % len(self.menu_items)
            self.display_main_menu()

        # DOWN button - navigate down
        elif self.lcd.button_pressed(3):
            self.lcd.wait_button_release(3)
            self.selected_menu_item = (self.selected_menu_item + 1) % len(self.menu_items)
            self.display_main_menu()

        # SELECT button - choose option
        elif self.lcd.button_pressed(1):
            self.lcd.wait_button_release(1)

            if self.selected_menu_item == 0:  # iButton
                logger.info("Entering iButton menu")
                self.current_state = State.IBUTTON_MENU
            elif self.selected_menu_item == 1:  # NFC
                logger.info("Entering NFC menu")
                self.current_state = State.NFC_MENU
            elif self.selected_menu_item == 2:  # RFID
                logger.info("Entering RFID menu")
                self.current_state = State.RFID_MENU
            elif self.selected_menu_item == 3:  # SubGHZ
                logger.info("Entering SubGHZ menu")
                self.current_state = State.SUBGHZ_MENU
            elif self.selected_menu_item == 4:  # IR
                logger.info("Entering IR menu")
                self.current_state = State.IR_MENU
            elif self.selected_menu_item == 5:  # Settings
                logger.info("Entering settings")
                self.current_state = State.SETTINGS

        # BTN5: BACK - return to home screen
        elif self.lcd.button_pressed(5):
            self.lcd.wait_button_release(5)
            logger.info("Returning to home screen")
            self.current_state = State.HOME_SCREEN

    def display_ibutton_menu(self):
        """Display iButton challenges menu"""
        self.lcd.clear()

        if self.ibutton is None:
            # iButton not available
            self.lcd.write_line(0, "iBtn Not Ready")
            self.lcd.write_line(1, "Connect USB L=Bk")
            return

        # Get challenge statuses
        challenges = self.db.get_all_challenges()

        # Show selected challenge with arrow
        challenge_names = ["Ch1:Touch", "Ch2:Clone", "Ch3:Emulate"]
        selected = challenge_names[self.selected_ibutton_challenge]

        # Add checkmark if completed
        if challenges[self.selected_ibutton_challenge]['completed']:
            selected = selected + " \u2713"  # ✓

        self.lcd.write_line(0, f">{selected}")
        self.lcd.write_line(1, "U/D SEL=Go L=Bk")

    def handle_ibutton_menu(self):
        """Handle iButton menu button input"""
        # BTN2: UP - navigate up
        if self.lcd.button_pressed(2):
            self.lcd.wait_button_release(2)
            self.selected_ibutton_challenge = (self.selected_ibutton_challenge - 1) % 3
            self.display_ibutton_menu()

        # BTN3: DOWN - navigate down
        elif self.lcd.button_pressed(3):
            self.lcd.wait_button_release(3)
            self.selected_ibutton_challenge = (self.selected_ibutton_challenge + 1) % 3
            self.display_ibutton_menu()

        # BTN1: SELECT - launch selected challenge (only if iButton available)
        elif self.lcd.button_pressed(1) and self.ibutton is not None:
            self.lcd.wait_button_release(1)
            challenge_num = self.selected_ibutton_challenge + 1  # Convert 0-2 to 1-3
            logger.info(f"Starting iButton challenge {challenge_num}")
            self.run_challenge(challenge_num)

        # BTN5: BACK - return to main menu
        elif self.lcd.button_pressed(5):
            self.lcd.wait_button_release(5)
            logger.info("Returning to main menu")
            self.current_state = State.MAIN_MENU

    def run_challenge(self, challenge_num: int):
        """
        Execute a challenge

        Args:
            challenge_num: Challenge number (1-3)
        """
        start_time = time.time()
        points_earned = 0

        try:
            # Run the appropriate challenge
            if challenge_num == 1:
                points_earned = self.ibutton.challenge_1_touch()
            elif challenge_num == 2:
                points_earned = self.ibutton.challenge_2_clone()
            elif challenge_num == 3:
                points_earned = self.ibutton.challenge_3_emulate()
            else:
                logger.error(f"Invalid challenge number: {challenge_num}")
                return

            time_taken = int(time.time() - start_time)

            # Record attempt in history
            success = points_earned > 0
            self.db.add_history(challenge_num, success, time_taken)

            # If successful, mark as completed and update score
            if success:
                self.db.mark_completed(challenge_num, time_taken)
                self.current_score = self.db.get_total_score()
                logger.info(f"Challenge {challenge_num} completed! Score: {self.current_score}/40")

        except Exception as e:
            logger.error(f"Error running challenge {challenge_num}: {e}")

        # Return to iButton menu
        self.current_state = State.IBUTTON_MENU

    def run_nfc_challenge(self, challenge_num: int):
        """
        Execute an NFC challenge

        Args:
            challenge_num: Challenge number (1-3)
        """
        start_time = time.time()
        points_earned = 0

        try:
            # Run the appropriate NFC challenge
            if challenge_num == 1:
                points_earned = self.nfc.challenge_1_detect()
            elif challenge_num == 2:
                points_earned = self.nfc.challenge_2_clone()
            elif challenge_num == 3:
                points_earned = self.nfc.challenge_3_mifare_attack()
            else:
                logger.error(f"Invalid NFC challenge number: {challenge_num}")
                return

            time_taken = int(time.time() - start_time)

            # Record attempt in history (challenges 4-6 are NFC)
            challenge_id = challenge_num + 3
            success = points_earned > 0
            self.db.add_history(challenge_id, success, time_taken)

            # If successful, mark as completed and update score
            if success:
                self.db.mark_completed(challenge_id, time_taken)
                self.current_score = self.db.get_total_score()
                logger.info(f"NFC Challenge {challenge_num} completed! Score: {self.current_score}/90")

        except Exception as e:
            logger.error(f"Error running NFC challenge {challenge_num}: {e}")

        # Return to NFC menu
        self.current_state = State.NFC_MENU

    def run_rfid_challenge(self, challenge_num: int):
        """
        Execute an RFID challenge

        Args:
            challenge_num: Challenge number (1-3)
        """
        start_time = time.time()
        points_earned = 0

        try:
            # Run the appropriate RFID challenge
            if challenge_num == 1:
                points_earned = self.rfid.challenge_1_detect()
            elif challenge_num == 2:
                points_earned = self.rfid.challenge_2_clone()
            elif challenge_num == 3:
                points_earned = self.rfid.challenge_3_simulate()
            else:
                logger.error(f"Invalid RFID challenge number: {challenge_num}")
                return

            time_taken = int(time.time() - start_time)

            # Record attempt in history (challenges 7-9 are RFID)
            challenge_id = challenge_num + 6
            success = points_earned > 0
            self.db.add_history(challenge_id, success, time_taken)

            # If successful, mark as completed and update score
            if success:
                self.db.mark_completed(challenge_id, time_taken)
                self.current_score = self.db.get_total_score()
                logger.info(f"RFID Challenge {challenge_num} completed! Score: {self.current_score}/90")

        except Exception as e:
            logger.error(f"Error running RFID challenge {challenge_num}: {e}")

        # Return to RFID menu
        self.current_state = State.RFID_MENU

    def display_settings(self):
        """Display settings menu"""
        self.lcd.clear()
        self.lcd.write_line(0, "Settings")
        self.lcd.write_line(1, "1:Stat 2:Reset")

    def handle_settings(self):
        """Handle settings menu input"""
        if self.lcd.button_pressed(1):
            self.lcd.wait_button_release(1)
            logger.info("Showing statistics")
            self.display_stats()
            return

        elif self.lcd.button_pressed(2):
            self.lcd.wait_button_release(2)
            logger.info("Reset score requested")
            self.current_state = State.RESET_CONFIRM
            return

        elif self.lcd.button_pressed(5):
            self.lcd.wait_button_release(5)
            logger.info("Returning to main menu")
            self.current_state = State.MAIN_MENU

    def display_stats(self):
        """Display statistics screen"""
        stats = self.db.get_stats()

        self.lcd.clear()
        self.lcd.write_line(0, f"Score: {stats['total_score']}/40")
        self.lcd.write_line(1, f"{stats['completed_count']}/3 Tries:{stats['total_attempts']}")

        # Auto-return after 5 seconds or BTN5
        start_time = time.time()
        while time.time() - start_time < 5:
            if self.lcd.button_pressed(5):
                self.lcd.wait_button_release(5)
                break
            time.sleep(0.1)

        self.current_state = State.SETTINGS

    def display_about(self):
        """Display about screen"""
        self.lcd.clear()
        self.lcd.write_line(0, "ZeroRange v1.0")
        self.lcd.write_line(1, "Flipper Train")

        # Wait for BTN5 to return
        while True:
            if self.lcd.button_pressed(5):
                self.lcd.wait_button_release(5)
                break
            time.sleep(0.1)

        self.current_state = State.SETTINGS

    def reset_scores_confirm(self):
        """Display reset confirmation and handle input"""
        self.lcd.clear()
        self.lcd.write_line(0, "Reset scores?")
        self.lcd.write_line(1, "1:Yes 5:No")

        while True:
            if self.lcd.button_pressed(1):
                self.lcd.wait_button_release(1)

                # Perform reset
                logger.info("Resetting all scores...")
                self.db.reset_scores()
                self.current_score = 0

                # Show confirmation
                self.lcd.clear()
                self.lcd.write_line(0, "Scores Reset!")
                self.lcd.write_line(1, "Progress cleared")
                time.sleep(2)

                self.current_state = State.MAIN_MENU
                return

            elif self.lcd.button_pressed(5):
                self.lcd.wait_button_release(5)
                logger.info("Reset cancelled")
                self.current_state = State.SETTINGS
                return

            time.sleep(0.1)

    def display_nfc_menu(self):
        """Display NFC challenges menu"""
        if self.nfc is None:
            self.lcd.clear()
            self.lcd.write_line(0, "NFC - No PM3!")
            self.lcd.write_line(1, "L=Back")
            return

        # Get challenge statuses
        challenges = self.db.get_all_challenges()

        self.lcd.clear()

        # Show selected challenge with arrow
        challenge_names = ["Ch4:Detect", "Ch5:Clone", "Ch6:MIFARE"]
        selected = challenge_names[self.selected_nfc_challenge]

        # Add checkmark if completed
        if challenges[3 + self.selected_nfc_challenge]['completed']:
            selected = selected + " \u2713"  # ✓

        self.lcd.write_line(0, f">{selected}")
        self.lcd.write_line(1, "U/D SEL=Go L=Bk")

    def handle_nfc_menu(self):
        """Handle NFC menu button input"""
        if self.nfc is None:
            # No Proxmark available
            if self.lcd.button_pressed(5):
                self.lcd.wait_button_release(5)
                self.current_state = State.MAIN_MENU
            return

        # BTN2: UP - navigate up
        if self.lcd.button_pressed(2):
            self.lcd.wait_button_release(2)
            self.selected_nfc_challenge = (self.selected_nfc_challenge - 1) % 3
            self.display_nfc_menu()

        # BTN3: DOWN - navigate down
        elif self.lcd.button_pressed(3):
            self.lcd.wait_button_release(3)
            self.selected_nfc_challenge = (self.selected_nfc_challenge + 1) % 3
            self.display_nfc_menu()

        # BTN1: SELECT - launch selected challenge
        elif self.lcd.button_pressed(1):
            self.lcd.wait_button_release(1)
            challenge_num = self.selected_nfc_challenge + 1  # Convert 0-2 to 1-3
            logger.info(f"Starting NFC challenge {challenge_num}")
            self.run_nfc_challenge(challenge_num)

        # BTN5: BACK - return to main menu
        elif self.lcd.button_pressed(5):
            self.lcd.wait_button_release(5)
            logger.info("Returning to main menu")
            self.current_state = State.MAIN_MENU

    def display_rfid_menu(self):
        """Display RFID challenges menu"""
        if self.rfid is None:
            self.lcd.clear()
            self.lcd.write_line(0, "RFID - No PM3!")
            self.lcd.write_line(1, "L=Back")
            return

        # Get challenge statuses
        challenges = self.db.get_all_challenges()

        self.lcd.clear()

        # Show selected challenge with arrow
        challenge_names = ["Ch7:Detect", "Ch8:Clone", "Ch9:Simulate"]
        selected = challenge_names[self.selected_rfid_challenge]

        # Add checkmark if completed
        if challenges[6 + self.selected_rfid_challenge]['completed']:
            selected = selected + " \u2713"  # ✓

        self.lcd.write_line(0, f">{selected}")
        self.lcd.write_line(1, "U/D SEL=Go L=Bk")

    def handle_rfid_menu(self):
        """Handle RFID menu input"""
        if self.rfid is None:
            # No Proxmark available
            if self.lcd.button_pressed(5):
                self.lcd.wait_button_release(5)
                self.current_state = State.MAIN_MENU
            return

        # BTN2: UP - navigate up
        if self.lcd.button_pressed(2):
            self.lcd.wait_button_release(2)
            self.selected_rfid_challenge = (self.selected_rfid_challenge - 1) % 3
            self.display_rfid_menu()

        # BTN3: DOWN - navigate down
        elif self.lcd.button_pressed(3):
            self.lcd.wait_button_release(3)
            self.selected_rfid_challenge = (self.selected_rfid_challenge + 1) % 3
            self.display_rfid_menu()

        # BTN1: SELECT - launch selected challenge
        elif self.lcd.button_pressed(1):
            self.lcd.wait_button_release(1)
            challenge_num = self.selected_rfid_challenge + 1  # Convert 0-2 to 1-3
            logger.info(f"Starting RFID challenge {challenge_num}")
            self.run_rfid_challenge(challenge_num)

        # BTN5: BACK - return to main menu
        elif self.lcd.button_pressed(5):
            self.lcd.wait_button_release(5)
            logger.info("Returning to main menu")
            self.current_state = State.MAIN_MENU

    def display_subghz_menu(self):
        """Display SubGHZ challenges menu"""
        if self.subghz is None:
            self.lcd.clear()
            self.lcd.write_line(0, "SubGHz-No HackRF")
            self.lcd.write_line(1, "L=Back")
            return

        # Get challenge statuses
        challenges = self.db.get_all_challenges()

        self.lcd.clear()

        # Show selected challenge with arrow
        challenge_names = ["Ch10:Detect", "Ch11:Replay", "Ch12:Analyze"]
        selected = challenge_names[self.selected_subghz_challenge]

        # Add checkmark if completed (challenges 10-12 are at index 9-11)
        if len(challenges) > 9 + self.selected_subghz_challenge:
            if challenges[9 + self.selected_subghz_challenge]['completed']:
                selected = selected + " \u2713"  # checkmark

        self.lcd.write_line(0, f">{selected}")
        self.lcd.write_line(1, "U/D SEL=Go L=Bk")

    def handle_subghz_menu(self):
        """Handle SubGHZ menu input"""
        if self.subghz is None:
            # No HackRF available
            if self.lcd.button_pressed(5):
                self.lcd.wait_button_release(5)
                self.current_state = State.MAIN_MENU
            return

        # BTN2: UP - navigate up
        if self.lcd.button_pressed(2):
            self.lcd.wait_button_release(2)
            self.selected_subghz_challenge = (self.selected_subghz_challenge - 1) % 3
            self.display_subghz_menu()

        # BTN3: DOWN - navigate down
        elif self.lcd.button_pressed(3):
            self.lcd.wait_button_release(3)
            self.selected_subghz_challenge = (self.selected_subghz_challenge + 1) % 3
            self.display_subghz_menu()

        # BTN1: SELECT - launch selected challenge
        elif self.lcd.button_pressed(1):
            self.lcd.wait_button_release(1)
            challenge_num = self.selected_subghz_challenge + 1  # Convert 0-2 to 1-3
            logger.info(f"Starting SubGHZ challenge {challenge_num}")
            self.run_subghz_challenge(challenge_num)

        # BTN5: BACK - return to main menu
        elif self.lcd.button_pressed(5):
            self.lcd.wait_button_release(5)
            logger.info("Returning to main menu")
            self.current_state = State.MAIN_MENU

    def run_subghz_challenge(self, challenge_num: int):
        """
        Execute a SubGHZ challenge

        Args:
            challenge_num: Challenge number (1-3)
        """
        start_time = time.time()
        points_earned = 0

        try:
            # Run the appropriate SubGHZ challenge
            if challenge_num == 1:
                points_earned = self.subghz.challenge_1_detect()
            elif challenge_num == 2:
                points_earned = self.subghz.challenge_2_replay()
            elif challenge_num == 3:
                points_earned = self.subghz.challenge_3_analyze()
            else:
                logger.error(f"Invalid SubGHZ challenge number: {challenge_num}")
                return

            time_taken = int(time.time() - start_time)

            # Record attempt in history (challenges 10-12 are SubGHZ)
            challenge_id = challenge_num + 9
            success = points_earned > 0
            self.db.add_history(challenge_id, success, time_taken)

            # If successful, mark as completed and update score
            if success:
                self.db.mark_completed(challenge_id, time_taken)
                self.current_score = self.db.get_total_score()
                logger.info(f"SubGHZ Challenge {challenge_num} completed! Score: {self.current_score}/150")

        except Exception as e:
            logger.error(f"Error running SubGHZ challenge {challenge_num}: {e}")

        # Return to SubGHZ menu
        self.current_state = State.SUBGHZ_MENU

    def display_ir_menu(self):
        """Display IR challenges menu"""
        if self.ir is None:
            self.lcd.clear()
            self.lcd.write_line(0, "IR - No FLIRC!")
            self.lcd.write_line(1, "L=Back")
            return

        # Get challenge statuses
        challenges = self.db.get_all_challenges()

        self.lcd.clear()

        # Show selected challenge with arrow
        challenge_names = ["Ch13:Detect", "Ch14:Replay", "Ch15:Protocol"]
        selected = challenge_names[self.selected_ir_challenge]

        # Add checkmark if completed (challenges 13-15 are at index 12-14)
        if len(challenges) > 12 + self.selected_ir_challenge:
            if challenges[12 + self.selected_ir_challenge]['completed']:
                selected = selected + " \u2713"  # checkmark

        self.lcd.write_line(0, f">{selected}")
        self.lcd.write_line(1, "U/D SEL=Go L=Bk")

    def handle_ir_menu(self):
        """Handle IR menu input"""
        if self.ir is None:
            # No FLIRC available
            if self.lcd.button_pressed(5):
                self.lcd.wait_button_release(5)
                self.current_state = State.MAIN_MENU
            return

        # BTN2: UP - navigate up
        if self.lcd.button_pressed(2):
            self.lcd.wait_button_release(2)
            self.selected_ir_challenge = (self.selected_ir_challenge - 1) % 3
            self.display_ir_menu()

        # BTN3: DOWN - navigate down
        elif self.lcd.button_pressed(3):
            self.lcd.wait_button_release(3)
            self.selected_ir_challenge = (self.selected_ir_challenge + 1) % 3
            self.display_ir_menu()

        # BTN1: SELECT - launch selected challenge
        elif self.lcd.button_pressed(1):
            self.lcd.wait_button_release(1)
            challenge_num = self.selected_ir_challenge + 1  # Convert 0-2 to 1-3
            logger.info(f"Starting IR challenge {challenge_num}")
            self.run_ir_challenge(challenge_num)

        # BTN5: BACK - return to main menu
        elif self.lcd.button_pressed(5):
            self.lcd.wait_button_release(5)
            logger.info("Returning to main menu")
            self.current_state = State.MAIN_MENU

    def run_ir_challenge(self, challenge_num: int):
        """
        Execute an IR challenge

        Args:
            challenge_num: Challenge number (1-3)
        """
        start_time = time.time()
        points_earned = 0

        try:
            # Run the appropriate IR challenge
            if challenge_num == 1:
                points_earned = self.ir.challenge_1_detect()
            elif challenge_num == 2:
                points_earned = self.ir.challenge_2_replay()
            elif challenge_num == 3:
                points_earned = self.ir.challenge_3_protocol()
            else:
                logger.error(f"Invalid IR challenge number: {challenge_num}")
                return

            time_taken = int(time.time() - start_time)

            # Record attempt in history (challenges 13-15 are IR)
            challenge_id = challenge_num + 12
            success = points_earned > 0
            self.db.add_history(challenge_id, success, time_taken)

            # If successful, mark as completed and update score
            if success:
                self.db.mark_completed(challenge_id, time_taken)
                self.current_score = self.db.get_total_score()
                logger.info(f"IR Challenge {challenge_num} completed! Score: {self.current_score}/150")

        except Exception as e:
            logger.error(f"Error running IR challenge {challenge_num}: {e}")

        # Return to IR menu
        self.current_state = State.IR_MENU

    def main_loop(self):
        """Main state machine loop"""
        logger.info("Entering main loop")
        logger.info(f"Initial state: {self.current_state}")

        while True:
            try:
                if self.current_state == State.HOME_SCREEN:
                    logger.info("Displaying home screen")
                    self.display_home_screen()
                    while self.current_state == State.HOME_SCREEN:
                        self.handle_home_screen()
                        time.sleep(0.1)

                elif self.current_state == State.MAIN_MENU:
                    logger.info("Displaying main menu")
                    self.display_main_menu()
                    logger.info("Main menu displayed, entering input loop")
                    while self.current_state == State.MAIN_MENU:
                        self.handle_main_menu()
                        time.sleep(0.1)

                elif self.current_state == State.IBUTTON_MENU:
                    self.display_ibutton_menu()
                    while self.current_state == State.IBUTTON_MENU:
                        self.handle_ibutton_menu()
                        time.sleep(0.1)

                elif self.current_state == State.NFC_MENU:
                    self.display_nfc_menu()
                    while self.current_state == State.NFC_MENU:
                        self.handle_nfc_menu()
                        time.sleep(0.1)

                elif self.current_state == State.RFID_MENU:
                    self.display_rfid_menu()
                    while self.current_state == State.RFID_MENU:
                        self.handle_rfid_menu()
                        time.sleep(0.1)

                elif self.current_state == State.SUBGHZ_MENU:
                    self.display_subghz_menu()
                    while self.current_state == State.SUBGHZ_MENU:
                        self.handle_subghz_menu()
                        time.sleep(0.1)

                elif self.current_state == State.IR_MENU:
                    self.display_ir_menu()
                    while self.current_state == State.IR_MENU:
                        self.handle_ir_menu()
                        time.sleep(0.1)

                elif self.current_state == State.SETTINGS:
                    self.display_settings()
                    while self.current_state == State.SETTINGS:
                        self.handle_settings()
                        time.sleep(0.1)

                elif self.current_state == State.RESET_CONFIRM:
                    self.reset_scores_confirm()

                # Other states are handled within their respective functions

            except Exception as e:
                logger.error(f"Error in main loop: {e}", exc_info=True)
                time.sleep(1)

    def cleanup(self):
        """Clean up resources before exit"""
        logger.info("Cleaning up...")

        try:
            if self.lcd:
                self.lcd.clear()
                self.lcd.write_line(0, "  Shutting down  ")
                self.lcd.write_line(1, "   Bye bye...   ")
                time.sleep(2)
                self.lcd.clear()
                self.lcd.close()

            if self.ibutton:
                self.ibutton.close()

            if self.subghz:
                self.subghz.close()

            if self.ir:
                self.ir.close()

            if self.db:
                self.db.close()

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    def run(self):
        """Main entry point"""
        try:
            self.init_system()
            self.main_loop()

        except KeyboardInterrupt:
            logger.info("Interrupted by user")

        except Exception as e:
            logger.error(f"Fatal error: {e}", exc_info=True)

        finally:
            self.cleanup()


def main():
    """Entry point"""
    logger.info("=" * 50)
    logger.info("ZeroRange starting...")
    logger.info("=" * 50)

    app = ZeroRange()
    app.run()

    logger.info("ZeroRange stopped")


if __name__ == "__main__":
    main()
