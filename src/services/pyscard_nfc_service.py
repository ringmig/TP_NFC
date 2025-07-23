#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Alternative NFC service using pyscard for macOS compatibility.
"""

import logging
from typing import Optional, Callable
from threading import Thread, Event
import time

try:
    from smartcard.System import readers
    from smartcard.util import toHexString
    from smartcard.CardType import AnyCardType
    from smartcard.CardRequest import CardRequest
    from smartcard.CardConnectionObserver import CardConnectionObserver
    PYSCARD_AVAILABLE = True
except ImportError:
    PYSCARD_AVAILABLE = False

from ..models import NFCTag


class PyscardNFCService:
    """Alternative NFC service using pyscard for better macOS compatibility."""
    
    def __init__(self, logger: logging.Logger):
        """
        Initialize NFC service.
        
        Args:
            logger: Logger instance
        """
        self.logger = logger
        self.reader = None
        self.connection = None
        self.is_connected = False
        
    def connect(self) -> bool:
        """
        Connect to NFC reader.
        
        Returns:
            bool: True if connected successfully
        """
        if not PYSCARD_AVAILABLE:
            self.logger.error("pyscard not installed. Run: pip install pyscard")
            return False
            
        try:
            # Get all readers
            reader_list = readers()
            
            if not reader_list:
                self.logger.error("No smart card readers found")
                return False
                
            # Use first available reader
            self.reader = reader_list[0]
            self.is_connected = True
            self.logger.info(f"Connected to reader: {self.reader}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to reader: {e}")
            return False
            
    def disconnect(self) -> None:
        """Disconnect from NFC reader."""
        if self.connection:
            self.connection.disconnect()
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
            
        # Retry logic for handling card connection issues
        max_retries = 2
        for attempt in range(max_retries + 1):
            try:
                if attempt > 0:
                    self.logger.debug(f"Retry attempt {attempt}/{max_retries}")
                    time.sleep(0.5)  # Brief delay between retries
                
                self.logger.info("Waiting for NFC tag...")
                
                # Create a card request with timeout
                cardtype = AnyCardType()
                cardrequest = CardRequest(timeout=timeout, cardType=cardtype)
                
                # Wait for card
                cardservice = cardrequest.waitforcard()
                
                # Connect to the card with error handling
                try:
                    cardservice.connection.connect()
                except Exception as connect_error:
                    if "unresponsive" in str(connect_error).lower() or "T0 or T1" in str(connect_error):
                        if attempt < max_retries:
                            self.logger.warning(f"Card connection failed (attempt {attempt + 1}): {connect_error}")
                            continue
                        else:
                            self.logger.error(f"Card consistently unresponsive after {max_retries + 1} attempts")
                            return None
                    else:
                        raise connect_error
                
                # Get UID (for most cards, this is the response to the GET UID command)
                # For NTAG213, we can use the GET_VERSION command
                GET_UID = [0xFF, 0xCA, 0x00, 0x00, 0x00]
                response, sw1, sw2 = cardservice.connection.transmit(GET_UID)
                
                if sw1 == 0x90 and sw2 == 0x00:
                    uid = toHexString(response).replace(' ', '')
                    self.logger.info(f"Tag detected with UID: {uid}")
                    
                    # Create NFCTag instance
                    tag = NFCTag(uid)
                    
                    # Disconnect from this card
                    cardservice.connection.disconnect()
                    
                    return tag
                else:
                    self.logger.error(f"Failed to read UID: SW1={sw1:02X} SW2={sw2:02X}")
                    return None
                    
            except Exception as e:
                if attempt < max_retries and ("unresponsive" in str(e).lower() or "T0 or T1" in str(e)):
                    self.logger.warning(f"Tag read failed (attempt {attempt + 1}): {e}")
                    continue
                else:
                    # Final attempt or different error type
                    if "timeout" in str(e).lower():
                        self.logger.info("No tag detected within timeout period")
                    else:
                        self.logger.error(f"Error reading NFC tag: {e}")
                    return None
        
        # If we get here, all retries failed
        self.logger.error("All retry attempts failed")
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
        if not PYSCARD_AVAILABLE:
            return False
            
        try:
            # Get current reader list
            reader_list = readers()
            
            if not reader_list:
                self.is_connected = False
                return False
                
            # If we had a reader before, check if it's still there
            if self.reader:
                if self.reader not in reader_list:
                    self.logger.info("Previous reader disconnected")
                    self.reader = None
                    self.is_connected = False
                    return False
            else:
                # No previous reader, try to connect to first available
                self.reader = reader_list[0]
                self.logger.info(f"Reader detected: {self.reader}")
                
            self.is_connected = True
            return True
            
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
        
    def cancel_read(self) -> None:
        """Cancel ongoing read operation."""
        # Pyscard doesn't have a direct cancel, but timeout will handle it
        pass
        
    def beep(self) -> None:
        """Make the reader beep (if supported)."""
        # This is reader-specific
        pass