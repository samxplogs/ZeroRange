"""Toy rolling-code scheme for ZeroRange Sam Garage module.

DISCLAIMER: This is a deliberately weak, fictional scheme for training purposes
only. It bears NO resemblance to KeeLoq, AES rolling, or any real product.
Seed and device ID are visible in config.json — a learner can derive the key
by capturing a handful of frames.

Frame layout (10 bytes, OOK 433.92 MHz, 250 µs symbol, MSB first):
    [ID3 ID2 ID1 ID0] [CTR3 CTR2 CTR1 CTR0] [CRC1 CRC0]

  ID      = 4-byte device ID (fixed per remote, from config)
  CTR_enc = counter XOR seed  (encoded[i] = counter_bytes[i] XOR seed[i])
  CRC     = CRC-16/CCITT-FALSE over (ID + CTR_enc)
"""

import struct


# CRC-16/CCITT-FALSE (poly=0x1021, init=0xFFFF, no reflection, no xorout)
def _crc16(data: bytes) -> int:
    crc = 0xFFFF
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return crc


FRAME_SIZE = 10  # bytes


def encode_frame(device_id: bytes, counter: int, seed: bytes) -> bytes:
    """Build one 10-byte rolling-code frame.

    Args:
        device_id: 4-byte device identifier.
        counter:   32-bit unsigned counter value.
        seed:      4-byte XOR seed (the "secret").

    Returns:
        10-byte frame ready for OOK transmission.
    """
    if len(device_id) != 4:
        raise ValueError("device_id must be 4 bytes")
    if len(seed) != 4:
        raise ValueError("seed must be 4 bytes")
    if not (0 <= counter <= 0xFFFFFFFF):
        raise ValueError("counter must be 32-bit unsigned")

    ctr_bytes = struct.pack(">I", counter)
    ctr_encoded = bytes(c ^ s for c, s in zip(ctr_bytes, seed))
    payload = device_id + ctr_encoded
    crc = _crc16(payload)
    return payload + struct.pack(">H", crc)


def decode_frame(frame: bytes, seed: bytes) -> tuple:
    """Decode a 10-byte frame.

    Returns:
        (device_id: bytes, counter: int, crc_valid: bool)
    """
    if len(frame) != FRAME_SIZE:
        raise ValueError(f"frame must be {FRAME_SIZE} bytes, got {len(frame)}")
    if len(seed) != 4:
        raise ValueError("seed must be 4 bytes")

    device_id = frame[0:4]
    ctr_encoded = frame[4:8]
    crc_received = struct.unpack(">H", frame[8:10])[0]

    counter_bytes = bytes(c ^ s for c, s in zip(ctr_encoded, seed))
    counter = struct.unpack(">I", counter_bytes)[0]

    crc_computed = _crc16(frame[0:8])
    return device_id, counter, (crc_received == crc_computed)


# ---------------------------------------------------------------------------
# Flipper .sub v1 helpers
# ---------------------------------------------------------------------------

_PREAMBLE_ON = 3400    # µs
_PREAMBLE_OFF = -3400
_BIT1_ON = 500
_BIT1_OFF = -250
_BIT0_ON = 250
_BIT0_OFF = -500
_END_GAP = -10000


def frame_to_ook_timings(frame: bytes) -> list:
    """Convert a frame to a list of OOK on/off µs timings (Flipper RAW format).

    Positive = carrier on, negative = carrier off.
    """
    timings = [_PREAMBLE_ON, _PREAMBLE_OFF]
    for byte in frame:
        for bit_pos in range(7, -1, -1):  # MSB first
            if (byte >> bit_pos) & 1:
                timings += [_BIT1_ON, _BIT1_OFF]
            else:
                timings += [_BIT0_ON, _BIT0_OFF]
    timings.append(_END_GAP)
    return timings


def ook_timings_to_frame(timings: list, tolerance: float = 0.4) -> bytes | None:
    """Attempt to decode a list of OOK timings back to a 10-byte frame.

    Returns the frame bytes, or None if decoding fails.
    tolerance: fraction of symbol period allowed as jitter.
    """
    sym = 250  # µs base symbol
    tol = int(sym * tolerance)

    bits = []
    i = 0
    # Skip preamble — look for the first bit-like pulse
    # Preamble is ~3400µs; skip any run > 1000µs
    while i < len(timings) - 1:
        on = timings[i]
        if not isinstance(on, int) or on < 0:
            i += 1
            continue
        if on > 1000:
            i += 2  # skip preamble pair
            continue
        # Decode bit
        if abs(on - _BIT1_ON) <= tol:
            bits.append(1)
        elif abs(on - _BIT0_ON) <= tol:
            bits.append(0)
        i += 2

    if len(bits) < FRAME_SIZE * 8:
        return None

    raw = bits[:FRAME_SIZE * 8]
    frame_bytes = bytearray()
    for byte_idx in range(FRAME_SIZE):
        byte_val = 0
        for bit_pos in range(8):
            byte_val = (byte_val << 1) | raw[byte_idx * 8 + bit_pos]
        frame_bytes.append(byte_val)
    return bytes(frame_bytes)


def write_sub_file(path, device_id: bytes, counter: int, seed: bytes,
                   freq_hz: int = 433920000) -> None:
    """Write a Flipper .sub v1 file for one frame press."""
    frame = encode_frame(device_id, counter, seed)
    timings = frame_to_ook_timings(frame)
    raw_str = " ".join(str(t) for t in timings)
    content = (
        "Filetype: Flipper SubGhz RAW File\n"
        "Version: 1\n"
        f"Frequency: {freq_hz}\n"
        "Preset: FuriHalSubGhzPresetOok270Async\n"
        "Protocol: RAW\n"
        f"RAW_Data: {raw_str}\n"
    )
    with open(path, "w") as f:
        f.write(content)


def read_sub_file(path) -> list:
    """Parse a Flipper .sub file and return RAW_Data timings as list of ints."""
    with open(path) as f:
        for line in f:
            if line.startswith("RAW_Data:"):
                return [int(x) for x in line.split(":", 1)[1].split()]
    return []
