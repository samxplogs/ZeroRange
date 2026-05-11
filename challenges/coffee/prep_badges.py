"""Prep Badges — standalone badge emulation tool for the Coffee module.

Lets a trainer (or learner) emulate either reference badge via PM3 so a
Flipper Zero or other NFC device can read and save it.

Controls during emulation:
  SELECT  — toggle Key B display on/off
  ◄ BACK  — stop emulation and return
"""

import time
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_KEY_B_FORMATTED = "B4 EE C0 FF EE 11"


class PrepBadges:
    """Badge emulation prep tool — no scoring, no prerequisites."""

    def __init__(self, lcd, config: dict, proxmark):
        self.lcd = lcd
        self.cfg = config
        self.pm3 = proxmark

    # ------------------------------------------------------------------ public

    def run(self) -> None:
        """Show badge selection menu and handle emulation sessions."""
        badge_options = [
            ("Low  1,50 EUR", "low"),
            ("High 50,00 EUR", "high"),
        ]
        selected = 0

        while True:
            label, key = badge_options[selected]
            self.lcd.clear()
            self.lcd.write_line(0, f">{label}")
            self.lcd.write_line(1, "U/D SEL=Go ◄=Bk")

            if self.lcd.button_pressed(2):       # UP
                self.lcd.wait_button_release(2)
                selected = (selected - 1) % len(badge_options)
            elif self.lcd.button_pressed(3):     # DOWN
                self.lcd.wait_button_release(3)
                selected = (selected + 1) % len(badge_options)
            elif self.lcd.button_pressed(1):     # SELECT — launch emulation
                self.lcd.wait_button_release(1)
                self._emulate(label.strip(), key)
            elif self.lcd.button_pressed(5):     # BACK — exit prep
                self.lcd.wait_button_release(5)
                return

            time.sleep(0.1)

    # ------------------------------------------------------------------ private

    def _badge_path(self, key: str) -> Path:
        paths = self.cfg.get("badge_paths", {})
        rel = paths.get(key, f"challenges/coffee/badges/credit_{key}.nfc")
        return Path(rel)

    def _emulate(self, label: str, badge_key: str) -> None:
        """Start PM3 emulation of the selected badge."""
        if self.pm3 is None or self.pm3.simulation_mode:
            self.lcd.clear()
            self.lcd.write_line(0, "PM3 not found!")
            self.lcd.write_line(1, "Connect PM3 ◄=Bk")
            while not self.lcd.button_pressed(5):
                time.sleep(0.1)
            self.lcd.wait_button_release(5)
            return

        badge_path = self._badge_path(badge_key)
        self.lcd.clear()
        self.lcd.write_line(0, f"Loading {label[:10]}")
        self.lcd.write_line(1, "Starting PM3...")

        try:
            handle = self.pm3.emulate_mfc_from_file(badge_path)
        except Exception as exc:
            logger.error(f"Prep emulation failed: {exc}")
            self.lcd.clear()
            self.lcd.write_line(0, "PM3 load failed!")
            self.lcd.write_line(1, str(exc)[:16])
            time.sleep(3)
            return

        logger.info(f"Prep: emulating {badge_key} badge")
        show_key = False

        try:
            while True:
                self.lcd.clear()
                if show_key:
                    self.lcd.write_line(0, _KEY_B_FORMATTED)
                    self.lcd.write_line(1, "SEL=Hide  ◄=Stop")
                else:
                    short = label[:14]
                    self.lcd.write_line(0, f"Emul: {short}")
                    self.lcd.write_line(1, "SEL=KeyB  ◄=Stop")

                if self.lcd.button_pressed(1):   # SEL — toggle Key B
                    self.lcd.wait_button_release(1)
                    show_key = not show_key

                elif self.lcd.button_pressed(5): # BACK — stop
                    self.lcd.wait_button_release(5)
                    break

                time.sleep(0.15)

        finally:
            handle.stop()
            logger.info("Prep: emulation stopped")

        self.lcd.clear()
        self.lcd.write_line(0, "Emulation stopped")
        self.lcd.write_line(1, "Badge saved? OK!")
        time.sleep(2)
