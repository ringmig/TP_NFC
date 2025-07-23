#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NFC Tag model for NTAG213 tags.
"""

from typing import Optional
from datetime import datetime


class NFCTag:
    """Model representing an NTAG213 NFC tag."""
    
    def __init__(self, uid: str):
        """
        Initialize NFC tag.
        
        Args:
            uid: Unique identifier of the NFC tag
        """
        self.uid = uid
        self.original_id: Optional[int] = None
        self.guest_name: Optional[str] = None
        self.registered_at: Optional[datetime] = None
        self.last_scan: Optional[datetime] = None
        self.scan_count: int = 0
        
    def register_to_guest(self, original_id: int, guest_name: str) -> None:
        """
        Register this tag to a guest.
        
        Args:
            original_id: Guest's original ID from the spreadsheet
            guest_name: Guest's full name
        """
        self.original_id = original_id
        self.guest_name = guest_name
        self.registered_at = datetime.now()
        
    def record_scan(self) -> None:
        """Record a scan event."""
        self.last_scan = datetime.now()
        self.scan_count += 1
        
    def is_registered(self) -> bool:
        """Check if tag is registered to a guest."""
        return self.original_id is not None
        
    def __str__(self) -> str:
        """String representation of the tag."""
        if self.is_registered():
            return f"Tag {self.uid} - Guest: {self.guest_name} (ID: {self.original_id})"
        return f"Tag {self.uid} - Unregistered"
        
    def to_dict(self) -> dict:
        """Convert tag to dictionary format."""
        return {
            'uid': self.uid,
            'original_id': self.original_id,
            'guest_name': self.guest_name,
            'registered_at': self.registered_at.isoformat() if self.registered_at else None,
            'last_scan': self.last_scan.isoformat() if self.last_scan else None,
            'scan_count': self.scan_count
        }