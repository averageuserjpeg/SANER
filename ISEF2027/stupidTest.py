import numpy as np
import random
import pygame
import math
import pymunk

# =========================================================
# CONFIG
# =========================================================
W, H = 10, 10
STEPS = 900
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
    abx, aby = bx - ax, by - ay
    apx, apy = px - ax, py - ay
    ab_len2 = abx * abx + aby * aby + 1e-9
    t = (apx * abx + apy * aby) / ab_len2
    t = max(0, min(1, t))
    cx, cy = ax + abx * t, ay + aby * t
    dx, dy = px - cx, py - cy
    return math.hypot(dx, dy), (cx, cy)

# =========================================================
# VASCULAR SYSTEM
# =========================================================
class VascularSystem:
    def __init__(self):
        self.tips = []
        self.paths_data = []
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
            ring_tips.append(Tip(x, y, tangent, 0))

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
                ax, ay = attract_to_targets(tip, tips_by_id)

                dx = (ANGLE_INFLUENCE * math.cos(tip.angle) +
                      FIELD_INFLUENCE * fx +
                      NEIGHBOR_ATTRACT * ax +
                      REPEL_FORCE * rx +
                      NOISE * np.random.randn() +
                      JITTER * (random.random() - 0.5))

                dy = (ANGLE_INFLUENCE * math.sin(tip.angle) +
                      FIELD_INFLUENCE * fy +
                      NEIGHBOR_ATTRACT * ay +
                      REPEL_FORCE * ry +
                      NOISE * np.random.randn() +
                      JITTER * (random.random() - 0.5))

                norm = math.hypot(dx, dy) + 1e-6
                dx, dy = dx / norm, dy / norm

                tip.x += dx * STEP_SIZE
                tip.y += dy * STEP_SIZE
                tip.path.append((tip.x, tip.y))

                if tip.generation < MAX_GENERATION and random.random() < (BASE_BRANCH - tip.generation * BRANCH_DECAY):
                    new_tips.append(Tip(tip.x, tip.y, tip.angle + random.choice([-1, 1]) * 0.8, tip.generation + 1))

            self.tips.extend(new_tips)

        self.paths_data = [(t.path, t.generation) for t in self.tips if len(t.path) > 4]

# =========================================================
# FLOW FIELD
# =========================================================
class VascularFlowField:
    def __init__(self, paths_data, grid_res=120):
        self.grid_res = grid_res
        self.paths_data = paths_data
        self.field_grid = [[None for _ in range(grid_res)] for _ in range(grid_res)]
        self._generate()

    def _generate(self):
        for path, gen in self.paths_data:
            for i in range(len(path) - 1):
                p1, p2 = path[i], path[i + 1]
                vx, vy = p2[0] - p1[0], p2[1] - p1[1]
                l = math.hypot(vx, vy) + 1e-9
                vx, vy = vx / l, vy / l

                min_x = max(0, int(min(p1[0], p2[0]) * self.grid_res / W))
                max_x = min(self.grid_res - 1, int(max(p1[0], p2[0]) * self.grid_res / W))
                min_y = max(0, int(min(p1[1], p2[1]) * self.grid_res / H))
                max_y = min(self.grid_res - 1, int(max(p1[1], p2[1]) * self.grid_res / H))

                for gx in range(min_x, max_x + 1):
                    for gy in range(min_y, max_y + 1):
                        self.field_grid[gx][gy] = (vx, vy, 0.5)

    def sample_flow(self, x, y):
        gx = int((x / W) * self.grid_res)
        gy = int((y / H) * self.grid_res)
        if 0 <= gx < self.grid_res and 0 <= gy < self.grid_res:
            cell = self.field_grid[gx][gy]
            if cell:
                vx, vy, _ = cell
                return vx * 120, vy * 120
        return 0.0, 0.0

# =========================================================
# SIMULATION
# =========================================================
def run_simulation():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_SIZE, SCREEN_SIZE))
    clock = pygame.time.Clock()

    space = pymunk.Space()
    space.gravity = (0, 0)

    vascular_sys = VascularSystem()
    flow_field = VascularFlowField(vascular_sys.paths_data)

    def to_screen(pt):
        return int(pt[0] / W * SCREEN_SIZE), int(pt[1] / H * SCREEN_SIZE)

    def update_particle(body, _gravity, _damping, dt):
        wx = body.position.x / SCREEN_SIZE * W
        wy = body.position.y / SCREEN_SIZE * H
        vx, vy = flow_field.sample_flow(wx, wy)
        body.velocity = (vx, vy)

    particles = []

    def spawn_particle():
        if not vascular_sys.paths_data:
            return
        path = random.choice(vascular_sys.paths_data)[0]
        px, py = to_screen(random.choice(path[:max(1, len(path)//4)]))

        mass = 1
        radius = 3
        moment = pymunk.moment_for_circle(mass, 0, radius)

        body = pymunk.Body(mass, moment)
        body.position = (px, py)
        body.velocity_func = update_particle

        shape = pymunk.Circle(body, radius)
        shape.elasticity = 0.1
        shape.friction = 0.0

        space.add(body, shape)
        particles.append(body)

    for _ in range(200):
        spawn_particle()

    running = True
    while running:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False

        space.step(1 / 60)

        screen.fill((20, 10, 15))

        for path, _ in vascular_sys.paths_data:
            pts = [to_screen(p) for p in path]
            if len(pts) > 1:
                pygame.draw.lines(screen, (80, 20, 25), False, pts, 2)

        for body in particles:
            x, y = body.position
            pygame.draw.circle(screen, (235, 55, 65), (int(x), int(y)), 3)

            if x < 0 or x > SCREEN_SIZE or y < 0 or y > SCREEN_SIZE:
                body.position = to_screen(random.choice(vascular_sys.paths_data)[0][0:1])

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    run_simulation()