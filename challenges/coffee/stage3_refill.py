"""Stage 3 — Top Up the Balance.

Learner presents a forged MIFARE Classic 1K badge (magic card or Flipper
emulation) with a valid value block at block 40 whose decoded value
is >= the configured threshold (default 5000 cents = 50,00 EUR).

PM3 reads block 40 and validates the value block structure.
"""

import time
import logging
from typing import Optional

from challenges.coffee.value_block import validate, decode, ValueBlockError

logger = logging.getLogger(__name__)

_KEY_B = "B4EEC0FFEE11"
_VALUE_BLOCK_ADDR = 40
_BREWMASTER_TAG = b"BREW"


class Stage3:
    """Credit top-up / value-block forgery challenge."""

    def __init__(self, lcd, db, config: dict, proxmark, sse_emit=None):
        self.lcd = lcd
        self.db = db
        self.cfg = config
        self.pm3 = proxmark
        self.sse = sse_emit or (lambda _: None)

    # ------------------------------------------------------------------ helpers

    def _challenge_id(self) -> int:
        return 18

    def _already_complete(self) -> bool:
        status = self.db.get_challenge_status(self._challenge_id())
        return status is not None and status["completed"]

    def _award(self, time_taken: int) -> None:
        self.db.add_history(self._challenge_id(), True, time_taken)
        self.db.mark_completed(self._challenge_id(), time_taken)
        self.sse({"stage": 3, "status": "success", "points": 10})

    def _threshold(self) -> int:
        return int(self.cfg.get("credit_threshold_cents", 5000))

    def _read_block40(self) -> Optional[bytes]:
        """Read block 40 with Key B. Returns 16 raw bytes or None."""
        key_b = self.cfg.get("master_key_b_hex", _KEY_B)
        addr = int(self.cfg.get("value_block_addr", _VALUE_BLOCK_ADDR))
        try:
            return self.pm3.read_block(addr, bytes.fromhex(key_b), "B")
        except Exception as exc:
            logger.warning(f"PM3 read_block error: {exc}")
            return None

    def _check_sanity(self) -> bool:
        """Quick check: is block 1 tagged with BREWMASTERPRO?"""
        try:
            data = self.pm3.read_block(1, bytes.fromhex("FFFFFFFFFFFF"), "A")
            return data is not None and data[:4] == _BREWMASTER_TAG
        except Exception:
            return True  # Don't hard-block on this sanity check

    # ------------------------------------------------------------------ public

    def run(self) -> int:
        """Run Stage 3. Returns points earned (10 or 0)."""
        logger.info("Coffee Stage 3: Top-up starting")

        if self._already_complete():
            self.lcd.clear()
            self.lcd.write_line(0, "Stage 3 done!")
            self.lcd.write_line(1, "Already solved ✓")
            time.sleep(2)
            return 0

        if self.pm3 is None or self.pm3.simulation_mode:
            self.lcd.clear()
            self.lcd.write_line(0, "Proxmark3 needed")
            self.lcd.write_line(1, "Not detected!")
            time.sleep(3)
            return 0

        threshold = self._threshold()
        threshold_eur = f"{threshold // 100},{threshold % 100:02d}"

        self.lcd.clear()
        self.lcd.write_line(0, "Coffee Stage 3")
        self.lcd.write_line(1, "Refill your card")
        time.sleep(2)

        self.lcd.clear()
        self.lcd.write_line(0, f"Need >={threshold_eur} EUR")
        self.lcd.write_line(1, "Present to PM3")
        time.sleep(2)

        start_time = time.time()

        while True:
            self.lcd.clear()
            self.lcd.write_line(0, "Hold card to PM3")
            self.lcd.write_line(1, "SEL=Read ◄=Back")

            # Wait for SELECT or BACK
            while True:
                if self.lcd.button_pressed(1):
                    self.lcd.wait_button_release(1)
                    break
                if self.lcd.button_pressed(5):
                    self.lcd.wait_button_release(5)
                    return 0
                time.sleep(0.1)

            self.lcd.clear()
            self.lcd.write_line(0, "Reading block 40")
            self.lcd.write_line(1, "Please wait...")

            raw = self._read_block40()

            if raw is None:
                self.lcd.clear()
                self.lcd.write_line(0, "Auth failed!")
                self.lcd.write_line(1, "Need Key B badge")
                self.sse({"event": "credit_observed", "value_cents": None, "error": "auth_failed"})
                time.sleep(3)
                continue

            # Validate structure
            try:
                validate(raw)
            except ValueBlockError as exc:
                reason = str(exc)
                # Map to short LCD reason
                if "Bad ~V" in reason:
                    lcd_reason = "Bad ~V"
                elif "Bad addr" in reason:
                    lcd_reason = "Bad addr"
                else:
                    lcd_reason = reason[:14]
                self.lcd.clear()
                self.lcd.write_line(0, "Invalid block!")
                self.lcd.write_line(1, lcd_reason)
                logger.info(f"Stage 3 invalid block: {reason} | raw={raw.hex()}")
                self.sse({"event": "credit_observed", "value_cents": None, "error": lcd_reason})
                time.sleep(3)
                continue

            value = decode(raw)
            logger.info(f"Stage 3 block 40 value={value} cents (threshold={threshold})")
            self.sse({"event": "credit_observed", "value_cents": value})

            if value < threshold:
                value_eur = f"{value // 100},{value % 100:02d}"
                self.lcd.clear()
                self.lcd.write_line(0, "Value too low!")
                self.lcd.write_line(1, f"{value_eur} EUR < {threshold_eur}")
                time.sleep(3)
                continue

            # Success!
            elapsed = int(time.time() - start_time)
            value_eur = f"{value // 100},{value % 100:02d}"
            self._award(elapsed)
            logger.info(f"Stage 3 completed in {elapsed}s, value={value} cents")

            self.lcd.clear()
            self.lcd.write_line(0, "TOPPED UP! +10pt")
            self.lcd.write_line(1, f"{value_eur} EUR OK!")
            time.sleep(3)

            self.lcd.clear()
            self.lcd.write_line(0, "COFFEE MODULE")
            self.lcd.write_line(1, "COMPLETE! 30/30!")
            time.sleep(4)

            self.lcd.clear()
            self.lcd.write_line(0, "Congratulations!")
            self.lcd.write_line(1, "◄=Back to menu")
            while not self.lcd.button_pressed(5):
                time.sleep(0.1)
            self.lcd.wait_button_release(5)
            return 10
