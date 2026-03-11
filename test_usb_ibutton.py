#!/usr/bin/env python3
"""Quick test for USB iButton reader"""

import sys
import logging
from ibutton_usb_reader import IButtonUSBReader

logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(message)s'
)

print("=" * 60)
print("USB iButton Reader Test")
print("=" * 60)
print("\nPlace an iButton on the reader within 30 seconds...")
print("Press Ctrl+C to cancel\n")

try:
    reader = IButtonUSBReader("/dev/input/event1")
    ibutton_id = reader.read_blocking(timeout=30)

    if ibutton_id:
        print(f"\n✓ SUCCESS!")
        print(f"  iButton ID: {ibutton_id}")
        sys.exit(0)
    else:
        print("\n✗ TIMEOUT - No iButton detected")
        sys.exit(1)

except KeyboardInterrupt:
    print("\n\nTest cancelled by user")
    sys.exit(1)
except PermissionError:
    print("\n✗ ERROR: Permission denied")
    print("  Run with: sudo python3 test_usb_ibutton.py")
    sys.exit(1)
except Exception as e:
    print(f"\n✗ ERROR: {e}")
    sys.exit(1)
