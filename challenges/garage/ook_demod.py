"""OOK demodulation helpers for ZeroRange Sam Garage module.

Operates on either:
  - Flipper .sub v1 RAW_Data timing lists (preferred — no heavy deps)
  - Raw IQ byte files from HackRF (requires numpy)

The primary path for training is .sub files, since the learner captures
with a Flipper Zero.  IQ support is best-effort.
"""

import logging
from pathlib import Path
from typing import Optional

from challenges.garage.rolling_scheme import (
    FRAME_SIZE,
    ook_timings_to_frame,
    read_sub_file,
    decode_frame,
)

logger = logging.getLogger(__name__)


def demod_sub_file(path, seed: bytes) -> Optional[tuple]:
    """Decode the first valid rolling-code frame in a Flipper .sub file.

    Returns:
        (device_id: bytes, counter: int) on success, or None.
    """
    try:
        timings = read_sub_file(path)
    except OSError as exc:
        logger.warning(f"ook_demod: cannot open {path}: {exc}")
        return None
    if not timings:
        logger.warning(f"ook_demod: no RAW_Data in {path}")
        return None
    frame = ook_timings_to_frame(timings)
    if frame is None:
        logger.warning(f"ook_demod: could not reconstruct frame from {path}")
        return None
    device_id, counter, crc_ok = decode_frame(frame, seed)
    if not crc_ok:
        logger.warning(f"ook_demod: CRC mismatch in {path}")
        return None
    return device_id, counter


def demod_iq_file(path, seed: bytes,
                  sample_rate: int = 2_000_000,
                  freq_hz: int = 433_920_000,
                  symbol_us: int = 250) -> Optional[tuple]:
    """Attempt to decode a rolling-code frame from a raw HackRF IQ file.

    Returns (device_id, counter) or None.  Requires numpy.
    """
    try:
        import numpy as np
    except ImportError:
        logger.error("ook_demod: numpy not available for IQ demodulation")
        return None

    try:
        raw = Path(path).read_bytes()
        # HackRF IQ: interleaved int8 (I, Q)
        iq = np.frombuffer(raw, dtype=np.int8).astype(np.float32)
        if len(iq) < 2:
            return None
        i_samples = iq[0::2]
        q_samples = iq[1::2]
        amplitude = np.sqrt(i_samples ** 2 + q_samples ** 2)

        samples_per_symbol = int(sample_rate * symbol_us / 1_000_000)
        threshold = amplitude.max() * 0.3

        # Downsample to one bit per symbol
        bits = []
        step = samples_per_symbol
        for start in range(0, len(amplitude) - step, step):
            chunk = amplitude[start:start + step]
            bits.append(1 if chunk.mean() > threshold else 0)

        # Scan for preamble-like burst then decode
        frame_bits = FRAME_SIZE * 8
        for start in range(len(bits) - frame_bits):
            candidate = bits[start:start + frame_bits]
            frame = bytearray()
            for byte_idx in range(FRAME_SIZE):
                byte_val = 0
                for bp in range(8):
                    byte_val = (byte_val << 1) | candidate[byte_idx * 8 + bp]
                frame.append(byte_val)
            frame_bytes = bytes(frame)
            device_id, counter, crc_ok = decode_frame(frame_bytes, seed)
            if crc_ok:
                logger.info(f"ook_demod IQ: found counter={counter}")
                return device_id, counter

        logger.warning("ook_demod IQ: no valid frame found")
        return None

    except Exception as exc:
        logger.error(f"ook_demod IQ error: {exc}")
        return None
