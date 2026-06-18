import pygame
import random
import math

from nanoparticle import Nanoparticle
from electromagnet import Electromagnet
from mazeUNUSED import generate_maze, maze_to_walls
from vascular import VascularSystem, W, H
from target_zone import TargetZone

# Import the network extractor and the new waypoint agent module
from vascularPathfindableConverter import VascularGraph
from waypoint import WaypointAgent

pygame.init()

# --- CONFIG ---
WIDTH, HEIGHT = 1000, 700
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("I STILL NEED AN INTERNSHIP")
clock = pygame.time.Clock()
FPS = 60

COLOR_BG = (20, 24, 30)
COLOR_TEXT = (200, 200, 200)
COLOR_COUNTER = (0, 255, 100) # Green accent for the counter

# --- MAZE CONFIG ---
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

# Global toggle state to track whether the node graph should render
show_graph_overlay = False
v_graph = None
blue_agent = None

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
# --- RESET / INITIALIZATION FUNCTION ---
# =========================================================
def reset_simulation():
    """Regenerates all system networks, magnets, target zone, and nanoparticles."""
    global maze_grid, walls, magnets, vascular, target_box, particles, v_graph, blue_agent
    
    # 1. Regenerate Maze Walls
    maze_grid = generate_maze(maze_cols, maze_rows)
    walls = maze_to_walls(maze_grid, maze_cell_size, maze_origin_x, maze_origin_y)

    # 2. Reset Electromagnets
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

    # 3. Regenerate Vascular Network
    vascular = VascularSystem()

    # 4. Generate the Pathfindable Network Structure from the continuous vessels
    v_graph = VascularGraph(vascular)

    # 5. Instantiate Target Zone
    target_box = TargetZone(vascular, world_to_screen, size=75, alpha=75)

    particles = []
    for _ in range(40):
        wx, wy = vascular.get_random_vessel_point()
        x, y = world_to_screen(wx, wy)
        particles.append(Nanoparticle(x, y))


    blue_agent = WaypointAgent(vascular, v_graph, target_box, screen_to_world, particles, magnets)


# Initialize the first game state
reset_simulation()

# --- UI ---
font = pygame.font.SysFont(None, 24)

# =========================================================
# --- COLLISION ENGINE ---
# =========================================================
def resolve_particle_collisions(particles):
    count = len(particles)
    for i in range(count):
        p1 = particles[i]
        p1_x, p1_y = p1.x, p1.y
        p1_r = p1.radius

        for j in range(i + 1, count):
            p2 = particles[j]
            
            dx = p2.x - p1_x
            if dx > 10 or dx < -10: continue
            
            dy = p2.y - p1_y
            if dy > 10 or dy < -10: continue

            dist_sq = dx * dx + dy * dy
            min_dist = p1_r + p2.radius

            if dist_sq >= min_dist * min_dist:
                continue

            dist = math.sqrt(dist_sq) + 1e-9
            overlap = min_dist - dist

            nx = dx / dist
            ny = dy / dist
            push = overlap * 0.5

            p1.x -= nx * push
            p1.y -= ny * push
            p2.x += nx * push
            p2.y += ny * push

            relvx = p2.vx - p1.vx
            relvy = p2.vy - p1.vy
            rel_dot = relvx * nx + relvy * ny

            if rel_dot < 0:
                impulse = -rel_dot * 0.5
                p1.vx -= impulse * nx
                p1.vy -= impulse * ny
                p2.vx += impulse * nx
                p2.vy += impulse * ny

# =========================================================
# --- MAIN LOOP ---
# =========================================================
# Track how many consecutive seconds the threshold has been met
zone_timer = 0.0  

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        # Intercept keystrokes to handle the spacebar toggle option
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                show_graph_overlay = not show_graph_overlay

        for m in magnets:
            m.handle_event(event)

    # --- PHYSICS (FIXED COLLISION ORDER) ---
    for p in particles:
        p.update_multi_physics(magnets, vascular)

    STEPS = 4
    for _ in range(STEPS):
        for p in particles:
            p.vx *= 0.995
            p.vy *= 0.995
            
            speed_sq = p.vx * p.vx + p.vy * p.vy
            max_sq = p.max_speed * p.max_speed
            if speed_sq > max_sq:
                scale = p.max_speed / math.sqrt(speed_sq)
                p.vx *= scale
                p.vy *= scale

            p.old_x = p.x
            p.old_y = p.y

            p.x += p.vx / STEPS
            p.y += p.vy / STEPS
            p._resolve_world_bounds()

        resolve_particle_collisions(particles)

        for p in particles:
            result = vascular.constrain_particle(p, screen_to_world)
            if result is not None:
                sx, sy = world_to_screen(float(result[0]), float(result[1]))
                
                dx = sx - p.old_x
                dy = sy - p.old_y
                dist = math.hypot(dx, dy)
                if dist > 1e-6:
                    nx = dx / dist
                    ny = dy / dist
                    dot_product = p.vx * nx + p.vy * ny
                    if dot_product > 0:
                        p.vx -= dot_product * nx * 1.2
                        p.vy -= dot_product * ny * 1.2
                
                p.x = float(sx)
                p.y = float(sy)

    # Update our new Waypoint Agent path navigation state
    if blue_agent is not None:
        blue_agent.update(particles, magnets)
        

    # =========================================================
    # --- TARGET ZONE CHECK & RESET LOGIC ---
    # =========================================================
    # Define bounding dimensions of the zone in pixels
    zone_left = target_box.rect_x
    zone_right = target_box.rect_x + target_box.size
    zone_top = target_box.rect_y
    zone_bottom = target_box.rect_y + target_box.size

    # Count how many particles are inside the zone bounds
    contained_count = 0

    zone_left = target_box.rect_x
    zone_right = target_box.rect_x + target_box.size
    zone_top = target_box.rect_y
    zone_bottom = target_box.rect_y + target_box.size

    for p in particles:

        if zone_left <= p.x <= zone_right and zone_top <= p.y <= zone_bottom:
            contained_count += 1
            p.in_zone = True
        else:
            p.in_zone = False

    total_particles = len(particles)
    current_percentage = contained_count / total_particles if total_particles > 0 else 0
    
    # Check if containment meets or exceeds 60%
    if current_percentage >= 0.60:
        # clock.get_time() returns milliseconds since the last frame; convert to seconds
        zone_timer += clock.get_time() / 1000.0
    else:
        # Reset the timer immediately if density drops below threshold
        zone_timer = 0.0

    # If held successfully for 2.0 seconds, wipe the state and redraw
    if zone_timer >= 2.0:
        zone_timer = 0.0  
        reset_simulation()
        continue # Skip rendering this frame and restart loop with new layout

    # --- DRAW ---
    screen.fill(COLOR_BG)

    for m in magnets:
        m.draw(screen)

    vascular.draw(screen, world_to_screen)
    
    # If active, overlay the extracted structural node graph straight onto the vessels
    if show_graph_overlay and v_graph is not None:
        v_graph.draw_overlay(screen, world_to_screen)

    target_box.draw(screen)

    # Render the bright blue waypoint agent smoothly over the channels
    if blue_agent is not None:
        # blue_agent.draw(screen, world_to_screen)
        pass

    for p in particles:
        p.draw(screen)

    # --- UI RENDER ---
    txt_bum = font.render("ur a bum", True, COLOR_TEXT)
    screen.blit(txt_bum, (20, 20))
    
    # Visual indicator of overlay status
    overlay_status = "ON" if show_graph_overlay else "OFF"
    txt_overlay = font.render(f"Graph Map (Space): {overlay_status}", True, (0, 180, 255))
    screen.blit(txt_overlay, (20, 45))
    
    # Counter 1: Particle Capacity Ratio
    counter_str = f"In Zone: {contained_count}/{total_particles} ({int(current_percentage * 100)}%)"
    txt_counter = font.render(counter_str, True, COLOR_COUNTER)
    screen.blit(txt_counter, (WIDTH - 240, 20))

    # Counter 2: Remaining Hold Duration Countdown
    time_left = max(0.0, 2.0 - zone_timer) if zone_timer > 0 else 2.0
    timer_str = f"Hold Time: {time_left:.1f}s / 2.0s"
    
    # Color-shift timer to orange when active to visually grab attention
    timer_color = (255, 140, 0) if zone_timer > 0 else COLOR_TEXT
    txt_timer = font.render(timer_str, True, timer_color)
    screen.blit(txt_timer, (WIDTH - 240, 45))

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()