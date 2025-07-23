#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Android NFC service using plyer and Android API
"""

import logging
from typing import Optional, Callable
from threading import Thread, Event
import time

try:
    from plyer import nfc
    from plyer.utils import platform
    PLYER_AVAILABLE = True
except ImportError:
    PLYER_AVAILABLE = False

try:
    # Android-specific imports
    from jnius import autoclass, PythonJavaClass, java_method
    from android.runnable import run_on_ui_thread
    from android import activity, mActivity
    ANDROID_AVAILABLE = True
except ImportError:
    ANDROID_AVAILABLE = False

from ..models import NFCTag

class AndroidNFCService:
    """NFC service for Android using plyer and native Android API"""
    
    def __init__(self, logger: logging.Logger):
        """
        Initialize Android NFC service.
        
        Args:
            logger: Logger instance
        """
        self.logger = logger
        self.is_connected = False
        self.scan_event = Event()
        self.last_tag: Optional[NFCTag] = None
        self._scan_callback = None
        
        # Android NFC classes
        if ANDROID_AVAILABLE:
            self.NfcAdapter = autoclass('android.nfc.NfcAdapter')
            self.Intent = autoclass('android.content.Intent')
            self.IntentFilter = autoclass('android.content.IntentFilter')
            self.PendingIntent = autoclass('android.app.PendingIntent')
            self.Tag = autoclass('android.nfc.Tag')
            
    def connect(self) -> bool:
        """
        Initialize NFC connection on Android.
        
        Returns:
            bool: True if NFC is available and enabled
        """
        if not ANDROID_AVAILABLE:
            self.logger.error("Android environment not available")
            return False
            
        try:
            # Get NFC adapter
            context = mActivity
            self.nfc_adapter = self.NfcAdapter.getDefaultAdapter(context)
            
            if self.nfc_adapter is None:
                self.logger.error("NFC not supported on this device")
                return False
                
            if not self.nfc_adapter.isEnabled():
                self.logger.error("NFC is disabled - please enable in device settings")
                return False
                
            self.is_connected = True
            self.logger.info("Android NFC initialized successfully")
            
            # Set up NFC intent handling
            self._setup_nfc_intent_handling()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Android NFC: {e}")
            return False
    
    def _setup_nfc_intent_handling(self):
        """Set up Android NFC intent handling"""
        try:
            # Create intent for NFC discovery
            intent = self.Intent(mActivity, mActivity.getClass())
            intent.addFlags(self.Intent.FLAG_ACTIVITY_SINGLE_TOP)
            
            # Create pending intent
            self.pending_intent = self.PendingIntent.getActivity(
                mActivity, 0, intent, self.PendingIntent.FLAG_MUTABLE
            )
            
            # Create intent filters for different NFC technologies
            filters = []
            
            # NDEF filter
            ndef_filter = self.IntentFilter(self.NfcAdapter.ACTION_NDEF_DISCOVERED)
            filters.append(ndef_filter)
            
            # Tech discovered filter  
            tech_filter = self.IntentFilter(self.NfcAdapter.ACTION_TECH_DISCOVERED)
            filters.append(tech_filter)
            
            # Tag discovered filter (catches all)
            tag_filter = self.IntentFilter(self.NfcAdapter.ACTION_TAG_DISCOVERED)
            filters.append(tag_filter)
            
            self.intent_filters = filters
            
            # Tech lists for different NFC technologies
            self.tech_lists = [
                ["android.nfc.tech.Ndef"],
                ["android.nfc.tech.NdefFormatable"], 
                ["android.nfc.tech.NfcA"],
                ["android.nfc.tech.NfcB"],
                ["android.nfc.tech.NfcF"],
                ["android.nfc.tech.NfcV"]
            ]
            
            self.logger.info("NFC intent handling configured")
            
        except Exception as e:
            self.logger.error(f"Failed to setup NFC intent handling: {e}")
    
    def enable_foreground_dispatch(self):
        """Enable foreground NFC dispatch for the current activity"""
        if not self.is_connected:
            return
            
        try:
            self.nfc_adapter.enableForegroundDispatch(
                mActivity,
                self.pending_intent,
                self.intent_filters,
                self.tech_lists
            )
            self.logger.debug("Enabled NFC foreground dispatch")
        except Exception as e:
            self.logger.error(f"Failed to enable foreground dispatch: {e}")
    
    def disable_foreground_dispatch(self):
        """Disable foreground NFC dispatch"""
        if not self.is_connected:
            return
            
        try:
            self.nfc_adapter.disableForegroundDispatch(mActivity)
            self.logger.debug("Disabled NFC foreground dispatch")
        except Exception as e:
            self.logger.error(f"Failed to disable foreground dispatch: {e}")
    
    def process_nfc_intent(self, intent):
        """
        Process NFC intent from Android system.
        
        Args:
            intent: Android Intent containing NFC data
        """
        try:
            action = intent.getAction()
            
            if action in [
                self.NfcAdapter.ACTION_NDEF_DISCOVERED,
                self.NfcAdapter.ACTION_TECH_DISCOVERED,
                self.NfcAdapter.ACTION_TAG_DISCOVERED
            ]:
                # Get the tag from the intent
                tag = intent.getParcelableExtra(self.NfcAdapter.EXTRA_TAG)
                
                if tag:
                    # Extract UID
                    uid_bytes = tag.getId()
                    uid = ''.join(['%02X' % (b & 0xff) for b in uid_bytes])
                    
                    self.logger.info(f"NFC tag detected: {uid}")
                    
                    # Create NFCTag instance
                    nfc_tag = NFCTag(uid)
                    self.last_tag = nfc_tag
                    
                    # Trigger callback if set
                    if self._scan_callback:
                        self._scan_callback(nfc_tag)
                    
                    # Set scan event
                    self.scan_event.set()
                    
                    return True
                    
        except Exception as e:
            self.logger.error(f"Error processing NFC intent: {e}")
            
        return False
    
    def read_tag(self, timeout: int = 5) -> Optional[NFCTag]:
        """
        Read NFC tag (blocking).
        
        Args:
            timeout: Timeout in seconds
            
        Returns:
            NFCTag instance if successful, None otherwise
        """
        if not self.is_connected:
            self.logger.error("NFC not connected")
            return None
            
        try:
            self.logger.info("Waiting for NFC tag...")
            self.last_tag = None
            self.scan_event.clear()
            
            # Enable foreground dispatch
            self.enable_foreground_dispatch()
            
            # Wait for tag detection
            if self.scan_event.wait(timeout):
                return self.last_tag
            else:
                self.logger.info("No tag detected within timeout")
                return None
                
        except Exception as e:
            self.logger.error(f"Error reading NFC tag: {e}")
            return None
        finally:
            # Always disable foreground dispatch
            self.disable_foreground_dispatch()
    
    def read_tag_async(self, callback: Callable[[NFCTag], None], timeout: int = 5) -> None:
        """
        Read NFC tag asynchronously.
        
        Args:
            callback: Function to call when tag is read
            timeout: Timeout in seconds
        """
        self._scan_callback = callback
        
        def _read():
            tag = self.read_tag(timeout)
            if tag and callback:
                callback(tag)
                
        thread = Thread(target=_read)
        thread.daemon = True
        thread.start()
    
    def disconnect(self) -> None:
        """Disconnect from NFC"""
        if self.is_connected:
            self.disable_foreground_dispatch()
            self.is_connected = False
            self.logger.info("Disconnected from Android NFC")
    
    def check_connection(self) -> bool:
        """
        Check if NFC is available and enabled.
        
        Returns:
            bool: True if NFC is available
        """
        if not ANDROID_AVAILABLE:
            return False
            
        try:
            if self.nfc_adapter is None:
                return False
                
            return self.nfc_adapter.isEnabled()
            
        except Exception as e:
            self.logger.debug(f"NFC connection check failed: {e}")
            return False
    
    def write_data_to_tag(self, tag_uid: str, data: str) -> bool:
        """
        Write data to NFC tag.
        
        Args:
            tag_uid: Tag UID
            data: Data to write
            
        Returns:
            bool: True if successful
        """
        # TODO: Implement NFC writing for Android
        self.logger.info(f"Writing to tag {tag_uid}: {data}")
        return True
    
    def cancel_read(self) -> None:
        """Cancel ongoing read operation"""
        self.scan_event.set()
        self.disable_foreground_dispatch()
    
    def beep(self) -> None:
        """Make device beep (using system sound)"""
        try:
            # Use Android system sound
            if ANDROID_AVAILABLE:
                ToneGenerator = autoclass('android.media.ToneGenerator')
                AudioManager = autoclass('android.media.AudioManager')
                
                tone_gen = ToneGenerator(
                    AudioManager.STREAM_NOTIFICATION, 100
                )
                tone_gen.startTone(ToneGenerator.TONE_PROP_BEEP, 200)
                tone_gen.release()
        except Exception as e:
            self.logger.debug(f"Could not play beep: {e}")