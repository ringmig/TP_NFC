#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to verify Android project structure and imports
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def test_imports():
    """Test that all core modules can be imported"""
    
    print("Testing Android project imports...")
    
    try:
        # Test config service
        from src.services.config_service import ConfigService
        print("✅ ConfigService imported successfully")
        
        # Test models
        from src.models.guest_record import GuestRecord
        from src.models.nfc_tag import NFCTag
        print("✅ Models imported successfully")
        
        # Test services
        from src.services.google_sheets_service import GoogleSheetsService
        from src.services.check_in_queue import CheckInQueue
        from src.services.tag_manager import TagManager
        print("✅ Core services imported successfully")
        
        # Test Android NFC service
        from src.services.android_nfc_service import AndroidNFCService
        print("✅ Android NFC service imported successfully")
        
        # Test logger
        from src.utils.logger import setup_logger
        print("✅ Logger utility imported successfully")
        
        # Test config loading
        config_service = ConfigService()
        config = config_service.load_config()
        print(f"✅ Config loaded: {len(config)} keys")
        
        print("\n🎉 All imports successful! Android project structure is ready.")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == '__main__':
    success = test_imports()
    sys.exit(0 if success else 1)