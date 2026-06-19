import sys
import termios
import threading
import time
import tty

from gpiozero import AngularServo, Button

try:
    from gpiozero.pins.pigpio import PiGPIOFactory
except ImportError:
    PiGPIOFactory = None

from image import ImageViewer, read_terminal_key


PREVIOUS_BUTTON_PIN = 14
NEXT_BUTTON_PIN = 15
SERVO_PIN = 18

READ_DELAY = 0.05
IMAGE_RETRY_DELAY = 5
SERVO_SETTLE_TIME = 0.7
SERVO_MIN_PULSE_WIDTH = 0.4 / 1000
SERVO_MAX_PULSE_WIDTH = 2.6 / 1000
SERVO_FRAME_WIDTH = 20 / 1000

IMAGE_STEPS = [
    ("image-1.jpg", -80),
    ("furkan-test.jpg", -40),
    ("furkan-test.jpg", 0),
    ("furkan-test.jpg", 40),
    ("furkan-test.jpg", 80),
]


running = True
current_step = 0
pending_step_delta = 0
pending_step_lock = threading.Lock()
last_servo_move = None


def start_button(name, pin, callback):
    try:
        button = Button(
            pin,
            pull_up=False,
            bounce_time=0.2,
        )
        button.when_pressed = callback
        return button
    except Exception as error:
        print(f"{name} button on GPIO {pin} not ready: {error}")
        return None


def start_servo():
    try:
        pin_factory = None
        if PiGPIOFactory is not None:
            try:
                pin_factory = PiGPIOFactory()
            except Exception as error:
                print(f"pigpio timing unavailable, using default GPIO timing: {error}")

        servo = AngularServo(
            SERVO_PIN,
            min_angle=-90,
            max_angle=90,
            min_pulse_width=SERVO_MIN_PULSE_WIDTH,
            max_pulse_width=SERVO_MAX_PULSE_WIDTH,
            frame_width=SERVO_FRAME_WIDTH,
            pin_factory=pin_factory,
        )
        print("Servo using pigpio timing." if pin_factory else "Servo using default GPIO timing.")
        return servo
    except Exception as error:
        print(f"Servo on GPIO {SERVO_PIN} not ready: {error}")
        return None


def start_image_viewer():
    try:
        return ImageViewer()
    except Exception as error:
        print(f"Image viewer not ready: {error}")
        return None


def set_step(step, image_viewer, servo):
    global current_step
    global last_servo_move

    current_step = step % len(IMAGE_STEPS)
    image_file, degrees = IMAGE_STEPS[current_step]

    if image_viewer is not None:
        image_viewer.load_image(image_file)

    if servo is not None:
        servo.angle = degrees
        last_servo_move = time.monotonic()

    print(
        f"Image {current_step + 1}/{len(IMAGE_STEPS)}: {image_file} "
        f"| servo {degrees:+d} degrees",
        flush=True,
    )


def next_step(image_viewer, servo):
    set_step(current_step + 1, image_viewer, servo)


def previous_step(image_viewer, servo):
    set_step(current_step - 1, image_viewer, servo)


def queue_step(delta):
    global pending_step_delta

    with pending_step_lock:
        pending_step_delta += delta


def take_pending_step_delta():
    global pending_step_delta

    with pending_step_lock:
        delta = pending_step_delta
        pending_step_delta = 0

    return delta


def update_servo_hold(servo):
    global last_servo_move

    if servo is None or last_servo_move is None:
        return

    if time.monotonic() - last_servo_move >= SERVO_SETTLE_TIME:
        servo.detach()
        last_servo_move = None


def main():
    global running

    original_terminal_settings = None
    if sys.stdin.isatty():
        original_terminal_settings = termios.tcgetattr(sys.stdin)
        tty.setcbreak(sys.stdin)

    image_viewer = None
    next_image_retry = time.monotonic()
    servo = start_servo()

    previous_button = start_button(
        "Previous",
        PREVIOUS_BUTTON_PIN,
        lambda: queue_step(-1),
    )
    next_button = start_button(
        "Next",
        NEXT_BUTTON_PIN,
        lambda: queue_step(1),
    )

    try:
        print("bo7metrv image controller started.")
        print(f"GPIO {PREVIOUS_BUTTON_PIN}: previous image")
        print(f"GPIO {NEXT_BUTTON_PIN}: next image")
        print("Terminal controls: n/Space = next, p = previous, q = quit")

        while running:
            update_servo_hold(servo)

            if image_viewer is None:
                now = time.monotonic()
                if now >= next_image_retry:
                    image_viewer = start_image_viewer()
                    next_image_retry = now + IMAGE_RETRY_DELAY
                    if image_viewer is not None:
                        set_step(current_step, image_viewer, servo)
            else:
                step_delta = take_pending_step_delta()
                if step_delta:
                    set_step(current_step + step_delta, image_viewer, servo)

                terminal_key = read_terminal_key()
                if terminal_key == "q":
                    break
                if terminal_key in ("n", " ", "d"):
                    next_step(image_viewer, servo)
                elif terminal_key in ("p", "a"):
                    previous_step(image_viewer, servo)

                if not image_viewer.update(None):
                    break

            time.sleep(READ_DELAY)

    except KeyboardInterrupt:
        pass

    finally:
        if original_terminal_settings is not None:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, original_terminal_settings)
        if image_viewer is not None:
            image_viewer.close()
        if servo is not None:
            servo.detach()
        if previous_button is not None:
            previous_button.close()
        if next_button is not None:
            next_button.close()
        print("\nStopped.")


if __name__ == "__main__":
    main()
