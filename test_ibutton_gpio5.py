#!/usr/bin/env python3
"""
Test script for iButton reader on GPIO 5
Verify 1-Wire interface and iButton detection
Uses GPIO 6 (Pin 31) as pull-up source
"""

import os
import time
import sys

# Importer le helper GPIO
try:
    from gpio_helper import setup_gpio6_pullup
except ImportError:
    # Fallback si gpio_helper n'est pas disponible
    def setup_gpio6_pullup():
        """Fallback: essayer configuration basique"""
        try:
            import RPi.GPIO as GPIO
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            GPIO.setup(6, GPIO.OUT)
            GPIO.output(6, GPIO.HIGH)
            return True
        except:
            return False

# Configuration for GPIO 5
W1_BASE = "/sys/bus/w1/devices/"
GPIO_PIN = 5

def check_w1_interface():
    """Verify 1-Wire interface is enabled"""
    print("=" * 60)
    print("Test iButton - GPIO 5 avec pull-up GPIO 6")
    print("=" * 60)
    print()

    print("[1/5] Configuration pull-up GPIO 6 (Pin 31)...")
    if setup_gpio6_pullup():
        print("✓ GPIO 6 configuré en HIGH (3.3V)")

    print()
    print("[2/5] Vérification de l'interface 1-Wire...")
    if not os.path.exists(W1_BASE):
        print("❌ ERREUR: Interface 1-Wire non trouvée!")
        print()
        print("Solution:")
        print("1. Ouvrir /boot/config.txt:")
        print("   sudo nano /boot/config.txt")
        print()
        print("2. Ajouter cette ligne:")
        print("   dtoverlay=w1-gpio,gpiopin=5")
        print()
        print("3. Redémarrer:")
        print("   sudo reboot")
        return False

    print("✓ Interface 1-Wire trouvée")
    return True

def list_w1_devices():
    """List all 1-Wire devices"""
    print()
    print("[3/5] Liste des périphériques 1-Wire...")

    try:
        devices = os.listdir(W1_BASE)
        print(f"✓ Trouvé {len(devices)} périphérique(s):")
        for device in devices:
            print(f"  - {device}")
        return devices
    except Exception as e:
        print(f"❌ Erreur lors de la lecture: {e}")
        return []

def detect_ibutton_devices(devices):
    """Detect iButton devices (family code 01)"""
    print()
    print("[4/5] Recherche d'iButtons (code famille 01-)...")

    ibuttons = [d for d in devices if d.startswith("01-")]

    if not ibuttons:
        print("⚠ Aucun iButton détecté")
        print()
        print("Pour tester:")
        print("- Touchez le probe avec un iButton physique")
        print("- Ou utilisez Flipper Zero en mode émulation iButton")
        return None

    print(f"✓ Trouvé {len(ibuttons)} iButton(s):")
    for ib in ibuttons:
        print(f"  - {ib}")

    return ibuttons[0]

def read_ibutton_id(device_name):
    """Read iButton ID from device"""
    print()
    print("[5/5] Lecture de l'ID iButton...")

    try:
        # Try reading from 'id' file
        id_path = os.path.join(W1_BASE, device_name, "id")
        if os.path.exists(id_path):
            with open(id_path, 'r') as f:
                ibutton_id = f.read().strip()
            print(f"✓ ID détecté: {ibutton_id}")
            return ibutton_id
        else:
            # Fallback to device name
            print(f"✓ ID détecté: {device_name}")
            return device_name

    except Exception as e:
        print(f"❌ Erreur lors de la lecture de l'ID: {e}")
        return None

def continuous_monitoring():
    """Monitor for iButton continuously"""
    print()
    print("=" * 60)
    print("Mode surveillance continue")
    print("Appuyez sur Ctrl+C pour arrêter")
    print("=" * 60)
    print()

    last_id = None

    try:
        while True:
            # Check for devices
            devices = os.listdir(W1_BASE)
            ibuttons = [d for d in devices if d.startswith("01-")]

            if ibuttons:
                current_id = ibuttons[0]
                if current_id != last_id:
                    # New iButton detected
                    id_path = os.path.join(W1_BASE, current_id, "id")
                    if os.path.exists(id_path):
                        with open(id_path, 'r') as f:
                            display_id = f.read().strip()
                    else:
                        display_id = current_id

                    timestamp = time.strftime("%H:%M:%S")
                    print(f"[{timestamp}] ✓ iButton détecté: {display_id}")
                    last_id = current_id
            else:
                if last_id is not None:
                    timestamp = time.strftime("%H:%M:%S")
                    print(f"[{timestamp}] - iButton retiré")
                    last_id = None

            time.sleep(0.3)  # Poll every 300ms

    except KeyboardInterrupt:
        print()
        print("Arrêt de la surveillance")

def main():
    """Main test function"""
    # Step 1: Check 1-Wire interface
    if not check_w1_interface():
        sys.exit(1)

    # Step 2: List devices
    devices = list_w1_devices()
    if not devices:
        print()
        print("Aucun périphérique 1-Wire trouvé")
        sys.exit(1)

    # Step 3: Detect iButtons
    ibutton = detect_ibutton_devices(devices)

    # Step 4: Read ID if found
    if ibutton:
        ibutton_id = read_ibutton_id(ibutton)

        print()
        print("=" * 60)
        print("✓ TEST RÉUSSI!")
        print(f"iButton ID: {ibutton_id}")
        print("Le lecteur iButton fonctionne correctement sur GPIO 5")
        print("=" * 60)

    # Ask if user wants continuous monitoring
    print()
    response = input("Voulez-vous surveiller en continu? (o/N): ").strip().lower()
    if response in ['o', 'oui', 'y', 'yes']:
        continuous_monitoring()

if __name__ == "__main__":
    main()
