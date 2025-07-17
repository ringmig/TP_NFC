#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test NFC connectivity and basic functionality.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services import NFCService
from src.utils.logger import setup_logger


def main():
    """Test NFC reader connection and tag reading."""
    # Setup logger
    logger = setup_logger("NFC_Test", "DEBUG")
    
    print("NFC Reader Test")
    print("-" * 40)
    
    # Create NFC service (will auto-select best backend)
    nfc_service = NFCService(logger)
    
    # Try to connect
    print("Connecting to NFC reader...")
    if not nfc_service.connect():
        print("\nFailed to connect to NFC reader!")
        print("\nTroubleshooting:")
        print("1. Make sure NFC reader is connected via USB")
        print("2. On macOS with ACR122U:")
        print("   - Install pyscard: pip install pyscard")
        print("   - OR disable PC/SC: sudo kextunload -b com.apple.iokit.CSCRPCCardFamily")
        print("3. On Windows: Install reader drivers")
        print("4. Check no other NFC application is running")
        return 1
        
    print(f"Successfully connected using {nfc_service.backend_name} backend!")
    print("\nPlease tap an NFC tag on the reader...")
    
    try:
        # Read a tag
        tag = nfc_service.read_tag(timeout=10)
        
        if tag:
            print(f"\nTag detected!")
            print(f"UID: {tag.uid}")
            print(f"Tag info: {tag}")
        else:
            print("\nNo tag detected within timeout period.")
            
    except KeyboardInterrupt:
        print("\nTest cancelled by user.")
        
    finally:
        # Disconnect
        nfc_service.disconnect()
        print("\nTest completed.")
        
    return 0


if __name__ == "__main__":
    sys.exit(main())