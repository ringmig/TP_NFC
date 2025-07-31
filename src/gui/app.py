#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUI application for TP_NFC attendance system.
"""

import customtkinter as ctk
from customtkinter import CTkFont
import tkinter as tk
from tkinter import ttk
import threading
from typing import Optional, List, Dict
from datetime import datetime
import time
from PIL import Image
import os
import platform
import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import requests
import webbrowser

# Configure CustomTkinter
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# Theme Colors - Easy customization
THEME_COLORS = {
    # Background colors for different UI areas
    'window_background_dark': "#212121",   # Outer padded area in dark mode
    'window_background_light': "#f0f0f0",  # Outer padded area in light mode
    'main_frame_dark': "#212121",          # Main container (spaces between frames) in dark mode
    'main_frame_light': "#f0f0f0",         # Main container (spaces between frames) in light mode
    'header_frame_dark': "#2b2b2b",        # Header area (logo + stations) in dark mode
    'header_frame_light': "#dde0e4",       # Header area (logo + stations) in light mode
    'content_frame_dark': "#2b2b2b",       # Main content area in dark mode  
    'content_frame_light': "#dde0e4",      # Main content area in light mode
    'status_frame_dark': "#2b2b2b",        # Status bar area in dark mode
    'status_frame_light': "#dde0e4",       # Status bar area in light mode
    'guest_list_frame_dark': "#2b2b2b",    # Guest list panel in dark mode
    'guest_list_frame_light': "#dde0e4",   # Guest list panel in light mode
    
    # Button colors
    'button_blue': "#3b82f6",
    'button_orange': "#ff9800", 
    'button_green': "#4CAF50",
    'button_red': "#dc3545",
    'button_grey': "#6c757d",
    'button_purple': "#9c27b0",
    'button_selected_orange': "#ff6b35",
    
    # Status colors
    'status_success': "#4CAF50",
    'status_error': "#dc3545", 
    'status_warning': "#ff9800",
    'status_info': "#3b82f6",
    
    # Theme toggle colors
    'theme_dark_text': "#e0e0e0",
    'theme_light_text': "#404040",
    
    # TreeView colors 
    # Light mode TreeView
    'treeview_bg_light': "#ffffff",          # Main tree background
    'treeview_text_light': "#212529",        # Text color
    'treeview_heading_light': "#dde0e4",     # Column headers
    'treeview_odd_row_light': "#dde0e4",     # Alternating row color 1
    'treeview_even_row_light': "#ffffff",    # Alternating row color 2  
    'treeview_summary_light': "#dde0e4",     # Summary row background
    'treeview_summary_text_light': "#ff9800",# Summary row text color
    'treeview_selected_bg_light': "#cce5ff", # Selected row background
    'treeview_selected_fg_light': "#004085", # Selected row text
    
    # Dark mode TreeView
    'treeview_bg_dark': "#212121",           # Main tree background
    'treeview_text_dark': "white",             # Text color
    'treeview_heading_dark': "#2b2b2b",      # Column headers
    'treeview_odd_row_dark': "#2b2b2b",      # Alternating row color 1
    'treeview_even_row_dark': "#353535",     # Alternating row color 2
    'treeview_summary_dark': "#2b2b2b",      # Summary row background
    'treeview_summary_text_dark': "#ff9800", # Summary row text color
    'treeview_selected_bg_dark': "#4a4a4a",  # Selected row background
    'treeview_selected_fg_dark': "white",      # Selected row text
    
    # TreeView hover row colors
    'treeview_complete_bg': "#4CAF50",       # Fully checked-in guests (green)
    'treeview_complete_fg': "black",           # Text on complete background
    'treeview_hover_bg': "#ff9800",          # Manual check-in hover (orange)
    'treeview_hover_fg': "black",              # Text on hover background
    
    # TreeView normal hover colors (theme-specific)
    'treeview_normal_hover_light': "#e3f2fd", # Light blue hover in light mode
    'treeview_normal_hover_dark': "#424242",  # Grey hover in dark mode
    
    # TreeView font sizes
    'treeview_data_font_size': 13,           # Guest list data cell font size
    'treeview_header_font_size': 15,         # Guest list column header font size  
    'treeview_summary_font_size': 16,        # Summary row font size
}


class NFCApp(ctk.CTk):
    """Main application window."""

    # Status message constants
    STATUS_READY_REGISTRATION = ""
    STATUS_READY_WAITING_FOR_CHECKIN = "Check-in service running in the background..."
    STATUS_WAITING_FOR_CHECKIN = "Waiting for check-in..."
    STATUS_READY_CHECKIN = ""
    STATUS_CHECKIN_PAUSED = "Check-in Paused"
    STATUS_NFC_NOT_CONNECTED = "NFC READER NOT CONNECTED"
    STATUS_NFC_CONNECTED = "NFC reader connected!"
    STATUS_NO_TAG_DETECTED = "No tag detected - try again"
    STATUS_PLEASE_ENTER_GUEST_ID = "Please enter a Guest ID first"
    STATUS_INVALID_ID_FORMAT = "Invalid ID format"
    STATUS_TAG_ALREADY_REGISTERED = "Tag already registered to {guest_name}"
    STATUS_REFRESHING = "Refreshing.."
    
    # Sync status label constants
    SYNC_STATUS_CONNECTED = "Live  ◉"
    SYNC_STATUS_EMPTY = "Sheets Empty  ✕"
    SYNC_STATUS_RATE_LIMITED = "Rate Limited  ✕"
    SYNC_STATUS_NO_INTERNET = "No Internet  ✕"
    SYNC_STATUS_OFFLINE = "Google Service Offline  ✕"
    SYNC_STATUS_ERROR = "Sync Failed  ✕"
    
    # Internet connectivity test constants
    TEST_INTERNET_URL = "http://www.google.com"
    TEST_INTERNET_TIMEOUT = 4
    

    def __init__(self, config: dict, nfc_service, sheets_service, tag_manager, logger):
        super().__init__()

        self.config = config
        self.nfc_service = nfc_service
        self.sheets_service = sheets_service
        self.tag_manager = tag_manager
        self.logger = logger
        
        # Initialize theme state from config EARLY
        saved_theme = self.config.get('theme', 'dark')
        self.is_light_mode = (saved_theme == 'light')
        
        # Apply saved theme immediately
        if self.is_light_mode:
            ctk.set_appearance_mode("light")
            self.logger.info("Applied light theme from config")
        else:
            ctk.set_appearance_mode("dark")
            self.logger.info("Applied dark theme from config")

        # State
        self.current_station = "Reception"
        self.logger.info(f"Starting at station: {self.current_station}")
        self.is_registration_mode = False  # Reception is now checkpoint-only
        self.is_checkpoint_mode = True  # All stations are checkpoint stations
        self.guest_list_visible = False
        self.checkin_buttons_visible = False  # Hidden by default
        self.show_all_stations = True  # False = current station only
        self.settings_visible = False  # Settings panel visibility
        self.is_rewrite_mode = False  # Rewrite tag mode
        self.guests_data = []
        self.is_scanning = False
        self._scanning_thread_active = False  # Track active scanning thread
        self.erase_confirmation_state = False  # Track erase button confirmation state

        # Sorting removed due to summary row

        # Track hovered item for styling
        self.hovered_item = None

        # Operation tracking
        self.operation_in_progress = False
        self.last_sync_count = 0
        self._active_operations = 0  # Track active operations
        self.is_refreshing = False  # Flag to prevent concurrent refreshes
        self._rewrite_check_operation_active = False  # Track rewrite countdown operation
        self._rewrite_countdown_timer = None  # Timer for register countdown
        self._nfc_operation_lock = False  # Global lock to prevent concurrent NFC operations
        self._sheets_refresh_lock = threading.Lock()  # Prevent concurrent Google Sheets API calls
        
        # NFC connection tracking
        self._nfc_connected = False
        self._nfc_connection_error_logged = False
        self._check_nfc_connection_timer = None
        self._initial_ui_setup = True  # Flag to prevent NFC error on startup

        # Tag info display state
        self.is_displaying_tag_info = False
        self.tag_info_data = None

        # Settings auto-close timer
        self._settings_timer = None

        # Station caching to reduce API calls
        self._gui_cached_stations = None
        self._station_cache_time = 0

        # Thread pool management
        self.thread_pool = ThreadPoolExecutor(max_workers=3)
        self._shutdown_event = threading.Event()

        # Window setup
        self.withdraw()  # Hide window during initialization
        self.title(config['ui']['window_title'])
        
        # Set initial geometry with centered position
        width = config['ui']['window_width']
        height = config['ui']['window_height']
        self.update_idletasks()  # Ensure screen dimensions are available
        
        # Get actual screen dimensions
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        # If window is larger than screen, use 90% of screen size
        if width > screen_width or height > screen_height:
            width = int(screen_width * 0.9)
            height = int(screen_height * 0.9)
            self.logger.info(f"Window size adjusted to fit screen: {width}x{height}")
        
        # Calculate center position
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
        
        self.minsize(800, 800)

        # Check critical files before UI initialization
        self.check_file_integrity()
        
        # Setup UI
        self.setup_styles()
        self.create_widgets()
        self.load_logo()
        
        # Apply theme to TreeView immediately after widgets are created
        self._update_treeview_theme()
        
        # Platform-specific fullscreen implementation - moved after UI creation to prevent white screen
        self.setup_fullscreen()

        # Load initial data
        self.after(100, lambda: self.refresh_guest_data(user_initiated=False))
        
        # Also refresh stations after a short delay to catch any initially failed dynamic station loading
        self.after(1000, self._delayed_station_refresh)
        
        # Start periodic connection status check
        self.after(5000, self._periodic_status_check)
        
        # Start lightweight internet monitoring (after initial load)
        self.after(10000, self._check_internet_periodically)

        # Set up sync completion callback to update UI when background syncs complete
        self.tag_manager.set_sync_completion_callback(self.on_sync_complete)

        # Handle window close
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Bind ESC key to close dialogs
        self.bind_all("<Escape>", self.on_escape_key)
        
        # Grab focus when app launches
        self.after(100, self._grab_app_focus)
        
        # Start NFC connection monitoring after initial data load
        self.after(2500, self.start_nfc_connection_monitoring)

    def _grab_app_focus(self):
        """Show window and grab focus when app launches."""
        try:
            self.deiconify()  # Show window now that all UI is built
            self.lift()  # Bring window to front on launch only
            self.focus_force()  # Force focus to the window on launch only
        except Exception as e:
            self.logger.debug(f"Could not grab app focus: {e}")

    def _update_status_with_correct_type(self):
        """Update status with correct message and type based on current state."""
        message = self.get_ready_status_message()
        if message == self.STATUS_NFC_NOT_CONNECTED:
            self.update_status(message, "error", auto_clear=False)
        else:
            self.update_status(message, "normal", auto_clear=False)

    def _update_status_respecting_settings_mode_with_correct_type(self):
        """Update status with correct type while respecting settings mode."""
        message = self.get_ready_status_message()
        if message == self.STATUS_NFC_NOT_CONNECTED:
            self.update_status_respecting_settings_mode(message, "error")
        else:
            self.update_status_respecting_settings_mode(message, "normal")

    def update_status(self, message: str, status_type: str = "normal"):
        """Update status bar with message."""
        color_map = {
            "normal": "#ffffff",
            "success": "#4CAF50",
            "warning": "#ff9800",
            "error": "#f44336",
            "info": "#2196F3"
        }
        color = color_map.get(status_type, "#ffffff")
        self.safe_update_widget(
            'status_label',
            lambda w, text, tc: w.configure(text=text, text_color=tc),
            message, color
        )

    def submit_background_task(self, func, *args):
        """Submit background task to managed pool."""
        if not self._shutdown_event.is_set():
            return self.thread_pool.submit(func, *args)

    def on_closing(self):
        """Handle window close event."""
        self._shutdown_event.set()
        self.is_scanning = False
        if self._check_nfc_connection_timer:
            self.after_cancel(self._check_nfc_connection_timer)
        self.cleanup_widgets()
        self.thread_pool.shutdown(wait=True, timeout=5)
        self.destroy()
        
    def start_nfc_connection_monitoring(self):
        """Start monitoring NFC reader connection status."""
        # Clear initial UI setup flag
        self._initial_ui_setup = False
        
        # Do initial check to set the state correctly
        self._nfc_connected = self.nfc_service.is_connected
        
        # Only show disconnection message if we're actually disconnected after initial check
        if not self._nfc_connected:
            self.update_status(self.STATUS_NFC_NOT_CONNECTED, "error", auto_clear=False)
            # Update UI if in registration mode to hide elements
            if self.is_registration_mode and not self.settings_visible:
                self.update_mode_content()
        else:
            # NFC is connected - show waiting for check-in message
            if not self.is_registration_mode or self.is_checkpoint_mode:
                self._update_status_with_correct_type()
            
        # Start periodic checking
        self.check_nfc_connection()
        
    def check_nfc_connection(self):
        """Check NFC reader connection status periodically."""
        if self._shutdown_event.is_set():
            return
            
        was_connected = self._nfc_connected
        self._nfc_connected = self.nfc_service.is_connected
        
        # Connection status changed
        if was_connected != self._nfc_connected:
            if self._nfc_connected:
                # Just connected
                self.logger.info("NFC reader connected")
                self._nfc_connection_error_logged = False
                # Only show status if not in other operations
                if not self.operation_in_progress:
                    self.update_status(self.STATUS_NFC_CONNECTED, "success", auto_clear=True)
                    # Auto-clear is now handled by update_status after 2 seconds
                    self.after(2000, lambda: self._update_status_with_correct_type())
                # Resume scanning if appropriate
                self._resume_appropriate_scanning()
                # Update checkpoint content to show waiting message
                if not self.is_registration_mode or self.is_checkpoint_mode:
                    self._safe_configure_checkpoint_status()
                # Update registration content to show UI elements
                elif self.is_registration_mode and not self.settings_visible:
                    self.update_mode_content()
            else:
                # Just disconnected
                if not self._nfc_connection_error_logged:
                    self.logger.error("NFC reader disconnected")
                    self._nfc_connection_error_logged = True
                self.update_status(self.STATUS_NFC_NOT_CONNECTED, "error", auto_clear=False)
                # Stop all scanning
                self.is_scanning = False
                # Update checkpoint content to hide waiting message
                if not self.is_registration_mode or self.is_checkpoint_mode:
                    self._safe_configure_checkpoint_status()
                # Update registration content to hide UI elements
                elif self.is_registration_mode and not self.settings_visible:
                    self.update_mode_content()
                
                
        # Schedule next check - more frequent when disconnected
        check_interval = 2000 if self._nfc_connected else 5000  # 2s when connected, 5s when disconnected
        self._check_nfc_connection_timer = self.after(check_interval, self.check_nfc_connection)
        
    def _resume_appropriate_scanning(self):
        """Resume the appropriate scanning mode after NFC reconnection."""
        # Don't start if in settings or operation in progress
        if self.settings_visible or self.operation_in_progress or self.is_displaying_tag_info:
            return
            
        if self.is_rewrite_mode:
            # Register tag mode should NOT have background scanning
            self.logger.debug("Skipping background scanning in register tag mode")
        else:
            # All stations (including Reception) use checkpoint scanning
            self.start_checkpoint_scanning()

    def get_ready_status_message(self):
        """Get the appropriate ready status message based on current mode."""
        # Always check NFC connection first - use real-time check for accuracy
        if not self.nfc_service.is_connected:
            return self.STATUS_NFC_NOT_CONNECTED
        # Don't show ready messages in settings
        elif self.settings_visible:
            return ""
        # Show appropriate ready message based on station
        elif self.current_station == "Reception":
            return self.STATUS_READY_REGISTRATION
        else:
            return self.STATUS_READY_CHECKIN

    def check_file_integrity(self):
        """Check integrity of critical configuration files."""
        import os
        from pathlib import Path
        
        issues = []
        
        # Critical files to check
        critical_files = {
            'config/credentials.json': 'Google Sheets access',
            'config/config.json': 'Application configuration'
        }
        
        # Check config directory exists
        config_dir = Path('config')
        if not config_dir.exists():
            try:
                config_dir.mkdir(exist_ok=True)
                self.logger.info("Created missing config directory")
            except Exception as e:
                issues.append(f"Cannot create config directory: {e}")
        
        # Check write permissions
        try:
            test_file = config_dir / '.write_test'
            test_file.write_text('test')
            test_file.unlink()
        except Exception:
            issues.append("No write permission to config directory")
        
        # Check critical files
        for file_path, description in critical_files.items():
            file_obj = Path(file_path)
            if not file_obj.exists():
                if 'credentials.json' in file_path:
                    issues.append(f"Missing {description} file - check Google Sheets setup guide")
                else:
                    self.logger.warning(f"Missing {file_path} - will use defaults")
            else:
                # Check if file is readable
                try:
                    file_obj.read_text()
                except Exception as e:
                    issues.append(f"Cannot read {description} file: {e}")
        
        # Check logs directory
        logs_dir = Path('logs')
        if not logs_dir.exists():
            try:
                logs_dir.mkdir(exist_ok=True)
                self.logger.info("Created missing logs directory")
            except Exception as e:
                issues.append(f"Cannot create logs directory: {e}")
        
        # Show user-actionable issues
        if issues:
            error_msg = "Configuration issues detected:\n\n" + "\n• ".join(issues)
            error_msg += "\n\nCheck logs for detailed information."
            self.logger.error(f"File integrity issues: {issues}")
            # Show dialog after UI is ready
            self.after(1000, lambda: self._show_integrity_dialog(error_msg))

    def _show_integrity_dialog(self, message):
        """Show file integrity issues to user."""
        import tkinter.messagebox as messagebox
        messagebox.showerror("Configuration Issues", message)

    def setup_fullscreen(self):
        """Configure window display mode based on config settings."""
        system = platform.system()
        window_mode = self.config.get('ui', {}).get('window_mode', 'maximized').lower()

        self.logger.info(f"Setting window mode: {window_mode}")

        try:
            if window_mode == "fullscreen":
                self._set_fullscreen_mode(system)
            elif window_mode == "maximized":
                self._set_maximized_mode(system)
            elif window_mode == "normal":
                self._set_normal_mode()
            else:
                self.logger.warning(f"Unknown window mode '{window_mode}', using maximized")
                self._set_maximized_mode(system)

        except Exception as e:
            self.logger.warning(f"Window setup failed: {e}")
            # Final fallback to manual fullscreen
            try:
                width = self.winfo_screenwidth()
                height = self.winfo_screenheight()
                self.geometry(f"{width}x{height}+0+0")
                self.logger.info("Using geometry-based fullscreen fallback")
            except Exception as e2:
                self.logger.warning(f"Geometry fallback failed: {e2}")

        # Add F11 to toggle maximized state
        self.bind('<F11>', self.toggle_fullscreen)

        # Add refresh shortcuts (Cmd+R on Mac, Ctrl+R on Windows/Linux)
        if system == "Darwin":  # macOS
            self.bind('<Command-r>', self.on_refresh_shortcut)
            self.bind('<Command-f>', self.on_search_shortcut)
        else:  # Windows/Linux
            self.bind('<Control-r>', self.on_refresh_shortcut)
            self.bind('<Control-f>', self.on_search_shortcut)

    def _set_fullscreen_mode(self, system):
        """Set window to fullscreen mode."""
        if system == "Darwin":  # macOS
            try:
                self.attributes('-fullscreen', True)
                self.logger.info("macOS fullscreen mode enabled")
            except tk.TclError:
                # Fallback
                width = self.winfo_screenwidth()
                height = self.winfo_screenheight()
                self.geometry(f"{width}x{height}+0+0")
                self.logger.info("macOS using manual fullscreen geometry")
        elif system == "Linux":
            try:
                self.attributes('-fullscreen', True)
                self.logger.info("Linux fullscreen mode enabled")
            except tk.TclError:
                width = self.winfo_screenwidth()
                height = self.winfo_screenheight()
                self.geometry(f"{width}x{height}+0+0")
                self.logger.info("Linux using manual fullscreen geometry")
        else:  # Windows
            # Windows doesn't have true fullscreen, use maximized
            self.state('zoomed')
            self.logger.info("Windows maximized (fullscreen not supported)")

    def _set_maximized_mode(self, system):
        """Set window to maximized mode."""
        if system == "Darwin":  # macOS
            try:
                self.attributes('-zoomed', True)
                self.logger.info("macOS window maximized with -zoomed")
            except tk.TclError:
                try:
                    self.state('zoomed')
                    self.logger.info("macOS window maximized with state zoomed")
                except tk.TclError:
                    width = self.winfo_screenwidth()
                    height = self.winfo_screenheight()
                    self.geometry(f"{width}x{height}+0+0")
                    self.logger.info("macOS using manual fullscreen geometry")
        elif system == "Windows":
            self.state('zoomed')
            self.logger.info("Windows window maximized")
        elif system == "Linux":
            try:
                self.attributes('-zoomed', True)
                self.logger.info("Linux window maximized")
            except tk.TclError:
                width = self.winfo_screenwidth()
                height = self.winfo_screenheight()
                self.geometry(f"{width}x{height}+0+0")
                self.logger.info("Linux using manual fullscreen geometry")

    def _set_normal_mode(self):
        """Set window to normal size and center it."""
        width = self.config['ui']['window_width']
        height = self.config['ui']['window_height']
        
        # Update window to ensure we can get screen dimensions
        self.update_idletasks()
        
        # Get actual screen dimensions
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        # If window is larger than screen, use 90% of screen size
        if width > screen_width or height > screen_height:
            width = int(screen_width * 0.9)
            height = int(screen_height * 0.9)
        
        # Calculate center position
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        
        self.geometry(f"{width}x{height}+{x}+{y}")
        self.logger.info(f"Window set to normal size: {width}x{height} centered at {x},{y} on {screen_width}x{screen_height} screen")

    def toggle_fullscreen(self, event=None):
        """Toggle between fullscreen, maximized and normal window state."""
        system = platform.system()

        try:
            if system == "Darwin":  # macOS
                # Check current state and cycle through: normal -> maximized -> fullscreen -> normal
                try:
                    is_fullscreen = self.attributes('-fullscreen')
                    is_zoomed = self.attributes('-zoomed')

                    if is_fullscreen:
                        # Exit fullscreen to normal
                        self.attributes('-fullscreen', False)
                        self.geometry(f"{self.config['ui']['window_width']}x{self.config['ui']['window_height']}")
                    elif is_zoomed:
                        # Go to fullscreen
                        self.attributes('-fullscreen', True)
                    else:
                        # Go to maximized
                        self.attributes('-zoomed', True)
                except tk.TclError:
                    # Fallback for older macOS
                    if self.state() == 'zoomed':
                        self.state('normal')
                        self.geometry(f"{self.config['ui']['window_width']}x{self.config['ui']['window_height']}")
                    else:
                        self.state('zoomed')

            elif system == "Windows":
                if self.state() == 'zoomed':
                    self.state('normal')
                    self.geometry(f"{self.config['ui']['window_width']}x{self.config['ui']['window_height']}")
                else:
                    self.state('zoomed')

            elif system == "Linux":
                try:
                    is_fullscreen = self.attributes('-fullscreen')
                    if is_fullscreen:
                        self.attributes('-fullscreen', False)
                        self.geometry(f"{self.config['ui']['window_width']}x{self.config['ui']['window_height']}")
                    else:
                        self.attributes('-fullscreen', True)
                except tk.TclError:
                    # Fallback
                    current_state = self.attributes('-zoomed') if hasattr(self, 'attributes') else False
                    if current_state:
                        width = self.config['ui']['window_width']
                        height = self.config['ui']['window_height']
                        self.geometry(f"{width}x{height}")
                    else:
                        width = self.winfo_screenwidth()
                        height = self.winfo_screenheight()
                        self.geometry(f"{width}x{height}+0+0")

        except Exception as e:
            self.logger.error(f"Error toggling fullscreen: {e}")

    def on_refresh_shortcut(self, event=None):
        """Handle refresh keyboard shortcut (Cmd+R / Ctrl+R)."""
        # Clear search field and guest ID fields for user-initiated refresh
        if hasattr(self, 'search_var'):
            self.search_var.set("")
        if hasattr(self, 'id_entry'):
            self.id_entry.delete(0, 'end')
        if hasattr(self, 'rewrite_id_entry'):
            self.rewrite_id_entry.delete(0, 'end')
        
        self.refresh_guest_data(user_initiated=True)
        return "break"  # Prevent default browser refresh behavior

    def on_search_shortcut(self, event=None):
        """Handle search keyboard shortcut (Cmd+F / Ctrl+F)."""
        # Only focus search if guest list is visible
        if self.guest_list_visible and hasattr(self, 'search_entry'):
            self.search_entry.focus()
            self.search_entry.select_range(0, 'end')  # Select all text for easy replacement
        return "break"  # Prevent default browser find behavior

    def setup_styles(self):
        """Configure fonts and styles."""
        self.fonts = {
            'title': CTkFont(size=24, weight="bold"),
            'heading': CTkFont(size=18, weight="bold"),
            'body': CTkFont(size=14),
            'status': CTkFont(size=16, weight="bold"),
            'button': CTkFont(size=14, weight="bold")
        }

    def create_widgets(self):
        """Create all UI widgets."""
        # Configure window background (the padded area outside main UI) - theme aware
        self._update_window_background()
        
        # Main container with padding - background area controlled by THEME_COLORS
        main_bg_color = THEME_COLORS['main_frame_light'] if self.is_light_mode else THEME_COLORS['main_frame_dark']
        self.main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color=main_bg_color)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Header frame
        self.create_header()
        
        # Content frame
        self.create_content_frame()

    def _update_window_background(self):
        """Update window background color based on current theme."""
        if hasattr(self, 'is_light_mode') and self.is_light_mode:
            bg_color = THEME_COLORS['window_background_light']
        else:
            bg_color = THEME_COLORS['window_background_dark']
        self.configure(fg_color=bg_color)

    def _update_all_frame_backgrounds(self):
        """Update all frame background colors based on current theme."""
        # Update window background
        self._update_window_background()
        
        # Update individual frames if they exist
        is_light = hasattr(self, 'is_light_mode') and self.is_light_mode
        
        # Main frame (spaces between other frames)
        if hasattr(self, 'main_frame'):
            bg_color = THEME_COLORS['main_frame_light'] if is_light else THEME_COLORS['main_frame_dark']
            self.main_frame.configure(fg_color=bg_color)
        
        # Header frame - find it in the main_frame children
        for child in self.main_frame.winfo_children():
            if isinstance(child, ctk.CTkFrame) and child.cget('height') == 80:  # Header frame
                bg_color = THEME_COLORS['header_frame_light'] if is_light else THEME_COLORS['header_frame_dark']
                child.configure(fg_color=bg_color)
                break
        
        # Content frame
        if hasattr(self, 'content_frame'):
            bg_color = THEME_COLORS['content_frame_light'] if is_light else THEME_COLORS['content_frame_dark']
            self.content_frame.configure(fg_color=bg_color)
        
        # Status frame
        if hasattr(self, 'status_frame'):
            bg_color = THEME_COLORS['status_frame_light'] if is_light else THEME_COLORS['status_frame_dark']
            self.status_frame.configure(fg_color=bg_color)
        
        # Guest list frame
        if hasattr(self, 'list_frame'):
            bg_color = THEME_COLORS['guest_list_frame_light'] if is_light else THEME_COLORS['guest_list_frame_dark']
            self.list_frame.configure(fg_color=bg_color)

    def create_content_frame(self):
        """Create content frame."""
        # Theme-aware content frame (compact size)
        bg_color = THEME_COLORS['content_frame_light'] if self.is_light_mode else THEME_COLORS['content_frame_dark']
        self.content_frame = ctk.CTkFrame(self.main_frame, corner_radius=15, height=200, fg_color=bg_color)
        self.content_frame.pack(fill="x", pady=(20, 10))
        self.content_frame.pack_propagate(False)

        # Status bar
        self.create_status_bar()

        # Action buttons - removed, buttons moved to guest list panel
        # self.create_action_buttons()

        # Guest list panel (always show initially)
        self.create_guest_list_panel()
        self.list_frame.pack(fill="both", expand=True, pady=(10, 0))
        self.guest_list_visible = True

        # Initialize content based on mode
        self.update_mode_content()

    def cleanup_widgets(self):
        """Clean up widget references to prevent memory leaks."""
        if hasattr(self, 'guest_tree'):
            # Clear all items before destroying
            for item in self.guest_tree.get_children():
                self.guest_tree.delete(item)

        # Explicit cleanup of large data structures
        self.guests_data.clear()
        if hasattr(self, '_cached_guest_data'):
            self._cached_guest_data.clear()

    def create_header(self):
        """Create header with logo and station selector."""
        # Theme-aware header frame
        bg_color = THEME_COLORS['header_frame_light'] if self.is_light_mode else THEME_COLORS['header_frame_dark']
        header_frame = ctk.CTkFrame(self.main_frame, corner_radius=15, height=80, fg_color=bg_color)
        header_frame.pack(fill="x", pady=(0, 10))
        header_frame.pack_propagate(False)

        # Logo on the left
        self.logo_label = ctk.CTkLabel(header_frame, text="", width=80, height=80)
        self.logo_label.pack(side="left", padx=20)
        
        # Bind click event for spin animation easter egg
        self.logo_label.bind("<Button-1>", self.on_logo_click)

        # Settings button on the right - modernized hamburger menu
        self.settings_btn = ctk.CTkButton(
            header_frame,
            text="☰",
            command=self.toggle_settings,
            width=50,
            height=50,
            corner_radius=10,
            font=CTkFont(size=20, weight="bold"),
            border_width=2,
            fg_color="transparent",
            text_color="#6c757d",
            border_color="#6c757d",
            hover=False  # Disable built-in hover
        )
        
        # Add hover effects for hamburger menu
        def on_hamburger_enter(event):
            if not self.settings_visible:  # Only apply hover in hamburger mode
                self.settings_btn.configure(
                    fg_color="#6c757d",
                    text_color="#ffffff"
                )
                
        def on_hamburger_leave(event):
            if not self.settings_visible:  # Only apply hover in hamburger mode
                self.settings_btn.configure(
                    fg_color="transparent",
                    text_color="#6c757d"
                )
        
        self.settings_btn.bind("<Enter>", on_hamburger_enter)
        self.settings_btn.bind("<Leave>", on_hamburger_leave)
        # Settings button first (will be rightmost)
        self.settings_btn.pack(side="right", padx=(0, 20))
        
        # Sync status label second (will be to the left of settings button)
        self.sync_status_label = ctk.CTkLabel(
            header_frame,
            text="",
            font=self.fonts['body'],
            text_color="#4CAF50"
        )
        self.sync_status_label.pack(side="right", padx=(0, 20))
        self.update_settings_button()

        # Station buttons centered
        station_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        station_frame.place(relx=0.5, rely=0.5, anchor="center")

        station_label = ctk.CTkLabel(
            station_frame,
            text="",
            font=CTkFont(size=18, weight="bold")
        )
        station_label.pack(side="left", padx=(0, 15))

        # Container for station buttons
        buttons_container = ctk.CTkFrame(station_frame, fg_color="transparent")
        buttons_container.pack(side="left")

        # Create station buttons with enhanced styling
        self.station_buttons = {}
        
        # Get dynamic stations from Google Sheets (or fallback to config)
        available_stations = self.config['stations']  # Default
        
        # Use cached stations to avoid repeated API calls - fast-fail during startup
        try:
            available_stations = self._get_filtered_stations_for_view(fast_fail_startup=True)
        except Exception as e:
            self.logger.warning(f"Could not get stations: {e}")
            available_stations = self.config['stations']
        
        for i, station in enumerate(available_stations):
            btn = ctk.CTkButton(
                buttons_container,
                text=station,
                command=lambda s=station: self.on_station_button_click(s),
                width=110,
                height=50,
                corner_radius=12,
                font=CTkFont(size=15, weight="bold"),
                border_width=2,
                fg_color="transparent",  # No fill by default
                text_color="#3b82f6",   # Blue text color
                border_color="#3b82f6"  # Blue border
                # hover_color removed - handled by custom events
            )
            
            # Add hover text color control
            def on_enter(event, button=btn, station_name=station):
                if station_name != self.current_station:  # Only for non-selected buttons
                    button.configure(
                        fg_color="#3b82f6",      # Blue fill on hover
                        text_color="#212121"     # Dark grey text on hover
                    )
            
            def on_leave(event, button=btn, station_name=station):
                if station_name != self.current_station:  # Only for non-selected buttons
                    button.configure(
                        fg_color="transparent",  # Back to transparent
                        text_color="#3b82f6"     # Back to blue text
                    )
            
            btn.bind("<Enter>", on_enter)
            btn.bind("<Leave>", on_leave)
            
            btn.pack(side="left", padx=3)
            self.station_buttons[station] = btn

        # Highlight current station
        self.update_station_buttons()
        
        # Store the buttons container for dynamic updates
        self.station_buttons_container = buttons_container

    def create_status_bar(self):
        """Create status bar."""
        # Theme-aware status frame
        bg_color = THEME_COLORS['status_frame_light'] if self.is_light_mode else THEME_COLORS['status_frame_dark']
        self.status_frame = ctk.CTkFrame(self.main_frame, corner_radius=10, height=75, fg_color=bg_color)
        self.status_frame.pack(fill="x", pady=(10, 10))
        self.status_frame.pack_propagate(False)

        # Center - main status
        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="",
            font=self.fonts['status']
        )
        self.status_label.place(relx=0.5, rely=0.5, anchor="center")

        # Right side - copyright (only visible in settings)
        self.copyright_label = ctk.CTkLabel(
            self.status_frame,
            text="© 2025 Telepathic AB",
            font=CTkFont(size=12),
            text_color="#666666"
        )
        # Initially hidden

    def create_action_buttons(self):
        """Create action buttons."""
        button_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        button_frame.pack(fill="x")

        # Left frame for buttons
        left_frame = ctk.CTkFrame(button_frame, fg_color="transparent")
        left_frame.pack(side="left")

        # Right frame for buttons
        right_frame = ctk.CTkFrame(button_frame, fg_color="transparent")
        right_frame.pack(side="right")

        # Reception mode toggle button - removed as per new requirements
        # Initially hidden, will show only at Reception

        # Manual check-in button will be created in guest list panel next to sync status
        # Initially hidden, will show in checkpoint mode

    def create_guest_list_panel(self):
        """Create guest list panel."""
        # Theme-aware guest list frame
        bg_color = THEME_COLORS['guest_list_frame_light'] if self.is_light_mode else THEME_COLORS['guest_list_frame_dark']
        self.list_frame = ctk.CTkFrame(self.main_frame, corner_radius=15, fg_color=bg_color)
        # Initially hidden

        # Search bar
        search_frame = ctk.CTkFrame(self.list_frame, fg_color="transparent")
        search_frame.pack(fill="x", padx=10, pady=(10, 5))

        search_label = ctk.CTkLabel(search_frame, text="Search:", font=self.fonts['body'])
        search_label.pack(side="left", padx=(0, 10))

        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda *args: self._on_search_change())
        self.search_entry = ctk.CTkEntry(
            search_frame,
            textvariable=self.search_var,
            placeholder_text="Name or ID...",
            width=200
        )
        self.search_entry.pack(side="left")

        # Station view toggle container
        self.switch_container = ctk.CTkFrame(search_frame, fg_color="transparent")
        
        # Station view toggle label (on the left)
        self.station_view_label = ctk.CTkLabel(
            self.switch_container,
            text="All Stations",
            font=self.fonts['button']
        )
        self.station_view_label.pack(side="left", padx=(0, 10))
        
        # Station view toggle switch (modern toggle)
        self.station_view_switch = ctk.CTkSwitch(
            self.switch_container,
            text="",  # No text on the switch itself
            command=self.toggle_station_view,
            width=60,
            height=24,
            button_color="#2196F3",
            progress_color="#1976D2"
        )
        # Set initial state (True = All Stations, False = Single Station)
        self.station_view_switch.select()
        self.station_view_switch.pack(side="left")
        
        # Manual check-in button
        self.manual_checkin_btn = ctk.CTkButton(
            search_frame,
            text="Manual Check-in",
            command=self.toggle_manual_checkin,
            width=130,
            height=35,
            corner_radius=8,
            font=self.fonts['button'],
            border_width=2,
            fg_color="transparent",
            text_color="#ff9800",
            border_color="#ff9800",
            hover=False
        )
        
        # Add hover effects for manual checkin button
        def on_manual_checkin_enter(event):
            if self.checkin_buttons_visible:
                # Blue theme for cancel state (matching logs close button)
                self.manual_checkin_btn.configure(
                    fg_color="#3b82f6",
                    text_color="#ffffff"
                )
            else:
                # Orange theme for normal state
                self.manual_checkin_btn.configure(
                    fg_color="#ff9800",
                    text_color="#212121"
                )
                
        def on_manual_checkin_leave(event):
            if self.checkin_buttons_visible:
                # Blue outline for cancel state (matching logs close button)
                self.manual_checkin_btn.configure(
                    fg_color="transparent",
                    text_color="#3b82f6"
                )
            else:
                # Orange outline for normal state
                self.manual_checkin_btn.configure(
                    fg_color="transparent",
                    text_color="#ff9800"
                )
        
        self.manual_checkin_btn.bind("<Enter>", on_manual_checkin_enter)
        self.manual_checkin_btn.bind("<Leave>", on_manual_checkin_leave)
        # Buttons will be shown/hidden in update_mode_content


        # Guest list (using tkinter Treeview for table)
        self.create_guest_table()

    def create_guest_table(self):
        """Create the guest list table."""
        # Frame for treeview (no border)
        tree_frame = ctk.CTkFrame(self.list_frame, border_width=0)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=(5, 10))

        # Container for summary and main tree
        table_container = ctk.CTkFrame(tree_frame, fg_color="transparent", border_width=0)
        table_container.pack(fill="both", expand=True)

        # Scrollbar
        scrollbar = ctk.CTkScrollbar(table_container)
        scrollbar.pack(side="right", fill="y")

        # Columns will be set dynamically by _update_table_structure()
        # Start with basic columns, will be updated based on mode
        available_stations = self._get_filtered_stations_for_view()
        columns = ("id", "first", "last") + tuple(station.lower() for station in available_stations)

        # Fixed summary treeview (non-scrollable)
        self.summary_tree = ttk.Treeview(
            table_container,
            columns=columns,
            show="headings",
            height=1  # Only one row for summary
        )
        self.summary_tree.pack(fill="x", pady=(0, 1))

        # Main guest treeview (scrollable)
        self.guest_tree = ttk.Treeview(
            table_container,
            columns=columns,
            show="headings",
            yscrollcommand=scrollbar.set
        )
        scrollbar.configure(command=self.guest_tree.yview)
        self.guest_tree.pack(fill="both", expand=True)

        # Configure column headers and widths for both trees
        for tree in [self.summary_tree, self.guest_tree]:
            # Set initial headers (will be updated with guest count later)
            tree.heading("id", text="Guest ID", anchor="w")
            tree.heading("first", text="First Name", anchor="w")
            tree.heading("last", text="Last Name", anchor="w")

            # Set responsive column widths with padding for visual separation
            tree.column("id", width=80, minwidth=60, anchor="w")
            tree.column("first", width=150, minwidth=100, anchor="w")
            tree.column("last", width=150, minwidth=100, anchor="w")

            # Station columns - will be configured by _update_table_structure()
            for i, station in enumerate(available_stations):
                tree.heading(station.lower(), text=station, anchor="center")
                tree.column(station.lower(), width=120, minwidth=80, anchor="center")

        # Style for treeview
        style = ttk.Style()
        style.theme_use("clam")

        # Remove default border/padding layout
        style.layout("Treeview", [('Treeview.treearea', {'sticky': 'nswe'})])

        # Hide headers on summary tree (we only want the summary row)
        self.summary_tree.configure(show="")

        # Bind selection and editing
        self.guest_tree.bind("<Double-Button-1>", self.on_cell_double_click)

        # Bind click for check-in button and closing edit
        self.guest_tree.bind("<Button-1>", self.on_tree_click)
        
        # Disable selection entirely by setting selectmode to 'none'
        self.guest_tree.configure(selectmode='none')
        
        
        # Track editing state
        self.edit_entry = None
        self.edit_item = None
        self.edit_column = None
        
        # Track internet connection status
        self._internet_connected = True

        # Bind mouse motion for cursor changes and tooltips
        self.guest_tree.bind("<Motion>", self.on_tree_motion)
        self.guest_tree.bind("<Leave>", self.on_tree_leave)
        # Bind scroll events to update the hover at current mouse position
        self.guest_tree.bind("<MouseWheel>", self._on_scroll)  # For Windows/macOS
        self.guest_tree.bind("<Button-4>", self._on_scroll)    # For Linux scroll up
        self.guest_tree.bind("<Button-5>", self._on_scroll)    # For Linux scroll down
        
        # Disable hover/click effects for summary tree
        self.summary_tree.bind("<Motion>", lambda e: None)
        self.summary_tree.bind("<Leave>", lambda e: None)
        self.summary_tree.bind("<Button-1>", lambda e: "break")  # Prevent clicks
        
        # Tooltip state tracking
        self._tooltip_timer = None
        self._tooltip_window = None
        self._tooltip_item = None
        self._tooltip_column = None
        

        # Column headers without sorting functionality
        self.guest_tree.pack(fill="both", expand=True)

        # Configure tags for styling (like working version)
        self.guest_tree.tag_configure("checkin_hover", background=THEME_COLORS['treeview_hover_bg'], foreground=THEME_COLORS['treeview_hover_fg'])
        self.guest_tree.tag_configure("complete", background=THEME_COLORS['treeview_complete_bg'], foreground=THEME_COLORS['treeview_complete_fg'])
        # Tag configurations moved to _update_treeview_theme() for theme consistency

    def _is_guest_fully_checked_in(self, guest, available_stations):
        """Check if guest is checked in at all available stations."""
        for station in available_stations:
            station_key = station.lower()
            
            # Check both local and sheets data
            local_time = None
            sheets_time = None
            
            # Get local check-ins
            if hasattr(self, 'tag_manager'):
                local_check_ins = self.tag_manager.get_all_local_check_ins()
                guest_local_data = local_check_ins.get(guest.original_id, {})
                local_time = guest_local_data.get(station_key)
            
            # Get Google Sheets data
            if hasattr(guest, 'get_check_in_time'):
                sheets_time = guest.get_check_in_time(station_key)
            
            # If neither local nor sheets has data for this station, not complete
            if not sheets_time and not local_time:
                return False
        
        return True

    def _update_row_styling(self, item, guest_id):
        """Update row styling after edit to reflect complete status."""
        try:
            # Get stations based on current view mode
            view_stations = self._get_filtered_stations_for_view()
            
            # Get the current values from the tree item
            item_values = self.guest_tree.item(item)['values']
            
            # Check completion based on view mode
            if self.show_all_stations:
                # All stations mode: must have check-ins at ALL stations
                fully_checked_in = self._is_guest_complete_all_stations(int(guest_id), view_stations, item_values)
            else:
                # Current station mode: only need check-in at current station
                fully_checked_in = self._is_guest_complete_current_station(int(guest_id), item_values)
            
            # Apply appropriate styling
            if fully_checked_in:
                self.guest_tree.item(item, tags=["complete"])
            else:
                # Determine alternate row color
                row_index = self.guest_tree.index(item)
                if row_index % 2 == 0:
                    self.guest_tree.item(item, tags=["even"])
                else:
                    self.guest_tree.item(item, tags=["odd"])
        except Exception as e:
            self.logger.debug(f"Error updating row styling: {e}")

    def create_tag_info_content(self):
        """Create inline tag info display."""
        if not self.tag_info_data:
            return

        # Hide copyright text
        self.copyright_label.place_forget()

        # Note: All stations are now checkpoint-only, no special status bar hiding needed

        # Main container
        main_container = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        main_container.pack(fill="both", expand=True)

        # Center frame for content
        center_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        center_frame.place(relx=0.5, rely=0.5, anchor="center")

        # Guest details
        guest = self.tag_info_data['guest']
        check_ins = self.tag_info_data['check_ins']

        # Guest name
        name_label = ctk.CTkLabel(
            center_frame,
            text=f"{guest.firstname} {guest.lastname}",
            font=CTkFont(size=32, weight="bold"),
            text_color="#4CAF50"
        )
        name_label.pack(pady=(0, 20))

        # Find last check-in
        last_station = None
        last_time = None
        for station, time in check_ins.items():
            if time:
                last_station = station.title()
                last_time = time

        if last_station and last_time:
            # Last check-in:
            checkin_header_label = ctk.CTkLabel(
                center_frame,
                text="Last check-in:",
                font=CTkFont(size=18),
                text_color="#ffffff"
            )
            checkin_header_label.pack(pady=(0, 10))

            # Station name
            station_label = ctk.CTkLabel(
                center_frame,
                text=last_station,
                font=CTkFont(size=24, weight="bold"),
                text_color="#ffffff"
            )
            station_label.pack(pady=(0, 10))

            # Check-in time
            time_label = ctk.CTkLabel(
                center_frame,
                text=last_time,
                font=CTkFont(size=24, weight="bold"),
                text_color="#ffffff"
            )
            time_label.pack(pady=(0, 30))
        else:
            # No check-ins recorded
            no_checkin_label = ctk.CTkLabel(
                center_frame,
                text="No check-ins recorded",
                font=CTkFont(size=18),
                text_color="#ffffff"
            )
            no_checkin_label.pack(pady=(0, 30))

        # Countdown label
        self.tag_info_countdown_label = ctk.CTkLabel(
            center_frame,
            text="Auto-close in 10s",
            font=CTkFont(size=14),
            text_color="#999999"
        )
        self.tag_info_countdown_label.pack(pady=(0, 20))

        # Close button 
        close_btn = ctk.CTkButton(
            center_frame,
            text="✕",
            command=self.close_tag_info,
            width=50,
            height=50,
            corner_radius=10,
            font=CTkFont(size=20, weight="bold"),
            border_width=2,
            fg_color="transparent",
            text_color="#dc3545",
            border_color="#dc3545"
        )
        
        # Add hover effects for close button
        def on_close_enter(event, button=close_btn):
            button.configure(
                fg_color="#dc3545",
                text_color="#212121"
            )
            
        def on_close_leave(event, button=close_btn):
            button.configure(
                fg_color="transparent",
                text_color="#dc3545"
            )
            
        close_btn.bind("<Enter>", on_close_enter)
        close_btn.bind("<Leave>", on_close_leave)
        
        close_btn.pack()

        # Start auto-close countdown
        self._tag_info_auto_close_active = True
        self._tag_info_auto_close_countdown(10)

    def _tag_info_auto_close_countdown(self, countdown: int):
        """Auto-close countdown for tag info panel."""
        if countdown > 0 and self._tag_info_auto_close_active and self.is_displaying_tag_info:
            self.safe_update_widget(
                'tag_info_countdown_label',
                lambda w, text: w.configure(text=text),
                f"Auto-close in {countdown}s"
            )
            self.after(1000, lambda: self._tag_info_auto_close_countdown(countdown - 1))
        elif self._tag_info_auto_close_active and self.is_displaying_tag_info:
            # Countdown reached 0 - auto close
            self.close_tag_info()

    def close_tag_info(self):
        """Close tag info display and return to station view."""
        # Stop auto-close countdown
        self._tag_info_auto_close_active = False

        self.is_displaying_tag_info = False
        self.tag_info_data = None

        # Always return to station view (not settings)
        self.settings_visible = False
        self._cancel_settings_timer()
        # Clear search field when closing settings
        self.clear_search()
        
        # Clean up came_from_settings flag if it exists
        if hasattr(self, '_came_from_settings'):
            delattr(self, '_came_from_settings')

        # Status bar frame is never hidden, only content is cleared, so no need to restore it

        self.update_mode_content()
        self.update_settings_button()  # Restore hamburger button

        # Resume scanning if in checkpoint mode
        if not self.is_registration_mode or self.is_checkpoint_mode:
            self.start_checkpoint_scanning()

        # Set appropriate status based on current mode (but not in settings)
        if not self.settings_visible:
            self._update_status_with_correct_type()

    def create_settings_content(self):
        """Create settings content in the main content area."""
        # Status is already set by toggle_settings() - don't override it here
        # This prevents the "Ready" flash when opening settings

        # Main container with theme-aware rounded background that fills the content area
        bg_color = THEME_COLORS['content_frame_light'] if self.is_light_mode else THEME_COLORS['content_frame_dark']
        main_container = ctk.CTkFrame(self.content_frame, fg_color=bg_color, corner_radius=15)
        main_container.pack(fill="both", expand=True, padx=20, pady=20)

        # Center frame for centering the buttons - transparent to show main_container background
        center_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        center_frame.place(relx=0.5, rely=0.5, anchor="center")

        # Buttons container
        buttons_container = ctk.CTkFrame(center_frame, fg_color="transparent")
        buttons_container.pack(padx=20, pady=20)

        # Tag Info button with frame for cancel button
        tag_info_frame = ctk.CTkFrame(buttons_container, fg_color="transparent")
        tag_info_frame.pack(pady=10)

        self.tag_info_btn = ctk.CTkButton(
            tag_info_frame,
            text="Tag Info",
            command=self.tag_info,
            width=200,
            height=50,
            corner_radius=8,
            font=self.fonts['button'],
            border_width=2,
            fg_color="transparent",
            text_color="#2196F3",
            border_color="#2196F3",
            hover=False
        )
        
        # Add hover effects for Tag Info button
        def on_tag_info_enter(event):
            self.tag_info_btn.configure(fg_color="#2196F3", text_color="#212121")
        def on_tag_info_leave(event):
            self.tag_info_btn.configure(fg_color="transparent", text_color="#2196F3")
        
        self.tag_info_btn.bind("<Enter>", on_tag_info_enter)
        self.tag_info_btn.bind("<Leave>", on_tag_info_leave)
        self.tag_info_btn.pack(side="left")

        # Register Tag button
        self.rewrite_tag_btn = ctk.CTkButton(
            buttons_container,
            text="Register Tag",
            command=self.rewrite_tag,
            width=200,
            height=50,
            corner_radius=8,
            font=self.fonts['button'],
            border_width=2,
            fg_color="transparent",
            text_color="#ff9800",
            border_color="#ff9800",
            hover=False
        )
        
        # Add hover effects for Rewrite Tag button (settings)
        def on_rewrite_tag_enter(event):
            self.rewrite_tag_btn.configure(fg_color="#ff9800", text_color="#212121")
        def on_rewrite_tag_leave(event):
            self.rewrite_tag_btn.configure(fg_color="transparent", text_color="#ff9800")
        
        self.rewrite_tag_btn.bind("<Enter>", on_rewrite_tag_enter)
        self.rewrite_tag_btn.bind("<Leave>", on_rewrite_tag_leave)
        self.rewrite_tag_btn.pack(pady=10)

        # Erase Tag button with frame for cancel button (moved up)
        erase_frame = ctk.CTkFrame(buttons_container, fg_color="transparent")
        erase_frame.pack(pady=10)

        self.settings_erase_btn = ctk.CTkButton(
            erase_frame,
            text="Erase Tag",
            command=self.erase_tag_settings,
            width=200,
            height=50,
            corner_radius=8,
            font=self.fonts['button'],
            border_width=2,
            fg_color="transparent",
            text_color="#dc3545",
            border_color="#dc3545"
        )
        
        # Add hover effects for Erase Tag button
        def on_erase_enter(event):
            self.settings_erase_btn.configure(fg_color="#dc3545", text_color="#212121")
        def on_erase_leave(event):
            self.settings_erase_btn.configure(fg_color="transparent", text_color="#dc3545")
        
        self.settings_erase_btn.bind("<Enter>", on_erase_enter)
        self.settings_erase_btn.bind("<Leave>", on_erase_leave)
        self.settings_erase_btn.pack(side="left")

        # Theme Toggle button (replaces redundant Refresh Guest List)
        
        # Set button text and colors to show what it will switch TO
        if self.is_light_mode:
            button_text = "Dark Mode"
            button_color = "#404040"  # Dark grey - switch to dark mode
        else:
            button_text = "Light Mode"
            button_color = "#e0e0e0"  # Light grey - switch to light mode
            
        self.theme_btn = ctk.CTkButton(
            buttons_container,
            text=button_text,
            command=self.toggle_theme,
            width=200,
            height=50,
            corner_radius=8,
            font=self.fonts['button'],
            border_width=2,
            fg_color="transparent",
            text_color=button_color,
            border_color=button_color,
            hover=False  # Disable built-in hover
        )
        
        # Add hover effects for Theme Toggle button
        def on_theme_enter(event):
            self.theme_btn.configure(fg_color=button_color, text_color="#212121")
        def on_theme_leave(event):
            self.theme_btn.configure(fg_color="transparent", text_color=button_color)
        
        self.theme_btn.bind("<Enter>", on_theme_enter)
        self.theme_btn.bind("<Leave>", on_theme_leave)
        self.theme_btn.pack(pady=10)

        # Log button
        self.log_btn = ctk.CTkButton(
            buttons_container,
            text="View Logs",
            command=self.show_logs,
            width=200,
            height=50,
            corner_radius=8,
            font=self.fonts['button'],
            border_width=2,
            fg_color="transparent",
            text_color="#9c27b0",
            border_color="#9c27b0"
        )
        
        # Add hover effects for View Logs button
        def on_logs_enter(event):
            self.log_btn.configure(fg_color="#9c27b0", text_color="#212121")
        def on_logs_leave(event):
            self.log_btn.configure(fg_color="transparent", text_color="#9c27b0")
        
        self.log_btn.bind("<Enter>", on_logs_enter)
        self.log_btn.bind("<Leave>", on_logs_leave)
        self.log_btn.pack(pady=10)

        # Advanced button
        self.dev_mode_btn = ctk.CTkButton(
            buttons_container,
            text="Advanced",
            command=self.enter_developer_mode,
            width=200,
            height=50,
            corner_radius=8,
            font=self.fonts['button'],
            border_width=2,
            fg_color="transparent",
            text_color="#6c757d",
            border_color="#6c757d"
        )
        
        # Add hover effects for Advanced button
        def on_advanced_enter(event):
            self.dev_mode_btn.configure(fg_color="#6c757d", text_color="#212121")
        def on_advanced_leave(event):
            self.dev_mode_btn.configure(fg_color="transparent", text_color="#6c757d")
        
        self.dev_mode_btn.bind("<Enter>", on_advanced_enter)
        self.dev_mode_btn.bind("<Leave>", on_advanced_leave)
        self.dev_mode_btn.pack(pady=10)


    def toggle_settings(self):
        """Toggle settings panel visibility or close register mode."""
        # Handle register mode closing
        if self.is_rewrite_mode:
            self.logger.info("User clicked X button - closing register mode")
            self.close_register_mode()
            return
            
        action = "open" if not self.settings_visible else "close"
        self.logger.info(f"User clicked Settings button - {action} settings panel")
        # Block settings toggle if operation is in progress
        if self.operation_in_progress:
            self.update_status("Please wait for current operation to complete", "warning")
            return
            
        if self.settings_visible:
            # If settings are already open, close them
            self.settings_visible = False
            self._cancel_settings_timer()
            # Clear search field when closing settings
            self.clear_search()
            # Reset erase confirmation state when leaving settings
            self._reset_erase_confirmation()
            # Clear any stale settings references
            if hasattr(self, '_came_from_settings'):
                delattr(self, '_came_from_settings')
            self.update_mode_content()
            # Return to appropriate status
            if self.is_rewrite_mode:
                pass  # No status message needed - "Check-in Paused" shown in stations frame
            else:
                self._update_status_with_correct_type()
        else:
            self.settings_visible = True
            # Always stop any old timer and start fresh when opening settings
            self._cancel_settings_timer()  # Stop any ghost timers
            self._restart_settings_timer()  # Start fresh timer
            # Don't stop scanning when entering settings
            # Show appropriate status - check NFC connection first
            if not self.nfc_service.is_connected:
                self.update_status(self.STATUS_NFC_NOT_CONNECTED, "error", auto_clear=False)
            else:
                self.update_status(self.STATUS_READY_WAITING_FOR_CHECKIN, "normal")
            self.update_mode_content()
        
        self.update_settings_button()

    def update_settings_button(self):
        """Update settings button appearance based on state."""
        if self.is_displaying_tag_info:
            # Hide hamburger button completely when in tag info view
            self.settings_btn.pack_forget()
        elif self.is_rewrite_mode:
            # Show red X button in register mode
            if not self.settings_btn.winfo_ismapped():
                # Re-pack both elements in correct order to maintain layout
                self.sync_status_label.pack_forget()
                self.settings_btn.pack(side="right", padx=(0, 20))
                self.sync_status_label.pack(side="right", padx=(0, 20))
            self.settings_btn.configure(
                text="✕",
                border_width=2,
                fg_color="transparent",
                text_color="#dc3545",
                border_color="#dc3545"
            )
            
            # Add hover effects for X mode
            def on_register_x_enter(event):
                self.settings_btn.configure(
                    fg_color="#dc3545",
                    text_color="#212121"
                )
                    
            def on_register_x_leave(event):
                self.settings_btn.configure(
                    fg_color="transparent",
                    text_color="#dc3545"
                )
            
            # Remove old bindings and add new ones
            self.settings_btn.unbind("<Enter>")
            self.settings_btn.unbind("<Leave>")
            self.settings_btn.bind("<Enter>", on_register_x_enter)
            self.settings_btn.bind("<Leave>", on_register_x_leave)
        elif self.settings_visible:
            # Ensure button is visible and update appearance for settings mode
            if not self.settings_btn.winfo_ismapped():
                # Re-pack both elements in correct order to maintain layout
                self.sync_status_label.pack_forget()
                self.settings_btn.pack(side="right", padx=(0, 20))
                self.sync_status_label.pack(side="right", padx=(0, 20))
            self.settings_btn.configure(
                text="✕",
                border_width=2,
                fg_color="transparent",
                text_color="#dc3545",
                border_color="#dc3545"
            )
            
            # Add hover effects for X mode
            def on_settings_x_enter(event):
                if self.settings_visible:  # Only apply hover in X mode
                    self.settings_btn.configure(
                        fg_color="#dc3545",
                        text_color="#212121"
                    )
                    
            def on_settings_x_leave(event):
                if self.settings_visible:  # Only apply hover in X mode
                    self.settings_btn.configure(
                        fg_color="transparent",
                        text_color="#dc3545"
                    )
            
            # Remove old bindings and add new ones
            self.settings_btn.unbind("<Enter>")
            self.settings_btn.unbind("<Leave>")
            self.settings_btn.bind("<Enter>", on_settings_x_enter)
            self.settings_btn.bind("<Leave>", on_settings_x_leave)
        else:
            # Ensure button is visible and update appearance for normal mode
            if not self.settings_btn.winfo_ismapped():
                # Re-pack both elements in correct order to maintain layout
                self.sync_status_label.pack_forget()
                self.settings_btn.pack(side="right", padx=(0, 20))
                self.sync_status_label.pack(side="right", padx=(0, 20))
            self.settings_btn.configure(
                text="☰",
                border_width=2,
                fg_color="transparent",
                text_color="#6c757d",
                border_color="#6c757d"
            )
            
            # Restore hamburger hover bindings
            def on_hamburger_enter(event):
                if not self.settings_visible:
                    self.settings_btn.configure(
                        fg_color="#6c757d",
                        text_color="#ffffff"
                    )
                    
            def on_hamburger_leave(event):
                if not self.settings_visible:
                    self.settings_btn.configure(
                        fg_color="transparent",
                        text_color="#6c757d"
                    )
            
            self.settings_btn.bind("<Enter>", on_hamburger_enter)
            self.settings_btn.bind("<Leave>", on_hamburger_leave)

    def update_mode_content(self):
        """Update content based on current mode."""
        # Clear current content
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        # Ensure copyright label visibility matches settings mode
        if self.settings_visible:
            self.copyright_label.place(relx=1.0, rely=0.5, anchor="e", x=-20)
        else:
            self.copyright_label.place_forget()

        if self.settings_visible:
            # Hide guest list completely in settings
            if self.guest_list_visible:
                self.list_frame.pack_forget()
                self.guest_list_visible = False
            # Manual check-in button is now in guest list panel
            # Expand content frame to cover most of screen (leave space for status bar)
            self.content_frame.configure(height=600, corner_radius=15)
            self.create_settings_content()
            return
        elif self.is_displaying_tag_info:
            # Hide guest list when displaying tag info
            if self.guest_list_visible:
                self.list_frame.pack_forget()
                self.guest_list_visible = False
            # Manual check-in button is now in guest list panel
            # Expand content frame for tag info display
            self.content_frame.configure(height=400, corner_radius=15)
            self.create_tag_info_content()
            return
        else:
            # Restore compact content frame
            self.content_frame.configure(height=200, corner_radius=15)
            # Show guest list if not visible
            if not self.guest_list_visible:
                self.list_frame.pack(fill="both", expand=True, pady=(10, 0))
                self.guest_list_visible = True

            # Show buttons for all stations (in search bar area)
            if not self.is_rewrite_mode:
                # Manual check-in button positioning (rightmost)
                self.manual_checkin_btn.pack(side="right", padx=(5, 0))
                
                # Station view toggle switch container (to the left of manual check-in)
                self.switch_container.pack(side="right", padx=(10, 0))
                
                # Update button text based on current manual check-in state
                if self.checkin_buttons_visible:
                    self.manual_checkin_btn.configure(
                        text="✕ Cancel Manual Check-in",
                        border_width=2,
                        fg_color="transparent",
                        text_color="#3b82f6",
                        border_color="#3b82f6"
                    )
                else:
                    self.manual_checkin_btn.configure(
                        text="Manual Check-in",
                        border_width=2,
                        fg_color="transparent",
                        text_color="#ff9800",
                        border_color="#ff9800"
                    )
            else:
                # Hide buttons in rewrite mode
                self.switch_container.pack_forget()
                self.manual_checkin_btn.pack_forget()

        if self.is_rewrite_mode:
            self.create_rewrite_content()
        else:
            # All stations including Reception use checkpoint mode
            self.create_checkpoint_content()



    def create_registration_content(self):
        """Create registration mode UI for Reception - always shows UI with background check-in scanning."""
        # Center container
        center_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        center_frame.place(relx=0.5, rely=0.5, anchor="center")

        # Guest name display (above ID entry)
        self.guest_name_label = ctk.CTkLabel(
            center_frame,
            text="",
            font=CTkFont(size=36, weight="bold"),
            text_color="#4CAF50"
        )
        self.guest_name_label.pack(pady=(0, 25))

        # ID entry frame
        entry_frame = ctk.CTkFrame(center_frame, fg_color="transparent")
        entry_frame.pack()

        # ID entry
        self.id_entry = ctk.CTkEntry(
            entry_frame,
            width=200,
            height=50,
            font=CTkFont(size=20),
            placeholder_text="Guest ID"
        )
        self.id_entry.pack(side="left", padx=(0, 10))
        self.id_entry.bind("<Return>", lambda e: self.write_to_band())
        
        # Add trace to update guest name when ID changes
        self.id_entry.bind("<KeyRelease>", self._on_guest_id_change)
        self.id_entry.bind("<FocusOut>", self._on_guest_id_change)

        # Write button
        self.write_btn = ctk.CTkButton(
            entry_frame,
            text="Register Tag",
            command=self.write_to_band,
            width=120,
            height=50,
            font=self.fonts['button'],
            corner_radius=8,
            border_width=2,
            fg_color="transparent",
            text_color="#4CAF50",
            border_color="#4CAF50",
            hover=False  # Disable built-in hover
        )
        
        # Add hover effects for Write Tag button
        def on_write_enter(event):
            self.write_btn.configure(fg_color="#4CAF50", text_color="#212121")
        def on_write_leave(event):
            self.write_btn.configure(fg_color="transparent", text_color="#4CAF50")
        
        self.write_btn.bind("<Enter>", on_write_enter)
        self.write_btn.bind("<Leave>", on_write_leave)
        self.write_btn.pack(side="left")

        # Focus on entry
        self.safe_update_widget('id_entry', lambda w: w.focus())

        # Start checkpoint scanning in background for Reception
        self.start_checkpoint_scanning()

    def start_rewrite_tag_scanning(self):
        """Start background tag scanning for rewrite mode."""
        if self.is_rewrite_mode and not self.is_scanning:
            self.is_scanning = True
            self._rewrite_scan_loop()

    def _rewrite_scan_loop(self):
        """Background scanning loop for rewrite mode."""
        # Check NFC connection first
        if not self._nfc_connected:
            # Retry after delay if not connected
            self.after(1000, self._rewrite_scan_loop)
            return
            
        # Check global NFC lock first
        if self._nfc_operation_lock:
            # Retry after delay if locked
            self.after(500, self._rewrite_scan_loop)
            return
            
        # Also check if user operation is in progress
        if self.operation_in_progress:
            # Retry after delay
            self.after(500, self._rewrite_scan_loop)
            return
            
        if self.is_rewrite_mode and self.is_scanning:
            self.submit_background_task(self._scan_for_rewrite)

    def _scan_for_rewrite(self):
        """Scan for tag in rewrite mode with helpful status messages."""
        # Don't scan if a user operation is in progress
        if self.operation_in_progress:
            self.after(1000, self._rewrite_scan_loop)
            return

        # Don't scan if rewrite check operation is active (countdown in progress)
        if hasattr(self, '_rewrite_check_operation_active') and self._rewrite_check_operation_active:
            self.after(1000, self._rewrite_scan_loop)
            return

        # Mark as background operation
        self._active_operations += 1

        # Check global NFC lock before reading (race condition protection)
        if self._nfc_operation_lock or not self.is_scanning:
            self.logger.debug("Rewrite scan aborted - NFC operation lock active before tag read")
            self._active_operations -= 1
            return

        tag = self.nfc_service.read_tag(timeout=3)

        if not tag:
            self._active_operations -= 1
            self.after(100, self._rewrite_scan_loop)
            return
        
        # CRITICAL: Check NFC lock AGAIN after tag read to prevent race conditions
        if self._nfc_operation_lock or not self.is_scanning:
            self.logger.debug("Rewrite scan aborted - NFC operation started during tag read")
            self._active_operations -= 1
            return

        # Log successful tag detection
        self.logger.info(f"Tag detected for rewrite: {tag.uid}")
        
        # Cancel any countdown timer since tag was detected
        if self._rewrite_countdown_timer:
            self.after_cancel(self._rewrite_countdown_timer)
            self._rewrite_countdown_timer = None
        self._rewrite_check_operation_active = False
        self._hide_cancel_register_button()
        
        # Tag detected - check if guest ID field is filled
        guest_id = self.rewrite_id_entry.get().strip() if hasattr(self, 'rewrite_id_entry') else ""

        if not guest_id:
            # ID field is empty
            self._active_operations -= 1
            self.after(0, self.update_status, "Enter Guest ID first", "error")
            self.after(3000, lambda: self.update_status("", "normal"))
        else:
            # ID field has value
            self._active_operations -= 1
            self.after(0, self.update_status, "Press Rewrite Tag Button to begin", "info")
            self.after(3000, lambda: self.update_status("", "normal"))

        # Continue scanning after delay
        self.after(3500, self._rewrite_scan_loop)

    def start_registration_tag_scanning(self):
        """Start background tag scanning for registration mode."""
        # Only start if we've completed initial load and user hasn't manually interacted yet
        if (self.is_registration_mode and not self.is_checkpoint_mode and not self.is_scanning and
            hasattr(self, '_initial_load_complete')):
            self.is_scanning = True
            self.logger.debug("Starting registration scanning")
            self._registration_scan_loop()

    def _registration_scan_loop(self):
        """Background scanning loop for registration mode."""
        # Check NFC connection first
        if not self._nfc_connected:
            # Retry after delay if not connected
            self.after(1000, self._registration_scan_loop)
            return
            
        # Check global NFC lock first
        if self._nfc_operation_lock:
            # Retry after delay if locked
            self.after(500, self._registration_scan_loop)
            return
            
        if self.is_registration_mode and not self.is_checkpoint_mode and self.is_scanning:
            self.submit_background_task(self._scan_for_registration)

    def _scan_for_registration(self):
        """Scan for tag info in registration mode."""
        # Don't scan if a user operation is in progress (but allow background scanning to be interrupted)
        if self.operation_in_progress and not hasattr(self, '_allow_background_interrupt'):
            self.after(1000, self._registration_scan_loop)
            return

        # Mark as background operation (can be interrupted)
        self._active_operations += 1

        # Check global NFC lock before reading (race condition protection)
        if self._nfc_operation_lock or not self.is_scanning:
            self.logger.debug("Registration scan aborted - NFC operation lock active before tag read")
            self._active_operations -= 1
            return

        tag = self.nfc_service.read_tag(timeout=3)

        if not tag:
            self._active_operations -= 1
            self.after(100, self._registration_scan_loop)
            return
        
        # CRITICAL: Check NFC lock AGAIN after tag read to prevent race conditions
        if self._nfc_operation_lock or not self.is_scanning:
            self.logger.debug("Registration scan aborted - NFC operation started during tag read")
            self._active_operations -= 1
            return

        # Log successful tag detection
        self.logger.info(f"Tag detected: {tag.uid}")
        
        # Check if tag is registered
        if tag.uid not in self.tag_manager.tag_registry:
            self._active_operations -= 1
            self.after(0, self.update_status, "Unregistered tag - ready for new registration", "info")
            self.after(2000, self._restart_registration_scanning)
            return

        # Tag is registered - check for duplicates
        original_id = self.tag_manager.tag_registry[tag.uid]

        # Get fresh data from Google Sheets with error handling
        try:
            guest = self.sheets_service.find_guest_by_id(original_id)
        except Exception as e:
            # Network/connection error - don't show "missing guest" message
            self._active_operations -= 1
            # Network error - status already shown in sync label
            self.after(3000, self._restart_registration_scanning)
            return

        if guest:
            # Check for duplicate check-ins at current station
            station_lower = self.current_station.lower()

            # Get all check-in data (both local and Google Sheets)
            local_check_ins = self.tag_manager.get_all_local_check_ins()
            guest_local_data = local_check_ins.get(original_id, {})

            # Check local data first
            local_time = guest_local_data.get(station_lower)

            # Check Google Sheets data
            sheets_time = guest.get_check_in_time(station_lower)

            # Determine check-in status (Google Sheets takes precedence)
            checkin_time = sheets_time or local_time
            has_checkin = bool(checkin_time)

            self.logger.debug(f"Duplicate check for {original_id} at {station_lower}: Sheets={sheets_time}, Local={local_time}, HasCheckin={has_checkin}")

            if has_checkin:
                status_msg = f"{guest.firstname} {guest.lastname} already checked in at {self.current_station} at {checkin_time}"
                status_type = "warning"
            else:
                status_msg = f"{guest.firstname} {guest.lastname} - Ready for check-in"
                status_type = "success"
        else:
            # Guest not found in Google Sheets - skip showing message, let checkpoint scanning handle it
            self.logger.warning(f"Tag {tag.uid} registered to ID {original_id} but guest not found in Google Sheets")
            self._active_operations -= 1
            self.after(3000, self._restart_registration_scanning)
            return

        self._active_operations -= 1
        self.after(0, self.update_status, status_msg, status_type)
        self.after(3000, self._restart_registration_scanning)

    def _restart_registration_scanning(self):
        """Restart registration scanning after showing tag info."""
        # Only restart if we're still in registration mode, not in checkpoint mode, and not already scanning
        if (self.is_registration_mode and not self.is_checkpoint_mode and
            not self.is_scanning and hasattr(self, '_initial_load_complete')):
            self.logger.debug("Restarting registration scanning")
            self.is_scanning = True
            self._registration_scan_loop()

    def create_rewrite_content(self):
        """Create rewrite mode UI (similar to registration)."""
        # Center container
        center_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        center_frame.place(relx=0.5, rely=0.5, anchor="center")

        # Instructions
        instruction_label = ctk.CTkLabel(
            center_frame,
            text="Enter Guest ID:",
            font=self.fonts['heading']
        )
        instruction_label.pack(pady=(0, 20))

        # ID entry frame
        entry_frame = ctk.CTkFrame(center_frame, fg_color="transparent")
        entry_frame.pack()

        # ID entry
        self.rewrite_id_entry = ctk.CTkEntry(
            entry_frame,
            width=200,
            height=50,
            font=CTkFont(size=20),
            placeholder_text="Guest ID"
        )
        self.rewrite_id_entry.pack(side="left", padx=(0, 10))
        self.rewrite_id_entry.bind("<Return>", lambda e: self.rewrite_to_band())

        # Rewrite button
        self.rewrite_btn = ctk.CTkButton(
            entry_frame,
            text="Register Tag",
            command=self.rewrite_to_band,
            width=120,
            height=50,
            font=self.fonts['button'],
            corner_radius=8,
            border_width=2,
            fg_color="transparent",
            text_color="#ff9800",
            border_color="#ff9800",
            hover=False  # Disable built-in hover to prevent blue fill
        )
        
        # Add hover effects for Rewrite Tag button
        def on_rewrite_enter(event):
            self.rewrite_btn.configure(fg_color="#ff9800", text_color="#212121")
        def on_rewrite_leave(event):
            self.rewrite_btn.configure(fg_color="transparent", text_color="#ff9800")
        
        self.rewrite_btn.bind("<Enter>", on_rewrite_enter)
        self.rewrite_btn.bind("<Leave>", on_rewrite_leave)
        self.rewrite_btn.pack(side="left")

        # Cancel button (hidden initially, shown during countdown)
        self.cancel_register_btn = ctk.CTkButton(
            entry_frame,
            text="Cancel",
            command=self.cancel_register_operation,
            width=80,
            height=50,
            corner_radius=8,
            font=self.fonts['button'],
            border_width=2,
            fg_color="transparent",
            text_color="#dc3545",
            border_color="#dc3545"
        )
        
        # Add hover effects for cancel button
        def on_cancel_register_enter(event):
            self.cancel_register_btn.configure(
                fg_color="#dc3545",
                text_color="#212121"
            )
            
        def on_cancel_register_leave(event):
            self.cancel_register_btn.configure(
                fg_color="transparent",
                text_color="#dc3545"
            )
            
        self.cancel_register_btn.bind("<Enter>", on_cancel_register_enter)
        self.cancel_register_btn.bind("<Leave>", on_cancel_register_leave)
        # Hide cancel button initially - will be shown during operation


        # Focus on entry
        self.safe_update_widget('rewrite_id_entry', lambda w: w.focus())

        # Register tag mode should NOT have background scanning - only manual registration

    def create_checkpoint_content(self):
        """Create checkpoint mode UI."""
        # Center container
        center_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        center_frame.place(relx=0.5, rely=0.5, anchor="center")

        # Waiting label - check NFC connection status
        if self._nfc_connected:
            status_text = self.STATUS_WAITING_FOR_CHECKIN
            status_color = "#ffffff"
        else:
            status_text = ""  # Hide message when no NFC reader
            status_color = "#ffffff"
        
        self.checkpoint_status = ctk.CTkLabel(
            center_frame,
            text=status_text,
            font=CTkFont(size=28, weight="bold"),
            text_color=status_color
        )
        self.checkpoint_status.pack()

        # Start continuous scanning
        self.start_checkpoint_scanning()

    def write_to_band(self):
        """Handle write to band action."""
        self.logger.info("User clicked Write Tag button")
        guest_id = self.id_entry.get().strip()

        if not guest_id:
            self.update_status(self.STATUS_PLEASE_ENTER_GUEST_ID, "error")
            return

        try:
            guest_id = int(guest_id)
        except ValueError:
            self.update_status(self.STATUS_INVALID_ID_FORMAT, "error")
            return

        # Mark operation in progress
        self.operation_in_progress = True
        self._active_operations += 1  # Track operation start
        
        # Use NFC lock instead of stopping scanning to prevent conflicts
        self._nfc_operation_lock = True

        # Disable UI during operation
        self.safe_update_widget('write_btn', lambda w: w.configure(state="disabled"))
        self.safe_update_widget('id_entry', lambda w: w.configure(state="disabled"))

        # Show cancel button
        self.write_cancel_btn = ctk.CTkButton(
            self.write_btn.master,
            text="Cancel",
            command=self.cancel_write,
            width=80,
            height=50,
            font=self.fonts['button'],
            corner_radius=8,
            fg_color="#dc3545",
            hover_color="#c82333"
        )
        self.write_cancel_btn.pack(side="left", padx=(10, 0))

        # Start tag detection immediately with countdown display
        self._write_operation_active = True
        self._countdown_write_band(guest_id, 10)

        # Start the actual write operation in background
        self.submit_background_task(self._write_to_band_thread, guest_id)

    def cancel_write(self):
        """Cancel write operation."""
        self._write_operation_active = False
        self._active_operations -= 1  # Operation cancelled
        self.nfc_service.cancel_read()
        self.update_status("Write operation cancelled", "warning")
        self._cleanup_write_ui()

    def _cleanup_write_ui(self):
        """Clean up write operation UI."""
        # Release NFC lock
        self._nfc_operation_lock = False
        
        self.safe_update_widget('write_btn', lambda w: w.configure(state="normal"))
        self.safe_update_widget('id_entry', lambda w: w.configure(state="normal"))
        if hasattr(self, 'write_cancel_btn') and self.write_cancel_btn:
            try:
                if self.write_cancel_btn.winfo_exists():
                    self.write_cancel_btn.destroy()
            except Exception:
                pass
            delattr(self, 'write_cancel_btn')

    def _countdown_write_band(self, guest_id: int, countdown: int):
        """Show countdown for write band operation."""
        if countdown > 0 and self._write_operation_active:
            self.update_status(f"Tap wristband now... {countdown}s", "info")
            self.after(1000, lambda: self._countdown_write_band(guest_id, countdown - 1))
        elif self._write_operation_active:
            # Timeout reached
            self._write_operation_active = False
            self.update_status(self.STATUS_NO_TAG_DETECTED, "error")
            self._write_complete(None)

    def _write_to_band_thread(self, guest_id: int):
        """Thread function for writing to band."""
        try:
            # Verify NFC lock is still active (should be set by calling function)
            if not self._nfc_operation_lock:
                self.logger.warning("Write operation started without NFC lock")
                self._nfc_operation_lock = True

            # First read the tag to check if it's already registered
            tag = self.nfc_service.read_tag(timeout=10)
            if not tag:
                # Check what type of error occurred for better user feedback
                error_type = self.nfc_service.get_last_error_type()
                self._write_operation_active = False
                if error_type == 'timeout':
                    self.after(0, self._write_complete, None, "No tag detected")
                elif error_type in ('connection_failed', 'read_failed'):
                    self.after(0, self._write_complete, None, "Failed to read tag - try again")
                else:
                    self.after(0, self._write_complete, None, "No tag detected")
                return
            
            # Check if tag is already registered to a different guest
            if tag.uid in self.tag_manager.tag_registry:
                existing_guest_id = self.tag_manager.tag_registry[tag.uid]
                if existing_guest_id != guest_id:
                    # Tag is registered to different guest - prevent overwrite
                    try:
                        # Get guest info for error message
                        guest = self.sheets_service.find_guest_by_id(existing_guest_id)
                        existing_guest_name = f"{guest['first_name']} {guest['last_name']}" if guest else f"Guest {existing_guest_id}"
                    except Exception as e:
                        self.logger.error(f"Error getting existing guest info: {e}")
                        existing_guest_name = f"Guest {existing_guest_id}"
                    
                    # Create error result
                    error_result = {
                        'error': 'duplicate',
                        'existing_guest': existing_guest_name,
                        'existing_id': existing_guest_id
                    }
                    
                    self._write_operation_active = False
                    self.after(0, self._write_complete, error_result)
                    return

            # Tag is not registered or registered to same guest - use existing registration method
            result = self.tag_manager.register_tag_to_guest_with_existing_tag(guest_id, tag)

            # Always stop countdown when thread completes
            self._write_operation_active = False

            # Update UI in main thread
            self.after(0, self._write_complete, result)

        except Exception as e:
            # Stop countdown on error
            self._write_operation_active = False
            self.logger.error(f"Write operation error: {e}")
            self.after(0, self._write_complete, None)

    def _write_complete(self, result: Optional[Dict], error_message: str = None):
        """Handle write completion."""
        # Mark operation complete
        self.operation_in_progress = False
        self._active_operations -= 1  # Operation finished

        # Clean up UI
        self._cleanup_write_ui()

        if result:
            # Check if it's a duplicate error
            if isinstance(result, dict) and result.get('error') == 'duplicate':
                # Tag already registered to different guest
                existing_guest = result.get('existing_guest', 'Unknown Guest')
                error_msg = self.STATUS_TAG_ALREADY_REGISTERED.format(guest_name=existing_guest)
                self.update_status(error_msg, "error")
            else:
                # Successful registration
                self.update_status(f"✓ Registered to {result['guest_name']}", "success")
                self.safe_update_widget(
                    'guest_name_label',
                    lambda w, text: w.configure(text=text),
                    result['guest_name']
                )

                # Clear form after delay
                self.after(2000, self.clear_registration_form)

                # Refresh guest list after delay to ensure queue is updated and status is visible
                self.after(2500, lambda: self.refresh_guest_data(user_initiated=False))
        else:
            # Use custom error message if provided, otherwise use default
            message = error_message if error_message else self.STATUS_NO_TAG_DETECTED
            self.update_status(message, "error")

        self.id_entry.focus()
        
        # Checkpoint scanning will resume automatically when NFC lock is released

    def clear_registration_form(self):
        """Clear the registration form."""
        self.safe_update_widget('id_entry', lambda w: w.delete(0, 'end'))
        self.safe_update_widget('guest_name_label', lambda w: w.configure(text=""))
        # Show appropriate status based on mode
        if self.is_rewrite_mode:
            pass  # No status message needed - "Check-in Paused" shown in stations frame
        elif not self.settings_visible:
            self._update_status_with_correct_type()

    def _on_guest_id_change(self, event=None):
        """Update guest name display when Guest ID changes."""
        try:
            guest_id_text = self.id_entry.get().strip()
            
            # Clear name if ID is empty
            if not guest_id_text:
                self.safe_update_widget('guest_name_label', lambda w: w.configure(text=""))
                return
            
            # Validate ID format
            try:
                guest_id = int(guest_id_text)
            except ValueError:
                # Invalid format - clear name
                self.safe_update_widget('guest_name_label', lambda w: w.configure(text=""))
                return
            
            # Look up guest in cached data (much faster!)
            guest = None
            if hasattr(self, 'guests_data'):
                for g in self.guests_data:
                    if g.original_id == guest_id:
                        guest = g
                        break
            
            if guest:
                guest_name = guest.full_name
                self.safe_update_widget(
                    'guest_name_label',
                    lambda w, text: w.configure(text=text, text_color="#4CAF50"),
                    guest_name
                )
            else:
                # Guest not found - show "Guest not found" message
                self.safe_update_widget(
                    'guest_name_label',
                    lambda w: w.configure(text="Guest not found", text_color="#ff6b6b")
                )
                
        except Exception as e:
            self.logger.debug(f"Error updating guest name: {e}")
            # On error, just clear the label
            self.safe_update_widget('guest_name_label', lambda w: w.configure(text=""))

    # toggle_reception_mode method removed - Reception now always has checkpoint mode active

    def start_checkpoint_scanning(self):
        """Start continuous scanning for checkpoint mode."""
        # Allow checkpoint scanning at Reception if in checkpoint mode
        if (not self.is_registration_mode or self.is_checkpoint_mode) and not self.is_scanning:
            self.is_scanning = True
            self.logger.debug(f"Starting checkpoint scanning - Registration mode: {self.is_registration_mode}, Checkpoint mode: {self.is_checkpoint_mode}")
            self._checkpoint_scan_loop()
        elif self.is_scanning:
            self.logger.debug("Checkpoint scanning already active, skipping start")

    def _checkpoint_scan_loop(self):
        """Continuous scanning loop for checkpoint mode."""
        # Background scanning rules:
        # 1. Always scan in checkpoint mode (all stations including Reception)
        # 2. Allow scanning during tag info display if in check-in mode
        # 3. NEVER scan if global NFC operation lock is active
        # 4. NEVER scan if NFC reader is not connected

        # Check NFC connection first
        if not self._nfc_connected:
            # Retry after delay if not connected
            self.after(1000, self._checkpoint_scan_loop)
            return

        # Check global NFC lock first
        if self._nfc_operation_lock:
            # Retry after delay if locked
            self.after(500, self._checkpoint_scan_loop)
            return

        # Checkpoint scanning allowed when not in registration-only mode
        in_checkin_mode = (not self.is_registration_mode or self.is_checkpoint_mode)
        allow_during_tag_info = self.is_displaying_tag_info and in_checkin_mode

        should_scan = (in_checkin_mode and self.is_scanning) or allow_during_tag_info

        if should_scan and not self._scanning_thread_active:
            # Start scan in thread
            self._scanning_thread_active = True
            self.submit_background_task(self._scan_for_checkin)
        
        # Always schedule next check to keep scanning alive (reduced frequency for better lock responsiveness)
        if self.is_scanning:
            self.after(200, self._checkpoint_scan_loop)

    def _scan_for_checkin(self):
        """Scan for check-in (thread function)."""
        try:
            # FIRST: Check if we should abort before doing anything
            if self._nfc_operation_lock or not self.is_scanning or getattr(self, '_tag_info_operation_in_progress', False):
                self.logger.info(f"Background scan aborted immediately - NFC lock: {self._nfc_operation_lock}, is_scanning: {self.is_scanning}, tag_info_in_progress: {getattr(self, '_tag_info_operation_in_progress', False)}")
                self._scanning_thread_active = False
                return
                
            # Mark as background operation (can be interrupted)
            self._active_operations += 1

            # Check global NFC lock again before reading (race condition protection)
            if self._nfc_operation_lock or not self.is_scanning:
                self.logger.info(f"Background scan aborted - NFC lock: {self._nfc_operation_lock}, is_scanning: {self.is_scanning}")
                self._active_operations -= 1
                self._scanning_thread_active = False
                return

            # Read NFC tag first
            tag = self.nfc_service.read_tag(timeout=5)

            if not tag:
                self._active_operations -= 1
                # Continue scanning after short delay
                self.after(100, self._restart_scanning_after_timeout)
                return
            
            # CRITICAL: Check NFC lock AGAIN after tag read to prevent race conditions
            # This prevents check-ins when Tag Info or other operations started during the read
            if self._nfc_operation_lock or not self.is_scanning:
                self.logger.debug("Background scan aborted - NFC operation started during tag read")
                self._active_operations -= 1
                self._scanning_thread_active = False
                return
            
            # Check tag info cooldown to prevent same tag from checking in immediately after tag info
            import time
            if (hasattr(self, '_tag_info_cooldown_until') and 
                time.time() < self._tag_info_cooldown_until and
                hasattr(self, '_last_tag_info_tag') and 
                tag.uid == self._last_tag_info_tag):
                self.logger.info(f"Background scan ignored - tag {tag.uid} in cooldown after tag info")
                self._active_operations -= 1
                self._scanning_thread_active = False
                # Continue scanning after short delay
                self.after(500, self._restart_scanning_after_timeout)
                return

            # Log successful tag detection
            self.logger.info(f"Tag detected for check-in: {tag.uid}")
            
            # Check if tag is registered
            if tag.uid not in self.tag_manager.tag_registry:
                self._active_operations -= 1
                # Only show unregistered tag error in pure checkpoint mode (not registration mode)
                if not self.is_registration_mode:
                    self.after(0, self.update_status, "Unregistered tag", "error")
                    # Continue scanning after showing error
                    self.after(2000, self._restart_scanning_after_error)
                else:
                    # In registration mode, let registration scanning handle unregistered tags
                    self.after(100, self._restart_scanning_after_timeout)
                return

            original_id = self.tag_manager.tag_registry[tag.uid]

            # Get guest info and check for duplicates with error handling
            try:
                guest = self.sheets_service.find_guest_by_id(original_id)
            except Exception as e:
                # Network/connection error - don't show "missing guest" message
                self._active_operations -= 1
                # Network error - status already shown in sync label
                self.after(2000, self._restart_scanning_after_error)
                return

            if not guest:
                # Guest not found in Google Sheets - silently skip, registration scanning will handle the message
                self._active_operations -= 1
                # Continue scanning after showing error
                self.after(2000, self._restart_scanning_after_error)
                return

            if guest:
                # Set operation_in_progress early to prevent station transitions during processing
                self.after(0, lambda: setattr(self, 'operation_in_progress', True))
                
                try:
                    # Check both Google Sheets and local queue with error handling (consistent lowercase)
                    sheets_checkin = guest.is_checked_in_at(self.current_station.lower())
                    local_checkin = self.tag_manager.check_in_queue.has_check_in(original_id, self.current_station.lower())

                    if sheets_checkin or local_checkin:
                        self._active_operations -= 1
                        # Release operation lock since we're not proceeding with check-in
                        self.after(0, lambda: setattr(self, 'operation_in_progress', False))
                        # Get check-in time for consistent messaging like registration mode
                        local_check_ins = self.tag_manager.get_all_local_check_ins()
                        guest_local_data = local_check_ins.get(original_id, {})
                        local_time = guest_local_data.get(self.current_station.lower())
                        sheets_time = guest.get_check_in_time(self.current_station.lower())
                        checkin_time = sheets_time or local_time

                        if checkin_time:
                            status_msg = f"{guest.firstname} {guest.lastname} already checked in at {self.current_station} at {checkin_time}"
                        else:
                            status_msg = f"{guest.firstname} {guest.lastname} already checked in at {self.current_station}"

                        self.after(0, self.update_status, status_msg, "warning")
                        # Continue scanning after showing duplicate warning
                        self.after(2000, self._restart_scanning_after_duplicate)
                        return
                except Exception as e:
                    self.logger.error(f"Error checking duplicate status: {e}")
                    # Continue with check-in if duplicate check fails
                    # operation_in_progress remains True for normal check-in processing

            # Process normal check-in (operation_in_progress already set)
            result = self.tag_manager.process_checkpoint_scan_with_tag(tag, self.current_station)
            self._active_operations -= 1

            # If result is None (duplicate), it's already been handled
            if result is None:
                # Release operation lock since we're not proceeding to _checkin_complete
                self.after(0, lambda: setattr(self, 'operation_in_progress', False))
                # Continue scanning after showing duplicate
                self.after(2000, self._restart_scanning_after_duplicate)
                return

            # Update UI in main thread - _checkin_complete will manage operation_in_progress from here
            self.after(0, self._checkin_complete, result)
            
        finally:
            # Always clear the thread flag when done
            self._scanning_thread_active = False

    def _restart_scanning_after_duplicate(self):
        """Restart scanning after duplicate warning."""
        # Check if we should restart scanning (including during tag info)
        # Checkpoint scanning allowed when not in registration-only mode
        in_checkin_mode = (not self.is_registration_mode or self.is_checkpoint_mode)
        allow_during_tag_info = self.is_displaying_tag_info and in_checkin_mode

        should_scan = (in_checkin_mode and self.is_scanning) or allow_during_tag_info
        if should_scan:
            self._checkpoint_scan_loop()

    def _restart_scanning_after_timeout(self):
        """Restart scanning after timeout (no tag detected)."""
        # Check if we should be scanning
        # Checkpoint scanning allowed when not in registration-only mode
        in_checkin_mode = (not self.is_registration_mode or self.is_checkpoint_mode)
        allow_during_tag_info = self.is_displaying_tag_info and in_checkin_mode

        should_scan = in_checkin_mode or allow_during_tag_info
        if should_scan:
            self.logger.debug("Restarting scanning after timeout")
            self._checkpoint_scan_loop()

    def _restart_scanning_after_error(self):
        """Restart scanning after error (unregistered tag)."""
        # Check if we should be scanning
        # Checkpoint scanning allowed when not in registration-only mode
        in_checkin_mode = (not self.is_registration_mode or self.is_checkpoint_mode)
        allow_during_tag_info = self.is_displaying_tag_info and in_checkin_mode

        should_scan = in_checkin_mode or allow_during_tag_info
        if should_scan:
            self.logger.debug("Restarting scanning after error")
            self._checkpoint_scan_loop()

    def safe_update_widget(self, widget_attr: str, update_func, *args, **kwargs):
        """Safely update any widget with existence check.
        
        Args:
            widget_attr: Name of widget attribute
            update_func: Function to call for update (receives widget as first arg)
            *args, **kwargs: Additional arguments for update function
        """
        try:
            widget = getattr(self, widget_attr, None)
            if widget and hasattr(widget, 'winfo_exists') and widget.winfo_exists():
                update_func(widget, *args, **kwargs)
        except Exception as e:
            self.logger.debug(f"Widget {widget_attr} update failed: {e}")
    
    def _safe_configure_checkpoint_status(self):
        """Safely configure checkpoint status widget if it exists."""
        if self._nfc_connected:
            status_text = self.STATUS_WAITING_FOR_CHECKIN
        else:
            status_text = ""  # Hide message when no NFC reader
        
        self.safe_update_widget(
            'checkpoint_status',
            lambda w: w.configure(text=status_text, text_color="#ffffff")
        )

    def _checkin_complete(self, result: Optional[Dict]):
        """Handle check-in completion."""
        # operation_in_progress is already set by the scanning thread
        # Just track the additional UI operation
        self._active_operations += 1
        
        if result:
            self.logger.info(f"Check-in successful: {result['guest_name']} at {self.current_station}")
            self.safe_update_widget(
                'checkpoint_status',
                lambda w, text, tc: w.configure(text=text, text_color=tc),
                f"✓ {result['guest_name']} checked in at {result['timestamp']}",
                "#4CAF50"
            )

            # Delay refresh to ensure status is visible and sync has time to complete
            self.after(3000, lambda: self._checkin_processing_complete(True))

            # Reset after delay with safety check
            self.after(3000, self._safe_configure_checkpoint_status)
        else:
            # No result - immediately complete the operation
            self._checkin_processing_complete(False)
            
    def _checkin_processing_complete(self, refresh_needed: bool):
        """Complete check-in processing and release operation lock."""
        # Release operation lock
        self.operation_in_progress = False
        self._active_operations -= 1
        
        if refresh_needed:
            self.refresh_guest_data(False)
            
        # Continue scanning after processing is complete
        in_checkin_mode = not self.is_registration_mode or self.is_checkpoint_mode
        allow_during_tag_info = self.is_displaying_tag_info and (self.is_checkpoint_mode or not self.is_registration_mode)

        should_continue = (self.is_scanning and in_checkin_mode) or allow_during_tag_info
        if should_continue:
            self.after(100, self._checkpoint_scan_loop)

    def erase_tag_settings(self):
        """Erase tag functionality from settings panel with two-step confirmation."""
        self._restart_settings_timer()  # Restart timer on button interaction
        self.logger.info("User clicked Erase Tag button")
        if not self.erase_confirmation_state:
            # First click - show confirmation
            self.erase_confirmation_state = True
            self.settings_erase_btn.configure(
                text="Are you sure?",
                fg_color="#ff4444",
                hover_color="#dd3333"
            )
            # Auto-reset after 3 seconds if no second click
            self.after(3000, self._reset_erase_confirmation)
            return

        # Second click - proceed with erase
        self._reset_erase_confirmation()

        # Check NFC connection first
        if not self._nfc_connected:
            self.update_status(self.STATUS_NFC_NOT_CONNECTED, "error")
            return
            
        # Check if another NFC operation is already in progress
        if self._nfc_operation_lock:
            self.update_status("Another NFC operation is in progress...", "warning")
            return

        # Stop ALL background scanning and cancel any ongoing NFC operations
        self.is_scanning = False
        try:
            self.nfc_service.cancel_read()
        except Exception as e:
            self.logger.warning(f"Error cancelling NFC read before erase: {e}")

        # Set global NFC lock before marking operation in progress
        self._nfc_operation_lock = True
        
        # Mark operation in progress to block other operations
        self.operation_in_progress = True
        self._erase_cancelled = False  # Track cancellation state

        # Disable button during operation
        self.safe_update_widget('settings_erase_btn', lambda w: w.configure(state="disabled"))

        # Create cancel button underneath
        self.erase_cancel_btn = ctk.CTkButton(
            self.settings_erase_btn.master,
            text="Cancel",
            command=self.cancel_erase_settings,
            width=80,
            height=50,
            font=self.fonts['button'],
            corner_radius=8,
            fg_color="#dc3545",
            hover_color="#c82333"
        )
        self.erase_cancel_btn.pack(side="left", padx=(10, 0))

        # Start countdown and operation
        self._erase_operation_active = True
        self._countdown_erase_settings(10)

        self.submit_background_task(self._erase_tag_thread_settings)

    def _reset_erase_confirmation(self):
        """Reset erase button to normal state."""
        if self.erase_confirmation_state:
            self.erase_confirmation_state = False
            self.safe_update_widget(
                'settings_erase_btn',
                lambda w: w.configure(
                    text="Erase Tag",
                    border_width=2,
                    fg_color="transparent",
                    text_color="#dc3545",
                    border_color="#dc3545"
                )
            )

    def cancel_erase_settings(self):
        """Cancel erase operation from settings."""
        self._erase_operation_active = False
        self._erase_cancelled = True  # Mark as cancelled
        self.operation_in_progress = False
        # Release global NFC lock
        self._nfc_operation_lock = False
        self.nfc_service.cancel_read()

        # Set appropriate status based on mode context
        self.update_status_respecting_settings_mode("Erase cancelled", "warning")
        self._cleanup_erase_settings()

        # Restart scanning if appropriate
        self._restart_scanning_after_erase()

    def _restart_scanning_after_erase(self):
        """Restart scanning after erase operation if appropriate."""
        # Restart scanning based on current mode
        if self.current_station == "Reception":
            if self.is_registration_mode and not self.is_checkpoint_mode:
                # Reception now uses checkpoint scanning
                self.start_checkpoint_scanning()
            elif self.is_checkpoint_mode:
                self.start_checkpoint_scanning()
        else:
            # Non-Reception stations always use checkpoint scanning
            self.start_checkpoint_scanning()

    def _cleanup_erase_settings(self):
        """Clean up erase UI in settings."""
        # Reset confirmation state
        self._reset_erase_confirmation()
        self.safe_update_widget('settings_erase_btn', lambda w: w.configure(state="normal"))
        if hasattr(self, 'erase_cancel_btn') and self.erase_cancel_btn:
            try:
                if self.erase_cancel_btn.winfo_exists():
                    self.erase_cancel_btn.destroy()
            except Exception:
                pass
            delattr(self, 'erase_cancel_btn')

    def _countdown_erase_settings(self, countdown: int):
        """Countdown for erase in settings."""
        if countdown > 0 and self._erase_operation_active:
            self.update_status(f"Tap tag to erase... {countdown}s", "info")
            self.after(1000, lambda: self._countdown_erase_settings(countdown - 1))
        elif self._erase_operation_active and not getattr(self, '_erase_cancelled', False):
            # Only show timeout message if not cancelled
            self._erase_operation_active = False
            # Release global NFC lock on timeout
            self._nfc_operation_lock = False
            self.update_status(self.STATUS_NO_TAG_DETECTED, "error")
            self._erase_complete_settings(None)

    def _erase_tag_thread_settings(self):
        """Thread for erase operation in settings."""
        try:
            tag = self.nfc_service.read_tag(timeout=10)

            # Always stop countdown when thread completes
            self._erase_operation_active = False
            # Release global NFC lock when thread completes
            self._nfc_operation_lock = False

            if tag:
                result = self.tag_manager.clear_tag(tag.uid)
                self.after(0, self._erase_complete_settings, result)
            else:
                # No tag detected
                self.after(0, self._erase_complete_settings, None)

        except Exception as e:
            # Stop countdown on error
            self._erase_operation_active = False
            # Release global NFC lock on error
            self._nfc_operation_lock = False
            self.logger.error(f"Erase operation error: {e}")
            self.after(0, self._erase_complete_settings, None)

    def _erase_complete_settings(self, result: Optional[Dict]):
        """Handle erase completion in settings."""
        self.operation_in_progress = False
        self._cleanup_erase_settings()

        # Always show confirmation in status bar for erase operations
        if result:
            self.update_status(f"✓ {result['guest_name']}'s tag was erased", "success")
            self.after(2500, lambda: self.refresh_guest_data(user_initiated=False))
        elif result is None and not getattr(self, '_erase_cancelled', False):
            # Only show "No tag detected" if not cancelled
            self.update_status(self.STATUS_NO_TAG_DETECTED, "error")
        elif not getattr(self, '_erase_cancelled', False):
            self.update_status("Tag was not registered", "warning")

        # Restart scanning if appropriate
        self._restart_scanning_after_erase()

    def tag_info(self):
        """Show tag information functionality."""
        self._restart_settings_timer()  # Restart timer on button interaction
        self.logger.info("User clicked Tag Info button")
        # Check NFC connection first
        if not self._nfc_connected:
            self.update_status(self.STATUS_NFC_NOT_CONNECTED, "error")
            return
            
        # Check if another NFC operation is already in progress
        if self._nfc_operation_lock:
            self.update_status("Another NFC operation is in progress...", "warning")
            return

        # Set global NFC lock immediately to prevent race conditions
        self._nfc_operation_lock = True

        # Immediately stop all background scanning
        self.is_scanning = False
        
        self.logger.info("Tag info button pressed")
        
        # Force stop any active scanning thread
        self._scanning_thread_active = False

        # Add a flag to completely block background check-ins during tag info operation
        self._tag_info_operation_in_progress = True

        # Force cancel any ongoing NFC operations
        try:
            self.nfc_service.cancel_read()
        except Exception as e:
            self.logger.warning(f"Error cancelling NFC read: {e}")

        # Only wait for explicit user operations
        if self.operation_in_progress:
            self.update_status("Waiting for current operation to finish...", "warning")
            # Release lock since we're not proceeding
            self._nfc_operation_lock = False
            self.after(500, self.tag_info)
            return

        # Track if we came from settings
        if self.settings_visible:
            self._came_from_settings = True
        
        # Mark operation in progress
        self.operation_in_progress = True
        self._active_operations += 1

        # Disable button during operation
        self.safe_update_widget('tag_info_btn', lambda w: w.configure(state="disabled"))

        # Create cancel button
        self.tag_info_cancel_btn = ctk.CTkButton(
            self.tag_info_btn.master,
            text="Cancel",
            command=self.cancel_tag_info,
            width=80,
            height=50,
            font=self.fonts['button'],
            corner_radius=8,
            fg_color="#dc3545",
            hover_color="#c82333"
        )
        self.tag_info_cancel_btn.pack(side="left", padx=(10, 0))

        # Start countdown and operation
        self._tag_info_operation_active = True
        self._countdown_tag_info(10)

        self.submit_background_task(self._tag_info_thread)

    def cancel_tag_info(self):
        """Cancel tag info operation."""
        self._tag_info_operation_active = False
        self._tag_info_operation_in_progress = False  # Clear the blocking flag
        self.operation_in_progress = False
        self._active_operations -= 1
        
        # Release global NFC lock
        self._nfc_operation_lock = False

        # Cancel NFC read safely
        try:
            self.nfc_service.cancel_read()
        except Exception as e:
            self.logger.warning(f"Error cancelling NFC read: {e}")

        # Set appropriate status based on mode context
        self.update_status_respecting_settings_mode("Tag info cancelled", "warning")
        self._cleanup_tag_info()

    def _cleanup_tag_info(self):
        """Clean up tag info UI."""
        self.safe_update_widget('tag_info_btn', lambda w: w.configure(state="normal"))
        if hasattr(self, 'tag_info_cancel_btn') and self.tag_info_cancel_btn:
            try:
                if self.tag_info_cancel_btn.winfo_exists():
                    self.tag_info_cancel_btn.destroy()
            except Exception:
                pass
            delattr(self, 'tag_info_cancel_btn')

    def _countdown_tag_info(self, countdown: int):
        """Countdown for tag info."""
        if countdown > 0 and self._tag_info_operation_active:
            self.update_status(f"Tap tag for info... {countdown}s", "info")
            self.after(1000, lambda: self._countdown_tag_info(countdown - 1))
        elif self._tag_info_operation_active:
            # Timeout reached - stop operation and show timeout message
            self._tag_info_operation_active = False
            self.operation_in_progress = False
            self._active_operations -= 1
            # Release global NFC lock
            self._nfc_operation_lock = False
            self.update_status(self.STATUS_NO_TAG_DETECTED, "error")
            self._cleanup_tag_info()

    def _tag_info_thread(self):
        """Thread for tag info operation."""
        try:
            tag = self.nfc_service.read_tag(timeout=10)

            # Only proceed if operation is still active (not cancelled or timed out)
            if not self._tag_info_operation_active:
                return

            # Stop countdown and mark operation complete
            self._tag_info_operation_active = False
            self.operation_in_progress = False
            self._active_operations -= 1
            # Release global NFC lock
            self._nfc_operation_lock = False

            if tag:
                self.logger.info(f"Tag detected for info: {tag.uid}")
                # Measure performance from tag detection to info retrieval
                import time
                start_time = time.time()
                # Pass in-memory guest data for instant lookup (no API call needed!)
                info = self.tag_manager.get_tag_info(tag.uid, self.guests_data)
                retrieval_time = time.time() - start_time
                # Log differently based on whether it was from memory or API
                if retrieval_time < 0.1:  # Likely from memory (instant)
                    self.logger.info(f"Tag info retrieved from memory in {retrieval_time*1000:.1f}ms")
                else:
                    self.logger.info(f"Tag info retrieval took {retrieval_time:.2f}s (API fallback)")
                self.after(0, self._tag_info_complete, info)
            else:
                # Check what type of error occurred
                error_type = self.nfc_service.get_last_error_type()
                if error_type == 'timeout':
                    self.after(0, self.update_status, "No tag detected", "error")
                elif error_type == 'connection_failed':
                    self.after(0, self.update_status, "Failed to read tag - try again", "error")
                elif error_type == 'read_failed':
                    self.after(0, self.update_status, "Failed to read tag - try again", "error")
                else:
                    # Fallback message
                    self.after(0, self.update_status, "No tag detected", "error")
                self.after(0, self._cleanup_tag_info)

        except Exception as e:
            self.logger.error(f"Error in tag info thread: {e}")
            if self._tag_info_operation_active:
                self._tag_info_operation_active = False
                self.operation_in_progress = False
                self._active_operations -= 1
                # Release global NFC lock on error
                self._nfc_operation_lock = False
                self.after(0, self.update_status, "Tag read error", "error")
                self.after(0, self._cleanup_tag_info)

    def _tag_info_complete(self, tag_info: Optional[Dict]):
        """Display tag information inline."""
        import time
        start_time = time.time()
        # Add a short cooldown to prevent the same tag from triggering check-in immediately
        self._last_tag_info_tag = tag_info.get('tag_uid') if tag_info else None
        self._tag_info_cooldown_until = time.time() + 2.0  # 2 second cooldown
        
        # Clear the tag info operation flag to allow background scanning during display
        self._tag_info_operation_in_progress = False
        self._cleanup_tag_info()

        if tag_info:
            # Guest data is already available in tag_info from get_tag_info()
            # No need to make another API call - this eliminates duplicate Google Sheets access
            try:
                # Create a minimal guest object from the available data
                from src.models.guest_record import GuestRecord
                guest_name_parts = tag_info['guest_name'].split(' ', 1)
                firstname = guest_name_parts[0] if guest_name_parts else ""
                lastname = guest_name_parts[1] if len(guest_name_parts) > 1 else ""
                
                # Create guest record with the data we already have
                guest = GuestRecord(tag_info['original_id'], firstname, lastname)
                guest.check_ins = tag_info['check_ins']
            except Exception as e:
                self.logger.error(f"Error creating guest record from tag info: {e}")
                return

            if guest:
                # Clear settings mode and switch to inline display mode
                self.settings_visible = False
                self._cancel_settings_timer()
                # Clear search field when closing settings
                self.clear_search()
                self.is_displaying_tag_info = True
                self.tag_info_data = {
                    'guest': guest,
                    'check_ins': tag_info['check_ins']
                }
                # Clear countdown status message
                self.update_status("", "normal")
                self.update_mode_content()
                self.update_settings_button()  # Hide hamburger button when in tag info mode

                # Resume background scanning only if in check-in mode
                if self.is_checkpoint_mode or (not self.is_registration_mode):
                    self.start_checkpoint_scanning()
                # Don't update status - let the countdown show
                
                # Log UI display performance
                ui_time = time.time() - start_time
                self.logger.info(f"Tag info UI display took {ui_time:.2f}s")
            else:
                self.update_status("Guest data not found", "warning")
        else:
            self.update_status("Tag not registered", "warning")

    def _get_stations_cached(self, fast_fail_startup=False) -> List[str]:
        """Get stations with GUI-level caching to minimize API calls."""
        import time
        current_time = time.time()
        cache_duration = 30  # Cache for 30 seconds
        
        # Use cached data if recent
        if (self._gui_cached_stations is not None and 
            current_time - self._station_cache_time < cache_duration):
            return self._gui_cached_stations
        
        # Get stations from service (which has its own caching)
        try:
            if hasattr(self, 'sheets_service') and self.sheets_service:
                stations = self.sheets_service.get_available_stations(fast_fail_startup)
                self._gui_cached_stations = stations
                self._station_cache_time = current_time
                return stations
        except Exception:
            pass
        
        # Fallback to config stations
        fallback = self.config.get('stations', ['Reception', 'Lio', 'Juntos', 'Experimental', 'Unvrs'])
        self._gui_cached_stations = fallback
        self._station_cache_time = current_time
        return fallback

    def _auto_close_settings(self):
        """Auto-close settings after 15 seconds."""
        if self.settings_visible:
            self.settings_visible = False
            self._cancel_settings_timer()
            # Clear search field when closing settings
            self.clear_search()
            # Reset erase confirmation state when leaving settings
            self._reset_erase_confirmation()
            # Clear any stale settings references
            if hasattr(self, '_came_from_settings'):
                delattr(self, '_came_from_settings')
            self.update_settings_button()  # Fix: Update hamburger menu state
            self.update_mode_content()
            # Return to appropriate status
            if self.is_rewrite_mode:
                pass  # No status message needed - "Check-in Paused" shown in stations frame
            else:
                self._update_status_with_correct_type()

    def _cancel_settings_timer(self):
        """Cancel the settings auto-close timer."""
        if self._settings_timer:
            self.after_cancel(self._settings_timer)
            self._settings_timer = None
            
    def _restart_settings_timer(self):
        """Restart the settings auto-close timer after user interaction."""
        if self.settings_visible:
            # Cancel existing timer if any
            if self._settings_timer:
                self.after_cancel(self._settings_timer)
            # Start new timer
            self._settings_timer = self.after(15000, self._auto_close_settings)
            self.logger.debug("Settings timer restarted due to user interaction")

    def _create_themed_toplevel(self, parent=None):
        """Create a CTkToplevel window with correct title bar theme."""
        if parent is None:
            parent = self
        
        # Create the window
        window = ctk.CTkToplevel(parent)
        
        # Apply dark title bar if needed - will be called after deiconify()
        if not self.is_light_mode:
            # Store the window reference so we can apply dark title bar later
            window._needs_dark_title = True
        
        return window
    
    def apply_dark_title_bar_after_show(self, window):
        """Apply dark title bar after window is shown."""
        if hasattr(window, '_needs_dark_title') and window._needs_dark_title:
            self._apply_dark_title_bar(window)
            window._needs_dark_title = False
    
    def _apply_dark_title_bar(self, window):
        """Apply dark title bar to window on Windows."""
        try:
            import platform
            if platform.system() == "Windows":
                import ctypes as ct
                
                def apply_dark_mode():
                    try:
                        # Windows API constants
                        DWMWA_USE_IMMERSIVE_DARK_MODE = 20
                        
                        # Get window handle
                        hwnd = ct.windll.user32.GetParent(window.winfo_id())
                        
                        # Apply dark mode to title bar
                        value = ct.c_int(2)  # 2 = enable dark mode
                        ct.windll.dwmapi.DwmSetWindowAttribute(
                            hwnd, 
                            DWMWA_USE_IMMERSIVE_DARK_MODE,
                            ct.byref(value), 
                            ct.sizeof(value)
                        )
                    except Exception as e:
                        self.logger.debug(f"Dark title bar API call failed: {e}")
                
                # Apply immediately - window is already shown
                window.after(1, apply_dark_mode)
                
        except Exception as e:
            self.logger.debug(f"Could not apply dark title bar: {e}")

    def show_logs(self):
        """Show log viewer dialog."""
        self._restart_settings_timer()  # Restart timer on button interaction
        self.logger.info("User opened log viewer")
        log_window = self._create_themed_toplevel()
        log_window.title("Realtime Logs")
        log_window.transient(self)
        log_window.withdraw()  # Hide window during setup

        # Calculate center position
        width, height = 800, 600
        x = (log_window.winfo_screenwidth() // 2) - (width // 2)
        y = (log_window.winfo_screenheight() // 2) - (height // 2)
        log_window.geometry(f"{width}x{height}+{x}+{y}")
        log_window.deiconify()  # Show window at correct position
        self.apply_dark_title_bar_after_show(log_window)

        # Title
        title_label = ctk.CTkLabel(log_window, text="", font=self.fonts['heading'])
        title_label.pack(pady=5)

        # Log display frame
        log_frame = ctk.CTkFrame(log_window)
        log_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # Scrollable text area
        log_text = ctk.CTkTextbox(
            log_frame,
            font=CTkFont(family="Monaco", size=12),
            wrap="word"
        )
        log_text.pack(fill="both", expand=True, padx=10, pady=10)

        # Load and display logs
        try:
            log_file = Path(self.config['log_file'])
            if log_file.exists():
                with open(log_file, 'r') as f:
                    log_content = f.read()

                # Pretty format the logs
                lines = log_content.split('\n')
                formatted_lines = []

                for line in lines:
                    if not line.strip():
                        continue

                    # Color code by log level
                    if ' - ERROR - ' in line:
                        formatted_lines.append(f"🔴 {line}")
                    elif ' - WARNING - ' in line:
                        formatted_lines.append(f"🟡 {line}")
                    elif ' - INFO - ' in line:
                        formatted_lines.append(f"🔵 {line}")
                    elif ' - DEBUG - ' in line:
                        formatted_lines.append(f"⚪ {line}")
                    else:
                        formatted_lines.append(line)

                # Show latest 200 lines
                recent_lines = formatted_lines[-200:] if len(formatted_lines) > 200 else formatted_lines
                log_text.insert("1.0", "\n".join(recent_lines))

                # Scroll to bottom
                log_text.see("end")
            else:
                log_text.insert("1.0", "No log file found.")

        except Exception as e:
            log_text.insert("1.0", f"Error loading logs: {e}")

        # Close button - modernized
        close_btn = ctk.CTkButton(
            log_window,
            text="✕ Close",
            command=log_window.destroy,
            width=120,
            height=40,
            corner_radius=8,
            font=CTkFont(size=14, weight="bold"),
            border_width=2,
            fg_color="transparent",
            text_color="#3b82f6",
            border_color="#3b82f6"
        )
        
        # Add hover effects for log close button
        def on_log_close_enter(event):
            close_btn.configure(
                fg_color="#3b82f6",
                text_color="#ffffff"
            )
            
        def on_log_close_leave(event):
            close_btn.configure(
                fg_color="transparent",
                text_color="#3b82f6"
            )
            
        close_btn.bind("<Enter>", on_log_close_enter)
        close_btn.bind("<Leave>", on_log_close_leave)
        
        close_btn.pack(pady=(0, 20))
        
        # Set up auto-refresh
        self._setup_log_auto_refresh(log_text, log_window)

    def _setup_log_auto_refresh(self, text_widget, window):
        """Set up auto-refresh for log content."""
        def refresh_logs():
            if not window.winfo_exists():
                return
                
            try:
                # Clear current content
                text_widget.delete("1.0", "end")
                
                # Reload log file
                log_file = Path(self.config['log_file'])
                if log_file.exists():
                    with open(log_file, 'r') as f:
                        log_content = f.read()

                    # Pretty format the logs
                    lines = log_content.split('\n')
                    formatted_lines = []

                    for line in lines:
                        if not line.strip():
                            continue

                        # Color code by log level
                        if ' - ERROR - ' in line:
                            formatted_lines.append(f"🔴 {line}")
                        elif ' - WARNING - ' in line:
                            formatted_lines.append(f"🟡 {line}")
                        elif ' - INFO - ' in line:
                            formatted_lines.append(f"🔵 {line}")
                        elif ' - DEBUG - ' in line:
                            formatted_lines.append(f"⚪ {line}")
                        else:
                            formatted_lines.append(line)

                    # Show latest 100 lines for better performance
                    recent_lines = formatted_lines[-100:] if len(formatted_lines) > 100 else formatted_lines
                    text_widget.insert("1.0", "\n".join(recent_lines))

                    # Scroll to bottom
                    text_widget.see("end")
                else:
                    text_widget.insert("1.0", "No log file found.")
                    
                # Schedule next refresh in 2 seconds
                window.after(2000, refresh_logs)
                    
            except Exception as e:
                # If refresh fails, just continue
                text_widget.insert("end", f"\nRefresh error: {e}")
                window.after(5000, refresh_logs)  # Try again in 5 seconds
        
        # Start the refresh cycle
        window.after(2000, refresh_logs)  # First refresh in 2 seconds

    def enter_developer_mode(self):
        """Show password dialog for developer mode."""
        self._cancel_settings_timer()  # Stop timer - user entering advanced mode
        
        # Reset button appearance manually and remove focus (dialog causes state issues)
        self.dev_mode_btn.configure(
            fg_color="transparent", 
            text_color="#6c757d",
            border_color="#6c757d"
        )
        
        # Force button to lose focus to prevent stuck state
        self.focus_set()  # Move focus to main window
        
        password_window = self._create_themed_toplevel()
        password_window.title("")
        password_window.transient(self)
        password_window.withdraw()  # Hide window during setup
        
        # Reset button state when dialog closes
        def on_password_dialog_close():
            # Check if button still exists before configuring
            try:
                if hasattr(self, 'dev_mode_btn') and self.dev_mode_btn.winfo_exists():
                    self.dev_mode_btn.configure(
                        fg_color="transparent", 
                        text_color="#6c757d",
                        border_color="#6c757d"
                    )
            except:
                pass  # Button was already destroyed
            
            # Safely destroy window
            try:
                if password_window.winfo_exists():
                    password_window.destroy()
            except:
                pass  # Window was already destroyed
            
        password_window.protocol("WM_DELETE_WINDOW", on_password_dialog_close)

        # Calculate center position
        width, height = 300, 300
        x = (password_window.winfo_screenwidth() // 2) - (width // 2)
        y = (password_window.winfo_screenheight() // 2) - (height // 2)
        password_window.geometry(f"{width}x{height}+{x}+{y}")
        password_window.grab_set()
        password_window.deiconify()  # Show window at correct position
        self.apply_dark_title_bar_after_show(password_window)

        # Title
        title_label = ctk.CTkLabel(password_window, text="Enter Password", font=self.fonts['heading'])
        title_label.pack(pady=20)

        # Password entry
        password_entry = ctk.CTkEntry(
            password_window,
            placeholder_text="Password",
            show="*",
            width=200,
            height=40,
            font=self.fonts['body']
        )
        password_entry.pack(pady=10)
        password_entry.focus()

        # Status label
        status_label = ctk.CTkLabel(password_window, text="", font=self.fonts['body'])
        status_label.pack(pady=5)

        def check_password():
            entered_password = password_entry.get()
            correct_password = self.config.get('developer', {}).get('password', '8888')

            if entered_password == correct_password:
                password_window.destroy()
                self.show_developer_mode()
            else:
                status_label.configure(text="Incorrect password", text_color="#f44336")
                password_entry.delete(0, 'end')

        # Enter key binding
        password_entry.bind("<Return>", lambda e: check_password())

        # Buttons
        button_frame = ctk.CTkFrame(password_window, fg_color="transparent")
        button_frame.pack(pady=20)

        login_btn = ctk.CTkButton(
            button_frame,
            text="Enter",
            command=check_password,
            width=80,
            height=35,
            font=self.fonts['button'],
            border_width=2,
            fg_color="transparent",
            text_color="#28a745",
            border_color="#28a745",
            hover=False  # Disable built-in hover
        )
        
        # Add hover effects for Enter button
        def on_enter_btn_enter(event):
            login_btn.configure(
                fg_color="#28a745",
                text_color="#ffffff"
            )
            
        def on_enter_btn_leave(event):
            login_btn.configure(
                fg_color="transparent",
                text_color="#28a745"
            )
            
        login_btn.bind("<Enter>", on_enter_btn_enter)
        login_btn.bind("<Leave>", on_enter_btn_leave)
        login_btn.pack(side="left", padx=5)

        cancel_btn = ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=on_password_dialog_close,
            width=80,
            height=35,
            font=self.fonts['button'],
            border_width=2,
            fg_color="transparent",
            text_color="#6c757d",
            border_color="#6c757d",
            hover=False  # Disable built-in hover
        )
        
        # Add hover effects for Cancel button
        def on_cancel_btn_enter(event):
            cancel_btn.configure(
                fg_color="#6c757d",
                text_color="#ffffff"
            )
            
        def on_cancel_btn_leave(event):
            cancel_btn.configure(
                fg_color="transparent",
                text_color="#6c757d"
            )
            
        cancel_btn.bind("<Enter>", on_cancel_btn_enter)
        cancel_btn.bind("<Leave>", on_cancel_btn_leave)
        cancel_btn.pack(side="left", padx=5)

    def show_developer_mode(self):
        """Show developer mode interface."""
        dev_window = self._create_themed_toplevel()
        dev_window.title("")
        dev_window.resizable(False, False)
        dev_window.transient(self)
        dev_window.withdraw()  # Hide window during setup
        
        # Set up window close protocol to prevent stuck button states
        dev_window.protocol("WM_DELETE_WINDOW", lambda: dev_window.destroy())

        # Calculate center position
        width, height = 300, 280
        x = (dev_window.winfo_screenwidth() // 2) - (width // 2)
        y = (dev_window.winfo_screenheight() // 2) - (height // 2)
        dev_window.geometry(f"{width}x{height}+{x}+{y}")
        dev_window.deiconify()  # Show window at correct position
        self.apply_dark_title_bar_after_show(dev_window)

        # Main frame with padding
        main_frame = ctk.CTkFrame(dev_window)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Container frame for buttons to center them vertically
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(expand=True, fill="both")

        # Google Sheets button
        def open_google_sheets():
            """Open Google Sheets in default browser."""
            webbrowser.open("https://docs.google.com/spreadsheets/d/1x1HvvfYYp-SlhljTP5lebyZLAu21PVNEDTAe8w3SR-A/edit?usp=sharing")

        sheets_btn = ctk.CTkButton(
            button_frame,
            text="Open Google Sheets",
            command=open_google_sheets,
            width=220,
            height=50,
            corner_radius=8,
            font=self.fonts['button'],
            border_width=2,
            fg_color="transparent",
            text_color="#28a745",
            border_color="#28a745"
        )
        
        # Add hover effects for Google Sheets button
        def on_sheets_enter(event):
            sheets_btn.configure(
                fg_color="#28a745",
                text_color="#ffffff"
            )
            
        def on_sheets_leave(event):
            sheets_btn.configure(
                fg_color="transparent",
                text_color="#28a745"
            )
            
        sheets_btn.bind("<Enter>", on_sheets_enter)
        sheets_btn.bind("<Leave>", on_sheets_leave)
        sheets_btn.pack(pady=(20, 10), expand=True)


        # Clear All Data button
        self.clear_all_btn = ctk.CTkButton(
            button_frame,
            text="Clear All Guest Data",
            command=lambda: self.clear_all_data(dev_window),
            width=220,
            height=50,
            corner_radius=8,
            font=self.fonts['button'],
            border_width=2,
            fg_color="transparent",
            text_color="#dc3545",
            border_color="#dc3545"
        )
        
        # Add hover effects for Clear All Data button
        def on_clear_all_enter(event):
            self.clear_all_btn.configure(
                fg_color="#dc3545",
                text_color="#ffffff"
            )
            
        def on_clear_all_leave(event):
            self.clear_all_btn.configure(
                fg_color="transparent",
                text_color="#dc3545"
            )
            
        self.clear_all_btn.bind("<Enter>", on_clear_all_enter)
        self.clear_all_btn.bind("<Leave>", on_clear_all_leave)
        self.clear_all_btn.pack(pady=(0, 10), expand=True)

        # Close button - modernized
        def close_dev_window():
            """Close developer window and reset Advanced button state."""
            # Reset the Advanced button state (same as password dialog Cancel)
            self.dev_mode_btn.configure(
                fg_color="transparent", 
                text_color="#6c757d",
                border_color="#6c757d"
            )
            dev_window.destroy()
            
        close_btn = ctk.CTkButton(
            button_frame,
            text="✕ Close",
            command=close_dev_window,
            width=120,
            height=40,
            corner_radius=8,
            font=CTkFont(size=14, weight="bold"),
            border_width=2,
            fg_color="transparent",
            text_color="#3b82f6",
            border_color="#3b82f6",
            hover=False  # Disable built-in hover
        )
        
        # Add hover effects for dev close button
        def on_dev_close_enter(event):
            close_btn.configure(
                fg_color="#3b82f6",
                text_color="#ffffff"
            )
            
        def on_dev_close_leave(event):
            close_btn.configure(
                fg_color="transparent",
                text_color="#3b82f6"
            )
            
        close_btn.bind("<Enter>", on_dev_close_enter)
        close_btn.bind("<Leave>", on_dev_close_leave)
        
        close_btn.pack(expand=True)
        
        # Make window modal after all content is created
        dev_window.grab_set()

    def clear_all_data(self, dev_window):
        """Clear all guest data with confirmation."""
        # Reset button appearance and remove focus (dialog causes state issues)
        self.clear_all_btn.configure(
            fg_color="transparent",
            text_color="#dc3545",
            border_color="#dc3545"
        )
        
        # Force button to lose focus to prevent stuck state
        dev_window.focus_set()  # Move focus to dev window
        
        # Confirmation dialog
        confirm_window = self._create_themed_toplevel(dev_window)
        confirm_window.title("Confirm Clear All Data")
        confirm_window.geometry("300x300")
        confirm_window.transient(dev_window)
        confirm_window.grab_set()
        
        # Reset button state when confirmation dialog closes
        def on_confirm_dialog_close():
            self.clear_all_btn.configure(
                fg_color="transparent",
                text_color="#dc3545",
                border_color="#dc3545"
            )
            confirm_window.destroy()
            
        confirm_window.protocol("WM_DELETE_WINDOW", on_confirm_dialog_close)

        # Center window
        confirm_window.update_idletasks()
        x = (confirm_window.winfo_screenwidth() // 2) - (confirm_window.winfo_width() // 2)
        y = (confirm_window.winfo_screenheight() // 2) - (confirm_window.winfo_height() // 2)
        confirm_window.geometry(f"+{x}+{y}")

        # Warning
        warning_label = ctk.CTkLabel(
            confirm_window,
            text="🚨 CAUTION 🚨\n\nThis will permanently delete:\n• All local check-in data\n• All Google Sheets check-in data\n• All wristband registrations\n\nThis action CANNOT be undone!",
            font=self.fonts['button'],
            text_color="#dc3545",
            justify="center"
        )
        warning_label.pack(pady=20)

        # Buttons
        button_frame = ctk.CTkFrame(confirm_window, fg_color="transparent")
        button_frame.pack(pady=20)

        def execute_clear():
            confirm_window.destroy()
            dev_window.destroy()
            self._execute_clear_all_data()

        confirm_btn = ctk.CTkButton(
            button_frame,
            text="YES, DELETE ALL",
            command=execute_clear,
            width=120,
            height=40,
            corner_radius=8,
            font=CTkFont(size=12, weight="bold"),
            border_width=2,
            fg_color="transparent",
            text_color="#dc3545",
            border_color="#dc3545"
        )
        
        # Add hover effects for YES DELETE ALL button
        def on_confirm_delete_enter(event):
            confirm_btn.configure(
                fg_color="#dc3545",
                text_color="#ffffff"
            )
            
        def on_confirm_delete_leave(event):
            confirm_btn.configure(
                fg_color="transparent",
                text_color="#dc3545"
            )
            
        confirm_btn.bind("<Enter>", on_confirm_delete_enter)
        confirm_btn.bind("<Leave>", on_confirm_delete_leave)
        
        confirm_btn.pack(side="left", padx=10)

        cancel_btn = ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=on_confirm_dialog_close,
            width=100,
            height=40,
            corner_radius=8,
            font=self.fonts['button'],
            border_width=2,
            fg_color="transparent",
            text_color="#6c757d",
            border_color="#6c757d"
        )
        
        # Add hover effects for Cancel button
        def on_cancel_clear_enter(event):
            cancel_btn.configure(
                fg_color="#6c757d",
                text_color="#ffffff"
            )
            
        def on_cancel_clear_leave(event):
            cancel_btn.configure(
                fg_color="transparent",
                text_color="#6c757d"
            )
            
        cancel_btn.bind("<Enter>", on_cancel_clear_enter)
        cancel_btn.bind("<Leave>", on_cancel_clear_leave)
        
        cancel_btn.pack(side="left", padx=10)

    def _execute_clear_all_data(self):
        """Execute the clear all data operation."""
        self.update_status("Clearing all data...", "warning")

        # Run in thread to avoid blocking UI
        self.submit_background_task(self._clear_all_data_thread)

    def _clear_all_data_thread(self):
        """Thread function to clear all data."""
        try:
            # Clear local data
            self.tag_manager.clear_all_local_data()

            # Clear Google Sheets data
            success = self.tag_manager.clear_all_sheets_data()

            if success:
                self.after(0, self.update_status, "✓ All data cleared successfully", "success")
                # Refresh to show empty list
                self.after(1000, lambda: self.refresh_guest_data(user_initiated=False))
            else:
                self.after(0, self.update_status, "Failed to clear Google Sheets data", "error")

        except Exception as e:
            self.logger.error(f"Error clearing data: {e}")
            self.after(0, self.update_status, f"Error clearing data: {str(e)}", "error")

    def show_bulk_write_mode(self, parent_window):
        """Show bulk write interface inline in main window."""
        self.logger.info("Activating bulk write mode...")
        
        # Close the advanced dialog first
        parent_window.destroy()
        
        # Close settings mode completely
        self.settings_visible = False
        self._cancel_settings_timer()
        # Clear search field when closing settings
        self.clear_search()
        # Reset erase confirmation state when leaving settings
        self._reset_erase_confirmation()
        # Clear any stale settings references
        if hasattr(self, '_came_from_settings'):
            delattr(self, '_came_from_settings')
        
        # Stop all background scanning to prevent NFC conflicts in bulk write mode
        self.is_scanning = False
        try:
            self.nfc_service.cancel_read()
        except Exception as e:
            self.logger.debug(f"Error canceling NFC read during bulk write mode start: {e}")
        
        # Set bulk write mode flag
        self.is_bulk_write_mode = True
        self.logger.info(f"Bulk write mode flag set: {self.is_bulk_write_mode}")
        
        # Update UI for bulk write mode
        self.update_settings_button()
        self.update_station_buttons_visibility()
        
        # Update the main content to show bulk write UI
        self.logger.info("Calling update_mode_content for bulk write...")
        self.update_mode_content()
        
        self.logger.info("Bulk write mode activation complete")

    def _on_bulk_guest_id_change(self, event=None):
        """Handle guest ID change in bulk write mode."""
        if not hasattr(self, 'bulk_id_entry'):
            return
            
        guest_id_text = self.bulk_id_entry.get().strip()
        
        if not guest_id_text:
            self.bulk_guest_name_label.configure(text="")
            return
        
        try:
            guest_id = int(guest_id_text)
            
            # Search through cached guest data
            for guest in self.guests_data:
                if guest.original_id == guest_id:
                    full_name = f"{guest.firstname} {guest.lastname}".strip()
                    self.bulk_guest_name_label.configure(text=full_name)
                    return
            
            # Guest not found
            self.bulk_guest_name_label.configure(text="Guest not found")
            
        except ValueError:
            self.bulk_guest_name_label.configure(text="")

    def bulk_write_to_band(self):
        """Write UUID to wristband in bulk write mode."""
        if not hasattr(self, 'bulk_id_entry'):
            return
        
        # Check NFC connection first - don't show error if no reader
        if not self._nfc_connected:
            return  # Button should be disabled anyway, just silently return
            
        guest_id_text = self.bulk_id_entry.get().strip()
        if not guest_id_text:
            self.update_status("Please enter a Guest ID", "error")
            return
        
        try:
            guest_id = int(guest_id_text)
        except ValueError:
            self.update_status("Invalid Guest ID format", "error")
            return
        
        # Verify guest exists
        guest_found = False
        for guest in self.guests_data:
            if guest.original_id == guest_id:
                guest_found = True
                break
        
        if not guest_found:
            self.update_status("Guest not found", "error")
            return
        
        # Start timeout countdown and operation
        self._bulk_write_operation_active = True
        self._disable_bulk_write_ui()
        self._show_cancel_button()
        self._countdown_bulk_write(10)
        
        # Start bulk write operation in background
        self.submit_background_task(self._bulk_write_thread, guest_id)

    def _countdown_bulk_write(self, countdown: int):
        """Show countdown for bulk write operation."""
        if countdown > 0 and self._bulk_write_operation_active:
            self.update_status(f"Place wristband on reader... {countdown}s", "warning", False)
            self.after(1000, lambda: self._countdown_bulk_write(countdown - 1))
        elif self._bulk_write_operation_active:
            # Timeout reached
            self._bulk_write_operation_active = False
            self.update_status("No tag detected. Try again.", "error")
            self._enable_bulk_write_ui()
            self._hide_cancel_button()

    def _disable_bulk_write_ui(self):
        """Disable bulk write UI elements during operation."""
        self.safe_update_widget('bulk_write_btn', lambda w: w.configure(state="disabled"))
        self.safe_update_widget('bulk_id_entry', lambda w: w.configure(state="disabled"))

    def _enable_bulk_write_ui(self):
        """Re-enable bulk write UI elements."""
        self._bulk_write_operation_active = False
        self.safe_update_widget('bulk_id_entry', lambda w: w.configure(state="normal"))
        # Update button state based on NFC connection
        self.update_bulk_write_button_state()

    def _show_cancel_button(self):
        """Show the cancel button during bulk write operation."""
        if hasattr(self, 'cancel_bulk_write_btn'):
            self.cancel_bulk_write_btn.pack(side="left", padx=(10, 0))

    def _hide_cancel_button(self):
        """Hide the cancel button after bulk write operation."""
        if hasattr(self, 'cancel_bulk_write_btn'):
            self.cancel_bulk_write_btn.pack_forget()

    def cancel_bulk_write_operation(self):
        """Cancel the bulk write operation."""
        if self._bulk_write_operation_active:
            self._bulk_write_operation_active = False
            self.update_status("Bulk write cancelled", "info")
            self._enable_bulk_write_ui()
            self._hide_cancel_button()

    def _bulk_write_thread(self, guest_id):
        """Background thread for bulk write operation."""
        try:
            # Check if operation was cancelled
            if not self._bulk_write_operation_active:
                return
                
            # Read NFC tag to get UUID
            tag = self.nfc_service.read_tag(timeout=10)
            
            # Stop countdown when thread completes (success or failure)
            self.after(0, self._enable_bulk_write_ui)
            self.after(0, self._hide_cancel_button)
            
            if not tag:
                self.after(0, lambda: self.update_status("No tag detected. Try again.", "error"))
                return
            
            tag_uuid = tag.uid
            if not tag_uuid:
                self.after(0, lambda: self.update_status("Could not read tag UUID", "error"))
                return
            
            # Register tag using the same mechanism as normal registration
            self.logger.info(f"Registering tag {tag_uuid} to guest {guest_id} using bulk write mode")
            result = self.tag_manager.register_tag_to_guest_with_existing_tag(guest_id, tag)
            
            if result:
                # Also write UUID to Google Sheets column E (bulk write specific feature)
                self.logger.info(f"Writing UUID {tag_uuid} to Google Sheets column E for guest {guest_id}")
                sheets_success = self.sheets_service.write_wristband_uuid(guest_id, tag_uuid)
                
                if sheets_success:
                    self.logger.info(f"Successfully registered tag {tag_uuid} to guest {guest_id} and wrote to column E")
                    self.after(0, lambda: self.update_status("Tag registered", "success"))
                else:
                    self.logger.warning(f"Tag registered locally but failed to write UUID to Google Sheets column E for guest {guest_id}")
                    self.after(0, lambda: self.update_status("Tag registered (local only)", "warning"))
                    
                # Clear the entry after successful write
                self.after(2000, lambda: self.bulk_id_entry.delete(0, 'end') if hasattr(self, 'bulk_id_entry') else None)
                self.after(2000, lambda: self.bulk_guest_name_label.configure(text="") if hasattr(self, 'bulk_guest_name_label') else None)
            else:
                self.after(0, lambda: self.update_status("Failed to register tag", "error"))
        
        except Exception as e:
            self.logger.error(f"Bulk write error: {e}")
            # Stop countdown on error
            self.after(0, self._enable_bulk_write_ui)
            self.after(0, self._hide_cancel_button)
            
            # Provide more specific error messages
            error_msg = str(e)
            if "timeout" in error_msg.lower():
                display_msg = "Tag read timeout - try again"
            elif "connection" in error_msg.lower():
                display_msg = "NFC connection error - check reader"
            elif "sheets" in error_msg.lower() or "api" in error_msg.lower():
                display_msg = "Google Sheets error - check connection"
            else:
                display_msg = f"Bulk write error: {error_msg}"
            
            self.after(0, lambda: self.update_status(display_msg, "error"))

    def close_bulk_write_mode(self):
        """Close bulk write mode and return to main station."""
        self.is_bulk_write_mode = False
        
        # Update UI to show station buttons and normal hamburger menu
        self.update_settings_button()
        self.update_station_buttons_visibility()
        
        # Update content to show normal station view
        self.update_mode_content()
        
        # Return to checkpoint scanning if NFC is connected
        if self._nfc_connected and not self.is_scanning:
            self.start_checkpoint_scanning()

    def update_station_buttons_visibility(self):
        """Update station buttons visibility based on current mode."""
        if self.is_rewrite_mode:
            # Hide station buttons and show "Check ins paused" text
            if hasattr(self, 'station_buttons_container'):
                self.station_buttons_container.pack_forget()
            
            # Create or update register mode label
            if not hasattr(self, 'register_mode_label'):
                # Find the station frame to add the label
                station_frame = self.station_buttons_container.master
                self.register_mode_label = ctk.CTkLabel(
                    station_frame,
                    text="Check-in Paused",
                    font=CTkFont(size=18, weight="bold"),
                    text_color="#ff9800"
                )
            self.register_mode_label.pack(side="left")
        else:
            # Show station buttons and hide register mode label
            if hasattr(self, 'station_buttons_container'):
                self.station_buttons_container.pack(side="left")
            
            if hasattr(self, 'register_mode_label'):
                self.register_mode_label.pack_forget()

    def rewrite_tag(self):
        """Enter register tag mode."""
        self._restart_settings_timer()  # Restart timer on button interaction
        self.logger.info("User clicked Register Tag button")
        # Check NFC connection first
        if not self._nfc_connected:
            self.update_status(self.STATUS_NFC_NOT_CONNECTED, "error")
            return
            
        # Stop any background scanning to prevent NFC conflicts
        self.is_scanning = False

        self.settings_visible = False
        self._cancel_settings_timer()
        # Clear search field when closing settings
        self.clear_search()
        self.is_rewrite_mode = True
        self.is_registration_mode = False  # Ensure registration mode is off
        self.is_checkpoint_mode = False   # Disable checkpoint mode to prevent background scanning
        self.update_settings_button()
        self.update_station_buttons_visibility()
        
        self.update_mode_content()
        
        # Update table structure for registration mode (same as station toggle)
        self._update_table_structure()
        
        # Refresh table data
        if hasattr(self, 'guests_data') and self.guests_data:
            self._update_guest_table_silent(self.guests_data)
        # Keep status bar clear in rewrite mode - "Check-in Paused" shown in stations frame
        self.update_status("", "normal")


    def on_station_button_click(self, station: str):
        """Handle station button click."""
        # Special case: clicking current station while in settings closes settings
        if station == self.current_station:
            if self.settings_visible:
                self.settings_visible = False
                # Cancel auto-close timer
                self._cancel_settings_timer()
                # Clear search field when closing settings
                self.clear_search()
                self.update_settings_button()
                self.update_mode_content()
                # Clear any stale _came_from_settings flag
                if hasattr(self, '_came_from_settings'):
                    delattr(self, '_came_from_settings')
            return
            
        # Block station changes if operation is in progress
        if self.operation_in_progress:
            self.update_status("Please wait for current operation to complete", "warning")
            return
            
        # Exit rewrite mode if active and cancel any operations
        if self.is_rewrite_mode:
            self.cancel_any_rewrite_operations()
            self.exit_rewrite_mode()

        # Close settings if open
        if self.settings_visible:
            self.settings_visible = False
            # Cancel auto-close timer
            self._cancel_settings_timer()
            # Clear search field when closing settings
            self.clear_search()
            self.update_settings_button()

        # Close manual check-in mode when switching stations
        if self.checkin_buttons_visible:
            self.toggle_manual_checkin()

        # Clear any stale _came_from_settings flag during station transitions
        if hasattr(self, '_came_from_settings'):
            delattr(self, '_came_from_settings')

        # Stop all current scanning first
        self.is_scanning = False
        try:
            self.nfc_service.cancel_read()
        except Exception as e:
            self.logger.warning(f"Error cancelling NFC read during station switch: {e}")

        old_station = self.current_station
        self.current_station = station
        self.logger.info(f"Switched from {old_station} to {station}")
        self.is_registration_mode = False  # Reception is now checkpoint-only
        
        # Set checkpoint mode: all stations including Reception are checkpoint stations
        self.is_checkpoint_mode = True

        # Update station toggle label text if in single station mode
        if not self.show_all_stations:
            self.station_view_label.configure(text=f"{station} Only")
            # Update table structure to refresh column headers
            self._update_table_structure()

        # Update button highlighting
        self.update_station_buttons()

        self.update_mode_content()
        self.update_status(f"Switched to {station}", "info")

        # Start appropriate scanning for non-Reception stations after a short delay
        if station != "Reception":
            self.after(500, self.start_checkpoint_scanning)

        # Auto-refresh guest list to show station-specific check-ins
        # Add delay to prevent rapid refresh on fast switching
        if hasattr(self, '_station_switch_timer'):
            self.after_cancel(self._station_switch_timer)
        self._station_switch_timer = self.after(300, lambda: self.refresh_guest_data(user_initiated=False))

    def update_station_buttons(self):
        """Update station button styling to highlight current selection."""
        for station, btn in self.station_buttons.items():
            if station == self.current_station:
                # Selected station: filled with border
                btn.configure(
                    fg_color="#ff6b35",
                    hover_color="#e55a2b", 
                    text_color="white",
                    border_color="#ff6b35",
                    border_width=2
                )
            else:
                # Normal state: outline only with colored text
                # Hover: filled background with dark text
                btn.configure(
                    fg_color="transparent",
                    hover_color="#3b82f6",
                    text_color="#3b82f6",
                    border_color="#3b82f6",
                    border_width=2
                )
                # Note: CustomTkinter doesn't support hover text color directly
                # The hover effect will show blue background with blue text (still readable)
    
    def _check_and_refresh_stations(self):
        """Check if new stations were added to Google Sheets and refresh UI."""
        try:
            if not hasattr(self, 'sheets_service') or not self.sheets_service or not self.sheets_service.service:
                return
                
            # Get current stations (using cache)
            try:
                current_stations = self._get_stations_cached()
                if not current_stations:
                    return
            except Exception:
                return
                
            # Check if stations have changed
            current_buttons = set(self.station_buttons.keys())
            new_stations = set(current_stations)
            
            if current_buttons != new_stations:
                self.logger.info(f"Station change detected! Current: {current_buttons}, New: {new_stations}")
                
                # Clear station cache to force re-detection
                self.sheets_service.clear_station_cache()
                
                # Recreate station buttons
                self._recreate_station_buttons(current_stations)
                
                # Note: Table recreation disabled due to memory corruption
                # self._recreate_guest_table()
                
                # Refresh data
                self._update_guest_table_silent(self.guests_data)
                
                self.logger.info("Station UI refreshed with new stations")
                
        except Exception as e:
            self.logger.error(f"Error checking for new stations: {e}")
    
    def _recreate_station_buttons(self, stations):
        """Recreate station buttons with new stations."""
        # Clear existing buttons
        for btn in self.station_buttons.values():
            btn.destroy()
        self.station_buttons.clear()
        
        # Create new buttons
        for i, station in enumerate(stations):
            btn = ctk.CTkButton(
                self.station_buttons_container,
                text=station,
                command=lambda s=station: self.on_station_button_click(s),
                width=110,
                height=50,
                corner_radius=12,
                font=CTkFont(size=15, weight="bold"),
                border_width=2,
                fg_color="transparent",  # No fill by default
                text_color="#3b82f6",   # Blue text color
                border_color="#3b82f6"  # Blue border
                # hover_color removed - handled by custom events
            )
            
            # Add hover text color control
            def on_enter(event, button=btn, station_name=station):
                if station_name != self.current_station:  # Only for non-selected buttons
                    button.configure(
                        fg_color="#3b82f6",      # Blue fill on hover
                        text_color="#212121"     # Dark grey text on hover
                    )
            
            def on_leave(event, button=btn, station_name=station):
                if station_name != self.current_station:  # Only for non-selected buttons
                    button.configure(
                        fg_color="transparent",  # Back to transparent
                        text_color="#3b82f6"     # Back to blue text
                    )
            
            btn.bind("<Enter>", on_enter)
            btn.bind("<Leave>", on_leave)
            
            btn.pack(side="left", padx=3)
            self.station_buttons[station] = btn
            
        # Update highlighting
        self.update_station_buttons()
        
    def _recreate_guest_table(self):
        """Recreate the guest table with new columns - DISABLED due to memory corruption issues."""
        # This method causes memory corruption when destroying/recreating widgets
        # Instead, we'll just refresh the data without recreating the widget
        self.logger.warning("Guest table recreation disabled - restart app to see new columns")
        return
    
    
    def _delayed_station_refresh(self):
        """Force refresh of dynamic stations after UI initialization."""
        try:
            if hasattr(self, 'sheets_service') and self.sheets_service and self.sheets_service.service:
                # Clear both service cache and GUI cache to force fresh detection
                self.sheets_service.clear_station_cache()
                self._gui_cached_stations = None
                
                # Get fresh dynamic stations with fast-fail to prevent startup hanging
                dynamic_stations = self._get_stations_cached(fast_fail_startup=True)
                
                if dynamic_stations:
                    # Check if stations have changed
                    current_buttons = set(self.station_buttons.keys())
                    new_stations = set(dynamic_stations)
                    
                    if current_buttons != new_stations:
                        self.logger.info(f"New stations detected: {list(new_stations - current_buttons)}")
                        self._recreate_station_buttons(dynamic_stations)
                        # Note: Table recreation disabled due to memory corruption
                        # self._recreate_guest_table()
                        if hasattr(self, 'guests_data'):
                            self._update_guest_table_silent(self.guests_data)
        except Exception as e:
            self.logger.warning(f"Error refreshing stations: {e}")

    def toggle_guest_list(self):
        """Toggle guest list visibility."""
        if self.guest_list_visible:
            self.list_frame.pack_forget()
            self.toggle_list_btn.configure(text="Show Guest List ▼")
            self.guest_list_visible = False
        else:
            self.list_frame.pack(fill="both", expand=True, pady=(10, 0))
            self.toggle_list_btn.configure(text="Hide Guest List ▲")
            self.guest_list_visible = True

    def toggle_manual_checkin(self):
        """Toggle check-in button visibility in guest list."""
        action = "show" if not self.checkin_buttons_visible else "hide"
        self.logger.info(f"User clicked Manual Check-in button - {action} check-in buttons")
        self.checkin_buttons_visible = not self.checkin_buttons_visible

        # Update button text and color
        if self.checkin_buttons_visible:
            self.manual_checkin_btn.configure(
                text="✕ Cancel Manual Check-in",
                border_width=2,
                fg_color="transparent",
                text_color="#3b82f6",
                border_color="#3b82f6"
            )
            # Set orange hover when entering manual check-in mode
            self.guest_tree.tag_configure("checkin_hover", background=THEME_COLORS['treeview_hover_bg'], foreground=THEME_COLORS['treeview_hover_fg'])
        else:
            self.manual_checkin_btn.configure(
                text="Manual Check-in",
                border_width=2,
                fg_color="transparent",
                text_color="#ff9800",
                border_color="#ff9800"
            )
            # Keep orange hover color when returning to normal mode
            self.guest_tree.tag_configure("checkin_hover", background=THEME_COLORS['treeview_hover_bg'], foreground=THEME_COLORS['treeview_hover_fg'])

        # Refresh guest table to show/hide check-in buttons
        if self.guest_list_visible:
            # Check if there's an active search filter
            if hasattr(self, 'search_var') and self.search_var.get().strip():
                # Re-apply search filter to maintain filtered results
                self.filter_guest_list()
            else:
                # No search active, show all guests
                self._update_guest_table(self.guests_data)

    def toggle_station_view(self):
        """Toggle between all stations and current station only view."""
        # Get state from switch (True = All Stations, False = Single Station)
        self.show_all_stations = self.station_view_switch.get()
        
        # Always close manual check-in mode when switching station views
        if self.checkin_buttons_visible:
            self.toggle_manual_checkin()
        
        # Update label text based on state
        if self.show_all_stations:
            self.station_view_label.configure(text="All Stations")
        else:
            self.station_view_label.configure(text=f"{self.current_station} Only")
        
        # Update table structure (headers and columns)
        self._update_table_structure()
        
        # Refresh table to show/hide columns and update row coloring
        # Use silent refresh to preserve local check-ins and avoid interfering with sync
        if self.guest_list_visible:
            # Check if there's an active search filter
            if hasattr(self, 'search_var') and self.search_var.get().strip():
                # Re-apply search filter to maintain filtered results
                self.filter_guest_list()
            else:
                # No search active, show all guests
                self._update_guest_table_silent(self.guests_data)

    def _force_treeview_update(self):
        """Force TreeView to update its display after column changes."""
        if self.is_rewrite_mode:
            # Force all parent containers to update their geometry
            self.update_idletasks()
            
            # Don't set explicit TreeView width - let it naturally expand to fill container
            # Match the exact configuration used in single station mode
            for tree in [self.guest_tree, self.summary_tree]:
                tree.column("id", width=80, minwidth=60, anchor="w")
                tree.column("first", width=150, minwidth=100, anchor="w")
                tree.column("last", width=150, minwidth=100, anchor="w")
                tree.column("wristband", width=200, minwidth=150, anchor="center")
            
            # Force geometry update
            self.guest_tree.update_idletasks()
            self.summary_tree.update_idletasks()

    def _update_table_structure(self):
        """Update table columns and headers based on current station view or registration mode."""
        if self.is_rewrite_mode:
            # Registration mode: show wristband columns
            columns = ("id", "first", "last", "wristband")
            
            for tree in [self.summary_tree, self.guest_tree]:
                # Configure the tree with registration columns
                tree.configure(columns=columns)
                
                # Force column deletion and recreation to ensure clean state
                tree.delete(*tree.get_children())
                
                # IMPORTANT: Hide all old station columns that might be lingering
                # This ensures the TreeView recalculates its width properly
                all_possible_columns = ["id", "first", "last", "wristband", "reception", "lio", "juntos", "experimental", "unvrs"]
                for col in all_possible_columns:
                    try:
                        if col not in columns:
                            tree.column(col, width=0, minwidth=0, stretch=False)
                    except:
                        pass  # Column might not exist
                
                # Configure column headers and widths
                tree.heading("id", text="Guest ID", anchor="w")
                tree.heading("first", text="First Name", anchor="w")
                tree.heading("last", text="Last Name", anchor="w")
                tree.heading("wristband", text="Wristband", anchor="center")
                
                # Copy exact pattern from single station mode
                tree.column("id", width=80, minwidth=60, anchor="w")
                tree.column("first", width=150, minwidth=100, anchor="w")
                tree.column("last", width=150, minwidth=100, anchor="w")
                tree.column("wristband", width=200, minwidth=150, anchor="center")
            
            # Show summary tree in registration mode with wristband stats
            self.summary_tree.pack(fill="x", pady=(0, 1))
            
            # Force TreeView to recalculate its display width
            self.after(1, lambda: self._force_treeview_update())
            
        else:
            # Normal station view mode
            available_stations = self._get_filtered_stations_for_view()
            
            # Update column configuration for both trees
            columns = ("id", "first", "last") + tuple(station.lower() for station in available_stations)
            
            for tree in [self.summary_tree, self.guest_tree]:
                # Configure the tree with new columns
                tree.configure(columns=columns)
                
                # Configure fixed column headers and widths
                tree.heading("id", text="Guest ID", anchor="w")
                tree.heading("first", text="First Name", anchor="w")
                tree.heading("last", text="Last Name", anchor="w")
                
                tree.column("id", width=80, minwidth=60, anchor="w")
                tree.column("first", width=150, minwidth=100, anchor="w")
                tree.column("last", width=150, minwidth=100, anchor="w")
                
                # Configure station columns with responsive sizing
                for i, station in enumerate(available_stations):
                    station_key = station.lower()
                    # Only stretch the last column
                    is_last = (i == len(available_stations) - 1)
                    
                    # In single station mode, don't show station name (it's in toggle button above)
                    # In all stations mode, show all station names in headers
                    if len(available_stations) == 1:
                        tree.heading(station_key, text="", anchor="center")
                        tree.column(station_key, width=200, minwidth=150, anchor="center")
                    else:
                        tree.heading(station_key, text=station, anchor="center")
                        tree.column(station_key, width=120, minwidth=80, anchor="center")
            
            # Show summary tree in normal mode
            self.summary_tree.pack(fill="x", pady=(0, 1))

    def _get_filtered_stations_for_view(self, fast_fail_startup=False):
        """Get stations list based on current view mode (all stations vs current station only)."""
        try:
            all_stations = self._get_stations_cached(fast_fail_startup)
        except:
            all_stations = self.config['stations']
        
        if self.show_all_stations:
            return all_stations
        else:
            # Return only current station
            return [self.current_station] if self.current_station in all_stations else [self.current_station]

    def _is_guest_complete_all_stations(self, guest_id, available_stations, item_values):
        """Check if guest has check-ins at all stations (original logic)."""
        # Get local check-ins for this guest
        local_checkins = self.tag_manager.get_all_local_check_ins().get(guest_id, {})
        
        # Station columns start at index 3 (after id, first, last)
        for i, station in enumerate(available_stations):
            col_index = i + 3
            station_lower = station.lower()
            
            # Check tree value first
            tree_has_checkin = False
            if col_index < len(item_values):
                value = item_values[col_index]
                # A check-in exists if it starts with ✓ or has actual timestamp data
                tree_has_checkin = value.startswith("✓") or (value not in ["-", "", "Check-in"])
            
            # Check local queue
            local_has_checkin = station_lower in local_checkins
            
            # If neither tree nor local has check-in, not fully checked in
            if not tree_has_checkin and not local_has_checkin:
                return False
        
        return True

    def _is_guest_complete_current_station(self, guest_id, item_values):
        """Check if guest has check-in at current station only."""
        # Get local check-ins for this guest
        local_checkins = self.tag_manager.get_all_local_check_ins().get(guest_id, {})
        current_station_lower = self.current_station.lower()
        
        # Find current station column (always at index 3 in single-station view)
        if len(item_values) > 3:
            value = item_values[3]
            # Check tree value
            tree_has_checkin = value.startswith("✓") or (value not in ["-", "", "Check-in"])
            # Check local queue
            local_has_checkin = current_station_lower in local_checkins
            
            return tree_has_checkin or local_has_checkin
        
        return False

    def on_sync_complete(self):
        """Called when background sync completes - refresh UI."""
        # Always refresh after sync completes to show updated data
        self.logger.info("Sync completed, refreshing guest list")
        # Schedule refresh on main thread with slight delay to ensure data is ready
        self.after(500, lambda: self.refresh_guest_data(user_initiated=False))

    def _safe_background_refresh(self):
        """Safely refresh guest list in background."""
        if self.is_refreshing or self._active_operations > 0:
            return

        self.is_refreshing = True

        # Run refresh in background thread
        self.submit_background_task(self._background_refresh_thread)

    def _background_refresh_thread(self):
        """Background thread for refreshing guest data."""
        try:
            guests = self.sheets_service.get_all_guests()
            # Update table on main thread
            self.after(0, self._update_guest_table_silent, guests)
        except Exception as e:
            self.logger.error(f"Background refresh failed: {e}")
        finally:
            self.is_refreshing = False

    def update_sync_status(self, message: str, status_type: str = "normal"):
        """Update sync status label with appropriate color."""
        color_map = {
            "normal": "#3b82f6",
            "success": "#4CAF50",
            "warning": "#ff9800",
            "error": "#f44336"
        }
        color = color_map.get(status_type, "#4CAF50")
        self.safe_update_widget(
            'sync_status_label',
            lambda w, text, tc: w.configure(text=text, text_color=tc),
            message, color
        )

    def update_status_respecting_settings_mode(self, message: str, status_type: str = "normal"):
        """Update status while respecting settings mode."""
        if self.settings_visible and self.current_station == "Reception":
            # Reception in settings - show check-in messages and NFC errors
            # Don't show "Ready to register" or similar ready messages
            if message.startswith("✓ Checked in:") or message == self.STATUS_NFC_NOT_CONNECTED:
                self.update_status(message, status_type)
            else:
                self.update_status("", "normal")
        else:
            self.update_status(message, status_type)

    def _update_guest_table_silent(self, guests: List):
        """Update guest table without status messages (for background refresh)."""
        self.guests_data = guests

        # Get all local check-ins
        local_check_ins = self.tag_manager.get_all_local_check_ins()

        # Clear table
        for item in self.guest_tree.get_children():
            self.guest_tree.delete(item)

        # Get dynamic stations for summary row
        try:
            available_stations = self._get_filtered_stations_for_view()
        except:
            available_stations = self.config['stations']

        # Add summary row showing checked-in counts per station
        self._add_summary_row(guests, available_stations, local_check_ins)

        # Add guests
        for i, guest in enumerate(guests):
            values = [
                guest.original_id,
                guest.firstname,
                guest.lastname
            ]

            # Get dynamic stations
            # Use cached stations for table population
            try:
                available_stations = self._get_filtered_stations_for_view()
            except:
                available_stations = self.config['stations']
            
            # Add check-in status for each station
            for station in available_stations:
                station_key = station.lower()
                
                # Ensure the guest has this station in their check_ins dict
                if not hasattr(guest, 'ensure_station_exists'):
                    # For older guest objects without the method, add the station manually
                    if station_key not in guest.check_ins:
                        guest.check_ins[station_key] = None
                else:
                    guest.ensure_station_exists(station_key)
                
                # Google Sheets data takes priority (for manual edits compatibility)
                sheets_time = guest.get_check_in_time(station_key)
                local_time = local_check_ins.get(guest.original_id, {}).get(station_key)

                if sheets_time:
                    # Google Sheets has data - use it (no hourglass needed)
                    values.append(f"✓ {sheets_time}")
                elif local_time:
                    # No Google Sheets data but local data exists (pending sync)
                    values.append(f"✓ {local_time} ⏳")  # Clock emoji indicates pending
                elif self.checkin_buttons_visible:
                    values.append("Check-in")
                else:
                    values.append("-")

            # Determine row styling
            tags = []
            
            # Add alternate row coloring
            row_index = len(self.guest_tree.get_children())
            if row_index % 2 == 0:
                tags.append("even")
            else:
                tags.append("odd")
            
            # Check if guest is fully checked in at all stations
            if self._is_guest_fully_checked_in(guest, available_stations):
                tags = ["complete"]  # Override alternate colors with green
            
            item = self.guest_tree.insert("", "end", values=values, tags=tags)

        # Ensure tags are configured after table rebuild (using THEME_COLORS constants)
        if self.is_light_mode:
            odd_bg = THEME_COLORS['treeview_odd_row_light']
            even_bg = THEME_COLORS['treeview_even_row_light']
            text_color = THEME_COLORS['treeview_text_light']
        else:
            odd_bg = THEME_COLORS['treeview_odd_row_dark']
            even_bg = THEME_COLORS['treeview_even_row_dark']
            text_color = THEME_COLORS['treeview_text_dark']
        
        self.guest_tree.tag_configure("odd", background=odd_bg, foreground=text_color)
        self.guest_tree.tag_configure("even", background=even_bg, foreground=text_color)
        self.guest_tree.tag_configure("complete", background=THEME_COLORS['treeview_complete_bg'], foreground=THEME_COLORS['treeview_complete_fg'])
        # ALWAYS force orange hover (works in both light/dark themes)
        self.guest_tree.tag_configure("checkin_hover", background=THEME_COLORS['treeview_hover_bg'], foreground=THEME_COLORS['treeview_hover_fg'])

        # Sort by Last Name A-Ö permanently
        self._sort_by_lastname()

        # Update Google Sheets connection status
        self._update_sheets_connection_status()
            
        # Check if we need to refresh station buttons
        self._check_and_refresh_stations()

    def _add_summary_row(self, guests, available_stations, local_check_ins):
        """Add a summary row showing checked-in counts per station or wristband stats."""
        # Build summary values: show total guests in first column, other columns empty
        total_guests = len(guests)
        
        # Registration mode - show wristband stats
        if self.is_rewrite_mode:
            # Count guests with wristbands
            wristband_count = sum(1 for guest in guests if guest.wristband_uuid)
            summary_values = [f"{wristband_count}/{total_guests}", "", "", ""]
        # In single station mode, also show unchecked count
        elif not self.show_all_stations and len(available_stations) == 1:
            # Calculate unchecked count for the single station
            station_key = available_stations[0].lower()
            checked_count = 0
            
            for guest in guests:
                sheets_time = guest.get_check_in_time(station_key)
                local_time = local_check_ins.get(guest.original_id, {}).get(station_key)
                
                if sheets_time or local_time:
                    checked_count += 1
            
            unchecked_count = total_guests - checked_count
            summary_values = [f"{total_guests} guests ({unchecked_count} unchecked)", "", ""]
        else:
            # All stations mode - just show total guests
            summary_values = [f"{total_guests} guests", "", ""]
        
        # Calculate checked-in count for each station
        for station in available_stations:
            station_key = station.lower()
            checked_in_count = 0
            
            for guest in guests:
                # Check both Google Sheets data and local queue
                sheets_time = guest.get_check_in_time(station_key)
                local_time = local_check_ins.get(guest.original_id, {}).get(station_key)
                
                if sheets_time or local_time:
                    checked_in_count += 1
            
            # Add count - just the checked in number
            summary_values.append(str(checked_in_count))
        
        # Clear and add to fixed summary tree
        for item in self.summary_tree.get_children():
            self.summary_tree.delete(item)
        
        summary_item = self.summary_tree.insert("", "end", values=summary_values, tags=["summary"])
        
        # Configure summary row styling - will be updated by theme system
        # self.summary_tree.tag_configure("summary", background="#323232", foreground="white", font=("TkFixedFont", 14, "bold"))

    def _sort_by_lastname(self):
        """Sort guest list by Last Name A-Ö"""
        items = self.guest_tree.get_children('')
        
        if not items:
            return
            
        # Get guest data with last names for sorting
        guest_data = []
        for item in items:
            values = self.guest_tree.item(item)['values']
            if len(values) >= 3:  # Ensure we have lastname
                lastname = values[2]  # Last name is in column 2
                guest_data.append((lastname.lower(), item))  # Lowercase for proper sorting
        
        # Sort by lastname A-Ö
        guest_data.sort(key=lambda x: x[0])
        
        # Reorder items
        for index, (lastname, item) in enumerate(guest_data):
            self.guest_tree.move(item, '', index)

    def _update_summary_row_immediate(self):
        """Update just the summary row immediately without refreshing the entire table."""
        # Get all guest items from main tree (no summary row here now)
        guest_items = self.guest_tree.get_children('')
        
        if not guest_items:
            return
            
        # Get dynamic stations
        try:
            available_stations = self._get_filtered_stations_for_view()
        except:
            available_stations = self.config['stations']
        
        # Build new summary values: show total guests in first column, other columns empty
        total_guests = len(guest_items)
        
        # Get local check-ins for current counts
        local_check_ins = self.tag_manager.get_all_local_check_ins()
        
        # In single station mode, also show unchecked count
        if not self.show_all_stations and len(available_stations) == 1:
            # Calculate unchecked count for the single station
            station_key = available_stations[0].lower()
            checked_count = 0
            
            for guest_item in guest_items:
                guest_values = self.guest_tree.item(guest_item)['values']
                if len(guest_values) >= 3:
                    guest_id = int(guest_values[0])
                    
                    # Find the station column index
                    station_col_index = None
                    for i, col_station in enumerate(available_stations):
                        if col_station.lower() == station_key:
                            station_col_index = i + 3  # +3 for id, first, last columns
                            break
                    
                    if station_col_index and station_col_index < len(guest_values):
                        # Check tree value
                        tree_value = guest_values[station_col_index]
                        tree_has_checkin = tree_value not in ["-", "", "Check-in"]
                        
                        # Check local queue
                        local_has_checkin = local_check_ins.get(guest_id, {}).get(station_key)
                        
                        if tree_has_checkin or local_has_checkin:
                            checked_count += 1
            
            unchecked_count = total_guests - checked_count
            summary_values = [f"{total_guests} guests ({unchecked_count} unchecked)", "", ""]
        else:
            # All stations mode - just show total guests
            summary_values = [f"{total_guests} guests", "", ""]
        
        # Calculate checked-in count for each station based on current tree values
        for station in available_stations:
            station_key = station.lower()
            checked_in_count = 0
            
            for guest_item in guest_items:
                guest_values = self.guest_tree.item(guest_item)['values']
                if len(guest_values) >= 3:
                    guest_id = int(guest_values[0])
                    
                    # Find the station column index
                    station_col_index = None
                    for i, col_station in enumerate(available_stations):
                        if col_station.lower() == station_key:
                            station_col_index = i + 3  # +3 for id, first, last columns
                            break
                    
                    if station_col_index and station_col_index < len(guest_values):
                        # Check tree value
                        tree_value = guest_values[station_col_index]
                        tree_has_checkin = tree_value not in ["-", "", "Check-in"]
                        
                        # Check local queue
                        local_has_checkin = local_check_ins.get(guest_id, {}).get(station_key)
                        
                        if tree_has_checkin or local_has_checkin:
                            checked_in_count += 1
            
            # Add count - just the checked in number
            summary_values.append(str(checked_in_count))
        
        # Update the summary tree
        summary_items = self.summary_tree.get_children('')
        if summary_items:
            self.summary_tree.item(summary_items[0], values=summary_values)

    def _check_internet_connection(self):
        """Check internet connectivity with simple HTTP request."""
        try:
            response = requests.get(self.TEST_INTERNET_URL, timeout=self.TEST_INTERNET_TIMEOUT, stream=True)
            response.raise_for_status()
            response.close()
            return True
        except:
            return False

    def _periodic_status_check(self):
        """Periodically check connection status and update sync indicator."""
        # Only update if not currently refreshing/editing
        if not self.edit_entry and self._sheets_refresh_lock.acquire(blocking=False):
            try:
                self._update_sheets_connection_status()
            finally:
                self._sheets_refresh_lock.release()
        
        # Schedule next check in 10 seconds
        self.after(10000, self._periodic_status_check)

    def _start_id_clear_timer(self):
        """Start 15-second timer to auto-clear guest ID field."""
        # Cancel any existing timer
        if hasattr(self, '_id_clear_timer'):
            self.after_cancel(self._id_clear_timer)
        
        # Start new 15-second timer
        self._id_clear_timer = self.after(15000, self._auto_clear_id_field)

    def _auto_clear_id_field(self):
        """Auto-clear the guest ID field and guest name."""
        if hasattr(self, 'id_entry'):
            try:
                # Check if the widget still exists and is valid
                if self.id_entry.winfo_exists():
                    self.id_entry.delete(0, 'end')
                    # Also clear the guest name display
                    self.safe_update_widget('guest_name_label', lambda w: w.configure(text=""))
            except (AttributeError, tk.TclError):
                # Widget was destroyed, ignore the error
                pass

    def _check_internet_periodically(self):
        """Lightweight periodic internet check that updates status only."""
        try:
            # Quick check without blocking
            current_status = self._check_internet_connection()
            old_status = self._internet_connected
            
            # Update status if changed
            if current_status != old_status:
                self._internet_connected = current_status
                if not current_status:
                    # Internet lost
                    self.sync_status_label.configure(text=self.SYNC_STATUS_NO_INTERNET, text_color="#f44336")
                else:
                    # Internet restored - check Google Sheets and refresh data
                    self.logger.info("Internet connection restored - triggering data refresh")
                    self._update_sheets_connection_status()
                    # Trigger refresh like Cmd+R to sync any changes that occurred while offline
                    self.refresh_guest_data()
                    
        except Exception as e:
            # Don't log errors to avoid spam
            pass
        
        # Schedule next check in 10 seconds
        self.after(10000, self._check_internet_periodically)


    def _update_sheets_connection_status(self):
        """Update Google Sheets connection status in sync label."""
        try:
            # First check if we have internet (from background monitoring)
            if not self._internet_connected:
                self.sync_status_label.configure(text=self.SYNC_STATUS_NO_INTERNET, text_color="#f44336")
                return

            # Then check Google Sheets specifically
            if hasattr(self, 'sheets_service') and self.sheets_service:
                # Try a simple operation to test connectivity
                stations = self.sheets_service.get_available_stations()
                if stations:
                    # Successfully connected
                    self.sync_status_label.configure(text=self.SYNC_STATUS_CONNECTED, text_color="#4CAF50")
                else:
                    # Connected but no data
                    self.sync_status_label.configure(text=self.SYNC_STATUS_EMPTY, text_color="#ff9800")
            else:
                # No sheets service
                self.sync_status_label.configure(text=self.SYNC_STATUS_OFFLINE, text_color="#f44336")
        except Exception as e:
            # Check if it's a rate limiting issue first
            if "429" in str(e) or "quota" in str(e).lower():
                self.sync_status_label.configure(text=self.SYNC_STATUS_RATE_LIMITED, text_color="#ff9800")
            else:
                # For other Google Sheets specific errors, check internet again
                if self._check_internet_connection():
                    # Internet is fine, Google Sheets service issue
                    self.sync_status_label.configure(text=self.SYNC_STATUS_OFFLINE, text_color="#f44336")
                else:
                    # No internet connection
                    self.sync_status_label.configure(text=self.SYNC_STATUS_NO_INTERNET, text_color="#f44336")

    def toggle_theme(self):
        """Toggle between light and dark mode."""
        self._restart_settings_timer()  # Restart timer on button interaction
        self.logger.info("User clicked Theme Toggle button")
        
        # Toggle theme state
        self.is_light_mode = not self.is_light_mode
        
        if self.is_light_mode:
            # In light mode - button shows "Dark Mode" (what it switches to)
            ctk.set_appearance_mode("light")
            self.theme_btn.configure(
                text="Dark Mode",
                text_color=THEME_COLORS['theme_light_text'],
                border_color=THEME_COLORS['theme_light_text']
            )
            self.logger.info("Switched to light mode")
        else:
            # In dark mode - button shows "Light Mode" (what it switches to)
            ctk.set_appearance_mode("dark")
            self.theme_btn.configure(
                text="Light Mode",
                text_color=THEME_COLORS['theme_dark_text'],
                border_color=THEME_COLORS['theme_dark_text']
            )
            self.logger.info("Switched to dark mode")
        
        # Update all frame backgrounds for new theme
        self._update_all_frame_backgrounds()
        
        # Save theme preference
        self._save_theme_preference()
        
        # Update hover effects for new colors
        self._update_theme_hover_effects()
        
        # Update TreeView colors for the new theme
        self._update_treeview_theme()
        
        # If in settings mode, refresh settings content to apply new theme
        if self.settings_visible:
            self.update_mode_content()

    def _save_theme_preference(self):
        """Save theme preference to config."""
        try:
            self.config['theme'] = 'light' if self.is_light_mode else 'dark'
            with open('config/config.json', 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            self.logger.warning(f"Failed to save theme preference: {e}")

    def _update_theme_hover_effects(self):
        """Update hover effects for theme button after color change."""
        # Remove old bindings
        self.theme_btn.unbind("<Enter>")
        self.theme_btn.unbind("<Leave>")
        
        # Get current colors (opposite of current mode)
        current_color = "#404040" if self.is_light_mode else "#e0e0e0"
        
        # Add new hover effects with current colors
        def on_theme_enter(event):
            self.theme_btn.configure(fg_color=current_color, text_color="#212121")
        def on_theme_leave(event):
            self.theme_btn.configure(fg_color="transparent", text_color=current_color)
        
        self.theme_btn.bind("<Enter>", on_theme_enter)
        self.theme_btn.bind("<Leave>", on_theme_leave)

    def _update_treeview_theme(self):
        """Update TreeView colors based on current theme."""
        if not hasattr(self, 'guest_tree'):
            return

        style = ttk.Style()
        style.theme_use("clam")  # Ensure the clam theme is active

        if self.is_light_mode:
            # --- Light Mode Colors (from THEME_COLORS constants) ---
            tree_bg = THEME_COLORS['treeview_bg_light']
            text_color = THEME_COLORS['treeview_text_light']
            heading_bg = THEME_COLORS['treeview_heading_light']
            odd_row_bg = THEME_COLORS['treeview_odd_row_light']
            even_row_bg = THEME_COLORS['treeview_even_row_light']
            summary_bg = THEME_COLORS['treeview_summary_light']
            summary_text = THEME_COLORS['treeview_summary_text_light']
            selected_bg = THEME_COLORS['treeview_selected_bg_light']
            selected_fg = THEME_COLORS['treeview_selected_fg_light']
        else:
            # --- Dark Mode Colors (from THEME_COLORS constants) ---
            tree_bg = THEME_COLORS['treeview_bg_dark']
            text_color = THEME_COLORS['treeview_text_dark']
            heading_bg = THEME_COLORS['treeview_heading_dark']
            odd_row_bg = THEME_COLORS['treeview_odd_row_dark']
            even_row_bg = THEME_COLORS['treeview_even_row_dark']
            summary_bg = THEME_COLORS['treeview_summary_dark']
            summary_text = THEME_COLORS['treeview_summary_text_dark']
            selected_bg = THEME_COLORS['treeview_selected_bg_dark']
            selected_fg = THEME_COLORS['treeview_selected_fg_dark']

        # 1. Configure the BASE style for the Treeview widget
        style.configure("Treeview",
                        background=tree_bg,
                        foreground=text_color,
                        fieldbackground=tree_bg,  # This is crucial for row colors to work
                        borderwidth=0,
                        relief="flat",
                        rowheight=25,
                        font=("TkFixedFont", THEME_COLORS['treeview_data_font_size'], "normal"))

        # 2. Configure the Heading style
        style.configure("Treeview.Heading",
                        background=heading_bg,
                        foreground=text_color,
                        borderwidth=0,
                        relief="flat",
                        font=("TkFixedFont", THEME_COLORS['treeview_header_font_size'], "bold"))
        
        # 2b. Disable hover effects for headers
        style.map("Treeview.Heading",
                  background=[('active', heading_bg)],  # Same color on hover
                  foreground=[('active', text_color)])  # Same text color on hover

        # 3. Make selection invisible by using normal row colors
        style.map('Treeview',
                  background=[
                      ('selected', tree_bg)  # Same as normal background
                  ],
                  foreground=[
                      ('selected', text_color)  # Same as normal text
                  ])

        # 4. Configure the tags for alternating row colors and summary
        self.guest_tree.tag_configure("odd", background=odd_row_bg, foreground=text_color)
        self.guest_tree.tag_configure("even", background=even_row_bg, foreground=text_color)
        self.guest_tree.tag_configure("complete", background=THEME_COLORS['treeview_complete_bg'], foreground=THEME_COLORS['treeview_complete_fg'])
        
        # Configure hover tag based on current manual check-in mode
        if hasattr(self, 'checkin_buttons_visible') and self.checkin_buttons_visible:
            # Orange hover when manual check-in mode is active
            self.guest_tree.tag_configure("checkin_hover", background=THEME_COLORS['treeview_hover_bg'], foreground=THEME_COLORS['treeview_hover_fg'])
        else:
            # Light grey hover when in normal mode
            normal_hover_bg = THEME_COLORS['treeview_normal_hover_light'] if self.is_light_mode else THEME_COLORS['treeview_normal_hover_dark']
            self.guest_tree.tag_configure("checkin_hover", background=normal_hover_bg, foreground=text_color)

        # 5. Apply the same base styling to the summary tree (if it exists)
        if hasattr(self, 'summary_tree'):
            # Configure the summary tree to use the same base style as the main tree
            # This ensures the background is correct even before tags are applied
            style.configure("Summary.Treeview",
                            background=tree_bg,
                            foreground=text_color,
                            fieldbackground=tree_bg,
                            rowheight=25,
                            font=("TkFixedFont", THEME_COLORS['treeview_data_font_size'], "normal"))
            self.summary_tree.configure(style="Summary.Treeview")
            
            # Also configure the tag for the summary row content
            summary_font_size = THEME_COLORS['treeview_summary_font_size']
            self.summary_tree.tag_configure("summary", background=summary_bg, foreground=summary_text, font=("TkFixedFont", summary_font_size, "bold"))

        # 6. Refresh the data to apply new tags (this is more reliable than the old refresh method)
        if hasattr(self, 'guests_data'):
            self._update_guest_table(self.guests_data)


    def refresh_guest_data(self, user_initiated=True):
        """Refresh guest data from Google Sheets."""
        if user_initiated:
            self.logger.info("Manual refresh guest data requested")
            
        # Quick internet check (no logging for performance)
        internet_check = self._check_internet_connection()
            
        # Skip if editing is in progress
        if self.edit_entry:
            if user_initiated:
                self.update_status("Cannot refresh while editing", "warning")
            return
            
        # Skip if already refreshing
        if not self._sheets_refresh_lock.acquire(blocking=False):
            if user_initiated:
                self.update_status("Refresh already in progress", "warning")
            return
            
        # Update internet connection status
        self._internet_connected = internet_check
        if not internet_check:
            self.logger.info(f"No internet connection detected - will attempt to use cached data (user_initiated: {user_initiated})")
            self.sync_status_label.configure(text=self.SYNC_STATUS_NO_INTERNET, text_color="#f44336")

        # Show status message only for user-initiated refreshes
        if user_initiated:
            if self.settings_visible:
                # In settings, show in main status bar
                self.update_status(self.STATUS_REFRESHING, "info")
            else:
                # Normal mode, show in sync area
                self.update_sync_status(self.STATUS_REFRESHING, "normal")

        self._is_user_initiated_refresh = user_initiated

        # Run in thread
        self.submit_background_task(self._refresh_guest_data_thread)

    def _refresh_guest_data_thread(self):
        """Thread function for refreshing data."""
        try:
            # Always try to get guests - the sheets service will return cached data if offline
            self.logger.info(f"Attempting to get guests. Internet connected: {self._internet_connected}")
            guests = self.sheets_service.get_all_guests()
            self.logger.info(f"Retrieved {len(guests)} guests from sheets service")
            
            # Show offline message if no internet and user initiated
            if not self._internet_connected and hasattr(self, '_is_user_initiated_refresh') and self._is_user_initiated_refresh:
                self.after(0, self.update_status, "No internet connection - using cached data", "warning")
                
            # Resolve any sync conflicts (local data vs Google Sheets)
            self.tag_manager.resolve_sync_conflicts(guests)
            # Sync tag registry with wristband data from Google Sheets
            self.tag_manager.sync_tag_registry_with_sheets(guests)
            # Always update table even if empty to show local data
            self.after(0, self._update_guest_table, guests)
        except Exception as e:
            self.logger.error(f"Failed to fetch from Google Sheets: {e}")
            # Try to get cached data from sheets service as fallback
            try:
                cached_guests = getattr(self.sheets_service, '_cached_guests', [])
                self.logger.info(f"Using fallback cached data: {len(cached_guests)} guests")
                self.tag_manager.sync_tag_registry_with_sheets(cached_guests)
                self.after(0, self._update_guest_table, cached_guests)
            except:
                # Final fallback to existing app data
                self.tag_manager.sync_tag_registry_with_sheets(self.guests_data)
                self.after(0, self._update_guest_table, self.guests_data)
            # Only show cached data message for user-initiated refreshes, not automatic ones
            if hasattr(self, '_is_user_initiated_refresh') and self._is_user_initiated_refresh:
                self.after(0, self.update_sync_status, "Using cached data (Google Sheets offline)", "warning")
        finally:
            # Always release the refresh lock
            self._sheets_refresh_lock.release()

    def _update_guest_table(self, guests: List):
        """Update the guest table with new data."""
        self.guests_data = guests

        # Get all local check-ins
        local_check_ins = self.tag_manager.get_all_local_check_ins()

        # Get sync status to determine if we should show hourglasses
        registry_stats = self.tag_manager.get_registry_stats()
        sync_complete = registry_stats['pending_syncs'] == 0

        # Clear table
        for item in self.guest_tree.get_children():
            self.guest_tree.delete(item)

        # Reset hover state since all items are deleted
        self.hovered_item = None

        # Get dynamic stations for summary row
        try:
            available_stations = self._get_filtered_stations_for_view()
        except:
            available_stations = self.config['stations']

        # Add summary row showing checked-in counts per station or wristband stats
        self._add_summary_row(guests, available_stations, local_check_ins)

        # Track discrepancies for re-sync
        discrepancies = []

        # Add guests
        for i, guest in enumerate(guests):
            values = [
                guest.original_id,
                guest.firstname,
                guest.lastname
            ]

            if self.is_rewrite_mode:
                # Registration mode: add wristband column
                # Check if guest has wristband UUID in column E
                if guest.wristband_uuid:
                    values.append("✓")  # Checkmark for registered wristband
                else:
                    values.append("-")  # No wristband registered
            else:
                # Get dynamic stations
                # Use cached stations for table population
                try:
                    available_stations = self._get_filtered_stations_for_view()
                except:
                    available_stations = self.config['stations']
                
                # Add check-in status for each station
                for station in available_stations:
                    station_key = station.lower()
                
                    # Ensure the guest has this station in their check_ins dict
                    if station_key not in guest.check_ins:
                        guest.check_ins[station_key] = None
                    
                    # Google Sheets data takes priority (for manual edits compatibility)
                    sheets_time = guest.get_check_in_time(station_key)
                    local_time = local_check_ins.get(guest.original_id, {}).get(station_key)

                    if sheets_time:
                        # Google Sheets has data - use it (no hourglass needed)
                        values.append(f"✓ {sheets_time}")
                    elif local_time:
                        if sync_complete:
                            # If sync shows complete but Google Sheets is missing data, re-sync this item
                            discrepancies.append({
                                'guest_id': guest.original_id,
                                'station': station.lower(),
                                'timestamp': local_time
                            })
                            # Show without hourglass since sync claims to be complete
                            values.append(f"✓ {local_time}")
                        else:
                            # Sync still pending - show hourglass
                            values.append(f"✓ {local_time} ⏳")  # Clock emoji indicates pending
                    elif self.checkin_buttons_visible:
                        values.append("Check-in")
                    else:
                        values.append("-")

            # Determine row styling
            tags = []
            
            # Add alternate row coloring
            row_index = len(self.guest_tree.get_children())
            if row_index % 2 == 0:
                tags.append("even")
            else:
                tags.append("odd")
            
            if self.is_rewrite_mode:
                # Registration mode: highlight guests with registered wristbands
                if guest.wristband_uuid:
                    tags = ["complete"]  # Use green highlighting for registered wristbands
            else:
                # Check if guest is fully checked in at all stations
                if self._is_guest_fully_checked_in(guest, available_stations):
                    tags = ["complete"]  # Override alternate colors with green
            
            item = self.guest_tree.insert("", "end", values=values, tags=tags)

        # Handle discrepancies - re-sync items that should be synced but aren't
        if discrepancies:
            self.logger.warning(f"Found {len(discrepancies)} sync discrepancies, re-syncing...")
            self._handle_sync_discrepancies(discrepancies)

        # Ensure tags are configured after table rebuild (using THEME_COLORS constants)
        if self.is_light_mode:
            odd_bg = THEME_COLORS['treeview_odd_row_light']
            even_bg = THEME_COLORS['treeview_even_row_light']
            text_color = THEME_COLORS['treeview_text_light']
        else:
            odd_bg = THEME_COLORS['treeview_odd_row_dark']
            even_bg = THEME_COLORS['treeview_even_row_dark']
            text_color = THEME_COLORS['treeview_text_dark']
        
        self.guest_tree.tag_configure("odd", background=odd_bg, foreground=text_color)
        self.guest_tree.tag_configure("even", background=even_bg, foreground=text_color)
        self.guest_tree.tag_configure("complete", background=THEME_COLORS['treeview_complete_bg'], foreground=THEME_COLORS['treeview_complete_fg'])
        # ALWAYS force orange hover (works in both light/dark themes)
        self.guest_tree.tag_configure("checkin_hover", background=THEME_COLORS['treeview_hover_bg'], foreground=THEME_COLORS['treeview_hover_fg'])

        # Sort by Last Name A-Ö permanently
        self._sort_by_lastname()

        # Update Google Sheets connection status
        self._update_sheets_connection_status()

        # Force sync on startup if there are pending items
        registry_stats = self.tag_manager.get_registry_stats()
        if registry_stats['pending_syncs'] > 0 and not hasattr(self, '_initial_load_complete'):
            self.logger.info(f"Found {registry_stats['pending_syncs']} pending syncs at startup - forcing sync")
            self.after(1000, self._force_sync_on_startup)

        # Only show "Loaded X guests" message at startup and only if we have actual data
        if not hasattr(self, '_initial_load_complete') and len(guests) > 0:
            self.update_status(f"Loaded {len(guests)} guests", "success")
            # Fade to appropriate status after 2 seconds
            if self.is_rewrite_mode:
                self.after(2000, lambda: self.update_status("", "normal"))
            else:
                self.after(2000, lambda: self._update_status_respecting_settings_mode_with_correct_type())
            self._initial_load_complete = True

            # Start registration scanning after initial load if in registration mode
            if self.is_registration_mode and not self.is_checkpoint_mode:
                # Reception now uses checkpoint scanning
                self.after(2500, self.start_checkpoint_scanning)
        elif hasattr(self, '_is_user_initiated_refresh') and self._is_user_initiated_refresh:
            # Show confirmation if refresh was done in settings
            if self.settings_visible:
                self.update_status("✓ Refreshed", "success")
            delattr(self, '_is_user_initiated_refresh')  # Clean up flag
        elif self.is_rewrite_mode:
            # In rewrite mode, go straight to paused status
            # No status message needed - "Check-in Paused" shown in stations frame
            pass
        # No refresh messages for silent background refreshes

    def _handle_sync_discrepancies(self, discrepancies: List[Dict]):
        """Handle sync discrepancies by re-syncing missing data to Google Sheets."""
        def _resync_thread():
            for item in discrepancies:
                try:
                    # Force sync this specific item to Google Sheets
                    success = self.tag_manager.force_sync_item(
                        item['guest_id'],
                        item['station'],
                        item['timestamp']
                    )
                    if success:
                        self.logger.info(f"Re-synced {item['guest_id']} at {item['station']}")
                    else:
                        self.logger.warning(f"Failed to re-sync {item['guest_id']} at {item['station']}")
                except Exception as e:
                    self.logger.error(f"Error re-syncing discrepancy: {e}")

            # Refresh after re-sync attempts
            self.after(1000, lambda: self.refresh_guest_data(user_initiated=False))

        # Run re-sync in background thread
        thread = threading.Thread(target=_resync_thread)
        thread.daemon = True
        thread.start()

    def _on_search_change(self):
        """Handle search field changes - restart timer and filter list."""
        self._restart_settings_timer()  # Restart timer on search interaction
        self.filter_guest_list()

    def clear_search(self):
        """Clear the search field."""
        if hasattr(self, 'search_var'):
            self.search_var.set("")

    def filter_guest_list(self):
        """Filter guest list based on search with smart multi-word matching."""
        search_term = self.search_var.get().strip().lower()

        if not search_term:
            # Show all guests if search is empty
            self._update_guest_table(self.guests_data)
            return

        # Get all local check-ins
        local_check_ins = self.tag_manager.get_all_local_check_ins()

        # Clear table
        for item in self.guest_tree.get_children():
            self.guest_tree.delete(item)

        # Split search into words for smart matching
        search_words = search_term.split()

        # Get dynamic stations for summary row
        try:
            available_stations = self._get_filtered_stations_for_view()
        except:
            available_stations = self.config['stations']

        # Collect filtered guests first to calculate summary
        filtered_guests = []
        
        # Filter guests based on search
        for guest in self.guests_data:
            # Create searchable text from all guest fields
            guest_text = f"{guest.original_id} {guest.firstname} {guest.lastname} {guest.full_name}".lower()

            # Check if guest matches search
            matches = False

            if len(search_words) == 1:
                # Single word search - check if it appears anywhere
                matches = search_words[0] in guest_text
            else:
                # Multi-word search - all words must appear somewhere (order independent)
                matches = all(word in guest_text for word in search_words)

            if matches:
                filtered_guests.append(guest)

        # Add summary row for filtered results
        self._add_summary_row(filtered_guests, available_stations, local_check_ins)

        # Add filtered guests to table
        for guest in filtered_guests:
            values = [
                guest.original_id,
                guest.firstname,
                guest.lastname
            ]
                
            # Add check-in status for each station
            for station in available_stations:
                station_key = station.lower()
                
                # Ensure the guest has this station in their check_ins dict
                if station_key not in guest.check_ins:
                    guest.check_ins[station_key] = None
                
                # Google Sheets data takes priority (for manual edits compatibility)
                sheets_time = guest.get_check_in_time(station_key)
                local_time = local_check_ins.get(guest.original_id, {}).get(station_key)

                if sheets_time:
                    # Google Sheets has data - use it
                    values.append(f"✓ {sheets_time}")
                elif local_time:
                    # No Google Sheets data but local data exists (pending sync)
                    values.append(f"✓ {local_time} ⏳")  # Clock emoji indicates pending
                elif self.checkin_buttons_visible:
                    values.append("Check-in")
                else:
                    values.append("-")

            # Determine row styling
            tags = []
            
            # Add alternate row coloring
            row_index = len(self.guest_tree.get_children())
            if row_index % 2 == 0:
                tags.append("even")
            else:
                tags.append("odd")
            
            # Check if guest is fully checked in at all stations
            if self._is_guest_fully_checked_in(guest, available_stations):
                tags = ["complete"]  # Override alternate colors with green
            
            item = self.guest_tree.insert("", "end", values=values, tags=tags)

        # Sort by Last Name A-Ö permanently
        self._sort_by_lastname()

    def on_cell_double_click(self, event):
        """Handle double-click on treeview cell for editing or selection."""
        # Get the clicked item and column
        item = self.guest_tree.identify('item', event.x, event.y)
        column = self.guest_tree.identify('column', event.x, event.y)
        
        if not item or not column:
            return
        
        # Get column index
        col_num = int(column.replace('#', '')) - 1
        
        # Get all columns
        columns = list(self.guest_tree['columns'])
        
        # If clicking on ID, First Name, or Last Name columns, treat as guest selection
        if col_num < 3:
            self.on_guest_select_direct(item)
            return
        
        # For station columns, enable editing
        if col_num >= 3:
            self.start_cell_edit(item, column, col_num)
    
    def start_cell_edit(self, item, column, col_num):
        """Start editing a cell."""
        # Cancel any existing edit
        self.cancel_edit()
        
        # Get item values and bbox
        values = self.guest_tree.item(item)['values']
        bbox = self.guest_tree.bbox(item, column)
        
        if not bbox:
            return
        
        # Create entry widget
        self.edit_entry = tk.Entry(self.guest_tree, justify='center')
        self.edit_item = item
        self.edit_column = col_num
        
        # Set current value
        current_value = values[col_num] if col_num < len(values) else ""
        
        # Don't allow editing of "Check-in" buttons or "-" placeholders in manual mode
        if current_value == "Check-in" or (current_value == "-" and self.checkin_buttons_visible):
            return
            
        # Clean up display value (remove checkmarks and emojis)
        if isinstance(current_value, str):
            if current_value.startswith("✓"):
                current_value = current_value[2:].strip()
            if "⏳" in current_value:
                current_value = current_value.replace("⏳", "").strip()
            if current_value == "-":
                current_value = ""  # Clear the dash for editing
        
        self.edit_entry.insert(0, current_value)
        self.edit_entry.select_range(0, tk.END)
        
        # Place and show entry
        self.edit_entry.place(x=bbox[0], y=bbox[1], width=bbox[2], height=bbox[3])
        self.edit_entry.focus()
        
        # Bind events
        self.edit_entry.bind('<Return>', self.save_edit)
        self.edit_entry.bind('<Escape>', lambda e: self.cancel_edit())
        
        # Add a delay before binding the global click to avoid processing the current double-click
        self.after(100, lambda: self.bind_all('<Button-1>', self._on_global_click))
    
    def save_edit(self, event=None):
        """Save the edited value."""
        if not self.edit_entry or not self.edit_item:
            return
        
        # Prevent multiple save attempts
        if hasattr(self, '_saving_edit') and self._saving_edit:
            return
        self._saving_edit = True
        
        try:
            # Check if the item still exists
            try:
                item_values = list(self.guest_tree.item(self.edit_item)['values'])
            except Exception:
                # Item was deleted (likely from a refresh)
                self.cancel_edit()
                return
            
            new_value = self.edit_entry.get().strip()
            guest_id = item_values[0]
            
            # Get station name
            columns = list(self.guest_tree['columns'])
            station_name = columns[self.edit_column]
            
            # Store the item reference before canceling edit
            edited_item = self.edit_item
            edited_column = self.edit_column
            
            # Clean up edit widget immediately for responsiveness
            self.cancel_edit()
            
            # Update tree display immediately with hourglass for pending feedback
            if new_value:
                # Show with hourglass immediately for user feedback
                item_values[edited_column] = f"✓ {new_value} ⏳"
            else:
                item_values[edited_column] = "-"
            
            # Update the tree immediately
            self.guest_tree.item(edited_item, values=item_values)
            
            # Check if we need to update row styling (for complete status)
            self._update_row_styling(edited_item, guest_id)
            
            # Update summary row immediately to reflect the change
            self._update_summary_row_immediate()
            
            # Use queue system to avoid rate limiting, but don't refresh immediately
            # The sync completion callback will handle refreshes automatically
            def update_checkin():
                try:
                    if new_value:
                        # Get guest name from tree values (firstname lastname)
                        guest_name = f"{item_values[1]} {item_values[2]}"
                        # Add to queue - will sync automatically without rate limit issues
                        self.tag_manager.check_in_queue.add_check_in(int(guest_id), station_name.lower(), new_value, guest_name)
                        self.logger.info(f"Queued check-in for guest {guest_id} at {station_name}: {new_value}")
                    else:
                        # For clears, we can still use direct API since they're less frequent
                        self.sheets_service.mark_attendance(int(guest_id), station_name, "")
                        self.logger.info(f"Cleared check-in for guest {guest_id} at {station_name}")
                        
                        # Update local data immediately to prevent reappearing when toggling views
                        for guest in self.guests_data:
                            if guest.original_id == int(guest_id):
                                guest.check_ins[station_name.lower()] = None
                                break
                except Exception as e:
                    self.logger.error(f"Error updating check-in: {e}")
            
            # Run in background thread
            self.thread_pool.submit(update_checkin)
        
        finally:
            self._saving_edit = False
    
    def cancel_edit(self):
        """Cancel cell editing."""
        if self.edit_entry:
            self.edit_entry.destroy()
            self.edit_entry = None
        self.edit_item = None
        self.edit_column = None
        self._saving_edit = False
        # Unbind global click
        self.unbind_all('<Button-1>')
    
    def _on_global_click(self, event):
        """Handle global click to close edit."""
        # Only close if we have an active edit and the click wasn't on the entry
        if self.edit_entry and self.edit_entry.winfo_exists():
            # Check if click is on the entry widget
            widget = event.widget
            if widget != self.edit_entry:
                self.save_edit()
    
    def update_checkin_value(self, guest_id, station, value):
        """Update a check-in value in Google Sheets."""
        try:
            # Use sheets service directly to update
            result = self.sheets_service.mark_attendance(int(guest_id), station, value)
            if result:
                self.logger.info(f"Updated check-in for guest {guest_id} at {station} to: {value}")
        except Exception as e:
            self.logger.error(f"Error updating check-in: {e}")
    
    def clear_checkin_value(self, guest_id, station):
        """Clear a check-in value in Google Sheets."""
        try:
            # Mark with empty string to clear
            result = self.sheets_service.mark_attendance(int(guest_id), station, "")
            if result:
                self.logger.info(f"Cleared check-in for guest {guest_id} at {station}")
        except Exception as e:
            self.logger.error(f"Error clearing check-in: {e}")

    def on_guest_select(self, event):
        """Handle guest selection from list."""
        selection = self.guest_tree.selection()
        if selection:
            item = self.guest_tree.item(selection[0])
            guest_id = item['values'][0]

            if self.is_registration_mode:
                # Fill registration form
                self.id_entry.delete(0, 'end')
                self.id_entry.insert(0, str(guest_id))
                # Start 15-second auto-clear timer
                self._start_id_clear_timer()
            elif self.is_rewrite_mode:
                # Fill rewrite form
                self.rewrite_id_entry.delete(0, 'end')
                self.rewrite_id_entry.insert(0, str(guest_id))
            elif self.checkin_buttons_visible:
                # Fill manual check-in form
                self.manual_id_entry.delete(0, 'end')
                self.manual_id_entry.insert(0, str(guest_id))

    def on_guest_select_direct(self, item):
        """Handle guest selection directly from item (without selection)."""
        if item:
            item_data = self.guest_tree.item(item)
            guest_id = item_data['values'][0]

            if self.is_registration_mode:
                # Fill registration form
                self.id_entry.delete(0, 'end')
                self.id_entry.insert(0, str(guest_id))
                # Trigger guest name display update
                self._on_guest_id_change()
                # Start 15-second auto-clear timer
                self._start_id_clear_timer()
            elif self.is_rewrite_mode:
                # Fill rewrite form
                self.rewrite_id_entry.delete(0, 'end')
                self.rewrite_id_entry.insert(0, str(guest_id))
            elif self.checkin_buttons_visible:
                # Fill manual check-in form
                self.manual_id_entry.delete(0, 'end')
                self.manual_id_entry.insert(0, str(guest_id))

    def exit_rewrite_mode(self):
        """Exit rewrite mode and return to station view."""
        # Cancel any ongoing operations first
        self.cancel_any_rewrite_operations()

        # Stop rewrite scanning
        self.is_scanning = False

        self.is_rewrite_mode = False
        self.settings_visible = False
        self._cancel_settings_timer()
        # Clear search field when closing settings
        self.clear_search()
        self.is_registration_mode = False  # All stations are checkpoint-only
        self.update_settings_button()
        self.update_mode_content()

        # Resume scanning if in checkpoint mode
        if not self.is_registration_mode or self.is_checkpoint_mode:
            self.start_checkpoint_scanning()

        # Restore operational status
        self._update_status_with_correct_type()

    def cancel_any_rewrite_operations(self):
        """Cancel any ongoing rewrite operations."""
        # Cancel rewrite operation
        if hasattr(self, '_rewrite_operation_active'):
            self._rewrite_operation_active = False
        if hasattr(self, 'nfc_service'):
            self.nfc_service.cancel_read()
        # Clean up UI if needed
        if hasattr(self, 'rewrite_cancel_btn'):
            self.rewrite_cancel_btn.destroy()
            delattr(self, 'rewrite_cancel_btn')

    def rewrite_to_band(self):
        """Handle rewrite to band action."""
        # Block if another operation is in progress
        if self.operation_in_progress:
            self.update_status("Please wait for current operation to complete", "warning")
            return
            
        guest_id = self.rewrite_id_entry.get().strip()

        if not guest_id:
            self.update_status(self.STATUS_PLEASE_ENTER_GUEST_ID, "error")
            return

        try:
            guest_id = int(guest_id)
        except ValueError:
            self.update_status(self.STATUS_INVALID_ID_FORMAT, "error")
            return
            
        # Set global NFC lock to prevent race conditions with background scanning
        self._nfc_operation_lock = True
        
        # Mark operation in progress to block background scanning
        self.operation_in_progress = True
        self._active_operations += 1

        # Disable UI during tag check
        self.safe_update_widget('rewrite_btn', lambda w: w.configure(state="disabled"))
        self.safe_update_widget('rewrite_id_entry', lambda w: w.configure(state="disabled"))
        # Exit button handled by red X settings button - no separate exit button needed

        # Cancel any ongoing NFC operations to prevent conflicts
        try:
            self.nfc_service.cancel_read()
        except Exception as e:
            self.logger.warning(f"Error cancelling NFC read before rewrite: {e}")

        # Start countdown and operation
        self._rewrite_check_operation_active = True
        self._countdown_rewrite_check(5)

        # Start tag check operation
        thread = threading.Thread(target=self._check_tag_registration_thread, args=(guest_id,))
        thread.daemon = True
        thread.start()

    def _countdown_rewrite_check(self, countdown: int):
        """Show countdown for register operation."""
        if countdown > 0 and self._rewrite_check_operation_active:
            self.update_status(f"Place tag on reader... {countdown}s", "warning", False)
            # Show cancel button during countdown
            self._show_cancel_register_button()
            # Store timer ID so it can be cancelled
            self._rewrite_countdown_timer = self.after(1000, lambda: self._countdown_rewrite_check(countdown - 1))
        elif self._rewrite_check_operation_active:
            # Timeout reached
            self._rewrite_check_operation_active = False
            self._rewrite_countdown_timer = None
            # Release global NFC lock on timeout
            self._nfc_operation_lock = False
            self.update_status("No tag detected. Try again.", "error")
            self._enable_rewrite_ui()
            self._hide_cancel_register_button()

    def _check_tag_registration_thread(self, guest_id: int):
        """Thread to check if tag is already registered."""
        try:
            # Read tag to check registration
            tag = self.nfc_service.read_tag(timeout=5)

            if not tag:
                # Only show error message if operation is still active (not cancelled)
                if self._rewrite_check_operation_active:
                    # Check what type of error occurred for better user feedback
                    error_type = self.nfc_service.get_last_error_type()
                    self.after(0, self._enable_rewrite_ui)
                    if error_type == 'timeout':
                        self.after(0, self.update_status, "No tag detected", "error")
                    elif error_type in ('connection_failed', 'read_failed'):
                        self.after(0, self.update_status, "Failed to read tag - try again", "error")
                    else:
                        self.after(0, self.update_status, "No tag detected", "error")
                else:
                    # Operation was cancelled - just clean up UI without showing error
                    self.after(0, self._enable_rewrite_ui)
                # Stop countdown and release operation lock on failure/cancellation
                self._rewrite_check_operation_active = False
                self.after(0, self._release_rewrite_lock)
                return

            # Check if tag is registered
            if tag.uid in self.tag_manager.tag_registry:
                # Tag is registered - get current guest info
                current_guest_id = self.tag_manager.tag_registry[tag.uid]
                self.logger.info(f"Tag {tag.uid} is registered to guest ID {current_guest_id}")

                # Check if it's the same guest
                if current_guest_id == guest_id:
                    # Same guest - just show message
                    current_guest = self.sheets_service.find_guest_by_id(current_guest_id)
                    guest_name = current_guest.full_name if current_guest else f"Guest ID {current_guest_id}"
                    # Operation complete - stop countdown
                    self._rewrite_check_operation_active = False
                    self.after(0, self._enable_rewrite_ui)
                    self.after(0, self.update_status, f"Tag already registered to {guest_name}", "warning")
                    self.after(0, self._release_rewrite_lock)
                    return

                # Different guest - show confirmation dialog
                current_guest = self.sheets_service.find_guest_by_id(current_guest_id)
                new_guest = self.sheets_service.find_guest_by_id(guest_id)

                current_name = current_guest.full_name if current_guest else f"Guest ID {current_guest_id}"
                new_name = new_guest.full_name if new_guest else f"Guest ID {guest_id}"

                # Operation proceeding to confirmation - stop countdown
                self._rewrite_check_operation_active = False
                # Show confirmation dialog
                self.after(0, self._show_rewrite_confirmation, current_name, new_name, guest_id, tag)
            else:
                # Tag is clean - proceed with direct write
                self.logger.info(f"Tag {tag.uid} is not registered - proceeding with direct write")
                # Operation proceeding to rewrite - stop countdown
                self._rewrite_check_operation_active = False
                self.after(0, self._proceed_with_direct_rewrite, guest_id, tag)

        except Exception as e:
            self.logger.error(f"Error checking tag registration: {e}", exc_info=True)
            self._rewrite_check_operation_active = False
            # Release global NFC lock on error
            self._nfc_operation_lock = False
            self.after(0, self._enable_rewrite_ui)
            self.after(0, self.update_status, "Error reading tag", "error")
            self.after(0, self._release_rewrite_lock)

    def _show_rewrite_confirmation(self, current_name: str, new_name: str, guest_id: int, tag):
        """Show confirmation dialog for rewriting a registered tag."""
        # Re-enable UI first
        self._enable_rewrite_ui()

        # Create confirmation dialog
        confirm_window = self._create_themed_toplevel()
        confirm_window.title("Confirm Rewrite")
        confirm_window.geometry("450x350")
        confirm_window.transient(self)
        confirm_window.grab_set()

        # Center window
        confirm_window.update_idletasks()
        x = (confirm_window.winfo_screenwidth() // 2) - 225
        y = (confirm_window.winfo_screenheight() // 2) - 175
        confirm_window.geometry(f"+{x}+{y}")

        # Main frame
        main_frame = ctk.CTkFrame(confirm_window)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Title
        title_label = ctk.CTkLabel(
            main_frame,
            text="Tag Already Registered",
            font=CTkFont(size=22, weight="bold")
        )
        title_label.pack(pady=(10, 25))

        # Current registration info
        current_label = ctk.CTkLabel(
            main_frame,
            text=f"Currently registered to:\n{current_name}",
            font=CTkFont(size=16),
            justify="center"
        )
        current_label.pack(pady=(0, 15))

        # Arrow
        arrow_label = ctk.CTkLabel(
            main_frame,
            text="↓",
            font=CTkFont(size=28)
        )
        arrow_label.pack(pady=10)

        # New registration info
        new_label = ctk.CTkLabel(
            main_frame,
            text=f"Will be rewritten to:\n{new_name}",
            font=CTkFont(size=16, weight="bold"),
            text_color="#4CAF50",
            justify="center"
        )
        new_label.pack(pady=(0, 35))

        # Buttons
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack()

        def proceed_with_rewrite():
            """Proceed with rewrite using the already-detected tag."""
            self.logger.info(f"User confirmed rewrite for guest ID {guest_id}")
            confirm_window.destroy()
            self.update_status("Rewriting tag...", "info")
            self.rewrite_btn.configure(state="disabled")
            self.rewrite_id_entry.configure(state="disabled")
            # Exit button handled by red X settings button - no separate exit button needed

            # Execute rewrite in background thread
            thread = threading.Thread(target=self._execute_rewrite_thread, args=(guest_id, tag))
            thread.daemon = True
            thread.start()

        rewrite_btn = ctk.CTkButton(
            button_frame,
            text="Rewrite",
            command=proceed_with_rewrite,
            width=120,
            height=45,
            font=self.fonts['button'],
            border_width=2,
            fg_color="transparent",
            text_color="#ff9800",
            border_color="#ff9800"
        )
        
        # Add hover effects for Rewrite button  
        def on_rewrite_confirm_enter(event):
            rewrite_btn.configure(
                fg_color="#ff9800",
                text_color="#212121"
            )
            
        def on_rewrite_confirm_leave(event):
            rewrite_btn.configure(
                fg_color="transparent",
                text_color="#ff9800"
            )
            
        rewrite_btn.bind("<Enter>", on_rewrite_confirm_enter)
        rewrite_btn.bind("<Leave>", on_rewrite_confirm_leave)
        rewrite_btn.pack(side="left", padx=10)

        def cancel_rewrite():
            """Cancel rewrite and clear guest ID field."""
            confirm_window.destroy()
            # Clear the guest ID field
            self.rewrite_id_entry.delete(0, 'end')
            # Release operation lock on cancel
            self._release_rewrite_lock()

        cancel_btn = ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=cancel_rewrite,
            width=120,
            height=45,
            font=self.fonts['button'],
            border_width=2,
            fg_color="transparent",
            text_color="#6c757d",
            border_color="#6c757d"
        )
        
        # Add hover effects for Cancel rewrite button
        def on_cancel_rewrite_enter(event):
            cancel_btn.configure(
                fg_color="#6c757d",
                text_color="#ffffff"
            )
            
        def on_cancel_rewrite_leave(event):
            cancel_btn.configure(
                fg_color="transparent",
                text_color="#6c757d"
            )
            
        cancel_btn.bind("<Enter>", on_cancel_rewrite_enter)
        cancel_btn.bind("<Leave>", on_cancel_rewrite_leave)
        cancel_btn.pack(side="left", padx=10)

    def _proceed_with_direct_rewrite(self, guest_id: int, tag):
        """Proceed with direct rewrite for clean tags."""
        self.update_status("Writing to tag...", "info")

        # Execute rewrite using the already-detected tag
        thread = threading.Thread(target=self._execute_rewrite_thread, args=(guest_id, tag))
        thread.daemon = True
        thread.start()

    def _execute_rewrite_thread(self, guest_id: int, tag):
        """Execute the actual rewrite operation."""
        try:
            self.logger.info(f"Executing rewrite for guest ID {guest_id} with tag {tag.uid}")

            # Verify guest exists
            guest = self.sheets_service.find_guest_by_id(guest_id)
            if not guest:
                self.after(0, self._rewrite_complete, None)
                self.after(0, self.update_status, f"Guest ID {guest_id} not found", "error")
                return

            # Clear existing registration if any
            if tag.uid in self.tag_manager.tag_registry:
                existing_id = self.tag_manager.tag_registry[tag.uid]
                existing_guest = self.sheets_service.find_guest_by_id(existing_id)
                existing_name = existing_guest.full_name if existing_guest else f"ID {existing_id}"
                self.logger.info(f"Overwriting tag {tag.uid} from {existing_name} to {guest.full_name}")

            # Register the tag locally first
            tag.register_to_guest(guest_id, guest.full_name)
            self.tag_manager.tag_registry[tag.uid] = guest_id
            self.tag_manager.save_registry()

            # Create result dict for immediate UI update
            result = {
                'tag_uid': tag.uid,
                'original_id': guest_id,
                'guest_name': guest.full_name,
                'registered_at': datetime.now().isoformat(),
                'action': 'rewrite'
            }

            # Update local data immediately for instant feedback
            self.after(0, lambda: self._update_local_guest_wristband_and_complete(guest_id, tag.uid, result))

            # Background Google Sheets write (non-blocking)
            self.submit_background_task(self._background_wristband_write, guest_id, tag.uid)

            self.logger.info(f"Rewrite successful: {result}")

        except Exception as e:
            self.logger.error(f"Rewrite operation error: {e}", exc_info=True)
            self.after(0, self._rewrite_complete, None)

    def _background_wristband_write(self, guest_id: int, tag_uid: str):
        """Background task to write wristband UUID to Google Sheets."""
        try:
            success = self.sheets_service.write_wristband_uuid(guest_id, tag_uid)
            if success:
                self.logger.info(f"Background sync: Successfully wrote wristband UUID {tag_uid} to Google Sheets for guest {guest_id}")
            else:
                self.logger.warning(f"Background sync: Failed to write wristband UUID to Google Sheets for guest {guest_id}")
        except Exception as sheets_error:
            self.logger.error(f"Background sync: Error writing wristband UUID to Google Sheets: {sheets_error}")

    def _rewrite_complete(self, result: Optional[Dict]):
        """Handle rewrite completion."""
        # Cancel any countdown timer
        if self._rewrite_countdown_timer:
            self.after_cancel(self._rewrite_countdown_timer)
            self._rewrite_countdown_timer = None
        self._rewrite_check_operation_active = False
        self._hide_cancel_register_button()
        
        self._enable_rewrite_ui()

        if result:
            self.update_status(f"✓ Tag registered to {result['guest_name']}", "success")
            
            # Local data and UI are updated immediately by _execute_rewrite_thread
            # No need for delayed refresh since background sync handles Google Sheets
            
            self.after(2000, self.clear_rewrite_form)
        else:
            if self.status_label.cget("text") == "Registering tag...":
                self.update_status("Failed to register tag", "error")

        self.rewrite_id_entry.focus()

    def _update_local_guest_wristband(self, guest_id: int, wristband_uuid: str):
        """Update local guest data to reflect wristband registration."""
        try:
            # Find the guest in local data and update wristband_uuid
            for guest in self.guests_data:
                if guest.original_id == guest_id:
                    guest.wristband_uuid = wristband_uuid
                    self.logger.debug(f"Updated local guest data: Guest {guest_id} now has wristband {wristband_uuid}")
                    break
            
            # Immediately refresh the table to show the checkmark and green highlighting
            if hasattr(self, 'guests_data') and self.guests_data:
                self._update_guest_table_silent(self.guests_data)
                
        except Exception as e:
            self.logger.error(f"Error updating local guest wristband data: {e}")

    def _update_local_guest_wristband_and_complete(self, guest_id: int, wristband_uuid: str, result: dict):
        """Update local wristband data then complete the rewrite operation."""
        try:
            # First update the local data
            self._update_local_guest_wristband(guest_id, wristband_uuid)
            # Then complete the rewrite operation
            self._rewrite_complete(result)
        except Exception as e:
            self.logger.error(f"Error in wristband update and complete: {e}")
            self._rewrite_complete(None)

    def clear_rewrite_form(self):
        """Clear the register form."""
        self.safe_update_widget('rewrite_id_entry', lambda w: w.delete(0, 'end'))
        # Keep status bar clear in rewrite mode - "Check-in Paused" shown in stations frame
        self.update_status("", "normal")

    def close_register_mode(self):
        """Close register mode and return to main station."""
        self.is_rewrite_mode = False
        self.is_checkpoint_mode = True   # Re-enable checkpoint mode for background scanning
        
        # Update UI to show station buttons and normal hamburger menu
        self.update_settings_button()
        self.update_station_buttons_visibility()
        
        # Update content to show normal station view
        self.update_mode_content()
        
        # Restore table structure for normal mode (same as station toggle)
        self._update_table_structure()
        
        # Refresh table data
        if hasattr(self, 'guests_data') and self.guests_data:
            self._update_guest_table_silent(self.guests_data)
        
        # Return to checkpoint scanning if NFC is connected
        if self._nfc_connected and not self.is_scanning:
            self.start_checkpoint_scanning()

    def cancel_register_operation(self):
        """Cancel the register operation countdown."""
        if self._rewrite_check_operation_active:
            # Cancel the countdown timer
            if self._rewrite_countdown_timer:
                self.after_cancel(self._rewrite_countdown_timer)
                self._rewrite_countdown_timer = None
            
            # Stop the operation
            self._rewrite_check_operation_active = False
            
            # Release any locks
            if self._nfc_operation_lock:
                self._nfc_operation_lock = False
                
            # Cancel any ongoing NFC operation
            try:
                self.nfc_service.cancel_read()
            except Exception as e:
                self.logger.debug(f"Error canceling NFC read during registration cancel: {e}")
            
            # Update UI - show brief cancellation message then clear
            self.update_status("Registration cancelled", "info")
            # Clear status after 2 seconds to keep status bar clean in rewrite mode
            self.after(2000, lambda: self.update_status("", "normal"))
            self._enable_rewrite_ui()
            self._hide_cancel_register_button()

    def _show_cancel_register_button(self):
        """Show the cancel button during register operation countdown."""
        if hasattr(self, 'cancel_register_btn'):
            self.cancel_register_btn.pack(side="left", padx=(10, 0))

    def _hide_cancel_register_button(self):
        """Hide the cancel button after register operation."""
        if hasattr(self, 'cancel_register_btn'):
            self.cancel_register_btn.pack_forget()

    def _enable_rewrite_ui(self):
        """Re-enable register UI elements."""
        # Reset countdown operation flag and clear timer
        self._rewrite_check_operation_active = False
        if self._rewrite_countdown_timer:
            self.after_cancel(self._rewrite_countdown_timer)
            self._rewrite_countdown_timer = None

        self.safe_update_widget('rewrite_btn', lambda w: w.configure(state="normal"))
        self.safe_update_widget('rewrite_id_entry', lambda w: w.configure(state="normal"))
        self._hide_cancel_register_button()
        
        # Release the rewrite operation lock
        self._release_rewrite_lock()
            
    def _release_rewrite_lock(self):
        """Release the rewrite operation lock."""
        self.operation_in_progress = False
        self._active_operations -= 1
        # Release global NFC lock
        self._nfc_operation_lock = False

    def on_tree_motion(self, event):
        """Handle mouse motion over tree for cursor changes, hover styling, and phone tooltips."""
        
        # Check if mouse is over header area - if so, skip all hover effects
        region = self.guest_tree.identify("region", event.x, event.y)
        if region == "heading":
            # Clear any existing hover and tooltip when over headers
            self._clear_tooltip()
            if self.hovered_item:
                try:
                    current_tags = list(self.guest_tree.item(self.hovered_item, "tags"))
                    if "checkin_hover" in current_tags:
                        current_tags.remove("checkin_hover")
                        self.guest_tree.item(self.hovered_item, tags=current_tags)
                except tk.TclError:
                    pass
                self.hovered_item = None
            return
        
        # Get the item and column under mouse
        item = self.guest_tree.identify("item", event.x, event.y)
        column = self.guest_tree.identify("column", event.x, event.y)

        # Handle tooltip logic first
        self._handle_tooltip_motion(item, column, event.x, event.y)

        # Check if hovering over check-in button in any station column (manual check-in mode)
        if self.checkin_buttons_visible and item and column:
            column_index = int(column.replace('#', '')) - 1
            # Station columns start at index 3 (after id, first, last)
            # Get dynamic stations for current view
            try:
                available_stations = self._get_filtered_stations_for_view()
            except:
                available_stations = self.config['stations']
                
            if column_index >= 3 and column_index < 3 + len(available_stations):
                values = self.guest_tree.item(item, "values")
                if len(values) > column_index and values[column_index] == "Check-in":
                    # Clear previous hover
                    if self.hovered_item:
                        try:
                            current_tags = list(self.guest_tree.item(self.hovered_item, "tags"))
                            if "checkin_hover" in current_tags:
                                current_tags.remove("checkin_hover")
                                self.guest_tree.item(self.hovered_item, tags=current_tags)
                        except tk.TclError:
                            pass
                    
                    # Apply hover styling to check-in button
                    current_tags = list(self.guest_tree.item(item, "tags"))
                    if "checkin_hover" not in current_tags:
                        current_tags.append("checkin_hover")
                        self.guest_tree.item(item, tags=current_tags)
                    self.hovered_item = item

                    # Set hand cursor
                    self.guest_tree.configure(cursor="hand2")
                    return
        
        # For all other cases (normal mode or not over check-in button), use the streamlined hover
        self._update_hover(event)
        
        # Reset cursor
        self.guest_tree.configure(cursor="")

    def on_tree_leave(self, event):
        """Clear hover effect when the mouse leaves the Treeview."""
        self._clear_tooltip()
        
        # Clear hover styling when mouse leaves tree
        if self.hovered_item:
            try:
                current_tags = list(self.guest_tree.item(self.hovered_item, "tags"))
                if "checkin_hover" in current_tags:
                    current_tags.remove("checkin_hover")
                    self.guest_tree.item(self.hovered_item, tags=current_tags)
            except tk.TclError:
                pass  # Item was already removed
            self.hovered_item = None

    def _update_hover(self, event):
        """A single method to handle all hover effect updates."""
        # Check if mouse is over header area - if so, don't apply hover
        region = self.guest_tree.identify("region", event.x, event.y)
        if region == "heading":
            # Mouse is over header, don't apply hover effects
            if self.hovered_item:
                # Clear any existing hover
                try:
                    current_tags = list(self.guest_tree.item(self.hovered_item, "tags"))
                    if "checkin_hover" in current_tags:
                        current_tags.remove("checkin_hover")
                        self.guest_tree.item(self.hovered_item, tags=current_tags)
                except tk.TclError:
                    pass
                self.hovered_item = None
            return
        
        # Get the item under the cursor directly
        item = self.guest_tree.identify_row(event.y)

        # If the hovered item has changed since the last event, update the styling
        if item != self.hovered_item:
            # First, remove the hover tag from the previously hovered item (if any)
            if self.hovered_item:
                try:
                    current_tags = list(self.guest_tree.item(self.hovered_item, "tags"))
                    if "checkin_hover" in current_tags:
                        current_tags.remove("checkin_hover")
                        self.guest_tree.item(self.hovered_item, tags=current_tags)
                except tk.TclError:
                    # This can happen if a refresh occurs while hovered
                    pass

            # Now, apply the hover tag to the new item
            if item:
                # In normal mode, apply hover to any row
                # In manual check-in mode, the motion handler handles button-specific hover
                if not self.checkin_buttons_visible:
                    current_tags = list(self.guest_tree.item(item, "tags"))
                    if "checkin_hover" not in current_tags:
                        current_tags.append("checkin_hover")
                        self.guest_tree.item(item, tags=current_tags)

            # Update the reference to the currently hovered item
            self.hovered_item = item


    def _on_scroll(self, event):
        """Handle scroll events by updating hover at current mouse position."""
        # Clear any pending tooltip first since content has moved under mouse
        self._clear_tooltip()
        
        # Use a very short delay to allow the treeview to process the scroll
        # before we update the hover. This prevents lag and inaccuracy.
        if hasattr(self, '_scroll_hover_job'):
            self.after_cancel(self._scroll_hover_job)
        
        self._scroll_hover_job = self.after(1, self._update_hover_on_scroll)
    
    def _update_hover_on_scroll(self):
        """Update the hover effect after a scroll event."""
        try:
            # Get mouse position relative to the Treeview
            x = self.guest_tree.winfo_pointerx() - self.guest_tree.winfo_rootx()
            y = self.guest_tree.winfo_pointery() - self.guest_tree.winfo_rooty()

            # Identify the item directly under the cursor
            new_item = self.guest_tree.identify_row(y)

            # Update styling if the hovered item has changed
            if new_item != self.hovered_item:
                # Remove hover from the old item
                if self.hovered_item:
                    try:
                        tags = list(self.guest_tree.item(self.hovered_item, "tags"))
                        if "checkin_hover" in tags:
                            tags.remove("checkin_hover")
                            self.guest_tree.item(self.hovered_item, tags=tags)
                    except tk.TclError:
                        pass  # Item might have been deleted

                # Apply hover to the new item
                if new_item:
                    try:
                        # Only apply hover if not in manual check-in mode,
                        # as that mode has its own button-specific hover.
                        if not self.checkin_buttons_visible:
                            tags = list(self.guest_tree.item(new_item, "tags"))
                            if "checkin_hover" not in tags:
                                tags.append("checkin_hover")
                                self.guest_tree.item(new_item, tags=tags)
                    except tk.TclError:
                        pass # Item might have been deleted during a refresh

                self.hovered_item = new_item
                
            # Also re-evaluate tooltip for the new position after scroll
            if new_item:
                column = self.guest_tree.identify_column(x)
                self._handle_tooltip_motion(new_item, column, x, y)
        except Exception:
            # Fail silently if coordinates are invalid during rapid scrolling
            pass

    def _handle_tooltip_motion(self, item, column, x, y):
        """Handle tooltip logic during mouse motion."""
        # Skip if no item
        if not item:
            self._clear_tooltip()
            return
            
        # Skip tooltips when manual check-in mode is active
        if self.checkin_buttons_visible:
            self._clear_tooltip()
            return
            
        # Check if we're hovering over the same item and column
        if item == self._tooltip_item and column == self._tooltip_column:
            return  # Already processing this tooltip
            
        # Clear existing tooltip and timer
        self._clear_tooltip()
        
        # Start new tooltip timer for 2-second delay
        self._tooltip_item = item
        self._tooltip_column = column
        self._tooltip_timer = self.after(2000, lambda: self._show_phone_tooltip(item, x, y))

    def _clear_tooltip(self):
        """Clear any active tooltip timer or window."""
        if self._tooltip_timer:
            self.after_cancel(self._tooltip_timer)
            self._tooltip_timer = None
            
        if self._tooltip_window:
            self._tooltip_window.destroy()
            self._tooltip_window = None
            
        self._tooltip_item = None
        self._tooltip_column = None

    def _show_phone_tooltip(self, item, x, y):
        """Show phone number tooltip for the given item."""
        try:
            values = self.guest_tree.item(item, "values")
            if not values or len(values) < 3:
                return
                
            guest_id = int(values[0])
            
            # Find the guest in our data
            guest = None
            if hasattr(self, 'guests_data'):
                for g in self.guests_data:
                    if g.original_id == guest_id:
                        guest = g
                        break
                        
            if not guest:
                return
                
            # Get formatted phone number
            phone_text = guest.get_formatted_phone()
            
            # Create tooltip window
            self._tooltip_window = tk.Toplevel(self)
            self._tooltip_window.wm_overrideredirect(True)
            self._tooltip_window.wm_attributes("-topmost", True)
            
            # Position tooltip near mouse cursor (using TreeView's position)
            tree_x = self.guest_tree.winfo_rootx()
            tree_y = self.guest_tree.winfo_rooty()
            tooltip_x = tree_x + x + 10
            tooltip_y = tree_y + y + 10
            self._tooltip_window.wm_geometry(f"+{tooltip_x}+{tooltip_y}")
            
            # Create tooltip label with theme-appropriate styling
            if hasattr(self, 'current_theme') and self.current_theme == 'dark':
                bg_color = "#2b2b2b"
                fg_color = "#ffffff"
            else:
                bg_color = "#f8f9fa"
                fg_color = "#212121"
            
            label = tk.Label(
                self._tooltip_window,
                text=phone_text,
                background=bg_color,
                foreground=fg_color,
                relief="flat",
                borderwidth=0,
                font=("Arial", 30),
                padx=12,
                pady=6
            )
            label.pack()
            
        except Exception as e:
            self.logger.debug(f"Error showing phone tooltip: {e}")
            self._clear_tooltip()

    def on_tree_click(self, event):
        """Handle click on tree for check-in button and closing edit."""
        # First, check if we're editing and should save/close
        if self.edit_entry:
            # Get the clicked position
            clicked_item = self.guest_tree.identify("item", event.x, event.y)
            clicked_column = self.guest_tree.identify("column", event.x, event.y)
            
            # If clicking outside the currently edited cell, save and close
            if clicked_item != self.edit_item or clicked_column != f"#{self.edit_column + 1}":
                self.save_edit()
                # Don't process this click further if we were editing
                return
        
        # Identify the clicked region
        region = self.guest_tree.identify("region", event.x, event.y)
        if region != "cell":
            return

        # Get the clicked item and column
        item = self.guest_tree.identify("item", event.x, event.y)
        column = self.guest_tree.identify("column", event.x, event.y)

        if not item or not column:
            return

        column_index = int(column.replace('#', '')) - 1
        values = self.guest_tree.item(item, "values")
        
        # Station columns start at index 3 (after id, first, last)
        # Get dynamic stations for current view
        try:
            available_stations = self._get_filtered_stations_for_view()
        except:
            available_stations = self.config['stations']
            
        if column_index >= 3 and column_index < 3 + len(available_stations):
            # Only proceed if it says "Check-in"
            if len(values) > column_index and values[column_index] == "Check-in":
                guest_id = int(values[0])  # Ensure guest_id is int
                station = available_stations[column_index - 3]

                # Provide immediate visual feedback in cell
                import datetime
                timestamp = datetime.datetime.now().strftime("%H:%M")
                item_values = list(values)
                item_values[column_index] = f"✓ {timestamp} ⏳"
                self.guest_tree.item(item, values=item_values)

                # Update row styling immediately
                self._update_row_styling(item, guest_id)
                
                # Update summary row immediately to reflect the change
                self._update_summary_row_immediate()

                # Disable the click temporarily to prevent double-clicks
                self.guest_tree.configure(cursor="wait")
                self.after(1000, lambda: self.guest_tree.configure(cursor=""))

                self.quick_checkin(guest_id, station)

    def quick_checkin(self, guest_id, station=None):
        """Perform quick check-in for a guest at specific station."""
        # Block if another operation is in progress
        if self.operation_in_progress:
            self.update_status("Please wait for current operation to complete", "warning")
            return
            
        if station is None:
            station = self.current_station

        # Mark operation in progress
        self.operation_in_progress = True
        self._active_operations += 1
        
        # Log user action
        self.logger.info(f"User manually checked in guest {guest_id} at {station}")
        
        # Update status
        self.update_status(f"Checking in guest {guest_id} at {station}...", "info")

        # Run in thread
        thread = threading.Thread(target=self._quick_checkin_thread,
                                args=(guest_id, station))
        thread.daemon = True
        thread.start()

    def _quick_checkin_thread(self, guest_id: int, station: str):
        """Thread function for quick check-in."""
        try:
            # Use tag manager for manual check-in (uses local queue)
            result = self.tag_manager.manual_check_in(guest_id, station)

            if result:
                self.after(0, self.update_status, f"✓ Checked in {result['guest_name']} at {station}", "success")
                # Auto-close manual check-in mode after successful check-in
                if self.checkin_buttons_visible:
                    self.after(0, self.toggle_manual_checkin)
                # Delay refresh to ensure status is visible for minimum 2s
                self.after(2500, lambda: self.refresh_guest_data(user_initiated=False))
            else:
                self.after(0, self.update_status, f"Guest ID {guest_id} not found", "error")
        except Exception as e:
            self.logger.error(f"Manual check-in error: {e}")
            self.after(0, self.update_status, f"Check-in failed: {str(e)}", "error")
        finally:
            # Always release operation lock
            self.operation_in_progress = False
            self._active_operations -= 1

    def _force_sync_on_startup(self):
        """Force sync of pending items found at startup."""
        thread = threading.Thread(target=self._force_sync_thread)
        thread.daemon = True
        thread.start()

    def _force_sync_thread(self):
        """Background thread to force sync pending items."""
        try:
            # Trigger sync process
            self.tag_manager.force_sync_all_pending()
            # Refresh after sync
            self.after(2000, lambda: self.refresh_guest_data(user_initiated=False))
        except Exception as e:
            self.logger.error(f"Error in force sync: {e}")

    def update_status(self, message: str, status_type: str = "normal", auto_clear: bool = True):
        """Update status bar."""
        # Stop any existing NFC blinking
        if hasattr(self, '_nfc_blink_job') and self._nfc_blink_job is not None:
            try:
                self.after_cancel(self._nfc_blink_job)
            except ValueError:
                # Timer already expired or invalid
                pass
            self._nfc_blink_job = None
            
        # Check if this is the NFC not connected message
        if message == self.STATUS_NFC_NOT_CONNECTED:
            self._start_nfc_blink(message, status_type)
            return
            
        # Theme-aware color mapping
        if self.is_light_mode:
            color_map = {
                "normal": "#212529",  # Dark text for light mode
                "success": "#4CAF50",
                "error": "#f44336",
                "warning": "#ff9800",
                "info": "#2196F3"
            }
        else:
            color_map = {
                "normal": "#ffffff",  # White text for dark mode
                "success": "#4CAF50",
                "error": "#f44336",
                "warning": "#ff9800",
                "info": "#2196F3"
            }
        color = color_map.get(status_type, "#ffffff")
        self.safe_update_widget(
            'status_label',
            lambda w, text, tc: w.configure(text=text, text_color=tc),
            message, color
        )

        # Auto-clear all messages after 2 seconds (except empty messages)
        if auto_clear and message and message.strip():
            self.after(2000, lambda: self._auto_clear_status(message))

    def _start_nfc_blink(self, message: str, status_type: str):
        """Start blinking animation for NFC not connected status."""
        # Get the error color for when text is visible
        if self.is_light_mode:
            error_color = "#f44336"
        else:
            error_color = "#f44336"
            
        self._nfc_blink_state = True  # True = show text, False = hide text
        self._nfc_blink_message = message
        self._nfc_error_color = error_color
        self._do_nfc_blink()
    
    def _do_nfc_blink(self):
        """Perform one blink cycle."""
        if not hasattr(self, '_nfc_blink_message'):
            return
            
        if self._nfc_blink_state:
            # Show the full message with error color
            self.safe_update_widget(
                'status_label',
                lambda w, text, tc: w.configure(text=text, text_color=tc),
                self._nfc_blink_message, self._nfc_error_color
            )
        else:
            # Hide the text completely (empty string)
            self.safe_update_widget(
                'status_label',
                lambda w: w.configure(text=""),
            )
        
        # Toggle state and schedule next blink
        self._nfc_blink_state = not self._nfc_blink_state
        self._nfc_blink_job = self.after(800, self._do_nfc_blink)  # Blink every 800ms

    def _auto_clear_status(self, original_message: str):
        """Auto-clear status if it hasn't changed."""
        current_text = self.status_label.cget("text")
        if current_text == original_message:
            # Determine appropriate replacement message based on current mode
            if not self._nfc_connected:
                # Always show NFC disconnected message when not connected
                self.update_status(self.STATUS_NFC_NOT_CONNECTED, "error", False)
            elif self.is_rewrite_mode:
                # Clear message in rewrite mode - "Check-in Paused" shown in stations frame only
                self.update_status("", "normal", False)
            elif self.settings_visible:
                # Clear message in settings mode
                self.update_status("", "normal", False)
            else:
                # Use appropriate ready message for current mode
                message = self.get_ready_status_message()
                if message == self.STATUS_NFC_NOT_CONNECTED:
                    self.update_status(message, "error", False)
                else:
                    self.update_status(message, "normal", False)

    def load_logo(self):
        """Load and display PNG logo with high-quality scaling."""
        try:
            logo_path = Path(__file__).parent.parent.parent / "assets" / "logo.png"
            if logo_path.exists():
                self.original_logo_image = Image.open(logo_path)
                # Clean downscale from 140x140 to 70x70 (2:1 ratio for crisp results)
                logo_image = self.original_logo_image.resize((70, 70), Image.Resampling.LANCZOS)
                logo_ctk = ctk.CTkImage(light_image=logo_image, dark_image=logo_image, size=(70, 70))
                self.logo_label.configure(image=logo_ctk)
                self.logo_label.image = logo_ctk
                
                # Store original for animations
                self.original_logo_image = self.original_logo_image.resize((70, 70), Image.Resampling.LANCZOS)
                self.logo_spinning = False
        except Exception as e:
            self.logger.error(f"Failed to load logo: {e}")

    def on_logo_click(self, event):
        """Easter egg: spin the logo when clicked, then refresh data."""
        # Check cooldowns - only allow if not spinning and refresh cooldown has passed
        current_time = time.time()
        
        # Check refresh cooldown (3 seconds)
        if hasattr(self, '_logo_refresh_last_time'):
            if current_time - self._logo_refresh_last_time < 3.0:
                return  # Still in cooldown
        
        # Only allow clicking when not spinning
        if not hasattr(self, 'logo_spinning') or not self.logo_spinning:
            # Start spin animation
            self.spin_logo()
            # Trigger refresh after animation completes (1000ms + 100ms buffer)
            self.after(1100, lambda: self.refresh_guest_data(user_initiated=True))
            # Set refresh cooldown
            self._logo_refresh_last_time = current_time

    def spin_logo(self):
        """Animate the logo with a smooth spin effect."""
        if not hasattr(self, 'original_logo_image') or self.original_logo_image is None:
            return
            
        self.logo_spinning = True
        duration_ms = 1000  # Total animation time
        total_frames = 30   # Smooth animation with better timing
        degrees_per_frame = 360 / total_frames
        
        def animate_frame(frame):
            if frame >= total_frames:
                # Animation complete, start 500ms cooldown period
                self.after(500, lambda: setattr(self, 'logo_spinning', False))
                return
                
            # Ease-in-out function for smooth animation
            t = frame / total_frames
            eased_t = t * t * (3 - 2 * t)  # Smoothstep function
            
            # Calculate rotation angle with easing
            angle = eased_t * 360
            
            try:
                # Rotate the image
                rotated_image = self.original_logo_image.rotate(angle, resample=Image.Resampling.BICUBIC, expand=False)
                
                # Convert to CTkImage and update
                logo_ctk = ctk.CTkImage(light_image=rotated_image, dark_image=rotated_image, size=(70, 70))
                self.logo_label.configure(image=logo_ctk)
                self.logo_label.image = logo_ctk
                
                # Schedule next frame
                self.after(duration_ms // total_frames, lambda: animate_frame(frame + 1))
            except Exception as e:
                self.logger.debug(f"Logo animation frame error: {e}")
                self.logo_spinning = False
        
        # Start animation
        animate_frame(0)


    def on_escape_key(self, event):
        """Handle ESC key to close dialogs following state management patterns."""
        
        # Always clear tooltips when ESC is pressed
        self._clear_tooltip()
        
        # Check current dialog state and call appropriate close function
        
        # 1. Tag info display - ALWAYS return to station view
        if hasattr(self, '_tag_info_auto_close_active') and self._tag_info_auto_close_active:
            self.close_tag_info()
            return "break"
        
        # 2. Write to tag operation in reception - cancel the write (red Cancel button)
        if (hasattr(self, '_write_operation_active') and self._write_operation_active and 
            hasattr(self, 'write_cancel_btn') and self.write_cancel_btn.winfo_exists()):
            # ESC does same as clicking the red Cancel button
            self.cancel_write()
            return "break"
        
        # 3. Never interrupt other active NFC operations (but allow write cancellation above)
        if hasattr(self, 'operation_in_progress') and self.operation_in_progress:
            return "break"
        
        # 4. Rewrite mode - return to Reception checkpoint
        if hasattr(self, 'is_rewrite_mode') and self.is_rewrite_mode:
            self.exit_rewrite_mode()
            return "break"
        
        # 5. Settings panel - return to previous station
        if hasattr(self, 'settings_visible') and self.settings_visible:
            self.toggle_settings()
            return "break"
        
        # 6. Skip ESC handling if log or developer window is open
        try:
            # Check all toplevel windows (CTkToplevel for log/developer dialogs)
            for toplevel in self.winfo_toplevel().children:
                widget = self.nametowidget(toplevel)
                if isinstance(widget, ctk.CTkToplevel):
                    # Log or developer window is open - skip ESC handling
                    # Let the dialog handle ESC natively (for text input, etc.)
                    return
        except:
            pass
        
        # 7. Manual check-in mode (if the state tracking exists)
        if hasattr(self, 'checkin_buttons_visible') and getattr(self, 'checkin_buttons_visible', False):
            # Manual check-in is active - exit it
            if hasattr(self, 'toggle_manual_checkin'):
                self.toggle_manual_checkin()
                return "break"
        
        # For any other ESC usage, don't prevent default behavior
        return

    def on_closing(self):
        """Handle window closing."""
        self.is_scanning = False
        # Release any global locks
        self._nfc_operation_lock = False
        if self.nfc_service:
            self.nfc_service.disconnect()
        self.destroy()


def create_gui(config, nfc_service, sheets_service, tag_manager, logger):
    """Create and run the GUI application."""
    app = NFCApp(config, nfc_service, sheets_service, tag_manager, logger)
    return app
