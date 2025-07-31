#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tag manager service for coordinating NFC and Google Sheets operations.
"""

import logging
from typing import Dict, Optional, List
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
        """Load tag registry from file with backup recovery."""
        if self.registry_file.exists():
            try:
                with open(self.registry_file, 'r') as f:
                    self.tag_registry = json.load(f)
                self.logger.debug(f"Loaded {len(self.tag_registry)} tag mappings: {self.tag_registry}")
                if len(self.tag_registry) > 0:
                    self.logger.info(f"Loaded {len(self.tag_registry)} registered tags from registry")
            except Exception as e:
                self.logger.error(f"Error loading tag registry: {e}")
                # Try to recover from backup
                self._recover_from_backup()
        else:
            self.logger.info("No registry file found, starting with empty registry")

    def _recover_from_backup(self) -> None:
        """Attempt to recover tag registry from backup file."""
        backup_file = Path(str(self.registry_file) + ".backup")
        if backup_file.exists():
            try:
                with open(backup_file, 'r') as f:
                    self.tag_registry = json.load(f)
                self.logger.info(f"Tag registry restored from backup - {len(self.tag_registry)} tags recovered")
                
                # Save the recovered data as new main file
                self.save_registry()
                self.logger.info("Backup data saved as new registry file")
            except Exception as backup_error:
                self.logger.error(f"Backup recovery failed: {backup_error}")
                self.logger.info("Starting with empty registry")
                self.tag_registry = {}
        else:
            self.logger.warning("No backup file available, starting with empty registry")
            self.tag_registry = {}

    def save_registry(self) -> None:
        """Save tag registry to file with backup."""
        try:
            self.registry_file.parent.mkdir(exist_ok=True)
            
            # Create backup if main file exists and is not empty
            backup_file = Path(str(self.registry_file) + ".backup")
            if self.registry_file.exists() and self.registry_file.stat().st_size > 0:
                try:
                    backup_file.write_text(self.registry_file.read_text())
                    self.logger.debug(f"Created backup: {backup_file}")
                except Exception as backup_error:
                    self.logger.warning(f"Failed to create backup: {backup_error}")
            
            # Save main file
            with open(self.registry_file, 'w') as f:
                json.dump(self.tag_registry, f, indent=2)
            self.logger.debug(f"Saved registry with {len(self.tag_registry)} tags: {self.tag_registry}")
        except Exception as e:
            self.logger.error(f"Error saving tag registry: {e}")

    def rewrite_tag_to_guest(self, original_id: int) -> Optional[Dict[str, str]]:
        """
        Rewrite an NFC tag to a guest without auto-check-in.

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
        self.logger.info(f"Waiting for NFC tag to rewrite to {guest.full_name}...")
        tag = self.nfc_service.read_tag(timeout=10)

        if not tag:
            self.logger.error("No tag detected")
            return None

        # Check if tag is already registered
        if tag.uid in self.tag_registry:
            existing_id = self.tag_registry[tag.uid]
            if existing_id != original_id:
                self.logger.warning(f"Tag {tag.uid} was registered to ID {existing_id}, rewriting to {original_id}")

        # Register the tag
        tag.register_to_guest(original_id, guest.full_name)
        self.tag_registry[tag.uid] = original_id

        # Save registry
        self.save_registry()

        self.logger.info(f"Successfully rewritten tag {tag.uid} to {guest.full_name}")

        # NOTE: No auto-check-in for rewrite operations

        return {
            'tag_uid': tag.uid,
            'original_id': original_id,
            'guest_name': guest.full_name,
            'registered_at': datetime.now().isoformat()
        }

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
            existing_guest = self.sheets_service.find_guest_by_id(existing_id)
            existing_name = existing_guest.full_name if existing_guest else f"ID {existing_id}"

            if existing_id != original_id:
                self.logger.error(f"Tag {tag.uid} already registered to {existing_name}")
                return {
                    'error': 'duplicate',
                    'tag_uid': tag.uid,
                    'existing_guest': existing_name,
                    'existing_id': existing_id,
                    'requested_guest': guest.full_name,
                    'requested_id': original_id
                }
            else:
                # Same guest, same tag - this is fine, just update registration time
                self.logger.info(f"Re-registering tag {tag.uid} to same guest {guest.full_name}")

        # Register the tag
        tag.register_to_guest(original_id, guest.full_name)
        self.tag_registry[tag.uid] = original_id

        self.logger.info(f"Added tag {tag.uid} -> {original_id} to registry (register_tag_to_guest)")

        # Save registry
        self.save_registry()

        self.logger.info(f"Successfully registered tag {tag.uid} to {guest.full_name}")

        # Auto-check-in at Reception after successful registration
        reception_station = "Reception"

        # Check if already checked in at Reception (both Google Sheets and local queue)
        sheets_checkin = guest.is_checked_in_at(reception_station.lower())
        local_checkin = self.check_in_queue.has_check_in(original_id, reception_station.lower())

        if not sheets_checkin and not local_checkin:
            # Add automatic check-in at Reception
            timestamp = datetime.now().strftime("%H:%M")
            self.check_in_queue.add_check_in(original_id, reception_station, timestamp, guest.full_name)
            self.logger.info(f"Auto-checked in {guest.full_name} at {reception_station} during registration")
        else:
            self.logger.info(f"{guest.full_name} already checked in at {reception_station}")

        return {
            'tag_uid': tag.uid,
            'original_id': original_id,
            'guest_name': guest.full_name,
            'registered_at': datetime.now().isoformat(),
            'auto_checkin': not (sheets_checkin or local_checkin)  # Indicate if auto check-in occurred
        }

    def process_checkpoint_scan_with_tag(self, tag, station: str) -> Optional[Dict[str, str]]:
        """
        Process a checkpoint scan with already-read tag.

        Args:
            tag: Already read NFC tag
            station: Station name where the scan occurred

        Returns:
            Dict with scan info if successful, None otherwise
        """
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

        # Check if already checked in at this station (Google Sheets + local queue)
        # Use lowercase consistently for comparison
        sheets_checkin = guest.is_checked_in_at(station.lower())
        local_checkin = self.check_in_queue.has_check_in(original_id, station.lower())

        if sheets_checkin or local_checkin:
            self.logger.warning(f"Guest {guest.full_name} already checked in at {station}")
            # Don't add to queue - return None to indicate duplicate
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

        # Check if already checked in at this station (Google Sheets + local queue)
        # Use lowercase consistently for comparison
        sheets_checkin = guest.is_checked_in_at(station.lower())
        local_checkin = self.check_in_queue.has_check_in(original_id, station.lower())

        if sheets_checkin or local_checkin:
            self.logger.warning(f"Guest {guest.full_name} already checked in at {station}")
            # Don't process further - just return duplicate status
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

    def get_tag_info(self, tag_uid: str, guests_data: List = None) -> Optional[Dict[str, any]]:
        """Get information about a registered tag using local data for instant response."""
        if tag_uid not in self.tag_registry:
            return None

        original_id = self.tag_registry[tag_uid]
        
        # First try to use provided in-memory guest data (from TreeView)
        if guests_data:
            for guest in guests_data:
                if guest.original_id == original_id:
                    # Found in local memory - instant response!
                    self.logger.debug(f"Tag info retrieved from memory for guest {guest.full_name}")
                    
                    # Get check-ins including any pending local ones
                    check_ins = guest.check_ins.copy()
                    
                    # Also check for any pending check-ins in the queue
                    local_check_ins = self.check_in_queue.get_local_check_ins(original_id)
                    for station, time in local_check_ins.items():
                        if not check_ins.get(station):
                            check_ins[station] = time
                    
                    return {
                        'tag_uid': tag_uid,
                        'original_id': original_id,
                        'guest_name': guest.full_name,
                        'check_ins': check_ins
                    }
        
        # Fallback to API call only if guest not found in memory
        self.logger.info(f"Guest {original_id} not in memory, falling back to API")
        guest = self.sheets_service.find_guest_by_id(original_id)

        if guest:
            # Include local check-ins
            local_check_ins = self.check_in_queue.get_local_check_ins(original_id)

            # Merge with guest check-ins (Google Sheets takes precedence as source of truth)
            merged_check_ins = guest.check_ins.copy()
            for station, time in local_check_ins.items():
                # Only add local time if Google Sheets doesn't have data
                if not merged_check_ins.get(station):
                    merged_check_ins[station] = time

            return {
                'tag_uid': tag_uid,
                'original_id': original_id,
                'guest_name': guest.full_name,
                'check_ins': merged_check_ins
            }
        return None

    def rewrite_tag_to_guest(self, original_id: int) -> Optional[Dict[str, str]]:
        """
        Force rewrite/overwrite an NFC tag to a guest, ignoring existing registrations.

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
        self.logger.info(f"Waiting for NFC tag to rewrite to {guest.full_name}...")
        tag = self.nfc_service.read_tag(timeout=10)

        if not tag:
            self.logger.error("No tag detected")
            return None

        # Check if tag is already registered and log the change
        if tag.uid in self.tag_registry:
            existing_id = self.tag_registry[tag.uid]
            existing_guest = self.sheets_service.find_guest_by_id(existing_id)
            existing_name = existing_guest.full_name if existing_guest else f"ID {existing_id}"
            self.logger.info(f"Overwriting tag {tag.uid} from {existing_name} to {guest.full_name}")

        # Force register the tag (overwrite any existing registration)
        tag.register_to_guest(original_id, guest.full_name)
        self.tag_registry[tag.uid] = original_id

        # Save registry
        self.save_registry()

        self.logger.info(f"Successfully rewritten tag {tag.uid} to {guest.full_name}")

        return {
            'tag_uid': tag.uid,
            'original_id': original_id,
            'guest_name': guest.full_name,
            'registered_at': datetime.now().isoformat(),
            'action': 'rewrite'
        }

    def register_tag_to_guest_with_existing_tag(self, original_id: int, tag) -> Optional[Dict[str, str]]:
        """
        Register/rewrite an NFC tag to a guest using an already-detected tag.

        Args:
            original_id: Guest's original ID
            tag: Already detected NFC tag object

        Returns:
            Dict with tag info and guest name if successful, None otherwise
        """
        # First, verify guest exists in Google Sheets
        guest = self.sheets_service.find_guest_by_id(original_id)
        if not guest:
            self.logger.error(f"Guest with ID {original_id} not found in spreadsheet")
            return None

        # Check if tag is already registered and log the change
        if tag.uid in self.tag_registry:
            existing_id = self.tag_registry[tag.uid]
            existing_guest = self.sheets_service.find_guest_by_id(existing_id)
            existing_name = existing_guest.full_name if existing_guest else f"ID {existing_id}"
            self.logger.info(f"Rewriting tag {tag.uid} from {existing_name} to {guest.full_name}")
        else:
            self.logger.info(f"Registering new tag {tag.uid} to {guest.full_name}")

        # Force register the tag (overwrite any existing registration)
        tag.register_to_guest(original_id, guest.full_name)
        self.tag_registry[tag.uid] = original_id

        # Save registry
        self.save_registry()

        self.logger.info(f"Successfully registered/rewritten tag {tag.uid} to {guest.full_name}")

        return {
            'tag_uid': tag.uid,
            'original_id': original_id,
            'guest_name': guest.full_name,
            'registered_at': datetime.now().isoformat(),
            'action': 'rewrite'
        }

    def clear_tag(self, tag_uid: str) -> Optional[Dict[str, any]]:
        """
        Clear a tag registration.

        Args:
            tag_uid: Tag UID to clear

        Returns:
            Dict with guest info if cleared successfully, None if tag not found
        """
        self.logger.debug(f"Attempting to clear tag {tag_uid}")
        self.logger.debug(f"Current registry has {len(self.tag_registry)} tags: {list(self.tag_registry.keys())}")

        if tag_uid in self.tag_registry:
            # Get guest info before clearing
            original_id = self.tag_registry[tag_uid]
            guest = self.sheets_service.find_guest_by_id(original_id)

            # Clear the tag from registry
            del self.tag_registry[tag_uid]
            self.save_registry()
            self.logger.info(f"Cleared registration for tag {tag_uid}")

            # Return guest info
            return {
                'tag_uid': tag_uid,
                'original_id': original_id,
                'guest_name': guest.full_name if guest else f"Guest ID {original_id}",
                'cleared_at': datetime.now().isoformat()
            }
        else:
            self.logger.warning(f"Tag {tag_uid} not found in registry for clearing")
            return None

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

    def force_sync_item(self, original_id: int, station: str, timestamp: str) -> bool:
        """Force sync of a specific check-in item."""
        try:
            # Get guest info for name
            guest = self.sheets_service.find_guest_by_id(original_id)
            if not guest:
                return False

            # Add to queue for immediate sync
            self.check_in_queue.add_check_in(original_id, station, timestamp, guest.full_name)

            # Force immediate sync
            self.check_in_queue.force_sync()

            return True
        except Exception as e:
            self.logger.error(f"Error forcing sync for item: {e}")
            return False

    def resolve_sync_conflicts(self, all_guests) -> None:
        """Resolve conflicts between local data and Google Sheets."""
        self.check_in_queue.resolve_sync_conflicts(all_guests)

    def clear_all_local_data(self) -> None:
        """Clear all local check-in data and tag registry."""
        self.check_in_queue.clear_all_local_data()
        self.tag_registry.clear()
        self.save_registry()
        self.logger.warning("All local data cleared")

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

    def clear_all_sheets_data(self) -> bool:
        """Clear all check-in data from Google Sheets."""
        success = self.sheets_service.clear_all_check_in_data()
        if success:
            # Also clear all tag registrations since wristband data was cleared
            self.tag_registry.clear()
            self.save_registry()
            self.logger.info("Cleared all tag registrations along with Google Sheets data")
        return success

    def sync_tag_registry_with_sheets(self, guests_data: List) -> None:
        """Sync local tag registry with wristband data from Google Sheets."""
        try:
            # Build a mapping of current wristband UUIDs to guest IDs from Google Sheets
            sheets_wristbands = {}
            for guest in guests_data:
                if hasattr(guest, 'wristband_uuid') and guest.wristband_uuid:
                    sheets_wristbands[guest.wristband_uuid] = guest.original_id
            
            # Find tags in local registry that are no longer in Google Sheets
            tags_to_remove = []
            for tag_uid, guest_id in self.tag_registry.items():
                # If this tag is not in the sheets data, or points to different guest, remove it
                if tag_uid not in sheets_wristbands or sheets_wristbands[tag_uid] != guest_id:
                    tags_to_remove.append(tag_uid)
            
            # Remove orphaned tags
            if tags_to_remove:
                for tag_uid in tags_to_remove:
                    old_guest_id = self.tag_registry.pop(tag_uid, None)
                    self.logger.info(f"Removed orphaned tag {tag_uid} (was registered to guest {old_guest_id})")
                
                self.save_registry()
                self.logger.info(f"Synced tag registry: removed {len(tags_to_remove)} orphaned tag(s)")
            else:
                self.logger.debug("Tag registry sync: no orphaned tags found")
                
        except Exception as e:
            self.logger.error(f"Error syncing tag registry with sheets: {e}")

    def shutdown(self) -> None:
        """Clean shutdown of tag manager."""
        self.check_in_queue.stop_sync()
        self.save_registry()
