#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Google Sheets service for managing attendance data.
"""

import logging
from typing import List, Dict, Optional, Any
from pathlib import Path
import json

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
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
        
        # Guest data caching
        self._cached_guests = []
        self.guest_cache_file = Path("config/guest_cache.json")
        
        # Load cached guest data
        self.load_guest_cache()
        
    def load_guest_cache(self) -> None:
        """Load cached guest data from file."""
        if self.guest_cache_file.exists():
            try:
                with open(self.guest_cache_file, 'r') as f:
                    cached_data = json.load(f)
                    # Convert dict data back to GuestRecord objects
                    from ..models import GuestRecord
                    self._cached_guests = []
                    for guest_data in cached_data:
                        guest = GuestRecord(
                            original_id=guest_data['original_id'],
                            firstname=guest_data['firstname'],
                            lastname=guest_data['lastname'],
                            stations=guest_data.get('station_names', []),
                            mobile_number=guest_data.get('mobile_number', '')
                        )
                        # Restore check-ins
                        if 'check_ins' in guest_data:
                            guest.check_ins = guest_data['check_ins']
                        self._cached_guests.append(guest)
                self.logger.info(f"Loaded {len(self._cached_guests)} guests from cache")
            except Exception as e:
                self.logger.warning(f"Failed to load guest cache: {e}")
                self._cached_guests = []
        else:
            self.logger.debug("No guest cache file found")
    
    def save_guest_cache(self, guests: List) -> None:
        """Save guest data to cache file."""
        try:
            self.guest_cache_file.parent.mkdir(exist_ok=True)
            # Convert GuestRecord objects to dict for JSON serialization
            cache_data = []
            for guest in guests:
                guest_dict = {
                    'original_id': guest.original_id,
                    'firstname': guest.firstname,
                    'lastname': guest.lastname,
                    'mobile_number': getattr(guest, 'mobile_number', ''),
                    'check_ins': getattr(guest, 'check_ins', {}),
                    'station_names': getattr(guest, 'station_names', list(guest.check_ins.keys()) if hasattr(guest, 'check_ins') else [])
                }
                cache_data.append(guest_dict)
            
            with open(self.guest_cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
            self.logger.debug(f"Saved {len(guests)} guests to cache")
        except Exception as e:
            self.logger.warning(f"Failed to save guest cache: {e}")

    def authenticate(self) -> bool:
        """
        Authenticate with Google Sheets API using Service Account.
        
        Returns:
            bool: True if authenticated successfully
        """
        try:
            service_account_file = self.config.get('service_account_file')
            if not service_account_file:
                self.logger.error("No service_account_file specified in config")
                return False
                
            service_account_path = Path(service_account_file)
            if not service_account_path.exists():
                self.logger.error(f"Service account file not found: {service_account_path}")
                return False
                
            # Load Service Account credentials
            self.creds = Credentials.from_service_account_file(
                str(service_account_path),
                scopes=self.config['scopes']
            )
            
            # Build the service
            self.service = build('sheets', 'v4', credentials=self.creds, cache_discovery=False)
            self.logger.info("Successfully authenticated with Google Sheets using Service Account")
            
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
                    self.logger.warning(f"Network error (attempt {attempt + 1}/{self._connection_retries}) - retrying in {wait_time}s: {e}")
                    time.sleep(wait_time)
                    continue
                else:
                    # Final attempt failed
                    raise e
            except HttpError as e:
                # Retry certain HTTP errors that may be transient
                if e.resp.status in [500, 502, 503, 504] and attempt < self._connection_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    self.logger.warning(f"HTTP error {e.resp.status} (attempt {attempt + 1}/{self._connection_retries}) - retrying in {wait_time}s")
                    time.sleep(wait_time)
                    continue
                else:
                    # Don't retry client errors (4xx) or final attempt
                    raise e
            except Exception as e:
                # Non-network errors should not be retried
                raise e
    
    def get_dynamic_stations(self, fast_fail_startup=False) -> Dict[str, str]:
        """
        Dynamically detect station columns from Google Sheets headers.
        
        Args:
            fast_fail_startup: If True, use minimal retries for faster startup
        
        Returns:
            Dict mapping station names (lowercase) to column letters
        """
        try:
            if self._cached_stations is not None:
                return self._cached_stations
                
            # Get first row (headers) from spreadsheet with retry logic
            range_name = f"{self.sheet_name}!1:1"
            
            # Use fast-fail for startup to prevent hanging
            if fast_fail_startup:
                try:
                    # Single attempt with short timeout for startup
                    result = self._get_thread_safe_service().spreadsheets().values().get(
                        spreadsheetId=self.spreadsheet_id,
                        range=range_name
                    ).execute()
                    self.logger.debug("Fetched stations from Google Sheets (startup)")
                except Exception as e:
                    # Immediate fallback during startup
                    self.logger.debug(f"Station fetch failed during startup, using fallback: {e}")
                    raise e
            else:
                # Normal retry logic for runtime calls
                result = self._make_api_call(
                    lambda: self._get_thread_safe_service().spreadsheets().values().get(
                        spreadsheetId=self.spreadsheet_id,
                        range=range_name
                    ).execute()
                )
                self.logger.debug("Fetched stations from Google Sheets (runtime)")
            
            headers = result.get('values', [[]])[0] if result.get('values') else []
            
            # Build station mapping dynamically
            station_columns = {}
            
            # Known fixed columns (originalid, firstname, lastname, mobilenumber, wristband)
            expected_fixed_cols = ['originalid', 'firstname', 'lastname', 'mobilenumber', 'wristband']
            
            # Start from column F (index 5) to look for station headers (wristband is in column E)
            for i, header in enumerate(headers[5:], start=5):
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
            # Clear logging for station fetching failures
            if fast_fail_startup:
                self.logger.info(f"Could not fetch stations - using fallback: {e}")
            else:
                # Only log first error, then use debug for subsequent ones
                if not hasattr(self, '_dynamic_stations_error_logged'):
                    self.logger.warning(f"Could not fetch stations - retrying with fallback: {e}")
                    self._dynamic_stations_error_logged = True
                else:
                    self.logger.debug(f"Dynamic stations API call failed: {e}")
                    self.logger.debug("Using cached fallback stations")
            
            # Fallback to hardcoded stations (cached to avoid repeated failures)
            # Note: Station columns start from F (wristband is in column E)
            fallback_stations = {
                'reception': 'F',
                'lio': 'G', 
                'juntos': 'H',
                'experimental': 'I',
                'unvrs': 'J'
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
            try:
                station_columns = self.get_dynamic_stations()
            except Exception as station_error:
                self.logger.warning(f"Failed to get dynamic stations: {station_error}")
                # Return cached data if available when station detection fails
                if self._cached_guests:
                    self.logger.info(f"Station detection failed, using cached guest data ({len(self._cached_guests)} guests)")
                    return self._cached_guests
                return []
            
            # Calculate the last column letter based on detected stations
            if not station_columns:
                self.logger.warning("No station columns detected")
                if self._cached_guests:
                    self.logger.info(f"No stations detected, using cached guest data ({len(self._cached_guests)} guests)")
                    return self._cached_guests
                return []
                
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
                # Return cached data if available when spreadsheet is empty
                if self._cached_guests:
                    self.logger.info(f"Spreadsheet empty, using cached guest data ({len(self._cached_guests)} guests)")
                    return self._cached_guests
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
                        # Clean the ID field by removing BOM and other non-numeric characters
                        id_str = str(row[0]).strip().lstrip('\ufeff')
                        original_id = int(id_str)
                        firstname = row[1]
                        lastname = row[2]
                        
                        # Get mobile number from column D (index 3) if available
                        mobile_number = row[3] if len(row) > 3 else None
                        
                        # Get wristband UUID from column E (index 4) if available
                        wristband_uuid = row[4] if len(row) > 4 and row[4].strip() else None
                        
                        # Initialize guest with dynamic stations, mobile number, and wristband UUID
                        guest = GuestRecord(original_id, firstname, lastname, station_names, mobile_number, wristband_uuid)
                        
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
            # Save successful fetch to cache
            self.save_guest_cache(guests)
            self._cached_guests = guests  # Update in-memory cache
            return guests
            
        except HttpError as e:
            self.logger.error(f"Error fetching data from Google Sheets: {e}")
            # Return cached data if available
            if self._cached_guests:
                self.logger.info(f"Using cached guest data ({len(self._cached_guests)} guests)")
                return self._cached_guests
            return []
        except Exception as e:
            self.logger.error(f"Unexpected error fetching guests: {e}")
            # Return cached data if available
            if self._cached_guests:
                self.logger.info(f"Using cached guest data ({len(self._cached_guests)} guests)")
                return self._cached_guests
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
                if len(row) > 0:
                    # Clean the ID field by removing BOM and other non-numeric characters
                    row_id_str = str(row[0]).strip().lstrip('\ufeff')
                    if row_id_str == str(original_id):
                        if len(row) >= 3:
                            # Get mobile number from column D (index 3) if available
                            mobile_number = row[3] if len(row) > 3 else None
                        
                            # Initialize guest with dynamic stations and mobile number
                            guest = GuestRecord(int(row_id_str), row[1], row[2], station_names, mobile_number)
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

    def write_wristband_uuid(self, original_id: int, uuid_value: str) -> bool:
        """
        Write wristband UUID to column E for a specific guest.
        
        Args:
            original_id: Guest's original ID
            uuid_value: UUID to write to the wristband column
            
        Returns:
            bool: True if successful
        """
        try:
            # First, find the guest to get their row number
            guest = self.find_guest_by_id(original_id)
            if not guest:
                self.logger.error(f"Guest {original_id} not found")
                return False
                
            # Write to column E (wristband column)
            range_name = f"{self.sheet_name}!E{guest.row_number}"
            
            body = {
                'values': [[uuid_value]]
            }
            
            self._make_api_call(
                lambda: self._get_thread_safe_service().spreadsheets().values().update(
                    spreadsheetId=self.spreadsheet_id,
                    range=range_name,
                    valueInputOption='RAW',
                    body=body
                ).execute()
            )
            
            self.logger.info(f"Wrote wristband UUID {uuid_value} for guest {original_id} (Column E)")
            return True
            
        except Exception as e:
            self.logger.error(f"Error writing wristband UUID: {e}")
            return False
    
    def get_available_stations(self, fast_fail_startup=False) -> List[str]:
        """
        Get list of available station names for the GUI.
        
        Args:
            fast_fail_startup: If True, use minimal retries for faster startup
        
        Returns:
            List of station names in consistent title case formatting (never fails)
        """
        try:
            # Use cached data if available to avoid repeated API calls
            if self._cached_stations is not None:
                return [station.title() for station in self._cached_stations.keys()]
            
            # Only make API call if not cached
            station_columns = self.get_dynamic_stations(fast_fail_startup)
            return [station.title() for station in station_columns.keys()]
        except Exception as e:
            # Silent fallback - don't log repeated errors
            self.logger.debug(f"Using fallback stations due to: {e}")
            # Always return hardcoded stations as fallback
            return ['Reception', 'Lio', 'Juntos', 'Experimental', 'Unvrs']
            
    def get_station_column(self, station: str) -> str:
        """Get the column letter for a given station."""
        # Note: Station columns shifted right due to mobile number in column D
        station_columns = {
            'reception': 'E',
            'lio': 'F',
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
        """Clear all check-in data from Google Sheets (columns E-I, preserving mobile numbers in D only)."""
        try:
            # Get all rows to determine range (extending to I due to column shift)
            range_name = f"{self.sheet_name}!A:I"
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
                
            # Clear wristband and check-in columns (E-I) for all data rows, preserving mobile numbers in D only
            clear_range = f"{self.sheet_name}!E2:I{len(values)}"
            
            # Create empty values for clearing (5 columns: E, F, G, H, I)
            clear_values = [[""] * 5 for _ in range(len(values) - 1)]  # 5 columns (wristband + 4 check-in), all rows except header
            
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
            
            self.logger.warning(f"Cleared all wristband and check-in data from Google Sheets ({len(clear_values)} rows)")
            return True
            
        except Exception as e:
            self.logger.error(f"Error clearing Google Sheets data: {e}")
            return False