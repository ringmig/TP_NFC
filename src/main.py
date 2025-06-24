#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
TP_NFC main application

This is the entry point for the TP_NFC application.
Configuration parameters should be modified in config/config.json, not in this file.
'''

import os
import sys
import json
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.logger import setup_logger


def load_config():
    """Load configuration from config file."""
    config_path = Path(__file__).parent.parent / 'config' / 'config.json'
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading configuration: {e}")
        sys.exit(1)


def main():
    """Main application entry point."""
    # Load configuration
    config = load_config()
    
    # Setup logging
    logger = setup_logger(config['app_name'], config['log_level'], config['log_file'])
    
    logger.info(f"Starting {config['app_name']} v{config['version']}")
    
    try:
        # Application logic goes here
        logger.info("Application initialized successfully")
        
        # Example usage of settings
        logger.debug(f"Settings: {config['settings']}")
        
    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)
        return 1
    
    logger.info("Application finished successfully")
    return 0


if __name__ == "__main__":
    sys.exit(main())
