#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test NFC connectivity with pyscard (macOS-friendly).
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.pyscard_nfc_service import PyscardNFCService
from src.utils.logger import setup_logger


def main():
    """Test NFC reader connection and tag reading with pyscard."""
    # Setup logger
    logger = setup_logger("NFC_Test_Pyscard", "DEBUG")
    
    print("NFC Reader Test (pyscard)")
    print("-" * 40)
    
    # Check if pyscard is installed
    try:
        import smartcard
        print("✓ pyscard is installed")
    except ImportError:
        print("✗ pyscard not installed!")
        print("\nTo install:")
        print("pip install pyscard")
        return 1
    
    # Create NFC service
    nfc_service = PyscardNFCService(logger)
    
    # Try to connect
    print("\nConnecting to NFC reader...")
    if not nfc_service.connect():
        print("\nFailed to connect to NFC reader!")
        print("\nTroubleshooting:")
        print("1. Make sure NFC reader is connected via USB")
        print("2. On macOS, smart card drivers are built-in")
        print("3. Try: pip install --upgrade pyscard")
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