#!/bin/bash
# ZeroRange - Désactivation du hotspot WiFi
# Retour en mode client WiFi normal

set -e

if [ "$EUID" -ne 0 ]; then
    echo "Ce script doit être exécuté avec sudo"
    exit 1
fi

echo "=== Désactivation du hotspot WiFi ZeroRange ==="
echo ""

# Stop services
echo "Arrêt des services..."
systemctl stop hostapd
systemctl stop dnsmasq
systemctl stop lighttpd

# Disable services
echo "Désactivation des services..."
systemctl disable hostapd
systemctl disable dnsmasq
systemctl disable lighttpd

# Restore original dhcpcd.conf
echo "Restauration de la configuration réseau..."
if [ -f /etc/dhcpcd.conf.backup ]; then
    cp /etc/dhcpcd.conf.backup /etc/dhcpcd.conf
    echo "Configuration réseau restaurée"
else
    echo "⚠️  Pas de backup trouvé, configuration manuelle nécessaire"
fi

# Restore original dnsmasq.conf
if [ -f /etc/dnsmasq.conf.backup ]; then
    mv /etc/dnsmasq.conf.backup /etc/dnsmasq.conf
    echo "Configuration DNS restaurée"
fi

# Restart networking
echo "Redémarrage du réseau..."
systemctl restart dhcpcd

echo ""
echo "=== Hotspot désactivé! ==="
echo ""
echo "Le Raspberry Pi est maintenant en mode client WiFi."
echo "Connectez-vous à votre réseau WiFi habituel avec:"
echo "  sudo raspi-config"
echo "  > System Options > Wireless LAN"
echo ""
echo "Ou redémarrez pour appliquer les changements:"
echo "  sudo reboot"
echo ""
