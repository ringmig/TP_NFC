#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tag manager service for coordinating NFC and Google Sheets operations.
"""

import logging
from typing import Dict, Optional
from datetime import datetime
import json
from pathlib import Path

from ..models import NFCTag, GuestRecord
from .nfc_service import NFCService
from .google_sheets_service import GoogleSheetsService
from .check_in_queue import CheckInQueue


class TagManager:
    """Manages the relationship between NFC tags and guest records."""

    def __init__(self, nfc_service: NFCService, sheets_service: GoogleSheetsService, logger: logging.Logger):
        """
        Initialize tag manager.

        Args:
            nfc_service: NFC service instance
            sheets_service: Google Sheets service instance
            logger: Logger instance
        """
        self.nfc_service = nfc_service
        self.sheets_service = sheets_service
        self.logger = logger

        # In-memory mapping of tag UIDs to original IDs
        self.tag_registry: Dict[str, int] = {}
        self.registry_file = Path("config/tag_registry.json")

        # Initialize check-in queue for failsafe operation
        self.check_in_queue = CheckInQueue(logger)
        self.check_in_queue.set_sheets_service(sheets_service)
        self.check_in_queue.start_sync()

        # Load existing registry
        self.load_registry()

    def set_sync_completion_callback(self, callback) -> None:
        """Set callback to be called when sync completes."""
        self.check_in_queue.set_sync_completion_callback(callback)

    def load_registry(self) -> None:
        """Load tag registry from file."""
        if self.registry_file.exists():
            try:
                with open(self.registry_file, 'r') as f:
                    self.tag_registry = json.load(f)
                self.logger.info(f"Loaded {len(self.tag_registry)} tag mappings")
            except Exception as e:
                self.logger.error(f"Error loading tag registry: {e}")

    def save_registry(self) -> None:
        """Save tag registry to file."""
        try:
            self.registry_file.parent.mkdir(exist_ok=True)
            with open(self.registry_file, 'w') as f:
                json.dump(self.tag_registry, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving tag registry: {e}")

    def register_tag_to_guest(self, original_id: int) -> Optional[Dict[str, str]]:
        """
        Register an NFC tag to a guest.

        Args:
            original_id: Guest's original ID

        Returns:
            Dict with tag info and guest name if successful, None otherwise
        """
        # First, verify guest exists in Google Sheets
        guest = self.sheets_service.find_guest_by_id(original_id)
        if not guest:
            self.logger.error(f"Guest with ID {original_id} not found in spreadsheet")
            return None

        # Read NFC tag
        self.logger.info(f"Waiting for NFC tag to register to {guest.full_name}...")
        tag = self.nfc_service.read_tag(timeout=10)

        if not tag:
            self.logger.error("No tag detected")
            return None

        # Check if tag is already registered
        if tag.uid in self.tag_registry:
            existing_id = self.tag_registry[tag.uid]
            if existing_id != original_id:
                self.logger.warning(f"Tag {tag.uid} already registered to ID {existing_id}")
                # You might want to allow re-registration here

        # Register the tag
        tag.register_to_guest(original_id, guest.full_name)
        self.tag_registry[tag.uid] = original_id

        # Save registry
        self.save_registry()

        self.logger.info(f"Successfully registered tag {tag.uid} to {guest.full_name}")

        # Also queue check-in at Reception when registering
        timestamp = datetime.now().strftime("%H:%M")
        self.check_in_queue.add_check_in(original_id, "Reception", timestamp, guest.full_name)

        return {
            'tag_uid': tag.uid,
            'original_id': original_id,
            'guest_name': guest.full_name,
            'registered_at': datetime.now().isoformat()
        }

    def process_checkpoint_scan(self, station: str) -> Optional[Dict[str, str]]:
        """
        Process a tag scan at a checkpoint.

        Args:
            station: Station name where the scan occurred

        Returns:
            Dict with scan info if successful, None otherwise
        """
        # Read NFC tag
        self.logger.info(f"Waiting for tag scan at {station}...")
        tag = self.nfc_service.read_tag(timeout=10)

        if not tag:
            self.logger.error("No tag detected")
            return None

        # Look up original ID
        if tag.uid not in self.tag_registry:
            self.logger.error(f"Unregistered tag: {tag.uid}")
            return None

        original_id = self.tag_registry[tag.uid]

        # Get guest info
        guest = self.sheets_service.find_guest_by_id(original_id)
        if not guest:
            self.logger.error(f"Guest with ID {original_id} not found")
            return None

        # Add to local queue immediately (for instant UI feedback)
        timestamp = datetime.now().strftime("%H:%M")
        self.check_in_queue.add_check_in(original_id, station, timestamp, guest.full_name)

        self.logger.info(f"Queued attendance for ID {original_id} at {station}")

        return {
            'tag_uid': tag.uid,
            'original_id': original_id,
            'guest_name': guest.full_name,
            'station': station,
            'timestamp': timestamp
        }

    def manual_check_in(self, original_id: int, station: str) -> Optional[Dict[str, str]]:
        """
        Process manual check-in without tag scan.

        Args:
            original_id: Guest's original ID
            station: Station name

        Returns:
            Dict with check-in info if successful, None otherwise
        """
        # Get guest info
        guest = self.sheets_service.find_guest_by_id(original_id)
        if not guest:
            self.logger.error(f"Guest with ID {original_id} not found")
            return None

        # Add to local queue
        timestamp = datetime.now().strftime("%H:%M")
        self.check_in_queue.add_check_in(original_id, station, timestamp, guest.full_name)

        self.logger.info(f"Queued manual check-in for ID {original_id} at {station}")

        return {
            'original_id': original_id,
            'guest_name': guest.full_name,
            'station': station,
            'timestamp': timestamp
        }

    def get_tag_info(self, tag_uid: str) -> Optional[Dict[str, any]]:
        """Get information about a registered tag."""
        if tag_uid not in self.tag_registry:
            return None

        original_id = self.tag_registry[tag_uid]
        guest = self.sheets_service.find_guest_by_id(original_id)

        if guest:
            # Include local check-ins
            local_check_ins = self.check_in_queue.get_local_check_ins(original_id)

            # Merge with guest check-ins (local takes precedence)
            merged_check_ins = guest.check_ins.copy()
            for station, time in local_check_ins.items():
                merged_check_ins[station] = time

            return {
                'tag_uid': tag_uid,
                'original_id': original_id,
                'guest_name': guest.full_name,
                'check_ins': merged_check_ins
            }
        return None

    def clear_tag(self, tag_uid: str) -> bool:
        """
        Clear a tag registration.

        Args:
            tag_uid: Tag UID to clear

        Returns:
            bool: True if cleared successfully
        """
        if tag_uid in self.tag_registry:
            del self.tag_registry[tag_uid]
            self.save_registry()
            self.logger.info(f"Cleared registration for tag {tag_uid}")
            return True
        return False

    def get_registry_stats(self) -> Dict[str, int]:
        """Get statistics about the tag registry."""
        queue_status = self.check_in_queue.get_queue_status()
        return {
            'total_registered_tags': len(self.tag_registry),
            'unique_guests': len(set(self.tag_registry.values())),
            'pending_syncs': queue_status['pending'],
            'failed_syncs': queue_status['failed']
        }

    def get_all_local_check_ins(self) -> Dict[int, Dict[str, str]]:
        """Get all local check-in data."""
        return self.check_in_queue.get_all_local_check_ins()

    def force_sync(self) -> int:
        """Force immediate sync of pending check-ins."""
        return self.check_in_queue.force_sync()

    def shutdown(self) -> None:
        """Clean shutdown of tag manager."""
        self.check_in_queue.stop_sync()
        self.save_registry()
