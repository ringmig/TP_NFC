#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NFC Reader Diagnostic Tool for macOS
"""

import sys
import os
import subprocess
import platform

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import nfc
    NFC_INSTALLED = True
except ImportError:
    NFC_INSTALLED = False

try:
    import usb.core
    import usb.backend.libusb1
    USB_INSTALLED = True
except ImportError:
    USB_INSTALLED = False


def check_system():
    """Check system information."""
    print("System Information")
    print("-" * 40)
    print(f"Platform: {platform.system()} {platform.release()}")
    print(f"Python: {sys.version}")
    print(f"nfcpy installed: {NFC_INSTALLED}")
    print(f"pyusb installed: {USB_INSTALLED}")
    print()


def check_libusb():
    """Check if libusb is installed."""
    print("Checking libusb installation...")
    print("-" * 40)
    
    # Check if libusb is installed via Homebrew
    try:
        result = subprocess.run(['brew', 'list', 'libusb'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✓ libusb is installed via Homebrew")
            # Get libusb info
            info = subprocess.run(['brew', 'info', 'libusb'], 
                                capture_output=True, text=True)
            for line in info.stdout.split('\n'):
                if '/usr/local/Cellar/libusb' in line or '/opt/homebrew/Cellar/libusb' in line:
                    print(f"  Location: {line.strip()}")
                    break
        else:
            print("✗ libusb NOT found via Homebrew")
            print("  To install: brew install libusb")
    except FileNotFoundError:
        print("✗ Homebrew not found")
        print("  Install Homebrew first: https://brew.sh")
    
    print()


def list_usb_devices():
    """List all USB devices."""
    print("USB Devices")
    print("-" * 40)
    
    if not USB_INSTALLED:
        print("pyusb not installed. Install with: pip install pyusb")
        return
    
    try:
        # Try to find devices
        devices = list(usb.core.find(find_all=True))
        
        if not devices:
            print("No USB devices found (may need sudo)")
        else:
            print(f"Found {len(devices)} USB devices:")
            
            # Known NFC reader vendor/product IDs
            nfc_readers = {
                (0x072f, 0x2200): "ACR122U",
                (0x072f, 0x2100): "ACR122U (older)",
                (0x072f, 0x2224): "ACR1252U",
                (0x04e6, 0x5591): "SCL3711",
                (0x04e6, 0x5593): "SCL3712",
                (0x04cc, 0x2533): "ST Micro/Feig",
                (0x054c, 0x06c1): "Sony RC-S380",
                (0x054c, 0x06c3): "Sony RC-S380/P",
            }
            
            for device in devices:
                vid_pid = (device.idVendor, device.idProduct)
                reader_name = nfc_readers.get(vid_pid, "")
                
                if reader_name:
                    print(f"\n✓ NFC READER FOUND: {reader_name}")
                    print(f"  Vendor ID: 0x{device.idVendor:04x}")
                    print(f"  Product ID: 0x{device.idProduct:04x}")
                else:
                    # Only show if it might be an NFC reader
                    vendor_hex = f"{device.idVendor:04x}"
                    if vendor_hex in ['072f', '04e6', '04cc', '054c']:
                        print(f"\n? Possible NFC device:")
                        print(f"  Vendor ID: 0x{device.idVendor:04x}")
                        print(f"  Product ID: 0x{device.idProduct:04x}")
                        
    except usb.core.USBError as e:
        print(f"USB Error: {e}")
        print("\nTry running with sudo if permission denied")
    except Exception as e:
        print(f"Error listing USB devices: {e}")
    
    print()


def test_nfc_connection():
    """Test NFC connection with detailed error info."""
    print("Testing NFC Connection")
    print("-" * 40)
    
    if not NFC_INSTALLED:
        print("✗ nfcpy not installed")
        return
    
    # Test different connection strings
    connection_strings = [
        'usb',
        'usb:072f:2200',  # ACR122U
        'usb:04e6:5591',  # SCL3711
    ]
    
    for conn_str in connection_strings:
        print(f"\nTrying: {conn_str}")
        try:
            clf = nfc.ContactlessFrontend()
            if clf.open(conn_str):
                print(f"✓ SUCCESS! Connected with: {conn_str}")
                print(f"  Device: {clf.device}")
                clf.close()
                return True
            else:
                print(f"✗ Failed to open with {conn_str}")
        except Exception as e:
            print(f"✗ Error: {e}")
    
    return False


def show_troubleshooting():
    """Show troubleshooting steps."""
    print("\nTroubleshooting Steps")
    print("-" * 40)
    print("1. Install libusb (if not installed):")
    print("   brew install libusb")
    print()
    print("2. Install Python USB libraries:")
    print("   pip install pyusb")
    print()
    print("3. For ACR122U on macOS:")
    print("   - You may need to unload the PC/SC driver:")
    print("     sudo kextunload -b com.apple.iokit.CSCRPCCardFamily")
    print("   - To reload it later:")
    print("     sudo kextload -b com.apple.iokit.CSCRPCCardFamily")
    print()
    print("4. Try running with sudo (for USB permissions):")
    print("   sudo python test_nfc.py")
    print()
    print("5. Make sure no other NFC software is running")
    print("   (e.g., NFC Tools, TagWriter, etc.)")


def main():
    """Run diagnostic tests."""
    print("NFC Reader Diagnostic Tool")
    print("=" * 40)
    print()
    
    check_system()
    check_libusb()
    list_usb_devices()
    
    if test_nfc_connection():
        print("\n✓ NFC reader is working!")
    else:
        print("\n✗ Could not connect to NFC reader")
        show_troubleshooting()
    
    print("\nDiagnostic complete.")


if __name__ == "__main__":
    main()