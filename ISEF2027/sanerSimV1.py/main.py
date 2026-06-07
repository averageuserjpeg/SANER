import pygame
import random
import math

from nanoparticle import Nanoparticle
from electromagnet import Electromagnet
from maze import generate_maze, maze_to_walls
from vascular import VascularSystem, W, H

pygame.init()

# --- CONFIG ---
WIDTH, HEIGHT = 1000, 700
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("I STILL NEED AN INTERNSHIP")
clock = pygame.time.Clock()
FPS = 60

COLOR_BG = (20, 24, 30)
COLOR_TEXT = (200, 200, 200)

# =========================================================
# --- MAZE SETUP (unchanged, EM only) ---
# =========================================================

cols = 8
rows = 8
cell_size = 70

maze_cols = cols
maze_rows = rows
maze_cell_size = cell_size

maze_width = maze_cols * maze_cell_size
maze_height = maze_rows * maze_cell_size

maze_origin_x = (WIDTH - maze_width) // 2
maze_origin_y = (HEIGHT - maze_height) // 2

maze_grid = generate_maze(maze_cols, maze_rows)

walls = maze_to_walls(
    maze_grid,
    maze_cell_size,
    maze_origin_x,
    maze_origin_y
)

# =========================================================
# --- ELECTROMAGNETS ---
# =========================================================

em_grid_width = cols * cell_size
em_grid_height = rows * cell_size

max_x = maze_origin_x + maze_width - em_grid_width
max_y = maze_origin_y + maze_height - em_grid_height

em_start_x = random.randint(maze_origin_x, max_x)
em_start_y = random.randint(maze_origin_y, max_y)

magnets = []
for i in range(cols):
    for j in range(rows):
        x = em_start_x + i * cell_size + cell_size // 2
        y = em_start_y + j * cell_size + cell_size // 2
        magnets.append(Electromagnet(x, y, size=cell_size))

# =========================================================
# --- VASCULAR SYSTEM ---
# =========================================================

vascular = VascularSystem()

# =========================================================
# --- WORLD ↔ SCREEN HELPERS ---
# =========================================================

def world_to_screen(wx, wy):
    sx = maze_origin_x + (wx / W) * maze_width
    sy = maze_origin_y + (1 - wy / H) * maze_height
    return int(sx), int(sy)

def screen_to_world(sx, sy):
    wx = ((sx - maze_origin_x) / maze_width) * W
    wy = (1 - (sy - maze_origin_y) / maze_height) * H
    return wx, wy

# =========================================================
# --- NANOPARTICLES (FIXED SPAWN) ---
# =========================================================

particles = []
for _ in range(15):
    wx, wy = vascular.get_random_vessel_point()
    x, y = world_to_screen(wx, wy)
    particles.append(Nanoparticle(x, y))

# =========================================================
# --- UI ---
# =========================================================

font = pygame.font.SysFont(None, 24)

# =========================================================
# --- COLLISION ENGINE ---
# =========================================================

def resolve_particle_collisions(particles):
    for i in range(len(particles)):
        p1 = particles[i]
        r1 = p1.get_rect()

        for j in range(i + 1, len(particles)):
            p2 = particles[j]
            r2 = p2.get_rect()

            if not r1.colliderect(r2):
                continue

            dx_left = r2.right - r1.left
            dx_right = r1.right - r2.left
            dy_top = r2.bottom - r1.top
            dy_bottom = r1.bottom - r2.top

            min_dx = dx_left if abs(dx_left) < abs(dx_right) else -dx_right
            min_dy = dy_top if abs(dy_top) < abs(dy_bottom) else -dy_bottom

            if abs(min_dx) < abs(min_dy):
                p1.x += min_dx / 2
                p2.x -= min_dx / 2
                p1.vx *= -0.5
                p2.vx *= -0.5
            else:
                p1.y += min_dy / 2
                p2.y -= min_dy / 2
                p1.vy *= -0.5
                p2.vy *= -0.5

# =========================================================
# --- MAIN LOOP ---
# =========================================================

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        for m in magnets:
            m.handle_event(event)

    # --- PHYSICS ---
    for p in particles:
        p.update_multi_physics(magnets, vascular)
        # Execute sub-stepper with clean function mappings injected straight through
        p.apply_motion_substepped(vascular, screen_to_world, world_to_screen)

    resolve_particle_collisions(particles)

    # --- DRAW ---
    screen.fill(COLOR_BG)

    # electromagnets
    for m in magnets:
        m.draw(screen)

    # vascular system
    vascular.draw(screen, world_to_screen)

    # nanoparticles
    for p in particles:
        p.draw(screen)

    # UI
    txt = font.render("ur a bum", True, COLOR_TEXT)
    screen.blit(txt, (20, 20))

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
