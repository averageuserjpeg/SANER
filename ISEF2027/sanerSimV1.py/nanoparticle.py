import pygame
import random
import math

WIDTH = 1000
HEIGHT = 700

COLOR_PARTICLE = (50, 230, 80)


class Nanoparticle:
    def __init__(self, x, y):

        # --- POSITION ---
        self.x = float(x)
        self.y = float(y)

        # --- VELOCITY ---
        self.vx = random.uniform(-0.5, 0.5)
        self.vy = random.uniform(-0.5, 0.5)

        # --- BOX HITBOX (AABB) ---
        self.size = 8
        self.half = self.size / 2

        self.mass = 1.0
        self.max_speed = 5.0
        self.drag = 0.98

    # --- RECT GETTER ---
    def get_rect(self):
        return pygame.Rect(
            int(self.x - self.half),
            int(self.y - self.half),
            self.size,
            self.size
        )

    # --- MULTI MAGNET PHYSICS ---
    def update_multi_physics(self, magnets, walls):

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

                inv = 1.0 / dist
                dx *= inv
                dy *= inv

                effective_dist = max(dist, 50.0)

                magnetic_intensity = 75.0 / (effective_dist ** 1.1)

                total_fx += dx * magnetic_intensity
                total_fy += dy * magnetic_intensity

        self.vx += total_fx / self.mass
        self.vy += total_fy / self.mass

        self._apply_motion_substepped(walls)

    # --- MOTION ---
    def _apply_motion_substepped(self, walls):

        steps = 4

        for _ in range(steps):

            # drag
            self.vx *= self.drag
            self.vy *= self.drag

            # clamp speed
            speed_sq = self.vx * self.vx + self.vy * self.vy
            max_sq = self.max_speed * self.max_speed

            if speed_sq > max_sq:
                scale = self.max_speed / math.sqrt(speed_sq)
                self.vx *= scale
                self.vy *= scale

            self.x += self.vx / steps
            self.y += self.vy / steps

            self._resolve_world_bounds()
            self._resolve_wall_list(walls)

    # --- WORLD BOUNDS ---
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

    # --- WALL LIST ---
    def _resolve_wall_list(self, walls):
        my_rect = self.get_rect()

        for w in walls:
            if my_rect.colliderect(w):
                self._resolve_wall_collision(w)

    # --- RECT COLLISION RESOLVE ---
    def _resolve_wall_collision(self, rect):

        my_rect = self.get_rect()

        dx_left = rect.right - my_rect.left
        dx_right = my_rect.right - rect.left
        dy_top = rect.bottom - my_rect.top
        dy_bottom = my_rect.bottom - rect.top

        # find smallest overlap axis
        min_dx = dx_left if abs(dx_left) < abs(dx_right) else -dx_right
        min_dy = dy_top if abs(dy_top) < abs(dy_bottom) else -dy_bottom

        if abs(min_dx) < abs(min_dy):
            self.x += min_dx
            self.vx *= -0.5
        else:
            self.y += min_dy
            self.vy *= -0.5

    # --- DRAW ---
    def draw(self, surface):

        pygame.draw.rect(
            surface,
            COLOR_PARTICLE,
            self.get_rect()
        )