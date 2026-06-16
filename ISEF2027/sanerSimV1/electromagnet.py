import pygame
import numpy as np

COLOR_OFF = (160, 160, 185)
COLOR_BORDER = (40, 40, 40)

MIN_BLUE = np.array([80, 120, 160], dtype=float)
MAX_BLUE = np.array([124, 184, 255], dtype=float)


class Electromagnet:
    def __init__(self, x, y, size=60):
        self.center = np.array([float(x), float(y)])
        self.size = size

        self.is_active = False

        # Strength should be between 0.0 and 1.0
        self.strength = 0.0
        self.decay = 0.92
        

    def rect(self):
        return pygame.Rect(
            int(self.center[0] - self.size / 2),
            int(self.center[1] - self.size / 2),
            self.size,
            self.size
        )

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if self.rect().collidepoint(event.pos):
                    self.is_active = not self.is_active

                    # manual toggle for testing
                    self.strength = 1.0 if self.is_active else 0.0

    def draw(self, surface):
        rect = self.rect()

        s = max(0.0, min(1.0, self.strength))

        if s > 0:
            color = (
                int(160 - 40 * s),
                int(160 + 24 * s),
                int(185 + 70 * s)
            )
        else:
            color = COLOR_OFF

        pygame.draw.rect(surface, color, rect)
        pygame.draw.rect(surface, COLOR_BORDER, rect, 2)

        # decay every frame
        self.strength *= self.decay