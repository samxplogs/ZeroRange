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
from typing import Optional

from lcd_manager import LCDManager
from ibutton_handler import iButtonHandler
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
    MAIN_MENU = "MAIN_MENU"
    IBUTTON_MENU = "IBUTTON_MENU"
    NFC_MENU = "NFC_MENU"
    RFID_MENU = "RFID_MENU"
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
        self.db: Optional[Database] = None

        self.current_state = State.MAIN_MENU
        self.current_score = 0
        self.selected_menu_item = 0  # 0=iButton, 1=NFC, 2=RFID, 3=IR, 4=Settings
        self.menu_items = ["iButton", "NFC", "RFID", "IR", "Settings"]

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
            self.ibutton = iButtonHandler(self.lcd)

            self.lcd.write_line(1, "Ready!")
            time.sleep(1)

            logger.info(f"Initialization complete. Current score: {self.current_score}/40")

        except Exception as e:
            logger.error(f"Failed to initialize system: {e}")
            if self.lcd:
                self.lcd.clear()
                self.lcd.write_line(0, "INIT FAILED!")
                self.lcd.write_line(1, "Check logs")
                time.sleep(5)
            raise

    def display_main_menu(self):
        """Display main menu screen"""
        self.lcd.clear()
        self.lcd.write_line(0, f"ZeroRange {self.current_score}/40")
        self.lcd.write_line(1, "1:iBtn 4:Set")

    def handle_main_menu(self):
        """Handle main menu button input"""
        if self.lcd.button_pressed(1):
            self.lcd.wait_button_release(1)
            logger.info("Entering iButton menu")
            self.current_state = State.IBUTTON_MENU

        elif self.lcd.button_pressed(4):
            self.lcd.wait_button_release(4)
            logger.info("Entering settings")
            self.current_state = State.SETTINGS

    def display_ibutton_menu(self):
        """Display iButton challenges menu"""
        # Get challenge statuses
        challenges = self.db.get_all_challenges()

        self.lcd.clear()
        self.lcd.write_line(0, "iBtn Challenges")

        # Count completed challenges
        completed = sum(1 for ch in challenges[:3] if ch['completed'])
        self.lcd.write_line(1, f"{completed}/3 done 1-3:Go")

    def handle_ibutton_menu(self):
        """Handle iButton menu button input"""
        # BTN1-3: Launch challenges
        for btn in range(1, 4):
            if self.lcd.button_pressed(btn):
                self.lcd.wait_button_release(btn)
                logger.info(f"Starting challenge {btn}")
                self.run_challenge(btn)
                return

        # BTN5: Back to main menu
        if self.lcd.button_pressed(5):
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

    def main_loop(self):
        """Main state machine loop"""
        logger.info("Entering main loop")

        while True:
            try:
                if self.current_state == State.MAIN_MENU:
                    self.display_main_menu()
                    while self.current_state == State.MAIN_MENU:
                        self.handle_main_menu()
                        time.sleep(0.1)

                elif self.current_state == State.IBUTTON_MENU:
                    self.display_ibutton_menu()
                    while self.current_state == State.IBUTTON_MENU:
                        self.handle_ibutton_menu()
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
                self.lcd.write_line(1, "Shutting down...")
                time.sleep(1)
                self.lcd.clear()
                self.lcd.close()

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
