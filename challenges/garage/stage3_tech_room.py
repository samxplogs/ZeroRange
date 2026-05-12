"""Stage 3 — Tech Room (Proxmark3 MIFARE Classic, 10 pts).

PM3 emulates tech_room.nfc (sector 0 Key A = F15EC0DE0017).
Learner reads sector 0 with the leaked Key A to confirm access.
Auto-detect: PM3 emulation logs show Key A auth on sector 0.
Manual confirm: learner presses SELECT.
"""

import time
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class Stage3:
    _CHALLENGE_ID = 21

    def __init__(self, lcd, db, config: dict, proxmark, sse_emit=None):
        self.lcd = lcd
        self.db = db
        self.cfg = config
        self.pm3 = proxmark
        self.sse = sse_emit or (lambda _: None)

    def _already_complete(self) -> bool:
        status = self.db.get_challenge_status(self._CHALLENGE_ID)
        return status is not None and status["completed"]

    def _award(self, elapsed: int) -> None:
        self.db.add_history(self._CHALLENGE_ID, True, elapsed)
        self.db.mark_completed(self._CHALLENGE_ID, elapsed)
        self.sse({"stage": 3, "status": "success", "points": 10})
        self.sse({"event": "stage_complete", "stage": 3, "points": 10})
        self.sse({"event": "credit_summary", "stage": 3, "subtotal": 10, "total": 30})

    def _badge_path(self) -> Path:
        rel = self.cfg.get("badge_path", "challenges/garage/badges/tech_room.nfc")
        return Path(rel)

    def run(self) -> int:
        logger.info("Garage Stage 3: Tech room starting")

        if self._already_complete():
            self.lcd.clear()
            self.lcd.write_line(0, "Stage 3 done!")
            self.lcd.write_line(1, "Already solved ◄")
            while not self.lcd.button_pressed(5):
                time.sleep(0.1)
            self.lcd.wait_button_release(5)
            return 0

        # Pretext
        self.lcd.clear()
        self.lcd.write_line(0, "Garage Stage 3")
        self.lcd.write_line(1, "Tech room. Open!")
        time.sleep(2)

        if self.pm3 is None or self.pm3.simulation_mode:
            self.lcd.clear()
            self.lcd.write_line(0, "PM3 not found!")
            self.lcd.write_line(1, "Connect PM3 ◄")
            while not self.lcd.button_pressed(5):
                time.sleep(0.1)
            self.lcd.wait_button_release(5)
            return 0

        badge_path = self._badge_path()
        self.lcd.clear()
        self.lcd.write_line(0, "Loading badge...")
        self.lcd.write_line(1, "Starting PM3 sim")

        try:
            handle = self.pm3.emulate_mfc_from_file(badge_path)
        except Exception as exc:
            logger.error(f"Stage 3 emulation start failed: {exc}")
            self.lcd.clear()
            self.lcd.write_line(0, "PM3 load failed!")
            self.lcd.write_line(1, str(exc)[:16])
            time.sleep(3)
            return 0

        logger.info("Stage 3: emulating tech_room badge")
        start_time = time.time()
        key_a_hex = self.cfg.get("tech_room_key_a_hex", "F15EC0DE0017")
        key_a_bytes = bytes.fromhex(key_a_hex)
        sector0_blocks = [0, 1, 2]
        found = set()

        try:
            while True:
                self.lcd.clear()
                self.lcd.write_line(0, "PM3 emulates card")
                self.lcd.write_line(1, "SEL=Done ◄=Back")

                # Auto-detect: check PM3 sim log for Key A auth on sector 0
                if handle.log_lines:
                    for line in handle.log_lines:
                        line_l = line.lower()
                        if "authed" in line_l or "auth" in line_l:
                            for blk in sector0_blocks:
                                if f"block {blk}" in line_l or f"blk {blk}" in line_l:
                                    found.add(blk)
                    if found >= set(sector0_blocks):
                        elapsed = int(time.time() - start_time)
                        logger.info(f"Stage 3 auto-completed in {elapsed}s")
                        self._show_success(elapsed)
                        return 10

                if self.lcd.button_pressed(1):  # SELECT — manual verify
                    self.lcd.wait_button_release(1)
                    # Read block 0 with Key A to verify
                    ok = self._manual_verify(key_a_bytes)
                    if ok:
                        elapsed = int(time.time() - start_time)
                        self._show_success(elapsed)
                        return 10
                    else:
                        self.lcd.clear()
                        self.lcd.write_line(0, "Not yet!")
                        self.lcd.write_line(1, "Use Key A first")
                        time.sleep(2)

                if self.lcd.button_pressed(5):  # BACK
                    self.lcd.wait_button_release(5)
                    return 0

                time.sleep(0.2)

        finally:
            handle.stop()
            logger.info("Stage 3: emulation stopped")

    def _manual_verify(self, key_a: bytes) -> bool:
        """Read block 0 with Key A; return True on success."""
        self.lcd.clear()
        self.lcd.write_line(0, "Verifying...")
        self.lcd.write_line(1, "Reading sector 0")
        try:
            data = self.pm3.read_block(0, key_a, "A")
            return data is not None and len(data) == 16
        except Exception as exc:
            logger.warning(f"Stage 3 verify failed: {exc}")
            return False

    def _show_success(self, elapsed: int) -> None:
        self._award(elapsed)
        self.lcd.clear()
        self.lcd.write_line(0, "Access granted!")
        self.lcd.write_line(1, "+10pts  30/30!")
        time.sleep(3)
        self.lcd.clear()
        self.lcd.write_line(0, "Module complete!")
        self.lcd.write_line(1, "◄=Back to menu")
        while not self.lcd.button_pressed(5):
            time.sleep(0.1)
        self.lcd.wait_button_release(5)
