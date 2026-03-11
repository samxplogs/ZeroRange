#!/usr/bin/env python3
"""
SubGHZ Handler for ZeroRange
Challenges SubGHZ avec HackRF One SDR
"""

import time
import logging
import os
from typing import Tuple, Optional, Dict
from hackrf_handler import HackRFHandler

logger = logging.getLogger(__name__)


class SubGHZHandler:
    """Handles SubGHZ challenges using HackRF One"""

    # Target frequency for challenges (433.92 MHz - common garage door/keyfob)
    TARGET_FREQUENCY = 433920000

    # Signal detection threshold (dBm)
    DETECTION_THRESHOLD = -55

    def __init__(self, lcd, hackrf: Optional[HackRFHandler] = None):
        """
        Initialize SubGHZ handler

        Args:
            lcd: Instance de LCDManager
            hackrf: Instance de HackRFHandler (created if None)
        """
        self.lcd = lcd
        self.hackrf = hackrf

        # Initialize HackRF if not provided
        if self.hackrf is None:
            try:
                self.hackrf = HackRFHandler()
            except Exception as e:
                logger.error(f"Failed to initialize HackRF: {e}")
                raise

        # Set default frequency
        self.hackrf.set_frequency(self.TARGET_FREQUENCY)

        # Store last captured signal for challenges
        self.last_capture_path: Optional[str] = None
        self.last_capture_info: Optional[Dict] = None

        logger.info("SubGHZ handler initialized")

    def wait_for_signal(self, timeout: int, frequency: Optional[int] = None) -> Tuple[bool, Optional[Dict], int]:
        """
        Wait for RF signal detection with countdown

        Args:
            timeout: Maximum time to wait in seconds
            frequency: Frequency to monitor (uses default if None)

        Returns:
            tuple: (success, signal_info, time_taken)
        """
        freq = frequency or self.TARGET_FREQUENCY
        start_time = time.time()

        self.lcd.write_line(0, f"Scan {freq/1e6:.1f}MHz")

        while True:
            elapsed = int(time.time() - start_time)
            remaining = timeout - elapsed

            # Update countdown on LCD line 1
            countdown_text = f"L/R:Skip [{remaining}s]"
            self.lcd.write_line(1, countdown_text)

            # Try to capture and detect signal
            success, filepath, info = self.hackrf.capture_signal(
                duration_seconds=1.0,
                frequency=freq
            )

            if success and info.get('detected') and info.get('signal_strength', -100) > self.DETECTION_THRESHOLD:
                self.last_capture_path = filepath
                self.last_capture_info = info
                logger.info(f"Signal detected: {info['signal_strength']} dBm in {elapsed}s")
                return (True, info, elapsed)

            # Clean up if no good signal
            if filepath and os.path.exists(filepath):
                os.remove(filepath)

            # Check for skip button (BTN4 or BTN5)
            if self.lcd.button_pressed(4) or self.lcd.button_pressed(5):
                btn = 4 if self.lcd.button_pressed(4) else 5
                self.lcd.wait_button_release(btn)
                logger.info(f"Challenge skipped after {elapsed}s")
                return (False, None, elapsed)

            # Check timeout
            if elapsed >= timeout:
                logger.info(f"Timeout after {timeout}s")
                return (False, None, timeout)

            time.sleep(0.3)

    def challenge_1_detect(self) -> int:
        """
        Challenge 1: Detect & Capture
        Detect any RF signal in the SubGHZ band (433MHz)

        Returns:
            int: Points earned (10 or 0)
        """
        logger.info("Starting SubGHZ Challenge 1: Detect & Capture")

        # Display challenge screen
        self.lcd.clear()
        self.lcd.write_line(0, "SubGHz Ch1:Scan")

        # Wait for RF signal (60 second timeout)
        success, signal_info, time_taken = self.wait_for_signal(60)

        if success:
            # Display signal info briefly
            self.lcd.clear()
            strength = signal_info.get('signal_strength', 'N/A')
            self.lcd.write_line(0, f"Signal: {strength}dBm")

            freq_mhz = signal_info.get('frequency', 0) / 1e6
            self.lcd.write_line(1, f"Freq: {freq_mhz:.2f}MHz")
            time.sleep(3)

            # Success screen
            self.lcd.clear()
            self.lcd.write_line(0, "SOLVED! +10pts")
            self.lcd.write_line(1, "L:Back")

            logger.info(f"SubGHZ Challenge 1 completed in {time_taken}s")

            # Wait for user to press Back button
            while True:
                if self.lcd.button_pressed(5):
                    self.lcd.wait_button_release(5)
                    return 10
                time.sleep(0.1)
        else:
            # Fail screen
            self.lcd.clear()
            self.lcd.write_line(0, "NO SIGNAL")
            self.lcd.write_line(1, "1:Retry L:Back")

            logger.info("SubGHZ Challenge 1 failed")

            # Wait for button press
            while True:
                if self.lcd.button_pressed(1):
                    self.lcd.wait_button_release(1)
                    return self.challenge_1_detect()  # Retry
                elif self.lcd.button_pressed(5):
                    self.lcd.wait_button_release(5)
                    return 0  # Back to menu

                time.sleep(0.1)

    def challenge_2_replay(self) -> int:
        """
        Challenge 2: Record & Replay
        Capture a signal and replay it successfully

        Returns:
            int: Points earned (10 or 0)
        """
        logger.info("Starting SubGHZ Challenge 2: Record & Replay")

        # Step 1: Capture the original signal
        self.lcd.clear()
        self.lcd.write_line(0, "SubGHz Ch2 [1/2]")
        self.lcd.write_line(1, "Press TX button")
        time.sleep(2)

        self.lcd.write_line(0, "Recording...")

        success, signal_info, time_taken = self.wait_for_signal(45)

        if not success:
            # Failed to capture
            self.lcd.clear()
            self.lcd.write_line(0, "NO SIGNAL")
            self.lcd.write_line(1, "1:Retry L:Back")

            while True:
                if self.lcd.button_pressed(1):
                    self.lcd.wait_button_release(1)
                    return self.challenge_2_replay()
                elif self.lcd.button_pressed(5):
                    self.lcd.wait_button_release(5)
                    return 0

                time.sleep(0.1)

        # Signal captured
        self.lcd.clear()
        self.lcd.write_line(0, "Signal captured!")
        strength = signal_info.get('signal_strength', 'N/A')
        self.lcd.write_line(1, f"Strength: {strength}dBm")
        time.sleep(2)

        # Step 2: Replay the signal
        self.lcd.clear()
        self.lcd.write_line(0, "SubGHz Ch2 [2/2]")
        self.lcd.write_line(1, "Replaying...")

        if self.last_capture_path:
            replay_success = self.hackrf.replay_signal(
                self.last_capture_path,
                repeat=3
            )

            if replay_success:
                # Success!
                self.lcd.clear()
                self.lcd.write_line(0, "SOLVED! +10pts")
                self.lcd.write_line(1, "Signal replayed!")

                time.sleep(2)

                self.lcd.write_line(1, "L:Back")

                logger.info("SubGHZ Challenge 2 completed")

                # Wait for user to press Back button
                while True:
                    if self.lcd.button_pressed(5):
                        self.lcd.wait_button_release(5)
                        return 10
                    time.sleep(0.1)

        # Replay failed
        self.lcd.clear()
        self.lcd.write_line(0, "REPLAY FAILED")
        self.lcd.write_line(1, "1:Retry L:Back")

        logger.info("SubGHZ Challenge 2 failed - replay error")

        while True:
            if self.lcd.button_pressed(1):
                self.lcd.wait_button_release(1)
                return self.challenge_2_replay()
            elif self.lcd.button_pressed(5):
                self.lcd.wait_button_release(5)
                return 0

            time.sleep(0.1)

    def challenge_3_analyze(self) -> int:
        """
        Challenge 3: Signal Analysis
        Capture and identify the protocol/modulation of a signal

        Returns:
            int: Points earned (10 or 0)
        """
        logger.info("Starting SubGHZ Challenge 3: Signal Analysis")

        # Display challenge
        self.lcd.clear()
        self.lcd.write_line(0, "SubGHz Ch3:Anal")
        self.lcd.write_line(1, "Send RF signal")
        time.sleep(2)

        # Wait for signal
        success, signal_info, time_taken = self.wait_for_signal(60)

        if not success:
            self.lcd.clear()
            self.lcd.write_line(0, "NO SIGNAL")
            self.lcd.write_line(1, "1:Retry L:Back")

            while True:
                if self.lcd.button_pressed(1):
                    self.lcd.wait_button_release(1)
                    return self.challenge_3_analyze()
                elif self.lcd.button_pressed(5):
                    self.lcd.wait_button_release(5)
                    return 0

                time.sleep(0.1)

        # Analyze the captured signal
        self.lcd.clear()
        self.lcd.write_line(0, "Analyzing...")
        self.lcd.write_line(1, "Please wait...")

        if self.last_capture_path:
            analysis = self.hackrf.analyze_signal(self.last_capture_path)

            # Display analysis results
            self.lcd.clear()
            protocol = analysis.get('protocol', 'Unknown')[:16]
            self.lcd.write_line(0, f"Proto:{protocol}")

            modulation = analysis.get('modulation', 'Unknown')[:16]
            self.lcd.write_line(1, f"Mod:{modulation}")
            time.sleep(3)

            # Check if we got meaningful analysis
            if analysis.get('protocol') != 'Unknown' or analysis.get('confidence', 0) > 0.5:
                # Success - protocol identified
                self.lcd.clear()
                self.lcd.write_line(0, "SOLVED! +10pts")
                self.lcd.write_line(1, "L:Back")

                logger.info(f"SubGHZ Challenge 3 completed: {protocol}")

                while True:
                    if self.lcd.button_pressed(5):
                        self.lcd.wait_button_release(5)
                        return 10
                    time.sleep(0.1)
            else:
                # Could analyze but protocol unknown - still partial success
                self.lcd.clear()
                self.lcd.write_line(0, "SOLVED! +10pts")
                self.lcd.write_line(1, "Signal analyzed")

                time.sleep(2)
                self.lcd.write_line(1, "L:Back")

                logger.info("SubGHZ Challenge 3 completed (unknown protocol)")

                while True:
                    if self.lcd.button_pressed(5):
                        self.lcd.wait_button_release(5)
                        return 10
                    time.sleep(0.1)

        # Analysis failed
        self.lcd.clear()
        self.lcd.write_line(0, "ANALYSIS FAILED")
        self.lcd.write_line(1, "1:Retry L:Back")

        logger.info("SubGHZ Challenge 3 failed")

        while True:
            if self.lcd.button_pressed(1):
                self.lcd.wait_button_release(1)
                return self.challenge_3_analyze()
            elif self.lcd.button_pressed(5):
                self.lcd.wait_button_release(5)
                return 0

            time.sleep(0.1)

    def scan_all_frequencies(self) -> Dict[str, Dict]:
        """
        Utility: Scan all common SubGHZ frequencies

        Returns:
            dict: Results for each frequency band
        """
        self.lcd.clear()
        self.lcd.write_line(0, "Full band scan")
        self.lcd.write_line(1, "Please wait...")

        results = self.hackrf.scan_frequencies(
            duration_per_freq=2.0
        )

        return results

    def get_status(self) -> Dict:
        """Get current SubGHZ handler status"""
        return {
            'hackrf_status': self.hackrf.get_status(),
            'target_frequency': self.TARGET_FREQUENCY,
            'detection_threshold': self.DETECTION_THRESHOLD,
            'last_capture': self.last_capture_path
        }

    def close(self):
        """Clean up resources"""
        if self.hackrf:
            self.hackrf.cleanup()
        logger.info("SubGHZ handler closed")


# Test code
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format='[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s'
    )

    print("Testing SubGHZ handler...")
    print("Note: This requires LCD and HackRF hardware")

    try:
        # Test with mock LCD
        class MockLCD:
            def clear(self):
                print("[LCD] Clear")

            def write_line(self, line, text):
                print(f"[LCD L{line}] {text}")

            def button_pressed(self, btn):
                return False

            def wait_button_release(self, btn):
                pass

        lcd = MockLCD()

        # Test with simulated HackRF
        hackrf = HackRFHandler(simulation_mode=True)
        handler = SubGHZHandler(lcd, hackrf)

        print(f"\nStatus: {handler.get_status()}")

        print("\nTesting signal detection (simulated)...")
        # This would run the challenge in real scenario

        handler.close()
        print("\nSubGHZ handler test complete!")

    except Exception as e:
        print(f"Error: {e}")
        print("Make sure you're running on Raspberry Pi with hardware connected")
