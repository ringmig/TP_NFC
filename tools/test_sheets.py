#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Google Sheets connectivity and basic operations.
"""

import sys
import os
import json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.google_sheets_service import GoogleSheetsService
from src.utils.logger import setup_logger


def main():
    """Test Google Sheets connection and operations."""
    # Setup logger
    logger = setup_logger("Sheets_Test", "DEBUG")
    
    # Load config
    with open('config/config.json', 'r') as f:
        config = json.load(f)
    
    print("Google Sheets Test")
    print("-" * 40)
    
    # Check if spreadsheet ID is configured
    if config['google_sheets']['spreadsheet_id'] == "YOUR_SPREADSHEET_ID_HERE":
        print("\nERROR: Please configure your Google Sheets ID in config/config.json")
        print("You need to:")
        print("1. Open your Google Sheet")
        print("2. Copy the ID from the URL: docs.google.com/spreadsheets/d/[THIS_IS_THE_ID]/edit")
        print("3. Paste it in config/config.json")
        return 1
    
    # Create sheets service
    sheets_service = GoogleSheetsService(config['google_sheets'], logger)
    
    print("\nAuthenticating with Google Sheets...")
    if not sheets_service.authenticate():
        print("\nAuthentication failed!")
        print("\nTo set up Google Sheets access:")
        print("1. Go to https://console.cloud.google.com/")
        print("2. Create a new project or select existing")
        print("3. Enable Google Sheets API")
        print("4. Create credentials (OAuth 2.0 Client ID)")
        print("5. Download as 'credentials.json' and place in config/ folder")
        return 1
        
    print("Successfully authenticated!")
    
    # Test reading guests
    print("\nFetching guest list...")
    guests = sheets_service.get_all_guests()
    
    if guests:
        print(f"\nFound {len(guests)} guests:")
        # Show first 5 guests
        for guest in guests[:5]:
            print(f"  - {guest.original_id}: {guest.full_name}")
        if len(guests) > 5:
            print(f"  ... and {len(guests) - 5} more")
    else:
        print("\nNo guests found or unable to read sheet")
        print("Make sure your sheet has the correct format:")
        print("Columns: originalid, firstname, lastname, reception, lio, juntos, experimental, unvrs")
        
    # Test finding a specific guest
    if guests:
        test_id = guests[0].original_id
        print(f"\nTesting find by ID with guest {test_id}...")
        found_guest = sheets_service.find_guest_by_id(test_id)
        if found_guest:
            print(f"Found: {found_guest}")
        else:
            print("Failed to find guest")
            
    print("\nTest completed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())