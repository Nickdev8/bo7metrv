from time import sleep

from gpiozero import Servo


# Standard three-wire servo:
# Brown  -> GND
# Red    -> 5V power
# Yellow -> BCM GPIO 2 (physical pin 3)
SERVO_PIN = 2
MOVE_TIME = 2
STEPS = 100


servo = Servo(
    SERVO_PIN,
    min_pulse_width=0.5 / 1000,
    max_pulse_width=2.5 / 1000,
)

def move_servo(start_angle, end_angle):
    for step in range(STEPS + 1):
        progress = step / STEPS
        angle = start_angle + (end_angle - start_angle) * progress
        servo.value = angle / 90
        sleep(MOVE_TIME / STEPS)


print("Moving servo between -90 and +90 degrees.")
print("Each movement takes 2 seconds.")
print("Press Ctrl+C to stop.")

try:
    while True:
        move_servo(-90, 90)
        move_servo(90, -90)

except KeyboardInterrupt:
    print("\nStopping.")

finally:
    servo.detach()
