import pygame
import random

COLOR_WALL = (255, 80, 180)  # pink


class Wall:
    def __init__(self, x, y, size):
        self.rect = pygame.Rect(x, y, size, size)

    def draw(self, surface):
        pygame.draw.rect(surface, COLOR_WALL, self.rect)


def generate_walls(count, width, height, min_size=20, max_size=80):
    walls = []

    for _ in range(count):
        size = random.randint(min_size, max_size)

        x = random.randint(0, width - size)
        y = random.randint(0, height - size)

        walls.append(Wall(x, y, size))

    return walls