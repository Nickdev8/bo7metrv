import pygame
import sys
from pathlib import Path


IMAGE_PATH = "image.jpg"  # change this to your image file


def quit_now():
    pygame.quit()
    sys.exit(0)


def main():
    image_file = Path(IMAGE_PATH)

    if not image_file.exists():
        print(f"Image not found: {image_file}")
        sys.exit(1)

    pygame.init()

    # Fullscreen display
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    pygame.display.set_caption("Image Viewer")

    screen_width, screen_height = screen.get_size()

    # Load image
    image = pygame.image.load(str(image_file)).convert()

    # Scale image to fit screen while keeping aspect ratio
    img_width, img_height = image.get_size()
    scale = min(screen_width / img_width, screen_height / img_height)

    new_width = int(img_width * scale)
    new_height = int(img_height * scale)

    image = pygame.transform.smoothscale(image, (new_width, new_height))

    x = (screen_width - new_width) // 2
    y = (screen_height - new_height) // 2

    clock = pygame.time.Clock()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit_now()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    quit_now()

        screen.fill((0, 0, 0))
        screen.blit(image, (x, y))
        pygame.display.flip()

        clock.tick(60)


if __name__ == "__main__":
    main()