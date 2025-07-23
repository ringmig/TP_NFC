#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to verify Android project structure (without external dependencies)
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def test_structure():
    """Test project structure and basic imports"""
    
    print("Testing Android project structure...")
    
    # Check directory structure
    base_path = Path(__file__).parent
    required_dirs = [
        'src',
        'src/gui', 'src/gui/screens', 'src/gui/components', 'src/gui/layouts',
        'src/services', 'src/models', 'src/utils',
        'assets'
    ]
    
    for dir_path in required_dirs:
        full_path = base_path / dir_path
        if full_path.exists():
            print(f"✅ Directory exists: {dir_path}")
        else:
            print(f"❌ Missing directory: {dir_path}")
            return False
    
    # Check key files
    required_files = [
        'main.py',
        'buildozer.spec', 
        'requirements.txt',
        'README.md',
        'src/services/config_service.py',
        'src/services/android_nfc_service.py',
        'src/utils/logger.py',
        'src/gui/screens/main_screen.py'
    ]
    
    for file_path in required_files:
        full_path = base_path / file_path
        if full_path.exists():
            print(f"✅ File exists: {file_path}")
        else:
            print(f"❌ Missing file: {file_path}")
            return False
    
    # Test basic imports (without external dependencies)
    try:
        from src.services.config_service import ConfigService
        print("✅ ConfigService can be imported")
        
        from src.utils.logger import setup_logger
        print("✅ Logger utility can be imported")
        
        from src.services.android_nfc_service import AndroidNFCService
        print("✅ Android NFC service can be imported")
        
        # Test config creation
        config_service = ConfigService()
        config = config_service.load_config()
        print(f"✅ Config loaded with {len(config)} keys")
        
        # Test logger setup
        logger = setup_logger("test", "INFO")
        logger.info("Test log message")
        print("✅ Logger works correctly")
        
    except Exception as e:
        print(f"❌ Import/execution error: {e}")
        return False
    
    print("\n🎉 Android project structure is complete and ready!")
    print("\nNext steps:")
    print("1. Install dependencies: pip install -r requirements.txt")
    print("2. Add Google Sheets credentials to src/config/")
    print("3. Test on Android device: buildozer android debug")
    
    return True

if __name__ == '__main__':
    success = test_structure()
    sys.exit(0 if success else 1)