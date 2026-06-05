import pygame
import random
import math

COLOR_PARTICLE = (50, 230, 80)
WIDTH, HEIGHT = 1000, 700


class Nanoparticle:
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.vx = random.uniform(-0.5, 0.5)
        self.vy = random.uniform(-0.5, 0.5)
        self.size = 5
        self.half = self.size / 2
        self.mass = 1.0
        self.max_speed = 5.0
        self.drag = 0.98

    def get_rect(self):
        return pygame.Rect(
            int(self.x - self.half),
            int(self.y - self.half),
            self.size,
            self.size
        )

    def update_multi_physics(self, magnets, vascular):
        total_fx = 0.0
        total_fy = 0.0

        for m in magnets:
            if not m.is_active:
                continue

            dx = m.center[0] - self.x
            dy = m.center[1] - self.y
            dist_sq = dx * dx + dy * dy

            if dist_sq > 25:
                dist = math.sqrt(dist_sq)
                inv = 1.0 / (dist + 1e-9)
                dx *= inv
                dy *= inv

                effective_dist = max(dist, 50.0)
                magnetic_intensity = 75.0 / (effective_dist ** 1.1)

                total_fx += dx * magnetic_intensity
                total_fy += dy * magnetic_intensity

        self.vx += total_fx / self.mass
        self.vy += total_fy / self.mass

    def apply_motion_substepped(self, vascular, screen_to_world, world_to_screen):
        steps = 2  # 🔥 reduced from 4

        for _ in range(steps):
            self.vx *= self.drag
            self.vy *= self.drag

            speed_sq = self.vx * self.vx + self.vy * self.vy
            max_sq = self.max_speed * self.max_speed

            if speed_sq > max_sq:
                scale = self.max_speed / math.sqrt(speed_sq)
                self.vx *= scale
                self.vy *= scale

            # movement
            self.x += self.vx / steps
            self.y += self.vy / steps

            self._resolve_world_bounds()

            # vascular constraint (optimized)
            result = vascular.constrain_particle(self, screen_to_world)
            if result is not None:
                sx, sy = world_to_screen(float(result[0]), float(result[1]))
                self.x = float(sx)
                self.y = float(sy)

    def _resolve_world_bounds(self):
        if self.x - self.half < 0:
            self.x = self.half
            self.vx *= -0.5
        elif self.x + self.half > WIDTH:
            self.x = WIDTH - self.half
            self.vx *= -0.5

        if self.y - self.half < 0:
            self.y = self.half
            self.vy *= -0.5
        elif self.y + self.half > HEIGHT:
            self.y = HEIGHT - self.half
            self.vy *= -0.5

    def draw(self, surface):
        pygame.draw.rect(surface, COLOR_PARTICLE, self.get_rect())