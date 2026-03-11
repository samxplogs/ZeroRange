#!/bin/bash
# ZeroRange - Script d'installation du service systemd
# À exécuter sur le Raspberry Pi

set -e

echo "=== Installation du service ZeroRange ==="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Ce script doit être exécuté avec sudo"
    exit 1
fi

INSTALL_DIR="/home/sam/ZeroRange"
SERVICE_FILE="/etc/systemd/system/doublezero.service"

# Make scripts executable
echo "Rendre les scripts exécutables..."
chmod +x "$INSTALL_DIR/start_all.sh"
chmod +x "$INSTALL_DIR/stop_all.sh"

# Copy service file
echo "Installation du fichier de service..."
cp "$INSTALL_DIR/doublezero.service" "$SERVICE_FILE"

# Create log and PID directories
echo "Création des répertoires de logs..."
mkdir -p /var/log/doublezero
mkdir -p /var/run/doublezero
chown -R sam:sam /var/log/doublezero
chown -R sam:sam /var/run/doublezero

# Reload systemd
echo "Rechargement de systemd..."
systemctl daemon-reload

# Enable service to start at boot
echo "Activation du service au démarrage..."
systemctl enable doublezero.service

# Stop any running instance
echo "Arrêt des instances en cours..."
systemctl stop doublezero.service 2>/dev/null || true
pkill -9 -f "python3.*doublezero" 2>/dev/null || true
pkill -9 -f "http.server 8000" 2>/dev/null || true
pkill -9 -f "web_lcd_server" 2>/dev/null || true
sleep 2

# Start the service
echo "Démarrage du service..."
systemctl start doublezero.service

# Show status
echo ""
echo "=== Status du service ==="
systemctl status doublezero.service --no-pager

echo ""
echo "=== Installation terminée! ==="
echo ""
echo "Commandes utiles:"
echo "  sudo systemctl status doublezero   - Voir le statut"
echo "  sudo systemctl restart doublezero  - Redémarrer"
echo "  sudo systemctl stop doublezero     - Arrêter"
echo "  sudo systemctl start doublezero    - Démarrer"
echo "  sudo journalctl -u doublezero -f   - Voir les logs en temps réel"
echo ""
echo "Services lancés:"
echo "  - Application principale ZeroRange (LCD + Boutons)"
echo "  - Serveur HTTP sur http://$(hostname -I | awk '{print $1}'):8000"
echo "  - API LCD sur http://$(hostname -I | awk '{print $1}'):5000"
echo ""

# Ask about WiFi hotspot
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📡 Configuration optionnelle: Hotspot WiFi"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "ZeroRange peut créer son propre réseau WiFi (mode hotspot)."
echo "Cela permet d'utiliser ZeroRange PARTOUT sans réseau existant!"
echo ""
echo "Fonctionnalités:"
echo "  ✅ Point d'accès WiFi 'ZeroRange'"
echo "  ✅ Portail captif automatique"
echo "  ✅ Accès SSH sans configuration (10.0.0.1)"
echo "  ✅ Mode 100% portable et autonome"
echo ""
read -p "Voulez-vous activer le hotspot WiFi? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "Installation du hotspot WiFi..."
    bash "$INSTALL_DIR/setup_hotspot.sh"
    echo ""
    echo "✅ Hotspot WiFi configuré!"
    echo ""
    echo "Après le redémarrage:"
    echo "  - SSID: ZeroRange"
    echo "  - Mot de passe: (configured in setup_hotspot.sh)"
    echo "  - IP: 10.0.0.1"
    echo "  - Interface web: http://10.0.0.1:8000"
    echo "  - SSH: ssh sam@10.0.0.1"
    echo ""
    read -p "Redémarrer maintenant pour activer le hotspot? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Redémarrage dans 5 secondes..."
        sleep 5
        reboot
    else
        echo ""
        echo "⚠️  Redémarrez manuellement pour activer le hotspot:"
        echo "    sudo reboot"
    fi
else
    echo ""
    echo "Hotspot WiFi non installé."
    echo "Vous pouvez l'activer plus tard avec:"
    echo "  sudo bash $INSTALL_DIR/setup_hotspot.sh"
fi
echo ""
