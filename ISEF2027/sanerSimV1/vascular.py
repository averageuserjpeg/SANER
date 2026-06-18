import numpy as np
import random
import pygame
import math

# =========================================================
# CONFIG
# =========================================================
W, H = 10, 10
STEPS = 100
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
VESSEL_RADIUS = 0.30

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
            force += (d / dist) * (1.0 + max(0, (1.5 - dist)) * 2.0)
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
    t = max(0, min(1, (apx * abx + apy * aby) / ab_len2))
    cx = ax + abx * t
    cy = ay + aby * t
    dx = px - cx
    dy = py - cy
    return (dx * dx + dy * dy) ** 0.5, (cx, cy)

class VascularSystem:
    def __init__(self, screen_size=SCREEN_SIZE):
        self.screen_size = screen_size
        self.tips = []
        self.paths_data = []
        self.segments = []
        self.grid = {} 
        self.grid_res = 1.0  # Cell size for broadphase lookup
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
            t = Tip(x, y, angle + np.pi / 2 + np.random.randn() * 0.2, generation=0)
            ring_tips.append(t)

        for i in range(N):
            ring_tips[i].target_ids = [ring_tips[(i + 1) % N].id, ring_tips[(i + N // 2) % N].id]

        self.tips = ring_tips

        for _ in range(STEPS):
            new_tips = []
            active = [t for t in self.tips if t.alive]
            tips_by_id = {t.id: t for t in self.tips}
            if not active: break

            for tip in active:
                tip.age += 1
                fx, fy = field(tip.x, tip.y)
                rx, ry = repel(tip, active)
                attract = attract_to_targets(tip, tips_by_id)

                dx = (ANGLE_INFLUENCE * np.cos(tip.angle) + FIELD_INFLUENCE * fx +
                      NEIGHBOR_ATTRACT * attract[0] + REPEL_FORCE * rx +
                      NOISE * np.random.randn() + JITTER * (random.random() - 0.5))
                dy = (ANGLE_INFLUENCE * np.sin(tip.angle) + FIELD_INFLUENCE * fy +
                      NEIGHBOR_ATTRACT * attract[1] + REPEL_FORCE * ry +
                      NOISE * np.random.randn() + JITTER * (random.random() - 0.5))

                margin = 0.8
                if tip.x < margin or tip.x > W - margin or tip.y < margin or tip.y > H - margin:
                    tc_len = math.hypot(CX - tip.x, CY - tip.y) + 1e-6
                    dx += ((CX - tip.x) / tc_len) * 0.45
                    dy += ((CY - tip.y) / tc_len) * 0.45

                norm = np.hypot(dx, dy) + 1e-6
                tip.x += (dx / norm) * STEP_SIZE
                tip.y += (dy / norm) * STEP_SIZE
                tip.path.append((tip.x, tip.y))

                if tip.x < -0.8 or tip.x > W + 0.8 or tip.y < -0.8 or tip.y > H + 0.8:
                    tip.alive = False
                    continue

                if tip.age > ANAST_IMMUNITY:
                    for other in self.tips:
                        if other.id == tip.id or len(other.path) < 8: continue
                        dist, snap_pt = point_segment_distance(tip.x, tip.y, other.path[0][0], other.path[0][1], other.path[-1][0], other.path[-1][1])
                        if dist < ANAST_RADIUS:
                            tip.path.append(snap_pt)
                            tip.alive = False
                            break
                if not tip.alive: continue

                if tip.generation < MAX_GENERATION and random.random() < (BASE_BRANCH - (tip.generation * BRANCH_DECAY)):
                    new_tips.append(Tip(tip.x, tip.y, tip.angle + random.choice([-1, 1]) * (0.6 + np.random.rand() * 0.5), tip.generation + 1))
                tip.angle += np.random.randn() * 0.05
            self.tips.extend(new_tips)

        self.paths_data = [(t.path, t.generation) for t in self.tips if len(t.path) > 4]

        # Extra Bridges logic (kept completely intact)
        extra_bridges = []
        connection_threshold = ANAST_RADIUS * 1.5  
        for path, gen in self.paths_data:
            if len(path) < 2: continue
            ex, ey = path[-1]
            dir_x, dir_y = ex - path[-2][0], ey - path[-2][1]
            dir_len = math.hypot(dir_x, dir_y) + 1e-9
            dx_norm, dy_norm = dir_x / dir_len, dir_y / dir_len
            
            already_connected = False
            for test_path, _ in self.paths_data:
                if test_path is path: continue
                for vx, vy in test_path:
                    if math.hypot(vx - ex, vy - ey) < connection_threshold:
                        already_connected = True; break
                if already_connected: break
            if already_connected: continue

            best_dist, best_snap_pt = float('inf'), None
            for host_path, _ in self.paths_data:
                if host_path is path: continue
                for i in range(len(host_path) - 1):
                    dist, snap_pt = point_segment_distance(ex, ey, host_path[i][0], host_path[i][1], host_path[i+1][0], host_path[i+1][1])
                    if dist < best_dist: best_dist, best_snap_pt = dist, snap_pt

            if best_snap_pt is not None and best_dist < 4.0:
                sx, sy = best_snap_pt
                bridge_len = math.hypot(sx - ex, sy - ey) + 1e-9
                if (dx_norm * ((sx - ex) / bridge_len) + dy_norm * ((sy - ey) / bridge_len)) < -0.5 and bridge_len > 0.15: continue  
                extra_bridges.append(([(ex, ey), ((ex + sx) * 0.5 + random.uniform(-0.1, 0.1), (ey + sy) * 0.5 + random.uniform(-0.1, 0.1)), (sx, sy)], gen))
        self.paths_data.extend(extra_bridges)

        # Rebuild segments and populate spatial grid lookup mapping
        self.segments = []
        self.grid = {}
        for path, gen in self.paths_data:
            for i in range(len(path) - 1):
                seg = (path[i], path[i + 1], gen)
                self.segments.append(seg)
                
                # Spatial Hash mapping
                ax, ay = path[i]
                bx, by = path[i+1]
                x_min = int(floor(min(ax, bx) - VESSEL_RADIUS) / self.grid_res)
                x_max = int(floor(max(ax, bx) + VESSEL_RADIUS) / self.grid_res)
                y_min = int(floor(min(ay, by) - VESSEL_RADIUS) / self.grid_res)
                y_max = int(floor(max(ay, by) + VESSEL_RADIUS) / self.grid_res)
                
                for gx in range(x_min, x_max + 1):
                    for gy in range(y_min, y_max + 1):
                        self.grid.setdefault((gx, gy), []).append(seg)

    def get_random_vessel_point(self):
        if not self.segments: return W / 2, H / 2
        a, b, _ = random.choice(self.segments)
        return a[0] + (b[0] - a[0]) * random.random(), a[1] + (b[1] - a[1]) * random.random()

    def constrain_particle(self, particle, screen_to_world_func):
        if not self.segments: return None

        # 1. Convert particle position to world space to look up nearby segments
        px, py = screen_to_world_func(float(particle.x), float(particle.y))

        closest_dist = float('inf')
        closest_snap_x, closest_snap_y = px, py
        outside_any_vessel = True

        # Quick Spatial Grid Broadphase lookup
        gx = int(math.floor(px / self.grid_res))
        gy = int(math.floor(py / self.grid_res))
        
        nearby_segments = []
        for nx in range(gx - 1, gx + 2):
            for ny in range(gy - 1, gy + 2):
                if (nx, ny) in self.grid:
                    nearby_segments.extend(self.grid[(nx, ny)])
                    
        if not nearby_segments:
            nearby_segments = self.segments

        # Find the closest segment line
        for seg_a, seg_b, gen in nearby_segments:
            ax, ay = float(seg_a[0]), float(seg_a[1])
            bx, by = float(seg_b[0]), float(seg_b[1])
            
            dist, snap_pt = point_segment_distance(px, py, ax, ay, bx, by)

            if dist < closest_dist:
                closest_dist = dist
                closest_snap_x, closest_snap_y = float(snap_pt[0]), float(snap_pt[1])

        # 2. Hard threshold: Convert the closest vessel centerline point back to PIXELS
        # We will do our capping and bouncing entirely in screen pixels.
        from main import world_to_screen  # Import your main screen helper
        
        snap_sx, snap_sy = world_to_screen(closest_snap_x, closest_snap_y)
        
        # Calculate how wide the vessel is in pixels
        x0, _ = world_to_screen(0, 0)
        xr, _ = world_to_screen(VESSEL_RADIUS, 0)
        pixel_vessel_radius = abs(xr - x0)
        
        # Max distance a particle center can be from the centerline in pixels
        max_pixel_dist = max(0.1, pixel_vessel_radius - particle.radius)

        # Distance from particle to centerline in pixels
        dx_pixel = particle.x - snap_sx
        dy_pixel = particle.y - snap_sy
        pixel_dist = math.hypot(dx_pixel, dy_pixel)

        # If it goes beyond the pixel boundary of the tube, push it back in!
        if pixel_dist > max_pixel_dist and pixel_dist > 1e-6:
            # Normal vector pointing outwards from center of tube
            nx = dx_pixel / pixel_dist
            ny = dy_pixel / pixel_dist
            
            # Correct pixel position right to the edge
            corrected_sx = snap_sx + nx * max_pixel_dist
            corrected_sy = snap_sy + ny * max_pixel_dist
            
            # Clean velocity reflection using PIXEL vectors
            dot_product = particle.vx * nx + particle.vy * ny
            if dot_product > 0:  
                BOUNCE = 1.2
                particle.vx -= dot_product * nx * BOUNCE
                particle.vy -= dot_product * ny * BOUNCE
                
            # Convert corrected pixel position back to world units 
            # because main.py expects a world coordinate return value
            return screen_to_world_func(corrected_sx, corrected_sy)

        return None
    
    def draw(self, screen, world_to_screen_func):
        x0, _ = world_to_screen_func(0, 0)
        xr, _ = world_to_screen_func(VESSEL_RADIUS, 0)
        pixel_diameter = max(int(abs(xr - x0) * 2), 1)

        for path, gen in self.paths_data:
            color = (86, 87, 102)
            thickness = max(int(pixel_diameter * (1 - gen * 0.15)), 2)
            radius = thickness // 2

            for i in range(len(path) - 1):
                p1 = world_to_screen_func(path[i][0], path[i][1])
                p2 = world_to_screen_func(path[i+1][0], path[i+1][1])
                pygame.draw.line(screen, color, p1, p2, thickness)
                pygame.draw.circle(screen, color, p1, radius)
            if path:
                pygame.draw.circle(screen, color, world_to_screen_func(path[-1][0], path[-1][1]), radius)

# Utility floor lookup shorthand inline helper
def floor(val):
    return math.floor(val)