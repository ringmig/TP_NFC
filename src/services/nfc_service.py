#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NFC service for handling NTAG213 tag operations.
"""

import nfc
import logging
from typing import Optional, Callable
from threading import Thread, Event
import time

from ..models import NFCTag


class NFCService:
    """Service for handling NFC tag operations."""
    
    def __init__(self, logger: logging.Logger):
        """
        Initialize NFC service.
        
        Args:
            logger: Logger instance
        """
        self.logger = logger
        self.clf = None  # ContactlessFrontend instance
        self.is_connected = False
        self.scan_event = Event()
        self.last_tag: Optional[NFCTag] = None
        
    def connect(self) -> bool:
        """
        Connect to NFC reader.
        
        Returns:
            bool: True if connected successfully
        """
        try:
            self.clf = nfc.ContactlessFrontend()
            # Try common connection strings
            connection_strings = [
                'usb',  # Generic USB
                'usb:072f:2200',  # ACR122U
                'usb:04e6:5591',  # SCL3711
            ]
            
            for conn_str in connection_strings:
                try:
                    if self.clf.open(conn_str):
                        self.is_connected = True
                        self.logger.info(f"Connected to NFC reader: {conn_str}")
                        return True
                except:
                    continue
                    
            self.logger.error("No NFC reader found")
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to connect to NFC reader: {e}")
            return False
            
    def disconnect(self) -> None:
        """Disconnect from NFC reader."""
        if self.clf:
            self.clf.close()
            self.is_connected = False
            self.logger.info("Disconnected from NFC reader")
            
    def read_tag(self, timeout: int = 5) -> Optional[NFCTag]:
        """
        Read NFC tag (blocking).
        
        Args:
            timeout: Timeout in seconds
            
        Returns:
            NFCTag instance if successful, None otherwise
        """
        if not self.is_connected:
            self.logger.error("NFC reader not connected")
            return None
            
        try:
            self.logger.info("Waiting for NFC tag...")
            self.last_tag = None
            
            # Start the contactless frontend
            tag = self.clf.connect(
                rdwr={'on-connect': self._on_tag_connect},
                terminate=lambda: self.scan_event.is_set()
            )
            
            # Reset the event for next scan
            self.scan_event.clear()
            
            return self.last_tag
            
        except Exception as e:
            self.logger.error(f"Error reading NFC tag: {e}")
            return None
            
    def read_tag_async(self, callback: Callable[[NFCTag], None], timeout: int = 5) -> None:
        """
        Read NFC tag asynchronously.
        
        Args:
            callback: Function to call when tag is read
            timeout: Timeout in seconds
        """
        def _read():
            tag = self.read_tag(timeout)
            if tag:
                callback(tag)
                
        thread = Thread(target=_read)
        thread.daemon = True
        thread.start()
        
    def check_connection(self) -> bool:
        """
        Check if NFC reader is currently available.
        
        Returns:
            bool: True if reader is available
        """
        try:
            # If we don't have a connection, try to establish one
            if not self.clf or not self.is_connected:
                return self.connect()
                
            # Test if existing connection is still valid
            # This is a simple way to check without full operation
            return self.is_connected and self.clf is not None
            
        except Exception as e:
            self.logger.debug(f"Connection check failed: {e}")
            self.is_connected = False
            return False
        
    def write_data_to_tag(self, tag_uid: str, data: str) -> bool:
        """
        Write data to NFC tag (for future use).
        
        Args:
            tag_uid: Tag UID
            data: Data to write
            
        Returns:
            bool: True if successful
        """
        # Implementation for writing data to NTAG213
        # This is a placeholder for future functionality
        self.logger.info(f"Writing to tag {tag_uid}: {data}")
        return True
        
    def _on_tag_connect(self, tag) -> bool:
        """
        Handle tag connection event.
        
        Args:
            tag: nfcpy tag object
            
        Returns:
            bool: False to release the tag
        """
        try:
            # Extract UID from tag
            uid = tag.identifier.hex().upper()
            
            # Check if it's an NTAG213
            if hasattr(tag, 'product') and 'NTAG213' in str(tag.product):
                self.logger.info(f"NTAG213 detected: {uid}")
            else:
                self.logger.warning(f"Non-NTAG213 tag detected: {uid}")
                
            # Create NFCTag instance
            self.last_tag = NFCTag(uid)
            
            # Signal that we've read a tag
            self.scan_event.set()
            
            return False  # Release the tag
            
        except Exception as e:
            self.logger.error(f"Error processing tag: {e}")
            return False
            
    def cancel_read(self) -> None:
        """Cancel ongoing read operation."""
        self.scan_event.set()
        
    def beep(self) -> None:
        """Make the reader beep (if supported)."""
        # This is reader-specific, may not work on all readers
        pass