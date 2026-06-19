import os
import select
import sys
import termios
import tty
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

# Use the local HDMI display even when launched from an SSH shell.
os.environ["DISPLAY"] = os.environ.get("IMAGE_DISPLAY", ":0")
os.environ["SDL_VIDEO_FULLSCREEN_DISPLAY"] = os.environ.get(
    "IMAGE_FULLSCREEN_DISPLAY",
    "0",
)

xauthority_file = Path.home() / ".Xauthority"
if "XAUTHORITY" not in os.environ and xauthority_file.exists():
    os.environ["XAUTHORITY"] = str(xauthority_file)

import pygame


IMAGE_FILES = {
    pygame.K_1: "image-1.jpg",
    pygame.K_2: "furkan-test.jpg",
    pygame.K_3: "image-3.jpg",
    pygame.K_4: "image-4.jpg",
}

TERMINAL_IMAGE_FILES = {
    "1": "image-1.jpg",
    "2": "furkan-test.jpg",
    "3": "image-3.jpg",
    "4": "image-4.jpg",
}


def quit_now():
    pygame.quit()
    sys.exit(0)


def load_scaled_image(image_path, screen_width, screen_height):
    image_file = BASE_DIR / image_path

    if not image_file.exists():
        print(f"Image not found: {image_file}")
        return None, None

    image = pygame.image.load(str(image_file)).convert()

    img_width, img_height = image.get_size()
    scale = min(screen_width / img_width, screen_height / img_height)

    new_width = int(img_width * scale)
    new_height = int(img_height * scale)

    image = pygame.transform.smoothscale(image, (new_width, new_height))

    x = (screen_width - new_width) // 2
    y = (screen_height - new_height) // 2

    return image, (x, y)


def read_terminal_key():
    if not sys.stdin.isatty():
        return None

    readable, _, _ = select.select([sys.stdin], [], [], 0)
    if not readable:
        return None

    return sys.stdin.read(1).lower()


def load_image_for_screen(image_path, screen_width, screen_height):
    return load_scaled_image(image_path, screen_width, screen_height)


def main():
    original_terminal_settings = None
    if sys.stdin.isatty():
        original_terminal_settings = termios.tcgetattr(sys.stdin)
        tty.setcbreak(sys.stdin)

    pygame.init()

    try:
        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        pygame.display.set_caption("Image Viewer")
        pygame.mouse.set_visible(False)

        screen_width, screen_height = screen.get_size()

        current_image, current_position = load_image_for_screen(
            "image-1.jpg",
            screen_width,
            screen_height
        )

        if current_image is None:
            quit_now()

        print("Press 1-4 in this terminal to change images. Press q to quit.")
        clock = pygame.time.Clock()

        while True:
            terminal_key = read_terminal_key()
            if terminal_key in ("q", "\x1b"):
                quit_now()

            if terminal_key in TERMINAL_IMAGE_FILES:
                loaded_image, loaded_position = load_image_for_screen(
                    TERMINAL_IMAGE_FILES[terminal_key],
                    screen_width,
                    screen_height
                )

                if loaded_image is not None:
                    current_image = loaded_image
                    current_position = loaded_position

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    quit_now()

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        quit_now()

                    if event.key in IMAGE_FILES:
                        loaded_image, loaded_position = load_image_for_screen(
                            IMAGE_FILES[event.key],
                            screen_width,
                            screen_height
                        )

                        if loaded_image is not None:
                            current_image = loaded_image
                            current_position = loaded_position

            screen.fill((0, 0, 0))
            screen.blit(current_image, current_position)
            pygame.display.flip()

            clock.tick(60)

    except KeyboardInterrupt:
        pass

    finally:
        if original_terminal_settings is not None:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, original_terminal_settings)
        pygame.mouse.set_visible(True)
        pygame.quit()


if __name__ == "__main__":
    main()
