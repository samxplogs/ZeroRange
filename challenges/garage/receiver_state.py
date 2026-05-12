"""Synthetic rolling-code receiver state machine for ZeroRange Sam Garage module.

Simulates the garage-door controller that accepts rolling-code frames.
Runs entirely in Python — HackRF only TXes; the receiver logic lives here.

Acceptance rule:
    Accept frame iff:
      1. CRC is valid
      2. device_id matches
      3. decoded counter > last_accepted
      4. decoded counter <= last_accepted + window
"""

import logging
from typing import Optional, Callable

from challenges.garage.rolling_scheme import decode_frame

logger = logging.getLogger(__name__)


class ReceiverState:
    """Rolling-code receiver state machine.

    Attributes:
        last_accepted: Counter value of the last accepted frame.
        window:        How many future counter values the receiver tolerates.
        jammed:        When True, valid frames are silently dropped (not accepted).
    """

    def __init__(
        self,
        device_id: bytes,
        seed: bytes,
        initial_counter: int = 99,
        window: int = 16,
        on_event: Optional[Callable[[dict], None]] = None,
    ):
        """
        Args:
            device_id:       4-byte ID that frames must carry.
            seed:            4-byte XOR seed for decoding.
            initial_counter: last_accepted starts here (one below first press).
            window:          Max lookahead; accept counter in (last, last+window].
            on_event:        Optional callback(dict) for state-change notifications.
        """
        self.device_id = device_id
        self.seed = seed
        self.last_accepted = initial_counter
        self.window = window
        self.jammed = False
        self._emit = on_event or (lambda _: None)

    # ------------------------------------------------------------------ public

    def submit_frame(self, frame: bytes) -> tuple:
        """Attempt to accept a 10-byte frame.

        Returns:
            (accepted: bool, reason: str)
              reason is "ok" | "stale" | "out_of_window" | "bad_crc" | "wrong_id" | "jammed"
        """
        try:
            rx_id, counter, crc_ok = decode_frame(frame, self.seed)
        except Exception as exc:
            logger.warning(f"Receiver: decode error: {exc}")
            return False, "bad_crc"

        if not crc_ok:
            logger.debug(f"Receiver: bad CRC, counter={counter}")
            self._emit({"event": "replay_received", "counter": counter,
                        "accepted": False, "reason": "bad_crc"})
            return False, "bad_crc"

        if rx_id != self.device_id:
            logger.debug(f"Receiver: wrong device ID")
            self._emit({"event": "replay_received", "counter": counter,
                        "accepted": False, "reason": "wrong_id"})
            return False, "wrong_id"

        if self.jammed:
            logger.debug(f"Receiver: jammed, dropping counter={counter}")
            self._emit({"event": "replay_received", "counter": counter,
                        "accepted": False, "reason": "jammed"})
            return False, "jammed"

        if counter <= self.last_accepted:
            logger.debug(f"Receiver: stale counter={counter} (last={self.last_accepted})")
            self._emit({"event": "replay_received", "counter": counter,
                        "accepted": False, "reason": "stale"})
            return False, "stale"

        if counter > self.last_accepted + self.window:
            logger.debug(
                f"Receiver: out-of-window counter={counter} "
                f"(last={self.last_accepted}, window={self.window})"
            )
            self._emit({"event": "replay_received", "counter": counter,
                        "accepted": False, "reason": "out_of_window"})
            return False, "out_of_window"

        # Accept
        prev = self.last_accepted
        self.last_accepted = counter
        logger.info(f"Receiver: accepted counter={counter} (prev={prev})")
        self._emit({"event": "replay_received", "counter": counter,
                    "accepted": True, "reason": "ok"})
        self._emit({"event": "window_slid",
                    "last_accepted": self.last_accepted,
                    "window": self.window})
        return True, "ok"

    def set_jammed(self, jammed: bool) -> None:
        """Toggle the simulated jamming state."""
        self.jammed = jammed
        if jammed:
            logger.info("Receiver: jamming enabled — valid frames will be dropped")
            self._emit({"event": "jam_started"})
        else:
            logger.info("Receiver: jamming disabled")

    def get_state(self) -> dict:
        return {
            "last_accepted": self.last_accepted,
            "window": self.window,
            "jammed": self.jammed,
        }
