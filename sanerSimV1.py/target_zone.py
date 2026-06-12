import pygame
import random

class TargetZone:
    def __init__(self, vascular_system, world_to_screen_func, size=120, alpha=80):
        """
        Spawns a semi-transparent green box centered on a random point 
        along the vascular system network.
        
        :param vascular_system: Instance of the VascularSystem
        :param world_to_screen_func: The world_to_screen helper from main.py
        :param size: Width and height of the target box in pixels
        :param alpha: Transparency level (0 = invisible, 255 = fully opaque)
        """
        self.size = size
        self.alpha = alpha
        self.color = (0, 255, 100) # Vibrant green
        
        # 1. Get a random coordinate along the generated blood vessels
        wx, wy = vascular_system.get_random_vessel_point()
        
        # 2. Convert world coordinates to pixel coordinates
        self.cx, self.cy = world_to_screen_func(wx, wy)
        
        # 3. Define the bounding rectangle parameters
        self.rect_x = self.cx - (self.size // 2)
        self.rect_y = self.cy - (self.size // 2)

    def draw(self, screen):
        """Renders the semi-transparent box onto the Pygame surface."""
        # Pygame requires an independent Surface layer to render transparency (Alpha)
        surface = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        
        # Draw the filled box onto the temporary surface
        surface.fill((*self.color, self.alpha))
        
        # Optional: Draw a solid border to give the zone structure
        pygame.draw.rect(surface, self.color, (0, 0, self.size, self.size), 2)
        
        # Blit the temporary alpha surface onto the main window screen
        screen.blit(surface, (self.rect_x, self.rect_y))