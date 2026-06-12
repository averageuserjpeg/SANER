import pygame
import numpy as np

COLOR_ON = (124, 184, 230)
COLOR_OFF = (160, 160, 185)   
COLOR_BORDER = (40, 40, 40)   # grey grid lines


class Electromagnet:
    def __init__(self, x, y, size=60):
        self.center = np.array([float(x), float(y)])
        self.size = size
        self.is_active = False

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

    def draw(self, surface):

        rect = self.rect()

        # fill
        color = COLOR_ON if self.is_active else COLOR_OFF
        pygame.draw.rect(surface, color, rect)

        # border (this is what makes grid look "snapped")
        pygame.draw.rect(surface, COLOR_BORDER, rect, 2)