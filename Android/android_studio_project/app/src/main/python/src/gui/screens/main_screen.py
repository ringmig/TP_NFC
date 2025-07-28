#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main screen for TP_NFC Android app
"""

from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.button import MDRaisedButton, MDIconButton
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.uix.textfield import MDTextField
from kivymd.uix.selectioncontrol import MDSwitch
from kivymd.uix.navigationdrawer import MDNavigationDrawer
from kivymd.uix.list import OneLineListItem
from kivy.metrics import dp

class MainScreen(MDScreen):
    """Main screen with station selection and NFC functionality"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_station = "Reception"
        self.is_registration_mode = True
        self.build_ui()
        
    def build_ui(self):
        """Build the main UI layout"""
        # Main layout
        main_layout = MDBoxLayout(
            orientation='vertical',
            spacing=dp(10),
            adaptive_height=True
        )
        
        # Top bar
        toolbar = MDTopAppBar(
            title="TP NFC - Reception",
            elevation=2,
            left_action_items=[["menu", lambda x: self.open_station_menu()]],
            right_action_items=[["cog", lambda x: self.open_settings()]]
        )
        
        # Content area
        content_layout = MDBoxLayout(
            orientation='vertical',
            spacing=dp(20),
            adaptive_height=True,
            padding=[dp(20), dp(20), dp(20), dp(20)]
        )
        
        # Station info card
        station_card = self.create_station_card()
        content_layout.add_widget(station_card)
        
        # NFC interaction card
        nfc_card = self.create_nfc_card()
        content_layout.add_widget(nfc_card)
        
        # Status card
        status_card = self.create_status_card()
        content_layout.add_widget(status_card)
        
        # Add to main layout
        main_layout.add_widget(toolbar)
        main_layout.add_widget(content_layout)
        
        self.add_widget(main_layout)
    
    def create_station_card(self):
        """Create station information card"""
        card = MDCard(
            orientation='vertical',
            padding=dp(20),
            spacing=dp(10),
            elevation=2,
            size_hint_y=None,
            height=dp(120)
        )
        
        # Station title
        station_label = MDLabel(
            text=f"Current Station: {self.current_station}",
            theme_text_color="Primary",
            font_style="H6",
            size_hint_y=None,
            height=dp(40)
        )
        
        # Mode switch
        mode_layout = MDBoxLayout(
            orientation='horizontal',
            spacing=dp(10),
            size_hint_y=None,
            height=dp(40)
        )
        
        mode_label = MDLabel(
            text="Registration Mode:",
            theme_text_color="Secondary",
            size_hint_x=0.7
        )
        
        mode_switch = MDSwitch(
            active=self.is_registration_mode,
            size_hint_x=0.3,
            on_active=self.toggle_mode
        )
        
        mode_layout.add_widget(mode_label)
        mode_layout.add_widget(mode_switch)
        
        card.add_widget(station_label)
        card.add_widget(mode_layout)
        
        return card
    
    def create_nfc_card(self):
        """Create NFC interaction card"""
        card = MDCard(
            orientation='vertical',
            padding=dp(20),
            spacing=dp(15),
            elevation=2,
            size_hint_y=None,
            height=dp(300)
        )
        
        # Title
        title = MDLabel(
            text="NFC Operations",
            theme_text_color="Primary", 
            font_style="H6",
            size_hint_y=None,
            height=dp(40)
        )
        
        if self.is_registration_mode:
            # Registration UI
            guest_id_field = MDTextField(
                hint_text="Enter Guest ID",
                helper_text="Enter the guest's ID number",
                helper_text_mode="persistent",
                size_hint_y=None,
                height=dp(60)
            )
            
            write_button = MDRaisedButton(
                text="WRITE TAG",
                size_hint_y=None,
                height=dp(50),
                on_release=self.write_tag
            )
            
            card.add_widget(title)
            card.add_widget(guest_id_field)
            card.add_widget(write_button)
        else:
            # Check-in UI
            nfc_prompt = MDLabel(
                text="Ready for check-in\n\nTap NFC tag to check in guest",
                theme_text_color="Secondary",
                halign="center",
                size_hint_y=None,
                height=dp(100)
            )
            
            card.add_widget(title)
            card.add_widget(nfc_prompt)
        
        return card
    
    def create_status_card(self):
        """Create status information card"""
        card = MDCard(
            orientation='vertical',
            padding=dp(20),
            spacing=dp(10),
            elevation=2,
            size_hint_y=None,
            height=dp(100)
        )
        
        status_label = MDLabel(
            text="Status: Ready",
            theme_text_color="Primary",
            font_style="Body1"
        )
        
        connection_label = MDLabel(
            text="🔵 NFC Ready • ✅ Network Connected",
            theme_text_color="Secondary",
            font_style="Caption"
        )
        
        card.add_widget(status_label)
        card.add_widget(connection_label)
        
        return card
    
    def open_station_menu(self):
        """Open station selection menu"""
        print("Open station menu")
        # TODO: Implement station selection dialog
        
    def open_settings(self):
        """Open settings screen"""
        print("Open settings")
        # TODO: Implement settings screen
        
    def toggle_mode(self, switch, value):
        """Toggle between registration and check-in mode"""
        self.is_registration_mode = value
        print(f"Mode switched to: {'Registration' if value else 'Check-in'}")
        # TODO: Rebuild NFC card with new mode
        
    def write_tag(self, button):
        """Handle write tag button press"""
        print("Write tag button pressed")
        # TODO: Implement NFC tag writing