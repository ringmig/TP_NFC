#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuration service for Android app
"""

import json
import os
from pathlib import Path
from typing import Dict, Any

class ConfigService:
    """Handles application configuration for Android"""
    
    def __init__(self):
        # Android app storage paths
        self.app_dir = self._get_app_directory()
        self.config_dir = self.app_dir / "config"
        self.logs_dir = self.app_dir / "logs"
        
        # Ensure directories exist
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
    def _get_app_directory(self) -> Path:
        """Get the application data directory for Android"""
        # Try to get Android app directory
        try:
            from android.storage import app_storage_path
            return Path(app_storage_path())
        except ImportError:
            # Fallback for desktop testing
            return Path.home() / ".tpnfc_android"
    
    def load_config(self) -> Dict[str, Any]:
        """Load application configuration"""
        config_file = self.config_dir / "config.json"
        
        # Default configuration for Android
        default_config = {
            "app_name": "TP_NFC_Android",
            "version": "1.0.0",
            "log_level": "INFO",
            "log_file": str(self.logs_dir / "TP_NFC_Android.log"),
            "google_sheets": {
                "spreadsheet_id": "1x1HvvfYYp-SlhljTP5lebyZLAu21PVNEDTAe8w3SR-A",
                "credentials_file": str(self.config_dir / "credentials.json"),
                "token_file": str(self.config_dir / "token.json"),
                "scopes": ["https://www.googleapis.com/auth/spreadsheets"],
                "sheet_name": "Sheet1"
            },
            "stations": [
                "Reception",
                "Lio", 
                "Juntos",
                "Experimental",
                "Unvrs"
            ],
            "ui": {
                "theme": "dark",
                "primary_color": "blue",
                "accent_color": "orange"
            },
            "nfc": {
                "read_timeout": 10,
                "auto_scan": True
            },
            "developer": {
                "password": "8888"
            }
        }
        
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    # Merge with defaults
                    default_config.update(user_config)
            except Exception as e:
                print(f"Error loading config: {e}")
        else:
            # Save default config
            self.save_config(default_config)
        
        return default_config
    
    def save_config(self, config: Dict[str, Any]) -> None:
        """Save configuration to file"""
        config_file = self.config_dir / "config.json"
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def get_config_dir(self) -> Path:
        """Get configuration directory path"""
        return self.config_dir
    
    def get_logs_dir(self) -> Path:
        """Get logs directory path""" 
        return self.logs_dir