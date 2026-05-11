#!/usr/bin/env python3
"""
Coffee Handler for ZeroRange — Sam BrewMaster Pro training module.

DISCLAIMER: Sam BrewMaster Pro is an entirely fictional brand created for
ZeroRange. Any resemblance to real coffee/vending badge systems,
manufacturers, or deployments is purely coincidental. This module exists
for hands-on security training in a controlled environment only.

Three-stage chained scenario:
  Stage 1 (10 pts) — iButton technician token
  Stage 2 (10 pts) — Crack & dump the employee badge via PM3 emulation
  Stage 3 (10 pts) — Top up the balance (value-block forgery)
"""

import glob
import json
import logging
import time
from pathlib import Path
from typing import Optional

try:
    from ibutton_usb_reader import IButtonUSBReader
except ImportError:
    IButtonUSBReader = None  # type: ignore[assignment,misc]

from challenges.coffee.stage1_technician import Stage1
from challenges.coffee.stage2_dump import Stage2
from challenges.coffee.stage3_refill import Stage3
from challenges.coffee.prep_badges import PrepBadges

logger = logging.getLogger(__name__)

_DISCLAIMER_LINES = [
    "Sam BrewMaster Pro",
    "is FICTIONAL.",
    "Training env only.",
    "No real systems.",
]

_MODULE_MAX = 30


class _HIDReaderAdapter:
    """Adapts IButtonUSBReader to the interface expected by Stage1."""

    def __init__(self, lcd, device_path: str):
        self.lcd = lcd
        self._reader: Optional[IButtonUSBReader] = None
        self._last_uid: Optional[str] = None
        self._device_path = device_path

        try:
            if IButtonUSBReader is None:
                raise RuntimeError("evdev / IButtonUSBReader not available")
            self._reader = IButtonUSBReader(device_path)
            self._reader.start(callback=self._on_uid)
            logger.info(f"HID reader opened on {device_path}")
        except Exception as exc:
            logger.warning(f"HID reader not available on {device_path}: {exc}")

    def _on_uid(self, uid: str) -> None:
        self._last_uid = uid

    def wait_for_uid(self, timeout: int = 60) -> Optional[str]:
        """Block until a UID arrives, timeout, or BACK button pressed."""
        if self._reader is None:
            self.lcd.clear()
            self.lcd.write_line(0, "iBtn reader")
            self.lcd.write_line(1, "not detected!")
            time.sleep(3)
            return None

        self._last_uid = None
        start = time.time()

        while True:
            elapsed = int(time.time() - start)
            remaining = timeout - elapsed
            self.lcd.write_line(1, f"◄=Back [{remaining}s]")

            if self._last_uid:
                uid = self._last_uid
                self._last_uid = None
                return uid

            if self.lcd.button_pressed(5):
                return None

            if elapsed >= timeout:
                return None

            time.sleep(0.2)

    def close(self) -> None:
        if self._reader:
            self._reader.close()
            self._reader = None


def _find_hid_device() -> str:
    """Return the first /dev/input/event* that looks like an iButton USB reader."""
    for path in sorted(glob.glob("/dev/input/event*")):
        try:
            from evdev import InputDevice
            dev = InputDevice(path)
            name = dev.name.lower()
            dev.close()
            if any(kw in name for kw in ("ibutton", "hid", "keyboard", "usb")):
                return path
        except Exception:
            continue
    return "/dev/input/event0"  # fallback


def _load_config() -> dict:
    try:
        cfg_path = Path(__file__).parent / "config.json"
        with open(cfg_path) as f:
            full = json.load(f)
        return full.get("coffee", {})
    except Exception as exc:
        logger.warning(f"Failed to load config.json: {exc}")
        return {}


class CoffeeHandler:
    """Handles the Coffee Machine training scenario."""

    def __init__(self, lcd, db, proxmark=None, sse_emit=None):
        self.lcd = lcd
        self.db = db
        self.pm3 = proxmark
        self.sse = sse_emit or (lambda _: None)
        self.cfg = _load_config()
        self._hid: Optional[_HIDReaderAdapter] = None

    # ------------------------------------------------------------------ score

    def get_module_score(self) -> int:
        total = 0
        for cid in (16, 17, 18):
            status = self.db.get_challenge_status(cid)
            if status and status["completed"]:
                total += status["points"]
        return total

    # ------------------------------------------------------------------ UI helpers

    def _show_disclaimer(self) -> None:
        for line in _DISCLAIMER_LINES:
            self.lcd.clear()
            self.lcd.write_line(0, "Sam BrewMaster")
            self.lcd.write_line(1, line[:16])
            time.sleep(1.5)

    def _stage_menu(self) -> int:
        """Show the stage + prep sub-menu.

        Returns:
            1-3  — launch that stage
            4    — launch prep badges
            0    — back to main menu
        """
        selected = 0
        # items: (label, challenge_id_or_None)
        items = [
            ("Stage1:iButton", 16),
            ("Stage2:Crack",   17),
            ("Stage3:Refill",  18),
            ("Prep Badges",    None),
        ]

        while True:
            score = self.get_module_score()
            label, cid = items[selected]
            if cid is not None:
                status = self.db.get_challenge_status(cid)
                done = status and status["completed"]
                marker = "\x07" if done else " "   # checkmark glyph or space
            else:
                marker = " "

            self.lcd.clear()
            self.lcd.write_line(0, f">{label[:14]}{marker}")
            self.lcd.write_line(1, f"U/D SEL=Go {score}/30")

            if self.lcd.button_pressed(2):
                self.lcd.wait_button_release(2)
                selected = (selected - 1) % len(items)
            elif self.lcd.button_pressed(3):
                self.lcd.wait_button_release(3)
                selected = (selected + 1) % len(items)
            elif self.lcd.button_pressed(1):
                self.lcd.wait_button_release(1)
                return selected + 1   # 1=Stage1, 2=Stage2, 3=Stage3, 4=Prep
            elif self.lcd.button_pressed(5):
                self.lcd.wait_button_release(5)
                return 0

            time.sleep(0.1)

    # ------------------------------------------------------------------ public

    def run(self) -> int:
        """Entry point called by zerorange.py. Returns total points earned this session."""
        logger.info("Coffee module started")
        self._show_disclaimer()

        hid_path = _find_hid_device()
        self._hid = _HIDReaderAdapter(self.lcd, hid_path)

        try:
            earned_this_session = 0

            while True:
                choice = self._stage_menu()
                if choice == 0:
                    break

                pts = self._run_stage(choice)
                earned_this_session += pts

        finally:
            if self._hid:
                self._hid.close()
                self._hid = None

        logger.info(f"Coffee module exited, earned {earned_this_session} pts this session")
        return earned_this_session

    def _run_stage(self, stage_num: int) -> int:
        if stage_num == 1:
            handler = Stage1(self.lcd, self.db, self.cfg, self._hid, self.sse)
        elif stage_num == 2:
            handler = Stage2(self.lcd, self.db, self.cfg, self.pm3, self.sse)
        elif stage_num == 3:
            handler = Stage3(self.lcd, self.db, self.cfg, self.pm3, self.sse)
        elif stage_num == 4:
            # Prep Badges — no scoring, returns 0 always
            prep = PrepBadges(self.lcd, self.cfg, self.pm3)
            try:
                prep.run()
            except Exception as exc:
                logger.error(f"Prep Badges crashed: {exc}", exc_info=True)
                self.lcd.clear()
                self.lcd.write_line(0, "Prep error!")
                self.lcd.write_line(1, "Check logs ◄")
                time.sleep(3)
            return 0
        else:
            return 0

        try:
            return handler.run()
        except Exception as exc:
            logger.error(f"Coffee stage {stage_num} crashed: {exc}", exc_info=True)
            self.lcd.clear()
            self.lcd.write_line(0, f"Stage {stage_num} error!")
            self.lcd.write_line(1, "Check logs ◄")
            time.sleep(3)
            return 0

    def close(self) -> None:
        if self._hid:
            self._hid.close()
            self._hid = None
