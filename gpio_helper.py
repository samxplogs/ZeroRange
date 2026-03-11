"""
Helper module pour gérer GPIO 6 comme pull-up source
Compatible Raspberry Pi 5 (utilise RPi.GPIO ou gpiod)
"""

import os

GPIO_PULLUP = 6  # GPIO 6 (Pin 31)

def setup_gpio6_pullup():
    """
    Configure GPIO 6 en OUTPUT HIGH pour pull-up iButton
    Retourne True si succès, False sinon
    """

    # Méthode 1: RPi.GPIO
    try:
        import RPi.GPIO as GPIO

        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(GPIO_PULLUP, GPIO.OUT)
        GPIO.output(GPIO_PULLUP, GPIO.HIGH)

        return True
    except (ImportError, Exception):
        pass

    # Méthode 2: gpiod (Raspberry Pi 5)
    try:
        import gpiod

        chip = gpiod.Chip('gpiochip4')
        line = chip.get_line(GPIO_PULLUP)
        line.request(consumer="ibutton_pullup", type=gpiod.LINE_REQ_DIR_OUT, default_vals=[1])

        return True
    except (ImportError, Exception):
        pass

    # Méthode 3: Ligne de commande
    try:
        result = os.system(f"gpioset gpiochip4 {GPIO_PULLUP}=1 2>/dev/null &")
        if result == 0:
            return True
    except:
        pass

    return False

def cleanup_gpio6():
    """Nettoyer GPIO 6 à la sortie"""
    try:
        import RPi.GPIO as GPIO
        GPIO.cleanup(GPIO_PULLUP)
    except:
        pass
