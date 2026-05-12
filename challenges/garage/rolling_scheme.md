# Sam Garage — Toy Rolling-Code Scheme

> **Disclaimer:** This scheme is entirely fictional and deliberately weak.
> It does NOT resemble KeeLoq, AES rolling, or any real product.
> The seed ships in `config.json` — treat it as the "secret" the receiver
> and remote share. A learner can derive it by capturing multiple frames.

---

## Frame format (10 bytes, MSB first)

```
 Byte:  0   1   2   3   4   5   6   7   8   9
       [ID3 ID2 ID1 ID0][CTR3 CTR2 CTR1 CTR0][CRC1 CRC0]
```

| Field | Size | Description |
|-------|------|-------------|
| `ID`  | 4 bytes | Device identifier (fixed per remote) |
| `CTR_enc` | 4 bytes | `counter[i] XOR seed[i]` (big-endian) |
| `CRC` | 2 bytes | CRC-16/CCITT-FALSE over bytes 0–7 |

### Encoding

```python
CTR_enc[i] = counter_byte[i] XOR seed[i]   (i = 0..3, big-endian)
CRC = CRC16_CCITT_FALSE(ID + CTR_enc)       # poly=0x1021, init=0xFFFF
```

### Receiver acceptance rule

```
Accept iff:
  1. CRC valid
  2. decoded device_id == configured device_id
  3. decoded counter  >  last_accepted
  4. decoded counter  <= last_accepted + window   (default window = 16)
```

---

## OOK modulation (Flipper .sub v1, 433.92 MHz)

| Symbol | Duration | Level |
|--------|----------|-------|
| Preamble | 3400 µs ON, 3400 µs OFF |
| Bit `1`  | 500 µs ON, 250 µs OFF |
| Bit `0`  | 250 µs ON, 500 µs OFF |
| End gap  | 10 000 µs OFF |

All 80 bits (10 bytes × 8 bits) are transmitted MSB first, no encoding layer.

---

## RollJam principle (training explanation)

1. Attacker jams the receiver while capturing frame N.
2. Receiver never sees frame N → counter stays at N-1.
3. Attacker captures frame N+1 (owner presses again) while still jamming.
4. Attacker stops jamming and replays frame N → receiver accepts it (N > N-1).
5. Attacker holds frame N+1 for later use.

This exercise uses a **simulated** jam: ZeroRange's receiver state machine has a
`jammed` flag that suppresses acceptance without any radio interference.
No real jamming is performed or needed.
