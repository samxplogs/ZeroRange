"""Stage 2 — Pedestrian Gate (iButton, 10 pts).

Learner touches the configured DS1990 iButton to the USB HID reader.
On success: awards 10 pts and reveals the tech-room Key A as a "side-channel
post-it leak" on the LCD and web companion.
"""

import time
import logging

logger = logging.getLogger(__name__)


class Stage2:
    _CHALLENGE_ID = 20

    def __init__(self, lcd, db, config: dict, hid_reader, sse_emit=None):
        self.lcd = lcd
        self.db = db
        self.cfg = config
        self.hid = hid_reader
        self.sse = sse_emit or (lambda _: None)

    def _already_complete(self) -> bool:
        status = self.db.get_challenge_status(self._CHALLENGE_ID)
        return status is not None and status["completed"]

    def _award(self, elapsed: int) -> None:
        self.db.add_history(self._CHALLENGE_ID, True, elapsed)
        self.db.mark_completed(self._CHALLENGE_ID, elapsed)
        self.sse({"stage": 2, "status": "success", "points": 10})
        self.sse({"event": "stage_complete", "stage": 2, "points": 10})

    def _show_leak(self) -> None:
        raw = self.cfg.get("tech_room_key_a_hex", "F15EC0DE0017")
        fmt = " ".join(raw[i:i+2] for i in range(0, len(raw), 2))
        self.lcd.clear()
        self.lcd.write_line(0, "Post-it on door:")
        self.lcd.write_line(1, fmt[:16])
        time.sleep(4)
        self.lcd.clear()
        self.lcd.write_line(0, "Tech room Key A:")
        self.lcd.write_line(1, fmt[:16])
        time.sleep(3)
        self.sse({"event": "key_leaked", "key_a_hex": raw})

    def run(self) -> int:
        logger.info("Garage Stage 2: Pedestrian gate starting")

        if self._already_complete():
            self._show_leak()
            return 0

        self.lcd.clear()
        self.lcd.write_line(0, "Garage Stage 2")
        self.lcd.write_line(1, "Side gate. Fob?")
        time.sleep(2)

        if self.hid is None:
            self.lcd.clear()
            self.lcd.write_line(0, "iBtn reader N/A")
            self.lcd.write_line(1, "Connect reader ◄")
            while not self.lcd.button_pressed(5):
                time.sleep(0.1)
            self.lcd.wait_button_release(5)
            return 0

        max_wrong = self.cfg.get("max_wrong_reads_stage2", 3)
        target_uid = (
            self.cfg.get("pedestrian_uid", "")
            .upper().replace("-", "").replace(" ", "")
        )
        wrong_streak = 0
        start_time = time.time()

        while True:
            self.lcd.clear()
            self.lcd.write_line(0, "Touch iBtn fob")
            self.lcd.write_line(1, "◄=Back")

            uid = self.hid.wait_for_uid(timeout=60)

            if uid is None:
                self.lcd.clear()
                self.lcd.write_line(0, "No fob seen")
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

            uid_norm = uid.upper().replace("-", "").replace(" ", "")

            if uid_norm == target_uid:
                elapsed = int(time.time() - start_time)
                logger.info(f"Stage 2 solved in {elapsed}s, UID={uid_norm}")
                self.lcd.clear()
                self.lcd.write_line(0, "Gate unlocked!")
                self.lcd.write_line(1, "+10pts")
                time.sleep(2)
                self._award(elapsed)
                self._show_leak()
                self.lcd.clear()
                self.lcd.write_line(0, "Stage 2 done!")
                self.lcd.write_line(1, "◄=Back to menu")
                while not self.lcd.button_pressed(5):
                    time.sleep(0.1)
                self.lcd.wait_button_release(5)
                return 10
            else:
                wrong_streak += 1
                logger.warning(f"Stage 2 wrong UID: {uid_norm}, streak={wrong_streak}")
                self.lcd.clear()
                self.lcd.write_line(0, "Wrong fob!")
                if wrong_streak >= max_wrong:
                    self.lcd.write_line(1, "Try a different")
                    time.sleep(2)
                    self.lcd.clear()
                    self.lcd.write_line(0, "fob.")
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
