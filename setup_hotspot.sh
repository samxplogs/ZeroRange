#!/bin/bash
# ZeroRange - Configuration du hotspot WiFi
# Crée un point d'accès WiFi "ZeroRange" avec portail captif

set -e

if [ "$EUID" -ne 0 ]; then
    echo "Ce script doit être exécuté avec sudo"
    exit 1
fi

echo "=== Configuration du hotspot WiFi ZeroRange ==="
echo ""

# Configuration
SSID="ZeroRange"
PASSWORD="your_password_here"
INTERFACE="wlan0"
IP_ADDRESS="10.0.0.1"
DHCP_RANGE_START="10.0.0.10"
DHCP_RANGE_END="10.0.0.50"

# Install required packages
echo "Installation des paquets nécessaires..."
apt-get update
apt-get install -y hostapd dnsmasq iptables-persistent

# Stop services
echo "Arrêt des services..."
systemctl stop hostapd
systemctl stop dnsmasq

# Configure static IP for wlan0
echo "Configuration de l'IP statique..."
cat > /etc/dhcpcd.conf.zerorange << EOF
# ZeroRange hotspot configuration
interface $INTERFACE
    static ip_address=$IP_ADDRESS/24
    nohook wpa_supplicant
EOF

# Backup original dhcpcd.conf if not already done
if [ ! -f /etc/dhcpcd.conf.backup ]; then
    cp /etc/dhcpcd.conf /etc/dhcpcd.conf.backup
fi

# Append ZeroRange config to dhcpcd.conf
cat /etc/dhcpcd.conf.zerorange >> /etc/dhcpcd.conf

# Configure hostapd
echo "Configuration de hostapd..."
cat > /etc/hostapd/hostapd.conf << EOF
# ZeroRange WiFi Hotspot Configuration
interface=$INTERFACE
driver=nl80211

# Network configuration
ssid=$SSID
hw_mode=g
channel=7
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0

# Security configuration
wpa=2
wpa_passphrase=$PASSWORD
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
EOF

# Point hostapd to config file
echo 'DAEMON_CONF="/etc/hostapd/hostapd.conf"' > /etc/default/hostapd

# Configure dnsmasq
echo "Configuration de dnsmasq..."
# Backup original dnsmasq.conf
if [ ! -f /etc/dnsmasq.conf.backup ]; then
    mv /etc/dnsmasq.conf /etc/dnsmasq.conf.backup
fi

cat > /etc/dnsmasq.conf << EOF
# ZeroRange DNS and DHCP configuration
interface=$INTERFACE
dhcp-range=$DHCP_RANGE_START,$DHCP_RANGE_END,255.255.255.0,24h

# DNS configuration
# Redirect all DNS queries to our captive portal
address=/#/$IP_ADDRESS

# Don't forward queries without a domain part
domain-needed
bogus-priv

# Log queries
log-queries
log-facility=/var/log/dnsmasq.log
EOF

# Configure captive portal (lighttpd)
echo "Installation du serveur web pour le portail captif..."
apt-get install -y lighttpd

# Configure lighttpd to redirect to our web interface
cat > /etc/lighttpd/lighttpd.conf << 'EOF'
server.modules = (
    "mod_access",
    "mod_alias",
    "mod_redirect",
    "mod_rewrite"
)

server.document-root = "/var/www/html"
server.upload-dirs = ( "/var/cache/lighttpd/uploads" )
server.errorlog = "/var/log/lighttpd/error.log"
server.pid-file = "/run/lighttpd.pid"
server.username = "www-data"
server.groupname = "www-data"
server.port = 80

index-file.names = ( "index.html" )

# Redirect all requests to captive portal
$HTTP["host"] !~ "^10\.0\.0\.1" {
    url.redirect = ( "^/(.*)" => "http://10.0.0.1:8000/home.html" )
}

# For requests to our IP, proxy to Python HTTP server
$HTTP["host"] == "10.0.0.1" {
    url.redirect = ( "^/$" => "http://10.0.0.1:8000/home.html" )
}

mimetype.assign = (
    ".html" => "text/html",
    ".txt" => "text/plain",
    ".jpg" => "image/jpeg",
    ".png" => "image/png",
    ".css" => "text/css",
    ".js" => "application/javascript"
)
EOF

# Create captive portal detection files (for Apple, Android, Windows)
mkdir -p /var/www/html
cat > /var/www/html/index.html << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta http-equiv="refresh" content="0;url=http://10.0.0.1:8000/home.html">
    <title>ZeroRange - Redirection</title>
</head>
<body>
    <p>Redirection vers ZeroRange...</p>
    <p>Si vous n'êtes pas redirigé, <a href="http://10.0.0.1:8000/home.html">cliquez ici</a></p>
</body>
</html>
EOF

# Hotspot detection files
cat > /var/www/html/hotspot-detect.html << EOF
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2//EN">
<HTML>
<HEAD><TITLE>Success</TITLE></HEAD>
<BODY>Success</BODY>
</HTML>
EOF

cat > /var/www/html/generate_204 << EOF
HTTP/1.1 302 Found
Location: http://10.0.0.1:8000/home.html
EOF

cat > /var/www/html/connecttest.txt << EOF
Microsoft Connect Test
EOF

# Enable IP forwarding (optional, if you want internet sharing later)
echo "Activation du forwarding IP..."
sed -i 's/#net.ipv4.ip_forward=1/net.ipv4.ip_forward=1/' /etc/sysctl.conf
sysctl -p

# Configure firewall to allow SSH
echo "Configuration du firewall..."
iptables -A INPUT -p tcp --dport 22 -j ACCEPT
iptables -A INPUT -p tcp --dport 8000 -j ACCEPT
iptables -A INPUT -p tcp --dport 5000 -j ACCEPT
iptables -A INPUT -p tcp --dport 80 -j ACCEPT
netfilter-persistent save

# Enable services
echo "Activation des services..."
systemctl unmask hostapd
systemctl enable hostapd
systemctl enable dnsmasq
systemctl enable lighttpd

# Start services
echo "Démarrage des services..."
systemctl restart dhcpcd
sleep 2
systemctl start hostapd
systemctl start dnsmasq
systemctl start lighttpd

echo ""
echo "=== Configuration terminée! ==="
echo ""
echo "Détails du hotspot WiFi:"
echo "  SSID: $SSID"
echo "  Mot de passe: $PASSWORD"
echo "  IP du Raspberry Pi: $IP_ADDRESS"
echo ""
echo "Accès:"
echo "  Interface web: http://$IP_ADDRESS:8000"
echo "  API LCD: http://$IP_ADDRESS:5000"
echo "  SSH: ssh sam@$IP_ADDRESS"
echo ""
echo "Redémarrez le Raspberry Pi pour appliquer tous les changements:"
echo "  sudo reboot"
echo ""
