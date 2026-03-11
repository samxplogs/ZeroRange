#!/usr/bin/env python3
"""
Configure GPIO 6 (Pin 31) comme source 3.3V pour pull-up iButton
Version compatible Raspberry Pi 5 (utilise RPi.GPIO ou gpiod)
"""

import sys
import os

GPIO_PULLUP = 6  # GPIO 6 (Pin 31)

def setup_with_rpigpio():
    """Méthode 1: Utiliser RPi.GPIO"""
    try:
        import RPi.GPIO as GPIO

        print("[Méthode] RPi.GPIO")

        # Configuration
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        # Configurer GPIO 6 en OUTPUT HIGH
        GPIO.setup(GPIO_PULLUP, GPIO.OUT)
        GPIO.output(GPIO_PULLUP, GPIO.HIGH)

        print(f"✓ GPIO {GPIO_PULLUP} configuré en HIGH (3.3V)")
        return True

    except ImportError:
        return False
    except Exception as e:
        print(f"✗ Erreur RPi.GPIO: {e}")
        return False

def setup_with_gpiod():
    """Méthode 2: Utiliser gpiod (Raspberry Pi 5)"""
    try:
        import gpiod

        print("[Méthode] libgpiod")

        # Ouvrir le chip GPIO
        chip = gpiod.Chip('gpiochip4')  # Raspberry Pi 5 utilise gpiochip4

        # Obtenir la ligne GPIO 6
        line = chip.get_line(GPIO_PULLUP)

        # Configurer en output et mettre à HIGH
        line.request(consumer="ibutton_pullup", type=gpiod.LINE_REQ_DIR_OUT, default_vals=[1])

        print(f"✓ GPIO {GPIO_PULLUP} configuré en HIGH (3.3V)")

        # Note: La ligne restera active jusqu'à la fin du programme
        # Pour usage permanent, utiliser un service systemd

        return True

    except ImportError:
        return False
    except Exception as e:
        print(f"✗ Erreur gpiod: {e}")
        return False

def setup_with_command():
    """Méthode 3: Utiliser gpioset en ligne de commande"""
    try:
        print("[Méthode] gpioset (ligne de commande)")

        # Essayer avec gpioset
        result = os.system(f"gpioset gpiochip4 {GPIO_PULLUP}=1 &")

        if result == 0:
            print(f"✓ GPIO {GPIO_PULLUP} configuré en HIGH (3.3V)")
            return True
        else:
            return False

    except Exception as e:
        print(f"✗ Erreur commande: {e}")
        return False

def check_gpio_status():
    """Vérifier l'état de GPIO 6"""
    try:
        import gpiod

        chip = gpiod.Chip('gpiochip4')
        line = chip.get_line(GPIO_PULLUP)
        line.request(consumer="check", type=gpiod.LINE_REQ_DIR_IN)

        value = line.get_value()
        status = "HIGH (3.3V)" if value == 1 else "LOW (0V)"

        print(f"\nÉtat GPIO {GPIO_PULLUP}: {status}")

        line.release()

    except:
        pass

def main():
    print("=" * 60)
    print("Configuration GPIO 6 pour pull-up iButton")
    print("=" * 60)
    print()

    success = False

    # Essayer différentes méthodes
    print("Tentative de configuration...\n")

    # Méthode 1: RPi.GPIO
    if not success:
        success = setup_with_rpigpio()

    # Méthode 2: gpiod
    if not success:
        success = setup_with_gpiod()

    # Méthode 3: Ligne de commande
    if not success:
        success = setup_with_command()

    print()

    if success:
        print("=" * 60)
        print("✅ Configuration réussie!")
        print()
        print("Câblage:")
        print("  Pin 31 (GPIO 6) --> [4.7kΩ] --> Pin 29 (GPIO 5)")
        print("  Pin 29 (GPIO 5) --> DATA probe iButton")
        print("  Pin 30 (GND)    --> GND probe iButton")
        print("=" * 60)

        check_gpio_status()

        return 0
    else:
        print("=" * 60)
        print("❌ Échec de la configuration")
        print()
        print("Solutions:")
        print("1. Installer RPi.GPIO:")
        print("   sudo apt install python3-rpi.gpio")
        print()
        print("2. Installer libgpiod:")
        print("   sudo apt install gpiod python3-libgpiod")
        print()
        print("3. Configuration manuelle:")
        print("   gpioset gpiochip4 6=1")
        print("=" * 60)

        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nInterrompu par l'utilisateur")
        sys.exit(1)
