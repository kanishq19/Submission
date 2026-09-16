# 2D version of bouncingball.py. pos/vel/g are numpy [x, y] arrays, so one
# expression updates both axes. See README.md for the numpy notes and the maths.

import numpy as np
import pygame

pygame.init()

W, H = 600, 600
screen = pygame.display.set_mode((W, H))
clock = pygame.time.Clock()

center = np.array([W / 2, H / 2])
R = 250

pos = center.copy().astype(float)  # copy: else pos and center are the same array
vel = np.random.uniform(-200, 200, 2)
g = np.array([0, 900])  # no x pull; +y is down in screen coords

r = 12

running = True

while running:
    dt = clock.tick(60) / 1000

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # fill up

    pos += vel * dt

    d = pos - center             # arena centre -> ball centre
    distance = np.linalg.norm(d) # sqrt(dx^2 + dy^2)

    if (distance + r > R):  # outer edge past the wall

        # normal
        n = d/distance # gives unit normal vector
    
        # offset correction
        # overshoot, undone along the inward normal so the ball ends
        # the frame exactly touching the wall
        offset = distance + r - R
        pos -= n * offset

       
        vel -= 2 * np.dot(vel, n) * n  # v' = v - 2(v.n)n

    vel += g * dt

    screen.fill("black")
    pygame.draw.circle(screen, "white", center.astype(int), R, 2)
    pygame.draw.circle(screen, "red", pos.astype(int), r)

    pygame.display.flip()

pygame.quit()