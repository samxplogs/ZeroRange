#!/bin/bash
# ZeroRange Installation Script for Raspberry Pi
# Run with: sudo bash install.sh

set -e  # Exit on error

echo "================================================"
echo "ZeroRange Installation Script"
echo "================================================"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "ERROR: Please run as root (sudo bash install.sh)"
    exit 1
fi

# Check if running on Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null; then
    echo "WARNING: This doesn't appear to be a Raspberry Pi"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "Step 1: Installing system dependencies..."
apt update
apt install -y python3 python3-pip i2c-tools sqlite3

echo ""
echo "Step 2: Installing Python packages..."
pip3 install adafruit-circuitpython-charlcd adafruit-blinka --break-system-packages 2>/dev/null || pip3 install adafruit-circuitpython-charlcd adafruit-blinka

echo ""
echo "Step 3: Enabling I2C..."
raspi-config nonint do_i2c 0

echo ""
echo "Step 4: Enabling 1-Wire on GPIO 5..."
if ! grep -q "dtoverlay=w1-gpio,gpiopin=5" /boot/config.txt; then
    echo "dtoverlay=w1-gpio,gpiopin=5" >> /boot/config.txt
    echo "Added 1-Wire overlay to /boot/config.txt"
else
    echo "1-Wire overlay already configured"
fi

echo ""
echo "Step 5: Creating logs directory..."
mkdir -p logs
chmod 755 logs

echo ""
echo "Step 6: Installing systemd service..."
cp zerorange.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable zerorange
echo "Service installed and enabled for auto-start"

echo ""
echo "Step 7: Testing I2C connection..."
if i2cdetect -y 1 | grep -q "27"; then
    echo "SUCCESS: Adafruit LCD found at address 0x27"
elif i2cdetect -y 1 | grep -q "3f"; then
    echo "SUCCESS: Adafruit LCD found at address 0x3F"
else
    echo "WARNING: LCD not detected at 0x27 or 0x3F. Check wiring!"
fi

echo ""
echo "Step 8: Testing 1-Wire interface..."
if [ -d "/sys/bus/w1/devices/" ]; then
    echo "SUCCESS: 1-Wire interface enabled"
    echo "Devices found:"
    ls /sys/bus/w1/devices/
else
    echo "WARNING: 1-Wire interface not ready (may need reboot)"
fi

echo ""
echo "================================================"
echo "Installation Complete!"
echo "================================================"
echo ""
echo "Next steps:"
echo "1. Reboot the Raspberry Pi: sudo reboot"
echo "2. After reboot, service will start automatically"
echo "3. Check status: sudo systemctl status zerorange"
echo "4. View logs: sudo journalctl -u zerorange -f"
echo ""
echo "To test manually before reboot:"
echo "  python3 zerorange.py"
echo ""
echo "To start service now (without reboot):"
echo "  sudo systemctl start zerorange"
echo ""
