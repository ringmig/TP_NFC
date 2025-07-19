#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TP_NFC main application

This is the entry point for the TP_NFC attendance tracking system.
Configuration parameters should be modified in config/config.json, not in this file.
"""

import os
import sys
import json
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.logger import setup_logger
from src.services import NFCService, GoogleSheetsService, TagManager
from src.gui import create_gui


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
        # Initialize services
        logger.info("Initializing services...")

        # NFC Service
        nfc_service = NFCService(logger)
        if not nfc_service.connect():
            logger.warning("Failed to connect to NFC reader - continuing anyway")
            # Continue anyway - reader might be connected later
        else:
            logger.info("NFC reader connected successfully")

        # Google Sheets Service
        sheets_service = GoogleSheetsService(config['google_sheets'], logger)
        if not sheets_service.authenticate():
            logger.warning("Failed to authenticate with Google Sheets - continuing anyway")
            # Continue anyway - might work in offline mode
        else:
            logger.info("Google Sheets authenticated successfully")

        # Tag Manager
        tag_manager = TagManager(nfc_service, sheets_service, logger)
        logger.info("Tag manager initialized")

        # Create and run GUI
        logger.info("Starting GUI application...")
        app = create_gui(config, nfc_service, sheets_service, tag_manager, logger)

        # Set sync completion callback after GUI is created
        tag_manager.set_sync_completion_callback(app.on_sync_completed)

        # Run the GUI main loop
        app.mainloop()

    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)
        return 1
    finally:
        # Cleanup
        if 'tag_manager' in locals():
            tag_manager.shutdown()
            logger.info("Tag manager shut down")
        if 'nfc_service' in locals() and nfc_service.is_connected:
            nfc_service.disconnect()
            logger.info("NFC service disconnected")

    logger.info("Application finished")
    return 0


if __name__ == "__main__":
    sys.exit(main())
