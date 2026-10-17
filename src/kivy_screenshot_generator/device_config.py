# Copyright 2026 The terCAD team. All rights reserved.
# Use of this source code is governed by a MIT license that can be found in the LICENSE file.

import re
from dataclasses import dataclass, field
from enum import Enum


class TargetPlatform(str, Enum):
    IOS = 'ios'
    ANDROID = 'android'
    MACOS = 'macos'
    WINDOWS = 'windows'
    LINUX = 'linux'


@dataclass(frozen=True)
class EdgeInsets:
    top: float = 0
    bottom: float = 0
    left: float = 0
    right: float = 0


@dataclass(frozen=True)
class DeviceConfig:
    name: str
    # Physical screen size in pixels (width, height)
    size: tuple
    device_pixel_ratio: float
    platform: TargetPlatform = None
    safe_area: EdgeInsets = field(default_factory=EdgeInsets)
    navigation_bar_height: float = 56

    @property
    def logical_size(self):
        return (self.size[0] / self.device_pixel_ratio, self.size[1] / self.device_pixel_ratio)

    @property
    def folder_name(self):
        """Directory name of the device inside the locale folder (e.g. 'iPhone_15_Pro')."""
        return sanitize(self.name)

    @property
    def is_mobile(self):
        return self.platform in (TargetPlatform.IOS, TargetPlatform.ANDROID)

    def __str__(self):
        return self.name


def sanitize(value):
    return re.sub(r'[^\w\-.]', '_', value)


_IPHONE_NOTCH = EdgeInsets(top=47, bottom=34)
_IPHONE_CLASSIC = EdgeInsets(top=20, bottom=0)
_IPAD = EdgeInsets(top=24, bottom=20)


class PlatformDevices:
    """Platform-specific device configurations."""

    # iOS Devices
    IPHONE_15_PRO_MAX = DeviceConfig(
        name='iPhone 15 Pro Max',  # Apple Marketplace [iPhone 6.9" Display]
        size=(1290, 2796), device_pixel_ratio=3.0, platform=TargetPlatform.IOS, safe_area=_IPHONE_NOTCH)
    IPHONE = DeviceConfig(
        name='iPhone 6.5dm',  # Apple Marketplace [iPhone 6.5" Display]
        size=(1284, 2778), device_pixel_ratio=3.0, platform=TargetPlatform.IOS, safe_area=_IPHONE_NOTCH)
    IPHONE_15_PRO = DeviceConfig(
        name='iPhone 15 Pro',  # Apple Marketplace [iPhone 6.3" Display]
        size=(1179, 2556), device_pixel_ratio=3.0, platform=TargetPlatform.IOS, safe_area=_IPHONE_NOTCH)
    IPHONE_14 = DeviceConfig(
        name='iPhone 14',  # Apple Marketplace [iPhone 6.1" Display]
        size=(1170, 2532), device_pixel_ratio=3.0, platform=TargetPlatform.IOS, safe_area=_IPHONE_NOTCH)
    IPHONE_DUO = DeviceConfig(
        name='iPhone Duo',
        size=(1398, 2034), device_pixel_ratio=3.0, platform=TargetPlatform.IOS, safe_area=_IPHONE_NOTCH)
    IPHONE_DUO_OPENED = DeviceConfig(
        name='iPhone Duo opened',
        size=(2853, 2007), device_pixel_ratio=3.0, platform=TargetPlatform.IOS, safe_area=_IPHONE_NOTCH)
    IPHONE_55 = DeviceConfig(
        name='iPhone 5.5dm',  # Apple Marketplace [iPhone 5.5" Display]
        size=(1242, 2208), device_pixel_ratio=3.0, platform=TargetPlatform.IOS, safe_area=_IPHONE_NOTCH)
    IPHONE_SE = DeviceConfig(
        name='iPhone SE 3rd Gen',  # Apple Marketplace [iPhone 4.7" Display]
        size=(750, 1334), device_pixel_ratio=2.0, platform=TargetPlatform.IOS, safe_area=_IPHONE_CLASSIC)
    IPHONE_4DM = DeviceConfig(
        name='iPhone 4dm',  # Apple Marketplace [iPhone 4" Display]
        size=(640, 1136), device_pixel_ratio=2.0, platform=TargetPlatform.IOS, safe_area=_IPHONE_CLASSIC)
    IPHONE_3DM = DeviceConfig(
        name='iPhone 3.5dm',  # Apple Marketplace [iPhone 3.5" Display]
        size=(640, 920), device_pixel_ratio=2.0, platform=TargetPlatform.IOS)
    IPAD_PRO = DeviceConfig(
        name='iPad Pro 12.9',  # Apple Marketplace [iPad 13" Display]
        size=(2048, 2732), device_pixel_ratio=2.0, platform=TargetPlatform.IOS, safe_area=_IPAD)
    IPAD_11DM = DeviceConfig(
        name='iPad 11dm',  # Apple Marketplace [iPad 11" Display]
        size=(1668, 2420), device_pixel_ratio=2.0, platform=TargetPlatform.IOS, safe_area=_IPAD)
    IPAD_PRO_2ND = DeviceConfig(
        name='iPad Pro 2nd Gen',  # Apple Marketplace [iPad 12.9" Display]
        size=(2048, 2732), device_pixel_ratio=2.0, platform=TargetPlatform.IOS, safe_area=_IPAD)
    IPAD_10_5DM = DeviceConfig(
        name='iPad 10.5dm',  # Apple Marketplace [iPad 10.5" Display]
        size=(1668, 2224), device_pixel_ratio=2.0, platform=TargetPlatform.IOS, safe_area=_IPAD)
    IPAD_9_7DM = DeviceConfig(
        name='iPad 9.7dm',  # Apple Marketplace [iPad 9.7" Display]
        size=(1536, 2008), device_pixel_ratio=2.0, platform=TargetPlatform.IOS, safe_area=_IPAD)

    # Android Devices
    PIXEL_8_PRO = DeviceConfig(
        name='Pixel 8 Pro',
        size=(1344, 2992), device_pixel_ratio=2.8, platform=TargetPlatform.ANDROID, safe_area=EdgeInsets(top=24))
    PIXEL_7A = DeviceConfig(
        name='Pixel 7a',
        size=(1080, 2400), device_pixel_ratio=2.2, platform=TargetPlatform.ANDROID, safe_area=EdgeInsets(top=24))
    GALAXY_S24 = DeviceConfig(
        name='Galaxy S24',
        size=(1080, 2340), device_pixel_ratio=3.0, platform=TargetPlatform.ANDROID, safe_area=EdgeInsets(top=28))
    GALAXY_S24_ULTRA = DeviceConfig(
        name='Galaxy S24 Ultra',
        size=(1440, 3120), device_pixel_ratio=3.0, platform=TargetPlatform.ANDROID, safe_area=EdgeInsets(top=34))
    GALAXY_TAB_S9 = DeviceConfig(
        name='Galaxy Tab S9',
        size=(1600, 2560), device_pixel_ratio=2.0, platform=TargetPlatform.ANDROID, safe_area=EdgeInsets(top=24))

    # Desktop Devices
    MACBOOK = DeviceConfig(
        name='MacBook',  # Apple Marketplace
        size=(2880, 1800), device_pixel_ratio=2.0, platform=TargetPlatform.MACOS, navigation_bar_height=0)
    MACBOOK_PRO_14 = DeviceConfig(
        name='MacBook Pro 14dm',
        size=(3024, 1964), device_pixel_ratio=2.0, platform=TargetPlatform.MACOS, navigation_bar_height=0)
    MACBOOK_AIR_13 = DeviceConfig(
        name='MacBook Air 13dm',
        size=(2560, 1664), device_pixel_ratio=2.0, platform=TargetPlatform.MACOS, navigation_bar_height=0)
    WINDOWS_1080P = DeviceConfig(
        name='Windows 1080p',
        size=(1920, 1080), device_pixel_ratio=1.0, platform=TargetPlatform.WINDOWS, navigation_bar_height=0)
    WINDOWS_1440P = DeviceConfig(
        name='Windows 1440p',
        size=(2560, 1440), device_pixel_ratio=1.25, platform=TargetPlatform.WINDOWS, navigation_bar_height=0)
    LINUX_1080P = DeviceConfig(
        name='Linux 1080p',
        size=(1920, 1080), device_pixel_ratio=1.0, platform=TargetPlatform.LINUX, navigation_bar_height=0)

    # Grouped collections
    IPHONES = (IPHONE, IPHONE_15_PRO, IPHONE_15_PRO_MAX, IPHONE_14, IPHONE_DUO, IPHONE_DUO_OPENED,
               IPHONE_55, IPHONE_SE, IPHONE_4DM, IPHONE_3DM)
    IPADS = (IPAD_PRO, IPAD_11DM, IPAD_PRO_2ND, IPAD_10_5DM, IPAD_9_7DM)
    ANDROID_PHONES = (PIXEL_8_PRO, PIXEL_7A, GALAXY_S24, GALAXY_S24_ULTRA)
    ANDROID_TABLETS = (GALAXY_TAB_S9,)
    DESKTOPS = (MACBOOK, MACBOOK_PRO_14, MACBOOK_AIR_13, WINDOWS_1080P, WINDOWS_1440P, LINUX_1080P)

    ALL_DEVICES = IPHONES + IPADS + ANDROID_PHONES + ANDROID_TABLETS + DESKTOPS
    MOBILE_DEVICES = IPHONES + ANDROID_PHONES
    TABLET_DEVICES = IPADS + ANDROID_TABLETS

    @classmethod
    def by_name(cls, name):
        """Find a device by its name or folder name (e.g. 'iPhone 15 Pro' or 'iPhone_15_Pro')."""
        return next((d for d in cls.ALL_DEVICES if name in (d.name, d.folder_name)), None)
