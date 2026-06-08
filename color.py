import time
import signal
import sys

import adafruit_tcs34725
from adafruit_extended_bus import ExtendedI2C
from gpiozero import Button, LED


# I2C sensor bus
# dtoverlay=i2c-gpio,bus=3,i2c_gpio_sda=14,i2c_gpio_scl=15
i2c = ExtendedI2C(3)
sensor = adafruit_tcs34725.TCS34725(i2c)

# More sensitive sensor settings
sensor.integration_time = 154
sensor.gain = 16


# GPIO pins
SENSOR_LED_PIN = 18
TOGGLE_LED_BUTTON_PIN = 23
EXIT_BUTTON_PIN = 24


sensor_led = LED(SENSOR_LED_PIN)

toggle_led_button = Button(
    TOGGLE_LED_BUTTON_PIN,
    pull_up=True,
    bounce_time=0.2
)

exit_button = Button(
    EXIT_BUTTON_PIN,
    pull_up=True,
    bounce_time=0.2
)


sensor_led_on = True
running = True

sensor_led.on()


def color_block(r, g, b):
    return f"\033[48;2;{r};{g};{b}m          \033[0m"


def rgb_to_hex(r, g, b):
    return f"#{r:02X}{g:02X}{b:02X}"


def brighten_rgb(r, g, b, minimum_brightness=80):
    max_value = max(r, g, b)

    if max_value == 0:
        return 0, 0, 0

    scale = 255 / max_value

    r = int(r * scale)
    g = int(g * scale)
    b = int(b * scale)

    r = max(r, minimum_brightness if r > 0 else 0)
    g = max(g, minimum_brightness if g > 0 else 0)
    b = max(b, minimum_brightness if b > 0 else 0)

    return min(r, 255), min(g, 255), min(b, 255)


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


def cleanup_and_exit():
    sensor_led.off()
    print("\nStopped.")
    sys.exit(0)


toggle_led_button.when_pressed = toggle_sensor_led
exit_button.when_pressed = stop_program


print("TCS34725 color sensor started.")
print("GPIO 23 button toggles the sensor LED.")
print("GPIO 24 button exits the script.")
print("Press Ctrl+C to stop.")
print()

try:
    while running:
        raw_r, raw_g, raw_b = sensor.color_rgb_bytes

        lux = sensor.lux
        color_temperature = sensor.color_temperature

        bright_r, bright_g, bright_b = brighten_rgb(raw_r, raw_g, raw_b)

        raw_hex = rgb_to_hex(raw_r, raw_g, raw_b)
        bright_hex = rgb_to_hex(bright_r, bright_g, bright_b)

        raw_block = color_block(raw_r, raw_g, raw_b)
        bright_block = color_block(bright_r, bright_g, bright_b)

        lux_text = f"{lux:8.2f}" if lux is not None else "   n/a  "
        temp_text = f"{color_temperature:5.0f}K" if color_temperature is not None else " n/a "

        led_text = "ON " if sensor_led_on else "OFF"

        print(
            f"LED: {led_text}  |  "
            f"RAW {raw_block} RGB: {raw_r:3d}, {raw_g:3d}, {raw_b:3d} {raw_hex}  |  "
            f"BOOSTED {bright_block} RGB: {bright_r:3d}, {bright_g:3d}, {bright_b:3d} {bright_hex}  |  "
            f"Lux: {lux_text}  "
            f"Temp: {temp_text}",
            end="\r",
            flush=True
        )

        time.sleep(0.1)

except KeyboardInterrupt:
    pass

finally:
    cleanup_and_exit()