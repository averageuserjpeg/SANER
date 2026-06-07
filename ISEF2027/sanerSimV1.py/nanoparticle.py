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

        # Particle size
        self.radius = 4
        self.half = self.radius

        self.mass = 1.0
        self.max_speed = 5.0
        self.drag = 0.98

    def get_rect(self):
        return pygame.Rect(
            int(self.x - self.radius),
            int(self.y - self.radius),
            self.radius * 2,
            self.radius * 2
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

    def apply_motion_substepped(
        self,
        vascular,
        screen_to_world,
        world_to_screen
    ):
        steps = 2

        for _ in range(steps):

            self.vx *= self.drag
            self.vy *= self.drag

            speed_sq = self.vx * self.vx + self.vy * self.vy
            max_sq = self.max_speed * self.max_speed

            if speed_sq > max_sq:
                scale = self.max_speed / math.sqrt(speed_sq)
                self.vx *= scale
                self.vy *= scale

            # Move
            self.x += self.vx / steps
            self.y += self.vy / steps

            self._resolve_world_bounds()

            # Vascular constraint
            result = vascular.constrain_particle(
                self,
                screen_to_world
            )

            if result is not None:
                sx, sy = world_to_screen(
                    float(result[0]),
                    float(result[1])
                )

                self.x = float(sx)
                self.y = float(sy)

    def _resolve_world_bounds(self):

        if self.x - self.radius < 0:
            self.x = self.radius
            self.vx *= -0.5

        elif self.x + self.radius > WIDTH:
            self.x = WIDTH - self.radius
            self.vx *= -0.5

        if self.y - self.radius < 0:
            self.y = self.radius
            self.vy *= -0.5

        elif self.y + self.radius > HEIGHT:
            self.y = HEIGHT - self.radius
            self.vy *= -0.5

    def draw(self, surface):

        # Main particle
        pygame.draw.circle(
            surface,
            COLOR_PARTICLE,
            (int(self.x), int(self.y)),
            self.radius
        )

        # Tiny highlight for depth
        pygame.draw.circle(
            surface,
            (220, 255, 220),
            (
                int(self.x - self.radius * 0.3),
                int(self.y - self.radius * 0.3)
            ),
            max(1, self.radius // 3)
        )