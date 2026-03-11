# Installation Guide

Full installation guide for ZeroRange on a Raspberry Pi.

## Prerequisites

### Hardware
- Raspberry Pi 5 (or Pi 4)
- Adafruit I2C 16x2 RGB LCD Shield
- iButton USB Reader (HID keyboard emulation)
- Proxmark3 (optional, for NFC/RFID challenges)
- HackRF One (optional, for SubGHZ challenges)

### Software
- Raspberry Pi OS (Bookworm or later)
- Python 3.9+
- I2C enabled (`sudo raspi-config` > Interface Options > I2C > Enable)

## Step 1: Clone the repository

```bash
git clone https://github.com/samxplogs/ZeroRange.git
cd ZeroRange
```

## Step 2: Install dependencies

```bash
# System packages
sudo apt-get update
sudo apt-get install -y python3-pip python3-smbus python3-evdev i2c-tools git

# Python packages
pip3 install -r requirements.txt

# LCD support
sudo apt-get install -y python3-adafruit-circuitpython-charlcd
```

## Step 3: Verify hardware

```bash
# Check I2C (should show 0x20, 0x27, or 0x3F)
sudo i2cdetect -y 1

# Check iButton USB reader
ls -la /dev/input/by-id/ | grep c216

# Check Proxmark3 (if connected)
lsusb | grep -i proxmark

# Check HackRF (if connected)
lsusb | grep -i hackrf
```

## Step 4: Run ZeroRange

```bash
sudo python3 zerorange.py
```

> `sudo` is required for access to I2C, USB HID devices, and Proxmark3.

## Auto-start (systemd service)

Install ZeroRange as a service that starts automatically on boot:

```bash
sudo bash install_service.sh
```

This starts 3 services:
1. **ZeroRange** - Main application (LCD + challenges)
2. **HTTP server** (port 8000) - Web interface and documentation
3. **LCD API** (port 5000) - Remote LCD control via REST

### Service management

```bash
sudo systemctl status zerorange    # Check status
sudo systemctl restart zerorange   # Restart
sudo systemctl stop zerorange      # Stop
sudo systemctl start zerorange     # Start
sudo journalctl -u zerorange -f    # View live logs
```

## WiFi Hotspot (optional)

Create a standalone WiFi access point so ZeroRange works anywhere without an existing network:

```bash
sudo bash setup_hotspot.sh
sudo reboot
```

After reboot:
- Connect to WiFi network **ZeroRange** with the password you configured in `setup_hotspot.sh`
- A captive portal opens automatically
- Web interface: `http://10.0.0.1:8000`
- SSH: `ssh sam@10.0.0.1`

> Edit `setup_hotspot.sh` to set your own WiFi password before running it.

## Web Interface

Access the web interface from any device on the same network:

```
http://<RASPBERRY_PI_IP>:8000
```

> The Pi gets its IP via DHCP. Run `hostname -I` on the Pi to find it.
> In hotspot mode, the IP is always `10.0.0.1`.

### Available pages

| Page | URL | Description |
|------|-----|-------------|
| Home | `/home.html` | LCD simulator in real-time |
| Documentation | `/documentation.html` | Full challenge guide |
| Contact | `/contact.html` | Contact info |

### LCD API endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/lcd` | Current LCD state |
| POST | `/lcd/clear` | Clear the LCD |
| POST | `/lcd/write` | Write text to LCD |
| POST | `/button/{num}` | Simulate a button press |

## Deploying from another machine

You can deploy from your computer to the Pi over the network:

```bash
# Copy files to the Pi
scp -r ZeroRange/* user@<RASPBERRY_PI_IP>:/home/sam/ZeroRange/

# SSH into the Pi and install
ssh user@<RASPBERRY_PI_IP>
cd /home/sam/ZeroRange
sudo bash install_service.sh
```

Or use the provided deploy script (edit it first with your Pi's IP):

```bash
cp deploy_to_pi.sh.example deploy_to_pi.sh
# Edit deploy_to_pi.sh with your Pi's IP and credentials
./deploy_to_pi.sh
```

## Troubleshooting

### Service won't start
```bash
sudo journalctl -u zerorange -xe
cd /home/sam/ZeroRange && sudo bash start_all.sh
```

### LCD not detected
```bash
sudo i2cdetect -y 1
# Should show 0x20, 0x27, or 0x3F
```

### iButton not reading
```bash
sudo python3 test_usb_ibutton.py
```

### Ports already in use
```bash
sudo netstat -tlnp | grep -E '(8000|5000)'
sudo pkill -f "http.server 8000"
sudo pkill -f "web_lcd_server"
```

## Uninstall

```bash
sudo systemctl stop zerorange
sudo systemctl disable zerorange
sudo rm /etc/systemd/system/zerorange.service
sudo systemctl daemon-reload
sudo rm -rf /var/log/zerorange /var/run/zerorange
```
