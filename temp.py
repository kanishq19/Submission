"""Falling Sand Simulation — assignment template.

Your task: implement the physics inside ``SandSim.update()`` so that
sand and water behave like they do in real life.

  Sand  -> falls straight down; if blocked, slides diagonally downhill.
  Water -> falls like sand, but when it *can't* fall it spreads sideways.

Only SAND and WATER are required. Fire, smoke, walls, wood, etc. are a
bonus — add a new entry to :class:`Material`, a colour, and a rule.

Run it:  uv run python assignment/temp.py
"""

from __future__ import annotations

from enum import IntEnum

import numpy as np
import pygame


class Material(IntEnum):
    """Every cell in the grid holds one of these values.

    IntEnum means each name is also a normal integer, so a grid can be
    a plain NumPy array of numbers. EMPTY must stay 0 so that a fresh grid
    (which NumPy fills with zeros) starts out as empty space.
    """

    EMPTY = 0
    SAND = 1
    WATER = 2

    # Bonus materials
    WOOD = 3
    FIRE = 4
    SMOKE = 5


# The colour (R, G, B) drawn for each material.
PALETTE = {
    Material.EMPTY: (0, 0, 0),
    Material.SAND: (194, 178, 128),
    Material.WATER: (52, 120, 235),
    Material.WOOD: (120, 72, 35),
    Material.FIRE: (255, 80, 20),
    Material.SMOKE: (120, 120, 120),
}

# Turned into a NumPy array so that looking up a cell's colour is a single
# fast indexing operation: COLORS[grid] gives the RGB value of every cell.
_COLORS = np.array([PALETTE[m] for m in Material], dtype=np.uint8)

# One shared random generator for the whole program. Everything that needs
# a coin-flip (diagonal direction, which side to move) pulls from this.
_rng = np.random.default_rng()


class SandSim:
    """Holds the grid and does the physics + rendering.

    The grid is ``self._types``, a 2D NumPy array of shape (HEIGHT, WIDTH)
    where grid[y, x] is the material at row ``y`` (0 = top) and column
    ``x`` (0 = left).
    """

    def __init__(
        self,
        width: int,
        height: int,
        cell_size: int = 4,
        fps: int = 120
    ) -> None:
        self.cell_size = cell_size
        self.fps = fps
        self.brush = Material.SAND
        self.brush_radius = 2
        self.resize_cells(width, height)

    # ------------------------------------------------------------------ #
    # Grid lifecycle
    # ------------------------------------------------------------------ #
    def resize_cells(self, width: int, height: int) -> None:
        """Replace the grid with a fresh empty one of the given size."""
        self.width = int(width)
        self.height = int(height)

        # NumPy fills with zeros = Material.EMPTY. Good.
        self._types = np.zeros(
            (self.height, self.width),
            dtype=np.uint8
        )

        # Per-cell attributes.
        # Used for fire and smoke age.
        self._attrs = np.zeros(
            (self.height, self.width),
            dtype=np.uint16
        )

    def clear(self) -> None:
        """Reset every cell to empty space."""
        self._types[:] = 0
        self._attrs[:] = 0

    # ------------------------------------------------------------------ #
    # Painting (mouse input)
    # ------------------------------------------------------------------ #
    def paint_at(self, x: int, y: int) -> None:
        """Place the current brush material in a disc of cells at (x, y).

        ``x``/``y`` are in *grid* coordinates (screen pixels / cell_size).
        """
        r = self.brush_radius
        x0, x1 = max(0, x - r), min(self.width, x + r + 1)
        y0, y1 = max(0, y - r), min(self.height, y + r + 1)

        if x1 <= x0 or y1 <= y0:
            return

        # mgrid gives two grids of y- and x-coordinates over the block;
        # the `disc` mask keeps only cells within a circle of radius r.
        yy, xx = np.mgrid[y0:y1, x0:x1]
        disc = ((xx - x) ** 2 + (yy - y) ** 2) <= r * r

        xs, ys = xx[disc], yy[disc]

        self._types[ys, xs] = int(self.brush)

        # Newly painted fire/smoke starts at age 0.
        if self.brush == Material.FIRE or self.brush == Material.SMOKE:
            self._attrs[ys, xs] = 0
        else:
            self._attrs[ys, xs] = 0

    # ------------------------------------------------------------------ #
    # Physics
    # ------------------------------------------------------------------ #
    def update(self) -> None:
        """Advance the simulation by one tick.

        Rules:

        SAND:
            1. Falls straight down if possible.
            2. If blocked, slides diagonally down-left/down-right.
            3. Otherwise stays in place.

        WATER:
            1. Falls straight down if possible.
            2. If blocked, slides diagonally.
            3. If still blocked, spreads sideways.

        WOOD:
            - Does not move.
            - Does not age.
            - Can be ignited by nearby fire.

        FIRE:
            - Rises upward.
            - Spreads sideways.
            - Ages every tick.
            - Disappears after 60 ticks.
            - Has a 20% chance per neighbouring wood cell to ignite it.
            - If touching water, turns into smoke.

        SMOKE:
            - Rises upward.
            - Spreads sideways.
            - Ages every tick.
            - Disappears after 40 ticks.
        """

        G = self._types
        A = self._attrs

        G_new = G.copy()
        A_new = A.copy()

        # Random column order removes left/right bias.
        columns = np.random.permutation(self.width)

        # Process from bottom to top.
        for y in range(self.height - 1, -1, -1):
            for x in columns:

                material = G[y, x]

                # ------------------------------------------------------ #
                # SAND
                # ------------------------------------------------------ #
                if material == Material.SAND:

                    # Fall straight down.
                    if (
                        y + 1 < self.height
                        and G[y + 1, x] == Material.EMPTY
                        and G_new[y + 1, x] == Material.EMPTY
                    ):
                        G_new[y, x] = Material.EMPTY
                        G_new[y + 1, x] = Material.SAND

                    else:
                        # Try diagonal movement.
                        sides = [-1, 1]
                        _rng.shuffle(sides)

                        for dx in sides:
                            nx = x + dx

                            if (
                                0 <= nx < self.width
                                and y + 1 < self.height
                                and G[y + 1, nx] == Material.EMPTY
                                and G_new[y + 1, nx] == Material.EMPTY
                            ):
                                G_new[y, x] = Material.EMPTY
                                G_new[y + 1, nx] = Material.SAND
                                break

                # ------------------------------------------------------ #
                # WATER
                # ------------------------------------------------------ #
                elif material == Material.WATER:

                    moved = False

                    # Fall straight down.
                    if (
                        y + 1 < self.height
                        and G[y + 1, x] == Material.EMPTY
                        and G_new[y + 1, x] == Material.EMPTY
                    ):
                        G_new[y, x] = Material.EMPTY
                        G_new[y + 1, x] = Material.WATER
                        moved = True

                    # Slide diagonally.
                    if not moved:
                        sides = [-1, 1]
                        _rng.shuffle(sides)

                        for dx in sides:
                            nx = x + dx

                            if (
                                0 <= nx < self.width
                                and y + 1 < self.height
                                and G[y + 1, nx] == Material.EMPTY
                                and G_new[y + 1, nx] == Material.EMPTY
                            ):
                                G_new[y, x] = Material.EMPTY
                                G_new[y + 1, nx] = Material.WATER
                                moved = True
                                break

                    # Spread sideways.
                    if not moved:
                        sides = [-1, 1]
                        _rng.shuffle(sides)

                        for dx in sides:
                            nx = x + dx

                            if (
                                0 <= nx < self.width
                                and G[y, nx] == Material.EMPTY
                                and G_new[y, nx] == Material.EMPTY
                            ):
                                G_new[y, x] = Material.EMPTY
                                G_new[y, nx] = Material.WATER
                                moved = True
                                break

                # ------------------------------------------------------ #
                # WOOD
                # ------------------------------------------------------ #
                elif material == Material.WOOD:

                    # Wood never moves and never ages.
                    pass

                # ------------------------------------------------------ #
                # FIRE
                # ------------------------------------------------------ #
                elif material == Material.FIRE:

                    # Check the eight neighbouring cells for reactions.
                    touching_water = False

                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):

                            if dx == 0 and dy == 0:
                                continue

                            nx = x + dx
                            ny = y + dy

                            if not (
                                0 <= nx < self.width
                                and 0 <= ny < self.height
                            ):
                                continue

                            neighbour = G[ny, nx]

                            # Water quenches fire.
                            if neighbour == Material.WATER:
                                touching_water = True

                            # Fire can ignite wood with probability 0.2.
                            elif neighbour == Material.WOOD:
                                if _rng.random() < 0.2:
                                    G_new[ny, nx] = Material.FIRE
                                    A_new[ny, nx] = 0

                    # Water takes priority over movement.
                    if touching_water:
                        G_new[y, x] = Material.SMOKE
                        A_new[y, x] = 0
                        continue

                    # Increase fire age.
                    new_age = int(A[y, x]) + 1

                    # Fire disappears after 60 ticks.
                    if new_age >= 60:
                        G_new[y, x] = Material.EMPTY
                        A_new[y, x] = 0
                        continue

                    A_new[y, x] = new_age

                    moved = False

                    # Fire rises upward.
                    if (
                        y - 1 >= 0
                        and G[y - 1, x] == Material.EMPTY
                        and G_new[y - 1, x] == Material.EMPTY
                    ):
                        G_new[y, x] = Material.EMPTY
                        G_new[y - 1, x] = Material.FIRE
                        A_new[y - 1, x] = new_age
                        moved = True

                    # Fire spreads sideways if it cannot rise.
                    if not moved:
                        sides = [-1, 1]
                        _rng.shuffle(sides)

                        for dx in sides:
                            nx = x + dx

                            if (
                                0 <= nx < self.width
                                and G[y, nx] == Material.EMPTY
                                and G_new[y, nx] == Material.EMPTY
                            ):
                                G_new[y, x] = Material.EMPTY
                                G_new[y, nx] = Material.FIRE
                                A_new[nx * 0 + y, nx] = new_age
                                moved = True
                                break

                # ------------------------------------------------------ #
                # SMOKE
                # ------------------------------------------------------ #
                elif material == Material.SMOKE:

                    # Increase smoke age.
                    new_age = int(A[y, x]) + 1

                    # Smoke disappears after 40 ticks.
                    if new_age >= 40:
                        G_new[y, x] = Material.EMPTY
                        A_new[y, x] = 0
                        continue

                    A_new[y, x] = new_age

                    moved = False

                    # Smoke rises upward.
                    if (
                        y - 1 >= 0
                        and G[y - 1, x] == Material.EMPTY
                        and G_new[y - 1, x] == Material.EMPTY
                    ):
                        G_new[y, x] = Material.EMPTY
                        G_new[y - 1, x] = Material.SMOKE
                        A_new[y - 1, x] = new_age
                        moved = True

                    # Smoke spreads sideways if it cannot rise.
                    if not moved:
                        sides = [-1, 1]
                        _rng.shuffle(sides)

                        for dx in sides:
                            nx = x + dx

                            if (
                                0 <= nx < self.width
                                and G[y, nx] == Material.EMPTY
                                and G_new[y, nx] == Material.EMPTY
                            ):
                                G_new[y, x] = Material.EMPTY
                                G_new[y, nx] = Material.SMOKE
                                A_new[y, nx] = new_age
                                moved = True
                                break

        # Swap the grids.
        self._types = G_new
        self._attrs = A_new

    # ------------------------------------------------------------------ #
    # Rendering (boilerplate — nothing to do here)
    # ------------------------------------------------------------------ #
    def surface(self) -> pygame.Surface:
        """Snapshot the grid as a pygame.Surface, scaled up by cell_size.

        _COLORS[grid] turns the cell-material grid into a grid of RGB
        pixels in one shot. pygame expects the axes as (WIDTH, HEIGHT),
        numpy stores them as (HEIGHT, WIDTH), so transpose swaps them back.
        """
        rgb = _COLORS[self._types]

        surf = pygame.surfarray.make_surface(
            np.ascontiguousarray(np.transpose(rgb, (1, 0, 2)))
        )

        if self.cell_size > 1:
            surf = pygame.transform.scale(
                surf,
                (
                    self.width * self.cell_size,
                    self.height * self.cell_size
                )
            )

        return surf


def main() -> None:
    """Setup + event loop. Boilerplate — nothing to do here."""
    pygame.init()

    screen = pygame.display.set_mode(
        (800, 600),
        pygame.RESIZABLE
    )

    pygame.display.set_caption(
        "Falling Sand — "
        "1 sand, 2 water, 3 wood, 4 fire, 5 smoke, "
        "0 erase, [ ] brush, C clear"
    )

    clock = pygame.time.Clock()

    sim = SandSim(800 // 4, 600 // 4)

    running = True

    while running:

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:

                k = event.key

                if k == pygame.K_ESCAPE:
                    running = False

                elif k == pygame.K_1:
                    sim.brush = Material.SAND

                elif k == pygame.K_2:
                    sim.brush = Material.WATER

                elif k == pygame.K_3:
                    sim.brush = Material.WOOD

                elif k == pygame.K_4:
                    sim.brush = Material.FIRE

                elif k == pygame.K_5:
                    sim.brush = Material.SMOKE

                elif k in (pygame.K_0, pygame.K_e):
                    sim.brush = Material.EMPTY

                elif k == pygame.K_LEFTBRACKET:
                    sim.brush_radius = max(
                        1,
                        sim.brush_radius - 1
                    )

                elif k == pygame.K_RIGHTBRACKET:
                    sim.brush_radius = min(
                        40,
                        sim.brush_radius + 1
                    )

                elif k == pygame.K_c:
                    sim.clear()

            elif event.type == pygame.VIDEORESIZE:

                screen = pygame.display.set_mode(
                    event.size,
                    pygame.RESIZABLE
                )

                sim.resize_cells(
                    event.size[0] // sim.cell_size,
                    event.size[1] // sim.cell_size
                )

        if pygame.mouse.get_pressed()[0]:

            mx, my = pygame.mouse.get_pos()

            sim.paint_at(
                mx // sim.cell_size,
                my // sim.cell_size
            )

        sim.update()

        screen.blit(
            sim.surface(),
            (0, 0)
        )

        pygame.display.flip()

        clock.tick(sim.fps)

    pygame.quit()


if __name__ == "__main__":
    main()