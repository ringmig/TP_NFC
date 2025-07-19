#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Local check-in queue for failsafe attendance tracking.
Ensures check-ins are never lost even if Google Sheets sync fails.
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Callable
from threading import Lock, Thread, Event
import time


class CheckInQueue:
    """Manages local check-in queue with persistent storage."""

    def __init__(self, logger: logging.Logger, queue_file: str = "config/check_in_queue.json"):
        """
        Initialize check-in queue.

        Args:
            logger: Logger instance
            queue_file: Path to persistent queue file
        """
        self.logger = logger
        self.queue_file = Path(queue_file)
        self.queue: List[Dict] = []
        self.lock = Lock()
        self.stop_event = Event()
        self.sync_thread = None
        self.sheets_service = None
        self.sync_completion_callback: Optional[Callable[[], None]] = None

        # Local check-in cache for immediate UI updates
        self.local_check_ins: Dict[int, Dict[str, str]] = {}

        # Load existing queue
        self.load_queue()

    def load_queue(self) -> None:
        """Load queue from persistent storage."""
        if self.queue_file.exists():
            try:
                with open(self.queue_file, 'r') as f:
                    data = json.load(f)
                    self.queue = data.get('pending', [])
                    self.local_check_ins = {
                        int(k): v for k, v in data.get('local_check_ins', {}).items()
                    }
                self.logger.info(f"Loaded {len(self.queue)} pending check-ins from queue")
            except Exception as e:
                self.logger.error(f"Error loading queue: {e}")

    def save_queue(self) -> None:
        """Save queue to persistent storage."""
        try:
            self.queue_file.parent.mkdir(exist_ok=True)
            with open(self.queue_file, 'w') as f:
                json.dump({
                    'pending': self.queue,
                    'local_check_ins': self.local_check_ins,
                    'last_saved': datetime.now().isoformat()
                }, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving queue: {e}")

    def add_check_in(self, original_id: int, station: str, timestamp: str, guest_name: str) -> bool:
        """
        Add check-in to queue and local cache.

        Args:
            original_id: Guest's original ID
            station: Station name
            timestamp: Check-in time
            guest_name: Guest's full name

        Returns:
            bool: True if added successfully
        """
        try:
            with self.lock:
                # Check if already checked in at this station
                if original_id in self.local_check_ins and \
                   self.local_check_ins[original_id].get(station.lower()):
                    self.logger.warning(f"Guest {guest_name} already checked in at {station}")
                    return False  # Don't add duplicate

                # Add to queue for sync
                check_in = {
                    'original_id': original_id,
                    'station': station,
                    'timestamp': timestamp,
                    'guest_name': guest_name,
                    'queued_at': datetime.now().isoformat(),
                    'attempts': 0
                }
                self.queue.append(check_in)

                # Update local cache for immediate UI feedback - always use lowercase
                if original_id not in self.local_check_ins:
                    self.local_check_ins[original_id] = {}
                # Store with lowercase key
                self.local_check_ins[original_id][station.lower()] = timestamp

                # Save immediately
                self.save_queue()

                self.logger.info(f"Queued check-in: {guest_name} at {station}")
                return True
        except Exception as e:
            self.logger.error(f"Error adding check-in: {e}")
            return False

    def has_check_in(self, original_id: int, station: str) -> bool:
        """
        Check if guest already has a check-in at the specified station.

        Args:
            original_id: Guest's original ID
            station: Station name

        Returns:
            bool: True if guest already checked in at this station
        """
        with self.lock:
            return (original_id in self.local_check_ins and
                   self.local_check_ins[original_id].get(station.lower()) is not None)

    def get_local_check_ins(self, original_id: int) -> Dict[str, str]:
        """Get local check-in data for a guest."""
        return self.local_check_ins.get(original_id, {})

    def get_all_local_check_ins(self) -> Dict[int, Dict[str, str]]:
        """Get all local check-in data."""
        with self.lock:
            return self.local_check_ins.copy()

    def set_sheets_service(self, sheets_service) -> None:
        """Set Google Sheets service for syncing."""
        self.sheets_service = sheets_service

    def set_sync_completion_callback(self, callback: Callable[[], None]) -> None:
        """Set callback to be called when sync completes successfully."""
        self.sync_completion_callback = callback

    def start_sync(self) -> None:
        """Start background sync thread."""
        if not self.sync_thread or not self.sync_thread.is_alive():
            self.stop_event.clear()
            self.sync_thread = Thread(target=self._sync_loop, daemon=True)
            self.sync_thread.start()
            self.logger.info("Started check-in sync thread")

    def stop_sync(self) -> None:
        """Stop background sync thread."""
        self.stop_event.set()
        if self.sync_thread and self.sync_thread.is_alive():
            self.sync_thread.join(timeout=5)
            self.logger.info("Stopped check-in sync thread")

    def _sync_loop(self) -> None:
        """Background sync loop."""
        while not self.stop_event.is_set():
            try:
                # Process queue every 5 seconds
                self._process_queue()
                self.stop_event.wait(5)
            except Exception as e:
                self.logger.error(f"Error in sync loop: {e}")
                self.stop_event.wait(10)  # Wait longer on error

    def _process_queue(self) -> None:
        """Process pending check-ins in queue."""
        if not self.sheets_service or not self.queue:
            return

        with self.lock:
            # Process a copy to avoid holding lock during API calls
            pending = self.queue.copy()

        successful = []
        retry_delay = 30  # Reduced retry delay from 60 to 30 seconds
        any_synced = False

        for i, check_in in enumerate(pending):
            # Skip if recently failed (but reduce wait time)
            if check_in['attempts'] > 0:
                last_attempt = datetime.fromisoformat(check_in.get('last_attempt', check_in['queued_at']))
                if (datetime.now() - last_attempt).seconds < retry_delay:
                    continue

            try:
                # Check if Google Sheets already has data (manual edit)
                guest = self.sheets_service.find_guest_by_id(check_in['original_id'])
                if guest and guest.get_check_in_time(check_in['station'].lower()):
                    # Google Sheets already has data - remove from queue and local cache
                    successful.append(i)
                    self.logger.info(f"Skipping sync for {check_in['guest_name']} at {check_in['station']} - already in Google Sheets")

                    # Remove from local cache since it's already in Google Sheets
                    with self.lock:
                        if check_in['original_id'] in self.local_check_ins:
                            station_key = check_in['station'].lower()
                            if station_key in self.local_check_ins[check_in['original_id']]:
                                del self.local_check_ins[check_in['original_id']][station_key]
                                # Remove guest entry if no more stations
                                if not self.local_check_ins[check_in['original_id']]:
                                    del self.local_check_ins[check_in['original_id']]
                    continue

                # Attempt to sync with Google Sheets
                success = self.sheets_service.mark_attendance(
                    check_in['original_id'],
                    check_in['station'],
                    check_in['timestamp']
                )

                if success:
                    successful.append(i)
                    self.logger.info(f"Synced check-in: {check_in['guest_name']} at {check_in['station']}")
                    any_synced = True
                else:
                    # Check if Google Sheets already has ANY data for this check-in (even different timestamp)
                    existing_guest = self.sheets_service.find_guest_by_id(check_in['original_id'])
                    if existing_guest and existing_guest.get_check_in_time(check_in['station'].lower()):
                        # Google Sheets has different data - accept Google Sheets as truth
                        sheets_time = existing_guest.get_check_in_time(check_in['station'].lower())
                        self.logger.warning(f"Sync conflict: {check_in['guest_name']} at {check_in['station']} - "
                                          f"Local: {check_in['timestamp']}, Sheets: {sheets_time} - "
                                          f"Keeping Google Sheets data")
                        successful.append(i)
                        # DON'T remove from local cache here - do it after processing all items
                    else:
                        # Real failure - increment attempts
                        check_in['attempts'] += 1
                        check_in['last_attempt'] = datetime.now().isoformat()
                        # Force retry after max 3 attempts
                        if check_in['attempts'] >= 3:
                            self.logger.error(f"Max sync attempts reached for {check_in['guest_name']} at {check_in['station']}")
                            successful.append(i)  # Remove from queue after max attempts

            except Exception as e:
                self.logger.error(f"Failed to sync check-in: {e}")
                check_in['attempts'] += 1
                check_in['last_attempt'] = datetime.now().isoformat()

        # Remove successful items from queue
        if successful:
            with self.lock:
                # Remove in reverse order to maintain indices
                for i in sorted(successful, reverse=True):
                    if i < len(self.queue):
                        check_in = self.queue[i]

                        # Clean up local cache for successfully synced items
                        if check_in['original_id'] in self.local_check_ins:
                            station_key = check_in['station'].lower()
                            if station_key in self.local_check_ins[check_in['original_id']]:
                                del self.local_check_ins[check_in['original_id']][station_key]
                                # Remove guest entry if no more stations
                                if not self.local_check_ins[check_in['original_id']]:
                                    del self.local_check_ins[check_in['original_id']]

                        self.queue.pop(i)
                self.save_queue()

        # Call sync completion callback if any items were synced
        if any_synced and self.sync_completion_callback:
            try:
                # Schedule callback on main thread if possible (for GUI updates)
                if hasattr(self.sync_completion_callback, '__self__') and hasattr(self.sync_completion_callback.__self__, 'after'):
                    self.sync_completion_callback.__self__.after(0, self.sync_completion_callback)
                else:
                    self.sync_completion_callback()
            except Exception as e:
                self.logger.error(f"Error in sync completion callback: {e}")

    def force_sync(self) -> int:
        """Force immediate sync of all pending items."""
        self._process_queue()
        return len(self.queue)

    def resolve_sync_conflicts(self, all_guests) -> None:
        """Resolve conflicts between local cache and Google Sheets data."""
        if not self.sheets_service or not all_guests:
            return

        conflicts_found = 0

        with self.lock:
            # Check each guest in local cache
            for original_id, local_stations in self.local_check_ins.items():
                # Find corresponding guest in Google Sheets
                guest = None
                for g in all_guests:
                    if g.original_id == original_id:
                        guest = g
                        break

                if not guest:
                    continue

                # Check each station in local cache
                for station, local_time in local_stations.items():
                    sheets_time = guest.get_check_in_time(station)

                    # Conflict: local has data but Google Sheets doesn't
                    if local_time and not sheets_time:
                        # Check if already in queue
                        already_queued = any(
                            item['original_id'] == original_id and
                            item['station'].lower() == station.lower()
                            for item in self.queue
                        )

                        if not already_queued:
                            # Re-queue for sync
                            conflict_item = {
                                'original_id': original_id,
                                'station': station.title(),
                                'timestamp': local_time,
                                'guest_name': guest.full_name,
                                'queued_at': datetime.now().isoformat(),
                                'attempts': 0,
                                'conflict_resolved': True
                            }
                            self.queue.append(conflict_item)
                            conflicts_found += 1

                            self.logger.warning(
                                f"Sync conflict detected: {guest.full_name} at {station.title()} "
                                f"- local data exists but Google Sheets entry was deleted. Re-queuing for sync."
                            )

            if conflicts_found > 0:
                self.save_queue()
                self.logger.info(f"Resolved {conflicts_found} sync conflicts - data will be restored to Google Sheets")

    def clear_all_local_data(self) -> None:
        """Clear all local data (queue and cache)."""
        with self.lock:
            self.queue.clear()
            self.local_check_ins.clear()
            self.save_queue()
        self.logger.warning("All local check-in data cleared")

    def get_queue_status(self) -> Dict[str, int]:
        """Get current queue status."""
        with self.lock:
            return {
                'pending': len(self.queue),
                'failed': sum(1 for item in self.queue if item['attempts'] > 0),
                'total_local_check_ins': sum(len(stations) for stations in self.local_check_ins.values())
            }
