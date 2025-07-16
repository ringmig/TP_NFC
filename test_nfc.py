#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test NFC connectivity and basic functionality.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.nfc_service import NFCService
from src.utils.logger import setup_logger


def main():
    """Test NFC reader connection and tag reading."""
    # Setup logger
    logger = setup_logger("NFC_Test", "DEBUG")
    
    # Create NFC service
    nfc_service = NFCService(logger)
    
    print("NFC Reader Test")
    print("-" * 40)
    
    # Try to connect
    print("Connecting to NFC reader...")
    if not nfc_service.connect():
        print("Failed to connect to NFC reader!")
        print("Make sure:")
        print("1. NFC reader is connected via USB")
        print("2. Drivers are installed")
        print("3. No other application is using the reader")
        return 1
        
    print("Successfully connected to NFC reader!")
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