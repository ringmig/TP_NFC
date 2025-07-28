#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TP_NFC Android - Main entry point
"""

import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from kivy.app import App
from kivy.lang import Builder
from kivymd.app import MDApp
from kivymd.theming import ThemableBehavior
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.screen import MDScreen

from src.gui.screens.main_screen import MainScreen
from src.services.config_service import ConfigService

class TPNFCApp(MDApp):
    """TP_NFC Android Application"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = "TP NFC - Attendance Tracker"
        
        # Load configuration
        self.config_service = ConfigService()
        self.config = self.config_service.load_config()
        
        # Theme setup
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.accent_palette = "Orange"
        
    def build(self):
        """Build the application"""
        # Create screen manager
        sm = MDScreenManager()
        
        # Add main screen
        main_screen = MainScreen(name='main')
        sm.add_widget(main_screen)
        
        return sm

if __name__ == '__main__':
    TPNFCApp().run()