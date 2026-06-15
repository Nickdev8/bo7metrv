import colorsys
import time

import adafruit_tcs34725
from adafruit_extended_bus import ExtendedI2C
from gpiozero import Button, LED


# I2C sensor bus:
# dtoverlay=i2c-gpio,bus=3,i2c_gpio_sda=14,i2c_gpio_scl=15
I2C_BUS = 3

SENSOR_LED_PIN = 18
TOGGLE_SENSOR_LED_BUTTON_PIN = 23
EXIT_BUTTON_PIN = 24

COLOR_LED_PINS = {
    "red": 25,
    "yellow": 8,
    "green": 7,
    "cyan": 1,
    "blue": 12,
    "magenta": 16,
}

MIN_BRIGHTNESS = 20
MIN_SATURATION = 0.20
READ_DELAY = 0.1


i2c = ExtendedI2C(I2C_BUS)
sensor = adafruit_tcs34725.TCS34725(i2c)
sensor.integration_time = 154
sensor.gain = 16

sensor_led = LED(SENSOR_LED_PIN)
color_leds = {
    color: LED(pin)
    for color, pin in COLOR_LED_PINS.items()
}

toggle_sensor_led_button = Button(
    TOGGLE_SENSOR_LED_BUTTON_PIN,
    pull_up=True,
    bounce_time=0.2,
)
exit_button = Button(
    EXIT_BUTTON_PIN,
    pull_up=True,
    bounce_time=0.2,
)

sensor_led_on = True
running = True


def detect_color(red, green, blue):
    brightness = max(red, green, blue)
    if brightness < MIN_BRIGHTNESS:
        return None

    hue, saturation, _ = colorsys.rgb_to_hsv(
        red / 255,
        green / 255,
        blue / 255,
    )

    if saturation < MIN_SATURATION:
        return None

    hue_degrees = hue * 360

    if hue_degrees < 30 or hue_degrees >= 330:
        return "red"
    if hue_degrees < 90:
        return "yellow"
    if hue_degrees < 150:
        return "green"
    if hue_degrees < 210:
        return "cyan"
    if hue_degrees < 270:
        return "blue"
    return "magenta"


def show_color(color):
    for name, led in color_leds.items():
        if name == color:
            led.on()
        else:
            led.off()


def toggle_sensor_led():
    global sensor_led_on

    sensor_led_on = not sensor_led_on
    if sensor_led_on:
        sensor_led.on()
    else:
        sensor_led.off()


def stop_program():
    global running
    running = False


toggle_sensor_led_button.when_pressed = toggle_sensor_led
exit_button.when_pressed = stop_program
sensor_led.on()

print("Color sensor and LEDs started.")
print("LED mapping:")
for color_name, pin in COLOR_LED_PINS.items():
    print(f"  {color_name:7s} -> GPIO {pin}")
print("GPIO 23 toggles the sensor LED.")
print("GPIO 24 or Ctrl+C stops the program.")

last_color = object()

try:
    while running:
        red, green, blue = sensor.color_rgb_bytes
        detected_color = detect_color(red, green, blue)
        show_color(detected_color)

        if detected_color != last_color:
            color_text = detected_color if detected_color else "none"
            print(
                f"RGB: {red:3d}, {green:3d}, {blue:3d} -> {color_text}"
            )
            last_color = detected_color

        time.sleep(READ_DELAY)

except KeyboardInterrupt:
    pass

finally:
    sensor_led.off()
    show_color(None)
    print("Stopped.")
