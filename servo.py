from time import sleep

from gpiozero import Servo


# Standard three-wire servo:
# Brown  -> GND
# Red    -> 5V power
# Yellow -> BCM GPIO 2 (physical pin 3)
SERVO_PIN = 2
MOVE_DELAY = 1


servo = Servo(
    SERVO_PIN,
    min_pulse_width=0.5 / 1000,
    max_pulse_width=2.5 / 1000,
)

print("Sweeping servo on GPIO 2.")
print("Press Ctrl+C to stop.")

try:
    while True:
        servo.min()
        sleep(MOVE_DELAY)

        servo.mid()
        sleep(MOVE_DELAY)

        servo.max()
        sleep(MOVE_DELAY)

        servo.mid()
        sleep(MOVE_DELAY)

except KeyboardInterrupt:
    print("\nStopping.")

finally:
    servo.detach()
