"""Flipper Zero .nfc v4 → Proxmark3 .eml converter for the Garage module.

Duplicated from challenges/coffee/nfc_to_pm3_eml.py to avoid cross-module
imports; the logic is identical.
"""

import re
from pathlib import Path

_BLOCK_RE = re.compile(r"^Block\s+(\d+):\s+([0-9A-Fa-f ]+)$")


def parse_nfc(path) -> dict:
    """Parse a Flipper .nfc v4 file.

    Returns:
        dict mapping block_number (int) → bytes (16 bytes each).
    """
    blocks = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            m = _BLOCK_RE.match(line)
            if m:
                block_num = int(m.group(1))
                hex_bytes = bytes.fromhex(m.group(2).replace(" ", ""))
                if len(hex_bytes) != 16:
                    raise ValueError(
                        f"Block {block_num} has {len(hex_bytes)} bytes, expected 16"
                    )
                blocks[block_num] = hex_bytes
    return blocks


def blocks_to_eml(blocks: dict, total_blocks: int = 64) -> str:
    """Serialise block dict to PM3 .eml format (one 32-hex-char line per block)."""
    lines = []
    for i in range(total_blocks):
        b = blocks.get(i, bytes(16))
        lines.append(b.hex())
    return "\n".join(lines) + "\n"


def nfc_to_eml(src, dst) -> None:
    """Convert a .nfc file to a .eml file."""
    blocks = parse_nfc(src)
    eml = blocks_to_eml(blocks)
    Path(dst).write_text(eml)


def eml_to_blocks(path) -> dict:
    """Parse a PM3 .eml file back to a block dict."""
    blocks = {}
    with open(path) as f:
        for idx, line in enumerate(f):
            line = line.strip()
            if line:
                blocks[idx] = bytes.fromhex(line)
    return blocks
