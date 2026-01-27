# ZeroRange - Flipper Zero Training System

**Tagline**: "Practice. Master. Repeat."

A legal, controlled environment for practicing Flipper Zero RFID/NFC/iButton capabilities on Raspberry Pi 5.

## Overview

ZeroRange is a CTF-style training system that helps you master your Flipper Zero skills through hands-on challenges. Phase 1 focuses on iButton challenges, with NFC and RFID coming in future phases.

**Current Phase**: Phase 1 - iButton Challenges (40 points total)

## Features

- **Interactive LCD Interface**: 16x2 character display (Adafruit I2C LCD)
- **Progressive Challenges**: 3 iButton challenges ranging from basic to advanced
- **Score Tracking**: SQLite database tracks progress, attempts, and best times
- **Auto-start**: Systemd service for automatic startup on boot
- **Detailed Logging**: Full activity logging for debugging and analysis

## Hardware Requirements

### Required Components

1. **Raspberry Pi 5** (or Pi 4)
   - Raspberry Pi OS Lite 64-bit (no Desktop needed)
   - I2C enabled (bus 1)
   - 1-Wire enabled (GPIO 5)

2. **Adafruit I2C LCD 16x2**
   - 16x2 LCD I2C display with RGB backlight
   - I2C address: 0x27 (or 0x3F depending on model)
   - Note: Buttons not required (challenges can be controlled via software)

3. **iButton Probe**
   - DS9092 or compatible
   - Connected to GPIO 4 (1-Wire DATA)
   - 4.7kΩ pull-up resistor between DATA and 3.3V

4. **Flipper Zero** (for practicing challenges)

### Wiring Diagram

```
Raspberry Pi 5          Adafruit LCD
--------------          ------------
GPIO 2 (SDA)    ----->  SDA
GPIO 3 (SCL)    ----->  SCL
5V              ----->  VCC (or 3.3V, check your LCD)
GND             ----->  GND

Raspberry Pi 5          iButton Probe
--------------          -------------
GPIO 5 (1-Wire) ----->  DATA (with 4.7kΩ pull-up to 3.3V)
GND             ----->  GND
```

## Software Installation

### 1. System Prerequisites

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python dependencies
sudo apt install -y python3 python3-pip i2c-tools

# Install Python packages for Adafruit LCD
pip3 install adafruit-circuitpython-charlcd adafruit-blinka
```

### 2. Enable I2C and 1-Wire

```bash
# Enable I2C
sudo raspi-config
# Select: Interface Options -> I2C -> Yes

# Enable 1-Wire on GPIO 5
sudo nano /boot/config.txt
# Add this line:
dtoverlay=w1-gpio,gpiopin=5

# Reboot
sudo reboot
```

### 3. Verify Hardware

```bash
# Check I2C devices (should see 0x4A)
i2cdetect -y 1

# Check 1-Wire devices
ls -la /sys/bus/w1/devices/
# Should show w1_bus_master1 (and iButton when connected)
```

### 4. Install ZeroRange

```bash
# Clone or copy ZeroRange to Pi
cd /home/pi
git clone https://github.com/yourusername/zerorange.git
cd zerorange

# Create logs directory
mkdir -p logs

# Test the application
python3 zerorange.py
```

### 5. Install Systemd Service (Auto-start)

```bash
# Copy service file to systemd
sudo cp zerorange.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable auto-start
sudo systemctl enable zerorange

# Start service
sudo systemctl start zerorange

# Check status
sudo systemctl status zerorange

# View logs
sudo journalctl -u zerorange -f
```

## Usage

### Navigation

- **BTN1**: Select/Confirm first option
- **BTN2**: Select second option
- **BTN3**: Select third option
- **BTN4**: Settings menu
- **BTN5**: Back/Cancel

### Main Menu

```
ZeroRange v1.0
Score: 0/40

BTN1=iBtn  BTN4=Set
```

### Challenges (Phase 1)

#### Challenge 1: Touch & Read (10 points)
**Difficulty**: ★☆☆
**Objective**: Detect any iButton with your Flipper Zero

**Steps**:
1. Select Challenge 1 from iButton menu
2. Use Flipper Zero to read any iButton key
3. Touch the iButton probe with the Flipper
4. Success when any valid iButton ID is detected

**Timeout**: 60 seconds

---

#### Challenge 2: Clone iButton (15 points)
**Difficulty**: ★★☆
**Objective**: Read a physical iButton key, then emulate it

**Steps**:
1. Select Challenge 2 from iButton menu
2. **Step 1**: Touch probe with physical iButton key (via Flipper)
   - System saves the ID
3. Remove the key
4. **Step 2**: Use Flipper's emulation to clone the saved ID
   - Touch probe again with emulated key
5. Success when emulated ID matches original

**Timeout**: 90 seconds (total)

---

#### Challenge 3: Emulate Specific ID (15 points)
**Difficulty**: ★★★
**Objective**: Create and emulate a specific iButton ID shown on screen

**Steps**:
1. Select Challenge 3 from iButton menu
2. System displays target ID (e.g., `01-A3F5B2C8D1E9`)
3. Manually create this ID in Flipper Zero:
   - Go to iButton → Add Manually
   - Enter the exact ID shown
4. Emulate the key and touch probe
5. Success when emulated ID matches target exactly

**Timeout**: 120 seconds

### Settings Menu

- **View Stats**: See total score, completed challenges, attempts
- **Reset Score**: Clear all progress (requires confirmation)
- **About**: Version and project info

## File Structure

```
/home/pi/zerorange/
├── zerorange.py              # Main application
├── lcd_manager.py            # LCD control
├── ibutton_handler.py        # Challenge logic
├── database.py               # Score persistence
├── config.json               # Configuration
├── zerorange.service         # Systemd service
├── scores.db                 # SQLite database (auto-created)
├── logs/
│   └── zerorange.log         # Application logs
└── README.md                 # This file
```

## Troubleshooting

### LCD not displaying

```bash
# Check I2C connection
i2cdetect -y 1
# Should show device at 0x4A

# Check I2C permissions
sudo usermod -a -G i2c pi
```

### iButton not detected

```bash
# Verify 1-Wire enabled
ls /sys/bus/w1/devices/
# Should show w1_bus_master1

# Check dtoverlay
cat /boot/config.txt | grep w1-gpio
# Should show: dtoverlay=w1-gpio,gpiopin=5

# Test with physical iButton
cat /sys/bus/w1/devices/01-*/id
# Should display iButton ID
```

### Service not starting

```bash
# Check service status
sudo systemctl status zerorange

# View detailed logs
sudo journalctl -u zerorange -n 50

# Check Python errors
python3 /home/pi/zerorange/zerorange.py
```

### Database errors

```bash
# Check database file
ls -la /home/pi/zerorange/scores.db

# Test database directly
sqlite3 /home/pi/zerorange/scores.db "SELECT * FROM challenges;"

# Reset database (WARNING: deletes all progress)
rm /home/pi/zerorange/scores.db
python3 /home/pi/zerorange/zerorange.py
```

## Development

### Running in Development Mode

```bash
# Run with debug logging
cd /home/pi/zerorange
python3 -c "
import logging
logging.basicConfig(level=logging.DEBUG)
from zerorange import main
main()
"
```

### Testing Individual Modules

```bash
# Test LCD
python3 lcd_manager.py

# Test database
python3 database.py

# Test iButton handler
python3 ibutton_handler.py
```

## Future Phases

### Phase 2 (Planned)
- NFC challenges (MIFARE, NTAG)
- RFID 125kHz challenges
- Sub-GHz challenges (if hardware available)

### Phase 3 (Planned)
- WiFi challenges
- Bluetooth challenges
- Multi-stage scenarios

## Legal Notice

ZeroRange is designed for **educational purposes only** in a **controlled environment**. Only practice on hardware you own or have explicit permission to use. Never use these skills on systems you don't own or control.

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Test thoroughly on real hardware
4. Submit a pull request

## License

MIT License - See LICENSE file for details

## Credits

- Created for Flipper Zero enthusiasts
- Inspired by CTF challenges and hacking labs
- Built with Python and Raspberry Pi

## Support

- Issues: https://github.com/yourusername/zerorange/issues
- Wiki: https://github.com/yourusername/zerorange/wiki

---

**Practice. Master. Repeat.**
