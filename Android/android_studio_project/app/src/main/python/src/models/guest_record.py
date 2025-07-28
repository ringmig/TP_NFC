#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Guest record model for attendance tracking.
"""

from typing import Optional, Dict, Union
from datetime import datetime


class GuestRecord:
    """Model representing a guest record from the spreadsheet."""
    
    def __init__(self, original_id: int, firstname: str, lastname: str):
        """
        Initialize guest record.
        
        Args:
            original_id: Unique identifier from the spreadsheet
            firstname: Guest's first name
            lastname: Guest's last name
        """
        self.original_id = original_id
        self.firstname = firstname
        self.lastname = lastname
        self.full_name = f"{firstname} {lastname}"
        
        # Station check-ins (station_name -> timestamp string or datetime)
        self.check_ins: Dict[str, Optional[Union[str, datetime]]] = {
            'reception': None,
            'lio': None,
            'juntos': None,
            'experimental': None,
            'unvrs': None
        }
        
        # Associated NFC tag
        self.nfc_tag_uid: Optional[str] = None
        
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
        return station in self.check_ins and self.check_ins[station] is not None
        
    def get_check_in_time(self, station: str) -> Optional[Union[str, datetime]]:
        """Get check-in time for a specific station."""
        station = station.lower()
        return self.check_ins.get(station)
        
    def assign_tag(self, tag_uid: str) -> None:
        """Assign an NFC tag to this guest."""
        self.nfc_tag_uid = tag_uid
        
    def has_tag(self) -> bool:
        """Check if guest has an assigned NFC tag."""
        return self.nfc_tag_uid is not None
        
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