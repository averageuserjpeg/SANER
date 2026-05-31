import random
import pygame

# Directions for maze carving
DIRS = {
    "N": (0, -1),
    "S": (0, 1),
    "W": (-1, 0),
    "E": (1, 0),
}

OPPOSITE = {
    "N": "S",
    "S": "N",
    "W": "E",
    "E": "W",
}


class Cell:
    def __init__(self):
        # start with all walls present
        self.walls = {"N", "S", "E", "W"}
        self.visited = False


def generate_maze(cols, rows):
    """
    Generates a perfect maze using iterative DFS (recursive backtracker).
    Result: a fully connected maze with no isolated cells.
    """

    grid = [[Cell() for _ in range(rows)] for _ in range(cols)]

    stack = []
    start = (0, 0)

    stack.append(start)
    grid[0][0].visited = True

    while stack:
        cx, cy = stack[-1]

        neighbors = []

        for d, (dx, dy) in DIRS.items():
            nx, ny = cx + dx, cy + dy

            if 0 <= nx < cols and 0 <= ny < rows:
                if not grid[nx][ny].visited:
                    neighbors.append((d, nx, ny))

        if neighbors:
            d, nx, ny = random.choice(neighbors)

            # remove walls between current and next cell
            grid[cx][cy].walls.remove(d)
            grid[nx][ny].walls.remove(OPPOSITE[d])

            grid[nx][ny].visited = True
            stack.append((nx, ny))

        else:
            stack.pop()

    return grid


def maze_to_walls(grid, cell_size, offset_x, offset_y):
    """
    Converts maze grid into pygame.Rect wall segments.
    Each wall becomes a thin rectangle.
    """

    walls = []

    cols = len(grid)
    rows = len(grid[0])

    for x in range(cols):
        for y in range(rows):

            cell = grid[x][y]

            cx = offset_x + x * cell_size
            cy = offset_y + y * cell_size

            thickness = 15  # wall thickness

            # North wall
            if "N" in cell.walls:
                walls.append(
                    pygame.Rect(cx, cy, cell_size, thickness)
                )

            # South wall
            if "S" in cell.walls:
                walls.append(
                    pygame.Rect(cx, cy + cell_size, cell_size, thickness)
                )

            # West wall
            if "W" in cell.walls:
                walls.append(
                    pygame.Rect(cx, cy, thickness, cell_size)
                )

            # East wall
            if "E" in cell.walls:
                walls.append(
                    pygame.Rect(cx + cell_size, cy, thickness, cell_size)
                )

    return walls