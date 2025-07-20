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
from PIL import Image
import os
import platform
from pathlib import Path

# Configure CustomTkinter
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


class NFCApp(ctk.CTk):
    """Main application window."""

    # Status message constants
    STATUS_READY_REGISTRATION = "Ready. Waiting for registration"
    STATUS_READY_CHECKIN = "Ready. Waiting for tap"
    STATUS_CHECKIN_PAUSED = "Check-In Paused"

    def __init__(self, config: dict, nfc_service, sheets_service, tag_manager, logger):
        super().__init__()

        self.config = config
        self.nfc_service = nfc_service
        self.sheets_service = sheets_service
        self.tag_manager = tag_manager
        self.logger = logger

        # State
        self.current_station = "Reception"
        self.is_registration_mode = True
        self.is_checkpoint_mode = False  # New state for Reception checkpoint scanning
        self.guest_list_visible = False
        self.checkin_buttons_visible = False  # Hidden by default
        self.settings_visible = False  # Settings panel visibility
        self.is_rewrite_mode = False  # Rewrite tag mode
        self.guests_data = []
        self.is_scanning = False
        self.erase_confirmation_state = False  # Track erase button confirmation state

        # Sorting state - default to Last Name A-Z
        self.current_sort_column = "last"
        self.current_sort_reverse = False

        # Track hovered item for styling
        self.hovered_item = None

        # Operation tracking
        self.operation_in_progress = False
        self.last_sync_count = 0
        self._active_operations = 0  # Track active operations
        self.is_refreshing = False  # Flag to prevent concurrent refreshes
        self._rewrite_check_operation_active = False  # Track rewrite countdown operation

        # Tag info display state
        self.is_displaying_tag_info = False
        self.tag_info_data = None

        # Window setup
        self.title(config['ui']['window_title'])
        self.geometry(f"{config['ui']['window_width']}x{config['ui']['window_height']}")
        self.minsize(500, 400)

        # Platform-specific fullscreen implementation
        self.setup_fullscreen()

        # Center window (fallback if fullscreen doesn't work)
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (self.winfo_width() // 2)
        y = (self.winfo_screenheight() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")

        # Setup UI
        self.setup_styles()
        self.create_widgets()
        self.load_logo()

        # Load initial data
        self.after(100, lambda: self.refresh_guest_data(user_initiated=False))

        # Set up sync completion callback to update UI when background syncs complete
        self.tag_manager.set_sync_completion_callback(self.on_sync_complete)

        # Handle window close
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def get_ready_status_message(self):
        """Get the appropriate ready status message based on current mode."""
        if self.current_station == "Reception" and self.is_registration_mode and not self.is_checkpoint_mode:
            return self.STATUS_READY_REGISTRATION
        else:
            return self.STATUS_READY_CHECKIN

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
        """Set window to normal size."""
        width = self.config['ui']['window_width']
        height = self.config['ui']['window_height']
        self.geometry(f"{width}x{height}")
        self.logger.info(f"Window set to normal size: {width}x{height}")

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
            'status': CTkFont(size=16),
            'button': CTkFont(size=14, weight="bold")
        }

    def create_widgets(self):
        """Create all UI widgets."""
        # Main container with padding
        self.main_frame = ctk.CTkFrame(self, corner_radius=0)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Header frame
        self.create_header()

        # Content frame (compact size)
        self.content_frame = ctk.CTkFrame(self.main_frame, corner_radius=15, height=200)
        self.content_frame.pack(fill="x", pady=(20, 10))
        self.content_frame.pack_propagate(False)

        # Status bar
        self.create_status_bar()

        # Action buttons
        self.create_action_buttons()

        # Guest list panel (always show initially)
        self.create_guest_list_panel()
        self.list_frame.pack(fill="both", expand=True, pady=(10, 0))
        self.guest_list_visible = True

        # Initialize content based on mode
        self.update_mode_content()

    def create_header(self):
        """Create header with logo and station selector."""
        header_frame = ctk.CTkFrame(self.main_frame, corner_radius=15, height=80)
        header_frame.pack(fill="x", pady=(0, 10))
        header_frame.pack_propagate(False)

        # Logo on the left
        self.logo_label = ctk.CTkLabel(header_frame, text="", width=80, height=80)
        self.logo_label.pack(side="left", padx=20)

        # Settings button on the right
        self.settings_btn = ctk.CTkButton(
            header_frame,
            text="☰",
            command=self.toggle_settings,
            width=50,
            height=50,
            corner_radius=10,
            font=CTkFont(size=20, weight="bold"),
            fg_color="#4a4a4a",
            hover_color="#5a5a5a"
        )
        self.settings_btn.pack(side="right", padx=20)
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
        for i, station in enumerate(self.config['stations']):
            btn = ctk.CTkButton(
                buttons_container,
                text=station,
                command=lambda s=station: self.on_station_button_click(s),
                width=110,
                height=50,
                corner_radius=12,
                font=CTkFont(size=15, weight="bold"),
                border_width=2
            )
            btn.pack(side="left", padx=3)
            self.station_buttons[station] = btn

        # Highlight current station
        self.update_station_buttons()

    def create_status_bar(self):
        """Create status bar."""
        self.status_frame = ctk.CTkFrame(self.main_frame, corner_radius=10, height=75)
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

        # Reception mode toggle button (only visible at Reception)
        self.reception_mode_btn = ctk.CTkButton(
            left_frame,
            text="Switch to Check-in Mode",
            command=self.toggle_reception_mode,
            width=180,
            height=35,
            corner_radius=8,
            font=self.fonts['button'],
            fg_color="#2196F3",
            hover_color="#1976D2"
        )
        # Initially hidden, will show only at Reception

        # Manual check-in button
        self.manual_checkin_btn = ctk.CTkButton(
            right_frame,
            text="Manual Check-in",
            command=self.toggle_manual_checkin,
            width=130,
            height=35,
            corner_radius=8,
            font=self.fonts['button'],
            fg_color="#ff9800",
            hover_color="#f57c00"
        )
        # Initially hidden, will show in checkpoint mode

    def create_guest_list_panel(self):
        """Create guest list panel."""
        self.list_frame = ctk.CTkFrame(self.main_frame, corner_radius=15)
        # Initially hidden

        # Search bar
        search_frame = ctk.CTkFrame(self.list_frame, fg_color="transparent")
        search_frame.pack(fill="x", padx=10, pady=(10, 5))

        search_label = ctk.CTkLabel(search_frame, text="Search:", font=self.fonts['body'])
        search_label.pack(side="left", padx=(0, 10))

        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda *args: self.filter_guest_list())
        self.search_entry = ctk.CTkEntry(
            search_frame,
            textvariable=self.search_var,
            placeholder_text="Name or ID...",
            width=200
        )
        self.search_entry.pack(side="left")

        # Sync status label (on same line as search)
        self.sync_status_label = ctk.CTkLabel(
            search_frame,
            text="",
            font=self.fonts['body'],
            text_color="#4CAF50"
        )
        self.sync_status_label.pack(side="right", padx=(20, 0))

        # Guest list (using tkinter Treeview for table)
        self.create_guest_table()

    def create_guest_table(self):
        """Create the guest list table."""
        # Frame for treeview
        tree_frame = ctk.CTkFrame(self.list_frame)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=(5, 10))

        # Scrollbar
        scrollbar = ctk.CTkScrollbar(tree_frame)
        scrollbar.pack(side="right", fill="y")

        # Overview mode: show all stations
        columns = ("id", "first", "last") + tuple(station.lower() for station in self.config['stations'])

        # Treeview with flexible height
        self.guest_tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="headings",
            yscrollcommand=scrollbar.set
        )
        scrollbar.configure(command=self.guest_tree.yview)

        # Configure column headers and widths
        self.guest_tree.heading("id", text="Guest ID", anchor="w")
        self.guest_tree.heading("first", text="First Name", anchor="w")
        self.guest_tree.heading("last", text="Last Name", anchor="w")

        # Set responsive column widths with padding for visual separation
        self.guest_tree.column("id", width=80, minwidth=60, anchor="w")
        self.guest_tree.column("first", width=150, minwidth=100, anchor="w")
        self.guest_tree.column("last", width=150, minwidth=100, anchor="w")

        # Set headers and widths for all stations with responsive sizing and padding
        for i, station in enumerate(self.config['stations']):
            self.guest_tree.heading(station.lower(), text=station, anchor="w")
            self.guest_tree.column(station.lower(), width=120, minwidth=80, anchor="w")

        # Style for treeview
        style = ttk.Style()
        style.theme_use("clam")

        # Configure treeview colors
        style.configure("Treeview",
                       background="#212121",
                       foreground="white",
                       fieldbackground="#212121",
                       borderwidth=1,
                       relief="flat",
                       rowheight=25,
                       font=("TkFixedFont", 12, "normal"))

        style.configure("Treeview.Heading",
                       background="#323232",
                       foreground="white",
                       borderwidth=1,
                       relief="flat",
                       font=("TkFixedFont", 13, "bold"))

        # Map item states to colors - include hover (active) state
        style.map('Treeview',
                  background=[('selected', '#4a4a4a'), ('active', '#ff9800')],
                  foreground=[('selected', 'white'), ('active', 'white')])

        # Bind selection
        self.guest_tree.bind("<Double-Button-1>", self.on_guest_select)

        # Bind click for check-in button
        self.guest_tree.bind("<Button-1>", self.on_tree_click)

        # Bind mouse motion for cursor changes
        self.guest_tree.bind("<Motion>", self.on_tree_motion)

        # Bind column headers for sorting
        sortable_columns = ["id", "first", "last"]
        for col in sortable_columns:
            self.guest_tree.heading(col, command=lambda c=col: self.sort_treeview(c))

        self.guest_tree.pack(fill="both", expand=True)

        # Sorting state
        self.sort_reverse = {}

        # Configure hover tag for check-in buttons
        self.guest_tree.tag_configure("checkin_hover", background="#ff9800", foreground="white")

    def create_tag_info_content(self):
        """Create inline tag info display."""
        if not self.tag_info_data:
            return

        # Hide copyright text
        self.copyright_label.place_forget()

        # Hide status bar content only when Reception is in registration mode (keep frame visible)
        if self.current_station == "Reception" and self.is_registration_mode and not self.is_checkpoint_mode:
            self.status_label.configure(text="")

        # Main container
        main_container = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        main_container.pack(fill="both", expand=True)

        # Center frame for content
        center_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        center_frame.place(relx=0.5, rely=0.5, anchor="center")

        # Guest details
        guest = self.tag_info_data['guest']
        check_ins = self.tag_info_data['check_ins']

        # Guest name (large and bold)
        name_label = ctk.CTkLabel(
            center_frame,
            text=f"{guest.firstname} {guest.lastname}",
            font=CTkFont(size=32, weight="bold"),
            text_color="#4CAF50"
        )
        name_label.pack(pady=(0, 30))

        # Find last check-in
        last_station = None
        last_time = None
        for station, time in check_ins.items():
            if time:
                last_station = station.title()
                last_time = time

        # Last check-in info
        if last_station and last_time:
            checkin_text = f"Last check-in: {last_station} at {last_time}"
        else:
            checkin_text = "No check-ins recorded"

        checkin_label = ctk.CTkLabel(
            center_frame,
            text=checkin_text,
            font=CTkFont(size=18),
            text_color="#ffffff"
        )
        checkin_label.pack(pady=(0, 30))

        # Countdown label
        self.tag_info_countdown_label = ctk.CTkLabel(
            center_frame,
            text="Auto-close in 10s",
            font=CTkFont(size=14),
            text_color="#999999"
        )
        self.tag_info_countdown_label.pack(pady=(0, 20))

        # Close button (red X, same style as hamburger menu)
        close_btn = ctk.CTkButton(
            center_frame,
            text="✕",
            command=self.close_tag_info,
            width=50,
            height=50,
            corner_radius=10,
            font=CTkFont(size=20, weight="bold"),
            fg_color="#dc3545",
            hover_color="#c82333"
        )
        close_btn.pack()

        # Start auto-close countdown
        self._tag_info_auto_close_active = True
        self._tag_info_auto_close_countdown(10)

    def _tag_info_auto_close_countdown(self, countdown: int):
        """Auto-close countdown for tag info panel."""
        if countdown > 0 and self._tag_info_auto_close_active and self.is_displaying_tag_info:
            self.tag_info_countdown_label.configure(text=f"Auto-close in {countdown}s")
            self.after(1000, lambda: self._tag_info_auto_close_countdown(countdown - 1))
        elif self._tag_info_auto_close_active and self.is_displaying_tag_info:
            # Countdown reached 0 - auto close
            self.close_tag_info()

    def close_tag_info(self):
        """Close tag info display and return to normal mode."""
        # Stop auto-close countdown
        self._tag_info_auto_close_active = False

        self.is_displaying_tag_info = False
        self.tag_info_data = None

        # Always return to station view (not settings)
        self.settings_visible = False
        # Hide copyright when leaving settings
        self.copyright_label.place_forget()

        # Clean up any settings references
        if hasattr(self, '_came_from_settings'):
            delattr(self, '_came_from_settings')

        # Status bar frame is never hidden, only content is cleared, so no need to restore it

        self.update_mode_content()
        self.update_settings_button()  # Restore hamburger button

        # Resume scanning if in checkpoint mode
        if not self.is_registration_mode or self.is_checkpoint_mode:
            self.start_checkpoint_scanning()

        # Set appropriate status based on current mode
        self.update_status(self.get_ready_status_message(), "normal")

    def create_settings_content(self):
        """Create settings content in the main content area."""
        # Set appropriate status text based on mode - keep status bar visible
        if self.current_station == "Reception" and self.is_registration_mode and not self.is_checkpoint_mode:
            # Hide registration waiting text, keep status bar for other messages
            self.update_status("", "normal")
        elif self.is_checkpoint_mode or (not self.is_registration_mode):
            # Show check-in waiting text for check-in modes
            self.update_status(self.STATUS_READY_CHECKIN, "normal")
        else:
            # Default for other stations
            self.update_status(self.STATUS_READY_CHECKIN, "normal")

        # Main container that fills and centers content
        main_container = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        main_container.pack(fill="both", expand=True)

        # Center frame for all content
        center_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        center_frame.place(relx=0.5, rely=0.5, anchor="center")



        # Buttons container
        buttons_container = ctk.CTkFrame(center_frame, fg_color="transparent")
        buttons_container.pack()

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
            fg_color="#2196F3",
            hover_color="#1976D2"
        )
        self.tag_info_btn.pack(side="left")

        # Rewrite Tag button
        self.rewrite_tag_btn = ctk.CTkButton(
            buttons_container,
            text="Rewrite Tag",
            command=self.rewrite_tag,
            width=200,
            height=50,
            corner_radius=8,
            font=self.fonts['button'],
            fg_color="#ff9800",
            hover_color="#f57c00"
        )
        self.rewrite_tag_btn.pack(pady=10)

        # Refresh Guest List button
        self.refresh_btn = ctk.CTkButton(
            buttons_container,
            text="Refresh Guest List",
            command=self.refresh_guest_data,
            width=200,
            height=50,
            corner_radius=8,
            font=self.fonts['button'],
            fg_color="#4CAF50",
            hover_color="#45a049"
        )
        self.refresh_btn.pack(pady=10)

        # Erase Tag button with frame for cancel button
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
            fg_color="#dc3545",
            hover_color="#c82333"
        )
        self.settings_erase_btn.pack(side="left")

        # Log button
        self.log_btn = ctk.CTkButton(
            buttons_container,
            text="View Logs",
            command=self.show_logs,
            width=200,
            height=50,
            corner_radius=8,
            font=self.fonts['button'],
            fg_color="#9c27b0",
            hover_color="#7b1fa2"
        )
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
            fg_color="#6c757d",
            hover_color="#5a6268"
        )
        self.dev_mode_btn.pack(pady=10)

    def sort_treeview(self, col):
        """Sort treeview by column."""
        # Determine sort direction
        if self.current_sort_column == col:
            # Same column clicked - toggle direction
            self.current_sort_reverse = not self.current_sort_reverse
        else:
            # New column clicked - start with ascending
            self.current_sort_column = col
            self.current_sort_reverse = False

        # Apply the sort
        self._apply_current_sort()

        # Update old sort_reverse dict for compatibility
        self.sort_reverse[col] = self.current_sort_reverse

    def _apply_current_sort(self):
        """Apply the current sort column and direction to the treeview."""
        if not self.current_sort_column:
            return

        # Get all items
        items = [(self.guest_tree.set(k, self.current_sort_column), k) for k in self.guest_tree.get_children('')]

        # Check if we need numeric sort for ID column
        if self.current_sort_column == "id":
            items.sort(key=lambda x: int(x[0]) if x[0].isdigit() else 0, reverse=self.current_sort_reverse)
        else:
            items.sort(reverse=self.current_sort_reverse)

        # Rearrange items
        for index, (val, k) in enumerate(items):
            self.guest_tree.move(k, '', index)

    def toggle_settings(self):
        """Toggle settings panel visibility."""
        if self.settings_visible:
            self.settings_visible = False
            # Reset erase confirmation state when leaving settings
            self._reset_erase_confirmation()
            # Hide copyright
            self.copyright_label.place_forget()
            self.update_mode_content()
            # Return to appropriate status
            if self.is_rewrite_mode:
                self.update_status(self.STATUS_CHECKIN_PAUSED, "warning")
            else:
                self.update_status(self.get_ready_status_message(), "normal")
        else:
            self.settings_visible = True
            # Show copyright on right side, centered vertically
            self.copyright_label.place(relx=1.0, rely=0.5, anchor="e", x=-20)
            # Don't stop scanning when entering settings
            # Show appropriate status in settings - only for check-in modes
            if self.is_checkpoint_mode or (not self.is_registration_mode):
                self.update_status("Ready. Waiting for Check-In", "normal")
            # No status text shown for registration mode in settings (can't register while settings open)
            self.update_mode_content()
        self.update_settings_button()

    def update_settings_button(self):
        """Update settings button appearance based on state."""
        if self.is_displaying_tag_info or self.is_rewrite_mode:
            # Hide hamburger button completely when in tag info view or rewrite mode
            self.settings_btn.pack_forget()
        elif self.settings_visible:
            self.settings_btn.pack(side="right", padx=20)
            self.settings_btn.configure(
                text="✕",
                fg_color="#dc3545",
                hover_color="#c82333"
            )
        else:
            self.settings_btn.pack(side="right", padx=20)
            self.settings_btn.configure(
                text="☰",
                fg_color="#4a4a4a",
                hover_color="#5a5a5a"
            )

    def update_mode_content(self):
        """Update content based on current mode."""
        # Clear current content
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        if self.settings_visible:
            # Hide guest list completely in settings
            if self.guest_list_visible:
                self.list_frame.pack_forget()
                self.guest_list_visible = False
            # Hide buttons when in settings
            self.manual_checkin_btn.pack_forget()
            self.reception_mode_btn.pack_forget()  # Hide reception mode button in settings
            # Expand content frame to cover most of screen (leave space for status bar)
            self.content_frame.configure(height=600)
            self.create_settings_content()
            return
        elif self.is_displaying_tag_info:
            # Hide guest list when displaying tag info
            if self.guest_list_visible:
                self.list_frame.pack_forget()
                self.guest_list_visible = False
            # Hide buttons when displaying tag info
            self.manual_checkin_btn.pack_forget()
            self.reception_mode_btn.pack_forget()  # Hide reception mode button
            # Expand content frame for tag info display
            self.content_frame.configure(height=400)
            self.create_tag_info_content()
            return
        else:
            # Restore compact content frame
            self.content_frame.configure(height=200)
            # Show guest list if not visible
            if not self.guest_list_visible:
                self.list_frame.pack(fill="both", expand=True, pady=(10, 0))
                self.guest_list_visible = True

            # Only show buttons when not in settings or rewrite mode
            if not self.is_rewrite_mode:
                # Show buttons when not in settings or rewrite
                self.manual_checkin_btn.pack(side="left", padx=5)

                # Update button text based on current manual check-in state
                if self.checkin_buttons_visible:
                    self.manual_checkin_btn.configure(
                        text="Cancel Manual Check-in",
                        fg_color="#dc3545",
                        hover_color="#c82333"
                    )
                else:
                    self.manual_checkin_btn.configure(
                        text="Manual Check-in",
                        fg_color="#ff9800",
                        hover_color="#f57c00"
                    )

                # Show Reception mode toggle only at Reception station (only in normal mode, not settings or rewrite)
                if self.current_station == "Reception":
                    self.reception_mode_btn.pack(side="left", padx=5)
                    if self.is_checkpoint_mode:
                        self.reception_mode_btn.configure(text="Switch to Registration Mode")
                    else:
                        self.reception_mode_btn.configure(text="Switch to Check-in Mode")
                else:
                    self.reception_mode_btn.pack_forget()
            else:
                # Hide buttons in rewrite mode
                self.manual_checkin_btn.pack_forget()
                self.reception_mode_btn.pack_forget()

        if self.is_rewrite_mode:
            self.create_rewrite_content()
        elif self.is_registration_mode and not self.is_checkpoint_mode:
            self.create_registration_content()
        else:
            # Checkpoint mode
            self.create_checkpoint_content()

    def create_registration_content(self):
        """Create registration mode UI."""
        # Center container
        center_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        center_frame.place(relx=0.5, rely=0.5, anchor="center")

        # Instructions
        instruction_label = ctk.CTkLabel(
            center_frame,
            text="Enter Guest ID to register:",
            font=self.fonts['heading']
        )
        instruction_label.pack(pady=(0, 20))

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

        # Write button
        self.write_btn = ctk.CTkButton(
            entry_frame,
            text="Write Tag",
            command=self.write_to_band,
            width=120,
            height=50,
            font=self.fonts['button'],
            corner_radius=8
        )
        self.write_btn.pack(side="left")

        # Guest name display (initially hidden)
        self.guest_name_label = ctk.CTkLabel(
            center_frame,
            text="",
            font=self.fonts['heading'],
            text_color="#4CAF50"
        )
        self.guest_name_label.pack(pady=(20, 0))

        # Focus on entry
        self.id_entry.focus()

        # Start background tag scanning for registration mode
        self.start_registration_tag_scanning()

    def start_rewrite_tag_scanning(self):
        """Start background tag scanning for rewrite mode."""
        if self.is_rewrite_mode and not self.is_scanning:
            self.is_scanning = True
            self._rewrite_scan_loop()

    def _rewrite_scan_loop(self):
        """Background scanning loop for rewrite mode."""
        if self.is_rewrite_mode and self.is_scanning:
            thread = threading.Thread(target=self._scan_for_rewrite)
            thread.daemon = True
            thread.start()

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

        tag = self.nfc_service.read_tag(timeout=3)

        if not tag:
            self._active_operations -= 1
            self.after(100, self._rewrite_scan_loop)
            return

        # Tag detected - check if guest ID field is filled
        guest_id = self.rewrite_id_entry.get().strip() if hasattr(self, 'rewrite_id_entry') else ""

        if not guest_id:
            # ID field is empty
            self._active_operations -= 1
            self.after(0, self.update_status, "Enter Guest ID first", "error")
            self.after(3000, lambda: self.update_status(self.STATUS_CHECKIN_PAUSED, "warning"))
        else:
            # ID field has value
            self._active_operations -= 1
            self.after(0, self.update_status, "Press Rewrite Tag Button to begin", "info")
            self.after(3000, lambda: self.update_status(self.STATUS_CHECKIN_PAUSED, "warning"))

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
        if self.is_registration_mode and not self.is_checkpoint_mode and self.is_scanning:
            thread = threading.Thread(target=self._scan_for_registration)
            thread.daemon = True
            thread.start()

    def _scan_for_registration(self):
        """Scan for tag info in registration mode."""
        # Don't scan if a user operation is in progress (but allow background scanning to be interrupted)
        if self.operation_in_progress and not hasattr(self, '_allow_background_interrupt'):
            self.after(1000, self._registration_scan_loop)
            return

        # Mark as background operation (can be interrupted)
        self._active_operations += 1

        tag = self.nfc_service.read_tag(timeout=3)

        if not tag:
            self._active_operations -= 1
            self.after(100, self._registration_scan_loop)
            return

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
            self.after(0, self.update_status, "Network error - check connection", "error")
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
            text="Rewrite Tag",
            command=self.rewrite_to_band,
            width=120,
            height=50,
            font=self.fonts['button'],
            corner_radius=8,
            fg_color="#ff9800",
            hover_color="#f57c00"
        )
        self.rewrite_btn.pack(side="left")

        # Exit rewrite button (red X)
        self.exit_rewrite_btn = ctk.CTkButton(
            center_frame,
            text="X",
            command=self.exit_rewrite_mode,
            width=50,
            height=50,
            corner_radius=8,
            font=CTkFont(size=14, weight="bold"),
            fg_color="#dc3545",
            hover_color="#c82333"
        )
        self.exit_rewrite_btn.pack(pady=(20, 0))

        # Focus on entry
        self.rewrite_id_entry.focus()

        # Start background tag scanning for rewrite mode
        self.start_rewrite_tag_scanning()

    def create_checkpoint_content(self):
        """Create checkpoint mode UI."""
        # Center container
        center_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        center_frame.place(relx=0.5, rely=0.5, anchor="center")

        # Waiting label
        self.checkpoint_status = ctk.CTkLabel(
            center_frame,
            text="Waiting for tap...",
            font=CTkFont(size=28, weight="bold")
        )
        self.checkpoint_status.pack()

        # Start continuous scanning
        self.start_checkpoint_scanning()

    def write_to_band(self):
        """Handle write to band action."""
        guest_id = self.id_entry.get().strip()

        if not guest_id:
            self.update_status("Please enter a guest ID", "error")
            return

        try:
            guest_id = int(guest_id)
        except ValueError:
            self.update_status("Invalid ID format", "error")
            return

        # Mark operation in progress
        self.operation_in_progress = True
        self._active_operations += 1  # Track operation start

        # Disable UI during operation
        self.write_btn.configure(state="disabled")
        self.id_entry.configure(state="disabled")

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
        thread = threading.Thread(target=self._write_to_band_thread, args=(guest_id,))
        thread.daemon = True
        thread.start()

    def cancel_write(self):
        """Cancel write operation."""
        self._write_operation_active = False
        self._active_operations -= 1  # Operation cancelled
        self.nfc_service.cancel_read()
        self.update_status("Write operation cancelled", "warning")
        self._cleanup_write_ui()

    def _cleanup_write_ui(self):
        """Clean up write operation UI."""
        self.write_btn.configure(state="normal")
        self.id_entry.configure(state="normal")
        if hasattr(self, 'write_cancel_btn'):
            self.write_cancel_btn.destroy()
            delattr(self, 'write_cancel_btn')

    def _countdown_write_band(self, guest_id: int, countdown: int):
        """Show countdown for write band operation."""
        if countdown > 0 and self._write_operation_active:
            self.update_status(f"Tap wristband now... {countdown}s", "info")
            self.after(1000, lambda: self._countdown_write_band(guest_id, countdown - 1))
        elif self._write_operation_active:
            # Timeout reached
            self._write_operation_active = False
            self.update_status("No tag detected", "error")
            self._write_complete(None)

    def _write_to_band_thread(self, guest_id: int):
        """Thread function for writing to band."""
        try:
            # Use 10-second timeout to match countdown
            result = self.tag_manager.register_tag_to_guest(guest_id)

            # Always stop countdown when thread completes
            self._write_operation_active = False

            # Update UI in main thread
            self.after(0, self._write_complete, result)

        except Exception as e:
            # Stop countdown on error
            self._write_operation_active = False
            self.logger.error(f"Write operation error: {e}")
            self.after(0, self._write_complete, None)

    def _write_complete(self, result: Optional[Dict]):
        """Handle write completion."""
        # Mark operation complete
        self.operation_in_progress = False
        self._active_operations -= 1  # Operation finished

        # Clean up UI
        self._cleanup_write_ui()

        if result:
            self.update_status(f"✓ Registered to {result['guest_name']}", "success")
            self.guest_name_label.configure(text=result['guest_name'])

            # Clear form after delay
            self.after(2000, self.clear_registration_form)

            # Refresh guest list after delay to ensure queue is updated and status is visible
            self.after(2500, lambda: self.refresh_guest_data(user_initiated=False))
        else:
            self.update_status("No tag detected", "error")

        self.id_entry.focus()

    def clear_registration_form(self):
        """Clear the registration form."""
        self.id_entry.delete(0, 'end')
        self.guest_name_label.configure(text="")
        # Show appropriate status based on mode
        if self.is_rewrite_mode:
            self.update_status(self.STATUS_CHECKIN_PAUSED, "warning")
        elif not self.settings_visible:
            self.update_status(self.get_ready_status_message(), "normal")

    def toggle_reception_mode(self):
        """Toggle between Registration and Checkpoint mode at Reception."""
        if self.current_station == "Reception":
            # Stop all current scanning first
            self.is_scanning = False
            try:
                self.nfc_service.cancel_read()
            except Exception as e:
                self.logger.warning(f"Error cancelling NFC read during mode switch: {e}")

            self.is_checkpoint_mode = not self.is_checkpoint_mode
            if self.is_checkpoint_mode:
                self.update_status("Switched to Check-in Mode", "info")
                # Start checkpoint scanning after a short delay
                self.after(500, self.start_checkpoint_scanning)
            else:
                self.update_status("Switched to Registration Mode", "info")
                # Start registration scanning after a short delay
                self.after(500, self.start_registration_tag_scanning)
            self.update_mode_content()

    def start_checkpoint_scanning(self):
        """Start continuous scanning for checkpoint mode."""
        # Allow checkpoint scanning at Reception if in checkpoint mode
        if (not self.is_registration_mode or self.is_checkpoint_mode) and not self.is_scanning:
            self.is_scanning = True
            self.logger.debug(f"Starting checkpoint scanning - Registration mode: {self.is_registration_mode}, Checkpoint mode: {self.is_checkpoint_mode}")
            self._checkpoint_scan_loop()

    def _checkpoint_scan_loop(self):
        """Continuous scanning loop for checkpoint mode."""
        # Background scanning rules:
        # 1. Always scan in checkpoint mode (non-reception stations)
        # 2. Only scan at Reception if in checkpoint mode (not registration mode)
        # 3. Allow scanning during tag info display if in check-in mode

        in_checkin_mode = not self.is_registration_mode or self.is_checkpoint_mode
        allow_during_tag_info = self.is_displaying_tag_info and in_checkin_mode

        should_scan = (in_checkin_mode and self.is_scanning) or allow_during_tag_info

        if should_scan:
            # Start scan in thread
            thread = threading.Thread(target=self._scan_for_checkin)
            thread.daemon = True
            thread.start()

    def _scan_for_checkin(self):
        """Scan for check-in (thread function)."""
        # Mark as background operation (can be interrupted)
        self._active_operations += 1

        # Read NFC tag first
        tag = self.nfc_service.read_tag(timeout=5)

        if not tag:
            self._active_operations -= 1
            # Continue scanning after short delay
            self.after(100, self._restart_scanning_after_timeout)
            return

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
            self.after(0, self.update_status, "Network error - check connection", "error")
            self.after(2000, self._restart_scanning_after_error)
            return

        if not guest:
            # Guest not found in Google Sheets - silently skip, registration scanning will handle the message
            self._active_operations -= 1
            # Continue scanning after showing error
            self.after(2000, self._restart_scanning_after_error)
            return

        if guest:
            try:
                # Check both Google Sheets and local queue with error handling (consistent lowercase)
                sheets_checkin = guest.is_checked_in_at(self.current_station.lower())
                local_checkin = self.tag_manager.check_in_queue.has_check_in(original_id, self.current_station.lower())

                if sheets_checkin or local_checkin:
                    self._active_operations -= 1
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

        # Process normal check-in
        result = self.tag_manager.process_checkpoint_scan_with_tag(tag, self.current_station)
        self._active_operations -= 1

        # If result is None (duplicate), it's already been handled
        if result is None:
            # Continue scanning after showing duplicate
            self.after(2000, self._restart_scanning_after_duplicate)
            return

        # Update UI in main thread
        self.after(0, self._checkin_complete, result)

    def _restart_scanning_after_duplicate(self):
        """Restart scanning after duplicate warning."""
        # Check if we should restart scanning (including during tag info)
        in_checkin_mode = not self.is_registration_mode or self.is_checkpoint_mode
        allow_during_tag_info = self.is_displaying_tag_info and in_checkin_mode

        should_scan = (in_checkin_mode and self.is_scanning) or allow_during_tag_info
        if should_scan:
            self._checkpoint_scan_loop()

    def _restart_scanning_after_timeout(self):
        """Restart scanning after timeout (no tag detected)."""
        # Only restart if we should be scanning and are not already scanning
        in_checkin_mode = not self.is_registration_mode or self.is_checkpoint_mode
        allow_during_tag_info = self.is_displaying_tag_info and in_checkin_mode

        should_scan = (in_checkin_mode and not self.is_scanning) or allow_during_tag_info
        if should_scan:
            self.logger.debug("Restarting scanning after timeout")
            if not self.is_scanning:
                self.is_scanning = True
            self._checkpoint_scan_loop()

    def _restart_scanning_after_error(self):
        """Restart scanning after error (unregistered tag)."""
        # Only restart if we should be scanning and are not already scanning
        in_checkin_mode = not self.is_registration_mode or self.is_checkpoint_mode
        allow_during_tag_info = self.is_displaying_tag_info and in_checkin_mode

        should_scan = (in_checkin_mode and not self.is_scanning) or allow_during_tag_info
        if should_scan:
            self.logger.debug("Restarting scanning after error")
            if not self.is_scanning:
                self.is_scanning = True
            self._checkpoint_scan_loop()

    def _checkin_complete(self, result: Optional[Dict]):
        """Handle check-in completion."""
        if result:
            self.checkpoint_status.configure(
                text=f"✓ {result['guest_name']} checked in at {result['timestamp']}",
                text_color="#4CAF50"
            )
            self.update_status(f"Checked in: {result['guest_name']}", "success")

            # Delay refresh to ensure status is visible and sync has time to complete
            self.after(3000, lambda: self.refresh_guest_data(False))

            # Reset after delay
            self.after(3000, lambda: self.checkpoint_status.configure(
                text="Waiting for tap...",
                text_color="#ffffff"
            ))

        # Continue scanning after a short delay - only in check-in modes
        in_checkin_mode = not self.is_registration_mode or self.is_checkpoint_mode
        allow_during_tag_info = self.is_displaying_tag_info and (self.is_checkpoint_mode or not self.is_registration_mode)

        should_continue = (self.is_scanning and in_checkin_mode) or allow_during_tag_info
        if should_continue:
            self.after(1000, self._checkpoint_scan_loop)

    def erase_tag_settings(self):
        """Erase tag functionality from settings panel with two-step confirmation."""
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

        # Stop ALL background scanning and cancel any ongoing NFC operations
        self.is_scanning = False
        try:
            self.nfc_service.cancel_read()
        except Exception as e:
            self.logger.warning(f"Error cancelling NFC read before erase: {e}")

        # Mark operation in progress to block other operations
        self.operation_in_progress = True

        # Disable button during operation
        self.settings_erase_btn.configure(state="disabled")

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

        thread = threading.Thread(target=self._erase_tag_thread_settings)
        thread.daemon = True
        thread.start()

    def _reset_erase_confirmation(self):
        """Reset erase button to normal state."""
        if self.erase_confirmation_state:
            self.erase_confirmation_state = False
            if hasattr(self, 'settings_erase_btn'):
                self.settings_erase_btn.configure(
                    text="Erase Tag",
                    fg_color="#dc3545",
                    hover_color="#c82333"
                )

    def cancel_erase_settings(self):
        """Cancel erase operation from settings."""
        self._erase_operation_active = False
        self.operation_in_progress = False
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
                self.start_registration_tag_scanning()
            elif self.is_checkpoint_mode:
                self.start_checkpoint_scanning()
        else:
            # Non-Reception stations always use checkpoint scanning
            self.start_checkpoint_scanning()

    def _cleanup_erase_settings(self):
        """Clean up erase UI in settings."""
        # Reset confirmation state
        self._reset_erase_confirmation()
        self.settings_erase_btn.configure(state="normal")
        if hasattr(self, 'erase_cancel_btn'):
            self.erase_cancel_btn.destroy()
            delattr(self, 'erase_cancel_btn')

    def _countdown_erase_settings(self, countdown: int):
        """Countdown for erase in settings."""
        if countdown > 0 and self._erase_operation_active:
            self.update_status(f"Tap tag to erase... {countdown}s", "info")
            self.after(1000, lambda: self._countdown_erase_settings(countdown - 1))
        elif self._erase_operation_active:
            self._erase_operation_active = False
            self.update_status("No tag detected", "error")
            self._erase_complete_settings(None)

    def _erase_tag_thread_settings(self):
        """Thread for erase operation in settings."""
        try:
            tag = self.nfc_service.read_tag(timeout=10)

            # Always stop countdown when thread completes
            self._erase_operation_active = False

            if tag:
                result = self.tag_manager.clear_tag(tag.uid)
                self.after(0, self._erase_complete_settings, result)
            else:
                # No tag detected
                self.after(0, self._erase_complete_settings, None)

        except Exception as e:
            # Stop countdown on error
            self._erase_operation_active = False
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
        elif result is None:
            self.update_status("No tag detected", "error")
        else:
            self.update_status("Tag was not registered", "warning")

        # Restart scanning if appropriate
        self._restart_scanning_after_erase()

    def tag_info(self):
        """Show tag information functionality."""
        # Immediately stop all background scanning
        self.is_scanning = False

        # Force cancel any ongoing NFC operations
        try:
            self.nfc_service.cancel_read()
        except Exception as e:
            self.logger.warning(f"Error cancelling NFC read: {e}")

        # Only wait for explicit user operations
        if self.operation_in_progress:
            self.update_status("Waiting for current operation to finish...", "warning")
            self.after(500, self.tag_info)
            return

        # Track if we came from settings
        if self.settings_visible:
            self._came_from_settings = True

        # Mark operation in progress
        self.operation_in_progress = True
        self._active_operations += 1

        # Disable button during operation
        self.tag_info_btn.configure(state="disabled")

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

        thread = threading.Thread(target=self._tag_info_thread)
        thread.daemon = True
        thread.start()

    def cancel_tag_info(self):
        """Cancel tag info operation."""
        self._tag_info_operation_active = False
        self.operation_in_progress = False
        self._active_operations -= 1

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
        try:
            self.tag_info_btn.configure(state="normal")
            if hasattr(self, 'tag_info_cancel_btn'):
                self.tag_info_cancel_btn.destroy()
                delattr(self, 'tag_info_cancel_btn')
        except Exception as e:
            self.logger.warning(f"Error cleaning up tag info UI: {e}")

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
            self.update_status("No tag detected", "error")
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

            if tag:
                info = self.tag_manager.get_tag_info(tag.uid)
                self.after(0, self._tag_info_complete, info)
            else:
                # No tag detected
                self.after(0, self.update_status, "No tag detected", "error")
                self.after(0, self._cleanup_tag_info)

        except Exception as e:
            self.logger.error(f"Error in tag info thread: {e}")
            if self._tag_info_operation_active:
                self._tag_info_operation_active = False
                self.operation_in_progress = False
                self._active_operations -= 1
                self.after(0, self.update_status, "Tag read error", "error")
                self.after(0, self._cleanup_tag_info)

    def _tag_info_complete(self, tag_info: Optional[Dict]):
        """Display tag information inline."""
        self._cleanup_tag_info()

        if tag_info:
            # Find guest details with error handling
            try:
                guest = self.sheets_service.find_guest_by_id(tag_info['original_id'])
            except Exception as e:
                self.update_status("Network error - check connection", "error")
                return

            if guest:
                # Clear settings mode and switch to inline display mode
                self.settings_visible = False
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
            else:
                self.update_status("Guest data not found", "warning")
        else:
            self.update_status("Tag not registered", "warning")

    def show_logs(self):
        """Show log viewer dialog."""
        log_window = ctk.CTkToplevel(self)
        log_window.title("Application Logs")
        log_window.geometry("800x600")
        log_window.transient(self)

        # Center window
        log_window.update_idletasks()
        x = (log_window.winfo_screenwidth() // 2) - (log_window.winfo_width() // 2)
        y = (log_window.winfo_screenheight() // 2) - (log_window.winfo_height() // 2)
        log_window.geometry(f"+{x}+{y}")

        # Title
        title_label = ctk.CTkLabel(log_window, text="", font=self.fonts['heading'])
        title_label.pack(pady=20)

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

        # Close button
        close_btn = ctk.CTkButton(
            log_window,
            text="Close",
            command=log_window.destroy,
            width=100,
            height=35
        )
        close_btn.pack(pady=(0, 20))

    def enter_developer_mode(self):
        """Show password dialog for developer mode."""
        password_window = ctk.CTkToplevel(self)
        password_window.title("")
        password_window.geometry("300x300")
        password_window.transient(self)
        password_window.grab_set()

        # Center window
        password_window.update_idletasks()
        x = (password_window.winfo_screenwidth() // 2) - (password_window.winfo_width() // 2)
        y = (password_window.winfo_screenheight() // 2) - (password_window.winfo_height() // 2)
        password_window.geometry(f"+{x}+{y}")

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
            font=self.fonts['button']
        )
        login_btn.pack(side="left", padx=5)

        cancel_btn = ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=password_window.destroy,
            width=80,
            height=35,
            font=self.fonts['button'],
            fg_color="#6c757d",
            hover_color="#5a6268"
        )
        cancel_btn.pack(side="left", padx=5)

    def show_developer_mode(self):
        """Show developer mode interface."""
        dev_window = ctk.CTkToplevel(self)
        dev_window.title("Developer Mode")
        dev_window.geometry("300x300")
        dev_window.resizable(False, False)
        dev_window.transient(self)
        dev_window.grab_set()

        # Center window
        dev_window.update_idletasks()
        x = (dev_window.winfo_screenwidth() // 2) - 150
        y = (dev_window.winfo_screenheight() // 2) - 150
        dev_window.geometry(f"+{x}+{y}")

        # Main frame with padding
        main_frame = ctk.CTkFrame(dev_window)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Title
        title_label = ctk.CTkLabel(main_frame, text="", font=self.fonts['heading'])
        title_label.pack(pady=(20, 30))

        # Clear All Data button
        self.clear_all_btn = ctk.CTkButton(
            main_frame,
            text="Clear All Guest Data",
            command=lambda: self.clear_all_data(dev_window),
            width=220,
            height=50,
            corner_radius=8,
            font=self.fonts['button'],
            fg_color="#dc3545",
            hover_color="#c82333"
        )
        self.clear_all_btn.pack(pady=(0, 30))

        # Close button
        close_btn = ctk.CTkButton(
            main_frame,
            text="Close",
            command=dev_window.destroy,
            width=100,
            height=35
        )
        close_btn.pack(pady=(0, 20))

    def clear_all_data(self, dev_window):
        """Clear all guest data with confirmation."""
        # Confirmation dialog
        confirm_window = ctk.CTkToplevel(dev_window)
        confirm_window.title("Confirm Clear All Data")
        confirm_window.geometry("300x300")
        confirm_window.transient(dev_window)
        confirm_window.grab_set()

        # Center window
        confirm_window.update_idletasks()
        x = (confirm_window.winfo_screenwidth() // 2) - (confirm_window.winfo_width() // 2)
        y = (confirm_window.winfo_screenheight() // 2) - (confirm_window.winfo_height() // 2)
        confirm_window.geometry(f"+{x}+{y}")

        # Warning
        warning_label = ctk.CTkLabel(
            confirm_window,
            text="🚨 CAUTION 🚨\n\nThis will permanently delete:\n• All local check-in data\n• All Google Sheets check-in data\n\nThis action CANNOT be undone!",
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
            fg_color="#dc3545",
            hover_color="#c82333"
        )
        confirm_btn.pack(side="left", padx=10)

        cancel_btn = ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=confirm_window.destroy,
            width=100,
            height=40,
            corner_radius=8,
            font=self.fonts['button'],
            fg_color="#6c757d",
            hover_color="#5a6268"
        )
        cancel_btn.pack(side="left", padx=10)

    def _execute_clear_all_data(self):
        """Execute the clear all data operation."""
        self.update_status("Clearing all data...", "warning")

        # Run in thread to avoid blocking UI
        thread = threading.Thread(target=self._clear_all_data_thread)
        thread.daemon = True
        thread.start()

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

    def rewrite_tag(self):
        """Enter rewrite tag mode."""
        # Stop any background scanning to prevent NFC conflicts
        self.is_scanning = False

        self.settings_visible = False
        # Hide copyright when leaving settings
        self.copyright_label.place_forget()
        self.is_rewrite_mode = True
        self.is_registration_mode = False  # Ensure registration mode is off
        self.update_settings_button()
        self.update_mode_content()
        self.update_status(self.STATUS_CHECKIN_PAUSED, "warning")


    def on_station_button_click(self, station: str):
        """Handle station button click."""
        # Exit rewrite mode if active and cancel any operations
        if self.is_rewrite_mode:
            self.cancel_any_rewrite_operations()
            self.exit_rewrite_mode()

        # Close settings if open
        if self.settings_visible:
            self.settings_visible = False
            self.update_settings_button()

        # Stop all current scanning first
        self.is_scanning = False
        try:
            self.nfc_service.cancel_read()
        except Exception as e:
            self.logger.warning(f"Error cancelling NFC read during station switch: {e}")

        self.current_station = station
        self.is_registration_mode = (station == "Reception")

        # Reset checkpoint mode when leaving Reception
        if station != "Reception":
            self.is_checkpoint_mode = False

        # Update button highlighting
        self.update_station_buttons()

        self.update_mode_content()
        self.update_status(f"Switched to {station}", "info")

        # Start appropriate scanning for non-Reception stations after a short delay
        if station != "Reception":
            self.after(500, self.start_checkpoint_scanning)

        # Auto-refresh guest list to show station-specific check-ins
        self.refresh_guest_data(user_initiated=False)

    def update_station_buttons(self):
        """Update station button styling to highlight current selection."""
        for station, btn in self.station_buttons.items():
            if station == self.current_station:
                # Highly highlighted selected station with border and glow effect
                btn.configure(
                    fg_color="#ff6b35",
                    hover_color="#e55a2b",
                    text_color="white",
                    border_color="#fff",
                    border_width=3
                )
            else:
                # Normal button styling
                btn.configure(
                    fg_color="#3b82f6",
                    hover_color="#2563eb",
                    text_color="white",
                    border_color="#3b82f6",
                    border_width=2
                )

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
        self.checkin_buttons_visible = not self.checkin_buttons_visible

        # Update button text and color
        if self.checkin_buttons_visible:
            self.manual_checkin_btn.configure(
                text="Cancel Manual Check-in",
                fg_color="#dc3545",
                hover_color="#c82333"
            )
        else:
            self.manual_checkin_btn.configure(
                text="Manual Check-in",
                fg_color="#ff9800",
                hover_color="#f57c00"
            )

        # Refresh guest table to show/hide check-in buttons
        if self.guest_list_visible:
            self._update_guest_table(self.guests_data)

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
        thread = threading.Thread(target=self._background_refresh_thread)
        thread.daemon = True
        thread.start()

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
            "normal": "#4CAF50",
            "success": "#4CAF50",
            "warning": "#ff9800",
            "error": "#f44336"
        }
        color = color_map.get(status_type, "#4CAF50")
        self.sync_status_label.configure(text=message, text_color=color)

    def update_status_respecting_settings_mode(self, message: str, status_type: str = "normal"):
        """Update status while respecting registration mode in settings."""
        if self.settings_visible and self.current_station == "Reception" and self.is_registration_mode and not self.is_checkpoint_mode:
            # Registration mode in settings - keep empty status
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

        # Add guests
        for i, guest in enumerate(guests):
            values = [
                guest.original_id,
                guest.firstname,
                guest.lastname
            ]

            # Add check-in status for each station
            for station in self.config['stations']:
                # Google Sheets data takes priority (for manual edits compatibility)
                sheets_time = guest.get_check_in_time(station.lower())
                local_time = local_check_ins.get(guest.original_id, {}).get(station.lower())

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

            item = self.guest_tree.insert("", "end", values=values)

        # Re-configure hover tag after refresh
        self.guest_tree.tag_configure("checkin_hover", background="#ff9800", foreground="white")

        # Apply current sort
        self._apply_current_sort()

        # Update sync status
        registry_stats = self.tag_manager.get_registry_stats()
        if registry_stats['pending_syncs'] > 0:
            self.sync_status_label.configure(text=f"⏳ {registry_stats['pending_syncs']} pending", text_color="#ff9800")
        else:
            self.sync_status_label.configure(text="✓ All synced", text_color="#4CAF50")

    def refresh_guest_data(self, user_initiated=True):
        """Refresh guest data from Google Sheets."""
        # Show status message only for user-initiated refreshes
        if user_initiated:
            if self.settings_visible:
                # In settings, show in main status bar
                self.update_status("Refreshing...", "info")
            else:
                # Normal mode, show in sync area
                self.update_sync_status("Refreshing...", "normal")

        self._is_user_initiated_refresh = user_initiated

        # Run in thread
        thread = threading.Thread(target=self._refresh_guest_data_thread)
        thread.daemon = True
        thread.start()

    def _refresh_guest_data_thread(self):
        """Thread function for refreshing data."""
        try:
            guests = self.sheets_service.get_all_guests()
            # Resolve any sync conflicts (local data vs Google Sheets)
            self.tag_manager.resolve_sync_conflicts(guests)
            # Always update table even if empty to show local data
            self.after(0, self._update_guest_table, guests)
        except Exception as e:
            self.logger.error(f"Failed to fetch from Google Sheets: {e}")
            # Still update table with existing data to show local check-ins
            self.after(0, self._update_guest_table, self.guests_data)
            # Only show cached data message for user-initiated refreshes, not automatic ones
            if hasattr(self, '_is_user_initiated_refresh') and self._is_user_initiated_refresh:
                self.after(0, self.update_sync_status, "Using cached data (Google Sheets offline)", "warning")

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

        # Track discrepancies for re-sync
        discrepancies = []

        # Add guests
        for i, guest in enumerate(guests):
            values = [
                guest.original_id,
                guest.firstname,
                guest.lastname
            ]

            # Add check-in status for each station
            for station in self.config['stations']:
                # Google Sheets data takes priority (for manual edits compatibility)
                sheets_time = guest.get_check_in_time(station.lower())
                local_time = local_check_ins.get(guest.original_id, {}).get(station.lower())

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

            item = self.guest_tree.insert("", "end", values=values)

        # Handle discrepancies - re-sync items that should be synced but aren't
        if discrepancies:
            self.logger.warning(f"Found {len(discrepancies)} sync discrepancies, re-syncing...")
            self._handle_sync_discrepancies(discrepancies)

        # Re-configure hover tag after refresh
        self.guest_tree.tag_configure("checkin_hover", background="#ff9800", foreground="white")

        # Apply current sort (default to Last Name A-Z on first load)
        self._apply_current_sort()

        # Update sync status display
        if registry_stats['pending_syncs'] > 0:
            self.sync_status_label.configure(text=f"⏳ {registry_stats['pending_syncs']} pending", text_color="#ff9800")

            # Force sync on startup if there are pending items
            if not hasattr(self, '_initial_load_complete'):
                self.logger.info(f"Found {registry_stats['pending_syncs']} pending syncs at startup - forcing sync")
                self.after(1000, self._force_sync_on_startup)
        else:
            self.sync_status_label.configure(text="✓ All synced", text_color="#4CAF50")

        # Only show "Loaded X guests" message at startup
        if not hasattr(self, '_initial_load_complete'):
            self.update_status(f"Loaded {len(guests)} guests", "success")
            # Fade to appropriate status after 2 seconds
            if self.is_rewrite_mode:
                self.after(2000, lambda: self.update_status(self.STATUS_CHECKIN_PAUSED, "warning"))
            else:
                self.after(2000, lambda: self.update_status_respecting_settings_mode(self.get_ready_status_message(), "normal"))
            self._initial_load_complete = True

            # Start registration scanning after initial load if in registration mode
            if self.is_registration_mode and not self.is_checkpoint_mode:
                self.after(2500, self.start_registration_tag_scanning)
        elif hasattr(self, '_is_user_initiated_refresh') and self._is_user_initiated_refresh:
            # Show confirmation if refresh was done in settings
            if self.settings_visible:
                self.update_status("✓ Refreshed", "success")
            delattr(self, '_is_user_initiated_refresh')  # Clean up flag
        elif self.is_rewrite_mode:
            # In rewrite mode, go straight to paused status
            self.update_status(self.STATUS_CHECKIN_PAUSED, "warning")
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

        # Add filtered guests
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
                values = [
                    guest.original_id,
                    guest.firstname,
                    guest.lastname
                ]

                # Add check-in status for each station
                for station in self.config['stations']:
                    # Google Sheets data takes priority (for manual edits compatibility)
                    sheets_time = guest.get_check_in_time(station.lower())
                    local_time = local_check_ins.get(guest.original_id, {}).get(station.lower())

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

                item = self.guest_tree.insert("", "end", values=values)

        # Apply current sort to filtered results
        self._apply_current_sort()

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
            elif self.is_rewrite_mode:
                # Fill rewrite form
                self.rewrite_id_entry.delete(0, 'end')
                self.rewrite_id_entry.insert(0, str(guest_id))
            elif self.is_manual_checkin_mode:
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
        self.is_registration_mode = (self.current_station == "Reception")
        self.update_settings_button()
        self.update_mode_content()

        # Resume scanning if in checkpoint mode
        if not self.is_registration_mode or self.is_checkpoint_mode:
            self.start_checkpoint_scanning()

        # Restore operational status
        self.update_status(self.get_ready_status_message(), "normal")

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
        guest_id = self.rewrite_id_entry.get().strip()

        if not guest_id:
            self.update_status("Please enter a guest ID", "error")
            return

        try:
            guest_id = int(guest_id)
        except ValueError:
            self.update_status("Invalid ID format", "error")
            return

        # Disable UI during tag check
        self.rewrite_btn.configure(state="disabled")
        self.rewrite_id_entry.configure(state="disabled")
        self.exit_rewrite_btn.configure(state="disabled")

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
        """Show countdown for rewrite check operation."""
        if countdown > 0 and self._rewrite_check_operation_active:
            self.update_status(f"Waiting for tag to rewrite... {countdown}s", "info", False)
            self.after(1000, lambda: self._countdown_rewrite_check(countdown - 1))
        elif self._rewrite_check_operation_active:
            # Timeout reached
            self._rewrite_check_operation_active = False
            self.update_status("No tag detected", "error")
            self._enable_rewrite_ui()

    def _check_tag_registration_thread(self, guest_id: int):
        """Thread to check if tag is already registered."""
        try:
            # Read tag to check registration
            tag = self.nfc_service.read_tag(timeout=5)

            # Always stop countdown when thread completes
            self._rewrite_check_operation_active = False

            if not tag:
                self.after(0, self._enable_rewrite_ui)
                self.after(0, self.update_status, "No tag detected", "error")
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
                    self.after(0, self._enable_rewrite_ui)
                    self.after(0, self.update_status, f"Tag already registered to {guest_name}", "warning")
                    return

                # Different guest - show confirmation dialog
                current_guest = self.sheets_service.find_guest_by_id(current_guest_id)
                new_guest = self.sheets_service.find_guest_by_id(guest_id)

                current_name = current_guest.full_name if current_guest else f"Guest ID {current_guest_id}"
                new_name = new_guest.full_name if new_guest else f"Guest ID {guest_id}"

                # Show confirmation dialog
                self.after(0, self._show_rewrite_confirmation, current_name, new_name, guest_id, tag)
            else:
                # Tag is clean - proceed with direct write
                self.logger.info(f"Tag {tag.uid} is not registered - proceeding with direct write")
                self.after(0, self._proceed_with_direct_rewrite, guest_id, tag)

        except Exception as e:
            self.logger.error(f"Error checking tag registration: {e}", exc_info=True)
            self._rewrite_check_operation_active = False
            self.after(0, self._enable_rewrite_ui)
            self.after(0, self.update_status, "Error reading tag", "error")

    def _show_rewrite_confirmation(self, current_name: str, new_name: str, guest_id: int, tag):
        """Show confirmation dialog for rewriting a registered tag."""
        # Re-enable UI first
        self._enable_rewrite_ui()

        # Create confirmation dialog
        confirm_window = ctk.CTkToplevel(self)
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
            self.exit_rewrite_btn.configure(state="disabled")

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
            fg_color="#ff9800",
            hover_color="#f57c00"
        )
        rewrite_btn.pack(side="left", padx=10)

        def cancel_rewrite():
            """Cancel rewrite and clear guest ID field."""
            confirm_window.destroy()
            # Clear the guest ID field
            self.rewrite_id_entry.delete(0, 'end')

        cancel_btn = ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=cancel_rewrite,
            width=120,
            height=45,
            font=self.fonts['button'],
            fg_color="#6c757d",
            hover_color="#5a6268"
        )
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

            # Register the tag
            tag.register_to_guest(guest_id, guest.full_name)
            self.tag_manager.tag_registry[tag.uid] = guest_id
            self.tag_manager.save_registry()

            # Create result dict for UI update
            result = {
                'tag_uid': tag.uid,
                'original_id': guest_id,
                'guest_name': guest.full_name,
                'registered_at': datetime.now().isoformat(),
                'action': 'rewrite'
            }

            self.logger.info(f"Rewrite successful: {result}")
            self.after(0, self._rewrite_complete, result)

        except Exception as e:
            self.logger.error(f"Rewrite operation error: {e}", exc_info=True)
            self.after(0, self._rewrite_complete, None)

    def _rewrite_complete(self, result: Optional[Dict]):
        """Handle rewrite completion."""
        self._enable_rewrite_ui()

        if result:
            self.update_status(f"✓ Tag rewritten to {result['guest_name']}", "success")
            self.after(2000, self.clear_rewrite_form)
            self.after(2500, lambda: self.refresh_guest_data(False))
        else:
            if self.status_label.cget("text") == "Rewriting tag...":
                self.update_status("Failed to rewrite tag", "error")

        self.rewrite_id_entry.focus()

    def clear_rewrite_form(self):
        """Clear the rewrite form."""
        self.rewrite_id_entry.delete(0, 'end')
        self.update_status(self.STATUS_CHECKIN_PAUSED, "warning")

    def _enable_rewrite_ui(self):
        """Re-enable rewrite UI elements."""
        # Reset countdown operation flag
        self._rewrite_check_operation_active = False

        if hasattr(self, 'rewrite_btn'):
            self.rewrite_btn.configure(state="normal")
        if hasattr(self, 'rewrite_id_entry'):
            self.rewrite_id_entry.configure(state="normal")
        if hasattr(self, 'exit_rewrite_btn'):
            self.exit_rewrite_btn.configure(state="normal")

    def on_tree_motion(self, event):
        """Handle mouse motion over tree for cursor changes and hover styling."""
        # Get the item and column under mouse
        item = self.guest_tree.identify("item", event.x, event.y)
        column = self.guest_tree.identify("column", event.x, event.y)

        # Clear previous hover styling
        if self.hovered_item:
            current_tags = list(self.guest_tree.item(self.hovered_item, "tags"))
            if "checkin_hover" in current_tags:
                current_tags.remove("checkin_hover")
                self.guest_tree.item(self.hovered_item, tags=current_tags)
            self.hovered_item = None

        # Check if hovering over check-in button in any station column
        if item and column:
            column_index = int(column.replace('#', '')) - 1
            # Station columns start at index 3 (after id, first, last)
            if column_index >= 3 and column_index < 3 + len(self.config['stations']):
                values = self.guest_tree.item(item, "values")
                if len(values) > column_index and values[column_index] == "Check-in":
                    # Apply hover styling
                    current_tags = list(self.guest_tree.item(item, "tags"))
                    current_tags.append("checkin_hover")
                    self.guest_tree.item(item, tags=current_tags)
                    self.hovered_item = item

                    # Set hand cursor
                    self.guest_tree.configure(cursor="hand2")
                    return

        # Reset cursor
        self.guest_tree.configure(cursor="")

    def on_tree_click(self, event):
        """Handle click on tree for check-in button."""
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
        # Station columns start at index 3 (after id, first, last)
        if column_index >= 3 and column_index < 3 + len(self.config['stations']):
            values = self.guest_tree.item(item, "values")

            # Only proceed if it says "Check-in"
            if len(values) > column_index and values[column_index] == "Check-in":
                guest_id = int(values[0])  # Ensure guest_id is int
                station = self.config['stations'][column_index - 3]

                # Disable the click temporarily to prevent double-clicks
                self.guest_tree.configure(cursor="wait")
                self.after(1000, lambda: self.guest_tree.configure(cursor=""))

                self.quick_checkin(guest_id, station)

    def quick_checkin(self, guest_id, station=None):
        """Perform quick check-in for a guest at specific station."""
        if station is None:
            station = self.current_station

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
                # Delay refresh to ensure status is visible for minimum 2s
                self.after(2500, lambda: self.refresh_guest_data(user_initiated=False))
            else:
                self.after(0, self.update_status, f"Guest ID {guest_id} not found", "error")
        except Exception as e:
            self.logger.error(f"Manual check-in error: {e}")
            self.after(0, self.update_status, f"Check-in failed: {str(e)}", "error")

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
        color_map = {
            "normal": "#ffffff",
            "success": "#4CAF50",
            "error": "#f44336",
            "warning": "#ff9800",
            "info": "#2196F3"
        }
        color = color_map.get(status_type, "#ffffff")
        self.status_label.configure(text=message, text_color=color)

        # Auto-clear all messages after 2 seconds (except empty messages)
        if auto_clear and message and message.strip():
            self.after(2000, lambda: self._auto_clear_status(message))

    def _auto_clear_status(self, original_message: str):
        """Auto-clear status if it hasn't changed."""
        current_text = self.status_label.cget("text")
        if current_text == original_message:
            # Determine appropriate replacement message based on current mode
            if self.is_rewrite_mode:
                self.update_status(self.STATUS_CHECKIN_PAUSED, "warning", False)
            elif self.settings_visible:
                # Clear message in settings mode
                self.update_status("", "normal", False)
            else:
                # Use appropriate ready message for current mode
                self.update_status(self.get_ready_status_message(), "normal", False)

    def load_logo(self):
        """Load and display logo."""
        try:
            logo_path = Path(__file__).parent.parent.parent / "assets" / "logo.png"
            if logo_path.exists():
                logo_image = Image.open(logo_path)
                logo_image = logo_image.resize((70, 70), Image.Resampling.LANCZOS)
                logo_ctk = ctk.CTkImage(light_image=logo_image, dark_image=logo_image, size=(70, 70))
                self.logo_label.configure(image=logo_ctk)
                self.logo_label.image = logo_ctk
        except Exception as e:
            self.logger.error(f"Failed to load logo: {e}")

    def on_closing(self):
        """Handle window closing."""
        self.is_scanning = False
        if self.nfc_service:
            self.nfc_service.disconnect()
        self.destroy()


def create_gui(config, nfc_service, sheets_service, tag_manager, logger):
    """Create and run the GUI application."""
    app = NFCApp(config, nfc_service, sheets_service, tag_manager, logger)
    return app
