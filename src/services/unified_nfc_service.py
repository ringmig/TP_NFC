#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unified NFC service that automatically selects the best backend.
"""

import logging
import platform
from typing import Optional, Callable, Union

from ..models import NFCTag

# Try to import both backends
try:
    from .nfc_service import NFCService as NFCPyService
    NFCPY_AVAILABLE = True
except ImportError:
    NFCPY_AVAILABLE = False

try:
    from .pyscard_nfc_service import PyscardNFCService
    PYSCARD_AVAILABLE = True
except ImportError:
    PYSCARD_AVAILABLE = False


class UnifiedNFCService:
    """
    Unified NFC service that automatically selects the best backend
    based on platform and availability.
    """
    
    def __init__(self, logger: logging.Logger, backend: Optional[str] = None):
        """
        Initialize unified NFC service.
        
        Args:
            logger: Logger instance
            backend: Force specific backend ('nfcpy' or 'pyscard'), None for auto
        """
        self.logger = logger
        self.backend_service = None
        self.backend_name = None
        
        # Select backend
        if backend == 'nfcpy' and NFCPY_AVAILABLE:
            self.backend_service = NFCPyService(logger)
            self.backend_name = 'nfcpy'
        elif backend == 'pyscard' and PYSCARD_AVAILABLE:
            self.backend_service = PyscardNFCService(logger)
            self.backend_name = 'pyscard'
        else:
            # Auto-select based on platform
            if platform.system() == 'Darwin':  # macOS
                # Prefer pyscard on macOS due to driver issues
                if PYSCARD_AVAILABLE:
                    self.backend_service = PyscardNFCService(logger)
                    self.backend_name = 'pyscard'
                elif NFCPY_AVAILABLE:
                    self.backend_service = NFCPyService(logger)
                    self.backend_name = 'nfcpy'
            else:  # Windows, Linux
                # Prefer nfcpy on other platforms
                if NFCPY_AVAILABLE:
                    self.backend_service = NFCPyService(logger)
                    self.backend_name = 'nfcpy'
                elif PYSCARD_AVAILABLE:
                    self.backend_service = PyscardNFCService(logger)
                    self.backend_name = 'pyscard'
        
        if self.backend_service:
            logger.info(f"Using {self.backend_name} backend for NFC")
        else:
            logger.error("No NFC backend available!")
            logger.error("Install either: pip install nfcpy pyusb OR pip install pyscard")
    
    def connect(self) -> bool:
        """Connect to NFC reader."""
        if not self.backend_service:
            return False
        
        # Try primary backend
        if self.backend_service.connect():
            return True
        
        # If failed on macOS with nfcpy, suggest alternatives
        if platform.system() == 'Darwin' and self.backend_name == 'nfcpy':
            self.logger.warning("nfcpy failed on macOS. Common solutions:")
            self.logger.warning("1. Run: sudo kextunload -b com.apple.iokit.CSCRPCCardFamily")
            self.logger.warning("2. Or install pyscard: pip install pyscard")
        
        return False
    
    def disconnect(self) -> None:
        """Disconnect from NFC reader."""
        if self.backend_service:
            self.backend_service.disconnect()
    
    def read_tag(self, timeout: int = 5) -> Optional[NFCTag]:
        """Read NFC tag."""
        if not self.backend_service:
            return None
        return self.backend_service.read_tag(timeout)
    
    def read_tag_async(self, callback: Callable[[NFCTag], None], timeout: int = 5) -> None:
        """Read NFC tag asynchronously."""
        if self.backend_service:
            self.backend_service.read_tag_async(callback, timeout)
    
    def get_last_error_type(self) -> Optional[str]:
        """
        Get the type of the last error that occurred.
        
        Returns:
            str: 'timeout', 'connection_failed', 'read_failed', or None if no error
        """
        if self.backend_service and hasattr(self.backend_service, 'get_last_error_type'):
            return self.backend_service.get_last_error_type()
        return None
    
    def write_data_to_tag(self, tag_uid: str, data: str) -> bool:
        """Write data to NFC tag."""
        if not self.backend_service:
            return False
        return self.backend_service.write_data_to_tag(tag_uid, data)
    
    def cancel_read(self) -> None:
        """Cancel ongoing read operation."""
        if self.backend_service:
            self.backend_service.cancel_read()
    
    def beep(self) -> None:
        """Make the reader beep (if supported)."""
        if self.backend_service:
            self.backend_service.beep()
    
    @property
    def is_connected(self) -> bool:
        """Check if connected to reader."""
        if self.backend_service:
            # Use check_connection method if available for real-time status
            if hasattr(self.backend_service, 'check_connection'):
                return self.backend_service.check_connection()
            else:
                return self.backend_service.is_connected
        return False