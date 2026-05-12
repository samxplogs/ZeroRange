"""Tests for challenges.garage.nfc_to_pm3_eml and the tech_room badge."""
import os
import tempfile
import unittest
from pathlib import Path

from challenges.garage.nfc_to_pm3_eml import parse_nfc, blocks_to_eml, nfc_to_eml, eml_to_blocks

_BADGE = Path("challenges/garage/badges/tech_room.nfc")
_KEY_A_S0 = bytes.fromhex("F15EC0DE0017")
_ACCESS = bytes.fromhex("FF078069")
_KEY_B_DEF = bytes.fromhex("FFFFFFFFFFFF")


class TestParseNfc(unittest.TestCase):
    def setUp(self):
        if not _BADGE.exists():
            self.skipTest("tech_room.nfc not found")

    def test_parses_64_blocks(self):
        blocks = parse_nfc(_BADGE)
        self.assertEqual(len(blocks), 64)

    def test_block_0_uid(self):
        blocks = parse_nfc(_BADGE)
        b0 = blocks[0]
        self.assertEqual(len(b0), 16)
        self.assertEqual(b0[:4], bytes.fromhex("04B73AC2"))

    def test_block_1_ascii_tag(self):
        blocks = parse_nfc(_BADGE)
        self.assertEqual(blocks[1], b"GARAGE-TECH-ROOM")

    def test_sector0_trailer_key_a(self):
        blocks = parse_nfc(_BADGE)
        trailer = blocks[3]
        self.assertEqual(trailer[:6], _KEY_A_S0)

    def test_sector0_trailer_access_bits(self):
        blocks = parse_nfc(_BADGE)
        trailer = blocks[3]
        self.assertEqual(trailer[6:10], _ACCESS)

    def test_other_sectors_default_key_a(self):
        blocks = parse_nfc(_BADGE)
        for sector in range(1, 16):
            trailer = blocks[sector * 4 + 3]
            self.assertEqual(
                trailer[:6], _KEY_B_DEF,
                f"Sector {sector} Key A should be default FFFFFFFFFFFF"
            )

    def test_all_blocks_16_bytes(self):
        blocks = parse_nfc(_BADGE)
        for i, b in blocks.items():
            self.assertEqual(len(b), 16, f"Block {i} wrong length")


class TestNfcToEml(unittest.TestCase):
    def setUp(self):
        if not _BADGE.exists():
            self.skipTest("tech_room.nfc not found")

    def test_eml_round_trip(self):
        fd, path = tempfile.mkstemp(suffix=".eml")
        os.close(fd)
        try:
            nfc_to_eml(_BADGE, path)
            recovered = eml_to_blocks(path)
            original = parse_nfc(_BADGE)
            for i in range(64):
                self.assertEqual(original[i], recovered[i], f"Block {i} mismatch")
        finally:
            os.unlink(path)

    def test_eml_line_count(self):
        blocks = parse_nfc(_BADGE)
        eml = blocks_to_eml(blocks)
        lines = [l for l in eml.strip().split("\n") if l]
        self.assertEqual(len(lines), 64)

    def test_eml_lines_are_32_hex_chars(self):
        blocks = parse_nfc(_BADGE)
        eml = blocks_to_eml(blocks)
        for line in eml.strip().split("\n"):
            if line:
                self.assertEqual(len(line), 32)
                int(line, 16)  # should not raise
