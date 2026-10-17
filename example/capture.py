from kivy_screenshot_generator import ScreenshotGenerator


def get_app():
    # Imported here: the Kivy window must be created after the device settings are applied
    from main import MyApp
    return MyApp(locale=gen.job.locale)


async def tap(tester):
    await tester.tap(tester.find_by_id('add'))
    await tester.pump()


gen = ScreenshotGenerator(locales=['en_US', 'de_DE'], fn_get_app=get_app)
gen.inject('1_home')
gen.inject('2_tap', before=tap)

if __name__ == '__main__':
    gen.run()
