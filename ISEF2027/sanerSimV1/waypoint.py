import pygame
import math

COLOR_WAYPOINT = (0, 180, 255)  # Bright neon blue


class WaypointAgent:
    def __init__(
        self,
        vascular_system,
        v_graph,
        target_zone,
        screen_to_world_func,
        particles,
        magnets
    ):
        self.radius = 8
        self.vascular_system = vascular_system
        self.v_graph = v_graph
        self.target_zone = target_zone
        self.screen_to_world_func = screen_to_world_func

        self.speed = 0.05
        self.wx = 0.0
        self.wy = 0.0

        self.path = []
        self.current_node_index = 0

        self.best_mag = None  # <- for debug drawing

        self.recalculate_spawn_and_path(particles, magnets)

    # =========================================================
    # SPAWN + PATH LOGIC
    # =========================================================
    def recalculate_spawn_and_path(self, particles, magnets):
        target_wx, target_wy = self.screen_to_world_func(
            self.target_zone.cx,
            self.target_zone.cy
        )

        if not particles or not magnets:
            self._spawn_at_target_goal(target_wx, target_wy)
            return

        # -------------------------------
        # 1. COUNT PARTICLES PER MAGNET
        # -------------------------------
        magnet_counts = {m: 0 for m in magnets}

        for p in particles:
            for m in magnets:
                if m.rect().collidepoint(int(p.x), int(p.y)):
                    magnet_counts[m] += 1
                    break

        # Fix: Sync self.best_mag calculation directly with what we use for ranking
        self.best_mag = max(magnet_counts, key=magnet_counts.get)

        # If the absolute best magnet has 0 particles, don't track it as a cluster
        if magnet_counts[self.best_mag] == 0:
            self.best_mag = None
            self._spawn_at_target_goal(target_wx, target_wy)
            return

        active_clusters = [
            (mag, count)
            for mag, count in magnet_counts.items()
            if count > 0
        ]

        # -------------------------------
        # 2. RANK MAGNETS
        # -------------------------------
        def sorting_key(item):
            mag, count = item
            m_wx, m_wy = self.screen_to_world_func(mag.center[0], mag.center[1])
            dist_to_target = math.hypot(
                m_wx - target_wx,
                m_wy - target_wy
            )
            return (count, -dist_to_target)

        ranked_magnets = sorted(
            active_clusters,
            key=sorting_key,
            reverse=True
        )

        # -------------------------------
        # 3. TRY BEST MAGNET FIRST
        # -------------------------------
        # -------------------------------
        # 3. TRY BEST MAGNET FIRST
        # -------------------------------
        for best_magnet, particle_count in ranked_magnets:

            m_wx, m_wy = self.screen_to_world_func(
                best_magnet.center[0],
                best_magnet.center[1]
            )

            ideal_node = self.v_graph.find_closest_node((m_wx, m_wy))

            print("\n----------------")
            print(f"TARGET MAGNET AT SCREEN POS: {best_magnet.center}")
            print(f"PARTICLE COUNT ON MAGNET: {particle_count}")
            print(f"CLOSEST NETWORK NODE FOUND: {ideal_node}")

            if not ideal_node:
                print("⚠️ CRITICAL: No node exists near this electromagnet area!")
                continue

            calculated_path = self.v_graph.find_path_bfs(
                ideal_node,
                (target_wx, target_wy)
            )

            if calculated_path:
                print(f"✅ PATH SUCCESS! Route found with {len(calculated_path)} nodes.")
                self.wx, self.wy = ideal_node
                self.path = calculated_path
                self.current_node_index = 0
                return
            else:
                # ---------------------------------------------------------
                # YOUR REQUESTED DEBUG SIGNAL
                # ---------------------------------------------------------
                print("❌ NO PATHWAY FOUND! The graph segment is physically isolated from the target goal.")

            # -------------------------------
            # RECOVERY (If primary path fails)
            # -------------------------------
            print("🔄 Attempting to locate nearest functional recovery node...")
            best_recovery_node = None
            best_recovery_path = []
            min_dist = float('inf')

            for node in self.v_graph.nodes:
                path_check = self.v_graph.find_path_bfs(
                    node,
                    (target_wx, target_wy)
                )

                if path_check:
                    dist = math.hypot(
                        node[0] - m_wx,
                        node[1] - m_wy
                    )

                    if dist < min_dist:
                        min_dist = dist
                        best_recovery_node = node
                        best_recovery_path = path_check

            if best_recovery_node:
                print(f"🩹 RECOVERY SUCCESS! Diverting agent to node {best_recovery_node}")
                self.wx, self.wy = best_recovery_node
                self.path = best_recovery_path
                self.current_node_index = 0
                return
            else:
                print("🚨 CRITICAL FAILURE: The entire network configuration cannot reach the target!")

        # -------------------------------
        # FORCE FALLBACK (Prevents freezing coordinates)
        # -------------------------------
        print("🛑 FALLING BACK: Routing directly to destination zone anchor.")
        self._spawn_at_target_goal(target_wx, target_wy)

    # =========================================================
    # FALLBACK SPAWN
    # =========================================================
    def _spawn_at_target_goal(self, target_wx, target_wy):
        best_node = None
        min_dist = float('inf')

        for node in self.v_graph.nodes:
            dist = math.hypot(
                node[0] - target_wx,
                node[1] - target_wy
            )

            if dist < min_dist:
                path_check = self.v_graph.find_path_bfs(
                    node,
                    (target_wx, target_wy)
                )

                if path_check:
                    min_dist = dist
                    best_node = node

        if best_node:
            self.wx, self.wy = best_node
            self.path = self.v_graph.find_path_bfs(
                best_node,
                (target_wx, target_wy)
            )
        else:
            self.wx, self.wy = target_wx, target_wy
            self.path = [(target_wx, target_wy)]

        self.current_node_index = 0

    # =========================================================
    # UPDATE
    # =========================================================
    def update(self, particles, magnets):
        if not self.path:
            return

        if self.current_node_index >= len(self.path):
            self.recalculate_spawn_and_path(particles, magnets)
            return

        tx, ty = self.path[self.current_node_index]

        dx = tx - self.wx
        dy = ty - self.wy
        dist = math.hypot(dx, dy)

        if dist < self.speed:
            self.wx, self.wy = tx, ty
            self.current_node_index += 1
        else:
            self.wx += (dx / dist) * self.speed
            self.wy += (dy / dist) * self.speed

    # =========================================================
    # DRAW
    # =========================================================
    def draw(self, screen, world_to_screen_func):
        sx, sy = world_to_screen_func(self.wx, self.wy)

        pygame.draw.circle(
            screen,
            COLOR_WAYPOINT,
            (int(sx), int(sy)),
            self.radius
        )

        pygame.draw.circle(
            screen,
            (255, 255, 255),
            (int(sx), int(sy)),
            2
        )

        # DEBUG RED BOX (safe now)
        if self.best_mag is not None:
            pygame.draw.rect(
                screen,
                (255, 0, 0),
                self.best_mag.rect(),
                3
            )