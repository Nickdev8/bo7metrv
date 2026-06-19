import sys
import termios
import time
import tty

from gpiozero import Button, Servo

from image import ImageViewer, read_terminal_key


PREVIOUS_BUTTON_PIN = 23
NEXT_BUTTON_PIN = 24
SERVO_PIN = 2

READ_DELAY = 0.05
IMAGE_RETRY_DELAY = 5

IMAGE_STEPS = [
    ("image-1.jpg", -90, -1.0),
    ("furkan-test.jpg", -45, -0.5),
    ("image-3.jpg", 0, 0.0),
    ("image-4.jpg", 45, 0.5),
    ("image-5.jpg", 90, 1.0),
]


running = True
current_step = 0


def start_button(name, pin, callback):
    try:
        button = Button(
            pin,
            pull_up=True,
            bounce_time=0.2,
        )
        button.when_pressed = callback
        return button
    except Exception as error:
        print(f"{name} button on GPIO {pin} not ready: {error}")
        return None


def start_servo():
    try:
        return Servo(
            SERVO_PIN,
            min_pulse_width=1 / 1000,
            max_pulse_width=2 / 1000,
        )
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

    current_step = step % len(IMAGE_STEPS)
    image_file, degrees, servo_value = IMAGE_STEPS[current_step]

    if image_viewer is not None:
        image_viewer.load_image(image_file)

    if servo is not None:
        servo.value = servo_value

    print(
        f"Image {current_step + 1}/{len(IMAGE_STEPS)}: {image_file} "
        f"| servo {degrees:+d} degrees",
        flush=True,
    )


def next_step(image_viewer, servo):
    set_step(current_step + 1, image_viewer, servo)


def previous_step(image_viewer, servo):
    set_step(current_step - 1, image_viewer, servo)


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
        lambda: previous_step(image_viewer, servo),
    )
    next_button = start_button(
        "Next",
        NEXT_BUTTON_PIN,
        lambda: next_step(image_viewer, servo),
    )

    try:
        print("bo7metrv image controller started.")
        print(f"GPIO {PREVIOUS_BUTTON_PIN}: previous image")
        print(f"GPIO {NEXT_BUTTON_PIN}: next image")
        print("Terminal controls: n/Space = next, p = previous, q = quit")

        while running:
            if image_viewer is None:
                now = time.monotonic()
                if now >= next_image_retry:
                    image_viewer = start_image_viewer()
                    next_image_retry = now + IMAGE_RETRY_DELAY
                    if image_viewer is not None:
                        set_step(current_step, image_viewer, servo)
            else:
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
