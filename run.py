import sys
import termios
import time
import tty

import adafruit_tcs34725
from adafruit_extended_bus import ExtendedI2C
from gpiozero import Button, LED, Servo

from image import ImageViewer, read_terminal_key


# dtoverlay=i2c-gpio,bus=3,i2c_gpio_sda=14,i2c_gpio_scl=15
I2C_BUS = 3

SENSOR_LED_PIN = 18
TOGGLE_SERVO_BUTTON_PIN = 23
TOGGLE_LEDS_BUTTON_PIN = 24
SERVO_PIN = 2
SERVO_POSITION_TIME = 2

#[25, 8, 7, 1, 12, 16]

COLOR_LED_PINS = {
    "blue": 25,
    "orange": 8,
    "yellow": 7,
    "magenta": 1,
    "pink": 12,
    # "x": 16,
}

TERMINAL_COLOR_HEX = {
    "blue": "#0000FF",
    "orange": "#FFA500",
    "yellow": "#FFFF00",
    "magenta": "#FF00FF",
    "pink": "#FF69B4",
    "none": "#808080",
}

CALIBRATION_COLORS = [
    ((100, 255, 160), "blue"),
    ((255, 160, 200), "magenta"),
    ((255, 255, 80), "yellow"),
    ((255, 105, 80), "orange"),
    ((255, 80, 80), "pink"),
]

MAX_COLOR_DISTANCE = 100
MINIMUM_BOOSTED_BRIGHTNESS = 80
READ_DELAY = 0.1
IMAGE_RETRY_DELAY = 5
SENSOR_RETRY_DELAY = 5


sensor_led = LED(SENSOR_LED_PIN)
servo = Servo(
    SERVO_PIN,
    min_pulse_width=1 / 1000,
    max_pulse_width=2 / 1000,
)
color_leds = {
    color: LED(pin)
    for color, pin in COLOR_LED_PINS.items()
}

toggle_servo_button = Button(
    TOGGLE_SERVO_BUTTON_PIN,
    pull_up=True,
    bounce_time=0.2,
)
toggle_leds_button = Button(
    TOGGLE_LEDS_BUTTON_PIN,
    pull_up=True,
    bounce_time=0.2,
)

running = True
leds_enabled = True
servo_running = True
servo_at_maximum = False
last_servo_move = time.monotonic()


def brighten_rgb(red, green, blue):
    max_value = max(red, green, blue)

    if max_value == 0:
        return 0, 0, 0

    scale = 255 / max_value
    boosted = [
        int(value * scale)
        for value in (red, green, blue)
    ]

    return tuple(
        min(
            max(value, MINIMUM_BOOSTED_BRIGHTNESS if value > 0 else 0),
            255,
        )
        for value in boosted
    )


def detect_color(red, green, blue):
    closest_rgb, closest_color = min(
        CALIBRATION_COLORS,
        key=lambda calibration: color_distance(
            (red, green, blue),
            calibration[0],
        ),
    )
    distance = color_distance((red, green, blue), closest_rgb)

    if MAX_COLOR_DISTANCE is not None and distance > MAX_COLOR_DISTANCE:
        return None, distance

    return closest_color, distance


def color_distance(first, second):
    return sum(
        (first_value - second_value) ** 2
        for first_value, second_value in zip(first, second)
    ) ** 0.5


def validate_calibration_colors():
    if not CALIBRATION_COLORS:
        raise ValueError("CALIBRATION_COLORS must contain at least one color.")

    unknown_colors = {
        color
        for _, color in CALIBRATION_COLORS
        if color not in COLOR_LED_PINS
    }
    if unknown_colors:
        names = ", ".join(sorted(unknown_colors))
        raise ValueError(f"No LED pin configured for: {names}")

    missing_terminal_colors = set(COLOR_LED_PINS) - set(TERMINAL_COLOR_HEX)
    if missing_terminal_colors:
        names = ", ".join(sorted(missing_terminal_colors))
        raise ValueError(f"No terminal color configured for: {names}")


def terminal_color_name(color, width=0):
    hex_color = TERMINAL_COLOR_HEX[color].lstrip("#")
    red = int(hex_color[0:2], 16)
    green = int(hex_color[2:4], 16)
    blue = int(hex_color[4:6], 16)
    text = f"{color:{width}s}"

    return f"\033[38;2;{red};{green};{blue}m{text}\033[0m"


def show_color(color):
    for name, led in color_leds.items():
        if leds_enabled and name == color:
            led.on()
        else:
            led.off()


def toggle_servo():
    global last_servo_move
    global servo_at_maximum
    global servo_running

    servo_running = not servo_running
    if servo_running:
        servo_at_maximum = False
        last_servo_move = time.monotonic()
        servo.min()
        print("\nServo enabled.")
    else:
        servo.detach()
        print("\nServo disabled.")


def toggle_leds():
    global leds_enabled

    leds_enabled = not leds_enabled
    if leds_enabled:
        sensor_led.on()
        print("\nLEDs enabled.")
    else:
        sensor_led.off()
        show_color(None)
        print("\nLEDs disabled.")


def update_servo():
    global last_servo_move
    global servo_at_maximum

    if not servo_running:
        return

    now = time.monotonic()
    if now - last_servo_move < SERVO_POSITION_TIME:
        return

    servo_at_maximum = not servo_at_maximum
    if servo_at_maximum:
        servo.max()
    else:
        servo.min()

    last_servo_move = now


def start_sensor():
    try:
        i2c = ExtendedI2C(I2C_BUS)
        color_sensor = adafruit_tcs34725.TCS34725(i2c)
        color_sensor.integration_time = 154
        color_sensor.gain = 16
        print("\nColor sensor ready.")
        return color_sensor
    except Exception as error:
        print(f"\nColor sensor not ready: {error}")
        return None


def start_image_viewer():
    try:
        return ImageViewer()
    except Exception as error:
        print(f"\nImage viewer not ready: {error}")
        return None


toggle_servo_button.when_pressed = toggle_servo
toggle_leds_button.when_pressed = toggle_leds
sensor_led.on()
servo.min()
validate_calibration_colors()

original_terminal_settings = None
if sys.stdin.isatty():
    original_terminal_settings = termios.tcgetattr(sys.stdin)
    tty.setcbreak(sys.stdin)

image_viewer = start_image_viewer()
next_image_retry = time.monotonic() + IMAGE_RETRY_DELAY
sensor = start_sensor()
next_sensor_retry = time.monotonic() + SENSOR_RETRY_DELAY

print("Image viewer, color sensor, LEDs, and servo started.")
print("LED mapping:")
for color_name, pin in COLOR_LED_PINS.items():
    print(f"  {terminal_color_name(color_name, 7)} -> GPIO {pin}")
print("GPIO 23 toggles the servo.")
print("GPIO 24 toggles the sensor LED and color LEDs.")
print("Press Ctrl+C to stop the program.")
print("Servo on GPIO 2 changes position every 2 seconds.")
print("Press 1-4 in this terminal to change images. Press q to quit.")

try:
    while running:
        update_servo()

        terminal_key = read_terminal_key()
        if image_viewer is None:
            now = time.monotonic()
            if now >= next_image_retry:
                image_viewer = start_image_viewer()
                next_image_retry = now + IMAGE_RETRY_DELAY
        elif not image_viewer.update(terminal_key):
            running = False
            break

        if sensor is None:
            now = time.monotonic()
            if now >= next_sensor_retry:
                sensor = start_sensor()
                next_sensor_retry = now + SENSOR_RETRY_DELAY
        else:
            try:
                raw_red, raw_green, raw_blue = sensor.color_rgb_bytes
                red, green, blue = brighten_rgb(raw_red, raw_green, raw_blue)
                detected_color, distance = detect_color(red, green, blue)
                show_color(detected_color)

                color_name = detected_color if detected_color else "none"
                color_text = terminal_color_name(color_name, 7)
                print(
                    f"RAW: ({raw_red:3d}, {raw_green:3d}, {raw_blue:3d})  "
                    f"BOOSTED: ({red:3d}, {green:3d}, {blue:3d}) "
                    f"-> {color_text} (distance: {distance:5.1f})",
                    end="\r",
                    flush=True,
                )
            except Exception as error:
                print(f"\nColor sensor read failed: {error}")
                sensor = None
                show_color(None)

        time.sleep(READ_DELAY)

except KeyboardInterrupt:
    pass

finally:
    if original_terminal_settings is not None:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, original_terminal_settings)
    if image_viewer is not None:
        image_viewer.close()
    sensor_led.off()
    show_color(None)
    servo.detach()
    print("\nStopped.")
