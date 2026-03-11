#!/usr/bin/env python3
"""
HackRF Handler for ZeroRange
Low-level interface for HackRF One SDR via hackrf_transfer and related tools
"""

import subprocess
import os
import time
import logging
import re
from typing import Optional, Dict, Tuple, List
from pathlib import Path

logger = logging.getLogger(__name__)

# Default capture directory
CAPTURE_DIR = Path("/tmp/zerorange_subghz")


class HackRFHandler:
    """Handles HackRF One hardware interface via command-line tools"""

    # Common SubGHZ frequencies (in Hz)
    FREQUENCIES = {
        '315MHz': 315000000,
        '433MHz': 433920000,
        '868MHz': 868000000,
        '915MHz': 915000000,
    }

    # Default parameters
    DEFAULT_SAMPLE_RATE = 2000000  # 2 MHz
    DEFAULT_LNA_GAIN = 32  # 0-40 dB
    DEFAULT_VGA_GAIN = 20  # 0-62 dB
    DEFAULT_TX_GAIN = 47  # 0-47 dB

    def __init__(self, simulation_mode: bool = False):
        """
        Initialize HackRF handler

        Args:
            simulation_mode: If True, simulate responses without hardware
        """
        self.simulation_mode = simulation_mode
        self.device_connected = False
        self.current_frequency = self.FREQUENCIES['433MHz']

        # Create capture directory
        CAPTURE_DIR.mkdir(parents=True, exist_ok=True)

        # Check if HackRF is available
        if not simulation_mode:
            self.device_connected = self._check_device()
        else:
            logger.info("HackRF running in simulation mode")
            self.device_connected = True

        if self.device_connected:
            logger.info("HackRF handler initialized")
        else:
            logger.warning("HackRF not detected - limited functionality")

    def _check_device(self) -> bool:
        """
        Check if HackRF device is connected

        Returns:
            bool: True if device is found
        """
        try:
            result = subprocess.run(
                ['hackrf_info'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0 and 'Serial number' in result.stdout:
                # Extract serial number for logging
                match = re.search(r'Serial number:\s*(\w+)', result.stdout)
                if match:
                    logger.info(f"HackRF detected: {match.group(1)}")
                return True
            else:
                logger.warning("HackRF not found")
                return False

        except FileNotFoundError:
            logger.error("hackrf_info not installed - run: sudo apt install hackrf")
            return False
        except subprocess.TimeoutExpired:
            logger.error("hackrf_info timed out")
            return False
        except Exception as e:
            logger.error(f"Error checking HackRF: {e}")
            return False

    def is_connected(self) -> bool:
        """Check if HackRF is connected"""
        if self.simulation_mode:
            return True
        return self._check_device()

    def set_frequency(self, freq_hz: int) -> bool:
        """
        Set the operating frequency

        Args:
            freq_hz: Frequency in Hz

        Returns:
            bool: True if valid frequency
        """
        # HackRF One range: 1 MHz to 6 GHz
        if 1000000 <= freq_hz <= 6000000000:
            self.current_frequency = freq_hz
            logger.info(f"Frequency set to {freq_hz / 1000000:.3f} MHz")
            return True
        else:
            logger.error(f"Invalid frequency: {freq_hz}")
            return False

    def capture_signal(
        self,
        duration_seconds: float = 5.0,
        frequency: Optional[int] = None,
        filename: Optional[str] = None
    ) -> Tuple[bool, Optional[str], Dict]:
        """
        Capture RF signal to file

        Args:
            duration_seconds: Capture duration
            frequency: Frequency in Hz (uses current if None)
            filename: Output filename (auto-generated if None)

        Returns:
            tuple: (success, filepath, signal_info)
        """
        freq = frequency or self.current_frequency

        if filename is None:
            timestamp = int(time.time())
            filename = f"capture_{freq}_{timestamp}.raw"

        filepath = CAPTURE_DIR / filename

        if self.simulation_mode:
            # Simulate capture
            logger.info(f"[SIM] Capturing {duration_seconds}s at {freq/1e6:.3f} MHz")
            time.sleep(min(duration_seconds, 2))  # Shortened for simulation

            # Create dummy file
            with open(filepath, 'wb') as f:
                f.write(b'\x00' * 1024)  # Dummy data

            signal_info = {
                'frequency': freq,
                'duration': duration_seconds,
                'sample_rate': self.DEFAULT_SAMPLE_RATE,
                'file_size': 1024,
                'detected': True,
                'signal_strength': -45  # dBm (simulated)
            }
            return (True, str(filepath), signal_info)

        # Real capture with hackrf_transfer
        try:
            # Calculate number of samples
            num_samples = int(duration_seconds * self.DEFAULT_SAMPLE_RATE)

            cmd = [
                'hackrf_transfer',
                '-r', str(filepath),
                '-f', str(freq),
                '-s', str(self.DEFAULT_SAMPLE_RATE),
                '-l', str(self.DEFAULT_LNA_GAIN),
                '-g', str(self.DEFAULT_VGA_GAIN),
                '-n', str(num_samples)
            ]

            logger.info(f"Starting capture: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=duration_seconds + 10
            )

            if result.returncode == 0 and filepath.exists():
                file_size = filepath.stat().st_size

                signal_info = {
                    'frequency': freq,
                    'duration': duration_seconds,
                    'sample_rate': self.DEFAULT_SAMPLE_RATE,
                    'file_size': file_size,
                    'detected': file_size > 1000,
                    'signal_strength': self._estimate_signal_strength(filepath)
                }

                logger.info(f"Capture complete: {file_size} bytes")
                return (True, str(filepath), signal_info)
            else:
                logger.error(f"Capture failed: {result.stderr}")
                return (False, None, {'error': result.stderr})

        except subprocess.TimeoutExpired:
            logger.error("Capture timed out")
            return (False, None, {'error': 'timeout'})
        except Exception as e:
            logger.error(f"Capture error: {e}")
            return (False, None, {'error': str(e)})

    def replay_signal(
        self,
        filepath: str,
        frequency: Optional[int] = None,
        repeat: int = 1
    ) -> bool:
        """
        Replay a captured signal

        Args:
            filepath: Path to captured signal file
            frequency: Transmission frequency (uses capture freq if None)
            repeat: Number of times to repeat

        Returns:
            bool: True if replay successful
        """
        freq = frequency or self.current_frequency

        if not os.path.exists(filepath):
            logger.error(f"Signal file not found: {filepath}")
            return False

        if self.simulation_mode:
            logger.info(f"[SIM] Replaying signal at {freq/1e6:.3f} MHz (x{repeat})")
            time.sleep(1)
            return True

        try:
            for i in range(repeat):
                cmd = [
                    'hackrf_transfer',
                    '-t', filepath,
                    '-f', str(freq),
                    '-s', str(self.DEFAULT_SAMPLE_RATE),
                    '-x', str(self.DEFAULT_TX_GAIN)
                ]

                logger.info(f"Replaying ({i+1}/{repeat}): {' '.join(cmd)}")

                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                if result.returncode != 0:
                    logger.error(f"Replay failed: {result.stderr}")
                    return False

                if i < repeat - 1:
                    time.sleep(0.5)  # Gap between repeats

            logger.info("Replay complete")
            return True

        except subprocess.TimeoutExpired:
            logger.error("Replay timed out")
            return False
        except Exception as e:
            logger.error(f"Replay error: {e}")
            return False

    def scan_frequencies(
        self,
        frequencies: Optional[List[int]] = None,
        duration_per_freq: float = 2.0
    ) -> Dict[int, Dict]:
        """
        Scan multiple frequencies for signals

        Args:
            frequencies: List of frequencies to scan (uses defaults if None)
            duration_per_freq: Time to listen on each frequency

        Returns:
            dict: {frequency: signal_info} for detected signals
        """
        if frequencies is None:
            frequencies = list(self.FREQUENCIES.values())

        results = {}

        for freq in frequencies:
            logger.info(f"Scanning {freq/1e6:.3f} MHz...")
            success, filepath, info = self.capture_signal(
                duration_seconds=duration_per_freq,
                frequency=freq
            )

            if success and info.get('detected'):
                results[freq] = info

                # Clean up temp file
                if filepath and os.path.exists(filepath):
                    os.remove(filepath)

        return results

    def detect_signal(
        self,
        timeout: int = 10,
        frequency: Optional[int] = None,
        threshold_dbm: float = -60
    ) -> Tuple[bool, Optional[Dict]]:
        """
        Wait for signal detection above threshold

        Args:
            timeout: Maximum time to wait
            frequency: Frequency to monitor
            threshold_dbm: Signal strength threshold

        Returns:
            tuple: (detected, signal_info)
        """
        freq = frequency or self.current_frequency
        start_time = time.time()

        while time.time() - start_time < timeout:
            success, filepath, info = self.capture_signal(
                duration_seconds=1.0,
                frequency=freq
            )

            if success and info.get('signal_strength', -100) > threshold_dbm:
                logger.info(f"Signal detected at {freq/1e6:.3f} MHz: {info['signal_strength']} dBm")

                # Keep the capture file for potential replay
                return (True, info)

            # Clean up temp file
            if filepath and os.path.exists(filepath):
                os.remove(filepath)

            time.sleep(0.5)

        return (False, None)

    def analyze_signal(self, filepath: str) -> Dict:
        """
        Analyze a captured signal for protocol identification

        Args:
            filepath: Path to captured signal file

        Returns:
            dict: Analysis results including potential protocol
        """
        if not os.path.exists(filepath):
            return {'error': 'File not found'}

        if self.simulation_mode:
            # Return simulated analysis
            return {
                'file': filepath,
                'protocol': 'OOK/ASK',
                'modulation': 'OOK',
                'data_rate': 1000,
                'encoding': 'Manchester',
                'possible_protocols': ['garage_door', 'car_key', 'doorbell'],
                'confidence': 0.75
            }

        try:
            # Get file size for basic analysis
            file_size = os.path.getsize(filepath)

            # Basic signal analysis (would use more sophisticated tools in production)
            analysis = {
                'file': filepath,
                'file_size': file_size,
                'sample_rate': self.DEFAULT_SAMPLE_RATE,
                'duration': file_size / (2 * self.DEFAULT_SAMPLE_RATE),
                'protocol': 'Unknown',
                'modulation': 'Unknown'
            }

            # Try to use rtl_433 for protocol detection if available
            try:
                result = subprocess.run(
                    ['rtl_433', '-r', filepath, '-A'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )

                if 'Protocol' in result.stdout:
                    analysis['protocol'] = 'Detected (see rtl_433 output)'
                    analysis['rtl_433_output'] = result.stdout[:500]

            except (FileNotFoundError, subprocess.TimeoutExpired):
                pass  # rtl_433 not available

            return analysis

        except Exception as e:
            logger.error(f"Analysis error: {e}")
            return {'error': str(e)}

    def _estimate_signal_strength(self, filepath: str) -> float:
        """
        Estimate signal strength from captured file

        Args:
            filepath: Path to captured file

        Returns:
            float: Estimated signal strength in dBm
        """
        try:
            # Read a sample of the file and estimate power
            with open(filepath, 'rb') as f:
                data = f.read(10000)

            if len(data) < 100:
                return -100  # No signal

            # Simple RMS calculation for I/Q samples (8-bit signed)
            samples = [int.from_bytes([b], 'little', signed=True) for b in data]
            rms = (sum(s**2 for s in samples) / len(samples)) ** 0.5

            # Convert to approximate dBm (calibration needed for accuracy)
            if rms > 0:
                dbm = 20 * (rms / 128) - 60  # Rough estimation
                return max(-100, min(0, dbm))
            return -100

        except Exception as e:
            logger.error(f"Error estimating signal strength: {e}")
            return -100

    def get_status(self) -> Dict:
        """
        Get current HackRF status

        Returns:
            dict: Status information
        """
        return {
            'connected': self.device_connected,
            'simulation_mode': self.simulation_mode,
            'current_frequency': self.current_frequency,
            'frequency_mhz': self.current_frequency / 1e6,
            'sample_rate': self.DEFAULT_SAMPLE_RATE,
            'capture_dir': str(CAPTURE_DIR)
        }

    def cleanup(self):
        """Clean up temporary files"""
        try:
            for f in CAPTURE_DIR.glob('capture_*.raw'):
                f.unlink()
            logger.info("Cleaned up temporary captures")
        except Exception as e:
            logger.error(f"Cleanup error: {e}")


# Test code
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format='[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s'
    )

    print("Testing HackRF handler...")

    # Test in simulation mode first
    handler = HackRFHandler(simulation_mode=True)

    print(f"\nStatus: {handler.get_status()}")

    print("\nTesting signal capture...")
    success, filepath, info = handler.capture_signal(duration_seconds=2.0)
    print(f"Capture result: {success}")
    print(f"Signal info: {info}")

    if filepath:
        print("\nTesting signal analysis...")
        analysis = handler.analyze_signal(filepath)
        print(f"Analysis: {analysis}")

    print("\nTesting frequency scan...")
    results = handler.scan_frequencies(
        frequencies=[315000000, 433920000],
        duration_per_freq=1.0
    )
    print(f"Scan results: {results}")

    handler.cleanup()
    print("\nHackRF handler test complete!")
