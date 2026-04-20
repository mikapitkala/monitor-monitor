# Monitor... uh Monitor

A hacky little script that keeps an eye on the number of connected monitors and then forces them into a specific behavior instead of defaulting to **Clone**. You can also quickly change your display setting by double clicking the desired mode. Lives on the system tray.

## The Issue

When you connect a new display to Windows for the first time, it defaults to **Clone**. 
This is fine at home, but quite annoying if you happen to be:

- A consultant or someone else who spends a lot of time in meeting rooms with external screens and monitors
- A teacher using classroom displays  
- Anyone who regularly plugs into strange new screens
- Tired of manually pressing Win+P every single time

**Monitor Monitor** sits in your system tray and automatically switches to your preferred mode (default: **Extend**) whenever a new display appears.

## Features

- Automatic mode switching on display connect/disconnect
- Four modes: Internal only, Clone, Extend, External only
- Lurks quietly in your system tray, watching... waiting... for an external monitor to show up
- Follows your Windows light/dark mode preference
- Quick-switch via tray icon or double-click
- Can start minimized with your preferred mode

## Installation

### Option 1: Download the .exe (Easiest)
1. Download the latest release from [Releases](link)
2. Extract and run `monitor-monitor.exe`
3. Windows Defender should make some noise about not running weird files you got off the Internet. Technically, Windows Defender is correct, you probably *shouldn't* run weird things you download online, but you can click on **More Information** and then **Run Anyway**, if you're feeling particularly confident.

### Option 2: Run from Source
\`\`\`bash
git clone https://github.com/mikapitkala/monitor-monitor
cd monitor-monitor
pip install -r requirements.txt
python -m monitor_monitor
\`\`\`

## Usage

1. Run `detect_screen_gui.exe` or `python -m monitor_monitor` depending on how you got your hands on it
2. You should see the user interface on the bottom right hand corner of your primary screen
3. Pick whichever mode you like. Default is **Extend** since that was the original ask in the Teams chat that spawned this project
4. Hook up a new screen, give it a few seconds and watch it do its thing
5. You can also minimize it to your system tray. You should see a little blue icon that indicates which mode is currently selected
6. You can quickly change the behavior by right clicking on the system tray icon and picking the mode you want
7. You can also *double click* on any of the modes in the UI to instantly switch to that display mode
8. Hit the red **Close** button or right click -> **Close** on the system tray icon to close the app

## Slightly Advanced Usage

You can add command line arguments to select the mode you like and start the app minimized to system tray.

```
'1' or 'internal' for Internal Only
'2' or 'clone' for Cloning the screen
'3' or 'extend' for Extending the screen (default setting)
'4' or 'external' for External Only

'--minimized' Start the application minimized to the system tray
```

For example, `detect_screen_gui.exe clone --minimized` will start the script in **Clone** mode and minimized.

Starting without any parameters will start in **Extend** mode.

## Automate

You can place a shortcut to the .exe file in your Windows *startup* folder:

1. Fire up an **Explorer** (Win + E) or **Run** window (Win + R) and enter `shell:startup` in the text field
2. Create a new shortcut and point it to wherever you put `detect_screen_gui.exe` along with any command line arguments you want to use

or set up **Task Scheduler** to run it automatically on login.

## Caveats

- **Windows only** - relies on PowerShell and DisplaySwitch.exe
- **Not instant** - the polling means there's a 1-5 second delay when connecting a new screen
- **Doesn't manage positions** - you may still need to rearrange displays in Windows Display Settings
- **Light/dark mode follows the OS** - no manual override
- **You can run multiple instances** - probably won't break anything, but try not to

## How It Works / FAQ

Monitor Monitor polls for connected displays every 5 seconds using a PowerShell query against WMI (`WmiMonitorBasicDisplayParams`). When the count changes, it invokes `DisplaySwitch.exe` with your preferred mode.

### WTF? Why would you do it like that?
Because the obvious `WM_DISPLAYCHANGE` Windows message doesn't seem to fire reliably when switching to clone mode (since the resolution doesn't necessarily change). Polling was a dumb solution to a stupid problem.

### Why PyInstaller? I'm sure you could make it smaller and more elegant.
Mostly to sneak around endpoint protection at work. Python was allowed.

## License

MIT - do whatever you want with it.
