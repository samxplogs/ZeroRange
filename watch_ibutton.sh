#!/bin/bash
# Surveillance visuelle en temps réel des périphériques 1-Wire

echo "=============================================="
echo " SURVEILLANCE iButton - Temps réel"
echo "=============================================="
echo ""
echo "Appuyez sur Ctrl+C pour arrêter"
echo ""
echo "----------------------------------------------"

while true; do
    clear
    echo "=============================================="
    echo " SURVEILLANCE iButton - $(date +%H:%M:%S)"
    echo "=============================================="
    echo ""

    # Vérifier GPIO 6
    if [ -f /sys/class/gpio/gpio6/value ]; then
        gpio6_val=$(cat /sys/class/gpio/gpio6/value 2>/dev/null)
        if [ "$gpio6_val" = "1" ]; then
            echo "✓ GPIO 6 Pull-up: HIGH (3.3V)"
        else
            echo "✗ GPIO 6 Pull-up: LOW (0V) - PROBLÈME!"
        fi
    else
        echo "⚠ GPIO 6 non configuré"
    fi

    echo ""
    echo "Périphériques 1-Wire détectés:"
    echo "----------------------------------------------"

    # Lister les périphériques
    found_ibutton=0
    device_count=0

    for device in /sys/bus/w1/devices/*; do
        device_name=$(basename "$device")

        if [ "$device_name" = "w1_bus_master1" ]; then
            echo "  - $device_name (bus master)"
        elif [[ "$device_name" == 01-* ]]; then
            echo "  ✓✓✓ $device_name ← iButton DÉTECTÉ!"
            found_ibutton=1
            device_count=$((device_count + 1))

            # Lire l'ID si possible
            if [ -f "$device/id" ]; then
                id_value=$(cat "$device/id" 2>/dev/null)
                echo "      ID: $id_value"
            fi
        elif [[ "$device_name" == 00-* ]]; then
            echo "  - $device_name (bruit/parasite)"
            device_count=$((device_count + 1))
        fi
    done

    echo "----------------------------------------------"
    echo ""

    if [ $found_ibutton -eq 1 ]; then
        echo "✓✓✓ STATUS: iButton TROUVÉ!"
    else
        echo "⚠ STATUS: Aucun iButton (seulement $device_count parasite(s))"
        echo ""
        echo "Actions:"
        echo "  1. Maintenir l'iButton fermement sur le probe"
        echo "  2. Vérifier que DATA probe → Pin 29"
        echo "  3. Vérifier que GND probe → Pin 30"
        echo "  4. Nettoyer les contacts du probe"
    fi

    echo ""
    echo "Rafraîchissement dans 1s..."

    sleep 1
done
