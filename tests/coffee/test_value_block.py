"""Tests for challenges.coffee.value_block — pure logic, no hardware."""

import struct
import unittest
from challenges.coffee.value_block import encode, decode, validate, ValueBlockError


class TestRoundTrip(unittest.TestCase):
    """encode → decode must be identity for any valid value."""

    VALUES = [0, 1, 150, 5000, 100_000, -40, -(2**31), 2**31 - 1]
    ADDR = 40  # block 40

    def test_round_trip(self):
        for v in self.VALUES:
            with self.subTest(value=v):
                block = encode(v, self.ADDR)
                self.assertEqual(len(block), 16)
                self.assertEqual(decode(block), v)

    def test_addr_in_block(self):
        block = encode(150, 40)
        self.assertEqual(block[12], 40)
        self.assertEqual(block[14], 40)
        self.assertEqual(block[13], 40 ^ 0xFF)
        self.assertEqual(block[15], 40 ^ 0xFF)

    def test_different_addrs(self):
        for addr in (0, 1, 40, 42, 255):
            block = encode(100, addr)
            self.assertEqual(decode(block), 100)
            self.assertEqual(block[12], addr)

    def test_inv_v_bytes(self):
        block = encode(150, 40)
        v_bytes = block[0:4]
        inv_v_bytes = block[4:8]
        for a, b in zip(v_bytes, inv_v_bytes):
            self.assertEqual(a ^ b, 0xFF)


class TestValidate(unittest.TestCase):
    """validate() must accept good blocks and reject specifically-broken ones."""

    def _good_block(self, value=150, addr=40):
        return encode(value, addr)

    def test_good_block_passes(self):
        for v in [0, 150, 5000, -40]:
            validate(self._good_block(v))  # no exception

    def test_wrong_length(self):
        with self.assertRaises(ValueBlockError) as ctx:
            validate(b"\x00" * 15)
        self.assertIn("length", str(ctx.exception).lower())

    def test_flip_v_byte_causes_bad_copy(self):
        block = bytearray(self._good_block(150, 40))
        block[0] ^= 0x01  # flip bit in V at index 0
        with self.assertRaises(ValueBlockError) as ctx:
            validate(bytes(block))
        self.assertIn("Bad ~V", str(ctx.exception))

    def test_flip_inv_v_byte_causes_bad_inv(self):
        block = bytearray(self._good_block(150, 40))
        block[5] ^= 0x01  # flip bit in ~V
        with self.assertRaises(ValueBlockError) as ctx:
            validate(bytes(block))
        self.assertIn("Bad ~V", str(ctx.exception))

    def test_flip_v2_byte_causes_bad_copy(self):
        block = bytearray(self._good_block(150, 40))
        block[9] ^= 0x01  # flip bit in second V copy
        with self.assertRaises(ValueBlockError) as ctx:
            validate(bytes(block))
        self.assertIn("Bad ~V", str(ctx.exception))

    def test_flip_addr_byte_12(self):
        block = bytearray(self._good_block(150, 40))
        block[12] ^= 0x01
        with self.assertRaises(ValueBlockError) as ctx:
            validate(bytes(block))
        self.assertIn("addr", str(ctx.exception).lower())

    def test_flip_addr_byte_14(self):
        block = bytearray(self._good_block(150, 40))
        block[14] ^= 0x01
        with self.assertRaises(ValueBlockError) as ctx:
            validate(bytes(block))
        self.assertIn("addr", str(ctx.exception).lower())

    def test_flip_inv_addr_byte_13(self):
        block = bytearray(self._good_block(150, 40))
        block[13] ^= 0x01
        with self.assertRaises(ValueBlockError) as ctx:
            validate(bytes(block))
        self.assertIn("addr", str(ctx.exception).lower())

    def test_flip_inv_addr_byte_15(self):
        block = bytearray(self._good_block(150, 40))
        block[15] ^= 0x01
        with self.assertRaises(ValueBlockError) as ctx:
            validate(bytes(block))
        self.assertIn("addr", str(ctx.exception).lower())

    def test_tamper_any_single_bit_bytes_0_to_11(self):
        """Flipping any bit in bytes 0-11 must fail validation."""
        good = self._good_block(5000, 40)
        for byte_idx in range(12):
            for bit in range(8):
                tampered = bytearray(good)
                tampered[byte_idx] ^= (1 << bit)
                with self.subTest(byte=byte_idx, bit=bit):
                    with self.assertRaises(ValueBlockError):
                        validate(bytes(tampered))

    def test_tamper_any_single_bit_bytes_12_to_15(self):
        """Flipping any bit in bytes 12-15 must fail validation."""
        good = self._good_block(5000, 40)
        for byte_idx in range(12, 16):
            for bit in range(8):
                tampered = bytearray(good)
                tampered[byte_idx] ^= (1 << bit)
                with self.subTest(byte=byte_idx, bit=bit):
                    with self.assertRaises(ValueBlockError):
                        validate(bytes(tampered))


class TestKnownBlocks(unittest.TestCase):
    """Verify exact byte sequences from the shipped badge files."""

    def test_credit_low_block40(self):
        # 150 cents at addr 40
        block = bytes.fromhex("96000000 69FFFFFF 96000000 28D728D7".replace(" ", ""))
        validate(block)
        self.assertEqual(decode(block), 150)
        self.assertEqual(block[12], 0x28)
        self.assertEqual(block[13], 0xD7)

    def test_credit_high_block40(self):
        # 5000 cents at addr 40
        block = bytes.fromhex("88130000 77ECFFFF 88130000 28D728D7".replace(" ", ""))
        validate(block)
        self.assertEqual(decode(block), 5000)

    def test_out_of_range_value(self):
        with self.assertRaises(ValueError):
            encode(2**31, 0)  # exceeds INT32_MAX
        with self.assertRaises(ValueError):
            encode(-(2**31) - 1, 0)  # below INT32_MIN


if __name__ == "__main__":
    unittest.main()
