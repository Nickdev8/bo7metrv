import time
import adafruit_tcs34725
from adafruit_extended_bus import ExtendedI2C


i2c = ExtendedI2C(3)
sensor = adafruit_tcs34725.TCS34725(i2c)

# More sensitive settings
sensor.integration_time = 154
sensor.gain = 16


def color_block(r, g, b):
    return f"\033[48;2;{r};{g};{b}m          \033[0m"


def rgb_to_hex(r, g, b):
    return f"#{r:02X}{g:02X}{b:02X}"


def brighten_rgb(r, g, b, minimum_brightness=80):
    max_value = max(r, g, b)

    if max_value == 0:
        return 0, 0, 0

    # Scale strongest channel up to 255
    scale = 255 / max_value

    r = int(r * scale)
    g = int(g * scale)
    b = int(b * scale)

    # Optional minimum brightness boost
    # This prevents very dark colors from looking almost black
    r = max(r, minimum_brightness if r > 0 else 0)
    g = max(g, minimum_brightness if g > 0 else 0)
    b = max(b, minimum_brightness if b > 0 else 0)

    return min(r, 255), min(g, 255), min(b, 255)


print("TCS34725 color sensor started.")
print("Showing boosted reconstructed color.")
print("Press Ctrl+C to stop.")
print()

try:
    while True:
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

        print(
            f"RAW {raw_block} RGB: {raw_r:3d}, {raw_g:3d}, {raw_b:3d} {raw_hex}  |  "
            f"BOOSTED {bright_block} RGB: {bright_r:3d}, {bright_g:3d}, {bright_b:3d} {bright_hex}  |  "
            f"Lux: {lux_text}  "
            f"Temp: {temp_text}",
            end="\r",
            flush=True
        )

        time.sleep(0.1)

except KeyboardInterrupt:
    print("\nStopped.")