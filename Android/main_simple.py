#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple test Android app - just to verify buildozer works
"""

from kivymd.app import MDApp
from kivymd.uix.label import MDLabel
from kivymd.uix.screen import MDScreen


class SimpleTestApp(MDApp):
    """Simple test app"""
    
    def build(self):
        """Build the app UI."""
        screen = MDScreen()
        label = MDLabel(
            text="Hello from TP_NFC Android!",
            halign="center",
            theme_text_color="Primary"
        )
        screen.add_widget(label)
        return screen


if __name__ == '__main__':
    SimpleTestApp().run()