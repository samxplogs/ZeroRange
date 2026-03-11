#!/usr/bin/env python3
"""
Diagnostic complet iButton - GPIO 5 avec pull-up GPIO 6
"""

import os
import sys

W1_BASE = "/sys/bus/w1/devices/"

def check_gpio6():
    """Vérifier GPIO 6 (pull-up)"""
    print("=" * 70)
    print("DIAGNOSTIC iButton - GPIO 5 + GPIO 6")
    print("=" * 70)
    print()

    print("[1/5] Vérification GPIO 6 (Pull-up)...")

    # Méthode 1: Vérifier via sysfs
    try:
        gpio_dir = "/sys/class/gpio/gpio6"
        if os.path.exists(gpio_dir):
            with open(f"{gpio_dir}/value", 'r') as f:
                value = f.read().strip()
            status = "HIGH (3.3V) ✓" if value == "1" else "LOW (0V) ✗"
            print(f"  GPIO 6 état: {status}")
        else:
            print("  GPIO 6: Non exporté")
            print("  → Exécuter: sudo python3 setup_gpio6_pullup_v2.py")
    except Exception as e:
        print(f"  Impossible de lire GPIO 6: {e}")

def check_1wire():
    """Vérifier interface 1-Wire"""
    print()
    print("[2/5] Vérification interface 1-Wire...")

    if not os.path.exists(W1_BASE):
        print("  ✗ Interface 1-Wire non disponible!")
        print("  → Vérifier /boot/firmware/config.txt")
        print("  → Ligne requise: dtoverlay=w1-gpio,gpiopin=5")
        return False

    print("  ✓ Interface 1-Wire présente")
    return True

def check_devices():
    """Lister tous les périphériques"""
    print()
    print("[3/5] Liste des périphériques 1-Wire...")

    try:
        devices = os.listdir(W1_BASE)
        print(f"  Trouvé {len(devices)} périphérique(s):")

        ibuttons = []
        noise = []

        for device in devices:
            if device == "w1_bus_master1":
                print(f"    - {device} (bus master)")
            elif device.startswith("01-"):
                print(f"    - {device} ✓ iButton!")
                ibuttons.append(device)
            elif device.startswith("00-"):
                print(f"    - {device} (bruit/parasite)")
                noise.append(device)
            else:
                print(f"    - {device}")

        return ibuttons, noise

    except Exception as e:
        print(f"  ✗ Erreur: {e}")
        return [], []

def check_wiring():
    """Afficher le câblage attendu"""
    print()
    print("[4/5] Câblage attendu...")
    print()
    print("  Pin 31 (GPIO 6) ──> [4.7kΩ] ──┐")
    print("                                 ├──> Pin 29 (GPIO 5) ──> DATA probe")
    print("  Pin 30 (GND) ──────────────────────────────────────> GND probe")
    print()

def troubleshooting(has_ibutton, noise_count):
    """Suggestions de dépannage"""
    print()
    print("[5/5] Diagnostic...")
    print()

    if has_ibutton:
        print("  ✓✓✓ iButton détecté avec succès!")
        print("  Le système fonctionne correctement.")
        return

    if noise_count > 0:
        print("  ⚠ Périphériques parasites détectés (00-XXXXXXXXXXXX)")
        print()
        print("  Causes possibles:")
        print("    1. Résistance pull-up manquante ou mauvaise valeur")
        print("       → Vérifier que c'est bien 4.7kΩ (pas 47kΩ ou 470Ω)")
        print()
        print("    2. Câblage incorrect")
        print("       → Pin 31 doit alimenter la résistance")
        print("       → La résistance doit aller vers Pin 29")
        print("       → Pin 29 doit aller au DATA du probe")
        print()
        print("    3. iButton pas bien en contact")
        print("       → Nettoyer le probe")
        print("       → Maintenir fermement l'iButton 2-3 secondes")
        print()
        print("    4. GPIO 6 pas en HIGH")
        print("       → Exécuter: sudo python3 setup_gpio6_pullup_v2.py")
    else:
        print("  ⚠ Aucun périphérique détecté")
        print()
        print("  Causes possibles:")
        print("    1. Probe iButton pas connecté")
        print("       → Vérifier DATA sur Pin 29")
        print("       → Vérifier GND sur Pin 30")
        print()
        print("    2. Interface 1-Wire pas sur le bon GPIO")
        print("       → Vérifier: dtoverlay=w1-gpio,gpiopin=5")
        print("       → Recharger: sudo modprobe -r w1_gpio && sudo modprobe w1_gpio")
        print()
        print("    3. Résistance pull-up manquante")
        print("       → 4.7kΩ OBLIGATOIRE entre Pin 31 et Pin 29")

def main():
    # Vérifications
    check_gpio6()

    if not check_1wire():
        sys.exit(1)

    ibuttons, noise = check_devices()
    check_wiring()
    troubleshooting(len(ibuttons) > 0, len(noise))

    print()
    print("=" * 70)

    if ibuttons:
        print("✓ SUCCÈS - iButton(s) détecté(s)")
        for ib in ibuttons:
            print(f"  {ib}")
    else:
        print("✗ ÉCHEC - Aucun iButton détecté")
        print()
        print("Actions recommandées:")
        print("  1. Vérifier le câblage physique (voir ci-dessus)")
        print("  2. Configurer GPIO 6: sudo python3 setup_gpio6_pullup_v2.py")
        print("  3. Relancer ce diagnostic: sudo python3 diagnose_ibutton.py")
        print("  4. Tester avec monitoring: sudo python3 monitor_ibutton_gpio5.py")

    print("=" * 70)

if __name__ == "__main__":
    main()
