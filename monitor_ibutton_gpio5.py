#!/usr/bin/env python3
"""
Surveillance continue iButton sur GPIO 5
Mode monitoring en temps réel - Appuyez sur Ctrl+C pour arrêter
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

W1_BASE = "/sys/bus/w1/devices/"

def monitor_ibutton():
    """Surveille en continu la détection d'iButton"""

    print("=" * 70)
    print("  SURVEILLANCE CONTINUE - iButton sur GPIO 5")
    print("=" * 70)
    print()

    # Configure GPIO 6 pull-up
    if setup_gpio6_pullup():
        print("  Pull-up: GPIO 6 (Pin 31) = HIGH ✓")
    else:
        print("  Pull-up: GPIO 6 non configuré (exécuter avec sudo)")

    print("  État: ACTIF")
    print("  Appuyez sur Ctrl+C pour arrêter")
    print()
    print("-" * 70)
    print()

    if not os.path.exists(W1_BASE):
        print("❌ ERREUR: Interface 1-Wire non disponible!")
        print()
        print("Configuration requise dans /boot/firmware/config.txt:")
        print("  dtoverlay=w1-gpio,gpiopin=5")
        print()
        print("Ensuite redémarrer ou recharger le module:")
        print("  sudo modprobe -r w1_gpio && sudo modprobe w1_gpio")
        return

    last_id = None
    detection_count = 0

    try:
        while True:
            # Lire les périphériques
            try:
                devices = os.listdir(W1_BASE)
                ibuttons = [d for d in devices if d.startswith("01-")]
            except Exception as e:
                print(f"[ERREUR] Lecture impossible: {e}")
                time.sleep(1)
                continue

            timestamp = time.strftime("%H:%M:%S")

            if ibuttons:
                current_id = ibuttons[0]

                if current_id != last_id:
                    # Nouveau iButton détecté
                    detection_count += 1

                    # Lire l'ID complet
                    try:
                        id_path = os.path.join(W1_BASE, current_id, "id")
                        if os.path.exists(id_path):
                            with open(id_path, 'r') as f:
                                display_id = f.read().strip()
                        else:
                            display_id = current_id
                    except:
                        display_id = current_id

                    print(f"[{timestamp}] ✓ DÉTECTÉ    | {display_id} (#{detection_count})")
                    last_id = current_id
            else:
                if last_id is not None:
                    # iButton retiré
                    print(f"[{timestamp}] - RETIRÉ     | Probe libre")
                    last_id = None

            time.sleep(0.3)  # Poll toutes les 300ms

    except KeyboardInterrupt:
        print()
        print("-" * 70)
        print()
        print(f"  Arrêt du monitoring")
        print(f"  Total détections: {detection_count}")
        print()
        print("=" * 70)
        sys.exit(0)

if __name__ == "__main__":
    monitor_ibutton()
