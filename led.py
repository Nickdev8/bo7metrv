from gpiozero import LED
from time import sleep


# Extra LEDs
EXTRA_LED_PINS = [25, 8, 7, 1, 12, 16]
STEP_DELAY = 0.5

extra_leds = [LED(pin) for pin in EXTRA_LED_PINS]


print("Cycling through LEDs one by one:")
print(", ".join(f"GPIO {pin}" for pin in EXTRA_LED_PINS))
print("Press Ctrl+C to stop.")

try:
    while True:
        for led in extra_leds:
            led.on()
            sleep(STEP_DELAY)
            led.off()

except KeyboardInterrupt:
    print("\nStopping.")

finally:
    for led in extra_leds:
        led.off()
