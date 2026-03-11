#!/usr/bin/env python3
"""
Configure GPIO 6 (Pin 31) comme source 3.3V pour pull-up iButton
Ce script configure GPIO 6 en OUTPUT HIGH pour alimenter la résistance pull-up
"""

import os
import sys

GPIO_PULLUP = 6  # GPIO 6 (Pin 31)
GPIO_EXPORT = "/sys/class/gpio/export"
GPIO_BASE = "/sys/class/gpio/gpio6"

def setup_gpio6_pullup():
    """Configure GPIO 6 en OUTPUT HIGH pour pull-up"""

    print("=" * 60)
    print("Configuration GPIO 6 pour pull-up iButton")
    print("=" * 60)
    print()

    try:
        # Export GPIO 6 si pas déjà fait
        if not os.path.exists(GPIO_BASE):
            print("[1/3] Export GPIO 6...")
            with open(GPIO_EXPORT, 'w') as f:
                f.write(str(GPIO_PULLUP))
            print("✓ GPIO 6 exporté")
        else:
            print("[1/3] GPIO 6 déjà exporté")

        # Configurer en OUTPUT
        print()
        print("[2/3] Configuration en OUTPUT...")
        direction_file = os.path.join(GPIO_BASE, "direction")
        with open(direction_file, 'w') as f:
            f.write("out")
        print("✓ GPIO 6 configuré en OUTPUT")

        # Mettre à HIGH (3.3V)
        print()
        print("[3/3] Activation HIGH (3.3V)...")
        value_file = os.path.join(GPIO_BASE, "value")
        with open(value_file, 'w') as f:
            f.write("1")
        print("✓ GPIO 6 = HIGH (3.3V)")

        print()
        print("=" * 60)
        print("✅ Configuration réussie!")
        print()
        print("Câblage:")
        print("  Pin 31 (GPIO 6) --> [4.7kΩ] --> Pin 29 (GPIO 5)")
        print("  Pin 29 (GPIO 5) --> DATA probe iButton")
        print("  Pin 30 (GND)    --> GND probe iButton")
        print("=" * 60)

        return True

    except PermissionError:
        print()
        print("❌ ERREUR: Permissions insuffisantes")
        print()
        print("Exécuter avec sudo:")
        print("  sudo python3 setup_gpio6_pullup.py")
        print()
        return False

    except Exception as e:
        print()
        print(f"❌ ERREUR: {e}")
        print()
        return False

def check_gpio6_status():
    """Vérifie l'état actuel de GPIO 6"""

    print()
    print("État actuel de GPIO 6:")
    print("-" * 60)

    if not os.path.exists(GPIO_BASE):
        print("⚠ GPIO 6 non exporté")
        return

    # Lire direction
    try:
        with open(os.path.join(GPIO_BASE, "direction"), 'r') as f:
            direction = f.read().strip()
        print(f"  Direction: {direction}")
    except:
        print("  Direction: Erreur lecture")

    # Lire valeur
    try:
        with open(os.path.join(GPIO_BASE, "value"), 'r') as f:
            value = f.read().strip()
        status = "HIGH (3.3V)" if value == "1" else "LOW (0V)"
        print(f"  Valeur: {value} ({status})")
    except:
        print("  Valeur: Erreur lecture")

    print("-" * 60)

if __name__ == "__main__":
    print()

    # Vérifier l'état actuel
    if os.path.exists(GPIO_BASE):
        check_gpio6_status()

    # Configurer GPIO 6
    success = setup_gpio6_pullup()

    if success:
        print()
        check_gpio6_status()
        sys.exit(0)
    else:
        sys.exit(1)
