# Coffee Module Integration Guide

> **Disclaimer:** Sam BrewMaster Pro is an entirely fictional brand created for
> ZeroRange. Any resemblance to real coffee/vending badge systems, manufacturers,
> or deployments is purely coincidental. This module exists for hands-on security
> training in a controlled environment only.

---

## Overview

The Coffee module (`coffee_handler.py`) chains three stages around a fictional
"Sam BrewMaster Pro" coffee station.  It uses:

| Hardware | Purpose |
|----------|---------|
| iButton USB HID reader | Stage 1 — read technician maintenance token |
| Proxmark3 | Stage 2 — emulate employee badge (hf mf sim) |
| Proxmark3 | Stage 3 — read-back and validate forged value block |

---

## LCD flow

From the root menu, scroll to **Coffee** (after IR) and press **SELECT**.

```
Coffee  0/30
SEL=Start L=Back
```

Pressing SELECT launches the internal stage sub-menu:

```
>Stage1:iButton✓
U/D SEL=Go 10/30
```

Navigate with **UP/DOWN**, launch with **SELECT**, return to main menu with **◄ (LEFT)**.

### Stage 1 — Technician Token

1. LCD: *Pull maint token* → place the DS1990 iButton on the USB HID reader.
2. On match: *Token OK! +10pts* → the LCD reveals the leaked Key B:

   ```
   Leaked log:
   KeyB=B4 EE C0 FF
   Sectors 8-14:
   B4 EE C0 FF EE 11
   ```

3. Three consecutive wrong reads show "Check right token" before retrying.

### Stage 2 — Crack & Dump Badge

1. PM3 emulates `challenges/coffee/badges/credit_low.nfc`.
2. LCD: *PM3 emulates badge. Read it!*
3. Learner uses Flipper Zero — add Key B `B4EEC0FFEE11` to the Flipper user
   dictionary (or use Mfkey32 against the emulation).
4. **Auto-detect**: ZeroRange monitors `hf mf sim` output for Key B auth events.
   When all sectors 8–14 appear, stage completes automatically.
5. **Manual confirm**: press **SELECT** when Flipper shows all 64 blocks
   readable.  ZeroRange then reads sectors 8–14 via PM3 to verify.

### Stage 3 — Top Up Balance

1. LCD: *Need >=50,00 EUR / Present to PM3*
2. Press **SELECT** when your card/Flipper emulation is on the PM3 antenna.
3. ZeroRange reads block 40 with Key B and validates the MIFARE value block:
   - Structure checks: V == V copy, ~V correct, addr consistent.
   - Value check: decoded cents ≥ 5000.
4. Precise rejection reasons:
   - `Bad ~V` — bytes 4-7 are not the bitwise complement of bytes 0-3.
   - `Bad addr` — addr/inv-addr bytes inconsistent.
   - `Value too low` — credit below threshold.

---

## Web companion

The web companion runs as a **separate** Flask service. The LCD loop and Flask
are independent processes — if Flask crashes, the LCD keeps working.

### Enable / disable the web companion

The web companion is controlled by its own systemd service:

```bash
# Enable and start
sudo systemctl enable zerorange-web
sudo systemctl start  zerorange-web

# Stop without disabling
sudo systemctl stop   zerorange-web

# Check status
sudo systemctl status zerorange-web
```

The service file is at `/etc/systemd/system/zerorange-web.service`.

**Install the service:**

```bash
sudo cp /home/pi/ZeroRange/zerorange-web.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable zerorange-web
sudo systemctl start  zerorange-web
```

### Accessing the web companion

Connect to the ZeroRange Wi-Fi hotspot, then open:

```
http://192.168.1.193/
```

(Or whatever the Pi's hotspot IP is — shown on the home screen.)

The `/scenarios/coffee/` page shows live stage animations over Server-Sent
Events.  No manual refresh needed; the page updates in lockstep with the LCD.

### Stage 3 counter animation

The credit counter in the web UI ticks to the observed value (even if rejected)
before showing pass/fail.  The SSE endpoint emits:

```json
{"event": "credit_observed", "value_cents": 4999}
```

followed by the red flash with rejection reason if the value is too low.

---

## Wiring and hardware notes

- **iButton HID reader**: enumerates as `/dev/input/event*`. ZeroRange
  auto-detects the first event device with "keyboard", "hid", or "ibutton"
  in its name.  If auto-detection fails, edit `coffee_handler._find_hid_device`.
- **Proxmark3**: `/dev/ttyACM0` by default (set in `proxmark_handler.py`).
  If disconnected between Stage 1 and Stage 2, a "Proxmark3 not detected"
  screen appears with retry.
- **Cleanup**: Stage 2 always stops the PM3 emulation on exit — even if
  `zerorange.py` is killed (the `finally` block in `stage2_dump.py` handles
  cleanup via `EmulationHandle.stop()`).

---

## Configuration (`config.json`)

```json
"coffee": {
  "technician_uid": "0100C0FFEE7E11AB",
  "master_key_b_hex": "B4EEC0FFEE11",
  "credit_threshold_cents": 5000,
  "value_block_addr": 40,
  "badge_paths": {
    "low":  "challenges/coffee/badges/credit_low.nfc",
    "high": "challenges/coffee/badges/credit_high.nfc"
  },
  "max_wrong_reads_stage1": 3
}
```

| Key | Description |
|-----|-------------|
| `technician_uid` | Expected iButton UID for Stage 1 (16 hex chars, no dashes) |
| `master_key_b_hex` | Key B for sectors 8–14 (12 hex chars) |
| `credit_threshold_cents` | Minimum credit (in cents) to pass Stage 3 |
| `value_block_addr` | Block number holding the credit value block (40) |
| `max_wrong_reads_stage1` | Wrong-UID streak before showing "Check token" hint |

---

## Running tests

```bash
cd /home/pi/ZeroRange
python3 -m pytest tests/coffee -v
```

Expected: **0 failures**.

---

## File layout

```
ZeroRange/
├── coffee_handler.py               # Main module entry point
├── challenges/coffee/
│   ├── __init__.py
│   ├── stage1_technician.py
│   ├── stage2_dump.py
│   ├── stage3_refill.py
│   ├── value_block.py              # MIFARE value-block encode/decode/validate
│   ├── nfc_to_pm3_eml.py           # Flipper .nfc v4 → PM3 .eml converter
│   └── badges/
│       ├── credit_low.nfc          # 1,50 EUR fixture
│       └── credit_high.nfc         # 50,00 EUR fixture
├── tests/coffee/
│   ├── test_value_block.py
│   ├── test_nfc_to_pm3_eml.py
│   └── test_coffee_handler.py
└── app/web/
    ├── wsgi.py
    ├── routes/coffee.py            # Blueprint + SSE endpoint
    ├── templates/scenarios/coffee.html
    └── static/scenarios/coffee/
        ├── logo.svg
        ├── logo-mono.svg
        ├── stage1.svg
        ├── stage2.svg
        └── stage3.svg
```
