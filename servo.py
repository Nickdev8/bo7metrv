from time import sleep

from gpiozero import Servo


# Standard three-wire servo:
# Brown  -> GND
# Red    -> 5V power
# Yellow -> BCM GPIO 2 (physical pin 3)
SERVO_PIN = 2
POSITION_TIME = 2


servo = Servo(
    SERVO_PIN,
    min_pulse_width=1 / 1000,
    max_pulse_width=2 / 1000,
)


print("Moving servo between -90 and +90 degrees.")
print("Holding each position for 2 seconds.")
print("Press Ctrl+C to stop.")

try:
    while True:
        servo.min()
        sleep(POSITION_TIME)

        servo.max()
        sleep(POSITION_TIME)

except KeyboardInterrupt:
    print("\nStopping.")

finally:
    servo.detach()
