import smbus
import time
import sys


I2C_BUS = 3
TCS34725_ADDRESS = 0x29

COMMAND_BIT = 0x80

REG_ENABLE = 0x00
REG_ATIME = 0x01
REG_CONTROL = 0x0F
REG_STATUS = 0x13
REG_CDATAL = 0x14

ENABLE_PON = 0x01
ENABLE_AEN = 0x02


def write_register(bus, register, value):
    bus.write_byte_data(
        TCS34725_ADDRESS,
        COMMAND_BIT | register,
        value
    )


def read_register(bus, register):
    return bus.read_byte_data(
        TCS34725_ADDRESS,
        COMMAND_BIT | register
    )


def read_word(bus, register):
    low = read_register(bus, register)
    high = read_register(bus, register + 1)
    return low | (high << 8)


def setup_sensor(bus):
    # Power on
    write_register(bus, REG_ENABLE, ENABLE_PON)
    time.sleep(0.01)

    # Enable RGBC sensor
    write_register(bus, REG_ENABLE, ENABLE_PON | ENABLE_AEN)

    # Integration time
    # 0xEB is about 50 ms
    # Lower value = longer integration = more sensitive
    write_register(bus, REG_ATIME, 0xEB)

    # Gain
    # 0x00 = 1x
    # 0x01 = 4x
    # 0x02 = 16x
    # 0x03 = 60x
    write_register(bus, REG_CONTROL, 0x01)


def read_color(bus):
    status = read_register(bus, REG_STATUS)

    # Bit 0 means valid color data available
    if not status & 0x01:
        return None

    clear = read_word(bus, REG_CDATAL)
    red = read_word(bus, REG_CDATAL + 2)
    green = read_word(bus, REG_CDATAL + 4)
    blue = read_word(bus, REG_CDATAL + 6)

    return clear, red, green, blue


def main():
    try:
        bus = smbus.SMBus(I2C_BUS)
    except FileNotFoundError:
        print(f"I2C bus {I2C_BUS} not found.")
        print("Check that dtoverlay=i2c-gpio,bus=3,i2c_gpio_sda=14,i2c_gpio_scl=15 is in /boot/config.txt")
        sys.exit(1)

    try:
        setup_sensor(bus)
        print("TCS34725 color sensor started.")
        print("Press Ctrl+C to stop.")
        print()

        while True:
            color = read_color(bus)

            if color is None:
                print("Waiting for valid color data...", end="\r")
            else:
                clear, red, green, blue = color

                if clear > 0:
                    red_percent = red / clear * 100
                    green_percent = green / clear * 100
                    blue_percent = blue / clear * 100
                else:
                    red_percent = green_percent = blue_percent = 0

                print(
                    f"CLEAR: {clear:5d} | "
                    f"RED: {red:5d} | "
                    f"GREEN: {green:5d} | "
                    f"BLUE: {blue:5d} | "
                    f"R%: {red_percent:5.1f} | "
                    f"G%: {green_percent:5.1f} | "
                    f"B%: {blue_percent:5.1f}",
                    end="\r"
                )

            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\nStopped.")

    finally:
        bus.close()


if __name__ == "__main__":
    main()