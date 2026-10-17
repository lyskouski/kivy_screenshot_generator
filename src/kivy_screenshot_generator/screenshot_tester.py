"""Interaction helpers for screenshot steps (Kivy counterpart of Flutter's `WidgetTester`).

Imported only inside the screenshot process: it pulls in the Kivy window.
"""

import asyncio
import os
import time

from kivy.animation import Animation
from kivy.base import EventLoop
from kivy.core.image import Image
from kivy.core.window import Window
from kivy.graphics import ClearBuffers, ClearColor, Fbo, Scale, Translate
from kivy.input.motionevent import MotionEvent
from kivy.uix.screenmanager import ScreenManager

# Two frames at 60 FPS: enough for Clock callbacks and a redraw
_FRAME = 1 / 30


class _Touch(MotionEvent):
    """Synthetic single touch dispatched through the regular input pipeline."""

    def __init__(self, x, y):
        super().__init__('ScreenshotTouch', id(self), self._args(x, y), is_touch=True, type_id='touch')
        self.profile = ['pos']

    @staticmethod
    def _args(x, y):
        return {'x': x / max(Window.width - 1.0, 1), 'y': y / max(Window.height - 1.0, 1)}

    def depack(self, args):
        self.sx = args['x']
        self.sy = args['y']
        super().depack(args)

    def down(self):
        EventLoop.post_dispatch_input('begin', self)

    def move_to(self, x, y):
        self.move(self._args(x, y))
        EventLoop.post_dispatch_input('update', self)

    def up(self):
        EventLoop.post_dispatch_input('end', self)


class ScreenshotTester:
    """Drives the running app from screenshot steps: find widgets, tap, type, wait."""

    def __init__(self, app):
        self.app = app

    @property
    def window(self):
        return Window

    # Waiting

    async def pump(self, duration=None):
        """Let the app process events and redraw, for `duration` seconds or a couple of frames."""
        await asyncio.sleep(max(duration or 0, _FRAME))

    def _is_animating(self):
        if Animation._instances:
            return True
        return any(isinstance(w, ScreenManager) and w.transition.is_active for w in self.walk())

    async def pump_and_settle(self, duration=0.1, timeout=10):
        """Pump at least `duration` seconds, then until animations and screen transitions finish."""
        await self.pump(duration)
        deadline = time.monotonic() + timeout
        while self._is_animating():
            if time.monotonic() > deadline:
                raise TimeoutError(f'Animations still running after {timeout}s')
            await self.pump()

    # Finding

    def walk(self):
        """All widgets of the window, including popups and dropdowns attached next to the root."""
        for child in reversed(Window.children):
            yield from child.walk(restrict=True)

    def find_all(self, predicate):
        return [w for w in self.walk() if predicate(w)]

    def find(self, predicate, index=0):
        """Return the `index`-th widget matching `predicate`; fail when it is not on screen."""
        matches = self.find_all(predicate)
        if len(matches) <= index:
            raise LookupError(f'Widget not found ({len(matches)} matches, index {index})')
        return matches[index]

    def find_by_id(self, widget_id, index=0):
        """Widget declared with `id: <widget_id>` in any KV rule."""
        matches = []
        for widget in self.walk():
            target = getattr(widget, 'ids', {}).get(widget_id)
            if target is not None and target not in matches:
                matches.append(target)
        if len(matches) <= index:
            raise LookupError(f"Widget with id '{widget_id}' not found")
        return matches[index]

    def find_by_text(self, text, index=0, exact=True):
        def matches(widget):
            value = getattr(widget, 'text', None)
            if not isinstance(value, str):
                return False
            return value == text if exact else text in value
        return self.find(matches, index)

    def find_by_type(self, cls, index=0):
        if isinstance(cls, str):
            return self.find(lambda w: type(w).__name__ == cls, index)
        return self.find(lambda w: isinstance(w, cls), index)

    # Interacting

    @staticmethod
    def _center(widget):
        return widget.to_window(widget.center_x, widget.center_y)

    async def tap(self, widget, duration=0.05):
        """Press and release a touch in the center of `widget`."""
        touch = _Touch(*self._center(widget))
        touch.down()
        await self.pump(duration)
        touch.up()
        await self.pump()

    async def long_press(self, widget, duration=1.0):
        await self.tap(widget, duration)

    async def drag(self, widget, dx, dy, steps=10, duration=0.3):
        """Swipe from the center of `widget` by (`dx`, `dy`) pixels."""
        x, y = self._center(widget)
        touch = _Touch(x, y)
        touch.down()
        for step in range(1, steps + 1):
            await self.pump(duration / steps)
            touch.move_to(x + dx * step / steps, y + dy * step / steps)
        touch.up()
        await self.pump()

    async def enter_text(self, widget, text):
        """Focus a TextInput and replace its content."""
        widget.focus = True
        await self.pump()
        widget.text = text
        await self.pump()

    async def show_screen(self, name, manager=None):
        """Switch a ScreenManager (the root one by default) to the screen `name`."""
        manager = manager or self.find_by_type(ScreenManager)
        manager.current = name
        await self.pump_and_settle()

    # Capturing

    def capture(self, path):
        """Save the whole window (popups and dropdowns included) as PNG in physical pixels.

        Renders the window canvas into an offscreen buffer, so it works for hidden windows too.
        """
        width, height = Window.size
        canvas = Window.canvas
        context = Window.render_context
        index = context.indexof(canvas)
        context.remove(canvas)
        fbo = Fbo(size=(width, height), with_stencilbuffer=True)
        with fbo:
            ClearColor(*(Window.clearcolor or (0, 0, 0, 1)))
            ClearBuffers()
            Scale(1, -1, 1)
            Translate(0, -height, 0)
        fbo.add(canvas)
        try:
            fbo.draw()
            image = Image(fbo.texture)
        finally:
            fbo.remove(canvas)
            context.insert(index, canvas)

        os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
        image.save(path, flipped=False)
        return path
