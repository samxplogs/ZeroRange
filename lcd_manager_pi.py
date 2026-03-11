"""
LCD Manager for Adafruit RGB LCD Shield
Handles I2C communication with 16x2 LCD display
"""

import board
import busio
import adafruit_character_lcd.character_lcd_rgb_i2c as character_lcd
import time
import logging

logger = logging.getLogger(__name__)


class LCDManager:
    """Manages Adafruit RGB LCD Shield for Raspberry Pi"""

    def __init__(self, address=0x20, bus=1):
        """
        Initialize LCD Manager

        Args:
            address: I2C address of Adafruit LCD Shield (default 0x20)
            bus: I2C bus number (ignored, uses board.I2C)
        """
        self.addr = address
        self.width = 16
        self.height = 2

        try:
            # Initialize I2C
            i2c = busio.I2C(board.SCL, board.SDA)

            # Initialize the RGB LCD (16 columns, 2 rows)
            self.lcd = character_lcd.Character_LCD_RGB_I2C(i2c, self.width, self.height)

            logger.info(f"Adafruit RGB LCD initialized at address 0x{address:02X}")
            self.init_display()
        except Exception as e:
            logger.error(f"Failed to initialize Adafruit RGB LCD: {e}")
            raise

    def init_display(self):
        """Initialize display: clear screen and set backlight"""
        try:
            self.lcd.clear()
            time.sleep(0.1)

            # Set backlight to white
            self.lcd.color = [100, 100, 100]

            logger.info("Adafruit RGB LCD initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize display: {e}")
            raise

    def clear(self):
        """Clear the entire display"""
        try:
            self.lcd.clear()
            time.sleep(0.002)
        except Exception as e:
            logger.error(f"Failed to clear display: {e}")

    def write_text(self, x, y, text):
        """
        Write text at specific position

        Args:
            x: Column position (0-15)
            y: Row position (0-1)
            text: Text to write (will be truncated to fit)
        """
        if not (0 <= x < self.width and 0 <= y < self.height):
            logger.warning(f"Invalid position: ({x}, {y})")
            return

        try:
            # Set cursor position
            self.lcd.cursor_position(x, y)

            # Write text (truncate if too long)
            max_length = self.width - x
            text_to_write = text[:max_length]

            self.lcd.message = text_to_write

        except Exception as e:
            logger.error(f"Failed to write text at ({x}, {y}): {e}")

    def write_line(self, line, text):
        """
        Write text to entire line (padded to 16 chars)

        Args:
            line: Line number (0-1)
            text: Text to write (will be padded or truncated to 16 chars)
        """
        # Clear the line first then write
        self.lcd.cursor_position(0, line)
        formatted_text = text.ljust(self.width)[:self.width]
        self.lcd.message = formatted_text

    def read_buttons(self):
        """
        Read button state (not supported yet)

        Returns:
            int: Always returns 0 for now
        """
        logger.debug("Button reading not yet implemented")
        return 0

    def button_pressed(self, button_num):
        """
        Check if specific button is pressed (not supported yet)

        Args:
            button_num: Button number (1-5)

        Returns:
            bool: Always returns False for now
        """
        return False

    def wait_button_release(self, button_num):
        """
        Wait until button is released (not supported, returns immediately)

        Args:
            button_num: Button number (1-5)
        """
        pass

    def get_pressed_button(self):
        """
        Get the first pressed button number (not supported yet)

        Returns:
            None: Always returns None for now
        """
        return None

    def close(self):
        """Close LCD connection"""
        try:
            self.lcd.clear()
            self.lcd.color = [0, 0, 0]
            logger.info("LCD closed")
        except Exception as e:
            logger.error(f"Failed to close LCD: {e}")


# Test code
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format='[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s'
    )

    try:
        print("Initializing Adafruit RGB LCD...")
        lcd = LCDManager()

        print("Writing test message...")
        lcd.write_line(0, "ZeroRange v1.0")
        lcd.write_line(1, "LCD Test OK!")

        print("Testing for 5 seconds...")
        time.sleep(5)

        lcd.clear()
        lcd.write_line(0, "Test complete!")
        time.sleep(2)

        lcd.close()
        print("Test finished!")

    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
