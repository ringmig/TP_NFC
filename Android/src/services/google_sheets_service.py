#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Google Sheets service for managing attendance data.
"""

import logging
from typing import List, Dict, Optional, Any
from pathlib import Path
import json

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pickle

from ..models import GuestRecord


class GoogleSheetsService:
    """Service for interacting with Google Sheets."""
    
    def __init__(self, config: dict, logger: logging.Logger):
        """
        Initialize Google Sheets service.
        
        Args:
            config: Google Sheets configuration
            logger: Logger instance
        """
        self.config = config
        self.logger = logger
        self.creds = None
        self.service = None
        self.spreadsheet_id = config['spreadsheet_id']
        self.sheet_name = config.get('sheet_name', 'Sheet1')
        
    def authenticate(self) -> bool:
        """
        Authenticate with Google Sheets API.
        
        Returns:
            bool: True if authenticated successfully
        """
        try:
            token_file = Path(self.config['token_file'])
            creds_file = Path(self.config['credentials_file'])
            
            # Load existing token
            if token_file.exists():
                with open(token_file, 'rb') as token:
                    self.creds = pickle.load(token)
                    
            # If there are no (valid) credentials available, let the user log in
            if not self.creds or not self.creds.valid:
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    self.creds.refresh(Request())
                else:
                    if not creds_file.exists():
                        self.logger.error(f"Credentials file not found: {creds_file}")
                        self.logger.error("Please download credentials.json from Google Cloud Console")
                        return False
                        
                    flow = InstalledAppFlow.from_client_secrets_file(
                        str(creds_file), self.config['scopes'])
                    self.creds = flow.run_local_server(port=0)
                    
                # Save the credentials for the next run
                with open(token_file, 'wb') as token:
                    pickle.dump(self.creds, token)
                    
            # Build the service
            self.service = build('sheets', 'v4', credentials=self.creds)
            self.logger.info("Successfully authenticated with Google Sheets")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to authenticate with Google Sheets: {e}")
            return False
            
    def get_all_guests(self) -> List[GuestRecord]:
        """
        Fetch all guest records from the spreadsheet.
        
        Returns:
            List of GuestRecord objects
        """
        try:
            # Define the range to read (including phone number column)
            range_name = f"{self.sheet_name}!A:I"
            
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            
            if not values:
                self.logger.warning("No data found in spreadsheet")
                return []
                
            # First row should be headers
            headers = values[0] if values else []
            guests = []
            
            # Process each row (skip header)
            for row in values[1:]:
                try:
                    # Ensure we have at least the required fields
                    if len(row) >= 3:
                        # Handle UTF-8 BOM character that may appear in first column
                        id_str = row[0].strip().lstrip('\ufeff')
                        original_id = int(id_str)
                        firstname = row[1]
                        lastname = row[2]
                        
                        guest = GuestRecord(original_id, firstname, lastname)
                        
                        # Store phone number if available
                        if len(row) > 3 and row[3]:
                            guest.phone_number = row[3]
                        
                        # Check for existing check-ins (shifted by 1 column due to phone number)
                        if len(row) > 4 and row[4]:  # reception
                            guest.check_ins['reception'] = row[4]
                        if len(row) > 5 and row[5]:  # lio/lío
                            guest.check_ins['lio'] = row[5]
                            guest.check_ins['lío'] = row[5]  # Store for both variants
                        if len(row) > 6 and row[6]:  # juntos
                            guest.check_ins['juntos'] = row[6]
                        if len(row) > 7 and row[7]:  # experimental
                            guest.check_ins['experimental'] = row[7]
                        if len(row) > 8 and row[8]:  # unvrs
                            guest.check_ins['unvrs'] = row[8]
                            
                        guests.append(guest)
                        
                except (ValueError, IndexError) as e:
                    self.logger.error(f"Error processing row {row}: {e}")
                    continue
                    
            self.logger.info(f"Fetched {len(guests)} guests from spreadsheet")
            return guests
            
        except HttpError as e:
            self.logger.error(f"Error fetching data from Google Sheets: {e}")
            return []
            
    def find_guest_by_id(self, original_id: int) -> Optional[GuestRecord]:
        """
        Find a specific guest by their original ID.
        
        Args:
            original_id: Guest's original ID
            
        Returns:
            GuestRecord if found, None otherwise
        """
        try:
            # Get full row data including phone and check-ins
            range_name = f"{self.sheet_name}!A:I"
            
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            
            # Find the row with matching ID
            for i, row in enumerate(values[1:], start=2):  # Start from row 2 (skip header)
                if len(row) > 0:
                    # Handle UTF-8 BOM character
                    id_str = row[0].strip().lstrip('\ufeff')
                    if str(id_str) == str(original_id):
                        if len(row) >= 3:
                            guest = GuestRecord(int(id_str), row[1], row[2])
                        guest.row_number = i  # Store row number for updates
                        
                        # Store phone number if available
                        if len(row) > 3 and row[3]:
                            guest.phone_number = row[3]
                        
                        # Load check-in data (shifted by 1 column due to phone number)
                        if len(row) > 4 and row[4]:  # reception
                            guest.check_ins['reception'] = row[4]
                        if len(row) > 5 and row[5]:  # lio/lío
                            guest.check_ins['lio'] = row[5]
                            guest.check_ins['lío'] = row[5]  # Store for both variants
                        if len(row) > 6 and row[6]:  # juntos
                            guest.check_ins['juntos'] = row[6]
                        if len(row) > 7 and row[7]:  # experimental
                            guest.check_ins['experimental'] = row[7]
                        if len(row) > 8 and row[8]:  # unvrs
                            guest.check_ins['unvrs'] = row[8]
                            
                        return guest
                        
            self.logger.warning(f"Guest with ID {original_id} not found")
            return None
            
        except Exception as e:
            self.logger.error(f"Error finding guest {original_id}: {e}")
            return None
            
    def mark_attendance(self, original_id: int, station: str, timestamp: str = "X") -> bool:
        """
        Mark attendance for a guest at a specific station.
        
        Args:
            original_id: Guest's original ID
            station: Station name (reception, lio, juntos, experimental, unvrs)
            timestamp: Value to put in the cell (default "X")
            
        Returns:
            bool: True if successful
        """
        try:
            # First, find the guest to get their row number
            guest = self.find_guest_by_id(original_id)
            if not guest:
                return False
                
            # Map station names to column letters (shifted by 1 due to phone number in column D)
            station_columns = {
                'reception': 'E',
                'lio': 'F',
                'lío': 'F',  # Handle accent mark
                'juntos': 'G',
                'experimental': 'H',
                'unvrs': 'I'
            }
            
            column = station_columns.get(station.lower())
            if not column:
                self.logger.error(f"Unknown station: {station}")
                return False
                
            # Update the specific cell
            range_name = f"{self.sheet_name}!{column}{guest.row_number}"
            
            body = {
                'values': [[timestamp]]
            }
            
            self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=range_name,
                valueInputOption='RAW',
                body=body
            ).execute()
            
            self.logger.info(f"Marked attendance for guest {original_id} at {station}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error marking attendance: {e}")
            return False
            
    def get_station_column(self, station: str) -> str:
        """Get the column letter for a given station."""
        station_columns = {
            'reception': 'E',
            'lio': 'F',
            'lío': 'F',  # Handle accent mark
            'juntos': 'G',
            'experimental': 'H',
            'unvrs': 'I'
        }
        return station_columns.get(station.lower(), '')
        
    def batch_update_attendance(self, updates: List[Dict[str, Any]]) -> bool:
        """
        Perform batch updates for multiple attendance marks.
        
        Args:
            updates: List of dicts with 'original_id', 'station', and 'timestamp'
            
        Returns:
            bool: True if successful
        """
        try:
            # Build batch update request
            requests = []
            
            for update in updates:
                guest = self.find_guest_by_id(update['original_id'])
                if not guest:
                    continue
                    
                column = self.get_station_column(update['station'])
                if not column:
                    continue
                    
                requests.append({
                    'range': f"{self.sheet_name}!{column}{guest.row_number}",
                    'values': [[update.get('timestamp', 'X')]]
                })
                
            if not requests:
                return False
                
            body = {
                'valueInputOption': 'RAW',
                'data': requests
            }
            
            self.service.spreadsheets().values().batchUpdate(
                spreadsheetId=self.spreadsheet_id,
                body=body
            ).execute()
            
            self.logger.info(f"Batch updated {len(requests)} attendance records")
            return True
            
        except Exception as e:
            self.logger.error(f"Error in batch update: {e}")
            return False
            
    def clear_all_check_in_data(self) -> bool:
        """Clear all check-in data from Google Sheets (columns D-H)."""
        try:
            # Get all rows to determine range
            range_name = f"{self.sheet_name}!A:H"
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            if len(values) <= 1:  # Only header row or empty
                self.logger.info("No check-in data to clear")
                return True
                
            # Clear check-in columns (E-I) for all data rows (D is phone number)
            clear_range = f"{self.sheet_name}!E2:I{len(values)}"
            
            # Create empty values for clearing
            clear_values = [[""] * 5 for _ in range(len(values) - 1)]  # 5 columns, all rows except header
            
            body = {
                'values': clear_values
            }
            
            self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=clear_range,
                valueInputOption='RAW',
                body=body
            ).execute()
            
            self.logger.warning(f"Cleared all check-in data from Google Sheets ({len(clear_values)} rows)")
            return True
            
        except Exception as e:
            self.logger.error(f"Error clearing Google Sheets data: {e}")
            return False