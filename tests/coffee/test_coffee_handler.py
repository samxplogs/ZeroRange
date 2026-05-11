"""Integration-style tests for the Coffee handler state machine.

All hardware is mocked — no LCD, PM3, or HID reader required.
"""

import time
import unittest
from unittest.mock import MagicMock, patch, PropertyMock

from challenges.coffee.value_block import encode


# ---------------------------------------------------------------------------
# Helpers / stubs
# ---------------------------------------------------------------------------

def _make_lcd():
    lcd = MagicMock()
    lcd.button_pressed.return_value = False
    lcd.wait_button_release.return_value = None
    lcd.write_line.return_value = None
    lcd.clear.return_value = None
    return lcd


def _make_db():
    db = MagicMock()
    db.get_challenge_status.return_value = {"completed": False, "points": 10, "best_time": None}
    db.get_total_score.return_value = 0
    db.add_history.return_value = None
    db.mark_completed.return_value = None
    return db


def _make_pm3(simulation_mode=False):
    pm3 = MagicMock()
    pm3.simulation_mode = simulation_mode
    return pm3


def _make_hid(uid_to_return=None):
    hid = MagicMock()
    hid.wait_for_uid.return_value = uid_to_return
    return hid


_CFG = {
    "technician_uid": "0100C0FFEE7E11AB",
    "master_key_b_hex": "B4EEC0FFEE11",
    "credit_threshold_cents": 5000,
    "value_block_addr": 40,
    "max_wrong_reads_stage1": 3,
    "badge_paths": {
        "low": "challenges/coffee/badges/credit_low.nfc",
        "high": "challenges/coffee/badges/credit_high.nfc",
    },
}


# ---------------------------------------------------------------------------
# Stage 1 tests
# ---------------------------------------------------------------------------

class TestStage1(unittest.TestCase):

    def _stage(self, lcd, db, hid):
        from challenges.coffee.stage1_technician import Stage1
        return Stage1(lcd, db, _CFG, hid, sse_emit=lambda _: None)

    def test_correct_uid_awards_10_pts(self):
        lcd = _make_lcd()
        db = _make_db()

        # Simulate: first wait_for_uid returns the correct UID, then back button pressed
        hid = _make_hid("0100C0FFEE7E11AB")
        # After success screen, back button pressed
        press_count = [0]
        def back_on_third_call(btn):
            press_count[0] += 1
            return press_count[0] > 5
        lcd.button_pressed.side_effect = back_on_third_call

        stage = self._stage(lcd, db, hid)

        with patch("time.sleep"):
            pts = stage.run()

        self.assertEqual(pts, 10)
        db.mark_completed.assert_called_once_with(16, unittest.mock.ANY)

    def test_wrong_uid_no_award(self):
        lcd = _make_lcd()
        db = _make_db()

        call_count = [0]
        def uid_then_back(**kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return "DEADBEEF00000000"
            return None  # triggers back-button path

        hid = MagicMock()
        hid.wait_for_uid.side_effect = uid_then_back

        # After wrong UID, press back
        btn_count = [0]
        def back_press(btn):
            btn_count[0] += 1
            return btn_count[0] > 10 and btn == 5
        lcd.button_pressed.side_effect = back_press

        stage = self._stage(lcd, db, hid)

        with patch("time.sleep"):
            pts = stage.run()

        self.assertEqual(pts, 0)
        db.mark_completed.assert_not_called()

    def test_already_complete_shows_leak_no_reawrd(self):
        lcd = _make_lcd()
        db = _make_db()
        db.get_challenge_status.return_value = {"completed": True, "points": 10, "best_time": 30}
        hid = _make_hid()

        # Back button after leak display
        btn_count = [0]
        def back_press(btn):
            btn_count[0] += 1
            return btn == 5 and btn_count[0] > 2
        lcd.button_pressed.side_effect = back_press

        stage = self._stage(lcd, db, hid)
        with patch("time.sleep"):
            pts = stage.run()

        self.assertEqual(pts, 0)  # no re-award
        db.mark_completed.assert_not_called()


# ---------------------------------------------------------------------------
# Stage 3 value-block validation tests
# ---------------------------------------------------------------------------

class TestStage3ValueBlock(unittest.TestCase):

    def _stage(self, lcd, db, pm3):
        from challenges.coffee.stage3_refill import Stage3
        return Stage3(lcd, db, _CFG, pm3, sse_emit=lambda _: None)

    def _run_with_block(self, raw_block: bytes, threshold: int = 5000):
        lcd = _make_lcd()
        db = _make_db()
        pm3 = _make_pm3()
        pm3.read_block.return_value = raw_block

        cfg = dict(_CFG, credit_threshold_cents=threshold)
        from challenges.coffee.stage3_refill import Stage3
        stage = Stage3(lcd, db, cfg, pm3, sse_emit=lambda _: None)

        # SELECT pressed twice then BACK
        sel_count = [0]
        back_count = [0]
        def btn_press(btn):
            if btn == 1:
                sel_count[0] += 1
                return sel_count[0] == 1
            if btn == 5:
                back_count[0] += 1
                return back_count[0] > 10  # eventually exit
            return False
        lcd.button_pressed.side_effect = btn_press

        with patch("time.sleep"):
            pts = stage.run()
        return pts, db, lcd

    def test_valid_high_credit_awards_10(self):
        good_block = encode(5000, 40)
        pts, db, lcd = self._run_with_block(good_block)
        self.assertEqual(pts, 10)
        db.mark_completed.assert_called_once_with(18, unittest.mock.ANY)

    def test_below_threshold_no_award(self):
        low_block = encode(4999, 40)
        pts, db, lcd = self._run_with_block(low_block)
        self.assertEqual(pts, 0)
        db.mark_completed.assert_not_called()
        # Check "too low" was shown
        calls = [str(c) for c in lcd.write_line.call_args_list]
        self.assertTrue(any("low" in c.lower() or "4999" in c or "Value" in c for c in calls))

    def test_bad_inv_v_shows_error(self):
        bad_block = bytearray(encode(5000, 40))
        bad_block[5] ^= 0x01  # corrupt ~V
        pts, db, lcd = self._run_with_block(bytes(bad_block))
        self.assertEqual(pts, 0)
        calls = [str(c) for c in lcd.write_line.call_args_list]
        self.assertTrue(any("Bad" in c or "~V" in c for c in calls))

    def test_bad_addr_shows_error(self):
        bad_block = bytearray(encode(5000, 40))
        bad_block[12] ^= 0x01  # corrupt addr
        pts, db, lcd = self._run_with_block(bytes(bad_block))
        self.assertEqual(pts, 0)
        calls = [str(c) for c in lcd.write_line.call_args_list]
        self.assertTrue(any("addr" in c.lower() or "Bad" in c for c in calls))

    def test_already_complete_no_reawrd(self):
        lcd = _make_lcd()
        db = _make_db()
        db.get_challenge_status.return_value = {"completed": True, "points": 10, "best_time": 60}
        pm3 = _make_pm3()

        from challenges.coffee.stage3_refill import Stage3
        stage = Stage3(lcd, db, _CFG, pm3, sse_emit=lambda _: None)
        with patch("time.sleep"):
            pts = stage.run()

        self.assertEqual(pts, 0)
        pm3.read_block.assert_not_called()


# ---------------------------------------------------------------------------
# Full module scoring
# ---------------------------------------------------------------------------

class TestCoffeeHandlerScore(unittest.TestCase):

    def test_score_reflects_completed_challenges(self):
        lcd = _make_lcd()
        db = _make_db()

        def status(cid):
            return {
                16: {"completed": True, "points": 10, "best_time": 10},
                17: {"completed": True, "points": 10, "best_time": 20},
                18: {"completed": False, "points": 10, "best_time": None},
            }[cid]
        db.get_challenge_status.side_effect = status

        from coffee_handler import CoffeeHandler
        handler = CoffeeHandler(lcd, db)
        self.assertEqual(handler.get_module_score(), 20)

    def test_zero_score_when_nothing_done(self):
        lcd = _make_lcd()
        db = _make_db()
        db.get_challenge_status.return_value = {"completed": False, "points": 10, "best_time": None}

        from coffee_handler import CoffeeHandler
        handler = CoffeeHandler(lcd, db)
        self.assertEqual(handler.get_module_score(), 0)


if __name__ == "__main__":
    unittest.main()
