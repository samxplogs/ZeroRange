# Garage Signal Fixtures

`press_N.sub` and `press_N_plus_1.sub` are Flipper Zero `.sub` v1 files encoding
two consecutive rolling-code press frames from the fictional "Sam Garage" remote.

- **Frequency:** 433.92 MHz
- **Modulation:** OOK (On-Off Keying)
- **Symbol period:** 250 µs
- **Counter:** `press_N` = initial_counter (default 100); `press_N_plus_1` = 101

## Frame format

See `challenges/garage/rolling_scheme.md` for the full spec.

## Regenerating fixtures

```bash
cd /path/to/ZeroRange
python3 - <<'EOF'
from challenges.garage.rolling_scheme import write_sub_file
import json, pathlib

cfg = json.loads(pathlib.Path("config.json").read_text())["garage"]["rolling"]
dev_id = bytes.fromhex(cfg["device_id_hex"].replace(" ", ""))
seed   = bytes.fromhex(cfg["seed_hex"].replace(" ", ""))
freq   = cfg["freq_hz"]
ctr    = cfg["initial_counter"]

write_sub_file("challenges/garage/signals/press_N.sub",          dev_id, ctr,     seed, freq)
write_sub_file("challenges/garage/signals/press_N_plus_1.sub",   dev_id, ctr + 1, seed, freq)
print("Done.")
EOF
```
