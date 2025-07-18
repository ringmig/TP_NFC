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
        self.guest_list_visible = False
        self.checkin_buttons_visible = False  # Hidden by default
        self.guests_data = []
        self.is_scanning = False

        # Window setup
        self.title(config['ui']['window_title'])
        self.geometry(f"{config['ui']['window_width']}x{config['ui']['window_height']}")
        self.minsize(500, 400)

        # Start in fullscreen
        try:
            self.state('zoomed')  # Windows fullscreen
        except:
            try:
                self.attributes('-zoomed', True)  # Linux fullscreen
            except:
                try:
                    self.attributes('-fullscreen', True)  # macOS fullscreen
                except:
                    pass  # Fallback to windowed mode

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

        # Handle window close
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

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

        # Content frame (switches based on mode)
        self.content_frame = ctk.CTkFrame(self.main_frame, corner_radius=15)
        self.content_frame.pack(fill="both", expand=True, pady=(20, 10))

        # Status bar
        self.create_status_bar()

        # Action buttons
        self.create_action_buttons()

        # Guest list panel (initially hidden)
        self.create_guest_list_panel()

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

        # Station selector centered
        station_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        station_frame.place(relx=0.5, rely=0.5, anchor="center")

        station_label = ctk.CTkLabel(
            station_frame,
            text="Station:",
            font=CTkFont(size=18, weight="bold")
        )
        station_label.pack(side="left", padx=(0, 15))

        self.station_var = tk.StringVar(value=self.current_station)
        self.station_dropdown = ctk.CTkComboBox(
            station_frame,
            values=self.config['stations'],
            variable=self.station_var,
            command=self.on_station_change,
            width=200,
            height=40,
            font=CTkFont(size=16, weight="bold"),
            state="readonly",
            button_hover_color="#2563eb",
            dropdown_hover_color="#1e40af"
        )
        self.station_dropdown.pack(side="left")

    def create_status_bar(self):
        """Create status bar."""
        self.status_frame = ctk.CTkFrame(self.main_frame, corner_radius=10, height=50)
        self.status_frame.pack(fill="x", pady=(10, 10))
        self.status_frame.pack_propagate(False)

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

        # Toggle guest list button on the left
        self.toggle_list_btn = ctk.CTkButton(
            button_frame,
            text="Show Guest List ▼",
            command=self.toggle_guest_list,
            width=150,
            height=35,
            corner_radius=8,
            font=self.fonts['button']
        )
        self.toggle_list_btn.pack(side="left", padx=5)

        # Right frame for other buttons
        right_frame = ctk.CTkFrame(button_frame, fg_color="transparent")
        right_frame.pack(side="right")

        # Erase tag button
        self.erase_btn = ctk.CTkButton(
            right_frame,
            text="Erase Tag",
            command=self.erase_tag,
            width=100,
            height=35,
            corner_radius=8,
            font=self.fonts['button'],
            fg_color="#dc3545",
            hover_color="#c82333"
        )
        self.erase_btn.pack(side="left", padx=5)

        # Refresh button
        self.refresh_btn = ctk.CTkButton(
            button_frame,
            text="Refresh",
            command=self.refresh_guest_data,
            width=100,
            height=35,
            corner_radius=8,
            font=self.fonts['button']
        )
        self.refresh_btn.pack(side="left", padx=5)

        # Manual check-in button
        self.manual_checkin_btn = ctk.CTkButton(
            right_frame,
            text="Manual Check-In",
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
        """Create collapsible guest list panel."""
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

        # Treeview
        self.guest_tree = ttk.Treeview(
            tree_frame,
            columns=("id", "first", "last", "status", "action"),
            show="headings",
            yscrollcommand=scrollbar.set,
            height=8
        )
        scrollbar.configure(command=self.guest_tree.yview)

        # Configure columns
        self.guest_tree.heading("id", text="Guest ID", anchor="w")
        self.guest_tree.heading("first", text="First Name", anchor="w")
        self.guest_tree.heading("last", text="Last Name", anchor="w")
        self.guest_tree.heading("status", text="Check-In Time", anchor="w")
        self.guest_tree.heading("action", text="", anchor="w")

        self.guest_tree.column("id", width=60, anchor="w")  # Left align
        self.guest_tree.column("first", width=120, anchor="w")
        self.guest_tree.column("last", width=120, anchor="w")
        self.guest_tree.column("status", width=100, anchor="w")
        self.guest_tree.column("action", width=120, anchor="e")  # Right align

        # Style for treeview
        style = ttk.Style()
        style.theme_use("clam")

        # Configure treeview colors
        style.configure("Treeview",
                       background="#212121",
                       foreground="white",
                       fieldbackground="#212121",
                       borderwidth=0)
        style.configure("Treeview.Heading",
                       background="#323232",
                       foreground="white",
                       borderwidth=0)

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
        for col in ("id", "first", "last", "status"):
            self.guest_tree.heading(col, command=lambda c=col: self.sort_treeview(c))

        self.guest_tree.pack(fill="both", expand=True)

        # Sorting state
        self.sort_reverse = {}

    def sort_treeview(self, col):
        """Sort treeview by column."""
        # Get all items
        items = [(self.guest_tree.set(k, col), k) for k in self.guest_tree.get_children('')]

        # Check if we need numeric sort for ID column
        if col == "id":
            items.sort(key=lambda x: int(x[0]) if x[0].isdigit() else 0, reverse=self.sort_reverse.get(col, False))
        else:
            items.sort(reverse=self.sort_reverse.get(col, False))

        # Rearrange items
        for index, (val, k) in enumerate(items):
            self.guest_tree.move(k, '', index)

        # Toggle sort direction for next click
        self.sort_reverse[col] = not self.sort_reverse.get(col, False)

    def update_mode_content(self):
        """Update content based on current mode."""
        # Clear current content
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        # Update button visibility - always show manual check-in button
        self.manual_checkin_btn.pack(side="left", padx=5)
        self.manual_checkin_btn.configure(text="Manual Check-in")

        if self.is_registration_mode:
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
            text="Enter Guest ID:",
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
        # Clean up UI
        self._cleanup_write_ui()

        if result:
            self.update_status(f"✓ Registered to {result['guest_name']}", "success")
            self.guest_name_label.configure(text=result['guest_name'])

            # Also check in at Reception
            try:
                timestamp = datetime.now().strftime("%H:%M")
                self.sheets_service.mark_attendance(result['original_id'], "Reception", timestamp)
                self.logger.info(f"Also checked in {result['guest_name']} at Reception")
            except Exception as e:
                self.logger.error(f"Failed to check in at Reception: {e}")

            # Clear form after delay
            self.after(2000, self.clear_registration_form)

            # Refresh guest list to show check-in
            self.refresh_guest_data()
        else:
            self.update_status("No tag detected", "error")

        self.id_entry.focus()

    def clear_registration_form(self):
        """Clear the registration form."""
        self.id_entry.delete(0, 'end')
        self.guest_name_label.configure(text="")
        self.update_status("Ready", "normal")

    def start_checkpoint_scanning(self):
        """Start continuous scanning for checkpoint mode."""
        if not self.is_registration_mode and not self.is_scanning:
            self.is_scanning = True
            self._checkpoint_scan_loop()

    def _checkpoint_scan_loop(self):
        """Continuous scanning loop for checkpoint mode."""
        if not self.is_registration_mode and self.is_scanning:
            # Start scan in thread
            thread = threading.Thread(target=self._scan_for_checkin)
            thread.daemon = True
            thread.start()

    def _scan_for_checkin(self):
        """Scan for check-in (thread function)."""
        result = self.tag_manager.process_checkpoint_scan(self.current_station)

        # Update UI in main thread
        self.after(0, self._checkin_complete, result)

    def _checkin_complete(self, result: Optional[Dict]):
        """Handle check-in completion."""
        if result:
            self.checkpoint_status.configure(
                text=f"✓ {result['guest_name']} checked in at {result['timestamp']}",
                text_color="#4CAF50"
            )
            self.update_status(f"Checked in: {result['guest_name']}", "success")

            # Refresh guest list to show updated check-in status
            if self.guest_list_visible:
                self.refresh_guest_data()

            # Reset after delay
            self.after(3000, lambda: self.checkpoint_status.configure(
                text="Waiting for tap...",
                text_color="#ffffff"
            ))

        # Continue scanning after a short delay
        if self.is_scanning and not self.is_registration_mode:
            self.after(1000, self._checkpoint_scan_loop)

    def on_station_change(self, station: str):
        """Handle station change."""
        self.current_station = station
        self.is_registration_mode = (station == "Reception")

        # Stop scanning if leaving checkpoint mode
        if self.is_registration_mode:
            self.is_scanning = False

        self.update_mode_content()
        self.update_status(f"Switched to {station}", "info")

        # Auto-refresh guest list to show station-specific check-ins
        self.refresh_guest_data()

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

        # Update button text
        if self.checkin_buttons_visible:
            self.manual_checkin_btn.configure(text="Hide Check-in Buttons")
        else:
            self.manual_checkin_btn.configure(text="Manual Check-in")

        # Refresh guest table to show/hide check-in buttons
        if self.guest_list_visible:
            self._update_guest_table(self.guests_data)

    def refresh_guest_data(self):
        """Refresh guest data from Google Sheets."""
        self.update_status("Refreshing data...", "info")

        # Run in thread
        thread = threading.Thread(target=self._refresh_guest_data_thread)
        thread.daemon = True
        thread.start()

    def _refresh_guest_data_thread(self):
        """Thread function for refreshing data."""
        try:
            guests = self.sheets_service.get_all_guests()
            self.after(0, self._update_guest_table, guests)
        except Exception as e:
            self.after(0, self.update_status, f"Failed to refresh: {str(e)}", "error")

    def _update_guest_table(self, guests: List):
        """Update the guest table with new data."""
        self.guests_data = guests

        # Clear table
        for item in self.guest_tree.get_children():
            self.guest_tree.delete(item)

        # Add guests
        for i, guest in enumerate(guests):
            # Show check-in status for current station
            check_in_time = guest.get_check_in_time(self.current_station.lower())
            if check_in_time:
                status = f"✓ {check_in_time}"
            else:
                status = "-"

            # Show check-in button only if checkin_buttons_visible and not checked in
            action = ""
            if self.checkin_buttons_visible and not check_in_time:
                action = "Check-in"

            item = self.guest_tree.insert("", "end", values=(
                guest.original_id,
                guest.firstname,
                guest.lastname,
                status,
                action
            ))

            # Apply row coloring based on check-in status
            if check_in_time:
                # Row is green when checked in
                self.guest_tree.item(item, tags=("checked_in",))
                self.guest_tree.tag_configure("checked_in", background="#2d5a2d", foreground="white")
            else:
                # Normal row color when not checked in
                self.guest_tree.item(item, tags=("not_checked_in",))
                self.guest_tree.tag_configure("not_checked_in", background="#212121", foreground="white")

        # Only show "Loaded X guests" message at startup
        if not hasattr(self, '_initial_load_complete'):
            self.update_status(f"Loaded {len(guests)} guests", "success")
            self.after(2000, lambda: self.update_status("Ready", "normal"))
            self._initial_load_complete = True

    def filter_guest_list(self):
        """Filter guest list based on search."""
        search_term = self.search_var.get().lower()

        # Clear table
        for item in self.guest_tree.get_children():
            self.guest_tree.delete(item)

        # Add filtered guests
        for guest in self.guests_data:
            if (search_term in str(guest.original_id) or
                search_term in guest.firstname.lower() or
                search_term in guest.lastname.lower()):
                # Show check-in status for current station
                check_in_time = guest.get_check_in_time(self.current_station.lower())
                if check_in_time:
                    status = f"✓ {check_in_time}"
                else:
                    status = "-"

                # Show check-in button only if checkin_buttons_visible and not checked in
                action = ""
                if self.checkin_buttons_visible and not check_in_time:
                    action = "Check-in"

                item = self.guest_tree.insert("", "end", values=(
                    guest.original_id,
                    guest.firstname,
                    guest.lastname,
                    status,
                    action
                ))

                # Apply row coloring based on check-in status
                if check_in_time:
                    # Row is green when checked in
                    self.guest_tree.item(item, tags=("checked_in",))
                    self.guest_tree.tag_configure("checked_in", background="#2d5a2d", foreground="white")
                else:
                    # Normal row color when not checked in
                    self.guest_tree.item(item, tags=("not_checked_in",))
                    self.guest_tree.tag_configure("not_checked_in", background="#212121", foreground="white")

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
            elif self.is_manual_checkin_mode:
                # Fill manual check-in form
                self.manual_id_entry.delete(0, 'end')
                self.manual_id_entry.insert(0, str(guest_id))

    def on_tree_motion(self, event):
        """Handle mouse motion over tree for cursor changes."""
        # Get the item and column under mouse
        item = self.guest_tree.identify("item", event.x, event.y)
        column = self.guest_tree.identify("column", event.x, event.y)

        # Check if hovering over check-in button
        if item and column == "#5":
            values = self.guest_tree.item(item, "values")
            if len(values) > 4 and values[4] == "Check-in":
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

        # Only handle clicks on the action column (5th column)
        if column != "#5":
            return

        # Get current values
        values = self.guest_tree.item(item, "values")
        action_text = values[4]  # Action is the 5th value

        # Only proceed if it says "Check-in"
        if action_text != "Check-in":
            return

        # Get guest ID and perform check-in
        guest_id = values[0]
        self.quick_checkin(guest_id)

    def quick_checkin(self, guest_id):
        """Perform quick check-in for a guest."""
        # Update status
        self.update_status(f"Checking in guest {guest_id}...", "info")

        # Run in thread
        thread = threading.Thread(target=self._quick_checkin_thread,
                                args=(guest_id, self.current_station))
        thread.daemon = True
        thread.start()

    def _quick_checkin_thread(self, guest_id: int, station: str):
        """Thread function for quick check-in."""
        try:
            # Get current time
            timestamp = datetime.now().strftime("%H:%M")

            # Mark attendance
            success = self.sheets_service.mark_attendance(guest_id, station, timestamp)

            if success:
                self.after(0, self.refresh_guest_data)
                self.after(0, self.update_status, f"✓ Checked in guest {guest_id}", "success")
            else:
                self.after(0, self.update_status, f"Failed to check in guest {guest_id}", "error")
        except Exception as e:
            self.after(0, self.update_status, f"Error: {str(e)}", "error")

    def erase_tag(self):
        """Erase tag functionality."""
        # Disable button during operation
        self.erase_btn.configure(state="disabled")

        # Show cancel button
        self.erase_cancel_btn = ctk.CTkButton(
            self.erase_btn.master,
            text="Cancel",
            command=self.cancel_erase,
            width=80,
            height=35,
            font=self.fonts['button'],
            corner_radius=8,
            fg_color="#dc3545",
            hover_color="#c82333"
        )
        self.erase_cancel_btn.pack(side="left", padx=(0, 5), before=self.erase_btn)

        # Start tag detection immediately with countdown display
        self._erase_operation_active = True
        self._countdown_erase_tag(10)

        # Start the actual erase operation in background
        thread = threading.Thread(target=self._erase_tag_thread)
        thread.daemon = True
        thread.start()

    def cancel_erase(self):
        """Cancel erase operation."""
        self._erase_operation_active = False
        self.nfc_service.cancel_read()
        self.update_status("Erase operation cancelled", "warning")
        self._cleanup_erase_ui()

    def _cleanup_erase_ui(self):
        """Clean up erase operation UI."""
        self.erase_btn.configure(state="normal")
        if hasattr(self, 'erase_cancel_btn'):
            self.erase_cancel_btn.destroy()
            delattr(self, 'erase_cancel_btn')

    def _countdown_erase_tag(self, countdown: int):
        """Show countdown for erase tag operation."""
        if countdown > 0 and self._erase_operation_active:
            self.update_status(f"Tap tag to erase... {countdown}s", "info", False)
            self.after(1000, lambda: self._countdown_erase_tag(countdown - 1))
        elif self._erase_operation_active:
            # Timeout reached
            self._erase_operation_active = False
            self.update_status("No tag detected", "error")
            self._erase_complete(None, False)

    def _erase_tag_thread(self):
        """Thread function for erasing tag."""
        # Use 10-second timeout to match countdown
        tag = self.nfc_service.read_tag(timeout=10)

        if tag and self._erase_operation_active:
            # Stop countdown and process erase
            self._erase_operation_active = False
            success = self.tag_manager.clear_tag(tag.uid)
            self.after(0, self._erase_complete, tag.uid, success)
        # If no tag and operation still active, let countdown handle timeout

    def _erase_complete(self, tag_uid: Optional[str], success: bool):
        """Handle erase completion."""
        # Clean up UI
        self._cleanup_erase_ui()

        if success and tag_uid:
            self.update_status("✓ Tag erased", "success")
            # Delay refresh to let confirmation message show for 2s
            self.after(2000, self.refresh_guest_data)
        elif tag_uid:
            self.update_status("Tag was not registered", "warning")
        else:
            self.update_status("No tag detected", "error")

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

        # Auto-fade to "Ready" after 2 seconds for non-normal messages
        if auto_fade and status_type != "normal":
            # Cancel any existing fade timer
            if hasattr(self, '_fade_timer'):
                self.after_cancel(self._fade_timer)
            # Set new fade timer
            self._fade_timer = self.after(2000, lambda: self.update_status("Ready", "normal", False))

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
