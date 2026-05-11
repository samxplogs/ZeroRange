"""MIFARE Classic value-block encode / decode / validate.

Format (16 bytes):
  [V  4B LE] [~V 4B LE] [V  4B LE] [addr 1B] [~addr 1B] [addr 1B] [~addr 1B]

All arithmetic on signed 32-bit integers (little-endian).
"""

import struct
from typing import Tuple


class ValueBlockError(ValueError):
    """Raised by validate() when a block is not a valid value block."""


def encode(value: int, addr: int) -> bytes:
    """Return a 16-byte MIFARE value block for *value* (signed 32-bit) at *addr*."""
    if not (-2**31 <= value <= 2**31 - 1):
        raise ValueError(f"value {value} out of signed 32-bit range")
    if not (0 <= addr <= 255):
        raise ValueError(f"addr {addr} out of byte range")

    v_le = struct.pack("<i", value)        # 4 bytes little-endian signed
    inv_v_le = bytes(b ^ 0xFF for b in v_le)
    a = bytes([addr])
    inv_a = bytes([addr ^ 0xFF])
    return v_le + inv_v_le + v_le + a + inv_a + a + inv_a


def decode(block: bytes) -> int:
    """Return the signed 32-bit value stored in a 16-byte value block.

    Raises ValueBlockError if the block fails structural validation.
    """
    validate(block)
    return struct.unpack("<i", block[0:4])[0]


def validate(block: bytes) -> None:
    """Raise ValueBlockError with a specific reason if *block* is invalid.

    Checks performed:
      1. Length must be 16.
      2. Bytes 0-3 == Bytes 8-11  (value triple-redundancy).
      3. Bytes 4-7 == bitwise complement of bytes 0-3.
      4. Bytes 12, 14 == Bytes 12, 14 match each other (addr consistent).
      5. Bytes 13, 15 == Bytes 13, 15 match each other (inv-addr consistent).
      6. Byte 13 == Byte 12 ^ 0xFF  (addr/inv-addr relationship).
    """
    if len(block) != 16:
        raise ValueBlockError(f"Bad length: expected 16, got {len(block)}")

    v = block[0:4]
    inv_v = block[4:8]
    v2 = block[8:12]

    if v != v2:
        raise ValueBlockError("Bad ~V: V copies at bytes 0-3 and 8-11 differ")

    expected_inv = bytes(b ^ 0xFF for b in v)
    if inv_v != expected_inv:
        raise ValueBlockError("Bad ~V: inverted copy at bytes 4-7 is wrong")

    addr = block[12]
    if block[14] != addr:
        raise ValueBlockError("Bad addr: addr bytes 12 and 14 differ")

    inv_addr = block[13]
    if block[15] != inv_addr:
        raise ValueBlockError("Bad addr: inv-addr bytes 13 and 15 differ")

    if inv_addr != (addr ^ 0xFF):
        raise ValueBlockError("Bad addr: inv-addr is not the complement of addr")
