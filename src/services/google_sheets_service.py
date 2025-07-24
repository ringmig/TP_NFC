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
import time
import ssl
import socket

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
        self._cached_stations = None  # Cache for dynamic station detection
        self._connection_retries = 3  # Number of retries for network errors
        
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
                    
            # Build the service with threading-safe configuration
            # This addresses WRONG_VERSION_NUMBER errors in threaded environments
            # by ensuring each service instance has its own HTTP connection
            
            try:
                # Force use of modern TLS by setting environment-level SSL context
                ssl_context = ssl.create_default_context()
                ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
                
                # Build service - the google-api-python-client will use the default SSL context
                self.service = build('sheets', 'v4', credentials=self.creds, cache_discovery=False)
                self.logger.info("Successfully authenticated with Google Sheets")
                
            except Exception as ssl_error:
                self.logger.warning(f"SSL context setup failed: {ssl_error}")
                # Try with basic build as fallback
                self.service = build('sheets', 'v4', credentials=self.creds, cache_discovery=False)
                self.logger.info("Successfully authenticated with Google Sheets (fallback)")
                
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to authenticate with Google Sheets: {e}")
            return False

    def _get_thread_safe_service(self):
        """
        Get a thread-safe service instance. 
        This addresses WRONG_VERSION_NUMBER errors in concurrent scenarios.
        """
        # For each API call in a thread, create a fresh service instance
        # This prevents HTTP connection sharing issues
        try:
            return build('sheets', 'v4', credentials=self.creds, cache_discovery=False)
        except Exception:
            # Fallback to shared service instance
            return self.service

    def _make_api_call(self, api_call_func, *args, **kwargs):
        """Make a resilient API call with retry logic for connection issues."""
        for attempt in range(self._connection_retries):
            try:
                return api_call_func(*args, **kwargs)
            except (ssl.SSLError, socket.error, ConnectionError, OSError) as e:
                if attempt < self._connection_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                    self.logger.debug(f"Network error (attempt {attempt + 1}), retrying in {wait_time}s: {e}")
                    time.sleep(wait_time)
                    continue
                else:
                    # Final attempt failed
                    raise e
            except HttpError as e:
                # Retry certain HTTP errors that may be transient
                if e.resp.status in [500, 502, 503, 504] and attempt < self._connection_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    self.logger.debug(f"HTTP error {e.resp.status} (attempt {attempt + 1}), retrying in {wait_time}s")
                    time.sleep(wait_time)
                    continue
                else:
                    # Don't retry client errors (4xx) or final attempt
                    raise e
            except Exception as e:
                # Non-network errors should not be retried
                raise e
    
    def get_dynamic_stations(self) -> Dict[str, str]:
        """
        Dynamically detect station columns from Google Sheets headers.
        
        Returns:
            Dict mapping station names (lowercase) to column letters
        """
        try:
            if self._cached_stations is not None:
                return self._cached_stations
                
            # Get first row (headers) from spreadsheet with retry logic
            range_name = f"{self.sheet_name}!1:1"
            result = self._make_api_call(
                lambda: self._get_thread_safe_service().spreadsheets().values().get(
                    spreadsheetId=self.spreadsheet_id,
                    range=range_name
                ).execute()
            )
            
            headers = result.get('values', [[]])[0] if result.get('values') else []
            
            # Build station mapping dynamically
            station_columns = {}
            
            # Known fixed columns (originalid, firstname, lastname)
            expected_fixed_cols = ['originalid', 'firstname', 'lastname']
            
            # Start from column D (index 3) to look for station headers
            for i, header in enumerate(headers[3:], start=3):
                try:
                    if header and isinstance(header, str) and header.strip():  # Only process string headers
                        # Skip any non-alphabetic content (images, formulas, etc.)
                        header_clean = header.strip()
                        if header_clean.replace(' ', '').replace('_', '').replace('-', '').isalpha():
                            station_name = header_clean.lower()
                            column_letter = self._index_to_column_letter(i)
                            station_columns[station_name] = column_letter
                except Exception as e:
                    # Skip problematic headers (images, complex objects, etc.)
                    self.logger.debug(f"Skipping header at index {i}: {e}")
                    continue
            
            # Cache the result
            self._cached_stations = station_columns
            return station_columns
            
        except Exception as e:
            # Only log first error, then use debug for subsequent ones
            if not hasattr(self, '_dynamic_stations_error_logged'):
                self.logger.error(f"Error detecting dynamic stations: {e}")
                self._dynamic_stations_error_logged = True
            else:
                self.logger.debug(f"Dynamic stations API call failed: {e}")
            
            # Fallback to hardcoded stations (cached to avoid repeated failures)
            fallback_stations = {
                'reception': 'D',
                'lio': 'E', 
                'juntos': 'F',
                'experimental': 'G',
                'unvrs': 'H'
            }
            self._cached_stations = fallback_stations
            return fallback_stations
    
    def _index_to_column_letter(self, index: int) -> str:
        """Convert 0-based column index to Excel column letter (A, B, C, ..., Z, AA, AB, ...)"""
        result = ""
        while index >= 0:
            result = chr(index % 26 + ord('A')) + result
            index = index // 26 - 1
        return result
    
    def clear_station_cache(self):
        """Clear cached station mapping to force re-detection on next call."""
        self._cached_stations = None
            
    def get_all_guests(self) -> List[GuestRecord]:
        """
        Fetch all guest records from the spreadsheet.
        
        Returns:
            List of GuestRecord objects
        """
        try:
            # Get dynamic station mapping first
            station_columns = self.get_dynamic_stations()
            
            # Calculate the last column letter based on detected stations
            max_col_index = max([ord(col) - ord('A') for col in station_columns.values()] + [7])  # At least H
            last_col_letter = self._index_to_column_letter(max_col_index)
            
            # Define the range to read (dynamic based on detected stations)
            range_name = f"{self.sheet_name}!A:{last_col_letter}"
            
            result = self._make_api_call(
                lambda: self._get_thread_safe_service().spreadsheets().values().get(
                    spreadsheetId=self.spreadsheet_id,
                    range=range_name
                ).execute()
            )
            
            values = result.get('values', [])
            
            if not values:
                self.logger.warning("No data found in spreadsheet")
                return []
                
            # First row should be headers
            headers = values[0] if values else []
            guests = []
            
            # Create reverse mapping: column letter -> station name
            col_to_station = {col: station for station, col in station_columns.items()}
            
            # Get list of station names for GuestRecord initialization
            station_names = [station.title() for station in station_columns.keys()]
            
            # Process each row (skip header)
            for row in values[1:]:
                try:
                    # Ensure we have at least the required fields
                    if len(row) >= 3:
                        original_id = int(row[0])
                        firstname = row[1]
                        lastname = row[2]
                        
                        # Initialize guest with dynamic stations
                        guest = GuestRecord(original_id, firstname, lastname, station_names)
                        
                        # Dynamically load check-ins based on detected stations
                        for col_letter, station_name in col_to_station.items():
                            col_index = ord(col_letter) - ord('A')  # Convert A=0, B=1, etc.
                            if len(row) > col_index and row[col_index]:
                                guest.check_ins[station_name] = row[col_index]
                            
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
            # Get dynamic station mapping first
            station_columns = self.get_dynamic_stations()
            
            # Calculate the last column letter based on detected stations
            max_col_index = max([ord(col) - ord('A') for col in station_columns.values()] + [7])  # At least H
            last_col_letter = self._index_to_column_letter(max_col_index)
            
            # Get full row data including check-ins
            range_name = f"{self.sheet_name}!A:{last_col_letter}"
            
            result = self._make_api_call(
                lambda: self._get_thread_safe_service().spreadsheets().values().get(
                    spreadsheetId=self.spreadsheet_id,
                    range=range_name
                ).execute()
            )
            
            values = result.get('values', [])
            
            # Create reverse mapping: column letter -> station name
            col_to_station = {col: station for station, col in station_columns.items()}
            
            # Get list of station names for GuestRecord initialization
            station_names = [station.title() for station in station_columns.keys()]
            
            # Find the row with matching ID
            for i, row in enumerate(values[1:], start=2):  # Start from row 2 (skip header)
                if len(row) > 0 and str(row[0]) == str(original_id):
                    if len(row) >= 3:
                        # Initialize guest with dynamic stations
                        guest = GuestRecord(int(row[0]), row[1], row[2], station_names)
                        guest.row_number = i  # Store row number for updates
                        
                        # Dynamically load check-in data based on detected stations
                        for col_letter, station_name in col_to_station.items():
                            col_index = ord(col_letter) - ord('A')  # Convert A=0, B=1, etc.
                            if len(row) > col_index and row[col_index]:
                                guest.check_ins[station_name] = row[col_index]
                            
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
            station: Station name (dynamically detected from headers)
            timestamp: Value to put in the cell (default "X")
            
        Returns:
            bool: True if successful
        """
        try:
            # First, find the guest to get their row number
            guest = self.find_guest_by_id(original_id)
            if not guest:
                return False
                
            # Get dynamic station mapping
            station_columns = self.get_dynamic_stations()
            
            column = station_columns.get(station.lower())
            if not column:
                self.logger.error(f"Unknown station: {station}. Available stations: {list(station_columns.keys())}")
                return False
                
            # Update the specific cell
            range_name = f"{self.sheet_name}!{column}{guest.row_number}"
            
            body = {
                'values': [[timestamp]]
            }
            
            self._make_api_call(
                lambda: self._get_thread_safe_service().spreadsheets().values().update(
                    spreadsheetId=self.spreadsheet_id,
                    range=range_name,
                    valueInputOption='RAW',
                    body=body
                ).execute()
            )
            
            self.logger.info(f"Marked attendance for guest {original_id} at {station} (Column {column})")
            return True
            
        except Exception as e:
            self.logger.error(f"Error marking attendance: {e}")
            return False
    
    def get_available_stations(self) -> List[str]:
        """
        Get list of available station names for the GUI.
        
        Returns:
            List of station names in consistent title case formatting (never fails)
        """
        try:
            # Use cached data if available to avoid repeated API calls
            if self._cached_stations is not None:
                return [station.title() for station in self._cached_stations.keys()]
            
            # Only make API call if not cached
            station_columns = self.get_dynamic_stations()
            return [station.title() for station in station_columns.keys()]
        except Exception as e:
            # Silent fallback - don't log repeated errors
            self.logger.debug(f"Using fallback stations due to: {e}")
            # Always return hardcoded stations as fallback
            return ['Reception', 'Lio', 'Juntos', 'Experimental', 'Unvrs']
            
    def get_station_column(self, station: str) -> str:
        """Get the column letter for a given station."""
        station_columns = {
            'reception': 'D',
            'lio': 'E',
            'juntos': 'F',
            'experimental': 'G',
            'unvrs': 'H'
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
            
            self._make_api_call(
                lambda: self._get_thread_safe_service().spreadsheets().values().batchUpdate(
                    spreadsheetId=self.spreadsheet_id,
                    body=body
                ).execute()
            )
            
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
            result = self._make_api_call(
                lambda: self._get_thread_safe_service().spreadsheets().values().get(
                    spreadsheetId=self.spreadsheet_id,
                    range=range_name
                ).execute()
            )
            
            values = result.get('values', [])
            if len(values) <= 1:  # Only header row or empty
                self.logger.info("No check-in data to clear")
                return True
                
            # Clear check-in columns (D-H) for all data rows
            clear_range = f"{self.sheet_name}!D2:H{len(values)}"
            
            # Create empty values for clearing
            clear_values = [[""] * 5 for _ in range(len(values) - 1)]  # 5 columns, all rows except header
            
            body = {
                'values': clear_values
            }
            
            self._make_api_call(
                lambda: self._get_thread_safe_service().spreadsheets().values().update(
                    spreadsheetId=self.spreadsheet_id,
                    range=clear_range,
                    valueInputOption='RAW',
                    body=body
                ).execute()
            )
            
            self.logger.warning(f"Cleared all check-in data from Google Sheets ({len(clear_values)} rows)")
            return True
            
        except Exception as e:
            self.logger.error(f"Error clearing Google Sheets data: {e}")
            return False