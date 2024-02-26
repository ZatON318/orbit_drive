from infi.systray import SysTrayIcon

def say_hello(systray):
    print("Hello, World!")
menu_options = (("Say Hello", None, say_hello),)
systray = SysTrayIcon("icon.ico", "Orbit Drive", menu_options)
systray.start()