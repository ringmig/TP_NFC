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

        # First check if tag is already registered
        self.update_status("Tap tag to check registration...", "info")
        
        # Disable UI during tag check
        self.rewrite_btn.configure(state="disabled")
        self.rewrite_id_entry.configure(state="disabled")
        self.exit_rewrite_btn.configure(state="disabled")

        # Start tag check operation
        thread = threading.Thread(target=self._check_tag_registration_thread, args=(guest_id,))
        thread.daemon = True
        thread.start()

    def _check_tag_registration_thread(self, guest_id: int):
        """Thread to check if tag is already registered."""
        try:
            # Read tag to check registration
            tag = self.nfc_service.read_tag(timeout=5)
            
            if not tag:
                # No tag detected
                self.after(0, self._enable_rewrite_ui)
                self.after(0, self.update_status, "No tag detected", "error")
                return
                
            # Check if tag is registered
            if tag.uid in self.tag_manager.tag_registry:
                # Tag is registered - get current guest info
                current_guest_id = self.tag_manager.tag_registry[tag.uid]
                self.logger.info(f"Tag {tag.uid} is registered to guest ID {current_guest_id}")
                
                current_guest = self.sheets_service.find_guest_by_id(current_guest_id)
                new_guest = self.sheets_service.find_guest_by_id(guest_id)
                
                # Log guest info for debugging
                if current_guest:
                    self.logger.info(f"Current guest: {current_guest.full_name}")
                else:
                    self.logger.warning(f"Current guest ID {current_guest_id} not found in sheets")
                    
                if new_guest:
                    self.logger.info(f"New guest: {new_guest.full_name}")
                else:
                    self.logger.warning(f"New guest ID {guest_id} not found in sheets")
                
                if current_guest and new_guest:
                    # Show confirmation popup with tag data stored
                    self.after(0, self._show_rewrite_confirmation, 
                             current_guest.full_name, new_guest.full_name, guest_id, tag)
                else:
                    # One or both guests not found - still proceed but with warning
                    current_name = current_guest.full_name if current_guest else f"Guest ID {current_guest_id}"
                    new_name = new_guest.full_name if new_guest else f"Guest ID {guest_id}"
                    self.after(0, self._show_rewrite_confirmation, current_name, new_name, guest_id, tag)
            else:
                # Tag is clean - proceed with direct rewrite
                self.logger.info(f"Tag {tag.uid} is not registered - proceeding with direct write")
                self.after(0, self._proceed_with_direct_rewrite, guest_id, tag)
                
        except Exception as e:
            self.logger.error(f"Error checking tag registration: {e}", exc_info=True)
            self.after(0, self._enable_rewrite_ui)
            self.after(0, self.update_status, "Error reading tag", "error")
    
    def _enable_rewrite_ui(self):
        """Re-enable rewrite UI elements."""
        self.rewrite_btn.configure(state="normal")
        self.rewrite_id_entry.configure(state="normal")
        self.exit_rewrite_btn.configure(state="normal")
    
    def _show_rewrite_confirmation(self, current_name: str, new_name: str, guest_id: int, tag):
        """Show confirmation dialog for rewriting a registered tag."""
        # Re-enable UI first
        self._enable_rewrite_ui()
        
        # Log for debugging
        self.logger.info(f"Showing rewrite confirmation: {current_name} -> {new_name}")
        
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
        
        # Current registration info - ensure name is displayed
        current_text = f"Currently registered to:\n{current_name if current_name else 'Unknown Guest'}"
        current_label = ctk.CTkLabel(
            main_frame,
            text=current_text,
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
        
        # New registration info - ensure name is displayed
        new_text = f"Will be rewritten to:\n{new_name if new_name else 'Unknown Guest'}"
        new_label = ctk.CTkLabel(
            main_frame,
            text=new_text,
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
            # Update status
            self.update_status("Rewriting tag...", "info")
            # Disable UI during rewrite
            self.rewrite_btn.configure(state="disabled")
            self.rewrite_id_entry.configure(state="disabled")
            self.exit_rewrite_btn.configure(state="disabled")
            
            # Proceed directly with the rewrite using the tag we already have
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
        
        cancel_btn = ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=confirm_window.destroy,
            width=120,
            height=45,
            font=self.fonts['button'],
            fg_color="#6c757d",
            hover_color="#5a6268"
        )
        cancel_btn.pack(side="left", padx=10)
    
    def _proceed_with_direct_rewrite(self, guest_id: int, tag):
        """Proceed with direct rewrite for clean tags."""
        # Update status
        self.update_status("Writing to tag...", "info")
        
        # Execute rewrite using the already-detected tag
        thread = threading.Thread(target=self._execute_rewrite_thread, args=(guest_id, tag))
        thread.daemon = True
        thread.start()
    
    def _execute_rewrite_thread(self, guest_id: int, tag):
        """Execute the actual rewrite operation."""
        try:
            self.logger.info(f"Executing rewrite for guest ID {guest_id} with tag {tag.uid}")
            
            # Use the tag that was already detected - no need to read again
            result = self.tag_manager.register_tag_to_guest_with_existing_tag(guest_id, tag)
            
            if result:
                self.logger.info(f"Rewrite successful: {result}")
            else:
                self.logger.error("Rewrite returned None result")
            
            # Update UI in main thread
            self.after(0, self._rewrite_complete, result)
            
        except Exception as e:
            self.logger.error(f"Rewrite operation error: {e}", exc_info=True)
            self.after(0, self._rewrite_complete, None)
    
    def _rewrite_complete(self, result: Optional[Dict]):
        """Handle rewrite completion."""
        self._enable_rewrite_ui()
        
        if result:
            self.update_status(f"✓ Tag rewritten to {result['guest_name']}", "success")
            
            # Clear form after delay
            self.after(2000, self.clear_rewrite_form)
            
            # Refresh guest list to update any status
            self.after(2500, lambda: self.refresh_guest_data(False))
        else:
            self.update_status("Failed to rewrite tag", "error")
        
        self.rewrite_id_entry.focus()
    
    def clear_rewrite_form(self):
        """Clear the rewrite form."""
        self.rewrite_id_entry.delete(0, 'end')
        self.update_status(self.STATUS_CHECKIN_PAUSED, "warning")
            
        self.rewrite_id_entry.focus()
    
    def clear_rewrite_form(self):
        """Clear the rewrite form."""
        self.rewrite_id_entry.delete(0, 'end')
        self.update_status(self.STATUS_CHECKIN_PAUSED, "warning")
            
    def _show_rewrite_confirmation(self, current_guest_name: str, new_guest_name: str, guest_id: int, tag):
        """Show confirmation dialog for rewriting registered tag."""
        # Re-enable UI first
        self._enable_rewrite_ui()
        
        # Create confirmation dialog
        confirm_window = ctk.CTkToplevel(self)
        confirm_window.title("Confirm Tag Rewrite")
        confirm_window.geometry("400x300")
        confirm_window.transient(self)
        confirm_window.grab_set()
        
        # Center window
        confirm_window.update_idletasks()
        x = (confirm_window.winfo_screenwidth() // 2) - (confirm_window.winfo_width() // 2)
        y = (confirm_window.winfo_screenheight() // 2) - (confirm_window.winfo_height() // 2)
        confirm_window.geometry(f"+{x}+{y}")
        
        # Main frame
        main_frame = ctk.CTkFrame(confirm_window)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Warning icon and title
        title_label = ctk.CTkLabel(
            main_frame,
            text="⚠️ Tag Already Registered",
            font=CTkFont(size=18, weight="bold"),
            text_color="#ff9800"
        )
        title_label.pack(pady=(10, 20))
        
        # Current assignment
        current_label = ctk.CTkLabel(
            main_frame,
            text=f"Currently registered to:\n{current_guest_name}",
            font=CTkFont(size=14),
            justify="center"
        )
        current_label.pack(pady=(0, 10))
        
        # Arrow
        arrow_label = ctk.CTkLabel(
            main_frame,
            text="↓",
            font=CTkFont(size=20, weight="bold"),
            text_color="#ff9800"
        )
        arrow_label.pack(pady=5)
        
        # New assignment
        new_label = ctk.CTkLabel(
            main_frame,
            text=f"Rewrite to:\n{new_guest_name}",
            font=CTkFont(size=14, weight="bold"),
            text_color="#4CAF50",
            justify="center"
        )
        new_label.pack(pady=(10, 20))
        
        # Buttons
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(pady=10)
        
        def proceed_rewrite():
            confirm_window.destroy()
            self._proceed_with_direct_rewrite(guest_id, tag)
        
        rewrite_btn = ctk.CTkButton(
            button_frame,
            text="Rewrite",
            command=proceed_rewrite,
            width=100,
            height=40,
            corner_radius=8,
            font=CTkFont(size=14, weight="bold"),
            fg_color="#ff9800",
            hover_color="#f57c00"
        )
        rewrite_btn.pack(side="left", padx=10)
        
        cancel_btn = ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=confirm_window.destroy,
            width=100,
            height=40,
            corner_radius=8,
            font=CTkFont(size=14, weight="bold"),
            fg_color="#6c757d",
            hover_color="#5a6268"
        )
        cancel_btn.pack(side="left", padx=10)
    
    def _proceed_with_direct_rewrite(self, guest_id: int, tag):
        """Proceed with rewrite using already-detected tag."""
        # Verify guest exists
        guest = self.sheets_service.find_guest_by_id(guest_id)
        if not guest:
            self.update_status(f"Guest ID {guest_id} not found", "error")
            return
        
        # Perform the rewrite directly using the detected tag
        try:
            # Log the change if tag was previously registered
            if tag.uid in self.tag_manager.tag_registry:
                existing_id = self.tag_manager.tag_registry[tag.uid]
                existing_guest = self.sheets_service.find_guest_by_id(existing_id)
                existing_name = existing_guest.full_name if existing_guest else f"ID {existing_id}"
                self.logger.info(f"Overwriting tag {tag.uid} from {existing_name} to {guest.full_name}")
            
            # Register the tag directly
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
            
            self._rewrite_complete(result)
            
        except Exception as e:
            self.logger.error(f"Error during direct rewrite: {e}")
            self.update_status("Rewrite failed", "error")
        """Show confirmation dialog for rewriting registered tag."""
        # Re-enable UI first
        self._enable_rewrite_ui()
        
        # Create confirmation dialog
        confirm_window = ctk.CTkToplevel(self)
        confirm_window.title("Confirm Tag Rewrite")
        confirm_window.geometry("400x400")
        confirm_window.transient(self)
        confirm_window.grab_set()
        
        # Center window
        confirm_window.update_idletasks()
        x = (confirm_window.winfo_screenwidth() // 2) - (confirm_window.winfo_width() // 2)
        y = (confirm_window.winfo_screenheight() // 2) - (confirm_window.winfo_height() // 2)
        confirm_window.geometry(f"+{x}+{y}")
        
        # Main content frame
        main_frame = ctk.CTkFrame(confirm_window)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        
        # Current guest info
        current_label = ctk.CTkLabel(
            main_frame,
            text="Tag is currently registered to:",
            font=CTkFont(size=14)
        )
        current_label.pack(pady=(0, 5))
        
        current_name_label = ctk.CTkLabel(
            main_frame,
            text=current_guest_name,
            font=CTkFont(size=18, weight="bold"),
            text_color="#2196F3"
        )
        current_name_label.pack(pady=(20, 20))
        
        # Arrow
        arrow_label = ctk.CTkLabel(
            main_frame,
            text="↓",
            font=CTkFont(size=24, weight="bold")
        )
        arrow_label.pack(pady=(20, 20))
        
        # New guest info
        new_label = ctk.CTkLabel(
            main_frame,
            text="Rewrite to:",
            font=CTkFont(size=14)
        )
        new_label.pack(pady=(0, 5))
        
        new_name_label = ctk.CTkLabel(
            main_frame,
            text=new_guest_name,
            font=CTkFont(size=18, weight="bold"),
            text_color="#2196F3"
        )
        new_name_label.pack(pady=(0, 20))
        
        # Warning
        warning_label = ctk.CTkLabel(
            main_frame,
            text="⚠️ This will overwrite the current registration",
            font=CTkFont(size=14, weight="bold"),
            text_color="#ff9800"
        )
        warning_label.pack(pady=(0, 30))
        
        # Buttons frame
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=(0, 10))
        
        # Cancel button
        cancel_btn = ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=confirm_window.destroy,
            width=120,
            height=40,
            corner_radius=8,
            font=CTkFont(size=14, weight="bold"),
            fg_color="#6c757d",
            hover_color="#5a6268"
        )
        cancel_btn.pack(side="left", padx=(0, 10))
        
        # Rewrite button (orange)
        rewrite_btn = ctk.CTkButton(
            button_frame,
            text="Rewrite",
            command=lambda: self._confirm_rewrite(confirm_window, guest_id, tag_uid),
            width=120,
            height=40,
            corner_radius=8,
            font=CTkFont(size=14, weight="bold"),
            fg_color="#ff9800",
            hover_color="#f57c00"
        )
        rewrite_btn.pack(side="right")
        
    def _confirm_rewrite(self, confirm_window, guest_id: int, tag_uid: str):
        """Confirm and execute the rewrite operation."""
        confirm_window.destroy()
        
        # Store the tag UID for rewrite operation
        self._rewrite_tag_uid = tag_uid
        
        # Proceed with rewrite
        self._proceed_with_rewrite(guest_id)
        
    def _enable_rewrite_ui(self):
        """Re-enable rewrite UI elements."""
        self.rewrite_btn.configure(state="normal")
        self.rewrite_id_entry.configure(state="normal")
        self.exit_rewrite_btn.configure(state="normal")
        
    def _proceed_with_rewrite(self, guest_id: int):
        """Proceed with the rewrite operation."""
        # Re-enable UI
        self._enable_rewrite_ui()
        
        # Mark operation in progress
        self.operation_in_progress = True
        self._active_operations += 1
        
        # Disable UI during operation
        self.rewrite_btn.configure(state="disabled")
        self.rewrite_id_entry.configure(state="disabled")
        self.exit_rewrite_btn.configure(state="disabled")
        
        # Show cancel button
        self.rewrite_cancel_btn = ctk.CTkButton(
            self.rewrite_btn.master,
            text="Cancel",
            command=self.cancel_rewrite,
            width=80,
            height=50,
            font=self.fonts['button'],
            corner_radius=8,
            fg_color="#dc3545",
            hover_color="#c82333"
        )
        self.rewrite_cancel_btn.pack(side="left", padx=(10, 0))
        
        # Start rewrite operation
        self._rewrite_operation_active = True
        self._countdown_rewrite_band(guest_id, 10)
        
        # Start the actual rewrite operation in background
        thread = threading.Thread(target=self._rewrite_to_band_thread, args=(guest_id,))
        thread.daemon = True
        thread.start()
        
    def cancel_rewrite(self):
        """Cancel rewrite operation."""
        self._rewrite_operation_active = False
        self._active_operations -= 1
        self.operation_in_progress = False
        self.nfc_service.cancel_read()
        self.update_status("Rewrite operation cancelled", "warning")
        self._cleanup_rewrite_ui()
        
    def _cleanup_rewrite_ui(self):
        """Clean up rewrite operation UI."""
        self._enable_rewrite_ui()
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
            self._rewrite_complete(None)
            
    def _rewrite_to_band_thread(self, guest_id: int):
        """Thread function for rewriting to band."""
        try:
            # If we have a specific tag UID from confirmation, rewrite that tag
            if hasattr(self, '_rewrite_tag_uid'):
                # Clear the existing registration first
                self.tag_manager.clear_tag(self._rewrite_tag_uid)
                delattr(self, '_rewrite_tag_uid')
            
            # Use 10-second timeout to match countdown
            result = self.tag_manager.register_tag_to_guest(guest_id)
            
            # Always stop countdown when thread completes
            self._rewrite_operation_active = False
            
            # Update UI in main thread
            self.after(0, self._rewrite_complete, result)
            
        except Exception as e:
            # Stop countdown on error
            self._rewrite_operation_active = False
            self.logger.error(f"Rewrite operation error: {e}")
            self.after(0, self._rewrite_complete, None)
            
    def _rewrite_complete(self, result: Optional[Dict]):
        """Handle rewrite completion."""
        # Mark operation complete
        self.operation_in_progress = False
        self._active_operations -= 1
        
        # Clean up UI
        self._cleanup_rewrite_ui()
        
        if result:
            self.update_status(f"✓ Tag rewritten to {result['guest_name']}", "success")
            
            # Clear form after delay
            self.after(2000, self.clear_rewrite_form)
            
            # Refresh guest list after delay
            self.after(2500, lambda: self.refresh_guest_data(False))
        else:
            self.update_status("No tag detected", "error")
            
        self.rewrite_id_entry.focus()
        
    def clear_rewrite_form(self):
        """Clear the rewrite form."""
        self.rewrite_id_entry.delete(0, 'end')
        self.update_status(self.STATUS_CHECKIN_PAUSED, "warning")
        separator.pack(pady=10)
        
        # New registration info
        new_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        new_frame.pack(pady=(10, 20))
        
        new_text = ctk.CTkLabel(
            new_frame,
            text="Rewrite to:",
            font=self.fonts['body'],
            text_color="#ffffff"  # White normal text as requested
        )
        new_text.pack()
        
        new_guest = ctk.CTkLabel(
            new_frame,
            text=new_guest_name,
            font=CTkFont(size=18, weight="bold"),
            text_color="#2196F3"  # Blue for consistency
        )
        new_guest.pack(pady=(5, 0))
        
        # Warning
        warning_label = ctk.CTkLabel(
            main_frame,
            text="⚠️ This will overwrite the current registration",
            font=self.fonts['body'],
            text_color="#ff9800"
        )
        warning_label.pack(pady=(10, 20))
        
        # Buttons
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(pady=(0, 10))
        
        def confirm_rewrite():
            confirm_window.destroy()
            self._proceed_with_rewrite(guest_id)
            
        def cancel_rewrite():
            confirm_window.destroy()
            self.update_status("Rewrite cancelled", "warning")
            
        confirm_btn = ctk.CTkButton(
            button_frame,
            text="Yes, Rewrite",
            command=confirm_rewrite,
            width=120,
            height=40,
            corner_radius=8,
            font=self.fonts['button'],
            fg_color="#ff9800",
            hover_color="#f57c00"
        )
        confirm_btn.pack(side="left", padx=(0, 10))
        
        cancel_btn = ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=cancel_rewrite,
            width=100,
            height=40,
            corner_radius=8,
            font=self.fonts['button'],
            fg_color="#6c757d",
            hover_color="#5a6268"
        )
        cancel_btn.pack(side="left")
        
    def _enable_rewrite_ui(self):
        """Re-enable rewrite UI elements."""
        if hasattr(self, 'rewrite_btn'):
            self.rewrite_btn.configure(state="normal")
        if hasattr(self, 'rewrite_id_entry'):
            self.rewrite_id_entry.configure(state="normal")
        if hasattr(self, 'exit_rewrite_btn'):
            self.exit_rewrite_btn.configure(state="normal")
            
    def _proceed_with_rewrite(self, guest_id: int):
        """Proceed with rewriting the tag."""
        # Mark operation in progress
        self.operation_in_progress = True
        self._active_operations += 1
        
        # Disable UI during operation
        self.rewrite_btn.configure(state="disabled")
        self.rewrite_id_entry.configure(state="disabled")
        self.exit_rewrite_btn.configure(state="disabled")
        
        # Show cancel button
        self.rewrite_cancel_btn = ctk.CTkButton(
            self.rewrite_btn.master,
            text="Cancel",
            command=self.cancel_rewrite,
            width=80,
            height=50,
            font=self.fonts['button'],
            corner_radius=8,
            fg_color="#dc3545",
            hover_color="#c82333"
        )
        self.rewrite_cancel_btn.pack(side="left", padx=(10, 0))
        
        # Start countdown and operation
        self._rewrite_operation_active = True
        self._countdown_rewrite(guest_id, 10)
        
        thread = threading.Thread(target=self._rewrite_to_band_thread, args=(guest_id,))
        thread.daemon = True
        thread.start()
        
    def cancel_rewrite(self):
        """Cancel rewrite operation."""
        self._rewrite_operation_active = False
        self._active_operations -= 1
        self.operation_in_progress = False
        self.nfc_service.cancel_read()
        self.update_status("Rewrite cancelled", "warning")
        self._cleanup_rewrite_ui()
        
    def _cleanup_rewrite_ui(self):
        """Clean up rewrite operation UI."""
        self._enable_rewrite_ui()
        if hasattr(self, 'rewrite_cancel_btn'):
            self.rewrite_cancel_btn.destroy()
            delattr(self, 'rewrite_cancel_btn')
            
    def _countdown_rewrite(self, guest_id: int, countdown: int):
        """Show countdown for rewrite operation."""
        if countdown > 0 and self._rewrite_operation_active:
            self.update_status(f"Tap wristband now... {countdown}s", "info", False)
            self.after(1000, lambda: self._countdown_rewrite(guest_id, countdown - 1))
        elif self._rewrite_operation_active:
            # Timeout reached
            self._rewrite_operation_active = False
            self.update_status("No tag detected", "error")
            self._rewrite_complete(None)
            
    def _rewrite_to_band_thread(self, guest_id: int):
        """Thread function for rewriting to band."""
        try:
            result = self.tag_manager.register_tag_to_guest(guest_id)
            
            # Always stop countdown when thread completes
            self._rewrite_operation_active = False
            
            # Update UI in main thread
            self.after(0, self._rewrite_complete, result)
            
        except Exception as e:
            # Stop countdown on error
            self._rewrite_operation_active = False
            self.logger.error(f"Rewrite operation error: {e}")
            self.after(0, self._rewrite_complete, None)
            
    def _rewrite_complete(self, result: Optional[Dict]):
        """Handle rewrite completion."""
        # Mark operation complete
        self.operation_in_progress = False
        self._active_operations -= 1
        
        # Clean up UI
        self._cleanup_rewrite_ui()
        
        if result:
            self.update_status(f"✓ Tag rewritten to {result['guest_name']}", "success")
            # Clear form after delay
            self.after(2000, self.clear_rewrite_form)
            # Refresh guest list
            self.after(2500, lambda: self.refresh_guest_data(False))
        else:
            self.update_status("No tag detected", "error")
            
        if hasattr(self, 'rewrite_id_entry'):
            self.rewrite_id_entry.focus()
            
    def clear_rewrite_form(self):
        """Clear the rewrite form."""
        if hasattr(self, 'rewrite_id_entry'):
            self.rewrite_id_entry.delete(0, 'end')
        self.update_status(self.STATUS_CHECKIN_PAUSED, "warning")