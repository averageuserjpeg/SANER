import pygame
import math
from collections import deque

class VascularGraph:
    def __init__(self, vascular_system, snap_precision=3):
        """
        Converts the disorganized paths_data into a structured node graph.
        snap_precision: Number of decimal places to round coordinates to ensure branches connect.
        """
        self.nodes = {}  # Map of (x, y) -> list of connected (nx, ny) nodes
        self.snap_precision = snap_precision
        self._build_graph(vascular_system)

    def _snap(self, pt):
        """Rounds a floating-point coordinate to force connections to merge cleanly."""
        return (round(pt[0], self.snap_precision), round(pt[1], self.snap_precision))

    def _build_graph(self, vascular_system):
        # Grab every single point (Stride = 1) to match the continuous physical layout perfectly
        STEP_STRIDE = 1 

        for path, _ in vascular_system.paths_data:
            if len(path) < 2:
                continue
            
            subsampled_path = path[::STEP_STRIDE]
            
            if path[-1] != subsampled_path[-1]:
                subsampled_path.append(path[-1])
                
            if len(subsampled_path) < 2:
                continue

            for i in range(len(subsampled_path) - 1):
                p1 = self._snap(subsampled_path[i])
                p2 = self._snap(subsampled_path[i+1])
                
                if p1 == p2:
                    continue
                
                if p1 not in self.nodes: self.nodes[p1] = set()
                if p2 not in self.nodes: self.nodes[p2] = set()
                
                self.nodes[p1].add(p2)
                self.nodes[p2].add(p1)

        # -----------------------------------------------------------------
        # PROXIMITY INTERSECTION WELDING
        # Fixes the hidden gap between branches and their parent vessels
        # -----------------------------------------------------------------
        WELD_RADIUS = 0.25 # Matches your simulation's ANAST_RADIUS
        node_list = list(self.nodes.keys())
        
        for i in range(len(node_list)):
            for j in range(i + 1, len(node_list)):
                n1 = node_list[i]
                n2 = node_list[j]
                
                # If two nodes are physically within the collision radius, weld them!
                if math.hypot(n1[0] - n2[0], n1[1] - n2[1]) <= WELD_RADIUS:
                    self.nodes[n1].add(n2)
                    self.nodes[n2].add(n1)

    def find_closest_node(self, world_pt):
        """Finds the nearest node in the graph to any random point in world space."""
        if not self.nodes:
            return None
        
        best_node = None
        min_dist = float('inf')
        
        for node in self.nodes:
            dist = math.hypot(node[0] - world_pt[0], node[1] - world_pt[1])
            if dist < min_dist:
                min_dist = dist
                best_node = node
                
        return best_node

    def find_path_bfs(self, start_world, end_world):
        """
        Finds a route from start to end using a Breadth-First Search (BFS).
        Returns a list of world coordinates mapping out the path.
        """
        start_node = self.find_closest_node(start_world)
        end_node = self.find_closest_node(end_world)
        
        if not start_node or not end_node:
            return []

        queue = deque([[start_node]])
        visited = {start_node}

        while queue:
            path = queue.popleft()
            current = path[-1]

            if current == end_node:
                return path

            for neighbor in self.nodes.get(current, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    new_path = list(path)
                    new_path.append(neighbor)
                    queue.append(new_path)
                    
        return [] # No path found

    def draw_overlay(self, screen, world_to_screen_func):
        """Draws bright cyan lines over the converted network to prove it mapped correctly."""
        # Draw the connections (Edges)
        for node, neighbors in self.nodes.items():
            p1 = world_to_screen_func(node[0], node[1])
            for n in neighbors:
                p2 = world_to_screen_func(n[0], n[1])
                pygame.draw.line(screen, (0, 255, 255), p1, p2, 2)
        
        # Draw the intersection points (Nodes)
        for node in self.nodes:
            p = world_to_screen_func(node[0], node[1])
            pygame.draw.circle(screen, (255, 0, 100), p, 3)