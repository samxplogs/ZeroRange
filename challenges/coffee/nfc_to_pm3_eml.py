"""Convert a Flipper Zero v4 MIFARE Classic .nfc file to a Proxmark3 .eml file.

The .eml format is one hex-encoded block per line (32 hex characters),
blocks 0-63 in order. The Proxmark3 loads it with:
  hf mf eload -f <file.eml>

Usage:
  python3 -m challenges.coffee.nfc_to_pm3_eml input.nfc output.eml
"""

import re
import sys
from pathlib import Path


_BLOCK_RE = re.compile(
    r"^Block\s+(\d+)\s*:\s*([0-9a-fA-F]{2}(?:\s+[0-9a-fA-F]{2}){15})\s*$"
)


class NfcConvertError(ValueError):
    """Raised when an .nfc file cannot be parsed or converted."""


def parse_nfc(path: Path) -> dict[int, bytes]:
    """Parse a Flipper Zero v4 MIFARE Classic .nfc file.

    Returns a dict mapping block number (0-63) to 16-byte block data.
    Raises NfcConvertError on format problems.
    """
    text = path.read_text(encoding="utf-8")

    if "Filetype: Flipper NFC device" not in text:
        raise NfcConvertError(f"{path}: not a Flipper NFC device file")

    if "Device type: MIFARE Classic" not in text:
        raise NfcConvertError(f"{path}: not a MIFARE Classic card")

    blocks: dict[int, bytes] = {}
    for line in text.splitlines():
        m = _BLOCK_RE.match(line.strip())
        if m:
            blk_num = int(m.group(1))
            raw = bytes(int(h, 16) for h in m.group(2).split())
            if len(raw) != 16:
                raise NfcConvertError(f"{path}: block {blk_num} has {len(raw)} bytes, expected 16")
            blocks[blk_num] = raw

    if len(blocks) != 64:
        raise NfcConvertError(
            f"{path}: expected 64 blocks, found {len(blocks)}"
        )

    return blocks


def blocks_to_eml(blocks: dict[int, bytes]) -> str:
    """Serialise a block dict to Proxmark3 .eml text (one hex line per block)."""
    lines = []
    for i in range(64):
        if i not in blocks:
            raise NfcConvertError(f"Missing block {i}")
        lines.append(blocks[i].hex().upper())
    return "\n".join(lines) + "\n"


def nfc_to_eml(src: Path, dst: Path) -> None:
    """Convert *src* (.nfc) to *dst* (.eml), overwriting *dst* if it exists."""
    blocks = parse_nfc(src)
    dst.write_text(blocks_to_eml(blocks), encoding="utf-8")


def eml_to_blocks(path: Path) -> dict[int, bytes]:
    """Parse a Proxmark3 .eml file back to a block dict (for round-trip tests)."""
    lines = [ln.strip() for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]
    if len(lines) != 64:
        raise NfcConvertError(f"{path}: expected 64 lines, got {len(lines)}")
    blocks: dict[int, bytes] = {}
    for i, line in enumerate(lines):
        raw = bytes.fromhex(line)
        if len(raw) != 16:
            raise NfcConvertError(f"{path}: line {i} has {len(raw)} bytes, expected 16")
        blocks[i] = raw
    return blocks


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} input.nfc output.eml", file=sys.stderr)
        sys.exit(1)
    nfc_to_eml(Path(sys.argv[1]), Path(sys.argv[2]))
    print(f"Converted {sys.argv[1]} → {sys.argv[2]}")
