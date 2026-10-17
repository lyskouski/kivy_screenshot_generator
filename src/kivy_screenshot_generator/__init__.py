# Copyright 2026 The terCAD team. All rights reserved.
# Use of this source code is governed by a MIT license that can be found in the LICENSE file.

"""Generate screenshots for a Kivy application across different screens and languages."""

from .device_config import DeviceConfig, EdgeInsets, PlatformDevices, TargetPlatform
from .generator import ScreenshotGenerator, ScreenshotJob
from .screenshot_config import ScreenshotConfig, ScreenshotPresets

__version__ = '1.0.0'

__all__ = [
    'DeviceConfig',
    'EdgeInsets',
    'PlatformDevices',
    'ScreenshotConfig',
    'ScreenshotGenerator',
    'ScreenshotJob',
    'ScreenshotPresets',
    'ScreenshotTester',
    'TargetPlatform',
]


def __getattr__(name):
    # Loaded lazily: importing it creates the Kivy window
    if name == 'ScreenshotTester':
        from .screenshot_tester import ScreenshotTester
        return ScreenshotTester
    raise AttributeError(name)
