"""Tests for challenges.garage.ook_demod."""
import os
import tempfile
import unittest

from challenges.garage.rolling_scheme import encode_frame, write_sub_file
from challenges.garage.ook_demod import demod_sub_file

_DEV = bytes.fromhex("DEADBEEF")
_SEED = bytes.fromhex("C0FFEE11")


class TestDemodSubFile(unittest.TestCase):
    def _tmp_sub(self, counter: int) -> str:
        fd, path = tempfile.mkstemp(suffix=".sub")
        os.close(fd)
        write_sub_file(path, _DEV, counter, _SEED)
        return path

    def test_round_trip_counter_100(self):
        path = self._tmp_sub(100)
        try:
            result = demod_sub_file(path, _SEED)
            self.assertIsNotNone(result)
            dev_id, counter = result
            self.assertEqual(dev_id, _DEV)
            self.assertEqual(counter, 100)
        finally:
            os.unlink(path)

    def test_round_trip_counter_0(self):
        path = self._tmp_sub(0)
        try:
            result = demod_sub_file(path, _SEED)
            self.assertIsNotNone(result)
            _, counter = result
            self.assertEqual(counter, 0)
        finally:
            os.unlink(path)

    def test_round_trip_counter_high(self):
        path = self._tmp_sub(65535)
        try:
            result = demod_sub_file(path, _SEED)
            self.assertIsNotNone(result)
            _, counter = result
            self.assertEqual(counter, 65535)
        finally:
            os.unlink(path)

    def test_missing_file_returns_none(self):
        result = demod_sub_file("/tmp/nonexistent_zr_test.sub", _SEED)
        self.assertIsNone(result)

    def test_wrong_seed_fails_crc(self):
        path = self._tmp_sub(42)
        try:
            wrong_seed = bytes.fromhex("DEADBEEF")
            result = demod_sub_file(path, wrong_seed)
            # May return None (CRC mismatch) or wrong counter — either is fine
            if result is not None:
                _, counter = result
                self.assertNotEqual(counter, 42)
        finally:
            os.unlink(path)
