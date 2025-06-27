import time
import board
import touchio
import neopixel
from rainbowio import colorwheel
import usb_hid # Required for HID devices
from adafruit_hid.mouse import Mouse 

# --- Mouse Setup ---
mouse = Mouse(usb_hid.devices)

# --- Existing CircuitPython Code ---
touch1 = touchio.TouchIn(board.TOUCH1)  # Touch 1 for brightness control
touch2 = touchio.TouchIn(board.TOUCH2)  # Touch 2 for color cycling

pixels = neopixel.NeoPixel(board.NEOPIXEL, 4, auto_write=False)

# Define time thresholds
SHORT_PRESS_THRESHOLD = 0.15  # Max time for a short press
LONG_PRESS_THRESHOLD = 1.0    # Time for long press
TOUCH_DEBOUNCE = 0.3  # Time to wait before detecting another touch

touched = time.monotonic()
last_touch1 = False
last_touch2 = False
color_index = 0  # Start with color index 0
colors = [
    (255, 0, 0),  # Red
    (0, 255, 0),  # Green
    (0, 0, 255),  # Blue
    (255, 255, 0),  # Yellow
    (0, 255, 255),  # Cyan
    (255, 0, 255),  # Magenta
    (255, 255, 255)  # White
]

# Initialize with low brightness
pixels.brightness = 0.1
pixels.show()

# Global time for rainbow effect
last_rainbow_update = time.monotonic()
rainbow_speed = 0.2  # Controls the speed of the rainbow effect
rainbow_delay = 0.05  # Delay between rainbow updates to prevent overloading

# --- Mouse Click Control Variables ---
last_click_time = time.monotonic()
min_click_delay = 0.05 # Fastest possible click rate
max_click_delay = 2.0  # Slowest possible click rate

def rainbow_effect():
    """Continuous rainbow effect that cycles through colors."""
    global last_rainbow_update
    current_time = time.monotonic()
    
    # Ensure rainbow updates at a controlled speed
    if current_time - last_rainbow_update >= rainbow_delay:
        color_index = int((current_time * rainbow_speed) % 256)
        for i in range(4):
            pixels[i] = colorwheel(color_index + (i * 64) % 256)  # Spread the colors across the pixels
        pixels.show()
        last_rainbow_update = current_time

while True:
    current_time = time.monotonic()
    time_since_touch = current_time - touched

    # Handle long press to adjust brightness (on touch1 or touch2)
    # The 'start_time' variable needs to be initialized if a long press is detected.
    # We'll initialize it when the touch first begins.
    if touch1.value and not last_touch1:
        touched = current_time  # Start the touch
        last_touch1 = True
        start_time = current_time # Initialize start_time for the current press

    if touch2.value and not last_touch2:
        touched = current_time  # Start the touch
        last_touch2 = True
        start_time = current_time # Initialize start_time for the current press

    # If a long press is detected on touch1 or touch2, adjust brightness
    # Ensure start_time is defined for the current touch
    if last_touch1 and (current_time - start_time) > LONG_PRESS_THRESHOLD:
        # Long press on touch1 for increasing brightness
        pixels.brightness = min(1.0, pixels.brightness + 0.01)  # Gradual increase for finer control
        pixels.show()

    elif last_touch2 and (current_time - start_time) > LONG_PRESS_THRESHOLD:
        # Long press on touch2 for decreasing brightness
        pixels.brightness = max(0.0, pixels.brightness - 0.01)  # Gradual decrease for finer control
        pixels.show()

    # Handle color cycling based on release (release the button to trigger color change)
    if not touch1.value and last_touch1:
        # Short press released: trigger the color change (cycle forward)
        color_index = (color_index + 1) % (len(colors) + 1)  # Cycle through colors and rainbow
        last_touch1 = False
        touched = current_time

    if not touch2.value and last_touch2:
        # Short press released: trigger the color change (cycle backward)
        color_index = (color_index - 1) % (len(colors) + 1)  # Cycle backward through colors and rainbow
        last_touch2 = False
        touched = current_time

    # Show color or rainbow effect
    if color_index < len(colors):  # Normal colors
        pixels.fill(colors[color_index])  # Set to the selected color
    else:  # Rainbow effect
        rainbow_effect()  # Call the rainbow effect function
    
    pixels.show()

    # Reset touch states if touch ends
    if not touch1.value:
        last_touch1 = False
    if not touch2.value:
        last_touch2 = False

    # --- Mouse Click Logic ---
    # Calculate click delay based on brightness
    # Invert brightness so higher brightness means lower delay (faster clicks)
    # Map brightness (0.0 to 1.0) to click delay (max_click_delay to min_click_delay)
    current_click_delay = max_click_delay - (pixels.brightness * (max_click_delay - min_click_delay))
    current_click_delay = max(min_click_delay, min(max_click_delay, current_click_delay)) # Ensure it stays within bounds

    if current_time - last_click_time >= current_click_delay:
        mouse.click(Mouse.LEFT_BUTTON) # Perform a left click at the current cursor position
        last_click_time = current_time

    # Small delay to prevent excessive CPU usage
    time.sleep(0.01)
