# Garage Module Integration Guide

> **Disclaimer:** "Sam Garage" is an entirely fictional facility created for
> ZeroRange. Any resemblance to real garage-remote products, access-control
> vendors, or rolling-code algorithms (KeeLoq, AES rolling, etc.) is **purely
> coincidental**. The toy rolling scheme is deliberately weaker than any real
> product and exists only for hands-on security training in a controlled
> environment.

---

## Overview

The Garage module (`garage_handler.py`) chains three scored stages around a
fictional commercial garage.

| Stage | Hardware | Topic | Points |
|-------|----------|-------|--------|
| 1 — Rolling Code | HackRF One | RollJam principle vs. OOK rolling code | 10 |
| 2 — Pedestrian Gate | iButton USB HID | iButton fob authentication | 10 |
| 3 — Tech Room | Proxmark3 | MIFARE Classic with side-channel leaked Key A | 10 |

---

## LCD menu flow

From the root menu, scroll to **Garage** and press **SELECT**.

```
Garage  0/30
SEL=Start L=Back
```

Pressing **SELECT** launches the internal stage menu:

```
>Stage1:RollJam
 U/D SEL=Go 0/30
```

Navigate with **▲ UP / ▼ DOWN**, launch with **● SELECT**, return with **◄ BACK**.

---

## Stage 1 — Rolling-Code Teardown (10 pts)

### Sub-stage 1a (3 pts): Replay rejected

1. ZeroRange TXes press N at 433.92 MHz OOK via HackRF.
2. Receiver internally advances counter to N+1.
3. ZeroRange replays press N against the receiver — it rejects it (stale counter).
4. LCD: `"Replay rejected — try harder."`
5. Learner presses **SELECT** to confirm they witnessed the rejection → **+3 pts**.

### Sub-stage 1b (7 pts): RollJam

1. ZeroRange simulates jamming (receiver's `jammed` flag prevents advancement).
2. ZeroRange TXes press N+1 — learner's Flipper can optionally capture it.
3. ZeroRange TXes press N+2 (second captured frame).
4. ZeroRange lifts jamming, then replays press N+1 → receiver accepts → **Gate OPEN → +7 pts**.

### Toy rolling-code format

See `challenges/garage/rolling_scheme.md` for the full spec. Summary:

```
Frame (10 bytes):  [ID3 ID2 ID1 ID0] [CTR_enc3..0] [CRC1 CRC0]
CTR_enc[i] = counter_byte[i] XOR seed[i]
CRC = CRC-16/CCITT-FALSE over bytes 0–7
Acceptance window: counter in (last_accepted, last_accepted + window]
```

The seed ships in `config.json`. It is intentionally weak — a learner can
derive it from a handful of captured frames. This is the educational point.

### TX power and legal responsibility

HackRF transmits at its configured power level (`DEFAULT_TX_GAIN = 47 dBm`
in `hackrf_handler.py`). The user is fully responsible for ensuring that:

- Transmission on 433.92 MHz complies with local regulations (ISM band rules
  differ between jurisdictions).
- No real garage receivers, vehicles, or access-control systems are in range.
- This training is conducted in a controlled lab environment.

To reduce TX power, edit `hackrf_handler.py`:

```python
DEFAULT_TX_GAIN = 14   # reduce to ~14 dBm; lower is safer
```

---

## Stage 2 — Pedestrian Gate (10 pts)

1. LCD: *"Touch iBtn fob"*
2. Learner touches the DS1990 iButton to the USB HID reader.
3. UID matches `config.garage.pedestrian_uid` → **+10 pts**.
4. Side-channel leak: LCD shows `"Tech room Key A: F1 5E C0 DE 00 17"` — use this for Stage 3.

Three consecutive wrong reads trigger a `"Try a different fob"` hint.
Stage is idempotent — re-running shows the leak without re-awarding.

---

## Stage 3 — Tech Room (10 pts)

1. PM3 emulates `challenges/garage/badges/tech_room.nfc`.
2. LCD: *"Tech room. Open it!"*
3. Learner reads sector 0 with Key A = `F1 5E C0 DE 00 17` (from Stage 2 leak).
4. Auto-detect: PM3 emulation log shows Key A auth on sector 0 → **+10 pts**.
5. Manual confirm: **SELECT** → ZeroRange reads block 0 with Key A to verify.

### Badge specification

| Field | Value |
|-------|-------|
| File | `challenges/garage/badges/tech_room.nfc` |
| Type | MIFARE Classic 1K |
| UID | `04 B7 3A C2` |
| ATQA | `00 04` |
| SAK | `08` |
| Sector 0 Key A | `F1 5E C0 DE 00 17` |
| All other sectors Key A | `FF FF FF FF FF FF` (default) |
| Block 1 | `GARAGE-TECH-ROOM` (ASCII) |

---

## Web companion

The web companion is a Flask app running as `zerorange-web` (separate systemd
service). Stage 1's view is event-driven via SSE and updates in real time.

### Status

```bash
sudo systemctl status zerorange-web
```

### Enable / disable

```bash
sudo systemctl enable --now zerorange-web   # start now + on boot
sudo systemctl stop  zerorange-web          # stop (stays enabled)
sudo systemctl disable --now zerorange-web  # disable completely
```

### Accessing the web companion

Connect to the ZeroRange Wi-Fi hotspot, then open:

```
http://192.168.1.193:8080/scenarios/garage/
```

- Scenario list: `http://192.168.1.193:8080/`
- Garage view:   `http://192.168.1.193:8080/scenarios/garage/`
- SSE stream:    `http://192.168.1.193:8080/scenarios/garage/events`

### SSE event reference

| Event JSON | When emitted |
|------------|-------------|
| `{"event": "press_emitted", "counter": N}` | HackRF TXed a frame |
| `{"event": "jam_started"}` | Jamming simulation enabled |
| `{"event": "frame_held", "counter": N, "tray_size": 1\|2}` | Frame added to capture tray |
| `{"event": "replay_received", "counter": N, "accepted": bool, "reason": "..."}` | Replay decoded and evaluated |
| `{"event": "window_slid", "last_accepted": N, "window": 16}` | Receiver accepted and advanced |
| `{"event": "stage_complete", "stage": 1\|2\|3, "points": N}` | Stage credited |
| `{"event": "key_leaked", "key_a_hex": "F15EC0DE0017"}` | Stage 2 Key A leak emitted |
| `{"stage": N, "status": "success", "points": 10}` | Stage N completed (legacy form) |

### Debug panel

The Stage 1 view has a `[DEBUG]` toggle that reveals:
- `last_accepted`, `window`, `tray_size`, `jammed` state
- A **Send press** button that fires a synthetic `press_emitted` event (TX only,
  no score change — useful for demo recordings).

---

## Configuration (`config.json`)

```json
"garage": {
  "rolling": {
    "device_id_hex":  "DE AD BE EF",
    "seed_hex":       "C0 FF EE 11",
    "freq_hz":        433920000,
    "modulation":     "OOK",
    "symbol_us":      250,
    "press_gap_ms":   1500,
    "counter_window": 16,
    "initial_counter": 100
  },
  "pedestrian_uid":      "REPLACE_WITH_DS1990_UID",
  "tech_room_key_a_hex": "F15EC0DE0017",
  "badge_path":  "challenges/garage/badges/tech_room.nfc",
  "signal_paths": {
    "press_N":        "challenges/garage/signals/press_N.sub",
    "press_N_plus_1": "challenges/garage/signals/press_N_plus_1.sub"
  },
  "max_wrong_reads_stage2": 3
}
```

| Key | Description |
|-----|-------------|
| `rolling.device_id_hex` | 4-byte device ID of the fictional remote (hex, spaces optional) |
| `rolling.seed_hex` | 4-byte XOR seed (the "secret"; intentionally derivable by inspection) |
| `rolling.freq_hz` | TX frequency in Hz (default 433.92 MHz) |
| `rolling.initial_counter` | Starting counter value (press N = initial_counter) |
| `rolling.counter_window` | Max lookahead; receiver accepts counter in (last, last+window] |
| `pedestrian_uid` | DS1990 UID for Stage 2 (16 hex chars, no dashes) |
| `tech_room_key_a_hex` | MIFARE Classic Key A for sector 0 (12 hex chars) |
| `badge_path` | Path to tech room .nfc badge |
| `max_wrong_reads_stage2` | Wrong-UID streak before "Try a different fob" hint |

### Setting the pedestrian UID

Run the Coffee Stage 1 (iButton) to find your DS1990's UID, or use any
iButton reader. Then update `config.json`:

```json
"pedestrian_uid": "0100C0FFEE7E11AB"
```

### Regenerating .sub fixtures

```bash
python3 - <<'EOF'
from challenges.garage.rolling_scheme import write_sub_file
import json, pathlib
cfg = json.loads(pathlib.Path("config.json").read_text())["garage"]["rolling"]
dev_id = bytes.fromhex(cfg["device_id_hex"].replace(" ", ""))
seed   = bytes.fromhex(cfg["seed_hex"].replace(" ", ""))
freq   = cfg["freq_hz"]
ctr    = cfg["initial_counter"]
write_sub_file("challenges/garage/signals/press_N.sub",         dev_id, ctr,     seed, freq)
write_sub_file("challenges/garage/signals/press_N_plus_1.sub",  dev_id, ctr + 1, seed, freq)
print("Done.")
EOF
```

---

## Wiring and hardware notes

- **HackRF One:** detected via `hackrf_info`. If unplugged between stages, a
  `"HackRF not found"` screen appears with a BACK option. TX-only during Stage 1
  — never TX and RX simultaneously.
- **iButton HID reader:** same auto-detect as the Coffee module
  (`_find_hid_device()` in `garage_handler.py`).
- **Proxmark3:** `/dev/ttyACM0` by default. Disconnecting surfaces a graceful
  error. Emulation is always stopped in a `finally` block on stage exit.
- **Cleanup:** killing `zerorange.py` mid-Stage-1 stops any `hackrf_transfer`
  child processes. Verify with `pgrep hackrf_transfer`.

---

## Running tests

```bash
cd /home/sam/ZeroRange
python3 -m unittest discover -s tests/garage -v
```

Expected: **60 tests, 0 failures**.

---

## Trainer quick-start checklist

Before a session:

1. Connect HackRF One, iButton USB reader, and Proxmark3 to the Pi.
2. Power on the Pi — `zerorange.service` and `zerorange-web` start automatically.
3. Set `config.garage.pedestrian_uid` to your DS1990's UID if not already done.
4. Optionally distribute `press_N.sub` / `press_N_plus_1.sub` to learners so
   they can compare the captured frames and verify the rolling scheme.
5. Brief learners: Stage 1 teaches why fixed replay fails; 1b teaches RollJam.
   Stage 2 demonstrates iButton authentication. Stage 3 uses the side-channel
   Key A from Stage 2 to complete the chain.

---

## File layout

```
ZeroRange/
├── garage_handler.py
├── challenges/garage/
│   ├── __init__.py
│   ├── rolling_scheme.py          # Frame encode/decode, .sub I/O
│   ├── rolling_scheme.md          # Toy rolling-code spec
│   ├── receiver_state.py          # Synthetic receiver state machine
│   ├── ook_demod.py               # OOK demodulation (.sub and IQ)
│   ├── nfc_to_pm3_eml.py          # Flipper .nfc v4 → PM3 .eml converter
│   ├── stage1_rolling.py          # Stage 1: RollJam demo
│   ├── stage2_pedestrian.py       # Stage 2: iButton gate
│   ├── stage3_tech_room.py        # Stage 3: MIFARE Classic
│   ├── signals/
│   │   ├── press_N.sub            # Flipper .sub, counter=100
│   │   ├── press_N_plus_1.sub     # Flipper .sub, counter=101
│   │   └── README.md
│   └── badges/
│       └── tech_room.nfc          # MIFARE Classic 1K, sector 0 Key A = F15EC0DE0017
├── tests/garage/
│   ├── test_rolling_scheme.py
│   ├── test_receiver_state.py
│   ├── test_ook_demod.py
│   ├── test_nfc_to_pm3_eml.py
│   └── test_garage_handler.py
├── app/web/
│   ├── routes/garage.py           # garage_bp blueprint + SSE + debug endpoint
│   ├── templates/scenarios/garage.html
│   └── static/scenarios/garage/
│       ├── logo.svg
│       ├── logo-mono.svg
│       ├── stage1.svg             # Event-driven rolling-code animation
│       ├── stage2.svg             # Gate + post-it leak animation
│       └── stage3.svg             # Server rack + MIFARE card animation
└── docs/
    └── GARAGE_INTEGRATION.md      # This file
```
