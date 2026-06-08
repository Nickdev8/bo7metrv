from gpiozero import LED
from signal import pause


# Extra LEDs
EXTRA_LED_PINS = [25, 8, 7, 1]

extra_leds = [LED(pin) for pin in EXTRA_LED_PINS]


print("Turning LEDs on:")
print("GPIO 25, GPIO 8, GPIO 7, GPIO 1")
print("Press Ctrl+C to stop.")

for led in extra_leds:
    led.on()

try:
    pause()

except KeyboardInterrupt:
    print("\nStopping.")

finally:
    for led in extra_leds:
        led.off()