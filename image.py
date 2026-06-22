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
    pygame.K_1: "1.jpeg",
    pygame.K_2: "2.jpeg",
    pygame.K_3: "3.jpeg",
    pygame.K_4: "4.jpeg",
}

TERMINAL_IMAGE_FILES = {
    "1": "1.jpeg",
    "2": "2.jpeg",
    "3": "3.jpeg",
    "4": "4.jpeg",
}


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


class ImageViewer:
    def __init__(self):
        try:
            pygame.init()
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
            pygame.display.set_caption("Image Viewer")
            pygame.mouse.set_visible(False)

            self.screen_width, self.screen_height = self.screen.get_size()
            self.current_image = None
            self.current_position = None
            self.load_image("1.jpeg")

            if self.current_image is None:
                raise RuntimeError("Could not load the default image.")
        except Exception:
            pygame.quit()
            raise

    def load_image(self, image_path):
        loaded_image, loaded_position = load_image_for_screen(
            image_path,
            self.screen_width,
            self.screen_height,
        )

        if loaded_image is None:
            return

        self.current_image = loaded_image
        self.current_position = loaded_position

    def update(self, terminal_key=None):
        if terminal_key in ("q", "\x1b"):
            return False

        if terminal_key in TERMINAL_IMAGE_FILES:
            self.load_image(TERMINAL_IMAGE_FILES[terminal_key])

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False

                if event.key in IMAGE_FILES:
                    self.load_image(IMAGE_FILES[event.key])

        self.screen.fill((0, 0, 0))
        self.screen.blit(self.current_image, self.current_position)
        pygame.display.flip()

        return True

    def close(self):
        pygame.mouse.set_visible(True)
        pygame.quit()


def main():
    original_terminal_settings = None
    if sys.stdin.isatty():
        original_terminal_settings = termios.tcgetattr(sys.stdin)
        tty.setcbreak(sys.stdin)

    viewer = None
    clock = pygame.time.Clock()

    try:
        viewer = ImageViewer()

        print("Press 1-4 in this terminal to change images. Press q to quit.")

        while True:
            terminal_key = read_terminal_key()
            if not viewer.update(terminal_key):
                break

            clock.tick(60)

    except KeyboardInterrupt:
        pass

    finally:
        if original_terminal_settings is not None:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, original_terminal_settings)
        if viewer is not None:
            viewer.close()


if __name__ == "__main__":
    main()
