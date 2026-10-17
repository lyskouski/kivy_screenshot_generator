# Copyright 2026 The terCAD team. All rights reserved.
# Use of this source code is governed by a MIT license that can be found in the LICENSE file.

import os

from kivy.app import App
from kivy.lang import Builder
from kivy.properties import NumericProperty, StringProperty

KV = '''
BoxLayout:
    orientation: 'vertical'
    padding: dp(24)
    spacing: dp(16)
    canvas.before:
        Color:
            rgba: 0.96, 0.95, 0.99, 1
        Rectangle:
            pos: self.pos
            size: self.size
    Label:
        text: app.title_text
        font_size: sp(24)
        color: 0.2, 0.1, 0.4, 1
        size_hint_y: None
        height: dp(48)
    Label:
        text: app.counter_text
        font_size: sp(16)
        color: 0.1, 0.1, 0.1, 1
        text_size: self.width, None
        halign: 'center'
        valign: 'bottom'
    Label:
        text: str(app.counter)
        font_size: sp(40)
        color: 0.1, 0.1, 0.1, 1
        size_hint_y: None
        height: dp(56)
    Widget:
    Button:
        id: add
        text: '+'
        font_size: sp(32)
        size_hint: None, None
        size: dp(64), dp(64)
        pos_hint: {'right': 1}
        on_release: app.counter += 1
'''

TEXTS = {
    'en_US': ('Flutter Demo Home Page', 'You have pushed the button this many times:'),
    'de_DE': ('Flutter-Demo-Startseite', 'So oft wurde der Knopf gedrückt:'),
}


class MyApp(App):
    counter = NumericProperty(0)
    title_text = StringProperty('')
    counter_text = StringProperty('')

    def __init__(self, locale=None, **kwargs):
        super().__init__(**kwargs)
        self.title_text, self.counter_text = TEXTS.get(locale or os.environ.get('LANG', '')[:5], TEXTS['en_US'])

    def build(self):
        return Builder.load_string(KV)


if __name__ == '__main__':
    MyApp().run()
