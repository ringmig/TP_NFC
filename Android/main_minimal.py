#!/usr/bin/env python3

from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout

class SimpleTPNFCApp(App):
    def build(self):
        layout = BoxLayout(orientation='vertical', padding=50, spacing=20)
        
        title = Label(
            text='TP_NFC Android App',
            font_size='24sp',
            size_hint_y=None,
            height='60dp'
        )
        
        status = Label(
            text='NFC Attendance Tracker\n\nBuilt with Python 3.11\nMinimal working version',
            font_size='16sp',
            halign='center'
        )
        status.bind(size=status.setter('text_size'))
        
        layout.add_widget(title)
        layout.add_widget(status)
        
        return layout

if __name__ == '__main__':
    SimpleTPNFCApp().run()