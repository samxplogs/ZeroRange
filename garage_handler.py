#!/usr/bin/env python3
"""
Garage Handler for ZeroRange — Sam Garage training module.

DISCLAIMER: "Sam Garage" is an entirely fictional facility. Any resemblance to
real garage-remote products, access-control vendors, or rolling-code algorithms
(KeeLoq, AES rolling, etc.) is purely coincidental. The toy rolling scheme used
here is deliberately weaker than any real product. This module exists for
hands-on security training in a controlled environment only.

Three-stage chained scenario (30 pts):
  Stage 1 (10 pts) — Rolling-code teardown via HackRF One
  Stage 2 (10 pts) — Pedestrian gate via iButton HID reader
  Stage 3 (10 pts) — Tech room via Proxmark3 MIFARE Classic
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

from challenges.garage.stage1_rolling import Stage1
from challenges.garage.stage2_pedestrian import Stage2
from challenges.garage.stage3_tech_room import Stage3

logger = logging.getLogger(__name__)

_DISCLAIMER_LINES = [
    "Sam Garage",
    "is FICTIONAL.",
    "Training env only.",
    "No real targets.",
]

_MODULE_MAX = 30


class _HIDReaderAdapter:
    """Adapts IButtonUSBReader to the interface expected by Stage2."""

    def __init__(self, lcd, device_path: str):
        self.lcd = lcd
        self._reader = None
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
    return "/dev/input/event0"


def _load_config() -> dict:
    try:
        cfg_path = Path(__file__).parent / "config.json"
        with open(cfg_path) as f:
            full = json.load(f)
        return full.get("garage", {})
    except Exception as exc:
        logger.warning(f"Failed to load config.json: {exc}")
        return {}


class GarageHandler:
    """Handles the Sam Garage training scenario."""

    def __init__(self, lcd, db, proxmark=None, hackrf=None, sse_emit=None):
        self.lcd = lcd
        self.db = db
        self.pm3 = proxmark
        self.hackrf = hackrf
        self.sse = sse_emit or (lambda _: None)
        self.cfg = _load_config()
        self._hid: Optional[_HIDReaderAdapter] = None

    # ------------------------------------------------------------------ score

    def get_module_score(self) -> int:
        total = 0
        for cid in (19, 20, 21):
            status = self.db.get_challenge_status(cid)
            if status and status["completed"]:
                total += status["points"]
        return total

    # ------------------------------------------------------------------ UI helpers

    def _show_disclaimer(self) -> None:
        for line in _DISCLAIMER_LINES:
            self.lcd.clear()
            self.lcd.write_line(0, "Sam Garage")
            self.lcd.write_line(1, line[:16])
            time.sleep(1.5)

    def _stage_menu(self) -> int:
        """Show the stage sub-menu.

        Returns 1-3 to launch that stage, 0 to go back.
        """
        selected = 0
        items = [
            ("Stage1:RollJam", 19),
            ("Stage2:Gate",    20),
            ("Stage3:TechRm",  21),
        ]

        while True:
            score = self.get_module_score()
            label, cid = items[selected]
            status = self.db.get_challenge_status(cid)
            done = status and status["completed"]
            marker = "\x07" if done else " "

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
                return selected + 1
            elif self.lcd.button_pressed(5):
                self.lcd.wait_button_release(5)
                return 0

            time.sleep(0.1)

    # ------------------------------------------------------------------ public

    def run(self) -> int:
        logger.info("Garage module started")
        self._show_disclaimer()

        hid_path = _find_hid_device()
        self._hid = _HIDReaderAdapter(self.lcd, hid_path)

        try:
            earned = 0
            while True:
                choice = self._stage_menu()
                if choice == 0:
                    break
                pts = self._run_stage(choice)
                earned += pts
        finally:
            if self._hid:
                self._hid.close()
                self._hid = None

        logger.info(f"Garage module exited, earned {earned} pts this session")
        return earned

    def _run_stage(self, stage_num: int) -> int:
        if stage_num == 1:
            handler = Stage1(self.lcd, self.db, self.cfg, self.hackrf, self.sse)
        elif stage_num == 2:
            handler = Stage2(self.lcd, self.db, self.cfg, self._hid, self.sse)
        elif stage_num == 3:
            handler = Stage3(self.lcd, self.db, self.cfg, self.pm3, self.sse)
        else:
            return 0

        try:
            return handler.run()
        except Exception as exc:
            logger.error(f"Garage stage {stage_num} crashed: {exc}", exc_info=True)
            self.lcd.clear()
            self.lcd.write_line(0, f"Stage {stage_num} error!")
            self.lcd.write_line(1, "Check logs ◄")
            time.sleep(3)
            return 0

    def close(self) -> None:
        if self._hid:
            self._hid.close()
            self._hid = None
