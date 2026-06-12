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
        self.walls = {"N", "S", "E", "W"}
        self.visited = False


def generate_maze(cols, rows):
    """
    Generate a connected maze using iterative DFS.
    """

    grid = [[Cell() for _ in range(rows)] for _ in range(cols)]

    stack = [(0, 0)]
    grid[0][0].visited = True

    while stack:
        cx, cy = stack[-1]

        neighbors = []

        for d, (dx, dy) in DIRS.items():
            nx = cx + dx
            ny = cy + dy

            if (
                0 <= nx < cols and
                0 <= ny < rows and
                not grid[nx][ny].visited
            ):
                neighbors.append((d, nx, ny))

        if neighbors:
            d, nx, ny = random.choice(neighbors)

            grid[cx][cy].walls.remove(d)
            grid[nx][ny].walls.remove(OPPOSITE[d])

            grid[nx][ny].visited = True
            stack.append((nx, ny))

        else:
            stack.pop()

    # Create loops and eliminate dead ends
    remove_all_dead_ends(grid)

    return grid


def count_openings(cell):
    return 4 - len(cell.walls)


def remove_all_dead_ends(grid):
    """
    Continues punching holes until no dead ends remain.
    Produces a highly looped vascular-style network.
    """

    cols = len(grid)
    rows = len(grid[0])

    changed = True

    while changed:
        changed = False

        for x in range(cols):
            for y in range(rows):

                cell = grid[x][y]

                # dead end = only one exit
                if count_openings(cell) == 1:

                    candidates = []

                    for d, (dx, dy) in DIRS.items():

                        nx = x + dx
                        ny = y + dy

                        if (
                            d in cell.walls and
                            0 <= nx < cols and
                            0 <= ny < rows
                        ):
                            candidates.append((d, nx, ny))

                    if candidates:

                        d, nx, ny = random.choice(candidates)

                        cell.walls.remove(d)
                        grid[nx][ny].walls.remove(OPPOSITE[d])

                        changed = True


def maze_to_walls(grid, cell_size, offset_x, offset_y):
    """
    Converts maze grid into pygame.Rect wall segments.
    """

    walls = []

    cols = len(grid)
    rows = len(grid[0])

    thickness = 15

    for x in range(cols):
        for y in range(rows):

            cell = grid[x][y]

            cx = offset_x + x * cell_size
            cy = offset_y + y * cell_size

            if "N" in cell.walls:
                walls.append(
                    pygame.Rect(
                        cx,
                        cy,
                        cell_size,
                        thickness
                    )
                )

            if "S" in cell.walls:
                walls.append(
                    pygame.Rect(
                        cx,
                        cy + cell_size,
                        cell_size,
                        thickness
                    )
                )

            if "W" in cell.walls:
                walls.append(
                    pygame.Rect(
                        cx,
                        cy,
                        thickness,
                        cell_size
                    )
                )

            if "E" in cell.walls:
                walls.append(
                    pygame.Rect(
                        cx + cell_size,
                        cy,
                        thickness,
                        cell_size
                    )
                )

    return walls