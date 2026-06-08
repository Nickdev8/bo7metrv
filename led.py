from gpiozero import Button, LED


# GPIO pins
SENSOR_LED_PIN = 18
TOGGLE_LED_BUTTON_PIN = 23
EXIT_BUTTON_PIN = 24

# Extra LEDs
EXTRA_LED_PINS = [25, 8, 7, 1]


sensor_led = LED(SENSOR_LED_PIN)
extra_leds = [LED(pin) for pin in EXTRA_LED_PINS]

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

# Turn all extra LEDs on
for led in extra_leds:
    led.on()