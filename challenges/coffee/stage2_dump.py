"""Stage 2 — Crack & Dump the Employee Badge.

The Pi instructs the Proxmark3 to emulate credit_low.nfc while the learner
reads it with their Flipper Zero. Stage passes when all sectors 8-14 have
been accessed with the correct Key B (auto-detected via PM3 log) or the
learner explicitly confirms success (manual verify path).
"""

import time
import logging
import threading
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

_SECTORS_NEEDED = set(range(8, 15))   # sectors 8-14
_KEY_B = "B4EEC0FFEE11"


class Stage2:
    """Badge dump / crack challenge."""

    def __init__(self, lcd, db, config: dict, proxmark, sse_emit=None):
        """
        Args:
            lcd:       LCDManager instance.
            db:        Database instance.
            config:    'coffee' sub-dict from config.json.
            proxmark:  ProxmarkHandler instance.
            sse_emit:  Optional callable(dict) for SSE events.
        """
        self.lcd = lcd
        self.db = db
        self.cfg = config
        self.pm3 = proxmark
        self.sse = sse_emit or (lambda _: None)
        self._emulation_handle = None
        self._unlocked_sectors: set[int] = set()
        self._lock = threading.Lock()

    # ------------------------------------------------------------------ helpers

    def _challenge_id(self) -> int:
        return 17

    def _already_complete(self) -> bool:
        status = self.db.get_challenge_status(self._challenge_id())
        return status is not None and status["completed"]

    def _award(self, time_taken: int) -> None:
        self.db.add_history(self._challenge_id(), True, time_taken)
        self.db.mark_completed(self._challenge_id(), time_taken)
        self.sse({"stage": 2, "status": "success", "points": 10})

    def _badge_path(self) -> Path:
        low = self.cfg.get("badge_paths", {}).get("low", "challenges/coffee/badges/credit_low.nfc")
        return Path(low)

    def _start_emulation(self) -> bool:
        """Convert badge to .eml and start PM3 emulation. Returns True on success."""
        try:
            badge_path = self._badge_path()
            handle = self.pm3.emulate_mfc_from_file(badge_path)
            self._emulation_handle = handle
            logger.info("PM3 emulation started for Stage 2")
            return True
        except Exception as exc:
            logger.error(f"Failed to start PM3 emulation: {exc}")
            return False

    def _stop_emulation(self) -> None:
        if self._emulation_handle is not None:
            try:
                self._emulation_handle.stop()
            except Exception as exc:
                logger.warning(f"Error stopping emulation: {exc}")
            self._emulation_handle = None

    def _parse_log_for_keys(self) -> None:
        """Check PM3 emulation log for sectors authenticated with Key B."""
        if self._emulation_handle is None:
            return
        try:
            for line in self._emulation_handle.read_log_lines():
                # PM3 hf mf sim output shows key auth attempts, e.g.:
                # "Auth sector 10 key B B4EEC0FFEE11"
                line_up = line.upper()
                if _KEY_B in line_up.replace(" ", ""):
                    # Try to extract sector number
                    import re
                    m = re.search(r"SECT(?:OR)?\s*(\d+)", line_up)
                    if m:
                        sec = int(m.group(1))
                        if sec in _SECTORS_NEEDED:
                            with self._lock:
                                self._unlocked_sectors.add(sec)
                                logger.debug(f"Stage 2: sector {sec} unlocked via log")
        except Exception as exc:
            logger.debug(f"Log parse error (non-fatal): {exc}")

    def _verify_manual(self) -> bool:
        """Ask PM3 to read sectors 8-14 using Key B. Returns True if all readable."""
        key_b = self.cfg.get("master_key_b_hex", _KEY_B)
        for sector in range(8, 15):
            first_block = sector * 4
            try:
                data = self.pm3.read_block(first_block, bytes.fromhex(key_b), "B")
                if data is not None:
                    with self._lock:
                        self._unlocked_sectors.add(sector)
            except Exception as exc:
                logger.warning(f"Manual verify sector {sector} failed: {exc}")
                return False
        with self._lock:
            return _SECTORS_NEEDED.issubset(self._unlocked_sectors)

    # ------------------------------------------------------------------ public

    def run(self) -> int:
        """Run Stage 2. Returns points earned (10 or 0)."""
        logger.info("Coffee Stage 2: Dump & Crack starting")

        if self._already_complete():
            self.lcd.clear()
            self.lcd.write_line(0, "Stage 2 done!")
            self.lcd.write_line(1, "Already solved ✓")
            time.sleep(2)
            return 0

        # Check PM3 present
        if self.pm3 is None or self.pm3.simulation_mode:
            self.lcd.clear()
            self.lcd.write_line(0, "Proxmark3 needed")
            self.lcd.write_line(1, "Not detected!")
            time.sleep(3)
            return 0

        self.lcd.clear()
        self.lcd.write_line(0, "Coffee Stage 2")
        self.lcd.write_line(1, "Starting PM3...")
        time.sleep(1)

        if not self._start_emulation():
            self.lcd.clear()
            self.lcd.write_line(0, "PM3 emul failed")
            self.lcd.write_line(1, "Reconnect PM3")
            time.sleep(4)
            return 0

        try:
            return self._run_with_emulation()
        finally:
            self._stop_emulation()

    def _run_with_emulation(self) -> int:
        self.lcd.clear()
        self.lcd.write_line(0, "PM3 emulates")
        self.lcd.write_line(1, "badge. Read it!")
        time.sleep(2)

        self.lcd.clear()
        self.lcd.write_line(0, "Use Flipper Zero")
        self.lcd.write_line(1, "Add KeyB hint→")
        time.sleep(3)

        start_time = time.time()
        while True:
            elapsed = int(time.time() - start_time)

            # Poll log for auto-detection
            self._parse_log_for_keys()

            with self._lock:
                unlocked = set(self._unlocked_sectors)

            if _SECTORS_NEEDED.issubset(unlocked):
                elapsed = int(time.time() - start_time)
                logger.info(f"Stage 2 auto-detected complete in {elapsed}s")
                return self._success(elapsed)

            # Show progress
            count = len(unlocked & _SECTORS_NEEDED)
            self.lcd.clear()
            self.lcd.write_line(0, f"Sectors:{count}/7 done")
            self.lcd.write_line(1, "SEL=Done ◄=Back")

            # Manual confirm button
            if self.lcd.button_pressed(1):
                self.lcd.wait_button_release(1)
                self.lcd.clear()
                self.lcd.write_line(0, "Verifying...")
                self.lcd.write_line(1, "PM3 reading...")
                if self._verify_manual():
                    elapsed = int(time.time() - start_time)
                    return self._success(elapsed)
                else:
                    self.lcd.clear()
                    self.lcd.write_line(0, "Not all sectors")
                    self.lcd.write_line(1, "readable w/ KeyB")
                    time.sleep(3)

            # Back button
            if self.lcd.button_pressed(5):
                self.lcd.wait_button_release(5)
                logger.info("Stage 2 aborted by user")
                return 0

            time.sleep(1)

    def _success(self, elapsed: int) -> int:
        self._award(elapsed)
        self.lcd.clear()
        self.lcd.write_line(0, "ALL SECTORS READ")
        self.lcd.write_line(1, "+10pts Stage 2!")
        time.sleep(3)
        self.lcd.clear()
        self.lcd.write_line(0, "Stage 2 done!")
        self.lcd.write_line(1, "◄=Back to menu")
        while not self.lcd.button_pressed(5):
            time.sleep(0.1)
        self.lcd.wait_button_release(5)
        return 10
