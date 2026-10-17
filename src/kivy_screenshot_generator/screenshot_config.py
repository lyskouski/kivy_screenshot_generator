from dataclasses import dataclass, field

from .device_config import PlatformDevices, TargetPlatform


def _platforms(ios=True, android=True, macos=True, windows=True, linux=False):
    return {'ios': ios, 'android': android, 'macos': macos, 'windows': windows, 'linux': linux}


def _device_types(phones=True, tablets=True, desktops=True):
    return {'phones': phones, 'tablets': tablets, 'desktops': desktops}


@dataclass
class ScreenshotConfig:
    # Linux is disabled by default for CI compatibility
    enabled_platforms: dict = field(default_factory=_platforms)
    enabled_device_types: dict = field(default_factory=_device_types)
    output_directory: str = 'screenshots'
    # Seconds to wait for animations before taking the screenshot
    animation_settle_time: float = 0.5
    # Render inside a virtual X server (xvfb-run) so windows larger than the monitor keep their size:
    # None = auto (Linux with xvfb-run installed), True = required, False = hidden local window
    headless: bool = None
    # Parallel app instances (each one is a separate process)
    workers: int = 1
    # Seconds before a single screenshot process is killed
    timeout: float = 180
    # Kivy log level inside the screenshot processes
    log_level: str = 'warning'

    def get_enabled_devices(self):
        """Get filtered device list based on configuration."""
        platforms = self.enabled_platforms
        types = self.enabled_device_types
        devices = []

        if types.get('phones'):
            if platforms.get('ios'):
                devices.extend(PlatformDevices.IPHONES)
            if platforms.get('android'):
                devices.extend(PlatformDevices.ANDROID_PHONES)

        if types.get('tablets'):
            if platforms.get('ios'):
                devices.extend(PlatformDevices.IPADS)
            if platforms.get('android'):
                devices.extend(PlatformDevices.ANDROID_TABLETS)

        if types.get('desktops'):
            desktop_platforms = (TargetPlatform.MACOS, TargetPlatform.WINDOWS, TargetPlatform.LINUX)
            devices.extend(d for d in PlatformDevices.DESKTOPS
                           if d.platform in desktop_platforms and platforms.get(d.platform.value))

        return devices


class ScreenshotPresets:
    """Predefined configurations for different scenarios (each call returns a fresh config)."""

    @staticmethod
    def mobile_only():
        return ScreenshotConfig(
            enabled_platforms=_platforms(macos=False, windows=False),
            enabled_device_types=_device_types(tablets=False, desktops=False))

    @staticmethod
    def ios_only():
        return ScreenshotConfig(
            enabled_platforms=_platforms(android=False, macos=False, windows=False),
            enabled_device_types=_device_types(desktops=False))

    @staticmethod
    def android_only():
        return ScreenshotConfig(
            enabled_platforms=_platforms(ios=False, macos=False, windows=False),
            enabled_device_types=_device_types(desktops=False))

    @staticmethod
    def desktop_only():
        return ScreenshotConfig(
            enabled_platforms=_platforms(ios=False, android=False, linux=True),
            enabled_device_types=_device_types(phones=False, tablets=False))

    @staticmethod
    def ci_optimized():
        """Fewer devices for faster builds."""
        return ScreenshotConfig(
            enabled_platforms=_platforms(macos=False, windows=False),
            enabled_device_types=_device_types(tablets=False, desktops=False),
            headless=True)

    @staticmethod
    def comprehensive():
        return ScreenshotConfig(enabled_platforms=_platforms(linux=True))
