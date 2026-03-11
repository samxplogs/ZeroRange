"""
LCD Manager for Adafruit RGB LCD Shield
Handles I2C communication with 16x2 LCD display and button input
"""

import board
import busio
import adafruit_character_lcd.character_lcd_rgb_i2c as character_lcd
import smbus2
import time
import logging
import json
import os

logger = logging.getLogger(__name__)

# Shared state files for web sync
SHARED_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'run')
LCD_STATE_FILE = os.path.join(SHARED_DIR, 'lcd_state.json')
WEB_BUTTON_FILE = os.path.join(SHARED_DIR, 'web_button.json')


class LCDManager:
    """Manages Adafruit RGB LCD Shield for Raspberry Pi"""

    # Button mapping: MCP23017 Pin -> Button Number
    # Pin 0 = SELECT (BTN1)
    # Pin 3 = UP (BTN2)
    # Pin 2 = DOWN (BTN3)
    # Pin 1 = RIGHT (BTN4)
    # Pin 4 = LEFT (BTN5)

    BTN_SELECT = 1
    BTN_UP = 2
    BTN_DOWN = 3
    BTN_RIGHT = 4
    BTN_LEFT = 5

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
        self._lines = ['', '']
        self._web_btn_cache = None

        # Ensure shared dir exists
        os.makedirs(SHARED_DIR, exist_ok=True)
        # Clear any stale web button
        self._clear_web_button()

        try:
            # Reset MCP23017 to clean state before initialization
            # This prevents GPIO configuration conflicts
            logger.info("Resetting MCP23017 to default state...")
            bus = smbus2.SMBus(1)
            bus.write_byte_data(address, 0x00, 0xFF)  # IODIRA - all inputs
            bus.write_byte_data(address, 0x01, 0xFF)  # IODIRB - all inputs
            bus.write_byte_data(address, 0x12, 0x00)  # GPIOA - clear outputs
            bus.write_byte_data(address, 0x13, 0x00)  # GPIOB - clear outputs
            bus.write_byte_data(address, 0x0C, 0x00)  # GPPUA - clear pull-ups
            bus.write_byte_data(address, 0x0D, 0x00)  # GPPUB - clear pull-ups
            bus.close()
            time.sleep(0.1)

            # Initialize I2C
            i2c = busio.I2C(board.SCL, board.SDA)

            # Initialize the RGB LCD (16 columns, 2 rows)
            # This also initializes the MCP23017 and buttons internally
            self.lcd = character_lcd.Character_LCD_RGB_I2C(i2c, self.width, self.height)

            logger.info(f"Adafruit RGB LCD initialized at address 0x{address:02X}")
            logger.info("Using LCD built-in button support")
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
            self._lines = ['', '']
            self._sync_state_to_file()
            time.sleep(0.05)
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
        # Format text to exactly 16 characters
        formatted_text = text.ljust(self.width)[:self.width]

        # Track state for web sync
        if 0 <= line <= 1:
            self._lines[line] = formatted_text
            self._sync_state_to_file()

        # Write entire line at once (faster and more reliable over I2C)
        self.lcd.cursor_position(0, line)
        self.lcd.message = formatted_text

    def read_buttons(self):
        """
        Read button state from LCD shield buttons

        Returns:
            int: Button state byte (bit-mapped)
                 Bit 0 = SELECT, Bit 1 = UP, Bit 2 = DOWN, Bit 3 = RIGHT, Bit 4 = LEFT
        """
        try:
            button_state = 0

            # Read from LCD's built-in button properties
            if self.lcd.select_button:
                button_state |= (1 << 0)
            if self.lcd.up_button:
                button_state |= (1 << 1)
            if self.lcd.down_button:
                button_state |= (1 << 2)
            if self.lcd.right_button:
                button_state |= (1 << 3)
            if self.lcd.left_button:
                button_state |= (1 << 4)

            return button_state
        except Exception as e:
            logger.error(f"Failed to read buttons: {e}")
            return 0

    def button_pressed(self, button_num):
        """
        Check if specific button is pressed (physical or web)

        Args:
            button_num: Button number (1=SELECT, 2=UP, 3=DOWN, 4=RIGHT, 5=LEFT)

        Returns:
            bool: True if button is pressed
        """
        if not (1 <= button_num <= 5):
            return False

        try:
            # Check physical buttons first
            if button_num == self.BTN_SELECT and self.lcd.select_button:
                return True
            elif button_num == self.BTN_UP and self.lcd.up_button:
                return True
            elif button_num == self.BTN_DOWN and self.lcd.down_button:
                return True
            elif button_num == self.BTN_RIGHT and self.lcd.right_button:
                return True
            elif button_num == self.BTN_LEFT and self.lcd.left_button:
                return True

            # Check web button (cached - file read only once per cycle)
            web_btn = self._read_web_button_file()
            if web_btn == button_num:
                self._web_btn_cache = None  # Consume the cached button
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to check button {button_num}: {e}")
            return False

    def wait_button_release(self, button_num):
        """
        Wait until button is released (debouncing)

        Args:
            button_num: Button number (1-5)
        """
        while self.button_pressed(button_num):
            time.sleep(0.05)  # 50ms polling

    def get_pressed_button(self):
        """
        Get the first pressed button number

        Returns:
            int or None: Button number (1-5) or None if no button pressed
        """
        button_state = self.read_buttons()
        if button_state == 0:
            return None

        # Check each button (priority to lower numbers)
        for btn in range(1, 6):
            if button_state & (1 << (btn - 1)):
                return btn

        return None

    def _sync_state_to_file(self):
        """Write current LCD state to shared file for web sync"""
        try:
            state = {'line1': self._lines[0], 'line2': self._lines[1]}
            tmp = LCD_STATE_FILE + '.tmp'
            with open(tmp, 'w') as f:
                json.dump(state, f)
            os.replace(tmp, LCD_STATE_FILE)
        except Exception:
            pass

    def _clear_web_button(self):
        """Clear the web button file"""
        try:
            if os.path.exists(WEB_BUTTON_FILE):
                os.remove(WEB_BUTTON_FILE)
        except Exception:
            pass

    def _read_web_button_file(self):
        """
        Read web button file once and cache the value.
        Subsequent calls return the cached value without file I/O.
        The cache is cleared only when consumed by button_pressed().
        """
        if self._web_btn_cache is not None:
            return self._web_btn_cache
        try:
            if not os.path.exists(WEB_BUTTON_FILE):
                return None
            with open(WEB_BUTTON_FILE, 'r') as f:
                data = json.load(f)
            os.remove(WEB_BUTTON_FILE)
            btn = data.get('button')
            if btn:
                self._web_btn_cache = btn
            return btn
        except Exception:
            return None

    def check_web_button(self):
        """
        Check if a button was pressed from the web interface

        Returns:
            int or None: Button number (1-5) or None
        """
        return self._read_web_button_file()

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
        print("Initializing Adafruit RGB LCD with button support...")
        lcd = LCDManager()

        print("Testing buttons...")
        lcd.write_line(0, "Button Test")
        lcd.write_line(1, "Press buttons!")

        print("Press buttons (LEFT to exit)...")
        while True:
            btn = lcd.get_pressed_button()
            if btn:
                btn_names = {1: "SELECT", 2: "UP", 3: "DOWN", 4: "RIGHT", 5: "LEFT"}
                print(f"Button {btn} ({btn_names[btn]}) pressed!")
                lcd.write_line(1, f"{btn_names[btn]} pressed!".ljust(16))
                lcd.wait_button_release(btn)

                if btn == 5:  # LEFT = exit
                    break

            time.sleep(0.1)

        lcd.clear()
        lcd.write_line(0, "Test complete!")
        time.sleep(1)
        lcd.close()
        print("Test finished!")

    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
