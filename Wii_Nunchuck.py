import time
import board
import adafruit_nunchuk
import usb_hid
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode
from adafruit_hid.mouse import Mouse

# Setup I2C and Nunchuk
i2c = board.I2C()
nc = adafruit_nunchuk.Nunchuk(i2c)

# HID devices
kbd = Keyboard(usb_hid.devices)
mouse = Mouse(usb_hid.devices)

# Modes
MODE_KEYBOARD = 0
MODE_JOYSTICK_MOUSE = 1
MODE_ACCEL_MOUSE = 2
mode = MODE_KEYBOARD

# Shake detection
shake_threshold = 60          # Raise if still too sensitive
shake_window = 3              # Require 3 strong changes
shake_debounce = 1.5          # Seconds between allowed shakes
last_shake_check = 0
shake_history = [0] * shake_window
prev_ay = 0

# Long-press detection for joystick mouse toggle
last_mode_toggle = 0
mode_hold_time = 1.0
button_c_pressed = False
button_z_pressed = False

# Movement settings
deadzone = 10
joystick_sensitivity = 0.15

# Tilt config 
tilt_center_x = 500
tilt_center_y = 500
tilt_deadzone = 15
tilt_scale = 0.15  # Raise if movement is too slow

def handle_keyboard_mode(x, y, c, z):
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

    # Buttons: Z = A, C = B
    if c:
        kbd.press(Keycode.B)
    else:
        kbd.release(Keycode.B)

    if z:
        kbd.press(Keycode.A)
    else:
        kbd.release(Keycode.A)

def handle_joystick_mouse_mode(x, y, c, z):
    dx = (x - 128)
    dy = (y - 128)

    if abs(dx) < deadzone:
        dx = 0
    if abs(dy) < deadzone:
        dy = 0

    dx = int(dx * joystick_sensitivity)
    dy = int(dy * -joystick_sensitivity)  

    if dx or dy:
        mouse.move(dx, dy)

    # Mouse buttons: Z = right click, C = left click
    if z:
        mouse.press(Mouse.RIGHT_BUTTON)
    else:
        mouse.release(Mouse.RIGHT_BUTTON)

    if c:
        mouse.press(Mouse.LEFT_BUTTON)
    else:
        mouse.release(Mouse.LEFT_BUTTON)

def handle_accel_mouse_mode(ax, ay, az, c, z):
    dx = ax - tilt_center_x
    dy = ay - tilt_center_y

    if abs(dx) < tilt_deadzone:
        dx = 0
    if abs(dy) < tilt_deadzone:
        dy = 0

    dx = int(dx * tilt_scale)
    dy = int(dy * tilt_scale)

    if dx != 0 or dy != 0:
        mouse.move(dx, dy)

    if z:
        mouse.press(Mouse.RIGHT_BUTTON)
    else:
        mouse.release(Mouse.RIGHT_BUTTON)

    if c:
        mouse.press(Mouse.LEFT_BUTTON)
    else:
        mouse.release(Mouse.LEFT_BUTTON)

while True:
    x, y = nc.joystick
    ax, ay, az = nc.acceleration
    c = nc.buttons.C
    z = nc.buttons.Z
    now = time.monotonic()

    # --- Shake detection ---
    delta_ay = abs(ay - prev_ay)
    prev_ay = ay
    shake_history.pop(0)
    shake_history.append(delta_ay)
    strong_shakes = sum(1 for d in shake_history if d > shake_threshold)

    if strong_shakes >= shake_window and (now - last_shake_check) > shake_debounce:
        last_shake_check = now
        if mode != MODE_ACCEL_MOUSE:
            mode = MODE_ACCEL_MOUSE
            print("Switched to ACCEL MOUSE mode (tilt)")
        else:
            mode = MODE_KEYBOARD
            print("Returned to KEYBOARD mode")
        kbd.release_all()
        mouse.release_all()
        time.sleep(0.3)

    # --- Button combo for joystick mouse toggle ---
    if c and z:
        if not (button_c_pressed and button_z_pressed):
            last_mode_toggle = now
        button_c_pressed = True
        button_z_pressed = True
    else:
        if button_c_pressed and button_z_pressed:
            if now - last_mode_toggle >= mode_hold_time:
                if mode == MODE_JOYSTICK_MOUSE:
                    mode = MODE_KEYBOARD
                    print("Returned to KEYBOARD mode")
                else:
                    mode = MODE_JOYSTICK_MOUSE
                    print("Switched to JOYSTICK MOUSE mode")
                kbd.release_all()
                mouse.release_all()
                time.sleep(0.3)
        button_c_pressed = False
        button_z_pressed = False

    # Skip all inputs during mode switching combo
    if c and z:
        pass
    else:
        if mode == MODE_KEYBOARD:
            handle_keyboard_mode(x, y, c, z)
        elif mode == MODE_JOYSTICK_MOUSE:
            handle_joystick_mouse_mode(x, y, c, z)
        elif mode == MODE_ACCEL_MOUSE:
            handle_accel_mouse_mode(ax, ay, az, c, z)

    time.sleep(0.01)
