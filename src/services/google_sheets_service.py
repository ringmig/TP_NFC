#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Google Sheets service for managing attendance data.
"""

import logging
from typing import List, Dict, Optional, Any
from pathlib import Path
import json
import threading
import queue
import time

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

        # API request serialization queue
        self.api_queue = queue.Queue()
        self.api_lock = threading.Lock()
        self.shutdown_flag = threading.Event()
        self.worker_thread = threading.Thread(target=self._api_worker, daemon=True)
        self.worker_thread.start()
        self.logger.debug("Google Sheets API request queue initialized")

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

    def _api_worker(self):
        """Worker thread that processes API requests serially to prevent SSL conflicts."""
        while not self.shutdown_flag.is_set():
            try:
                # Get request with timeout to allow shutdown checking
                request_data = self.api_queue.get(timeout=1.0)

                # Unpack request data
                func, args, kwargs, result_queue = request_data

                try:
                    # Execute the API call with minimal delay between calls
                    time.sleep(0.1)  # Small delay to prevent rapid-fire requests
                    result = func(*args, **kwargs)
                    result_queue.put(('success', result))
                except Exception as e:
                    result_queue.put(('error', e))
                finally:
                    self.api_queue.task_done()

            except queue.Empty:
                continue  # Check shutdown flag again
            except Exception as e:
                self.logger.error(f"Error in API worker thread: {e}")

    def _queue_api_request(self, func, *args, **kwargs):
        """Queue an API request for serial execution."""
        if self.shutdown_flag.is_set():
            raise RuntimeError("Google Sheets service is shutting down")

        result_queue = queue.Queue()
        self.api_queue.put((func, args, kwargs, result_queue))

        # Wait for result with timeout
        try:
            status, result = result_queue.get(timeout=30.0)  # 30 second timeout
            if status == 'error':
                raise result
            return result
        except queue.Empty:
            raise TimeoutError("API request timed out after 30 seconds")

    def shutdown(self):
        """Shutdown the API worker thread."""
        self.shutdown_flag.set()
        if self.worker_thread.is_alive():
            self.worker_thread.join(timeout=5.0)
        self.logger.debug("Google Sheets API queue shut down")

    def get_all_guests(self) -> List[GuestRecord]:
        """
        Fetch all guest records from the spreadsheet.

        Returns:
            List of GuestRecord objects
        """
        return self._queue_api_request(self._get_all_guests_internal)

    def _get_all_guests_internal(self) -> List[GuestRecord]:
        """Internal method to fetch all guest records - called via API queue."""
        try:
            # Define the range to read (all columns from checkin data)
            range_name = f"{self.sheet_name}!A:H"

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
                        original_id = int(row[0])
                        firstname = row[1]
                        lastname = row[2]

                        guest = GuestRecord(original_id, firstname, lastname)

                        # Check for existing check-ins
                        if len(row) > 3 and row[3]:  # reception
                            guest.check_ins['reception'] = row[3]
                        if len(row) > 4 and row[4]:  # lio
                            guest.check_ins['lio'] = row[4]
                        if len(row) > 5 and row[5]:  # juntos
                            guest.check_ins['juntos'] = row[5]
                        if len(row) > 6 and row[6]:  # experimental
                            guest.check_ins['experimental'] = row[6]
                        if len(row) > 7 and row[7]:  # unvrs
                            guest.check_ins['unvrs'] = row[7]

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
            # Get full row data including check-ins
            range_name = f"{self.sheet_name}!A:H"

            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=range_name
            ).execute()

            values = result.get('values', [])

            # Find the row with matching ID
            for i, row in enumerate(values[1:], start=2):  # Start from row 2 (skip header)
                if len(row) > 0 and str(row[0]) == str(original_id):
                    if len(row) >= 3:
                        guest = GuestRecord(int(row[0]), row[1], row[2])
                        guest.row_number = i  # Store row number for updates

                        # Load check-in data
                        if len(row) > 3 and row[3]:  # reception
                            guest.check_ins['reception'] = row[3]
                        if len(row) > 4 and row[4]:  # lio
                            guest.check_ins['lio'] = row[4]
                        if len(row) > 5 and row[5]:  # juntos
                            guest.check_ins['juntos'] = row[5]
                        if len(row) > 6 and row[6]:  # experimental
                            guest.check_ins['experimental'] = row[6]
                        if len(row) > 7 and row[7]:  # unvrs
                            guest.check_ins['unvrs'] = row[7]

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
        return self._queue_api_request(self._mark_attendance_internal, original_id, station, timestamp)

    def _mark_attendance_internal(self, original_id: int, station: str, timestamp: str = "X") -> bool:
        """Internal method to mark attendance - called via API queue."""
        try:
            # First, find the guest to get their row number (direct API call, no queue)
            range_name = f"{self.sheet_name}!A:H"
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=range_name
            ).execute()

            values = result.get('values', [])
            guest_row = None

            # Find the row with matching ID
            for i, row in enumerate(values[1:], start=2):  # Start from row 2 (skip header)
                if len(row) > 0 and str(row[0]) == str(original_id):
                    guest_row = i
                    break

            if not guest_row:
                return False

            # Map station names to column letters
            station_columns = {
                'reception': 'D',
                'lio': 'E',
                'juntos': 'F',
                'experimental': 'G',
                'unvrs': 'H'
            }

            column = station_columns.get(station.lower())
            if not column:
                self.logger.error(f"Unknown station: {station}")
                return False

            # Update the specific cell
            range_name = f"{self.sheet_name}!{column}{guest_row}"

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

            # Clear check-in columns (D-H) for all data rows
            clear_range = f"{self.sheet_name}!D2:H{len(values)}"

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
