import time
import board
import adafruit_nunchuk
import usb_hid
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode
from adafruit_hid.mouse import Mouse

# I2C and Nunchuk
i2c = board.I2C()
nc = adafruit_nunchuk.Nunchuk(i2c)

# HID setup
kbd = Keyboard(usb_hid.devices)
mouse = Mouse(usb_hid.devices)

# State
air_mouse_mode = False
last_mode_toggle = 0
mode_hold_time = 1.0  # seconds
button_c_pressed = False
button_z_pressed = False

# Config
deadzone = 10
mouse_sensitivity = 0.15  # lower = slower

def handle_keyboard_mode(x, y, c, z):
    # Arrow keys
    if x < 128 - 40:
        kbd.press(Keycode.LEFT_ARROW)
    else:
        kbd.release(Keycode.LEFT_ARROW)

    if x > 128 + 40:
        kbd.press(Keycode.RIGHT_ARROW)
    else:
        kbd.release(Keycode.RIGHT_ARROW)

    if y < 128 - 40:
        kbd.press(Keycode.DOWN_ARROW)
    else:
        kbd.release(Keycode.DOWN_ARROW)

    if y > 128 + 40:
        kbd.press(Keycode.UP_ARROW)
    else:
        kbd.release(Keycode.UP_ARROW)

    # Buttons
    if c:
        kbd.press(Keycode.B)
    else:
        kbd.release(Keycode.B)

    if z:
        kbd.press(Keycode.A)
    else:
        kbd.release(Keycode.A)

def handle_mouse_mode(x, y, c, z):
    # Convert joystick to mouse
    dx = (x - 128)
    dy = (y - 128) * -1  # invert Y

    # Apply deadzone
    if abs(dx) < deadzone:
        dx = 0
    if abs(dy) < deadzone:
        dy = 0

    # Apply sensitivity
    dx = int(dx * mouse_sensitivity)
    dy = int(dy * mouse_sensitivity)

    if dx != 0 or dy != 0:
        mouse.move(dx, dy)

    # Buttons (reversed!)
    if z:
        mouse.press(Mouse.RIGHT_BUTTON)  # Z = right click
    else:
        mouse.release(Mouse.RIGHT_BUTTON)

    if c:
        mouse.press(Mouse.LEFT_BUTTON)   # C = left click
    else:
        mouse.release(Mouse.LEFT_BUTTON)

while True:
    x, y = nc.joystick
    c = nc.buttons.C
    z = nc.buttons.Z
    now = time.monotonic()

    # Detect long-press both buttons
    if c and z:
        if not (button_c_pressed and button_z_pressed):
            last_mode_toggle = now
        button_c_pressed = True
        button_z_pressed = True
    else:
        if button_c_pressed and button_z_pressed:
            held_time = now - last_mode_toggle
            if held_time >= mode_hold_time:
                air_mouse_mode = not air_mouse_mode
                print("Air mouse mode:", air_mouse_mode)
                kbd.release_all()
                mouse.release_all()
                time.sleep(0.3)  # debounce
        button_c_pressed = False
        button_z_pressed = False

    # Don’t trigger keys/buttons during dual-button hold
    if c and z:
        pass
    else:
        if air_mouse_mode:
            handle_mouse_mode(x, y, c, z)
        else:
            handle_keyboard_mode(x, y, c, z)

    time.sleep(0.01)
