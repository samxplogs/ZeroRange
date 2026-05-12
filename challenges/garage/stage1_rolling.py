"""Stage 1 — Rolling-Code Teardown (10 pts = 3 + 7).

Sub-stage 1a (3 pts):
  ZeroRange TXes press N.  Receiver internally advances to N+1.
  ZeroRange submits a replay of press N → receiver rejects it.
  LCD shows "Replay rejected".  Learner presses SELECT to confirm → +3 pts.

Sub-stage 1b (7 pts, RollJam demo):
  Receiver is set to "jammed" (won't advance).
  ZeroRange TXes press N+1, then N+2 (learner can capture both with Flipper).
  Jamming lifted.  ZeroRange submits press N+1 → receiver accepts → "Gate OPEN" → +7 pts.
"""

import time
import logging

from challenges.garage.rolling_scheme import encode_frame
from challenges.garage.receiver_state import ReceiverState

logger = logging.getLogger(__name__)


class Stage1:
    _CHALLENGE_ID_1A = 19
    _CHALLENGE_ID_1B = None  # 1a and 1b share challenge 19; sub-pts handled internally
    _CHALLENGE_ID = 19

    def __init__(self, lcd, db, config: dict, hackrf, sse_emit=None):
        self.lcd = lcd
        self.db = db
        self.cfg = config
        self.hackrf = hackrf
        self.sse = sse_emit or (lambda _: None)

        rolling = config.get("rolling", {})
        self._device_id = bytes.fromhex(
            rolling.get("device_id_hex", "DEADBEEF").replace(" ", "")
        )
        self._seed = bytes.fromhex(
            rolling.get("seed_hex", "C0FFEE11").replace(" ", "")
        )
        self._freq = rolling.get("freq_hz", 433_920_000)
        self._press_gap_ms = rolling.get("press_gap_ms", 1500)
        self._window = rolling.get("counter_window", 16)
        self._initial_counter = rolling.get("initial_counter", 100)

    # ------------------------------------------------------------------ helpers

    def _challenge_done(self) -> bool:
        status = self.db.get_challenge_status(self._CHALLENGE_ID)
        return status is not None and status["completed"]

    def _award(self, pts: int, elapsed: int) -> None:
        self.db.add_history(self._CHALLENGE_ID, True, elapsed)
        self.db.mark_completed(self._CHALLENGE_ID, elapsed)
        self.sse({"stage": 1, "status": "success", "points": pts})
        self.sse({"event": "stage_complete", "stage": 1, "points": pts})

    def _tx_frame(self, counter: int, label: str) -> bool:
        """TX one OOK frame via HackRF (or simulate). Returns success."""
        frame = encode_frame(self._device_id, counter, self._seed)
        self.lcd.clear()
        self.lcd.write_line(0, f"Emitting {label}")
        self.lcd.write_line(1, f"ctr={counter}")
        self.sse({"event": "press_emitted", "counter": counter})

        if self.hackrf is None or self.hackrf.simulation_mode:
            logger.info(f"[SIM] TX press counter={counter}")
            time.sleep(0.5)
            return True

        # Write frame to temp .raw for hackrf_transfer TX
        import tempfile, struct, os
        from challenges.garage.rolling_scheme import frame_to_ook_timings
        timings = frame_to_ook_timings(frame)
        # Convert µs timings to IQ bytes (crude OOK: ON=127+127j, OFF=0)
        sr = 2_000_000
        iq_bytes = bytearray()
        for t in timings:
            n_samples = abs(t) * sr // 1_000_000
            if t > 0:
                iq_bytes += bytes([127, 127]) * max(1, n_samples)
            else:
                iq_bytes += bytes([0, 0]) * max(1, n_samples)

        with tempfile.NamedTemporaryFile(suffix=".raw", delete=False) as tf:
            tf.write(iq_bytes)
            tmp_path = tf.name
        try:
            ok = self.hackrf.replay_signal(tmp_path, frequency=self._freq)
        finally:
            os.unlink(tmp_path)
        return ok

    def _await_select_or_back(self, prompt0: str, prompt1: str) -> bool:
        """Show a two-line prompt; return True on SELECT, False on BACK."""
        self.lcd.clear()
        self.lcd.write_line(0, prompt0)
        self.lcd.write_line(1, prompt1)
        while True:
            if self.lcd.button_pressed(1):
                self.lcd.wait_button_release(1)
                return True
            if self.lcd.button_pressed(5):
                self.lcd.wait_button_release(5)
                return False
            time.sleep(0.1)

    # ------------------------------------------------------------------ sub-stages

    def _run_1a(self, receiver: ReceiverState, start_time: float) -> int:
        """Sub-stage 1a: fixed-code replay demo. Returns 0 or 3."""
        press_n = self._initial_counter

        # TX press N — receiver internally NOT advancing (we control it)
        self.lcd.clear()
        self.lcd.write_line(0, "Stage 1a: Replay")
        self.lcd.write_line(1, "Watching...")
        time.sleep(1)

        ok = self._tx_frame(press_n, "press N")
        if not ok:
            self.lcd.clear()
            self.lcd.write_line(0, "HackRF TX fail!")
            self.lcd.write_line(1, "SEL=Skip ◄=Back")
            if not self._await_select_or_back("HackRF TX fail!", "SEL=Skip ◄=Back"):
                return 0
        time.sleep(self._press_gap_ms / 1000)

        # The receiver saw press N and advanced
        accepted, reason = receiver.submit_frame(
            encode_frame(self._device_id, press_n, self._seed)
        )
        assert accepted, "First press should be accepted by fresh receiver"

        # Now replay press N — it is stale
        self.lcd.clear()
        self.lcd.write_line(0, "Replaying press N")
        self.lcd.write_line(1, "Will it work?...")
        time.sleep(1)
        self._tx_frame(press_n, "REPLAY N")
        time.sleep(0.5)

        accepted2, reason2 = receiver.submit_frame(
            encode_frame(self._device_id, press_n, self._seed)
        )
        # Should be rejected (stale)
        self.lcd.clear()
        if not accepted2:
            self.lcd.write_line(0, "Replay rejected")
            self.lcd.write_line(1, "Try harder ◄=Bk")
        else:
            self.lcd.write_line(0, "Accepted! (bug?)")
            self.lcd.write_line(1, "SEL=Continue")

        time.sleep(2)

        confirmed = self._await_select_or_back(
            "Got REJECTED?",
            "SEL=Yes ◄=Back"
        )
        if not confirmed:
            return 0

        pts = 3
        elapsed = int(time.time() - start_time)
        self.db.add_history(self._CHALLENGE_ID, True, elapsed)
        self.sse({"event": "stage_complete", "stage": "1a", "points": pts})

        self.lcd.clear()
        self.lcd.write_line(0, "Rolling code!")
        self.lcd.write_line(1, f"+{pts}pts — next: RJ")
        time.sleep(2)
        return pts

    def _run_1b(self, receiver: ReceiverState, start_time: float) -> int:
        """Sub-stage 1b: RollJam demo. Returns 0 or 7."""
        press_n1 = self._initial_counter + 1
        press_n2 = self._initial_counter + 2

        # Explain RollJam
        for msg in ["RollJam principle:", "Jam+capture x2,", "replay 1st press"]:
            self.lcd.clear()
            self.lcd.write_line(0, "1b: RollJam")
            self.lcd.write_line(1, msg[:16])
            time.sleep(1.5)

        # Enable jamming on the receiver
        receiver.set_jammed(True)
        self.lcd.clear()
        self.lcd.write_line(0, "JAMMING active")
        self.lcd.write_line(1, "Capturing presses")
        time.sleep(1)

        # TX press N+1 (receiver jammed, won't accept)
        self._tx_frame(press_n1, "press N+1")
        self.sse({"event": "frame_held", "counter": press_n1, "tray_size": 1})
        time.sleep(self._press_gap_ms / 1000)

        # TX press N+2 (still jammed)
        self._tx_frame(press_n2, "press N+2")
        self.sse({"event": "frame_held", "counter": press_n2, "tray_size": 2})
        time.sleep(self._press_gap_ms / 1000)

        # Lift jamming — receiver still at initial_counter (advanced by 1a)
        receiver.set_jammed(False)
        self.lcd.clear()
        self.lcd.write_line(0, "Jam lifted!")
        self.lcd.write_line(1, "Replaying N+1...")
        time.sleep(1)

        # Replay press N+1 — should be accepted
        self._tx_frame(press_n1, "REPLAY N+1")
        time.sleep(0.5)
        accepted, reason = receiver.submit_frame(
            encode_frame(self._device_id, press_n1, self._seed)
        )

        if accepted:
            self.lcd.clear()
            self.lcd.write_line(0, "Gate OPEN! +7pts")
            self.lcd.write_line(1, "RollJam success!")
            time.sleep(3)
            elapsed = int(time.time() - start_time)
            self._award(10, elapsed)  # total 10 pts for stage 1 (3+7)
            return 7
        else:
            self.lcd.clear()
            self.lcd.write_line(0, "Replay failed!")
            self.lcd.write_line(1, f"Reason: {reason[:10]}")
            time.sleep(3)
            return 0

    # ------------------------------------------------------------------ public

    def run(self) -> int:
        logger.info("Garage Stage 1: Rolling-code teardown starting")

        if self._challenge_done():
            self.lcd.clear()
            self.lcd.write_line(0, "Stage 1 done!")
            self.lcd.write_line(1, "Already solved ◄")
            while not self.lcd.button_pressed(5):
                time.sleep(0.1)
            self.lcd.wait_button_release(5)
            return 0

        # Splash
        for line in ["RollJam demo", "Garage door", "433 MHz OOK"]:
            self.lcd.clear()
            self.lcd.write_line(0, "Garage Stage 1")
            self.lcd.write_line(1, line)
            time.sleep(1.2)

        # HackRF check
        if self.hackrf is None:
            self.lcd.clear()
            self.lcd.write_line(0, "HackRF not found")
            self.lcd.write_line(1, "Connect HackRF ◄")
            while not self.lcd.button_pressed(5):
                time.sleep(0.1)
            self.lcd.wait_button_release(5)
            return 0

        start_time = time.time()
        receiver = ReceiverState(
            device_id=self._device_id,
            seed=self._seed,
            initial_counter=self._initial_counter - 1,
            window=self._window,
            on_event=self.sse,
        )

        total_pts = 0

        pts_1a = self._run_1a(receiver, start_time)
        if pts_1a == 0:
            return 0
        total_pts += pts_1a

        # Brief pause between sub-stages
        if not self._await_select_or_back("Ready for 1b?", "SEL=Go ◄=Skip"):
            return total_pts

        pts_1b = self._run_1b(receiver, start_time)
        total_pts += pts_1b

        self.lcd.clear()
        self.lcd.write_line(0, f"Stage 1: +{total_pts}pts")
        self.lcd.write_line(1, "◄=Back to menu")
        while not self.lcd.button_pressed(5):
            time.sleep(0.1)
        self.lcd.wait_button_release(5)
        return total_pts
