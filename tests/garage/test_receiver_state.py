"""Tests for challenges.garage.receiver_state."""
import unittest

from challenges.garage.rolling_scheme import encode_frame
from challenges.garage.receiver_state import ReceiverState

_DEV = bytes.fromhex("DEADBEEF")
_SEED = bytes.fromhex("C0FFEE11")
_INIT = 99  # last_accepted starts here; first valid counter is 100


def _mk_receiver(on_event=None) -> ReceiverState:
    return ReceiverState(
        device_id=_DEV,
        seed=_SEED,
        initial_counter=_INIT,
        window=16,
        on_event=on_event,
    )


def _frame(ctr: int) -> bytes:
    return encode_frame(_DEV, ctr, _SEED)


class TestReceiverBasic(unittest.TestCase):
    def test_accepts_first_valid_counter(self):
        rx = _mk_receiver()
        ok, reason = rx.submit_frame(_frame(100))
        self.assertTrue(ok)
        self.assertEqual(reason, "ok")
        self.assertEqual(rx.last_accepted, 100)

    def test_rejects_stale_replay(self):
        rx = _mk_receiver()
        rx.submit_frame(_frame(100))
        ok, reason = rx.submit_frame(_frame(100))
        self.assertFalse(ok)
        self.assertEqual(reason, "stale")

    def test_rejects_counter_below_last(self):
        rx = _mk_receiver()
        rx.submit_frame(_frame(105))
        ok, reason = rx.submit_frame(_frame(100))
        self.assertFalse(ok)
        self.assertEqual(reason, "stale")

    def test_accepts_within_window(self):
        rx = _mk_receiver()
        ok, reason = rx.submit_frame(_frame(115))  # 99 + 16 = 115
        self.assertTrue(ok)

    def test_rejects_out_of_window(self):
        rx = _mk_receiver()
        ok, reason = rx.submit_frame(_frame(116))  # 99 + 16 + 1
        self.assertFalse(ok)
        self.assertEqual(reason, "out_of_window")

    def test_sequential_advance(self):
        rx = _mk_receiver()
        for ctr in range(100, 110):
            ok, _ = rx.submit_frame(_frame(ctr))
            self.assertTrue(ok, f"counter {ctr} should be accepted")
        self.assertEqual(rx.last_accepted, 109)


class TestReceiverJamming(unittest.TestCase):
    def test_jammed_drops_valid_frame(self):
        rx = _mk_receiver()
        rx.set_jammed(True)
        ok, reason = rx.submit_frame(_frame(100))
        self.assertFalse(ok)
        self.assertEqual(reason, "jammed")
        self.assertEqual(rx.last_accepted, _INIT)  # not advanced

    def test_rolljam_sequence(self):
        rx = _mk_receiver()
        # Step 1: receiver sees press 100, advances
        rx.submit_frame(_frame(100))
        self.assertEqual(rx.last_accepted, 100)

        # Step 2: jam — presses 101, 102 transmitted but not accepted
        rx.set_jammed(True)
        ok1, _ = rx.submit_frame(_frame(101))
        ok2, _ = rx.submit_frame(_frame(102))
        self.assertFalse(ok1)
        self.assertFalse(ok2)
        self.assertEqual(rx.last_accepted, 100)

        # Step 3: lift jam and replay 101
        rx.set_jammed(False)
        ok3, reason3 = rx.submit_frame(_frame(101))
        self.assertTrue(ok3, f"Replay after jam should succeed, got: {reason3}")
        self.assertEqual(rx.last_accepted, 101)


class TestReceiverBadCrc(unittest.TestCase):
    def test_bad_crc_rejected(self):
        rx = _mk_receiver()
        frame = bytearray(_frame(100))
        frame[8] ^= 0xFF
        ok, reason = rx.submit_frame(bytes(frame))
        self.assertFalse(ok)
        self.assertEqual(reason, "bad_crc")


class TestReceiverWrongDevice(unittest.TestCase):
    def test_wrong_device_id_rejected(self):
        rx = _mk_receiver()
        frame = encode_frame(bytes.fromhex("CAFEBABE"), 100, _SEED)
        ok, reason = rx.submit_frame(frame)
        self.assertFalse(ok)
        self.assertEqual(reason, "wrong_id")


class TestReceiverEvents(unittest.TestCase):
    def test_events_emitted_on_accept(self):
        events = []
        rx = _mk_receiver(on_event=events.append)
        rx.submit_frame(_frame(100))
        event_names = [e["event"] for e in events]
        self.assertIn("replay_received", event_names)
        self.assertIn("window_slid", event_names)
        accepted_ev = next(e for e in events if e["event"] == "replay_received")
        self.assertTrue(accepted_ev["accepted"])

    def test_events_emitted_on_reject(self):
        events = []
        rx = _mk_receiver(on_event=events.append)
        rx.submit_frame(_frame(100))
        events.clear()
        rx.submit_frame(_frame(100))  # stale
        self.assertTrue(any(
            e["event"] == "replay_received" and not e["accepted"]
            for e in events
        ))

    def test_jam_event_emitted(self):
        events = []
        rx = _mk_receiver(on_event=events.append)
        rx.set_jammed(True)
        self.assertTrue(any(e["event"] == "jam_started" for e in events))
