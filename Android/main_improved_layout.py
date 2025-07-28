#!/usr/bin/env python3
"""
TP_NFC Android - Improved layout with better proportions
"""

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle

class GuestRow(BoxLayout):
    """A single guest row in the list"""
    def __init__(self, name, table, status="Not Checked In", **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = 45
        self.padding = 8
        self.spacing = 10
        
        # Guest name
        name_label = Label(
            text=name,
            size_hint_x=0.4,
            halign='left',
            valign='middle',
            font_size='14sp'
        )
        name_label.bind(size=name_label.setter('text_size'))
        
        # Table
        table_label = Label(
            text=f"Table {table}",
            size_hint_x=0.2,
            halign='center',
            valign='middle',
            font_size='14sp'
        )
        
        # Status
        self.status_label = Label(
            text=status,
            size_hint_x=0.4,
            halign='center',
            valign='middle',
            font_size='14sp',
            color=(0.8, 0.2, 0.2, 1) if status == "Not Checked In" else (0.2, 0.8, 0.2, 1)
        )
        
        self.add_widget(name_label)
        self.add_widget(table_label)
        self.add_widget(self.status_label)
        
        # Add background
        with self.canvas.before:
            Color(0.95, 0.95, 0.95, 1)
            self.rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self._update_rect, pos=self._update_rect)
    
    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size
    
    def check_in(self):
        """Mark guest as checked in"""
        self.status_label.text = "Checked In ✓"
        self.status_label.color = (0.2, 0.8, 0.2, 1)

class TPNFCApp(App):
    def build(self):
        # Main layout
        main_layout = BoxLayout(orientation='vertical', padding=15, spacing=15)
        
        # Top section (70% of screen) - Title, Status, Buttons
        top_section = BoxLayout(orientation='vertical', size_hint_y=0.7, spacing=15)
        
        # Title
        title = Label(
            text='TP_NFC Guest Tracker',
            font_size='28sp',
            size_hint_y=None,
            height=60,
            bold=True
        )
        
        # Status bar
        self.status = Label(
            text='Ready to scan NFC tags',
            font_size='18sp',
            size_hint_y=None,
            height=50,
            color=(0.3, 0.3, 0.8, 1)
        )
        
        # Button grid - 3 columns, bigger buttons
        button_grid = GridLayout(
            cols=3,
            rows=2,
            size_hint_y=None,
            height=200,
            spacing=15,
            padding=10
        )
        
        # Row 1 - Main action buttons
        self.scan_btn = Button(
            text='Start NFC\nScan',
            font_size='16sp',
            background_color=(0.2, 0.6, 1, 1),
            halign='center'
        )
        self.scan_btn.bind(on_press=self.toggle_scan)
        
        checkin_btn = Button(
            text='Manual\nCheck-in',
            font_size='16sp',
            background_color=(0.2, 0.8, 0.2, 1),
            halign='center'
        )
        checkin_btn.bind(on_press=self.manual_checkin)
        
        sync_btn = Button(
            text='Sync\nData',
            font_size='16sp',
            background_color=(0.8, 0.4, 0.2, 1),
            halign='center'
        )
        sync_btn.bind(on_press=self.sync_data)
        
        # Row 2 - Additional buttons
        stats_btn = Button(
            text='View\nStats',
            font_size='16sp',
            background_color=(0.6, 0.2, 0.8, 1),
            halign='center'
        )
        stats_btn.bind(on_press=self.show_stats)
        
        settings_btn = Button(
            text='Settings',
            font_size='16sp',
            background_color=(0.5, 0.5, 0.5, 1),
            halign='center'
        )
        settings_btn.bind(on_press=self.show_settings)
        
        help_btn = Button(
            text='Help',
            font_size='16sp',
            background_color=(0.8, 0.6, 0.2, 1),
            halign='center'
        )
        help_btn.bind(on_press=self.show_help)
        
        # Add buttons to grid
        button_grid.add_widget(self.scan_btn)
        button_grid.add_widget(checkin_btn)
        button_grid.add_widget(sync_btn)
        button_grid.add_widget(stats_btn)
        button_grid.add_widget(settings_btn)
        button_grid.add_widget(help_btn)
        
        # Add to top section
        top_section.add_widget(title)
        top_section.add_widget(self.status)
        top_section.add_widget(button_grid)
        
        # Bottom section (30% of screen) - Guest List
        bottom_section = BoxLayout(orientation='vertical', size_hint_y=0.3, spacing=5)
        
        # Guest list header
        header_layout = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=35,
            padding=8
        )
        header_layout.add_widget(Label(text='Guest Name', size_hint_x=0.4, bold=True, font_size='14sp'))
        header_layout.add_widget(Label(text='Table', size_hint_x=0.2, bold=True, font_size='14sp'))
        header_layout.add_widget(Label(text='Status', size_hint_x=0.4, bold=True, font_size='14sp'))
        
        # Guest list container
        self.guest_list = GridLayout(
            cols=1,
            spacing=2,
            size_hint_y=None
        )
        self.guest_list.bind(minimum_height=self.guest_list.setter('height'))
        
        # Scrollable guest list
        scroll_view = ScrollView()
        scroll_view.add_widget(self.guest_list)
        
        # Add sample guests
        self.guests = [
            ("Ana García", "1"),
            ("Carlos López", "1"),
            ("Maria Rodriguez", "2"),
            ("Juan Martínez", "2"),
            ("Sofia Hernández", "3"),
            ("Diego Pérez", "3"),
            ("Lucia Sánchez", "4"),
            ("Miguel Torres", "4"),
            ("Isabella Flores", "5"),
            ("Alejandro Ruiz", "5")
        ]
        
        self.guest_rows = []
        for name, table in self.guests:
            row = GuestRow(name, table)
            self.guest_rows.append(row)
            self.guest_list.add_widget(row)
        
        # Summary label
        self.summary = Label(
            text=f'Total Guests: {len(self.guests)} | Checked In: 0',
            size_hint_y=None,
            height=35,
            font_size='16sp',
            bold=True
        )
        
        # Add to bottom section
        bottom_section.add_widget(header_layout)
        bottom_section.add_widget(scroll_view)
        bottom_section.add_widget(self.summary)
        
        # Add sections to main layout
        main_layout.add_widget(top_section)
        main_layout.add_widget(bottom_section)
        
        # Simulate checking in first guest after 2 seconds
        Clock.schedule_once(lambda dt: self.demo_checkin(), 2)
        
        return main_layout
    
    def toggle_scan(self, instance):
        """Toggle NFC scanning"""
        if 'Start' in instance.text:
            instance.text = 'Stop NFC\nScan'
            instance.background_color = (0.8, 0.2, 0.2, 1)
            self.status.text = 'Scanning for NFC tags...'
            self.status.color = (0.2, 0.8, 0.2, 1)
        else:
            instance.text = 'Start NFC\nScan'
            instance.background_color = (0.2, 0.6, 1, 1)
            self.status.text = 'NFC scanning stopped'
            self.status.color = (0.3, 0.3, 0.8, 1)
    
    def manual_checkin(self, instance):
        """Simulate manual check-in"""
        for row in self.guest_rows:
            if row.status_label.text == "Not Checked In":
                row.check_in()
                self.update_summary()
                # Get guest name from the row (it's the first child's text)
                guest_name = row.children[2].text  # children are added in reverse order
                self.status.text = f'Manually checked in: {guest_name}'
                self.status.color = (0.2, 0.8, 0.2, 1)
                break
    
    def sync_data(self, instance):
        """Simulate data sync"""
        self.status.text = 'Syncing with Google Sheets...'
        self.status.color = (0.8, 0.6, 0.2, 1)
        Clock.schedule_once(lambda dt: self.sync_complete(), 2)
    
    def sync_complete(self):
        """Complete sync simulation"""
        self.status.text = 'Sync completed successfully!'
        self.status.color = (0.2, 0.8, 0.2, 1)
    
    def show_stats(self, instance):
        """Show statistics"""
        checked_in = sum(1 for row in self.guest_rows if row.status_label.text == "Checked In ✓")
        self.status.text = f'Stats: {checked_in}/{len(self.guests)} guests checked in'
        self.status.color = (0.6, 0.2, 0.8, 1)
    
    def show_settings(self, instance):
        """Show settings"""
        self.status.text = 'Settings menu (coming soon)'
        self.status.color = (0.5, 0.5, 0.5, 1)
    
    def show_help(self, instance):
        """Show help"""
        self.status.text = 'Help: Tap buttons to interact with the app'
        self.status.color = (0.8, 0.6, 0.2, 1)
    
    def demo_checkin(self):
        """Demo check-in for first guest"""
        if self.guest_rows:
            self.guest_rows[0].check_in()
            self.update_summary()
            self.status.text = 'Demo: Checked in Ana García via NFC'
            self.status.color = (0.2, 0.8, 0.2, 1)
    
    def update_summary(self):
        """Update the summary count"""
        checked_in = sum(1 for row in self.guest_rows if row.status_label.text == "Checked In ✓")
        self.summary.text = f'Total Guests: {len(self.guests)} | Checked In: {checked_in}'

if __name__ == '__main__':
    TPNFCApp().run()