#!/usr/bin/env python3
"""
Button Test Script
Displays which button is pressed on the LCD
Press Ctrl+C to exit
"""

import time
import sys
from lcd_manager import LCDManager

def main():
    print("Starting button test...")
    print("Press buttons to see which number they are")
    print("Press Ctrl+C to exit")

    try:
        lcd = LCDManager()
        lcd.clear()
        lcd.write_line(0, "Button Test")
        lcd.write_line(1, "Press a button")

        last_pressed = None

        while True:
            # Check all 5 buttons
            for btn in range(1, 6):
                if lcd.button_pressed(btn):
                    if last_pressed != btn:
                        # New button pressed
                        lcd.clear()
                        lcd.write_line(0, f"BTN{btn} pressed!")
                        lcd.write_line(1, "Try another...")
                        print(f"Button {btn} detected")
                        last_pressed = btn

                    # Wait for release
                    lcd.wait_button_release(btn)
                    lcd.clear()
                    lcd.write_line(0, "Button Test")
                    lcd.write_line(1, "Press a button")
                    last_pressed = None
                    break

            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\nTest stopped")
        lcd.clear()
        lcd.write_line(0, "Test ended")
        time.sleep(1)
        lcd.clear()
        lcd.close()

    except Exception as e:
        print(f"Error: {e}")
        if 'lcd' in locals():
            lcd.clear()
            lcd.close()

if __name__ == "__main__":
    main()
