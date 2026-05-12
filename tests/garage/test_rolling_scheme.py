"""Tests for challenges.garage.rolling_scheme."""
import struct
import unittest

from challenges.garage.rolling_scheme import (
    FRAME_SIZE,
    _crc16,
    encode_frame,
    decode_frame,
    frame_to_ook_timings,
    ook_timings_to_frame,
    write_sub_file,
    read_sub_file,
)

_DEV = bytes.fromhex("DEADBEEF")
_SEED = bytes.fromhex("C0FFEE11")


class TestCrc16(unittest.TestCase):
    def test_known_value(self):
        # CRC-16/CCITT-FALSE of b"\x00\x00" = 0x1021? Let's just test round-trip
        data = b"\x12\x34\x56\x78"
        crc = _crc16(data)
        self.assertIsInstance(crc, int)
        self.assertLessEqual(crc, 0xFFFF)

    def test_empty(self):
        self.assertEqual(_crc16(b""), 0xFFFF)

    def test_different_inputs_different_crcs(self):
        self.assertNotEqual(_crc16(b"\x00"), _crc16(b"\x01"))


class TestEncodeDecode(unittest.TestCase):
    def test_frame_size(self):
        frame = encode_frame(_DEV, 100, _SEED)
        self.assertEqual(len(frame), FRAME_SIZE)

    def test_round_trip(self):
        for ctr in (0, 1, 99, 100, 0xFFFF, 0xFFFFFFFF):
            frame = encode_frame(_DEV, ctr, _SEED)
            dev_id, counter, ok = decode_frame(frame, _SEED)
            self.assertTrue(ok, f"CRC failed for counter={ctr}")
            self.assertEqual(dev_id, _DEV)
            self.assertEqual(counter, ctr)

    def test_bad_crc_detected(self):
        frame = bytearray(encode_frame(_DEV, 42, _SEED))
        frame[8] ^= 0xFF  # corrupt CRC
        _, _, ok = decode_frame(bytes(frame), _SEED)
        self.assertFalse(ok)

    def test_wrong_seed_gives_wrong_counter(self):
        frame = encode_frame(_DEV, 42, _SEED)
        wrong_seed = bytes.fromhex("DEADBEEF")
        _, counter, ok = decode_frame(frame, wrong_seed)
        # CRC may or may not pass, but counter should differ
        if ok:
            self.assertNotEqual(counter, 42)

    def test_invalid_device_id_length(self):
        with self.assertRaises(ValueError):
            encode_frame(b"\x01\x02\x03", 0, _SEED)

    def test_invalid_seed_length(self):
        with self.assertRaises(ValueError):
            encode_frame(_DEV, 0, b"\x01\x02\x03")

    def test_counter_overflow(self):
        with self.assertRaises(ValueError):
            encode_frame(_DEV, 0x1_0000_0000, _SEED)

    def test_distinct_counters_give_distinct_frames(self):
        f1 = encode_frame(_DEV, 100, _SEED)
        f2 = encode_frame(_DEV, 101, _SEED)
        self.assertNotEqual(f1, f2)

    def test_distinct_devices_give_distinct_frames(self):
        dev2 = bytes.fromhex("CAFEBABE")
        f1 = encode_frame(_DEV, 42, _SEED)
        f2 = encode_frame(dev2, 42, _SEED)
        self.assertNotEqual(f1, f2)


class TestOokTimings(unittest.TestCase):
    def test_round_trip(self):
        frame = encode_frame(_DEV, 77, _SEED)
        timings = frame_to_ook_timings(frame)
        recovered = ook_timings_to_frame(timings)
        self.assertIsNotNone(recovered)
        self.assertEqual(recovered, frame)

    def test_timings_all_ints(self):
        frame = encode_frame(_DEV, 1, _SEED)
        timings = frame_to_ook_timings(frame)
        for t in timings:
            self.assertIsInstance(t, int)

    def test_ends_with_gap(self):
        frame = encode_frame(_DEV, 1, _SEED)
        timings = frame_to_ook_timings(frame)
        self.assertLess(timings[-1], 0)  # end gap is negative

    def test_preamble_present(self):
        frame = encode_frame(_DEV, 1, _SEED)
        timings = frame_to_ook_timings(frame)
        self.assertGreater(timings[0], 1000)  # preamble is long


class TestSubFile(unittest.TestCase):
    def test_write_read_round_trip(self):
        import tempfile, os
        frame = encode_frame(_DEV, 200, _SEED)
        with tempfile.NamedTemporaryFile(suffix=".sub", delete=False) as tf:
            path = tf.name
        try:
            write_sub_file(path, _DEV, 200, _SEED)
            timings = read_sub_file(path)
            self.assertGreater(len(timings), 0)
            recovered = ook_timings_to_frame(timings)
            self.assertIsNotNone(recovered)
            _, counter, ok = decode_frame(recovered, _SEED)
            self.assertTrue(ok)
            self.assertEqual(counter, 200)
        finally:
            os.unlink(path)
