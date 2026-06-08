import time
import adafruit_tcs34725
from adafruit_extended_bus import ExtendedI2C


# Software I2C bus 3 from:
# dtoverlay=i2c-gpio,bus=3,i2c_gpio_sda=14,i2c_gpio_scl=15
i2c = ExtendedI2C(3)

sensor = adafruit_tcs34725.TCS34725(i2c)

sensor.integration_time = 50
sensor.gain = 4


def color_block(r, g, b):
    """
    Prints a true-color ANSI background block.
    Works in most modern terminals.
    """
    return f"\033[48;2;{r};{g};{b}m          \033[0m"


def rgb_to_hex(r, g, b):
    return f"#{r:02X}{g:02X}{b:02X}"


print("TCS34725 color sensor started.")
print("Showing reconstructed color in terminal.")
print("Press Ctrl+C to stop.")
print()

try:
    while True:
        r, g, b = sensor.color_rgb_bytes
        lux = sensor.lux
        color_temperature = sensor.color_temperature

        hex_color = rgb_to_hex(r, g, b)
        block = color_block(r, g, b)

        print(
            f"{block}  "
            f"RGB: {r:3d}, {g:3d}, {b:3d}  "
            f"HEX: {hex_color}  "
            f"Lux: {lux:8.2f}  "
            f"Temp: {color_temperature:5.0f}K",
            end="\r",
            flush=True
        )

        time.sleep(0.1)

except KeyboardInterrupt:
    print("\nStopped.")