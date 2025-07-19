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
        self.after(100, self.refresh_guest_data)

        # Set up sync completion callback to update UI when background syncs complete
        self.tag_manager.set_sync_completion_callback(self.on_sync_complete)

        # Handle window close
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def setup_fullscreen(self):
        """Configure safe fullscreen behavior without system modifications."""
        system = platform.system()

        try:
            if system == "Darwin":  # macOS
                # Use simple window maximization instead of true fullscreen
                self.attributes('-zoomed', True)
                self.logger.info("macOS window maximized")

            elif system == "Windows":
                self.state('zoomed')
                self.logger.info("Windows window maximized")

            elif system == "Linux":
                self.attributes('-zoomed', True)
                self.logger.info("Linux window maximized")

        except Exception as e:
            self.logger.warning(f"Window maximization failed: {e}")
            # Fallback to manual fullscreen using screen dimensions
            try:
                width = self.winfo_screenwidth()
                height = self.winfo_screenheight()
                self.geometry(f"{width}x{height}+0+0")
                self.logger.info("Using geometry-based fullscreen")
            except Exception as e2:
                self.logger.warning(f"Geometry fallback failed: {e2}")

        # Add F11 to toggle maximized state
        self.bind('<F11>', self.toggle_fullscreen)

        # Add refresh shortcuts (Cmd+R on Mac, Ctrl+R on Windows/Linux)
        if system == "Darwin":  # macOS
            self.bind('<Command-r>', self.on_refresh_shortcut)
        else:  # Windows/Linux
            self.bind('<Control-r>', self.on_refresh_shortcut)

    def toggle_fullscreen(self, event=None):
        """Toggle between maximized and normal window state."""
        system = platform.system()

        try:
            if system == "Darwin":
                # Toggle macOS maximized state
                current_state = self.attributes('-zoomed')
                self.attributes('-zoomed', not current_state)

            elif system == "Windows":
                if self.state() == 'zoomed':
                    self.state('normal')
                    self.geometry(f"{self.config['ui']['window_width']}x{self.config['ui']['window_height']}")
                else:
                    self.state('zoomed')

            elif system == "Linux":
                current_state = self.attributes('-zoomed')
                self.attributes('-zoomed', not current_state)

        except Exception as e:
            self.logger.error(f"Error toggling fullscreen: {e}")

    def on_refresh_shortcut(self, event=None):
        """Handle refresh keyboard shortcut (Cmd+R / Ctrl+R)."""
        self.refresh_guest_data()
        return "break"  # Prevent default browser refresh behavior

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
        self.status_frame = ctk.CTkFrame(self.main_frame, corner_radius=10, height=50)
        self.status_frame.pack(fill="x", pady=(10, 10))
        self.status_frame.pack_propagate(False)

        # Center - main status
        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="Ready",
            font=self.fonts['status']
        )
        self.status_label.pack(expand=True)

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

        # Map item states to colors
        style.map('Treeview',
                  background=[('selected', '#4a4a4a')],
                  foreground=[('selected', 'white')])

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

        # Hide status bar only when Reception is in registration mode
        if self.current_station == "Reception" and self.is_registration_mode and not self.is_checkpoint_mode:
            self.status_frame.pack_forget()

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
        checkin_label.pack(pady=(0, 40))

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

    def close_tag_info(self):
        """Close tag info display and return to normal mode."""
        self.is_displaying_tag_info = False
        self.tag_info_data = None

        # Always return to main view (not settings or rewrite)
        self.settings_visible = False
        self.is_rewrite_mode = False  # Reset rewrite mode
        if hasattr(self, '_came_from_settings'):
            delattr(self, '_came_from_settings')

        # Restore status bar if it was hidden
        self.status_frame.pack(fill="x", pady=(10, 10))

        self.update_mode_content()
        self.update_settings_button()  # Restore hamburger button

        # Resume scanning if in checkpoint mode
        if not self.is_registration_mode or self.is_checkpoint_mode:
            self.start_checkpoint_scanning()

        # Set appropriate status based on current mode
        if self.current_station == "Reception" and not self.is_checkpoint_mode:
            self.update_status("Ready. Waiting for tag registration", "normal")
        elif self.current_station == "Reception" and self.is_checkpoint_mode:
            self.update_status("Ready. Waiting for Check-In", "normal")
        else:
            self.update_status("Ready. Waiting for Check-In", "normal")

    def create_settings_content(self):
        """Create settings content in the main content area."""
        # Set appropriate status text based on mode - keep status bar visible
        if self.current_station == "Reception" and self.is_registration_mode and not self.is_checkpoint_mode:
            # Hide registration waiting text, keep status bar for other messages
            self.update_status("", "normal")
        elif self.is_checkpoint_mode or (not self.is_registration_mode):
            # Show check-in waiting text for check-in modes
            self.update_status("Ready. Waiting for Check-In", "normal")
        else:
            # Default for other stations
            self.update_status("Ready. Waiting for Check-In", "normal")

        # Main container that fills and centers content
        main_container = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        main_container.pack(fill="both", expand=True)

        # Center frame for all content
        center_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        center_frame.place(relx=0.5, rely=0.5, anchor="center")



        # Buttons container
        buttons_container = ctk.CTkFrame(center_frame, fg_color="transparent")
        buttons_container.pack()

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

        # Developer Mode button
        self.dev_mode_btn = ctk.CTkButton(
            buttons_container,
            text="Developer Mode",
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
            self.update_mode_content()
            # Return to appropriate status
            if self.is_rewrite_mode:
                self.update_status("Check-In Paused", "warning")
            else:
                self.update_status("Ready", "normal")
        else:
            self.settings_visible = True
            # Don't stop scanning when entering settings
            # Show appropriate status in settings
            if self.current_station == "Reception" and self.is_registration_mode and not self.is_checkpoint_mode:
                self.update_status("Ready. Waiting for tag registration", "normal")
            elif self.is_checkpoint_mode or (not self.is_registration_mode):
                self.update_status("Ready. Waiting for Check-In", "normal")
            else:
                self.update_status("Ready. Waiting for Check-In", "normal")
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
            # Show buttons when not in settings
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

        # Show Reception mode toggle only at Reception station
        if self.current_station == "Reception":
            self.reception_mode_btn.pack(side="left", padx=5)
            if self.is_checkpoint_mode:
                self.reception_mode_btn.configure(text="Switch to Registration Mode")
            else:
                self.reception_mode_btn.configure(text="Switch to Check-in Mode")
        else:
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
            text="Enter Guest ID or Tap Tag to Check:",
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

    def start_registration_tag_scanning(self):
        """Start background tag scanning for registration mode."""
        if self.is_registration_mode and not self.is_checkpoint_mode and not self.is_scanning:
            self.is_scanning = True
            self._registration_scan_loop()

    def _registration_scan_loop(self):
        """Background scanning loop for registration mode."""
        if self.is_registration_mode and not self.is_checkpoint_mode and self.is_scanning:
            thread = threading.Thread(target=self._scan_for_registration)
            thread.daemon = True
            thread.start()

    def _scan_for_registration(self):
        """Scan for tag info in registration mode."""
        # Don't scan if another operation is in progress
        if self.operation_in_progress:
            self.after(1000, self._registration_scan_loop)
            return

        self.operation_in_progress = True
        self._active_operations += 1

        tag = self.nfc_service.read_tag(timeout=3)

        if not tag:
            self.operation_in_progress = False
            self._active_operations -= 1
            self.after(100, self._registration_scan_loop)
            return

        # Check if tag is registered
        if tag.uid not in self.tag_manager.tag_registry:
            self.operation_in_progress = False
            self._active_operations -= 1
            self.after(0, self.update_status, "Unregistered tag - ready for new registration", "info")
            self.after(2000, self._restart_registration_scanning)
            return

        # Tag is registered - show info
        original_id = self.tag_manager.tag_registry[tag.uid]
        # Get fresh data from Google Sheets
        guest = self.sheets_service.find_guest_by_id(original_id)

        if guest:
            # Priority: Check both local data and Google Sheets
            station_lower = self.current_station.lower()

            # Get all check-in data
            local_check_ins = self.tag_manager.get_all_local_check_ins()
            guest_local_data = local_check_ins.get(original_id, {})

            # Check local data
            local_time = guest_local_data.get(station_lower)

            # Check Google Sheets data (already fetched fresh from find_guest_by_id)
            sheets_time = guest.get_check_in_time(station_lower)

            # Use whichever has data (Google Sheets takes precedence)
            checkin_time = sheets_time or local_time

            self.logger.debug(f"Check-in status for {original_id} at {station_lower}: Sheets={sheets_time}, Local={local_time}")

            if checkin_time:
                status_msg = f"{guest.firstname} {guest.lastname} already checked in at {self.current_station} at {checkin_time}"
                status_type = "warning"
            else:
                status_msg = f"{guest.firstname} {guest.lastname} - Registered but not checked in"
                status_type = "success"
        else:
            status_msg = f"Tag registered to ID {original_id}"
            status_type = "success"

        self.operation_in_progress = False
        self._active_operations -= 1
        self.after(0, self.update_status, status_msg, status_type)
        self.after(3000, self._restart_registration_scanning)

    def _restart_registration_scanning(self):
        """Restart registration scanning after showing tag info."""
        if self.is_registration_mode and not self.is_checkpoint_mode and self.is_scanning:
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
            entry_frame,
            text="✕",
            command=self.exit_rewrite_mode,
            width=50,
            height=50,
            corner_radius=8,
            font=CTkFont(size=20, weight="bold"),
            fg_color="#dc3545",
            hover_color="#c82333"
        )
        self.exit_rewrite_btn.pack(side="left", padx=(10, 0))

        # Guest name display (initially hidden)
        self.rewrite_guest_name_label = ctk.CTkLabel(
            center_frame,
            text="",
            font=self.fonts['heading'],
            text_color="#4CAF50"
        )
        self.rewrite_guest_name_label.pack(pady=(20, 0))

        # Focus on entry
        self.rewrite_id_entry.focus()

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
            self.update_status(f"Tap wristband now... {countdown}s", "info", False)
            self.after(1000, lambda: self._countdown_write_band(guest_id, countdown - 1))
        elif self._write_operation_active:
            # Timeout reached
            self._write_operation_active = False
            self.update_status("No tag detected", "error")
            self._write_complete(None)

    def _write_to_band_thread(self, guest_id: int):
        """Thread function for writing to band."""
        # Use 5-second timeout to match countdown
        result = self.tag_manager.register_tag_to_guest(guest_id)

        # Stop countdown and update UI in main thread
        if result:
            self._write_operation_active = False
            self.after(0, self._write_complete, result)
        # If no result and operation still active, let countdown handle timeout

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
            self.after(2500, lambda: self.refresh_guest_data(False))
        else:
            self.update_status("No tag detected", "error")

        self.id_entry.focus()

    def clear_registration_form(self):
        """Clear the registration form."""
        self.id_entry.delete(0, 'end')
        self.guest_name_label.configure(text="")
        # Show appropriate status based on mode
        if self.is_rewrite_mode:
            self.update_status("Check-In Paused", "warning")
        elif not self.settings_visible:
            self.update_status("Ready", "normal")

    def toggle_reception_mode(self):
        """Toggle between Registration and Checkpoint mode at Reception."""
        if self.current_station == "Reception":
            self.is_checkpoint_mode = not self.is_checkpoint_mode
            if self.is_checkpoint_mode:
                self.is_scanning = False  # Stop any existing scanning
                self.update_status("Switched to Check-in Mode", "info")
            else:
                self.is_scanning = False  # Stop checkpoint scanning
                self.update_status("Switched to Registration Mode", "info")
            self.update_mode_content()

    def start_checkpoint_scanning(self):
        """Start continuous scanning for checkpoint mode."""
        # Allow checkpoint scanning at Reception if in checkpoint mode
        if (not self.is_registration_mode or self.is_checkpoint_mode) and not self.is_scanning:
            self.is_scanning = True
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
        self.operation_in_progress = True
        self._active_operations += 1

        # Read NFC tag first
        tag = self.nfc_service.read_tag(timeout=5)

        if not tag:
            self.operation_in_progress = False
            self._active_operations -= 1
            # Continue scanning after short delay
            self.after(100, self._restart_scanning_after_timeout)
            return

        # Check if tag is registered
        if tag.uid not in self.tag_manager.tag_registry:
            self.operation_in_progress = False
            self._active_operations -= 1
            self.after(0, self.update_status, "Unregistered tag", "error")
            # Continue scanning after showing error
            self.after(2000, self._restart_scanning_after_error)
            return

        original_id = self.tag_manager.tag_registry[tag.uid]

        # Get guest info and check for duplicates
        guest = self.sheets_service.find_guest_by_id(original_id)
        if guest:
            try:
                # Check both Google Sheets and local queue with error handling (consistent lowercase)
                sheets_checkin = guest.is_checked_in_at(self.current_station.lower())
                local_checkin = self.tag_manager.check_in_queue.has_check_in(original_id, self.current_station.lower())

                if sheets_checkin or local_checkin:
                    self.operation_in_progress = False
                    self._active_operations -= 1
                    guest_name = getattr(guest, 'firstname', 'Unknown') + ' ' + getattr(guest, 'lastname', '')
                    self.after(0, self.update_status, f"{guest_name.strip()} already checked in at {self.current_station}", "warning")
                    # Continue scanning after showing duplicate warning
                    self.after(2000, self._restart_scanning_after_duplicate)
                    return
            except Exception as e:
                self.logger.error(f"Error checking duplicate status: {e}")
                # Continue with check-in if duplicate check fails

        # Process normal check-in
        result = self.tag_manager.process_checkpoint_scan_with_tag(tag, self.current_station)
        self.operation_in_progress = False
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
        in_checkin_mode = not self.is_registration_mode or self.is_checkpoint_mode
        allow_during_tag_info = self.is_displaying_tag_info and in_checkin_mode

        should_scan = (in_checkin_mode and self.is_scanning) or allow_during_tag_info
        if should_scan:
            self._checkpoint_scan_loop()

    def _restart_scanning_after_error(self):
        """Restart scanning after error (unregistered tag)."""
        in_checkin_mode = not self.is_registration_mode or self.is_checkpoint_mode
        allow_during_tag_info = self.is_displaying_tag_info and in_checkin_mode

        should_scan = (in_checkin_mode and self.is_scanning) or allow_during_tag_info
        if should_scan:
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
        """Erase tag functionality from settings panel."""
        # Stop background scanning to prevent NFC conflicts
        self.is_scanning = False

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

    def cancel_erase_settings(self):
        """Cancel erase operation from settings."""
        self._erase_operation_active = False
        self.nfc_service.cancel_read()
        self.update_status("Erase cancelled", "warning")
        self._cleanup_erase_settings()

    def _cleanup_erase_settings(self):
        """Clean up erase UI in settings."""
        self.settings_erase_btn.configure(state="normal")
        if hasattr(self, 'erase_cancel_btn'):
            self.erase_cancel_btn.destroy()
            delattr(self, 'erase_cancel_btn')

    def _countdown_erase_settings(self, countdown: int):
        """Countdown for erase in settings."""
        if countdown > 0 and self._erase_operation_active:
            self.update_status(f"Tap tag to erase... {countdown}s", "info", False)
            self.after(1000, lambda: self._countdown_erase_settings(countdown - 1))
        elif self._erase_operation_active:
            self._erase_operation_active = False
            self.update_status("No tag detected", "error")
            self._erase_complete_settings(None, False)

    def _erase_tag_thread_settings(self):
        """Thread for erase operation in settings."""
        tag = self.nfc_service.read_tag(timeout=10)
        if tag and self._erase_operation_active:
            self._erase_operation_active = False
            success = self.tag_manager.clear_tag(tag.uid)
            self.after(0, self._erase_complete_settings, tag.uid, success)

    def _erase_complete_settings(self, tag_uid: Optional[str], success: bool):
        """Handle erase completion in settings."""
        self._cleanup_erase_settings()
        if success and tag_uid:
            self.update_status("✓ Tag erased", "success")
            self.after(2000, self.refresh_guest_data)
        elif tag_uid:
            self.update_status("Tag was not registered", "warning")
        else:
            self.update_status("No tag detected", "error")

    def tag_info(self):
        """Show tag information functionality."""
        # Allow tag info even during background scanning (different NFC operation)
        if self._active_operations > 1:  # Allow if only background scanning is active
            self.update_status("Another operation in progress", "warning")
            return

        # Stop background scanning to prevent NFC conflicts
        self.is_scanning = False

        # Track if we came from settings
        if self.settings_visible:
            self._came_from_settings = True

        # Mark operation in progress
        self.operation_in_progress = True
        self._active_operations += 1

        # Disable button during operation
        self.tag_info_btn.configure(state="disabled")

        # Create cancel button underneath
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

        self.update_status("Tag info cancelled", "warning")
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
            self.update_status(f"Tap tag for info... {countdown}s", "info", False)
            self.after(1000, lambda: self._countdown_tag_info(countdown - 1))
        elif self._tag_info_operation_active:
            self._tag_info_operation_active = False
            self.operation_in_progress = False
            self._active_operations -= 1
            self.update_status("No tag detected", "error")
            self._tag_info_complete(None)

    def _tag_info_thread(self):
        """Thread for tag info operation."""
        try:
            tag = self.nfc_service.read_tag(timeout=10)
            if tag and self._tag_info_operation_active:
                self._tag_info_operation_active = False
                self.operation_in_progress = False
                self._active_operations -= 1
                info = self.tag_manager.get_tag_info(tag.uid)
                self.after(0, self._tag_info_complete, info)
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
            # Find guest details
            guest = self.sheets_service.find_guest_by_id(tag_info['original_id'])

            if guest:
                # Clear settings mode and switch to inline display mode
                self.settings_visible = False
                self.is_displaying_tag_info = True
                self.tag_info_data = {
                    'guest': guest,
                    'check_ins': tag_info['check_ins']
                }
                self.update_mode_content()
                self.update_settings_button()  # Hide hamburger button when in tag info mode

                # Resume background scanning only if in check-in mode
                if self.is_checkpoint_mode or (not self.is_registration_mode):
                    self.start_checkpoint_scanning()
                    # Show appropriate status for check-in mode
                    if self.current_station == "Reception" and self.is_checkpoint_mode:
                        self.update_status("Ready. Waiting for Check-In", "normal")
                    else:
                        self.update_status("Ready. Waiting for Check-In", "normal")
                else:
                    # Registration mode - no background scanning during tag info
                    self.update_status("Ready. Waiting for tag registration", "normal")
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
        log_window.grab_set()

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
        password_window.title("Developer Mode")
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
        title_label = ctk.CTkLabel(main_frame, text="⚠️ Developer Mode ⚠️", font=self.fonts['heading'])
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
                self.after(1000, self.refresh_guest_data)
            else:
                self.after(0, self.update_status, "Failed to clear Google Sheets data", "error")

        except Exception as e:
            self.logger.error(f"Error clearing data: {e}")
            self.after(0, self.update_status, f"Error clearing data: {str(e)}", "error")

    def rewrite_tag(self):
        """Enter rewrite tag mode."""
        # Stop background scanning to prevent NFC conflicts
        self.is_scanning = False

        self.settings_visible = False
        self.is_rewrite_mode = True
        self.is_registration_mode = False  # Ensure registration mode is off
        self.update_settings_button()
        self.update_mode_content()
        self.update_status("Check-In Paused", "warning")


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

        self.current_station = station
        self.is_registration_mode = (station == "Reception")

        # Reset checkpoint mode when leaving Reception
        if station != "Reception":
            self.is_checkpoint_mode = False

        # Stop scanning if leaving checkpoint mode
        if self.is_registration_mode and not self.is_checkpoint_mode:
            self.is_scanning = False

        # Update button highlighting
        self.update_station_buttons()

        self.update_mode_content()
        self.update_status(f"Switched to {station}", "info")

        # Auto-refresh guest list to show station-specific check-ins
        self.refresh_guest_data()

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
        self.guest_tree.tag_configure("checkin_hover", background="#2196F3")

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
            self.update_status("Refreshing data...", "info")

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
            self.after(0, self.update_status, "Using cached data (Google Sheets offline)", "warning")

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
        self.guest_tree.tag_configure("checkin_hover", background="#2196F3")

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
                self.after(2000, lambda: self.update_status("Check-In Paused", "warning"))
            elif self.current_station == "Reception" and not self.is_checkpoint_mode:
                self.after(2000, lambda: self.update_status("Ready. Waiting for tag registration", "normal"))
            elif self.current_station == "Reception" and self.is_checkpoint_mode:
                self.after(2000, lambda: self.update_status("Ready. Waiting for Check-In", "normal"))
            else:
                self.after(2000, lambda: self.update_status("Ready. Waiting for Check-In", "normal"))
            self._initial_load_complete = True
        elif hasattr(self, '_is_user_initiated_refresh') and self._is_user_initiated_refresh:
            # Show confirmation for any user-initiated refresh (button or shortcut)
            self.update_status(f"✓ Refreshed {len(guests)} guests", "success")
            delattr(self, '_is_user_initiated_refresh')  # Clean up flag
        elif self.is_rewrite_mode:
            # In rewrite mode, go straight to paused status
            self.update_status("Check-In Paused", "warning")
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
        """Filter guest list based on search."""
        search_term = self.search_var.get().lower()

        # Get all local check-ins
        local_check_ins = self.tag_manager.get_all_local_check_ins()

        # Clear table
        for item in self.guest_tree.get_children():
            self.guest_tree.delete(item)

        # Add filtered guests
        for guest in self.guests_data:
            if (search_term in str(guest.original_id) or
                search_term in guest.firstname.lower() or
                search_term in guest.lastname.lower()):

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

        self.is_rewrite_mode = False
        self.settings_visible = False
        self.is_registration_mode = (self.current_station == "Reception")
        self.update_settings_button()
        self.update_mode_content()

        # Resume scanning if in checkpoint mode
        if not self.is_registration_mode or self.is_checkpoint_mode:
            self.start_checkpoint_scanning()

        # Restore operational status
        self.update_status("Ready", "normal")

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

        # Disable UI during operation
        self.rewrite_btn.configure(state="disabled")
        self.rewrite_id_entry.configure(state="disabled")
        self.exit_rewrite_btn.configure(state="disabled")  # Hide X button during operation

        # Show cancel button
        self.rewrite_cancel_btn = ctk.CTkButton(
            self.rewrite_btn.master,
            text="Cancel",
            command=self.cancel_rewrite_band,
            width=80,
            height=50,
            font=self.fonts['button'],
            corner_radius=8,
            fg_color="#dc3545",
            hover_color="#c82333"
        )
        self.rewrite_cancel_btn.pack(side="left", padx=(10, 0))

        # Start tag detection immediately with countdown display
        self._rewrite_operation_active = True
        self._countdown_rewrite_band(guest_id, 10)

        # Start the actual rewrite operation in background
        thread = threading.Thread(target=self._rewrite_to_band_thread, args=(guest_id,))
        thread.daemon = True
        thread.start()

    def cancel_rewrite_band(self):
        """Cancel rewrite operation."""
        self._rewrite_operation_active = False
        self.nfc_service.cancel_read()
        self.update_status("Rewrite operation cancelled", "warning")
        self._cleanup_rewrite_band_ui()

    def _cleanup_rewrite_band_ui(self):
        """Clean up rewrite operation UI."""
        self.rewrite_btn.configure(state="normal")
        self.rewrite_id_entry.configure(state="normal")
        self.exit_rewrite_btn.configure(state="normal")  # Re-enable X button
        if hasattr(self, 'rewrite_cancel_btn'):
            self.rewrite_cancel_btn.destroy()
            delattr(self, 'rewrite_cancel_btn')

    def _countdown_rewrite_band(self, guest_id: int, countdown: int):
        """Show countdown for rewrite band operation."""
        if countdown > 0 and self._rewrite_operation_active:
            self.update_status(f"Tap wristband now... {countdown}s", "info", False)
            self.after(1000, lambda: self._countdown_rewrite_band(guest_id, countdown - 1))
        elif self._rewrite_operation_active:
            # Timeout reached
            self._rewrite_operation_active = False
            self.update_status("No tag detected", "error")
            self._rewrite_band_complete(None)

    def _rewrite_to_band_thread(self, guest_id: int):
        """Thread function for rewriting to band."""
        # Use 10-second timeout to match countdown
        result = self.tag_manager.rewrite_tag_to_guest(guest_id)

        # Stop countdown and update UI in main thread
        if result:
            self._rewrite_operation_active = False  # Stop countdown
            self.after(0, self._rewrite_band_complete, result)
        # If no result and operation still active, let countdown handle timeout

    def _rewrite_band_complete(self, result: Optional[Dict]):
        """Handle rewrite completion."""
        # Clean up UI
        self._cleanup_rewrite_band_ui()

        if result:
            # Show confirmation in label only (not duplicate in status)
            self.rewrite_guest_name_label.configure(text=f"✓ Rewritten for {result['guest_name']}")

            # Clear the input field
            self.rewrite_id_entry.delete(0, 'end')

            # Fade the success message after 4 seconds
            self.after(4000, lambda: self.rewrite_guest_name_label.configure(text=""))

            # Delay refresh to ensure confirmation is visible
            self.after(2500, self.refresh_guest_data)
        else:
            self.update_status("No tag detected", "error")

        self.rewrite_id_entry.focus()

    def show_rewrite_success_buttons(self):
        """Show success buttons after rewrite completion."""
        # Create success button frame with more padding
        success_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        success_frame.place(relx=0.5, rely=0.8, anchor="center")

        # Rewrite another button
        rewrite_another_btn = ctk.CTkButton(
            success_frame,
            text="Rewrite Another Tag",
            command=self.clear_rewrite_form,
            width=200,
            height=40,
            corner_radius=8,
            font=self.fonts['button'],
            fg_color="#ff9800",
            hover_color="#f57c00"
        )
        rewrite_another_btn.pack(pady=20)

    def return_to_checkin_mode(self):
        """Return to normal check-in mode."""
        self.is_rewrite_mode = False
        self.current_station = "Reception"  # Default to reception
        self.is_registration_mode = True
        self.update_station_buttons()
        self.update_mode_content()

    def clear_rewrite_form(self):
        """Clear the rewrite form and hide success buttons."""
        self.rewrite_id_entry.delete(0, 'end')
        self.rewrite_guest_name_label.configure(text="")
        # Only show "Ready" when not in settings mode
        if not self.settings_visible:
            self.update_status("Ready", "normal")
        # Recreate the rewrite content to remove success buttons
        self.update_mode_content()

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

                self.quick_checkin_at_station(guest_id, station)

    def quick_checkin_at_station(self, guest_id, station):
        """Perform quick check-in for a guest at a specific station."""
        # Find guest name for better feedback
        guest_name = "Unknown"
        for guest in self.guests_data:
            if guest.original_id == guest_id:
                guest_name = guest.full_name
                break

        # Update status
        self.update_status(f"Checking in {guest_name} at {station}...", "info")

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
                # Update status first
                self.after(0, self.update_status, f"✓ Checked in {result['guest_name']} at {station}", "success")
                # Exit manual check-in mode
                self.after(50, self.toggle_manual_checkin)
                # Delay refresh to ensure status is visible for minimum 2s
                self.after(2500, self.refresh_guest_data)
            else:
                self.after(0, self.update_status, f"Guest ID {guest_id} not found", "error")
        except Exception as e:
            self.logger.error(f"Manual check-in error: {e}")
            self.after(0, self.update_status, f"Check-in failed: {str(e)}", "error")



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

    def update_status(self, message: str, status_type: str = "normal", auto_fade: bool = True):
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

        # Auto-fade after 2 seconds for non-normal messages (except countdown messages)
        if auto_fade and status_type != "normal" and not "..." in message:
            # Cancel any existing fade timer
            if hasattr(self, '_fade_timer'):
                self.after_cancel(self._fade_timer)
            # Set new fade timer - fade to appropriate status based on mode
            def fade_to_default():
                if self.is_rewrite_mode:
                    self.update_status("Check-In Paused", "warning", False)
                elif self.current_station == "Reception" and not self.is_checkpoint_mode:
                    self.update_status("Ready. Waiting for tag registration", "normal", False)
                elif self.current_station == "Reception" and self.is_checkpoint_mode:
                    self.update_status("Ready. Waiting for Check-In", "normal", False)
                else:
                    self.update_status("Ready. Waiting for Check-In", "normal", False)
            self._fade_timer = self.after(2000, fade_to_default)

    def on_sync_complete(self):
        """Called when background sync completes - silently update UI."""
        # Refresh guest data silently (no status messages)
        self.refresh_guest_data(user_initiated=False)

    def _force_sync_on_startup(self):
        """Force sync of pending items on startup."""
        try:
            pending_count = self.tag_manager.check_in_queue.force_sync()
            if pending_count == 0:
                self.logger.info("All pending syncs completed successfully")
                # Update sync status after successful sync
                self.after(500, self._update_sync_status_after_force)
            else:
                self.logger.warning(f"{pending_count} items still pending after force sync")
        except Exception as e:
            self.logger.error(f"Error during startup force sync: {e}")

    def _update_sync_status_after_force(self):
        """Update sync status after force sync completes."""
        registry_stats = self.tag_manager.get_registry_stats()
        if registry_stats['pending_syncs'] == 0:
            self.sync_status_label.configure(text="✓ All synced", text_color="#4CAF50")

    def on_closing(self):
        """Handle window closing."""
        self.is_scanning = False
        if self.tag_manager:
            self.tag_manager.shutdown()
        if self.nfc_service:
            self.nfc_service.disconnect()
        self.destroy()



def create_gui(config, nfc_service, sheets_service, tag_manager, logger):
    """Create and run the GUI application."""
    app = NFCApp(config, nfc_service, sheets_service, tag_manager, logger)
    return app
