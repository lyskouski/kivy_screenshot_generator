import asyncio
import inspect
import json
import os
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

from .device_config import PlatformDevices, sanitize
from .screenshot_config import ScreenshotPresets

# Set for the process that renders one screenshot; its absence means "orchestrate"
JOB_ENV = 'KIVY_SCREENSHOT_JOB'


def _csv_env(name):
    return [v.strip() for v in os.environ.get(name, '').split(',') if v.strip()]


def _flag_env(name):
    value = os.environ.get(name)
    return None if value is None else value.strip().lower() in ('1', 'true', 'yes')


@dataclass(frozen=True)
class ScreenshotJob:
    step: str
    device: object
    locale: str

    @property
    def title(self):
        return f'{self.step} - {self.device.name} - {self.locale}'


class ScreenshotGenerator:
    """Generate screenshots of a Kivy application across devices, locales and steps.

    Each screenshot is taken by a fresh process running the same script, so every step
    starts from a newly built app with the device's window size and pixel density.
    """

    def __init__(self, locales, fn_get_app, fn_init=None, config=None):
        """
        Args:
            locales: Locale codes; each one gets its own output folder (e.g. ['en_US', 'de_DE']).
            fn_get_app: Returns the (not yet running) App instance. Import the app inside it,
                so that the Kivy window is created only after the device settings are applied.
            fn_init: Optional `fn(device, config, locale)` (sync or async) called before
                `fn_get_app`, e.g. to prepare preferences for the locale.
            config: ScreenshotConfig; all devices of `ScreenshotPresets.comprehensive()` by default.
        """
        self.config = config or ScreenshotPresets.comprehensive()
        self.locales = list(locales)
        self.fn_get_app = fn_get_app
        self.fn_init = fn_init
        self.steps = {}
        self.devices = []
        # Current screenshot, set inside the screenshot process
        self.job = None
        self._init_devices()
        self._init_locales()

    # SCREENSHOT_DEVICES="iPhone 15 Pro,Pixel 7a"
    def _init_devices(self):
        enabled = self.config.get_enabled_devices()
        names = _csv_env('SCREENSHOT_DEVICES')
        if names:
            self.devices = [d for d in enabled if d.name in names or d.folder_name in names]
        else:
            self.devices = enabled

    # SCREENSHOT_LOCALES=en_US,de_DE
    def _init_locales(self):
        codes = _csv_env('SCREENSHOT_LOCALES')
        if codes:
            self.locales = [locale for locale in self.locales if locale in codes]

    def inject(self, title, before=None):
        """Register a screenshot. `before` is an optional `async fn(tester)` run before capturing.

        Steps are taken in the order they were injected, each one from a freshly started app.
        """
        self.steps[title] = before

    def output_path(self, job):
        return os.path.join(self.config.output_directory, job.locale, job.device.folder_name,
                            f'{sanitize(job.step)}.png')

    def run(self):
        """Main entry point: take all screenshots, or the single one this process was spawned for."""
        payload = os.environ.get(JOB_ENV)
        if payload:
            sys.exit(self._run_job(json.loads(payload)))
        sys.exit(self._run_all())

    # Orchestration

    def _collect_jobs(self):
        step_filter = set(_csv_env('SCREENSHOT_STEPS'))
        skip_existing = _flag_env('SKIP_EXISTANT') or _flag_env('SKIP_EXISTING')
        jobs = []
        for locale in self.locales:
            for device in self.devices:
                folder = os.path.join(self.config.output_directory, locale, device.folder_name)
                if skip_existing and os.path.isdir(folder):
                    print(f'Skipping {locale}/{device.name} - folder exists with screenshots')
                    continue
                for step in self.steps:
                    if step_filter and step not in step_filter:
                        continue
                    jobs.append(ScreenshotJob(step, device, locale))
        return jobs

    def _use_xvfb(self):
        headless = _flag_env('SCREENSHOT_HEADLESS')
        if headless is None:
            headless = self.config.headless
        available = sys.platform.startswith('linux') and shutil.which('xvfb-run') is not None
        if headless and not available:
            raise RuntimeError('Headless mode needs `xvfb-run` (e.g. `apt install xvfb`)')
        return available if headless is None else headless

    def _job_command(self, job, use_xvfb):
        # Re-run the very same script (`python capture.py`, `python -m pkg.capture`, ...)
        argv = list(getattr(sys, 'orig_argv', [sys.executable] + sys.argv))
        argv[0] = sys.executable
        if not use_xvfb:
            return argv
        width, height = job.device.size
        return ['xvfb-run', '--auto-servernum',
                f'--server-args=-screen 0 {width}x{height}x24 +extension GLX +render -noreset'] + argv

    def _job_env(self, job, use_xvfb):
        device = job.device
        width, height = device.size
        env = dict(os.environ)
        env.update({
            JOB_ENV: json.dumps({'step': job.step, 'device': device.name, 'locale': job.locale}),
            'KIVY_NO_ARGS': '1',
            'KIVY_METRICS_DENSITY': str(device.device_pixel_ratio),
            'KIVY_METRICS_FONTSCALE': '1',
            'KIVY_DPI': str(round(160 * device.device_pixel_ratio)),
            'KCFG_KIVY_LOG_LEVEL': self.config.log_level,
            'KCFG_GRAPHICS_WIDTH': str(width),
            'KCFG_GRAPHICS_HEIGHT': str(height),
            'KCFG_GRAPHICS_FULLSCREEN': '0',
            'KCFG_GRAPHICS_BORDERLESS': '1',
            'KCFG_GRAPHICS_RESIZABLE': '0',
            'KCFG_GRAPHICS_POSITION': 'custom',
            'KCFG_GRAPHICS_LEFT': '0',
            'KCFG_GRAPHICS_TOP': '0',
            # Available to the app to adapt its layout to the emulated device
            'SCREENSHOT_DEVICE': device.name,
            'SCREENSHOT_PLATFORM': device.platform.value if device.platform else '',
            'SCREENSHOT_LOCALE': job.locale,
            'SCREENSHOT_STEP': job.step,
        })
        if use_xvfb:
            # The virtual X server is the only display; keep SDL away from a Wayland session
            env['SDL_VIDEODRIVER'] = 'x11'
            env.pop('WAYLAND_DISPLAY', None)
        else:
            env['KCFG_GRAPHICS_WINDOW_STATE'] = 'hidden'
        return env

    def _spawn(self, job, use_xvfb):
        started = time.monotonic()
        try:
            result = subprocess.run(self._job_command(job, use_xvfb), env=self._job_env(job, use_xvfb),
                                    capture_output=True, text=True, timeout=self.config.timeout, check=False)
            ok, output = result.returncode == 0, result.stdout + result.stderr
        except subprocess.TimeoutExpired as e:
            ok, output = False, f'Timed out after {self.config.timeout}s\n{e.stdout or ""}{e.stderr or ""}'
        status = 'OK  ' if ok else 'FAIL'
        print(f'{status} {job.title} ({time.monotonic() - started:.1f}s)', flush=True)
        if not ok:
            print(output.rstrip(), flush=True)
        return ok

    def _run_all(self):
        jobs = self._collect_jobs()
        print(f'Devices: {[d.name for d in self.devices]}')
        print(f'Locales: {self.locales}')
        print(f'Screenshots to take: {len(jobs)}', flush=True)
        if not jobs:
            return 0
        use_xvfb = self._use_xvfb()
        workers = int(os.environ.get('SCREENSHOT_WORKERS') or self.config.workers)
        with ThreadPoolExecutor(max_workers=max(workers, 1)) as pool:
            results = list(pool.map(lambda job: self._spawn(job, use_xvfb), jobs))
        failed = results.count(False)
        print(f'Done: {len(jobs) - failed} saved to {self.config.output_directory}, {failed} failed')
        return 1 if failed else 0

    # Single screenshot (inside the spawned process)

    def _run_job(self, payload):
        device = PlatformDevices.by_name(payload['device'])
        self.job = ScreenshotJob(payload['step'], device, payload['locale'])
        try:
            asyncio.run(self._capture(self.job))
        except Exception:  # noqa: BLE001 - any failure of the app or the steps is reported
            import traceback
            traceback.print_exc()
            return 1
        return 0

    async def _capture(self, job):
        if self.fn_init is not None:
            result = self.fn_init(job.device, self.config, job.locale)
            if inspect.isawaitable(result):
                await result

        app = self.fn_get_app()
        driver = asyncio.ensure_future(self._drive(app, job))
        await app.async_run(async_lib='asyncio')
        # Surfaces errors of the steps (the app is already stopped by then)
        path = await driver
        print(f'Screenshot saved: {path}')

    async def _drive(self, app, job):
        from .screenshot_tester import ScreenshotTester
        tester = ScreenshotTester(app)
        try:
            while app.root is None or app.root.get_root_window() is None:
                await tester.pump()
            if tuple(tester.window.size) != tuple(job.device.size):
                raise RuntimeError(
                    f'Window is {tuple(tester.window.size)} instead of {job.device.size} '
                    '(limited by the monitor?): run with SCREENSHOT_HEADLESS=1 on Linux with xvfb')
            await tester.pump_and_settle(0.5 if job.device.is_mobile else 0.2)

            before = self.steps.get(job.step)
            if before is not None:
                await before(tester)

            await tester.pump_and_settle(self.config.animation_settle_time)
            return tester.capture(self.output_path(job))
        finally:
            app.stop()
