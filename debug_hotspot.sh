#!/bin/bash
# Debug script for WiFi hotspot issues

echo "=== ZeroRange Hotspot Diagnostics ==="
echo ""

echo "1. Checking hostapd service status..."
sudo systemctl status hostapd --no-pager
echo ""

echo "2. Checking dnsmasq service status..."
sudo systemctl status dnsmasq --no-pager
echo ""

echo "3. Checking WiFi interface status..."
iwconfig wlan0
echo ""

echo "4. Checking if WiFi is blocked..."
sudo rfkill list
echo ""

echo "5. Checking wlan0 IP configuration..."
ip addr show wlan0
echo ""

echo "6. Checking hostapd configuration..."
if [ -f /etc/hostapd/hostapd.conf ]; then
    echo "hostapd.conf exists:"
    sudo cat /etc/hostapd/hostapd.conf
else
    echo "❌ /etc/hostapd/hostapd.conf NOT FOUND"
fi
echo ""

echo "7. Recent hostapd logs..."
sudo journalctl -u hostapd -n 30 --no-pager
echo ""

echo "8. Recent dnsmasq logs..."
sudo journalctl -u dnsmasq -n 20 --no-pager
echo ""

echo "=== Diagnostics Complete ==="
