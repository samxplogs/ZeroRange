"""Stage 1 — Technician Token.

Prompts the learner to touch the maintenance iButton to the USB HID reader.
On success: awards 10 pts and reveals the leaked Key B for sectors 8-14.
"""

import time
import logging
from typing import Optional

logger = logging.getLogger(__name__)

_MAX_LINE = 16


class Stage1:
    """Technician-token iButton challenge."""

    def __init__(self, lcd, db, config: dict, hid_reader, sse_emit=None):
        """
        Args:
            lcd:        LCDManager instance.
            db:         Database instance.
            config:     The 'coffee' sub-dict from config.json.
            hid_reader: Object with wait_for_uid(timeout) -> Optional[str].
            sse_emit:   Optional callable(dict) for SSE events.
        """
        self.lcd = lcd
        self.db = db
        self.cfg = config
        self.hid = hid_reader
        self.sse = sse_emit or (lambda _: None)

    # ------------------------------------------------------------------ helpers

    def _challenge_id(self) -> int:
        return 16

    def _already_complete(self) -> bool:
        status = self.db.get_challenge_status(self._challenge_id())
        return status is not None and status["completed"]

    def _award(self, time_taken: int) -> None:
        self.db.add_history(self._challenge_id(), True, time_taken)
        self.db.mark_completed(self._challenge_id(), time_taken)
        self.sse({"stage": 1, "status": "success", "points": 10})

    def _show_leak(self) -> None:
        key_b = self.cfg.get("master_key_b_hex", "B4EEC0FFEE11")
        # Insert spaces every 2 chars for readability
        formatted = " ".join(key_b[i:i+2] for i in range(0, len(key_b), 2))
        self.lcd.clear()
        self.lcd.write_line(0, "Leaked log:")
        self.lcd.write_line(1, f"KeyB={formatted[:11]}")
        time.sleep(4)
        # Second screen for longer key display
        self.lcd.clear()
        self.lcd.write_line(0, "Sectors 8-14:")
        self.lcd.write_line(1, formatted[:16])
        time.sleep(3)

    # ------------------------------------------------------------------ public

    def run(self) -> int:
        """Run Stage 1. Returns points earned (10 or 0)."""
        logger.info("Coffee Stage 1: Technician Token starting")

        if self._already_complete():
            logger.info("Stage 1 already completed, skipping to leak reveal")
            self._show_leak()
            return 0  # Don't re-award

        # Splash / pretext
        self.lcd.clear()
        self.lcd.write_line(0, "Coffee Stage 1")
        self.lcd.write_line(1, "Pull maint token")
        time.sleep(2)

        max_wrong = self.cfg.get("max_wrong_reads_stage1", 3)
        wrong_streak = 0
        target_uid = self.cfg.get("technician_uid", "0100C0FFEE7E11AB").upper().replace("-", "")
        start_time = time.time()

        while True:
            self.lcd.clear()
            self.lcd.write_line(0, "Touch iBtn token")
            self.lcd.write_line(1, "◄=Back")

            uid = self.hid.wait_for_uid(timeout=60)

            if uid is None:
                # Back button pressed or timeout
                if self.lcd.button_pressed(5):
                    self.lcd.wait_button_release(5)
                    logger.info("Stage 1 aborted by user")
                    return 0
                # Timeout — offer retry
                self.lcd.clear()
                self.lcd.write_line(0, "No token seen")
                self.lcd.write_line(1, "SEL=Retry ◄=Back")
                while True:
                    if self.lcd.button_pressed(1):
                        self.lcd.wait_button_release(1)
                        break
                    if self.lcd.button_pressed(5):
                        self.lcd.wait_button_release(5)
                        return 0
                    time.sleep(0.1)
                continue

            # Normalise: strip dashes, upper-case
            uid_norm = uid.upper().replace("-", "").replace(" ", "")

            if uid_norm == target_uid:
                elapsed = int(time.time() - start_time)
                logger.info(f"Stage 1 completed in {elapsed}s, UID={uid_norm}")
                self.lcd.clear()
                self.lcd.write_line(0, "Token OK! +10pts")
                self.lcd.write_line(1, "Stage 1 SOLVED")
                time.sleep(2)
                self._award(elapsed)
                self._show_leak()
                self.lcd.clear()
                self.lcd.write_line(0, "Stage 1 done!")
                self.lcd.write_line(1, "◄=Back to menu")
                while not self.lcd.button_pressed(5):
                    time.sleep(0.1)
                self.lcd.wait_button_release(5)
                return 10
            else:
                wrong_streak += 1
                logger.warning(f"Stage 1 wrong UID: {uid_norm} (expected {target_uid}), streak={wrong_streak}")
                self.lcd.clear()
                self.lcd.write_line(0, "Wrong token!")
                if wrong_streak >= max_wrong:
                    self.lcd.write_line(1, "Check right token")
                    time.sleep(3)
                    self.lcd.clear()
                    self.lcd.write_line(0, "Wrong token")
                    self.lcd.write_line(1, "SEL=Retry ◄=Back")
                    wrong_streak = 0
                    while True:
                        if self.lcd.button_pressed(1):
                            self.lcd.wait_button_release(1)
                            break
                        if self.lcd.button_pressed(5):
                            self.lcd.wait_button_release(5)
                            return 0
                        time.sleep(0.1)
                else:
                    self.lcd.write_line(1, f"Try again ({max_wrong - wrong_streak} left)")
                    time.sleep(2)
