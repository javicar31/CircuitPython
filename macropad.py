from adafruit_macropad import MacroPad
from rainbowio import colorwheel
import time

macropad = MacroPad()
encoder_last_position = macropad.encoder
encoder_pressed_time = None
profile_last_action = time.monotonic()

# --- Tones for keypresses ---
tones = [196, 220, 246, 262, 294, 330, 349, 392, 440, 494, 523, 587]

# --- State ---
profile_menu = False
current_profile = 0
shortcut_index = 0

# --- Profiles ---
profiles = [
    {
        "name": "NumPad",
        "display_name": "NumPad",
        "rotation": 0,
        "volume": True,
        "keys": {
            0: macropad.Keycode.ONE,
            1: macropad.Keycode.TWO,
            2: macropad.Keycode.THREE,
            3: macropad.Keycode.FOUR,
            4: macropad.Keycode.FIVE,
            5: macropad.Keycode.SIX,
            6: macropad.Keycode.SEVEN,
            7: macropad.Keycode.EIGHT,
            8: macropad.Keycode.NINE,
            9: macropad.Keycode.ZERO,
            10: macropad.Keycode.MINUS,
            11: macropad.Keycode.EQUALS
        }
    },
    {
        "name": "Gaming (WASD)",
        "display_name": "Gaming\nWASD",
        "rotation": 90,
        "volume": True,
        "keys": {
            8: macropad.Keycode.W,
            4: macropad.Keycode.A,
            7: macropad.Keycode.S,
            10: macropad.Keycode.D,
            1: macropad.Keycode.SHIFT,
            3: macropad.Keycode.SPACE,
            6: macropad.Keycode.SPACE,
            9: macropad.Keycode.SPACE,
            5: macropad.Keycode.Q,
            11: macropad.Keycode.E
        }
    },
    {
        "name": "Mac Shortcuts",
        "display_name": "Mac\nShortcuts",
        "rotation": 0,
        "volume": False,
        "shortcuts": [
            ["Command", "SPACE", "safari", macropad.Keycode.RETURN],  # Open Safari
            ["Command", "SPACE", "steam", macropad.Keycode.RETURN],   # Open Steam
            ["Command", "SHIFT", "3"],                                 # Screenshot
            []                                                         # Blank
        ]
    },
    {
        "name": "Windows Shortcuts",
        "display_name": "Windows\nShortcuts",
        "rotation": 0,
        "volume": False,
        "shortcuts": [
            [macropad.Keycode.GUI, "r", macropad.Keycode.RETURN, "https://youtube.com", macropad.Keycode.RETURN],
            [macropad.Keycode.GUI, "r", macropad.Keycode.RETURN, "steam", macropad.Keycode.RETURN],
            [macropad.Keycode.GUI, macropad.Keycode.E],  # File explorer
            []
        ]
    },
    {
        "name": "Linux Shortcuts",
        "display_name": "Linux\nShortcuts",
        "rotation": 0,
        "volume": False,
        "shortcuts": [
            [macropad.Keycode.CONTROL, macropad.Keycode.ALT, "t"],  # Terminal
            ["steam"],
            ["echo 'Hello Linux'"],
            []
        ]
    }
]

# --- Display helper ---
def display_message(title, message=""):
    text_lines = macropad.display_text(title=title)
    if message:
        text_lines[1].text = message
    text_lines.show()

# --- Profile loader ---
def load_profile(index):
    profile = profiles[index]
    macropad.display.rotation = profile.get("rotation", 0)
    display_message("Profile", profile.get("display_name", profile["name"]))

# --- Key sequence processor ---
def process_sequence(seq):
    for item in seq:
        if isinstance(item, str):
            macropad.keyboard_layout.write(item)
        elif isinstance(item, int):
            macropad.keyboard.press(item)
    macropad.keyboard.release_all()

# --- Startup ---
load_profile(current_profile)

while True:
    now = time.monotonic()
    key_event = macropad.keys.events.get()
    macropad.encoder_switch_debounced.update()
    new_position = macropad.encoder

    # --- Exit profile menu after timeout ---
    if profile_menu and now - profile_last_action > 60:
        profile_menu = False
        load_profile(current_profile)

    # --- Handle encoder press (long: menu, short: shortcut trigger) ---
    if macropad.encoder_switch_debounced.pressed and encoder_pressed_time is None:
        encoder_pressed_time = now

    if macropad.encoder_switch_debounced.released:
        held = now - encoder_pressed_time if encoder_pressed_time else 0
        encoder_pressed_time = None

        if held > 1:
            profile_menu = not profile_menu
            shortcut_index = 0
            if profile_menu:
                macropad.display.rotation = 0
                display_message("Profile Menu", "Rotate to select")
            else:
                load_profile(current_profile)
            profile_last_action = now
        elif not profile_menu and not profiles[current_profile].get("volume", True):
            shortcuts = profiles[current_profile]["shortcuts"]
            if shortcut_index < len(shortcuts):
                process_sequence(shortcuts[shortcut_index])

    # --- Rotate encoder to change volume or select shortcut/profile ---
    if new_position != encoder_last_position:
        profile = profiles[current_profile]
        if profile_menu:
            if new_position > encoder_last_position:
                current_profile = (current_profile + 1) % len(profiles)
            else:
                current_profile = (current_profile - 1) % len(profiles)
            encoder_last_position = new_position
            display_message("Profile Menu", profiles[current_profile]["display_name"])
            profile_last_action = now

        elif not profile.get("volume", True):
            if new_position > encoder_last_position:
                shortcut_index = (shortcut_index + 1) % len(profile["shortcuts"])
            else:
                shortcut_index = (shortcut_index - 1) % len(profile["shortcuts"])
            encoder_last_position = new_position
            display_message(profile["display_name"], f"Option {shortcut_index + 1}")
        else:
            if new_position > encoder_last_position:
                macropad.consumer_control.send(macropad.ConsumerControlCode.VOLUME_INCREMENT)
            else:
                macropad.consumer_control.send(macropad.ConsumerControlCode.VOLUME_DECREMENT)
            encoder_last_position = new_position

    # --- Handle key events + tones ---
    if key_event and not profile_menu and profiles[current_profile].get("keys"):
        key = key_event.key_number
        if key_event.pressed:
            if key in profiles[current_profile]["keys"]:
                macropad.keyboard.press(profiles[current_profile]["keys"][key])
                if key < len(tones):
                    macropad.pixels[key] = colorwheel(int(255 / 12) * key)
                    macropad.start_tone(tones[key])
        elif key_event.released:
            macropad.keyboard.release_all()
            macropad.pixels.fill((0, 0, 0))
            macropad.stop_tone()
4556645
