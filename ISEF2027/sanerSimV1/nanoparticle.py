import pygame
import random
import math

COLOR_PARTICLE = (191, 255, 0)
WIDTH, HEIGHT = 1000, 700


class Nanoparticle:
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)

        self.vx = random.uniform(-0.5, 0.5)
        self.vy = random.uniform(-0.5, 0.5)

        # Particle size
        self.radius = 2
        self.half = self.radius

        self.mass = 1.0
        self.max_speed = 4.0
        self.drag = 0.90
        self.in_zone = False

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

        if self.in_zone:
            return

        for m in magnets:

            # convert magnet center to world-space field point
            mx, my = m.center[0], m.center[1]

            dx = mx - self.x
            dy = my - self.y
            dist_sq = dx * dx + dy * dy

            if dist_sq < 1e-6:
                continue

            dist = math.sqrt(dist_sq)

            # normalize direction
            nx = dx / dist
            ny = dy / dist

            # -------------------------------
            # FIELD STRENGTH (NEW CORE CHANGE)
            # -------------------------------
            strength = getattr(m, "strength", 0.0)

            if strength <= 0.0:
                continue

            # distance falloff (smooth gradient field)
            falloff_radius = 140.0
            falloff = max(0.0, 1.0 - dist / falloff_radius)

            # sharper center pull
            falloff = falloff * falloff

            # final force
            magnetic_intensity = strength * falloff * 18.0

            # dampen extreme proximity jitter
            if dist < 25.0:
                magnetic_intensity *= dist / 25.0

            total_fx += nx * magnetic_intensity
            total_fy += ny * magnetic_intensity

        # apply force
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

            # Keep track of old position before moving
            old_x = self.x
            old_y = self.y

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

                # Calculate the wall normal vector based on displacement
                dx = sx - old_x
                dy = sy - old_y
                dist = math.hypot(dx, dy)
                
                if dist > 1e-6:
                    nx = dx / dist
                    ny = dy / dist
                    
                    # Reflect velocity slightly or cancel out the velocity into the wall
                    dot_product = self.vx * nx + self.vy * ny
                    if dot_product > 0:
                        # Emphasize bounce factor (-1.2 for a clean bounce, -1.0 for perfect slide)
                        self.vx -= dot_product * nx * 1.2
                        self.vy -= dot_product * ny * 1.2

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