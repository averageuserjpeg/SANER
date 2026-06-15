import numpy as np
import pygame
import matplotlib.pyplot as plt
import random

# -----------------------------
# CONFIG
# -----------------------------
W, H = 10, 10
STEPS = 1200
STEP_SIZE = 0.088
CX, CY = W / 2, H / 2

# -----------------------------
# DYNAMICS
# -----------------------------
FIELD_INFLUENCE = 0.20
ANGLE_INFLUENCE = 0.25
NOISE = 0.13
REPEL_RADIUS = 2.0
REPEL_FORCE = 0.70
JITTER = 0.10

# Each tip is attracted to its two assigned neighbors
NEIGHBOR_ATTRACT = 0.60
NEIGHBOR_RADIUS = 5.0

# -----------------------------
# ANASTOMOSIS
# -----------------------------
ANAST_RADIUS = 0.22
ANAST_IMMUNITY = 40

# -----------------------------
# BRANCHING
# -----------------------------
MAX_GENERATION = 2
BASE_BRANCH = 0.045
BRANCH_DECAY = 0.008

# -----------------------------
# TIP
# -----------------------------
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
        self.target_ids = target_ids or []  # IDs of tips this one should connect to

tips = []

N = 6  # tips on the ring
RING_R = 3.5

ring_tips = []
for i in range(N):
    angle = (i / N) * 2 * np.pi
    x = CX + RING_R * np.cos(angle)
    y = CY + RING_R * np.sin(angle)
    # Aim tangentially — clockwise arc
    tangent = angle + np.pi / 2 + np.random.randn() * 0.2
    t = Tip(x, y, tangent, generation=0)
    ring_tips.append(t)

# Assign each tip to attract toward its clockwise neighbor
for i in range(N):
    ring_tips[i].target_ids = [ring_tips[(i + 1) % N].id, ring_tips[(i + N//2) % N].id]

tips.extend(ring_tips)


# -----------------------------
# FIELD
# -----------------------------
def field(x, y):
    return np.array([
        np.sin(y * 1.1) + 0.35 * np.cos(x * 1.9),
        np.cos(x * 1.1) + 0.35 * np.sin(y * 1.9)
    ])


def attract_to_targets(tip, all_tips_by_id):
    """Pull tip toward its assigned neighbor targets."""
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


def closest_point_on_path(px, py, path):
    best_dist = float('inf')
    best_pt = None
    for pt in path:
        d = np.hypot(px - pt[0], py - pt[1])
        if d < best_dist:
            best_dist = d
            best_pt = pt
    return best_dist, best_pt


# -----------------------------
# SIMULATION
# -----------------------------
for step in range(STEPS):
    new_tips = []
    active_tips = [t for t in tips if t.alive]
    tips_by_id = {t.id: t for t in tips}

    if not active_tips:
        break

    for tip in active_tips:
        tip.age += 1

        fx, fy = field(tip.x, tip.y)
        rx, ry = repel(tip, active_tips)
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

        # -----------------------------
        # ANASTOMOSIS
        # -----------------------------
        if tip.age > ANAST_IMMUNITY:
            for other in tips:
                if other.id == tip.id:
                    continue
                if len(other.path) < 8:
                    continue
                dist, snap_pt = closest_point_on_path(tip.x, tip.y, other.path)
                if dist < ANAST_RADIUS:
                    tip.path.append(snap_pt)
                    tip.alive = False
                    break

        if not tip.alive:
            continue

        # -----------------------------
        # BRANCHING
        # -----------------------------
        if tip.generation < MAX_GENERATION:
            branch_prob = BASE_BRANCH - (tip.generation * BRANCH_DECAY)
            if random.random() < branch_prob:
                angle_offset = random.choice([-1, 1]) * (0.6 + np.random.rand() * 0.5)
                child = Tip(
                    tip.x, tip.y,
                    tip.angle + angle_offset,
                    tip.generation + 1
                )
                new_tips.append(child)

        tip.angle += np.random.randn() * 0.05

    tips.extend(new_tips)


# -----------------------------
# PYGAME RENDER
# -----------------------------
pygame.init()

SCREEN_SIZE = 1000
screen = pygame.display.set_mode((SCREEN_SIZE, SCREEN_SIZE))
pygame.display.set_caption("SANER Vessel Generator")

clock = pygame.time.Clock()

paths_data = [(t.path, t.generation) for t in tips if len(t.path) > 4]

def world_to_screen(x, y):
    sx = int((x / W) * SCREEN_SIZE)
    sy = int((1 - y / H) * SCREEN_SIZE)  # flip Y like matplotlib
    return sx, sy

running = True

while running:

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill((255, 255, 255))

    for path, gen in paths_data:

        linewidth = max(15, int(20 - (gen * 2.5)))

        points = [world_to_screen(x, y) for x, y in path]

        if len(points) >= 2:

            for i in range(len(points) - 1):

                pygame.draw.line(
                    screen,
                    (255, 20, 147),   # deeppink
                    points[i],
                    points[i + 1],
                    linewidth
                )

                pygame.draw.circle(
                    screen,
                    (255, 20, 147),
                    points[i],
                    linewidth // 2
                )

                pygame.draw.circle(
                    screen,
                    (255, 20, 147),
                    points[i + 1],
                    linewidth // 2
                )

    pygame.display.flip()
    clock.tick(60)

pygame.quit()