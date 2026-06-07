import numpy as np
import random
import pygame
import math

# =========================================================
# CONFIG
# =========================================================

W, H = 10, 10
STEPS = 1200
STEP_SIZE = 0.088

FIELD_INFLUENCE = 0.20
ANGLE_INFLUENCE = 0.25
NOISE = 0.13
REPEL_RADIUS = 2.0
REPEL_FORCE = 0.70
JITTER = 0.10

NEIGHBOR_ATTRACT = 0.60
NEIGHBOR_RADIUS = 5.0

ANAST_RADIUS = 0.22
ANAST_IMMUNITY = 40

MAX_GENERATION = 2
BASE_BRANCH = 0.045
BRANCH_DECAY = 0.008

SCREEN_SIZE = 1000
VESSEL_RADIUS = 0.18

# =========================================================
# TIP SYSTEM
# =========================================================

vessel_counter = 0

class Tip:
    def __init__(self, x, y, angle, generation=0, target_ids=None):
        global vessel_counter
        self.id = vessel_counter
        vessel_counter += 1

        self.x = x
        self.y = y
        self.angle = angle
        self.path = [(x, y)]
        self.alive = True
        self.generation = generation
        self.age = 0
        self.target_ids = target_ids or []

# =========================================================
# MATH HELPERS
# =========================================================

def field(x, y):
    return np.array([
        np.sin(y * 1.1) + 0.35 * np.cos(x * 1.9),
        np.cos(x * 1.1) + 0.35 * np.sin(y * 1.9)
    ])

def attract_to_targets(tip, all_tips_by_id):
    force = np.zeros(2)
    for tid in tip.target_ids:
        target = all_tips_by_id.get(tid)
        if target is None:
            continue
        d = np.array([target.x - tip.x, target.y - tip.y])
        dist = np.linalg.norm(d) + 1e-6
        if dist < NEIGHBOR_RADIUS:
            strength = 1.0 + max(0, (1.5 - dist)) * 2.0
            force += (d / dist) * strength
    return force

def repel(tip, others):
    force = np.zeros(2)
    for o in others:
        if o.id == tip.id:
            continue
        d = np.array([tip.x - o.x, tip.y - o.y])
        dist = np.linalg.norm(d)
        if 1e-6 < dist < REPEL_RADIUS:
            force += d / (dist ** 3)
    return force

def point_segment_distance(px, py, ax, ay, bx, by):
    abx = bx - ax
    aby = by - ay
    apx = px - ax
    apy = py - ay

    ab_len2 = abx * abx + aby * aby + 1e-9
    t = (apx * abx + apy * aby) / ab_len2
    t = max(0, min(1, t))

    cx = ax + abx * t
    cy = ay + aby * t

    dx = px - cx
    dy = py - cy

    return (dx * dx + dy * dy) ** 0.5, (cx, cy)

# =========================================================
# VASCULAR SYSTEM
# =========================================================

class VascularSystem:
    def __init__(self, screen_size=SCREEN_SIZE):
        self.screen_size = screen_size
        self.tips = []
        self.paths_data = []
        self.segments = []
        self._build()

    def _build(self):
        global vessel_counter
        vessel_counter = 0

        N = 6
        RING_R = 3.5
        CX, CY = W / 2, H / 2

        ring_tips = []
        for i in range(N):
            angle = (i / N) * 2 * np.pi
            x = CX + RING_R * np.cos(angle)
            y = CY + RING_R * np.sin(angle)
            tangent = angle + np.pi / 2 + np.random.randn() * 0.2
            t = Tip(x, y, tangent, generation=0)
            ring_tips.append(t)

        for i in range(N):
            ring_tips[i].target_ids = [
                ring_tips[(i + 1) % N].id,
                ring_tips[(i + N // 2) % N].id
            ]

        self.tips = ring_tips

        for _ in range(STEPS):
            new_tips = []
            active = [t for t in self.tips if t.alive]
            tips_by_id = {t.id: t for t in self.tips}

            if not active:
                break

            for tip in active:
                tip.age += 1

                fx, fy = field(tip.x, tip.y)
                rx, ry = repel(tip, active)
                attract = attract_to_targets(tip, tips_by_id)

                dx = (
                    ANGLE_INFLUENCE * np.cos(tip.angle) +
                    FIELD_INFLUENCE * fx +
                    NEIGHBOR_ATTRACT * attract[0] +
                    REPEL_FORCE * rx +
                    NOISE * np.random.randn() +
                    JITTER * (random.random() - 0.5)
                )

                dy = (
                    ANGLE_INFLUENCE * np.sin(tip.angle) +
                    FIELD_INFLUENCE * fy +
                    NEIGHBOR_ATTRACT * attract[1] +
                    REPEL_FORCE * ry +
                    NOISE * np.random.randn() +
                    JITTER * (random.random() - 0.5)
                )

                norm = np.hypot(dx, dy) + 1e-6
                dx, dy = dx / norm, dy / norm

                tip.x += dx * STEP_SIZE
                tip.y += dy * STEP_SIZE
                tip.path.append((tip.x, tip.y))

                if tip.x < -0.5 or tip.x > W + 0.5 or tip.y < -0.5 or tip.y > H + 0.5:
                    tip.alive = False
                    continue

                if tip.age > ANAST_IMMUNITY:
                    for other in self.tips:
                        if other.id == tip.id:
                            continue
                        if len(other.path) < 8:
                            continue

                        dist, snap_pt = point_segment_distance(
                            tip.x, tip.y,
                            other.path[0][0], other.path[0][1],
                            other.path[-1][0], other.path[-1][1]
                        )

                        if dist < ANAST_RADIUS:
                            tip.path.append(snap_pt)
                            tip.alive = False
                            break

                if not tip.alive:
                    continue

                if tip.generation < MAX_GENERATION:
                    branch_prob = BASE_BRANCH - (tip.generation * BRANCH_DECAY)
                    if random.random() < branch_prob:
                        angle_offset = random.choice([-1, 1]) * (0.6 + np.random.rand() * 0.5)
                        new_tips.append(Tip(
                            tip.x,
                            tip.y,
                            tip.angle + angle_offset,
                            tip.generation + 1
                        ))

                tip.angle += np.random.randn() * 0.05

            self.tips.extend(new_tips)

        self.paths_data = [(t.path, t.generation) for t in self.tips if len(t.path) > 4]

        self.segments = []
        for path, gen in self.paths_data:
            for i in range(len(path) - 1):
                self.segments.append((path[i], path[i + 1], gen))

    def get_random_vessel_point(self):
        if not self.segments:
            return W / 2, H / 2

        safe_spawn_radius = VESSEL_RADIUS * 0.35
        for _ in range(200):
            a, b, _ = random.choice(self.segments)
            t = random.random()

            x = a[0] + (b[0] - a[0]) * t
            y = a[1] + (b[1] - a[1]) * t

            dx = b[0] - a[0]
            dy = b[1] - a[1]
            length = np.hypot(dx, dy) + 1e-9
            nx, ny = -dy / length, dx / length

            r = random.uniform(-safe_spawn_radius * 0.5, safe_spawn_radius * 0.5)
            x += nx * r
            y += ny * r

            valid = False
            for seg_a, seg_b, _ in self.segments:
                dist, _ = point_segment_distance(x, y, seg_a[0], seg_a[1], seg_b[0], seg_b[1])
                if dist <= safe_spawn_radius:
                    valid = True
                    break
            if valid:
                return x, y

        a, b, _ = random.choice(self.segments)
        return a[0], a[1]

    def constrain_particle(self, particle, screen_to_world_func):
        if not self.segments:
            return None

        # 1. Convert screen positions to world coords
        px, py = screen_to_world_func(float(particle.x), float(particle.y))
        px = float(px)
        py = float(py)

        # 2. Translate particle screen radius into world scale units
        px_edge, _ = screen_to_world_func(float(particle.x + particle.radius), float(particle.y))
        world_particle_radius = abs(px_edge - px)

        # Slippery boundary tracking
        max_allowed_dist = VESSEL_RADIUS - world_particle_radius

        closest_dist = float('inf')
        closest_snap_x = px
        closest_snap_y = py
        outside_any_vessel = True

        # 3. Scan segments with safe boundary filtering
        padding = VESSEL_RADIUS + world_particle_radius
        for seg_a, seg_b, gen in self.segments:
            ax, ay = float(seg_a[0]), float(seg_a[1])
            bx, by = float(seg_b[0]), float(seg_b[1])
            
            min_x = min(ax, bx) - padding
            max_x = max(ax, bx) + padding
            min_y = min(ay, by) - padding
            max_y = max(ay, by) + padding
            
            if not (min_x <= px <= max_x and min_y <= py <= max_y):
                continue

            dist, snap_pt = point_segment_distance(px, py, ax, ay, bx, by)
            
            if dist <= max_allowed_dist:
                outside_any_vessel = False

            if dist < closest_dist:
                closest_dist = dist
                closest_snap_x = float(snap_pt[0])
                closest_snap_y = float(snap_pt[1])

        # 4. Ultra-Slippery Boundary Physics
        if outside_any_vessel and closest_dist != float('inf'):
            dx = px - closest_snap_x
            dy = py - closest_snap_y
            mag = (dx * dx + dy * dy) ** 0.5
            
            if mag > 1e-6:
                nx = dx / mag
                ny = dy / mag
                
                # Snap the particle perfectly flush with the wall edge
                corrected_x = closest_snap_x + nx * max_allowed_dist
                corrected_y = closest_snap_y + ny * max_allowed_dist
                
                # Check normal velocity component relative to the wall
                dot_product = particle.vx * nx + particle.vy * ny
                
                if dot_product > 0:  # If moving into or pushing against the wall
                    # Perfect Elastic Slippery Bounce:
                    # Subtract only the perpendicular collision vector component.
                    particle.vx = (particle.vx - 1.5 * dot_product * nx)
                    particle.vy = (particle.vy - 1.5 * dot_product * ny)
                
                # Anti-stagnation baseline energy (ensures the particle never stalls out)
                speed_sq = particle.vx * particle.vx + particle.vy * particle.vy
                if speed_sq < 0.04:
                    particle.vx += random.uniform(-0.15, 0.15)
                    particle.vy += random.uniform(-0.15, 0.15)

                return corrected_x, corrected_y

        return None





    def draw(self, screen, world_to_screen_func):
        x0, _ = world_to_screen_func(0, 0)
        xr, _ = world_to_screen_func(VESSEL_RADIUS, 0)
        pixel_diameter = max(int(abs(xr - x0) * 2), 1)

        for path, gen in self.paths_data:
            color = (255, 0, 160) 
            thickness = max(int(pixel_diameter * (1 - gen * 0.15)), 2)
            radius = thickness // 2

            for i in range(len(path) - 1):
                p1 = world_to_screen_func(path[i][0], path[i][1])
                p2 = world_to_screen_func(path[i+1][0], path[i+1][1])
                
                pygame.draw.line(screen, color, p1, p2, thickness)
                pygame.draw.circle(screen, color, p1, radius)
            
            if path:
                p_last = world_to_screen_func(path[-1][0], path[-1][1])
                pygame.draw.circle(screen, color, p_last, radius)
