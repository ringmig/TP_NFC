#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Guest record model for attendance tracking.
"""

from typing import Optional, Dict, Union, List
from datetime import datetime


class GuestRecord:
    """Model representing a guest record from the spreadsheet."""
    
    def __init__(self, original_id: int, firstname: str, lastname: str, stations: List[str] = None, mobile_number: str = None, wristband_uuid: str = None):
        """
        Initialize guest record.
        
        Args:
            original_id: Unique identifier from the spreadsheet
            firstname: Guest's first name
            lastname: Guest's last name
            stations: List of station names to initialize (if None, uses default stations)
            mobile_number: Guest's mobile phone number
            wristband_uuid: Wristband UUID from column E
        """
        self.original_id = original_id
        self.firstname = firstname
        self.lastname = lastname
        self.full_name = f"{firstname} {lastname}"
        self.mobile_number = mobile_number
        self.wristband_uuid = wristband_uuid
        
        # Station check-ins (station_name -> timestamp string or datetime)
        # Initialize with provided stations or default hardcoded ones
        if stations:
            self.check_ins: Dict[str, Optional[Union[str, datetime]]] = {
                station.lower(): None for station in stations
            }
        else:
            # Fallback to hardcoded stations for backward compatibility
            self.check_ins: Dict[str, Optional[Union[str, datetime]]] = {
                'reception': None,
                'lio': None,
                'juntos': None,
                'experimental': None,
                'unvrs': None
            }
        
        # Associated NFC tag
        self.nfc_tag_uid: Optional[str] = None
        self.row_number: Optional[int] = None  # For Google Sheets updates
        
    def check_in_at_station(self, station: str) -> bool:
        """
        Record check-in at a specific station.
        
        Args:
            station: Station name (must be one of the predefined stations)
            
        Returns:
            bool: True if check-in successful, False if already checked in
        """
        station = station.lower()
        if station in self.check_ins:
            if self.check_ins[station] is None:
                self.check_ins[station] = datetime.now()
                return True
            return False  # Already checked in
        raise ValueError(f"Unknown station: {station}")
        
    def is_checked_in_at(self, station: str) -> bool:
        """Check if guest is checked in at a specific station."""
        station = station.lower()
        time_value = self.check_ins.get(station)
        # Consider empty or whitespace-only strings as not checked in
        if isinstance(time_value, str) and not time_value.strip():
            return False
        return time_value is not None
        
    def get_check_in_time(self, station: str) -> Optional[Union[str, datetime]]:
        """Get check-in time for a specific station."""
        station = station.lower()
        time_value = self.check_ins.get(station)
        # Return None for empty or whitespace-only strings
        if isinstance(time_value, str) and not time_value.strip():
            return None
        return time_value
        
    def assign_tag(self, tag_uid: str) -> None:
        """Assign an NFC tag to this guest."""
        self.nfc_tag_uid = tag_uid
        
    def has_tag(self) -> bool:
        """Check if guest has an assigned NFC tag."""
        return self.nfc_tag_uid is not None
    
    def ensure_station_exists(self, station: str) -> None:
        """
        Ensure a station exists in the check_ins dictionary.
        This supports dynamic station addition from Google Sheets.
        
        Args:
            station: Station name to add if not present
        """
        station = station.lower()
        if station not in self.check_ins:
            self.check_ins[station] = None
    
    def get_all_stations(self) -> List[str]:
        """Get list of all available stations for this guest."""
        return list(self.check_ins.keys())
    
    def get_formatted_phone(self) -> str:
        """Get formatted phone number with + prefix, or 'No number' if empty."""
        if not self.mobile_number or not str(self.mobile_number).strip():
            return "No number"
        
        # Clean the number (remove spaces, dashes, etc) and add + prefix
        phone = str(self.mobile_number).strip()
        if not phone.startswith('+'):
            phone = '+' + phone
        return phone
        
    def __str__(self) -> str:
        """String representation of the guest."""
        tag_status = f"Tag: {self.nfc_tag_uid}" if self.has_tag() else "No tag assigned"
        return f"Guest {self.original_id}: {self.full_name} ({tag_status})"
        
    def to_dict(self) -> dict:
        """Convert guest record to dictionary format."""
        return {
            'original_id': self.original_id,
            'firstname': self.firstname,
            'lastname': self.lastname,
            'full_name': self.full_name,
            'nfc_tag_uid': self.nfc_tag_uid,
            'check_ins': {
                station: time.isoformat() if isinstance(time, datetime) else time
                for station, time in self.check_ins.items()
            }
        }