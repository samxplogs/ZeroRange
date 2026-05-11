"""Tests for challenges.coffee.nfc_to_pm3_eml — parse + round-trip."""

import tempfile
import unittest
from pathlib import Path

from challenges.coffee.nfc_to_pm3_eml import (
    parse_nfc,
    blocks_to_eml,
    eml_to_blocks,
    nfc_to_eml,
    NfcConvertError,
)

_BADGES_DIR = Path(__file__).parent.parent.parent / "challenges" / "coffee" / "badges"


class TestParseShippedBadges(unittest.TestCase):
    """Both shipped .nfc fixtures must parse to exactly 64 blocks of 16 bytes."""

    def _check_badge(self, name: str) -> dict:
        path = _BADGES_DIR / name
        self.assertTrue(path.exists(), f"Badge file missing: {path}")
        blocks = parse_nfc(path)
        self.assertEqual(len(blocks), 64)
        for i in range(64):
            self.assertIn(i, blocks)
            self.assertEqual(len(blocks[i]), 16, f"Block {i} length != 16")
        return blocks

    def test_credit_low_parses(self):
        self._check_badge("credit_low.nfc")

    def test_credit_high_parses(self):
        self._check_badge("credit_high.nfc")


class TestRoundTrip(unittest.TestCase):
    """parse_nfc → blocks_to_eml → eml_to_blocks must be byte-equal for all 64 blocks."""

    def _round_trip(self, name: str):
        src = _BADGES_DIR / name
        blocks_orig = parse_nfc(src)

        with tempfile.TemporaryDirectory() as tmp:
            eml = Path(tmp) / "out.eml"
            nfc_to_eml(src, eml)
            blocks_back = eml_to_blocks(eml)

        self.assertEqual(len(blocks_back), 64)
        for i in range(64):
            self.assertEqual(
                blocks_orig[i],
                blocks_back[i],
                f"Block {i} differs after round-trip",
            )

    def test_round_trip_credit_low(self):
        self._round_trip("credit_low.nfc")

    def test_round_trip_credit_high(self):
        self._round_trip("credit_high.nfc")


class TestKnownBlockContent(unittest.TestCase):
    """Spot-check key blocks in the shipped fixtures."""

    def test_low_uid_block0(self):
        blocks = parse_nfc(_BADGES_DIR / "credit_low.nfc")
        # UID bytes 04 A3 F5 B2 at the start of block 0
        self.assertEqual(blocks[0][:4], bytes([0x04, 0xA3, 0xF5, 0xB2]))

    def test_high_uid_block0(self):
        blocks = parse_nfc(_BADGES_DIR / "credit_high.nfc")
        self.assertEqual(blocks[0][:4], bytes([0x04, 0x8C, 0x2F, 0xE1]))

    def test_brewmasterpro_block1(self):
        for name in ("credit_low.nfc", "credit_high.nfc"):
            with self.subTest(file=name):
                blocks = parse_nfc(_BADGES_DIR / name)
                self.assertEqual(blocks[1][:4], b"BREW")

    def test_low_credit_block40(self):
        from challenges.coffee.value_block import decode, validate
        blocks = parse_nfc(_BADGES_DIR / "credit_low.nfc")
        validate(blocks[40])
        self.assertEqual(decode(blocks[40]), 150)

    def test_high_credit_block40(self):
        from challenges.coffee.value_block import decode, validate
        blocks = parse_nfc(_BADGES_DIR / "credit_high.nfc")
        validate(blocks[40])
        self.assertEqual(decode(blocks[40]), 5000)

    def test_low_sector8_trailer_key_b(self):
        blocks = parse_nfc(_BADGES_DIR / "credit_low.nfc")
        trailer = blocks[35]  # sector 8, block 3 = block index 35
        self.assertEqual(trailer[10:16], bytes.fromhex("B4EEC0FFEE11"))

    def test_high_sector10_trailer_key_b(self):
        blocks = parse_nfc(_BADGES_DIR / "credit_high.nfc")
        trailer = blocks[43]  # sector 10, block 3 = block index 43
        self.assertEqual(trailer[10:16], bytes.fromhex("B4EEC0FFEE11"))


class TestParseErrors(unittest.TestCase):
    """Bad input files must raise NfcConvertError."""

    def _write_and_parse(self, content: str) -> dict:
        with tempfile.NamedTemporaryFile(suffix=".nfc", mode="w", delete=False) as f:
            f.write(content)
            path = Path(f.name)
        try:
            return parse_nfc(path)
        finally:
            path.unlink(missing_ok=True)

    def test_wrong_filetype(self):
        with self.assertRaises(NfcConvertError):
            self._write_and_parse("Filetype: Not Flipper\nDevice type: MIFARE Classic\n")

    def test_wrong_device_type(self):
        with self.assertRaises(NfcConvertError):
            self._write_and_parse(
                "Filetype: Flipper NFC device\nVersion: 4\nDevice type: NTAG215\n"
            )

    def test_incomplete_blocks(self):
        header = "Filetype: Flipper NFC device\nVersion: 4\nDevice type: MIFARE Classic\n"
        blocks = "\n".join(f"Block {i}: " + " ".join(["00"] * 16) for i in range(10))
        with self.assertRaises(NfcConvertError):
            self._write_and_parse(header + blocks)


if __name__ == "__main__":
    unittest.main()
