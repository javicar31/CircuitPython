# === Required Libraries ===
import time
import digitalio
import board
import usb_hid
import neopixel
from adafruit_hid.consumer_control import ConsumerControl
from adafruit_hid.consumer_control_code import ConsumerControlCode

# === NeoPixel Setup ===
pixel_pin = board.A0
num_pixels = 7
pixels = neopixel.NeoPixel(
    pixel_pin, num_pixels, brightness=0.3,
    auto_write=False, pixel_order=neopixel.GRBW
)

# Define colors for feedback
RED    = (255, 0, 0, 0)
ORANGE = (255, 127, 0, 0)
YELLOW = (255, 255, 0, 0)
GREEN  = (0, 255, 0, 0)
CYAN   = (0, 255, 255, 0)
BLUE   = (0, 0, 255, 0)
BLACK  = (0, 0, 0, 0)

COLOR_MAP = [RED, ORANGE, YELLOW, GREEN, CYAN, BLUE]  # Per button color
BRIGHTNESS_MODE_COLORS = [
    RED, ORANGE, YELLOW, GREEN, CYAN, BLUE,
    (255, 0, 255, 0),     # Magenta
    (127, 0, 255, 0),     # Purple
    (255, 192, 203, 0),   # Pink
    (255, 255, 255, 0),   # White
]

# === Button Setup ===
# List your physical button pins
button_pins = [board.A1, board.A2, board.A3, board.SCK, board.MISO, board.MOSI]

# Assign each button a media function
# Order matches the pins list above
buttonkeys = [
    ConsumerControlCode.REWIND,          # A1
    ConsumerControlCode.MUTE,            # A2
    ConsumerControlCode.VOLUME_DECREMENT, # A3
    ConsumerControlCode.FAST_FORWARD,    # SCK
    ConsumerControlCode.VOLUME_INCREMENT, # MISO
    ConsumerControlCode.PLAY_PAUSE       # MOSI
]

# Initialize buttons as input with pull-ups
buttons = []
for pin in button_pins:
    button = digitalio.DigitalInOut(pin)
    button.direction = digitalio.Direction.INPUT
    button.pull = digitalio.Pull.UP
    buttons.append(button)

# === HID Control Setup ===
cc = ConsumerControl(usb_hid.devices)

# === LED and Brightness State ===
led_enabled = True
last_color = BLACK
brightness = 0.3
in_brightness_mode = False
brightness_mode_color_index = 0

# Track timing for long/short presses
press_start_times = [None] * len(buttons)
long_press_flags = [False] * len(buttons)

# === LED Behavior Functions ===
def apply_led_state():
    """Update NeoPixel display based on LED state."""
    if led_enabled:
        pixels.brightness = brightness
        pixels.fill(last_color)
    else:
        pixels.fill(BLACK)
    pixels.show()

def flash_leds(times=10, speed=0.1):
    """Flash LEDs to indicate mode change."""
    for _ in range(times):
        pixels.fill((255, 255, 255, 0))  # Flash white
        pixels.show()
        time.sleep(speed)
        pixels.fill(BLACK)
        pixels.show()
        time.sleep(speed)

# === Main Program Loop ===
print("Ready! Hold Volume+ and Volume– for 5s to enter brightness mode.")

while True:
    now = time.monotonic()

    # --- Brightness Mode Activation ---
    if not buttons[2].value and not buttons[4].value and not in_brightness_mode:
        press_start = now
        while not buttons[2].value and not buttons[4].value:
            if time.monotonic() - press_start > 5.0:
                in_brightness_mode = True
                print("Entered brightness mode")
                flash_leds()
                break
            time.sleep(0.01)

    # --- Brightness Mode Loop ---
    while in_brightness_mode:
        vol_up = not buttons[4].value  # MISO
        vol_down = not buttons[2].value  # A3
        ffw = not buttons[3].value  # SCK
        rew = not buttons[0].value  # A1

        if vol_up:
            brightness = min(1.0, brightness + 0.25)
            print(f"Brightness increased: {brightness:.2f}")
            apply_led_state()
            time.sleep(0.3)

        elif vol_down:
            brightness = max(0.01, brightness - 0.25)
            print(f"Brightness decreased: {brightness:.2f}")
            apply_led_state()
            time.sleep(0.3)

        if ffw:
            # Next color
            brightness_mode_color_index = (brightness_mode_color_index + 1) % len(BRIGHTNESS_MODE_COLORS)
            last_color = BRIGHTNESS_MODE_COLORS[brightness_mode_color_index]
            print(f"Color forward: {last_color}")
            apply_led_state()
            while not buttons[3].value:
                time.sleep(0.01)

        if rew:
            # Previous color
            brightness_mode_color_index = (brightness_mode_color_index - 1) % len(BRIGHTNESS_MODE_COLORS)
            last_color = BRIGHTNESS_MODE_COLORS[brightness_mode_color_index]
            print(f"Color backward: {last_color}")
            apply_led_state()
            while not buttons[0].value:
                time.sleep(0.01)

        # Exit brightness mode
        if vol_up or vol_down:
            hold_start = time.monotonic()
            while not buttons[2].value or not buttons[4].value:
                if time.monotonic() - hold_start > 2.0:
                    in_brightness_mode = False
                    print("Exited brightness mode")
                    flash_leds()
                    break
                time.sleep(0.01)

        time.sleep(0.01)

    # --- Main Button Handling ---
    for i, button in enumerate(buttons):
        pressed = not button.value

        if pressed:
            if press_start_times[i] is None:
                press_start_times[i] = now

            # Check for long press
            press_duration = now - press_start_times[i]
            if press_duration > 1.0 and not long_press_flags[i]:
                long_press_flags[i] = True

                # Long press actions: toggle LED on select buttons
                if i in (0, 3):  # A1 and SCK
                    led_enabled = not led_enabled
                    print(f"[Button {i}] Long press → LED {'ON' if led_enabled else 'OFF'}")
                    apply_led_state()

                elif i in (1, 5):
                    print(f"[Button {i}] Long press → (placeholder for future feature)")

        else:
            # On release, handle short press if no long press occurred
            if press_start_times[i] is not None:
                if not long_press_flags[i]:
                    cc.send(buttonkeys[i])
                    print(f"[Button {i}] Short press → Sent {buttonkeys[i]}")
                    last_color = COLOR_MAP[i % len(COLOR_MAP)]
                    apply_led_state()

                # Reset state
                press_start_times[i] = None
                long_press_flags[i] = False

    time.sleep(0.01)
