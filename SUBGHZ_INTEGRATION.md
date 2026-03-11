# SubGHZ Integration - HackRF One

## Overview

ZeroRange now supports SubGHZ challenges using the HackRF One SDR (Software Defined Radio). This module allows you to detect, capture, replay, and analyze RF signals in the SubGHZ band (typically 300MHz - 928MHz).

## Hardware Requirements

- **HackRF One** SDR device
- USB connection to Raspberry Pi
- (Optional) Antenna suitable for target frequencies (433MHz/868MHz/915MHz)

## Software Dependencies

### Install HackRF Tools

```bash
# Update package list
sudo apt update

# Install HackRF tools
sudo apt install -y hackrf libhackrf-dev

# Install additional SDR tools (optional but recommended)
sudo apt install -y rtl-433 gnuradio

# Verify installation
hackrf_info
```

### Python Dependencies

No additional Python packages are required - the handler uses subprocess to interface with HackRF command-line tools.

## USB Setup

### Udev Rules for HackRF

Create a udev rule to allow non-root access:

```bash
sudo nano /etc/udev/rules.d/53-hackrf.rules
```

Add the following content:

```
ATTR{idVendor}=="1d50", ATTR{idProduct}=="604b", SYMLINK+="hackrf-jawbreaker-%k", MODE="660", GROUP="plugdev"
ATTR{idVendor}=="1d50", ATTR{idProduct}=="6089", SYMLINK+="hackrf-one-%k", MODE="660", GROUP="plugdev"
```

Reload rules:

```bash
sudo udevadm control --reload-rules
sudo udevadm trigger
```

Add your user to the plugdev group:

```bash
sudo usermod -aG plugdev $USER
```

Reboot or re-login for changes to take effect.

## Challenges

The SubGHZ module provides 3 challenges (10 points each):

### Challenge 10: Detect Signal
- **Objective**: Detect any RF signal in the 433MHz band
- **Timeout**: 60 seconds
- **How to complete**:
  1. Use a remote control (garage door, car key, doorbell)
  2. Press the button while within range of HackRF antenna
  3. ZeroRange will detect the signal when strength exceeds threshold

### Challenge 11: Record & Replay
- **Objective**: Capture a signal and replay it
- **Timeout**: 45 seconds capture + replay
- **How to complete**:
  1. Press your RF transmitter button during capture phase
  2. ZeroRange records the signal
  3. Signal is automatically replayed 3 times
  4. Verify replay worked on your target device

### Challenge 12: Signal Analysis
- **Objective**: Capture and analyze a signal's characteristics
- **Timeout**: 60 seconds
- **How to complete**:
  1. Transmit any RF signal
  2. ZeroRange captures and analyzes the signal
  3. Displays detected protocol/modulation information

## Architecture

```
+------------------+     +-------------------+     +------------------+
|   ZeroRange      |---->|  SubGHZHandler    |---->|  HackRFHandler   |
|   (Main App)     |     |  (Challenges)     |     |  (Hardware I/F)  |
+------------------+     +-------------------+     +------------------+
                                                           |
                                                           v
                                                   +------------------+
                                                   | hackrf_transfer  |
                                                   | rtl_433 (opt)    |
                                                   +------------------+
```

### Files

- `hackrf_handler.py` - Low-level HackRF interface using subprocess
- `subghz_handler.py` - Challenge logic and LCD interaction

## Configuration

### Default Frequencies

The handler supports these common SubGHZ frequencies:

| Band | Frequency | Common Uses |
|------|-----------|-------------|
| 315MHz | 315,000,000 Hz | US garage doors, car keys |
| 433MHz | 433,920,000 Hz | EU garage doors, remotes, sensors |
| 868MHz | 868,000,000 Hz | EU smart home, LoRa |
| 915MHz | 915,000,000 Hz | US LoRa, ISM band |

Default target: **433.92 MHz**

### Signal Detection Parameters

```python
# In subghz_handler.py
TARGET_FREQUENCY = 433920000  # 433.92 MHz
DETECTION_THRESHOLD = -55     # dBm

# In hackrf_handler.py
DEFAULT_SAMPLE_RATE = 2000000  # 2 MHz
DEFAULT_LNA_GAIN = 32          # 0-40 dB
DEFAULT_VGA_GAIN = 20          # 0-62 dB
DEFAULT_TX_GAIN = 47           # 0-47 dB (for replay)
```

## Testing

### Test HackRF Connection

```bash
# Check if HackRF is detected
hackrf_info

# Expected output:
# hackrf_info version: ...
# Serial number: ...
# Board ID Number: 2 (HackRF One)
```

### Test Signal Capture

```bash
# Capture 5 seconds at 433.92 MHz
hackrf_transfer -r test.raw -f 433920000 -s 2000000 -n 10000000

# Check file was created
ls -la test.raw
```

### Test Replay

```bash
# Replay captured signal
hackrf_transfer -t test.raw -f 433920000 -s 2000000 -x 47
```

### Run Handler Test

```bash
cd /path/to/ZeroRange
python3 hackrf_handler.py   # Tests HackRF handler
python3 subghz_handler.py   # Tests SubGHZ handler (needs mock LCD)
```

## Troubleshooting

### HackRF Not Detected

1. Check USB connection
2. Verify udev rules are installed
3. Check user is in `plugdev` group
4. Try `sudo hackrf_info`

### Signal Not Detected

1. Check antenna is connected
2. Verify frequency matches your transmitter
3. Move transmitter closer to antenna
4. Increase LNA/VGA gain values
5. Lower detection threshold

### Replay Not Working

1. Ensure original signal was captured correctly
2. Check TX gain is sufficient
3. Verify you're replaying at correct frequency
4. Some protocols have rolling codes (won't work with simple replay)

## Security Notice

This module is intended for **educational purposes** and authorized security research only.

**Legal considerations:**
- Only test on devices you own or have explicit permission to test
- RF transmission may be regulated in your jurisdiction
- Do not interfere with emergency services or critical infrastructure
- Rolling code systems (modern car keys, etc.) are designed to prevent replay attacks

## Database Schema

SubGHZ challenges are stored in the database with IDs 10-12:

```sql
-- SubGHZ challenges (10-12)
(10, 'subghz', 'Detect Signal', 'Capture RF signal', 10, 0, NULL)
(11, 'subghz', 'Record & Replay', 'Capture and replay', 10, 0, NULL)
(12, 'subghz', 'Signal Analysis', 'Analyze RF protocol', 10, 0, NULL)
```

## Future Enhancements

Potential improvements for future versions:

- [ ] Support for additional frequency bands
- [ ] Protocol-specific decoding (garage door brands, etc.)
- [ ] Signal visualization on web interface
- [ ] Save/load captured signals
- [ ] Brute force attack challenges (for educational purposes)
- [ ] Integration with GNU Radio for advanced signal processing
