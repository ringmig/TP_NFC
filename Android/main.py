#!/usr/bin/env python3

from kivy.app import App
from kivy.uix.label import Label


class TestApp(App):
    def build(self):
        return Label(text='Hello World!')


if __name__ == '__main__':
    TestApp().run()