#!/usr/bin/env python3
"""
TP_NFC Android - Fixed Mobile UI Design
"""

from kivy.app import App
from kivy.config import Config
# Set window size to mobile portrait before importing other modules
Config.set('graphics', 'width', '400')
Config.set('graphics', 'height', '700')
Config.set('graphics', 'resizable', False)

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.widget import Widget
from kivy.uix.image import Image
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle, RoundedRectangle, Ellipse, Line
from kivy.metrics import dp
import os
from datetime import datetime
import json
import logging
from pathlib import Path

# Check if running on Android
try:
    from jnius import autoclass
    ANDROID = True
except ImportError:
    ANDROID = False

# Import services from Android folder
from src.services.google_sheets_service import GoogleSheetsService
from src.models.guest_record import GuestRecord

# For phone calls
try:
    from plyer import call
    PLYER_AVAILABLE = True
except ImportError:
    PLYER_AVAILABLE = False
    import webbrowser  # Fallback for desktop testing

class ModernButton(Button):
    """Clean modern button with proper mobile styling"""
    def __init__(self, **kwargs):
        self.bg_color = kwargs.pop('bg_color', (0.2, 0.6, 1, 1))
        self.text_color = kwargs.pop('text_color', (1, 1, 1, 1))
        self.is_outline = kwargs.pop('is_outline', False)
        self.outline_color = kwargs.pop('outline_color', (0.2, 0.6, 1, 1))
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_down = ''
        self.background_color = (0, 0, 0, 0)  # Transparent
        self.bind(pos=self.update_graphics, size=self.update_graphics)
        # Force text color after widget is created
        Clock.schedule_once(self.set_text_color, 0)
        Clock.schedule_once(self.update_graphics, 0)
        
    def set_text_color(self, *args):
        """Force text color to be visible"""
        self.color = self.text_color
        
    def update_graphics(self, *args):
        if not self.canvas:
            return
        self.canvas.before.clear()
        with self.canvas.before:
            if self.is_outline:
                # Draw outline only - NO FILL
                Color(*self.outline_color)
                Line(rounded_rectangle=(self.pos[0]+1.5, self.pos[1]+1.5, self.size[0]-3, self.size[1]-3, dp(12)), width=2.5)
            else:
                # Filled button
                Color(*self.bg_color)
                RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(12)])

class HamburgerMenu(Button):
    """Hamburger menu with white background and black dots"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_down = ''
        self.background_color = (0, 0, 0, 0)
        self.bind(pos=self.update_graphics, size=self.update_graphics)
        Clock.schedule_once(self.update_graphics, 0)
        
    def update_graphics(self, *args):
        if not self.canvas:
            return
        self.canvas.before.clear()
        with self.canvas.before:
            # No outline, just dots on transparent background
            Color(1, 1, 1, 1)  # White dots
            dot_size = dp(3)
            dot_spacing = dp(5)
            center_y = self.pos[1] + self.size[1] / 2
            start_dot_x = self.pos[0] + (self.size[0] - (3 * dot_size + 2 * dot_spacing)) / 2
            dot_y = center_y - dot_size / 2
            
            Ellipse(pos=(start_dot_x, dot_y), size=(dot_size, dot_size))
            Ellipse(pos=(start_dot_x + dot_size + dot_spacing, dot_y), size=(dot_size, dot_size))
            Ellipse(pos=(start_dot_x + 2 * (dot_size + dot_spacing), dot_y), size=(dot_size, dot_size))

class GuestListItem(BoxLayout):
    """Clean guest list item with proper spacing and long press support"""
    def __init__(self, guest_id, name, status="-", is_even=False, app=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = dp(56)  # Material Design list item height
        self.padding = [dp(16), dp(8)]
        self.spacing = dp(12)
        self.guest_id = guest_id
        self.guest_name = name
        self.app = app
        self.touch_time = None
        self.long_press_triggered = False
        
        # Background - DARK MODE
        with self.canvas.before:
            if is_even:
                Color(0.15, 0.15, 0.15, 1)  # Dark gray for alternating rows
            else:
                Color(0.1, 0.1, 0.1, 1)  # Darker black
            self.bg_rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self._update_bg, pos=self._update_bg)
        
        # Guest ID - WHITE TEXT, LEFT ALIGNED
        id_label = Label(
            text=str(guest_id),
            size_hint_x=None,
            width=dp(40),
            font_size=dp(14),
            color=(1, 1, 1, 1),  # White text
            halign='left',  # Left aligned
            valign='middle'
        )
        id_label.bind(size=id_label.setter('text_size'))
        
        # Name - WHITE TEXT
        name_label = Label(
            text=name,
            font_size=dp(16),
            color=(1, 1, 1, 1),  # White text
            halign='left',
            valign='middle',
            bold=True
        )
        name_label.bind(size=name_label.setter('text_size'))
        
        # Status
        self.status_label = Label(
            text=status,
            size_hint_x=None,
            width=dp(100),
            font_size=dp(14),
            color=(0.2, 0.7, 0.2, 1) if status != "-" else (0.7, 0.7, 0.7, 1),
            halign='right',
            valign='middle'
        )
        self.status_label.bind(size=self.status_label.setter('text_size'))
        
        # Store references to labels for selection feedback
        self.id_label = id_label
        self.name_label = name_label
        
        self.add_widget(id_label)
        self.add_widget(name_label)
        self.add_widget(self.status_label)
    
    def _update_bg(self, instance, value):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size
    
    def check_in(self):
        # Check if guest is already checked in at current station
        status_text = self.status_label.text.strip().lower()
        if status_text != "-" and status_text != "":
            if status_text == "x":
                # Guest marked absent - show different message
                if self.app:
                    self.app.show_warning_message('Guest marked as absent', 3)
            else:
                # Guest already checked in - show orange warning message
                if self.app:
                    self.app.show_warning_message('Guest already checked in', 3)
            return False  # Indicate check-in was not performed
        
        # Show timestamp instead of "Checked In"
        now = datetime.now()
        timestamp = now.strftime("%H:%M")
        self.status_label.text = timestamp
        self.status_label.color = (0.2, 0.7, 0.2, 1)
        
        # Update row appearance for checked-in state
        self.update_checkin_appearance()
        # Update Google Sheets if service is available
        if self.app and self.app.sheets_service:
            try:
                # Get current station from app
                current_station = self.app.current_station.lower()
                # Mark attendance in Google Sheets
                success = self.app.sheets_service.mark_attendance(
                    self.guest_id, 
                    current_station, 
                    timestamp
                )
                if success:
                    self.app.logger.info(f"Checked in guest {self.guest_id} at {current_station}")
                    # Update local guest data immediately
                    if self.guest_id in self.app.guest_data_map:
                        guest_record = self.app.guest_data_map[self.guest_id]
                        guest_record.check_ins[current_station] = timestamp
                        # Also update the variant with accent mark if it's Lío
                        if current_station == 'lío':
                            guest_record.check_ins['lio'] = timestamp
                        elif current_station == 'lio':
                            guest_record.check_ins['lío'] = timestamp
                else:
                    self.app.logger.error(f"Failed to update Google Sheets for guest {self.guest_id}")
            except Exception as e:
                self.app.logger.error(f"Error updating Google Sheets: {e}")
        
        return True  # Indicate successful check-in
    
    def mark_absent(self):
        """Mark guest as absent with red styling and update Google Sheets"""
        # Set status to absent marker
        self.status_label.text = "X"
        self.status_label.color = (0.8, 0.2, 0.2, 1)  # Red color
        
        # Update row appearance for absent state
        self.update_absent_appearance()
        
        # Update Google Sheets with absent marker
        if self.app and self.app.sheets_service:
            try:
                # Get current station from app
                current_station = self.app.current_station.lower()
                # Mark as absent in Google Sheets with "X" symbol
                success = self.app.sheets_service.mark_attendance(
                    self.guest_id, 
                    current_station, 
                    "X"
                )
                if success:
                    self.app.logger.info(f"Marked guest {self.guest_id} as absent at {current_station}")
                    # Update local guest data immediately
                    if self.guest_id in self.app.guest_data_map:
                        guest_record = self.app.guest_data_map[self.guest_id]
                        guest_record.check_ins[current_station] = "X"
                        # Also update the variant with accent mark if it's Lío
                        if current_station == 'lío':
                            guest_record.check_ins['lio'] = "X"
                        elif current_station == 'lio':
                            guest_record.check_ins['lío'] = "X"
                else:
                    self.app.logger.error(f"Failed to update Google Sheets for guest {self.guest_id} absent status")
            except Exception as e:
                self.app.logger.error(f"Error updating Google Sheets with absent status: {e}")
    
    def update_absent_appearance(self):
        """Update row appearance for absent guests (red background, dark text)"""
        # Red background
        self.canvas.before.clear()
        with self.canvas.before:
            Color(0.8, 0.2, 0.2, 1)  # Red background
            self.bg_rect = Rectangle(size=self.size, pos=self.pos)
        
        # Dark grey text for better contrast on red
        self.id_label.color = (0.2, 0.2, 0.2, 1)  # Dark grey
        self.name_label.color = (0.2, 0.2, 0.2, 1)  # Dark grey
        self.status_label.color = (0.2, 0.2, 0.2, 1)  # Dark grey X mark
    
    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.touch_time = Clock.get_time()
            self.long_press_triggered = False
            self.touch_pos = touch.pos  # Store the touch position
            # Schedule long press check (reduced to 0.3 seconds for better responsiveness)
            self.long_press_event = Clock.schedule_once(self.trigger_long_press, 0.3)
            return True
        return super().on_touch_down(touch)
    
    def on_touch_up(self, touch):
        # Cancel long press if it hasn't triggered yet
        if hasattr(self, 'long_press_event') and self.long_press_event:
            self.long_press_event.cancel()
            self.long_press_event = None
            
        if self.collide_point(*touch.pos) and not self.long_press_triggered:
            # Normal tap - check if in register workflow (but not during scanning)
            if (self.app and self.app.register_state in ['select_guest', 'ready_to_register'] 
                and self.app.scanning_mode != 'register'):
                self.app.select_guest_for_register(self)
            elif self.app and self.app.register_state == 'ready' and self.app.scanning_mode is None:
                # Show visual feedback for normal guest selection (orange highlight)
                self.show_selection_feedback()
        self.touch_time = None
        return super().on_touch_up(touch)
    
    def trigger_long_press(self, dt):
        """Trigger long press after timer expires"""
        if self.touch_time:  # Still being touched
            self.long_press_triggered = True
            if self.app:
                self.app.show_guest_menu(self)
    
    def show_selection_feedback(self):
        """Show orange selection feedback with dark grey text"""
        # Orange background with dark grey text
        self.canvas.before.clear()
        with self.canvas.before:
            Color(0.95, 0.4, 0.15, 1)  # Orange background
            self.bg_rect = Rectangle(size=self.size, pos=self.pos)
        
        # Change text colors to dark grey
        self.id_label.color = (0.2, 0.2, 0.2, 1)  # Dark grey
        self.name_label.color = (0.2, 0.2, 0.2, 1)  # Dark grey
        # Keep status label color unchanged (green or grey)
        
        # Schedule return to normal after 0.3 seconds
        Clock.schedule_once(lambda dt: self.restore_normal_appearance(), 0.3)
    
    def update_checkin_appearance(self):
        """Update row appearance based on Google Sheets data"""
        status_text = self.status_label.text.strip().lower()
        
        if status_text == "x":
            # Absent - red background (from Google Sheets data)
            self.update_absent_appearance()
        elif status_text != "-" and status_text != "":
            # Checked in - green background (any non-empty, non-absent value)
            self.canvas.before.clear()
            with self.canvas.before:
                Color(0.2, 0.7, 0.2, 1)  # Green background
                self.bg_rect = Rectangle(size=self.size, pos=self.pos)
            
            # Dark grey text for better contrast on green
            self.id_label.color = (0.2, 0.2, 0.2, 1)  # Dark grey
            self.name_label.color = (0.2, 0.2, 0.2, 1)  # Dark grey
            self.status_label.color = (0.2, 0.2, 0.2, 1)  # Dark grey timestamp
        else:
            # Not checked in - restore normal appearance
            self.restore_normal_appearance()
    
    def restore_normal_appearance(self):
        """Restore normal row appearance after selection feedback"""
        # Check guest status based on Google Sheets data
        status_text = self.status_label.text.strip().lower()
        
        if status_text == "x":
            # Guest is marked absent - should have red background
            self.update_absent_appearance()
            return
        elif status_text != "-" and status_text != "":
            # Guest is checked in - should have green background
            self.update_checkin_appearance()
            return
        
        # Guest not checked in - use normal alternating colors
        # Determine if this is an even or odd row for alternating colors
        if hasattr(self.app, 'guest_rows'):
            try:
                row_index = self.app.guest_rows.index(self)
                is_even = (row_index % 2 == 0)
            except ValueError:
                is_even = True  # Fallback
        else:
            is_even = True  # Fallback
        
        # Restore background
        self.canvas.before.clear()
        with self.canvas.before:
            if is_even:
                Color(0.15, 0.15, 0.15, 1)  # Dark gray for alternating rows
            else:
                Color(0.1, 0.1, 0.1, 1)  # Darker black
            self.bg_rect = Rectangle(size=self.size, pos=self.pos)
        
        # Restore text colors to white
        self.id_label.color = (1, 1, 1, 1)  # White
        self.name_label.color = (1, 1, 1, 1)  # White
        # Status label color remains unchanged

class TPNFCApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.sheets_service = None
        self.guest_data = []
    
    def get_resource_path(self, relative_path):
        """Get correct file path for Android vs desktop"""
        if ANDROID:
            # On Android, files are in the app's private directory
            try:
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                app_dir = PythonActivity.mActivity.getFilesDir().getAbsolutePath()
                return os.path.join(app_dir, 'app', relative_path)
            except Exception:
                # Fallback to relative path if Android detection fails
                return relative_path
        else:
            # Desktop - use relative path
            return relative_path
    
    def init_google_sheets(self):
        """Initialize Google Sheets service and load guest data"""
        try:
            # Load config - use Android-aware path
            config_path = self.get_resource_path('config/config.json')
            self.logger.info(f"Looking for config at: {config_path}")
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            # Initialize sheets service
            self.sheets_service = GoogleSheetsService(
                config['google_sheets'],
                self.logger
            )
            
            # Authenticate
            if self.sheets_service.authenticate():
                # Fetch all guests
                self.guest_data = self.sheets_service.get_all_guests()
                self.logger.info(f"Loaded {len(self.guest_data)} guests from Google Sheets")
                return True
            else:
                self.logger.error("Failed to authenticate with Google Sheets")
                self.update_status("❌ ERROR: Google Sheets authentication failed. Check credentials.", "error")
                return False
                
        except FileNotFoundError as e:
            self.logger.error(f"Config file not found: {e}")
            self.update_status("❌ ERROR: Config files missing. Contact admin.", "error")
            return False
        except Exception as e:
            self.logger.error(f"Error initializing Google Sheets: {e}")
            self.update_status(f"❌ ERROR: Cannot connect to Google Sheets. {str(e)[:50]}...", "error") 
            return False
    
    def build(self):
        # Initialize logging
        self.logger = logging.getLogger('TPNFCApp')
        logging.basicConfig(level=logging.INFO)
        
        # Initialize current station early
        self.current_station = 'Reception'
        
        # Root container with dark background matching darkest row
        root = BoxLayout(orientation='vertical', spacing=0)
        with root.canvas.before:
            Color(0.1, 0.1, 0.1, 1)  # Same as darkest alternating row
            self.root_bg = Rectangle(size=root.size, pos=root.pos)
        root.bind(size=lambda instance, value: setattr(self.root_bg, 'size', value))
        root.bind(pos=lambda instance, value: setattr(self.root_bg, 'pos', value))
        
        # Status bar spacer
        spacer = Widget(size_hint_y=None, height=dp(20))
        root.add_widget(spacer)
        
        # Header bar
        header = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(56),
            padding=[dp(8), 0],
            spacing=dp(8)
        )
        
        # Header background - SAME AS ROOT
        with header.canvas.before:
            Color(0.1, 0.1, 0.1, 1)  # Same as root background
            self.header_bg = Rectangle(size=header.size, pos=header.pos)
        header.bind(size=self._update_header_bg, pos=self._update_header_bg)
        
        # Logo image - left aligned with NO PADDING
        # Get logo path using Android-aware method
        logo_path = self.get_resource_path('assets/logo.png')
        # Fallback to development path if not found
        if not os.path.exists(logo_path):
            logo_path = os.path.join('..', 'assets', 'logo.png')
        
        if logo_path:
            logo = Image(
                source=logo_path,
                size_hint_x=None,
                width=dp(60),
                fit_mode="contain"
            )
        else:
            logo = Label(
                text='TP NFC',
                font_size=dp(18),
                color=(1, 1, 1, 1),
                bold=True,
                size_hint_x=None,
                width=dp(60),
                halign='left'
            )
            logo.bind(size=logo.setter('text_size'))
        
        # Status text - Shows messages when needed, empty when idle
        self.status = Label(
            text='',  # Empty when idle
            font_size=dp(14),
            color=(1, 1, 1, 1),
            text_size=(None, None)  # Allow text to expand
        )
        
        # Hamburger menu
        menu_btn = HamburgerMenu(
            size_hint_x=None,
            width=dp(40)
        )
        menu_btn.bind(on_press=self.show_menu)
        
        header.add_widget(logo)
        header.add_widget(self.status)
        header.add_widget(menu_btn)
        root.add_widget(header)
        
        # Top action buttons - Tag Info and Register Tag (50/50 width)
        top_action_container = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(65),
            padding=[dp(16), dp(4)],
            spacing=dp(8)
        )
        
        # Tag Info button (50% width)
        self.tag_info_btn = ModernButton(
            text='Tag Info',
            text_color=(0.2, 0.6, 1, 1),
            is_outline=True,
            outline_color=(0.2, 0.6, 1, 1),
            font_size=dp(14),
            bold=True,
            size_hint_y=None,
            height=dp(50),
            size_hint_x=0.5  # 50% width
        )
        self.tag_info_btn.bind(on_press=self.handle_tag_info)
        
        # Register Tag button (50% width)
        self.register_btn = ModernButton(
            text='Register Tag',
            text_color=(0.95, 0.4, 0.15, 1),  # Orange text
            is_outline=True,
            outline_color=(0.95, 0.4, 0.15, 1),  # Orange outline
            font_size=dp(14),
            bold=True,
            size_hint_y=None,
            height=dp(50),
            size_hint_x=0.5  # 50% width
        )
        self.register_btn.bind(on_press=self.handle_register_workflow)
        
        top_action_container.add_widget(self.tag_info_btn)
        top_action_container.add_widget(self.register_btn)
        root.add_widget(top_action_container)
        
        # Check In Guest button - moved down with full width
        scan_container = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(80),  # Increased height for more padding
            padding=[dp(16), dp(12)],  # Full width padding
            spacing=dp(8)
        )
        
        self.scan_btn = ModernButton(
            text='Check In Guest',
            text_color=(0.15, 0.7, 0.3, 1),
            is_outline=True,
            outline_color=(0.15, 0.7, 0.3, 1),
            font_size=dp(14),
            bold=True,
            size_hint_y=None,
            height=dp(50)
        )
        self.scan_btn.bind(on_press=self.handle_scanning)
        
        scan_container.add_widget(self.scan_btn)
        root.add_widget(scan_container)
        
        # Register workflow state
        self.register_state = 'ready'  # ready, select_guest, ready_to_register
        self.selected_guest = None
        self.register_idle_timeout = None  # Auto-close timer
        
        # Search bar - increased spacing from Register button
        search_container = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(56),  # Increased height for more spacing
            padding=[dp(16), dp(12)],  # Increased vertical padding
            spacing=dp(8)
        )
        
        self.search_input = TextInput(
            hint_text='Search guests...',
            size_hint_y=None,
            height=dp(40),  # Taller search bar
            font_size=dp(14),
            multiline=False,
            background_color=(0, 0, 0, 0),  # Transparent background
            foreground_color=(1, 1, 1, 1),  # White text
            hint_text_color=(0.7, 0.7, 0.7, 1),  # Gray hint text
            cursor_color=(1, 1, 1, 1),  # White cursor
            padding=[dp(12), dp(12)],  # Better vertical centering
            background_normal='',
            background_active='',
            halign='center'  # Center text horizontally
        )
        self.search_input.bind(text=self.on_search_text)
        
        # Search input white outline
        with self.search_input.canvas.after:
            Color(1, 1, 1, 1)  # White outline
            self.search_outline = Line(
                rounded_rectangle=(self.search_input.x, self.search_input.y, 
                                   self.search_input.width, self.search_input.height, dp(6)),
                width=2
            )
        self.search_input.bind(pos=self._update_search_outline, size=self._update_search_outline)
        
        search_container.add_widget(self.search_input)
        root.add_widget(search_container)
        
        # Guest list section
        list_container = BoxLayout(orientation='vertical', spacing=0)
        
        # List header
        list_header = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(40),
            padding=[dp(16), dp(8)],
            spacing=dp(12)
        )
        
        # Header background - DARK MODE
        with list_header.canvas.before:
            Color(0.2, 0.2, 0.2, 1)  # Dark gray header
            self.list_header_bg = Rectangle(size=list_header.size, pos=list_header.pos)
        list_header.bind(size=self._update_list_header_bg, pos=self._update_list_header_bg)
        
        # Header labels - WHITE TEXT with increased font size
        id_header = Label(
            text='ID',
            size_hint_x=None,
            width=dp(40),
            font_size=dp(14),  # Increased by 2px
            color=(1, 1, 1, 1),  # White color
            bold=True,
            halign='left',
            valign='middle'
        )
        id_header.bind(size=id_header.setter('text_size'))
        
        name_header = Label(
            text='Guest Name',
            font_size=dp(14),  # Increased by 2px
            color=(1, 1, 1, 1),  # White color
            bold=True,
            halign='left',
            valign='middle'
        )
        name_header.bind(size=name_header.setter('text_size'))
        
        self.status_header = Label(
            text='1/10',  # Will be updated dynamically
            size_hint_x=None,
            width=dp(100),
            font_size=dp(14),  # Increased by 2px
            color=(1, 1, 1, 1),  # White color
            bold=True,
            halign='right',
            valign='middle'
        )
        self.status_header.bind(size=self.status_header.setter('text_size'))
        
        list_header.add_widget(id_header)
        list_header.add_widget(name_header)
        list_header.add_widget(self.status_header)
        
        # Guest list
        self.guest_list = GridLayout(
            cols=1,
            spacing=0,
            size_hint_y=None
        )
        self.guest_list.bind(minimum_height=self.guest_list.setter('height'))
        
        # Initialize Google Sheets and load real guest data
        self.init_google_sheets()
        
        # Convert guest data to the format expected by the UI
        guests = []
        if self.guest_data:
            # Sort by last name
            sorted_guests = sorted(self.guest_data, key=lambda g: g.lastname)
            for guest in sorted_guests:
                guests.append((guest.original_id, guest.full_name))
        else:
            # NO DEMO DATA FALLBACK - Show error message to staff
            self.logger.error("Failed to load guest data from Google Sheets - no guests available")
            guests = []
            # Show error in status bar
            self.update_status("❌ ERROR: Cannot load guest data. Check internet connection and try again.", "error")
        
        self.all_guests = guests  # Store all guests for filtering
        self.guest_rows = []
        self.visible_guest_rows = []  # Track currently visible/filtered rows
        self.guest_data_map = {}  # Map guest_id to GuestRecord for easy lookup
        
        # Build map for guest data
        if self.guest_data:
            for guest in self.guest_data:
                self.guest_data_map[guest.original_id] = guest
        
        for i, (guest_id, name) in enumerate(guests):
            row = GuestListItem(guest_id, name, is_even=(i % 2 == 0), app=self)
            
            # Check if guest has existing check-in for current station
            if guest_id in self.guest_data_map:
                guest_record = self.guest_data_map[guest_id]
                current_station_lower = self.current_station.lower()
                check_in_time = guest_record.check_ins.get(current_station_lower)
                if check_in_time:
                    # Guest already checked in at this station
                    # Normalize display: show lowercase 'x' as uppercase 'X'
                    display_text = "X" if check_in_time.strip().lower() == "x" else check_in_time
                    row.status_label.text = display_text
                    row.status_label.color = (0.2, 0.7, 0.2, 1)
                    # Update appearance for checked-in state
                    row.update_checkin_appearance()
            
            self.guest_rows.append(row)
            self.guest_list.add_widget(row)
        
        # Initialize visible rows to all rows (no filter applied initially)
        self.visible_guest_rows = self.guest_rows.copy()
        
        # Scrollable list
        scroll = ScrollView()
        scroll.add_widget(self.guest_list)
        
        list_container.add_widget(list_header)
        list_container.add_widget(scroll)
        root.add_widget(list_container)
        
        # Station buttons at bottom
        station_container = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=dp(70),
            padding=[dp(16), dp(8)],
            spacing=dp(8)
        )
        
        with station_container.canvas.before:
            Color(0.15, 0.15, 0.15, 1)
            self.station_bg = Rectangle(size=station_container.size, pos=station_container.pos)
        station_container.bind(size=self._update_station_bg, pos=self._update_station_bg)
        
        station_grid = GridLayout(
            cols=5,
            rows=1,
            spacing=dp(8),
            size_hint_y=None,
            height=dp(50)
        )
        
        stations = ['Reception', 'Lío', 'Juntos', 'Experimental', 'Unvrs']
        # Already initialized in beginning of build()
        self.station_buttons = {}
        
        for station in stations:
            is_current = (station == self.current_station)
            # Better text scaling
            if len(station) > 10:
                font_size = dp(10)
            elif len(station) > 8:
                font_size = dp(11)
            else:
                font_size = dp(13)
                
            if is_current:
                # Selected: orange fill, white text
                btn = ModernButton(
                    text=station,
                    font_size=font_size,
                    bg_color=(0.95, 0.4, 0.15, 1),
                    text_color=(1, 1, 1, 1),
                    is_outline=False,
                    bold=True
                )
            else:
                # Not selected: blue outline, blue text
                btn = ModernButton(
                    text=station,
                    font_size=font_size,
                    text_color=(0.2, 0.6, 1, 1),
                    is_outline=True,
                    outline_color=(0.2, 0.6, 1, 1),
                    bold=True
                )
            btn.bind(on_press=lambda x, s=station: self.station_selected(s))
            self.station_buttons[station] = btn
            station_grid.add_widget(btn)
        
        station_container.add_widget(station_grid)
        root.add_widget(station_container)
        
        # Initialize scanning state
        self.scanning_mode = None  # None, 'checkin', 'register', or 'tag_info'
        
        # Removed demo check-in - using real Google Sheets data
        
        # Update counter initially
        self.update_counter()
        
        # Button states for greying out
        self.button_states_normal = True
        
        return root
    
    def _update_header_bg(self, instance, value):
        self.header_bg.pos = instance.pos
        self.header_bg.size = instance.size
    
    def _update_list_header_bg(self, instance, value):
        self.list_header_bg.pos = instance.pos
        self.list_header_bg.size = instance.size
    
    def _update_station_bg(self, instance, value):
        self.station_bg.pos = instance.pos
        self.station_bg.size = instance.size
    
    def _update_search_outline(self, instance, value):
        self.search_outline.rounded_rectangle = (instance.x, instance.y, instance.width, instance.height, dp(6))
    
    def show_menu(self, instance):
        # Menu does nothing for now
        pass
    
    def station_selected(self, station):
        # Don't allow station changes during scanning
        if self.scanning_mode is not None:
            return
        
        # Update current station
        old_station = self.current_station
        self.current_station = station
        
        # Refresh guest data from Google Sheets to get latest check-ins
        self.refresh_from_sheets()
        
        # Update guest list to show check-ins for new station
        self.refresh_guest_checkins()
        
        # Show station switch message
        self.status.text = f'Switched to {station}'
        self.status.color = (1, 1, 1, 1)  # White text
        # Clear message after 3 seconds for better visibility
        Clock.schedule_once(lambda dt: setattr(self.status, 'text', ''), 3)
        
        # Update button colors
        if old_station in self.station_buttons:
            old_btn = self.station_buttons[old_station]
            # Change to outline style
            old_btn.is_outline = True
            old_btn.text_color = (0.2, 0.6, 1, 1)
            old_btn.outline_color = (0.2, 0.6, 1, 1)
            Clock.schedule_once(old_btn.set_text_color, 0)
            Clock.schedule_once(old_btn.update_graphics, 0)
        
        if station in self.station_buttons:
            new_btn = self.station_buttons[station]
            # Change to filled style
            new_btn.is_outline = False
            new_btn.bg_color = (0.95, 0.4, 0.15, 1)
            new_btn.text_color = (1, 1, 1, 1)
            Clock.schedule_once(new_btn.set_text_color, 0)
            Clock.schedule_once(new_btn.update_graphics, 0)
    
    def handle_register_workflow(self, instance):
        """Handle the register tag workflow states"""
        if self.register_state == 'ready':
            # Start guest selection and grey out other buttons
            self.register_state = 'select_guest'
            self.grey_out_buttons_except('register')
            self.register_btn.text = 'Select Guest'
            self.register_btn.text_color = (0.95, 0.4, 0.15, 1)  # Orange text
            self.register_btn.outline_color = (0.95, 0.4, 0.15, 1)  # Orange outline
            Clock.schedule_once(self.register_btn.set_text_color, 0)
            Clock.schedule_once(self.register_btn.update_graphics, 0)
            # Show Cancel button immediately
            self.update_check_in_button_for_register(True)
            self.status.text = 'Tap a guest to select for registration'
            
        elif self.register_state == 'ready_to_register':
            # Start NFC scanning - disable other scanning
            if self.scanning_mode in ['checkin', 'tag_info']:
                self.stop_scanning()
            
            self.scanning_mode = 'register'
            # Grey out other buttons during scanning
            self.grey_out_buttons_except('register')
            self.register_btn.text = 'Scanning... 10s'
            self.register_btn.text_color = (0.15, 0.7, 0.3, 1)  # Green text
            self.register_btn.outline_color = (0.15, 0.7, 0.3, 1)  # Green outline
            self.register_btn.is_outline = False
            self.register_btn.bg_color = (0.15, 0.7, 0.3, 1)  # Green fill
            self.register_btn.text_color = (1, 1, 1, 1)  # White text
            Clock.schedule_once(self.register_btn.set_text_color, 0)
            Clock.schedule_once(self.register_btn.update_graphics, 0)
            # Keep guest name in status during scanning (already set in select_guest_for_register)
            # Start actual NFC scanning with 10-second timeout
            self.start_nfc_register_scan()
        # Note: Removed close button functionality for select_guest and scanning states
    
    def reset_register_workflow(self):
        """Reset register workflow to initial state"""
        self.register_state = 'ready'
        self.selected_guest = None
        self.register_btn.text = 'Register Tag'
        self.register_btn.text_color = (0.95, 0.4, 0.15, 1)  # Orange
        self.register_btn.outline_color = (0.95, 0.4, 0.15, 1)  # Orange
        self.register_btn.is_outline = True  # Reset to outline style
        Clock.schedule_once(self.register_btn.set_text_color, 0)
        Clock.schedule_once(self.register_btn.update_graphics, 0)
        self.restore_all_buttons()
        # Clear any guest highlights
        self.clear_guest_highlights()
        # Restore Check In Guest button
        self.update_check_in_button_for_register(False)
        # Cancel auto-close timer if active
        if hasattr(self, 'register_idle_timeout') and self.register_idle_timeout:
            self.register_idle_timeout.cancel()
            self.register_idle_timeout = None
        # Cancel register scan timeout if active
        if hasattr(self, 'register_scan_timeout') and self.register_scan_timeout:
            self.register_scan_timeout.cancel()
            self.register_scan_timeout = None
        # Cancel register countdown timer if active
        if hasattr(self, 'register_countdown_timer') and self.register_countdown_timer:
            self.register_countdown_timer.cancel()
            self.register_countdown_timer = None
        # Clear status message
        self.clear_status_message()
    
    def start_nfc_register_scan(self):
        """Start NFC scanning for register tag with 10-second timeout"""
        # TODO: Start actual NFC scanning here
        
        # Schedule timeout after 10.5 seconds - this will show "No tag detected"
        self.register_scan_timeout = Clock.schedule_once(lambda dt: self.nfc_register_timeout(), 10.5)
        
        # Start countdown animation (start at 9 since we already show 10s)
        self.register_countdown_seconds = 9
        self.register_countdown_timer = Clock.schedule_interval(lambda dt: self.update_register_countdown(), 1)
    
    def update_register_countdown(self):
        """Update register button countdown display"""
        if self.scanning_mode == 'register' and self.register_countdown_seconds >= 0:
            self.register_btn.text = f'Scanning... {self.register_countdown_seconds}s'
            Clock.schedule_once(self.register_btn.set_text_color, 0)
            self.register_countdown_seconds -= 1
        else:
            # Stop countdown timer
            if hasattr(self, 'register_countdown_timer') and self.register_countdown_timer:
                self.register_countdown_timer.cancel()
                self.register_countdown_timer = None
            return False  # Stop the interval
    
    def nfc_register_timeout(self):
        """Handle NFC register scan timeout"""
        # Add locks to prevent timeout after cancel
        if (self.scanning_mode == 'register' and 
            self.register_state == 'ready_to_register' and
            hasattr(self, 'register_scan_timeout') and 
            self.register_scan_timeout is not None):
            
            self.scanning_mode = None
            self.register_scan_timeout = None  # Clear the timeout reference
            
            # Stop countdown timer
            if hasattr(self, 'register_countdown_timer') and self.register_countdown_timer:
                self.register_countdown_timer.cancel()
                self.register_countdown_timer = None
            
            # Restore register button to initial state (orange "Register Tag")
            self.register_btn.text = 'Register Tag'
            self.register_btn.text_color = (0.95, 0.4, 0.15, 1)  # Orange text
            self.register_btn.outline_color = (0.95, 0.4, 0.15, 1)  # Orange outline
            self.register_btn.is_outline = True  # Back to outline style
            self.register_btn.bg_color = (0, 0, 0, 0)  # Clear background
            Clock.schedule_once(self.register_btn.set_text_color, 0)
            Clock.schedule_once(self.register_btn.update_graphics, 0)
            
            # Restore Check In Guest button (remove Cancel state)
            self.update_check_in_button_for_register(False)
            
            # Restore other buttons
            self.restore_all_buttons()
            
            # Clear guest highlights and reset state immediately
            self.clear_guest_highlights()
            self.register_state = 'ready'
            self.selected_guest = None
            self.clear_status_message()
            
            # Show error message after button is restored
            self.show_error_message('No tag detected - try again', 3)
            # No need for reset_register_workflow since we already reset everything
        # If conditions not met, timeout was cancelled - do nothing
    
    def nfc_register_read_error(self):
        """Handle NFC register read error"""
        # Same cleanup as timeout but different message
        if (self.scanning_mode == 'register' and 
            self.register_state == 'ready_to_register' and
            hasattr(self, 'register_scan_timeout') and 
            self.register_scan_timeout is not None):
            
            # Cancel the timeout since we got a read error
            self.register_scan_timeout.cancel()
            self.register_scan_timeout = None
            self.scanning_mode = None
            
            # Stop countdown timer
            if hasattr(self, 'register_countdown_timer') and self.register_countdown_timer:
                self.register_countdown_timer.cancel()
                self.register_countdown_timer = None
            
            # Restore register button to initial state (orange "Register Tag")
            self.register_btn.text = 'Register Tag'
            self.register_btn.text_color = (0.95, 0.4, 0.15, 1)  # Orange text
            self.register_btn.outline_color = (0.95, 0.4, 0.15, 1)  # Orange outline
            self.register_btn.is_outline = True  # Back to outline style
            self.register_btn.bg_color = (0, 0, 0, 0)  # Clear background
            Clock.schedule_once(self.register_btn.set_text_color, 0)
            Clock.schedule_once(self.register_btn.update_graphics, 0)
            
            # Restore Check In Guest button (remove Cancel state)
            self.update_check_in_button_for_register(False)
            
            # Restore other buttons
            self.restore_all_buttons()
            
            # Clear guest highlights and reset state immediately
            self.clear_guest_highlights()
            self.register_state = 'ready'
            self.selected_guest = None
            self.clear_status_message()
            
            # Show read error message
            self.show_error_message('Tag failed to read - Try again', 3)
    
    def simulate_nfc_write(self):
        """Simulate successful NFC tag write - NOT USED IN PRODUCTION"""
        # This function is not called anymore - real NFC scanning will handle success
        pass
    
    def handle_scanning(self, instance):
        """Handle universal scanning button (Check In Guest / Cancel)"""
        # If in register workflow (any state), act as Cancel button
        if self.register_state in ['select_guest', 'ready_to_register']:
            # Cancel register workflow and its timeout with lock
            if hasattr(self, 'register_scan_timeout') and self.register_scan_timeout:
                self.register_scan_timeout.cancel()
                self.register_scan_timeout = None
            # Also cancel if currently scanning
            if self.scanning_mode == 'register':
                self.scanning_mode = None
            self.reset_register_workflow()
            return
            
        # If in tag info scanning mode, act as Cancel button
        if self.scanning_mode == 'tag_info':
            # Cancel tag info scanning and its timeout with lock
            if hasattr(self, 'tag_info_scan_timeout') and self.tag_info_scan_timeout:
                self.tag_info_scan_timeout.cancel()
                self.tag_info_scan_timeout = None
            self.stop_scanning()
            return
        
        # Normal Check In Guest functionality
        if self.scanning_mode is None and self.register_state == 'ready':
            # Start check-in scanning and grey out other buttons (only if not in register workflow)
            self.scanning_mode = 'checkin'
            self.grey_out_buttons_except('checkin')
            self.update_scan_button()
            self.status.text = ''
            # Start NFC scanning with timeout
            self.start_nfc_checkin_scan()
        elif self.scanning_mode == 'checkin':
            # Stop check-in scanning and cancel timeout with lock
            if hasattr(self, 'checkin_scan_timeout') and self.checkin_scan_timeout:
                self.checkin_scan_timeout.cancel()
                self.checkin_scan_timeout = None
            self.stop_scanning()
    
    def update_scan_button(self):
        """Update scan button appearance based on mode"""
        if self.scanning_mode == 'checkin':
            self.scan_btn.text = 'Scanning... 10s'
            self.scan_btn.text_color = (0.15, 0.7, 0.3, 1)  # Green text
            self.scan_btn.outline_color = (0.15, 0.7, 0.3, 1)  # Green outline
            self.scan_btn.is_outline = False
            self.scan_btn.bg_color = (0.15, 0.7, 0.3, 1)  # Green fill
            self.scan_btn.text_color = (1, 1, 1, 1)  # White text
        else:
            self.scan_btn.text = 'Check In Guest'
            self.scan_btn.text_color = (0.15, 0.7, 0.3, 1)  # Green text
            self.scan_btn.outline_color = (0.15, 0.7, 0.3, 1)  # Green outline
            self.scan_btn.is_outline = True
        
        Clock.schedule_once(self.scan_btn.set_text_color, 0)
        Clock.schedule_once(self.scan_btn.update_graphics, 0)
    
    def stop_scanning(self):
        """Stop all scanning modes and restore button states"""
        current_mode = self.scanning_mode
        self.scanning_mode = None
        
        # Cancel any active timeouts and countdown timers based on what was scanning
        if current_mode == 'checkin':
            if hasattr(self, 'checkin_scan_timeout') and self.checkin_scan_timeout:
                self.checkin_scan_timeout.cancel()
                self.checkin_scan_timeout = None
            if hasattr(self, 'checkin_countdown_timer') and self.checkin_countdown_timer:
                self.checkin_countdown_timer.cancel()
                self.checkin_countdown_timer = None
        elif current_mode == 'tag_info':
            if hasattr(self, 'tag_info_scan_timeout') and self.tag_info_scan_timeout:
                self.tag_info_scan_timeout.cancel()
                self.tag_info_scan_timeout = None
            if hasattr(self, 'tag_info_countdown_timer') and self.tag_info_countdown_timer:
                self.tag_info_countdown_timer.cancel()
                self.tag_info_countdown_timer = None
        elif current_mode == 'register':
            if hasattr(self, 'register_scan_timeout') and self.register_scan_timeout:
                self.register_scan_timeout.cancel()
                self.register_scan_timeout = None
            if hasattr(self, 'register_countdown_timer') and self.register_countdown_timer:
                self.register_countdown_timer.cancel()
                self.register_countdown_timer = None
        
        # Reset specific button based on what was scanning
        if current_mode == 'checkin':
            self.update_scan_button()
        elif current_mode == 'tag_info':
            self.tag_info_btn.text = 'Tag Info'
            self.tag_info_btn.text_color = (0.2, 0.6, 1, 1)
            self.tag_info_btn.outline_color = (0.2, 0.6, 1, 1)
            self.tag_info_btn.is_outline = True
            # Restore Check In Guest button from Cancel state
            self.update_check_in_button_for_tag_info(False)
            Clock.schedule_once(self.tag_info_btn.set_text_color, 0)
            Clock.schedule_once(self.tag_info_btn.update_graphics, 0)
        elif current_mode == 'register':
            # Don't reset register button here - let reset_register_workflow handle it
            pass
        
        self.restore_all_buttons()
        
        # Reset register workflow if it was scanning
        if self.register_state == 'ready_to_register' and self.register_btn.text == 'Scanning...':
            self.reset_register_workflow()
        else:
            self.status.text = ''
    
    
    def manual_checkin(self, instance):
        # This button is now just for demo purposes
        for row in self.guest_rows:
            if row.status_label.text == "-":
                row.check_in()
                self.update_summary()
                break
    
    def show_guest_menu(self, guest_row):
        """Show popup menu for guest actions"""
        # Create popup content
        content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
        
        # Create popup early so it can be referenced in callbacks
        popup = Popup(
            title='',  # No title
            content=content,
            size_hint=(0.8, None),
            height=dp(350),  # Will adjust later based on content
            background='',
            background_color=(0.1, 0.1, 0.1, 0.95),
            separator_color=(0, 0, 0, 0),  # Hide separator
            separator_height=0,  # No separator
            title_size=0  # No title space
        )
        
        # Guest info header
        guest_name_label = Label(
            text=guest_row.guest_name,
            font_size=dp(20),
            color=(1, 1, 1, 1),
            halign='center',
            bold=True,
            size_hint_y=None,
            height=dp(30)
        )
        content.add_widget(guest_name_label)
        
        # Get guest record for additional info
        guest_record = self.guest_data_map.get(guest_row.guest_id)
        if guest_record:
            # Show last check-in info across all stations
            last_checkin_info = "No previous check-ins"
            for station, time in guest_record.check_ins.items():
                if time:
                    last_checkin_info = f"Last seen: {station.title()} at {time}"
                    break
            
            checkin_info_label = Label(
                text=last_checkin_info,
                font_size=dp(14),
                color=(0.7, 0.7, 0.7, 1),
                halign='center',
                size_hint_y=None,
                height=dp(20)
            )
            content.add_widget(checkin_info_label)
            
            # Add spacing
            content.add_widget(Widget(size_hint_y=None, height=dp(10)))
            
            # Call button if phone number exists
            if guest_record.phone_number:
                call_btn = ModernButton(
                    text='Call',
                    text_color=(0.2, 0.6, 1, 1),  # Blue
                    is_outline=True,
                    outline_color=(0.2, 0.6, 1, 1),
                    size_hint_y=None,
                    height=dp(50),
                    font_size=dp(16),
                    bold=True
                )
                call_btn.bind(on_press=lambda x: self.call_guest(guest_record.phone_number, popup))
                content.add_widget(call_btn)
        
        # Check-in button - only show if guest is NOT checked in and NOT absent
        status_text = guest_row.status_label.text.strip().lower()
        if status_text == "-" or status_text == "":
            checkin_btn = ModernButton(
                text='Check In',
                text_color=(0.15, 0.7, 0.3, 1),  # Green
                is_outline=True,
                outline_color=(0.15, 0.7, 0.3, 1),
                size_hint_y=None,
                height=dp(50),
                font_size=dp(16),
                bold=True
            )
            checkin_btn.bind(on_press=lambda x: self.checkin_guest(guest_row, popup))
            content.add_widget(checkin_btn)
            
            # Mark Absent button - only show if guest is NOT checked in and NOT already absent
            absent_btn = ModernButton(
                text='Mark Absent',
                text_color=(0.8, 0.2, 0.2, 1),  # Red text
                is_outline=True,
                outline_color=(0.8, 0.2, 0.2, 1),  # Red outline
                size_hint_y=None,
                height=dp(50),
                font_size=dp(16),
                bold=True
            )
            absent_btn.bind(on_press=lambda x: self.mark_guest_absent(guest_row, popup))
            content.add_widget(absent_btn)
        # If already checked in or absent, don't show check-in/absent buttons
        
        # Cancel button
        cancel_btn = ModernButton(
            text='Cancel',
            text_color=(0.5, 0.5, 0.5, 1),  # Grey
            is_outline=True,
            outline_color=(0.5, 0.5, 0.5, 1),
            size_hint_y=None,
            height=dp(40),
            font_size=dp(14)
        )
        
        cancel_btn.bind(on_press=popup.dismiss)
        content.add_widget(cancel_btn)
        
        # Adjust popup height based on content (includes Mark Absent button)
        has_phone = guest_record and guest_record.phone_number
        has_action_buttons = guest_row.status_label.text == "-"  # Check-in + Mark Absent buttons
        if has_phone and has_action_buttons:
            popup.height = dp(390)  # Phone + check-in + absent buttons
        elif has_phone:
            popup.height = dp(270)  # Phone only (already checked in/absent)
        elif has_action_buttons:
            popup.height = dp(320)  # Check-in + absent buttons only
        else:
            popup.height = dp(200)  # Just guest info (already checked in/absent, no phone)
        
        popup.open()
    
    def checkin_guest(self, guest_row, popup):
        """Check in a specific guest and close popup"""
        success = guest_row.check_in()
        if success:
            self.update_summary()
        popup.dismiss()
        # Status text handled by check_in method
    
    def mark_guest_absent(self, guest_row, popup):
        """Mark a specific guest as absent and close popup"""
        guest_row.mark_absent()
        self.update_summary()
        popup.dismiss()
    
    def call_guest(self, phone_number, popup):
        """Call guest using native phone functionality"""
        popup.dismiss()
        
        # Clean phone number (remove spaces, dashes, etc)
        clean_number = ''.join(filter(str.isdigit, phone_number))
        
        if PLYER_AVAILABLE:
            # Use plyer for Android
            try:
                call.makecall(tel=clean_number)
                self.status.text = f'Calling {phone_number}'
                Clock.schedule_once(lambda dt: self.clear_status_message(), 3)
            except Exception as e:
                self.logger.error(f"Error making call: {e}")
                self.status.text = 'Unable to make call'
                Clock.schedule_once(lambda dt: self.clear_status_message(), 3)
        else:
            # Fallback for desktop testing
            tel_url = f'tel:{clean_number}'
            webbrowser.open(tel_url)
            self.status.text = f'Opening phone app for {phone_number}'
            Clock.schedule_once(lambda dt: self.clear_status_message(), 3)
    
    def show_stats(self, instance):
        # Removed - no longer needed
        pass
    
    
    def refresh_from_sheets(self):
        """Refresh guest data from Google Sheets to get latest check-ins"""
        if self.sheets_service:
            try:
                # Fetch fresh data from Google Sheets
                fresh_guest_data = self.sheets_service.get_all_guests()
                if fresh_guest_data:
                    self.guest_data = fresh_guest_data
                    # Rebuild the guest data map
                    self.guest_data_map = {}
                    for guest in self.guest_data:
                        self.guest_data_map[guest.original_id] = guest
                    self.logger.info(f"Refreshed {len(fresh_guest_data)} guests from Google Sheets")
                else:
                    self.logger.warning("Failed to refresh guest data from Google Sheets")
            except Exception as e:
                self.logger.error(f"Error refreshing from Google Sheets: {e}")
    
    def refresh_guest_checkins(self):
        """Refresh guest check-in status for current station"""
        if not hasattr(self, 'guest_rows'):
            return
            
        current_station_lower = self.current_station.lower()
        
        for row in self.guest_rows:
            # Reset status first
            row.status_label.text = "-"
            row.status_label.color = (0.7, 0.7, 0.7, 1)
            
            # Check if guest has check-in for current station
            if row.guest_id in self.guest_data_map:
                guest_record = self.guest_data_map[row.guest_id]
                check_in_time = guest_record.check_ins.get(current_station_lower)
                if check_in_time:
                    # Guest already checked in at this station
                    # Normalize display: show lowercase 'x' as uppercase 'X'
                    display_text = "X" if check_in_time.strip().lower() == "x" else check_in_time
                    row.status_label.text = display_text
                    row.status_label.color = (0.2, 0.7, 0.2, 1)
            
            # Update row appearance based on check-in status
            row.update_checkin_appearance()
        
        # Update visible rows if search is active
        if hasattr(self, 'search_input') and self.search_input.text.strip():
            # Re-run search to update visible rows
            self.on_search_text(self.search_input, self.search_input.text)
        else:
            # No search active, all rows are visible
            self.visible_guest_rows = self.guest_rows.copy()
        
        # Update summary after refresh
        self.update_summary()
    
    def update_summary(self):
        # Update header stats - count guests with timestamps (not "-")
        checked = sum(1 for row in self.guest_rows if row.status_label.text != "-")
        # Don't show persistent status message
        self.update_counter()
    
    def update_counter(self):
        # Update the header counter based on visible (filtered) rows
        if hasattr(self, 'visible_guest_rows') and self.visible_guest_rows:
            # Use filtered results if search is active
            checked = sum(1 for row in self.visible_guest_rows 
                         if row.status_label.text.strip().lower() not in ["-", "", "x"])
            total = len(self.visible_guest_rows)
        else:
            # Use all guests if no search filter
            checked = sum(1 for row in self.guest_rows 
                         if row.status_label.text.strip().lower() not in ["-", "", "x"])
            total = len(self.guest_rows)
        
        self.status_header.text = f'{checked}/{total}'
    
    def clear_guest_highlights(self):
        """Clear highlighting from all guest rows"""
        for i, row in enumerate(self.guest_rows):
            row.canvas.before.clear()
            with row.canvas.before:
                if i % 2 == 0:
                    Color(0.15, 0.15, 0.15, 1)
                else:
                    Color(0.1, 0.1, 0.1, 1)
                row.bg_rect = Rectangle(size=row.size, pos=row.pos)
    
    def select_guest_for_register(self, guest_row):
        """Select a guest for tag registration - allows changing selection"""
        # Don't allow selection during scanning
        if self.scanning_mode == 'register':
            return
            
        # If already in ready_to_register state, allow changing selection
        if self.register_state == 'ready_to_register':
            # Just update the selection, stay in same state
            self.selected_guest = guest_row
        else:
            # First selection - move to ready_to_register state
            self.selected_guest = guest_row
            self.register_state = 'ready_to_register'
        
        # Update button text and color - GREEN for ready to scan
        self.register_btn.text = 'Register'
        self.register_btn.text_color = (0.15, 0.7, 0.3, 1)  # Green text for ready to scan
        self.register_btn.outline_color = (0.15, 0.7, 0.3, 1)  # Green outline
        Clock.schedule_once(self.register_btn.set_text_color, 0)
        Clock.schedule_once(self.register_btn.update_graphics, 0)
        
        # Highlight selected guest in orange
        self.clear_guest_highlights()
        # Force canvas update for the selected row
        guest_row.canvas.before.clear()
        with guest_row.canvas.before:
            Color(0.95, 0.4, 0.15, 1)  # Orange highlight
            guest_row.bg_rect = Rectangle(size=guest_row.size, pos=guest_row.pos)
        # Force canvas to redraw
        guest_row.canvas.ask_update()
        
        # Show selected guest name in green bold text in status bar
        guest_name = guest_row.guest_name
        self.status.text = f"[b]{guest_name}[/b]"
        self.status.color = (0.15, 0.7, 0.3, 1)  # Green color
        self.status.markup = True  # Enable markup for bold text
        
        # Note: Cancel button is already shown from select_guest state
        
        # Start 15-second auto-close timer
        if hasattr(self, 'register_idle_timeout') and self.register_idle_timeout:
            self.register_idle_timeout.cancel()
        self.register_idle_timeout = Clock.schedule_once(lambda dt: self.auto_close_register(), 15)
    
    def show_error_message(self, message, duration=3):
        """Show an error message in red and clear it after duration"""
        self.status.text = message
        self.status.color = (0.8, 0.2, 0.2, 1)  # Red color
        # Clear message and restore white color after duration
        Clock.schedule_once(lambda dt: self.clear_status_message(), duration)
    
    def show_warning_message(self, message, duration=3):
        """Show a warning message in orange and clear it after duration"""
        self.status.text = message
        self.status.color = (0.95, 0.4, 0.15, 1)  # Orange color
        # Clear message and restore white color after duration
        Clock.schedule_once(lambda dt: self.clear_status_message(), duration)
    
    def clear_status_message(self):
        """Clear status message and restore normal white color"""
        self.status.text = ''
        self.status.color = (1, 1, 1, 1)  # White color
        self.status.markup = False  # Disable markup
    
    def update_check_in_button_for_register(self, show_cancel):
        """Update Check In Guest button to show Cancel when guest is selected"""
        if show_cancel:
            # Change to red Cancel button
            self.scan_btn.text = 'Cancel'
            self.scan_btn.text_color = (0.8, 0.2, 0.2, 1)  # Red text
            self.scan_btn.outline_color = (0.8, 0.2, 0.2, 1)  # Red outline
            self.scan_btn.is_outline = True  # Outline only, no fill
        else:
            # Restore to normal Check In Guest button
            self.scan_btn.text = 'Check In Guest'
            self.scan_btn.text_color = (0.15, 0.7, 0.3, 1)  # Green text
            self.scan_btn.outline_color = (0.15, 0.7, 0.3, 1)  # Green outline
            self.scan_btn.is_outline = True
        
        Clock.schedule_once(self.scan_btn.set_text_color, 0)
        Clock.schedule_once(self.scan_btn.update_graphics, 0)
    
    def update_check_in_button_for_tag_info(self, show_cancel):
        """Update Check In Guest button to show Cancel when tag info scanning"""
        if show_cancel:
            # Change to red Cancel button
            self.scan_btn.text = 'Cancel'
            self.scan_btn.text_color = (0.8, 0.2, 0.2, 1)  # Red text
            self.scan_btn.outline_color = (0.8, 0.2, 0.2, 1)  # Red outline
            self.scan_btn.is_outline = True  # Outline only, no fill
        else:
            # Restore to normal Check In Guest button
            self.scan_btn.text = 'Check In Guest'
            self.scan_btn.text_color = (0.15, 0.7, 0.3, 1)  # Green text
            self.scan_btn.outline_color = (0.15, 0.7, 0.3, 1)  # Green outline
            self.scan_btn.is_outline = True
        
        Clock.schedule_once(self.scan_btn.set_text_color, 0)
        Clock.schedule_once(self.scan_btn.update_graphics, 0)
    
    def auto_close_register(self):
        """Auto-close register workflow after 15 seconds of inactivity"""
        if self.register_state == 'ready_to_register':
            self.reset_register_workflow()
    
    def handle_tag_info(self, instance):
        """Handle tag info button press - start scanning for tag info"""
        if self.scanning_mode is None:
            # Start tag info scanning and grey out other buttons
            self.scanning_mode = 'tag_info'
            self.grey_out_buttons_except('tag_info')
            self.tag_info_btn.text = 'Scanning... 10s'
            self.tag_info_btn.text_color = (0.15, 0.7, 0.3, 1)  # Green text
            self.tag_info_btn.outline_color = (0.15, 0.7, 0.3, 1)  # Green outline
            self.tag_info_btn.is_outline = False
            self.tag_info_btn.bg_color = (0.15, 0.7, 0.3, 1)  # Green fill
            self.tag_info_btn.text_color = (1, 1, 1, 1)  # White text
            Clock.schedule_once(self.tag_info_btn.set_text_color, 0)
            Clock.schedule_once(self.tag_info_btn.update_graphics, 0)
            # Make Check In Guest button become Cancel during tag info scanning
            self.update_check_in_button_for_tag_info(True)
            self.status.text = ''
            # Start actual NFC scanning with timeout
            self.start_nfc_tag_info_scan()
        # Note: Removed elif - tag info button is disabled as close button when scanning
    
    def start_nfc_tag_info_scan(self):
        """Start NFC scanning for tag info with 10-second timeout"""
        # TODO: Start actual NFC scanning here
        
        # Schedule timeout after 10.5 seconds - this will show "No tag detected"
        self.tag_info_scan_timeout = Clock.schedule_once(lambda dt: self.nfc_tag_info_timeout(), 10.5)
        
        # Start countdown animation (start at 9 since we already show 10s)
        self.tag_info_countdown_seconds = 9
        self.tag_info_countdown_timer = Clock.schedule_interval(lambda dt: self.update_tag_info_countdown(), 1)
    
    def update_tag_info_countdown(self):
        """Update tag info button countdown display"""
        if self.scanning_mode == 'tag_info' and self.tag_info_countdown_seconds >= 0:
            self.tag_info_btn.text = f'Scanning... {self.tag_info_countdown_seconds}s'
            Clock.schedule_once(self.tag_info_btn.set_text_color, 0)
            self.tag_info_countdown_seconds -= 1
        else:
            # Stop countdown timer
            if hasattr(self, 'tag_info_countdown_timer') and self.tag_info_countdown_timer:
                self.tag_info_countdown_timer.cancel()
                self.tag_info_countdown_timer = None
            return False  # Stop the interval
    
    def nfc_tag_info_timeout(self):
        """Handle NFC tag info scan timeout"""
        # Add locks to prevent timeout after cancel
        if (self.scanning_mode == 'tag_info' and
            hasattr(self, 'tag_info_scan_timeout') and 
            self.tag_info_scan_timeout is not None):
            
            self.scanning_mode = None
            self.tag_info_scan_timeout = None  # Clear the timeout reference
            
            # Stop countdown timer
            if hasattr(self, 'tag_info_countdown_timer') and self.tag_info_countdown_timer:
                self.tag_info_countdown_timer.cancel()
                self.tag_info_countdown_timer = None
            self.restore_all_buttons()
            self.tag_info_btn.text = 'Tag Info'
            self.tag_info_btn.text_color = (0.2, 0.6, 1, 1)
            self.tag_info_btn.outline_color = (0.2, 0.6, 1, 1)
            self.tag_info_btn.is_outline = True
            # Restore Check In Guest button from Cancel state
            self.update_check_in_button_for_tag_info(False)
            Clock.schedule_once(self.tag_info_btn.set_text_color, 0)
            Clock.schedule_once(self.tag_info_btn.update_graphics, 0)
            self.show_error_message('No tag detected - try again', 3)
        # If conditions not met, timeout was cancelled - do nothing
    
    def simulate_tag_info_read(self):
        """Simulate reading tag info from NFC - NOT USED IN PRODUCTION"""
        # This function is not called anymore - real NFC scanning will handle success
        pass
    
    def show_tag_info_popup(self, guest_name, location, time):
        """Show tag information popup"""
        # Create popup content
        content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(20))
        
        # Tag info
        info_label = Label(
            text=f'Guest: {guest_name}\nLast Check-in: {location}\nTime: {time}',
            font_size=dp(16),
            color=(1, 1, 1, 1),
            halign='center'
        )
        info_label.bind(size=info_label.setter('text_size'))
        content.add_widget(info_label)
        
        # Close button
        close_btn = ModernButton(
            text='Close',
            bg_color=(0.3, 0.3, 0.3, 1),
            text_color=(1, 1, 1, 1),
            size_hint_y=None,
            height=dp(40),
            font_size=dp(14)
        )
        
        # Create popup
        popup = Popup(
            title='Guest Information',
            content=content,
            size_hint=(0.8, None),
            height=dp(220),
            background='',
            background_color=(0.1, 0.1, 0.1, 0.95),
            separator_color=(0.3, 0.3, 0.3, 1),
            title_color=(1, 1, 1, 1),
            title_size=dp(16)
        )
        
        close_btn.bind(on_press=popup.dismiss)
        content.add_widget(close_btn)
        
        popup.open()
        # Clear status after popup
        Clock.schedule_once(lambda dt: setattr(self.status, 'text', ''), 3)
    
    def start_nfc_checkin_scan(self):
        """Start NFC scanning for check-in with 10-second timeout"""
        # TODO: Start actual NFC scanning here
        # Schedule timeout after 10.5 seconds
        self.checkin_scan_timeout = Clock.schedule_once(lambda dt: self.nfc_checkin_timeout(), 10.5)
        
        # Start countdown animation (start at 9 since we already show 10s)
        self.checkin_countdown_seconds = 9
        self.checkin_countdown_timer = Clock.schedule_interval(lambda dt: self.update_checkin_countdown(), 1)
    
    def update_checkin_countdown(self):
        """Update check-in button countdown display"""
        if self.scanning_mode == 'checkin' and self.checkin_countdown_seconds >= 0:
            self.scan_btn.text = f'Scanning... {self.checkin_countdown_seconds}s'
            Clock.schedule_once(self.scan_btn.set_text_color, 0)
            self.checkin_countdown_seconds -= 1
        else:
            # Stop countdown timer
            if hasattr(self, 'checkin_countdown_timer') and self.checkin_countdown_timer:
                self.checkin_countdown_timer.cancel()
                self.checkin_countdown_timer = None
            return False  # Stop the interval
    
    def nfc_checkin_timeout(self):
        """Handle NFC check-in scan timeout"""
        # Add locks to prevent timeout after cancel
        if (self.scanning_mode == 'checkin' and
            hasattr(self, 'checkin_scan_timeout') and 
            self.checkin_scan_timeout is not None):
            
            self.scanning_mode = None
            self.checkin_scan_timeout = None  # Clear the timeout reference
            
            # Stop countdown timer
            if hasattr(self, 'checkin_countdown_timer') and self.checkin_countdown_timer:
                self.checkin_countdown_timer.cancel()
                self.checkin_countdown_timer = None
                
            self.restore_all_buttons()
            self.update_scan_button()
            self.show_error_message('No tag detected - try again', 3)
        # If conditions not met, timeout was cancelled - do nothing
    
    def grey_out_buttons_except(self, active_button):
        """Grey out all action buttons except the active one and disable search"""
        buttons = {
            'tag_info': self.tag_info_btn,
            'register': self.register_btn,
            'checkin': self.scan_btn
        }
        
        for btn_name, btn in buttons.items():
            if btn_name != active_button:
                # Don't grey out Cancel button during register workflow or tag info scanning
                if btn_name == 'checkin' and (self.register_state in ['select_guest', 'ready_to_register'] or self.scanning_mode == 'tag_info'):
                    continue  # Keep Cancel button active
                btn.opacity = 0.3  # Grey out
                btn.disabled = True
        
        # Disable search input during scanning
        self.search_input.disabled = True
        self.search_input.opacity = 0.5
    
    def restore_all_buttons(self):
        """Restore all buttons to normal state"""
        buttons = [self.tag_info_btn, self.register_btn, self.scan_btn]
        
        for btn in buttons:
            btn.opacity = 1.0
            btn.disabled = False
        
        # Re-enable search input
        self.search_input.disabled = False
        self.search_input.opacity = 1.0
        
        # Clear status
        self.status.text = ''
    
    def on_search_text(self, instance, text):
        # Filter guest list based on search text
        self.guest_list.clear_widgets()
        
        search_text = text.lower()
        visible_rows = []
        
        if search_text.strip() == "":
            # No search - show all guests
            visible_rows = self.guest_rows.copy()
        else:
            # Filter based on search text
            for row in self.guest_rows:
                if search_text in row.guest_name.lower() or search_text in str(row.guest_id):
                    visible_rows.append(row)
        
        # Store visible rows for counter calculation
        self.visible_guest_rows = visible_rows
        
        # Re-add visible rows with updated colors (considering check-in status)
        for i, row in enumerate(visible_rows):
            # Update row appearance based on check-in status and position
            status_text = row.status_label.text.strip().lower()
            if status_text == "x":
                # Absent - use red background
                row.update_absent_appearance()
            elif status_text != "-" and status_text != "":
                # Checked in - use green background
                row.update_checkin_appearance()
            else:
                # Not checked in - use alternating colors
                row.canvas.before.clear()
                with row.canvas.before:
                    if i % 2 == 0:
                        Color(0.15, 0.15, 0.15, 1)
                    else:
                        Color(0.1, 0.1, 0.1, 1)
                    row.bg_rect = Rectangle(size=row.size, pos=row.pos)
                # Restore white text for unchecked rows
                row.id_label.color = (1, 1, 1, 1)
                row.name_label.color = (1, 1, 1, 1)
            self.guest_list.add_widget(row)
        
        # Update counter to reflect filtered results
        self.update_counter()
        
        # Don't update status while searching if workflows are idle
        if self.register_state == 'ready' and self.scanning_mode is None:
            self.status.text = ''

if __name__ == '__main__':
    TPNFCApp().run()