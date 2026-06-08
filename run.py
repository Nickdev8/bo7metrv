import pygame
import sys
from pathlib import Path


IMAGE_FILES = {
    pygame.K_1: "image-1.jpg",
    pygame.K_2: "image-2.jpg",
    pygame.K_3: "image-3.jpg",
    pygame.K_4: "image-4.jpg",
}


def quit_now():
    pygame.quit()
    sys.exit(0)


def load_scaled_image(image_path, screen_width, screen_height):
    image_file = Path(image_path)

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


def main():
    pygame.init()

    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    pygame.display.set_caption("Image Viewer")

    screen_width, screen_height = screen.get_size()

    current_image, current_position = load_scaled_image(
        "image-1.jpg",
        screen_width,
        screen_height
    )

    if current_image is None:
        quit_now()

    clock = pygame.time.Clock()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit_now()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    quit_now()

                if event.key in IMAGE_FILES:
                    loaded_image, loaded_position = load_scaled_image(
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


if __name__ == "__main__":
    main()