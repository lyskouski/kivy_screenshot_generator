import json
import os

import pytest

from kivy_screenshot_generator import (
    PlatformDevices,
    ScreenshotConfig,
    ScreenshotGenerator,
    ScreenshotPresets,
    TargetPlatform,
)
from kivy_screenshot_generator.generator import JOB_ENV

ENV = ('SCREENSHOT_DEVICES', 'SCREENSHOT_LOCALES', 'SCREENSHOT_STEPS', 'SKIP_EXISTANT', 'SKIP_EXISTING')


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for name in ENV:
        monkeypatch.delenv(name, raising=False)


def make(config=None):
    gen = ScreenshotGenerator(locales=['en_US', 'de_DE'], fn_get_app=lambda: None, config=config)
    gen.inject('1_home')
    gen.inject('2_tap')
    return gen


def test_default_config_disables_linux():
    devices = ScreenshotConfig().get_enabled_devices()
    assert PlatformDevices.LINUX_1080P not in devices
    assert PlatformDevices.WINDOWS_1080P in devices


def test_comprehensive_is_default_and_has_all_devices():
    assert set(make().devices) == set(PlatformDevices.ALL_DEVICES)


def test_presets_filter_platforms():
    assert all(d.platform == TargetPlatform.IOS for d in ScreenshotPresets.ios_only().get_enabled_devices())
    mobile = ScreenshotPresets.mobile_only().get_enabled_devices()
    assert set(mobile) == set(PlatformDevices.MOBILE_DEVICES)
    desktop = ScreenshotPresets.desktop_only().get_enabled_devices()
    assert set(desktop) == set(PlatformDevices.DESKTOPS)


def test_device_names_are_unique():
    names = [d.name for d in PlatformDevices.ALL_DEVICES]
    assert len(names) == len(set(names))


def test_folder_names_match():
    assert PlatformDevices.IPHONE_15_PRO.folder_name == 'iPhone_15_Pro'
    assert PlatformDevices.IPAD_10_5DM.folder_name == 'iPad_10.5dm'
    assert PlatformDevices.by_name('iPad_10.5dm') is PlatformDevices.IPAD_10_5DM


def test_filters_by_env(monkeypatch):
    monkeypatch.setenv('SCREENSHOT_DEVICES', 'iPhone 15 Pro, Pixel_7a')
    monkeypatch.setenv('SCREENSHOT_LOCALES', 'de_DE')
    monkeypatch.setenv('SCREENSHOT_STEPS', '2_tap')
    gen = make()
    jobs = gen._collect_jobs()
    assert [(j.step, j.device.name, j.locale) for j in jobs] == [
        ('2_tap', 'iPhone 15 Pro', 'de_DE'),
        ('2_tap', 'Pixel 7a', 'de_DE'),
    ]


def test_jobs_keep_locale_device_step_order(monkeypatch):
    monkeypatch.setenv('SCREENSHOT_DEVICES', 'Pixel 7a')
    jobs = make()._collect_jobs()
    assert [(j.locale, j.step) for j in jobs] == [
        ('en_US', '1_home'), ('en_US', '2_tap'), ('de_DE', '1_home'), ('de_DE', '2_tap'),
    ]


def test_skip_existing_device_folders(monkeypatch, tmp_path):
    monkeypatch.setenv('SCREENSHOT_DEVICES', 'Pixel 7a,Galaxy S24')
    monkeypatch.setenv('SKIP_EXISTANT', 'true')
    os.makedirs(tmp_path / 'en_US' / 'Pixel_7a')
    gen = make(ScreenshotConfig(output_directory=str(tmp_path)))
    jobs = gen._collect_jobs()
    assert {(j.locale, j.device.name) for j in jobs} == {
        ('en_US', 'Galaxy S24'), ('de_DE', 'Pixel 7a'), ('de_DE', 'Galaxy S24'),
    }


def test_output_path(tmp_path):
    gen = make(ScreenshotConfig(output_directory=str(tmp_path)))
    gen.inject('3 with space')
    monkey_job = next(j for j in gen._collect_jobs() if j.step == '3 with space')
    assert gen.output_path(monkey_job) == os.path.join(
        str(tmp_path), monkey_job.locale, monkey_job.device.folder_name, '3_with_space.png')


def test_job_env_emulates_device():
    gen = make()
    job = next(j for j in gen._collect_jobs() if j.device == PlatformDevices.PIXEL_8_PRO)
    env = gen._job_env(job, use_xvfb=True)
    assert json.loads(env[JOB_ENV]) == {'step': job.step, 'device': 'Pixel 8 Pro', 'locale': job.locale}
    assert (env['KCFG_GRAPHICS_WIDTH'], env['KCFG_GRAPHICS_HEIGHT']) == ('1344', '2992')
    assert env['KIVY_METRICS_DENSITY'] == '2.8'
    assert env['SCREENSHOT_PLATFORM'] == 'android'
    assert env['SDL_VIDEODRIVER'] == 'x11'
    assert 'KCFG_GRAPHICS_WINDOW_STATE' not in env
    assert gen._job_env(job, use_xvfb=False)['KCFG_GRAPHICS_WINDOW_STATE'] == 'hidden'


def test_xvfb_screen_fits_device():
    gen = make()
    job = next(j for j in gen._collect_jobs() if j.device == PlatformDevices.MACBOOK)
    command = gen._job_command(job, use_xvfb=True)
    assert command[0] == 'xvfb-run'
    assert '-screen 0 2880x1800x24' in command[2]
