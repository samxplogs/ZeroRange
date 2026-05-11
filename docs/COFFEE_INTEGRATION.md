# Coffee Module Integration Guide

> **Disclaimer:** Sam BrewMaster Pro is an entirely fictional brand created for
> ZeroRange. Any resemblance to real coffee/vending badge systems, manufacturers,
> or deployments is purely coincidental. This module exists for hands-on security
> training in a controlled environment only.

---

## Overview

The Coffee module (`coffee_handler.py`) chains three scored stages around a fictional
"Sam BrewMaster Pro" coffee station, plus a **Prep Badges** tool for trainer setup.

| Hardware | Purpose |
|----------|---------|
| iButton USB HID reader | Stage 1 — read technician maintenance token |
| Proxmark3 | Prep, Stage 2, Stage 3 — badge emulation and read-back |

---

## LCD menu flow

From the root menu, scroll to **Coffee** (after IR) and press **SELECT**.

```
Coffee  0/30
SEL=Start L=Back
```

Pressing SELECT launches the Coffee sub-menu with four items:

```
>Stage1:iButton ✓    ← checkmark when completed
>Stage2:Crack
>Stage3:Refill
>Prep Badges         ← always accessible, no prerequisite
 U/D SEL=Go 10/30
```

Navigate with **▲ UP / ▼ DOWN**, launch with **● SELECT**, return to root menu with **◄ LEFT**.

---

## Prep Badges

**Purpose:** lets a trainer (or learner) have both reference badges saved on their
Flipper Zero (or any NFC device) before the session begins.  No points, no prerequisites.

### Selecting a badge

```
>Low  1,50 EUR       ← scroll with ▲▼
>High 50,00 EUR
 U/D SEL=Go ◄=Bk
```

Press **SELECT** to start emulating the chosen badge on the Proxmark3.

### During emulation

```
Emul: Low  1,50 EUR
SEL=KeyB  ◄=Stop
```

- The PM3 broadcasts the badge continuously.
- Point the Flipper Zero (NFC → Read) at the PM3 antenna and save the card.
- Any other ISO14443A reader works the same way.

### Revealing Key B on demand

Press **● SELECT** at any time to toggle Key B visibility on the LCD:

```
B4 EE C0 FF EE 11    ← key displayed so you can type it into Flipper
SEL=Hide  ◄=Stop
```

Press **SELECT** again to hide it.  Press **◄** to stop emulation and return.

### Badge reference

| Badge | UID | Credit | Key A (sectors 0–7) | Key B (sectors 8–14) |
|-------|-----|-------:|---------------------|----------------------|
| Low   | `04 A3 F5 B2` | 1,50 EUR | `FFFFFFFFFFFF` | `B4EEC0FFEE11` |
| High  | `04 8C 2F E1` | 50,00 EUR | `FFFFFFFFFFFF` | `B4EEC0FFEE11` |

Both are MIFARE Classic 1K, SAK `08`, ATQA `00 04`.

---

## Stage 1 — Technician Token (10 pts)

1. LCD: *Pull maint token* → place the DS1990 iButton on the USB HID reader.
2. On UID match: *Token OK! +10pts* → the LCD reveals the leaked Key B:

   ```
   Leaked log:
   KeyB=B4 EE C0 FF
   Sectors 8-14:
   B4 EE C0 FF EE 11
   ```

3. Three consecutive wrong reads show "Check right token" before retrying.
4. Stage is idempotent — re-running a completed stage shows the leak screen again without re-awarding points.

---

## Stage 2 — Crack & Dump Badge (10 pts)

1. PM3 emulates `challenges/coffee/badges/credit_low.nfc`.
2. LCD: *PM3 emulates badge. Read it!*
3. Learner uses Flipper Zero — add Key B `B4EEC0FFEE11` to the Flipper user
   dictionary (or use Mfkey32 against the emulation).

Two completion paths:

- **Auto-detect:** ZeroRange monitors the `hf mf sim` log for Key B auth events on
  sectors 8–14. When all seven sectors appear, the stage completes automatically.
- **Manual confirm:** Press **● SELECT** ("I'm done") — ZeroRange reads sectors 8–14
  via PM3 to verify all are accessible with Key B, then marks complete.

> **Tip:** Use **Prep Badges** before the session to save `credit_low.nfc` on the
> Flipper. Learners can then diff it against `credit_high.nfc` to discover the
> value-block encoding without needing to dump it from scratch.

---

## Stage 3 — Top Up Balance (10 pts)

1. LCD: *Need >=50,00 EUR / Present to PM3*
2. Press **● SELECT** when your forged card or Flipper emulation is on the PM3 antenna.
3. ZeroRange reads block 40 (sector 10, block 0) with Key B and validates:
   - **Structure:** V == V copy, ~V correct, addr/inv-addr consistent.
   - **Value:** decoded cents ≥ 5000 (configurable).

Precise rejection messages:

| LCD message | Meaning |
|-------------|---------|
| `Bad ~V` | Bytes 4–7 are not the bitwise complement of bytes 0–3 |
| `Bad addr` | Addr or inv-addr bytes inconsistent (bytes 12–15) |
| `Value too low` | Decoded credit is below the 50,00 EUR threshold |
| `Auth failed!` | PM3 could not authenticate — wrong key or wrong card type |

The web companion's credit counter animates to the observed value before showing
pass or fail, making the "I tried 49,99 EUR and it rejected" moment visible.

---

## Web companion

The web companion is a Flask app that runs as a **separate systemd service**
(`zerorange-web`).  The LCD main loop and Flask are fully independent — if Flask
crashes, the LCD keeps working.

### Status

```bash
sudo systemctl status zerorange-web
```

### Enable / disable

```bash
# Start now and on every boot
sudo systemctl enable --now zerorange-web

# Stop (keeps enabled at boot)
sudo systemctl stop  zerorange-web

# Disable completely
sudo systemctl disable --now zerorange-web
```

### Accessing the web companion

Connect to the ZeroRange Wi-Fi hotspot, then open:

```
http://192.168.1.193:8080/
```

- Scenario list: `http://192.168.1.193:8080/`
- Coffee view:   `http://192.168.1.193:8080/scenarios/coffee/`
- SSE stream:    `http://192.168.1.193:8080/scenarios/coffee/events`

The Coffee page updates in lockstep with the LCD via Server-Sent Events — no
manual refresh needed.

### SSE event reference

| Event JSON | When emitted |
|------------|-------------|
| `{"stage": 1, "status": "success", "points": 10}` | Stage 1 completed |
| `{"stage": 2, "status": "success", "points": 10}` | Stage 2 completed |
| `{"stage": 3, "status": "success", "points": 10}` | Stage 3 completed |
| `{"event": "credit_observed", "value_cents": N}` | Each Stage 3 read-back (pass or fail) |
| `{"event": "credit_observed", "value_cents": null, "error": "…"}` | Stage 3 auth or structure failure |

---

## Wiring and hardware notes

- **iButton HID reader:** enumerates as `/dev/input/event*`. ZeroRange auto-detects
  the first device whose name contains "keyboard", "hid", or "ibutton". If
  auto-detection fails, edit `_find_hid_device()` in `coffee_handler.py`.
- **Proxmark3:** `/dev/ttyACM0` by default (set in `proxmark_handler.py`).
  Disconnecting it between stages surfaces a "Proxmark3 not detected" screen with
  a retry option — no traceback.
- **Cleanup:** PM3 emulation is always stopped on stage exit, even if `zerorange.py`
  is killed mid-session (`EmulationHandle.stop()` runs in a `finally` block).
  Verify with `pgrep proxmark3` — there should be no orphaned process.

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
| `credit_threshold_cents` | Minimum credit in cents to pass Stage 3 (default 5000 = 50,00 €) |
| `value_block_addr` | Block number of the credit value block (default 40) |
| `badge_paths.low` | Path to the low-credit reference badge |
| `badge_paths.high` | Path to the high-credit reference badge |
| `max_wrong_reads_stage1` | Wrong-UID streak before showing the "Check token" hint |

---

## Running tests

```bash
cd /home/sam/ZeroRange
python3 -m unittest discover -s tests/coffee -v
```

Expected: **42 tests, 0 failures**.

---

## Trainer quick-start checklist

Before a session:

1. Connect iButton USB reader and Proxmark3 to the Pi.
2. Power on the Pi — `zerorange.service` and `zerorange-web` start automatically.
3. On the LCD: navigate to **Coffee → Prep Badges → Low** and hold the Proxmark3
   antenna near each learner's Flipper Zero so they can save `credit_low.nfc`.
4. Repeat for **Prep Badges → High** so learners have the reference dump to diff.
5. Touch the technician DS1990 iButton to the USB reader to confirm it reads correctly
   (use **Coffee → Stage 1** — it shows the UID without re-awarding points if already done).
6. Brief learners: their goal is to forge a badge that passes Stage 3 (≥ 50,00 EUR).

---

## File layout

```
ZeroRange/
├── coffee_handler.py                  # Module entry point + HID adapter + menu
├── challenges/coffee/
│   ├── __init__.py
│   ├── prep_badges.py                 # Prep Badges tool (PM3 emulation, Key B reveal)
│   ├── stage1_technician.py           # iButton UID match + Key B leak
│   ├── stage2_dump.py                 # PM3 emulation + sector log monitoring
│   ├── stage3_refill.py               # PM3 read-back + value-block validation
│   ├── value_block.py                 # MIFARE value-block encode/decode/validate
│   ├── nfc_to_pm3_eml.py              # Flipper .nfc v4 → PM3 .eml converter
│   └── badges/
│       ├── credit_low.nfc             # 1,50 EUR reference badge
│       └── credit_high.nfc            # 50,00 EUR reference badge
├── tests/coffee/
│   ├── test_value_block.py
│   ├── test_nfc_to_pm3_eml.py
│   └── test_coffee_handler.py
├── app/web/
│   ├── wsgi.py                        # Flask entry point (port 8080)
│   ├── routes/coffee.py               # Blueprint + SSE endpoint
│   ├── templates/scenarios/coffee.html
│   └── static/scenarios/coffee/
│       ├── logo.svg
│       ├── logo-mono.svg
│       ├── stage1.svg
│       ├── stage2.svg
│       └── stage3.svg
├── zerorange-web.service              # systemd unit for web companion
└── docs/
    └── COFFEE_INTEGRATION.md          # This file
```
