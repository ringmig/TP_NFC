#!/usr/bin/env python3
"""
TP_NFC Android - Simple version for GitHub Actions build
"""

from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button

class TPNFCApp(App):
    def build(self):
        # Main layout
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        
        # Title
        title = Label(
            text='TP_NFC Android',
            font_size='28sp',
            size_hint_y=None,
            height='60dp',
            bold=True
        )
        
        # Status
        self.status = Label(
            text='NFC Attendance Tracker\n\nVersion 0.1\nGitHub Actions Build',
            font_size='18sp',
            halign='center',
            valign='middle'
        )
        self.status.bind(size=self.status.setter('text_size'))
        
        # Button
        button = Button(
            text='Test Button',
            size_hint_y=None,
            height='50dp'
        )
        button.bind(on_press=self.on_button_press)
        
        # Add widgets
        layout.add_widget(title)
        layout.add_widget(self.status)
        layout.add_widget(button)
        
        return layout
    
    def on_button_press(self, instance):
        self.status.text = 'Button pressed!\n\nApp is working correctly.'

if __name__ == '__main__':
    TPNFCApp().run()