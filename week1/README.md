# Week 1: Rigid Balls, Round Walls

Gravity integration and collision detection for rigid balls bouncing inside a
circular boundary.

**Due: EOD, 7th June 2026.**

## What's in this folder

- [`week1.pdf`](./week1.pdf): the assignment itself. Read it first, it's the
  authority on what the simulation has to do.
- [`main.py`](./main.py): the code template. It opens a window and draws the
  bowl, but none of the physics is there yet. There are two `TODO` blocks in the
  main loop for you to fill in, one for falling and bouncing off the wall, one
  for balls hitting each other. Everything else, the window, the drawing and the
  loop itself, is already wired up.

> Some people complained that the template made them feel like they didn't code it. **You are FREE to use ur own code and not use the template**, just make sure to get the simulation done. Using the template or not won't make a difference. The main thing that matters is the simulation.

## Setup

Open a terminal inside this folder, then run these three, one at a time:

```bash
uv init
uv add pygame numpy
uv run main.py
```

The first sets up the project, the second downloads pygame and numpy, and the
third starts the simulation. It takes a moment the first time around.

After this, only `uv run main.py` is needed.

Don't have uv yet? Install it first. On macOS or Linux:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

On Windows (PowerShell):

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Close the terminal and open a fresh one afterwards.

## What to do

1. Read `week1.pdf`.
2. Fill in the `TODO` blocks in `main.py`.
3. Jot down your answers to **Question 1** and **Question 2** as you go. Keep
   them somewhere in this folder, a text file is fine. You'll need them for your
   submission, and half a page is plenty.

## Accessing positions of the balls.

If you haven't worked with lists much, this is the part worth reading before you
start.

The template keeps the balls in two lists, `positions` and `velocities`. A list
is just an ordered collection of things, and you pull a thing out of it by its
position in the line, counting from zero:

```python
positions[0]    # the first ball
positions[1]    # the second ball
positions[2]    # the third, and so on
```

The two lists line up with each other. Ball number `i` has position
`positions[i]` and velocity `velocities[i]`, so index `0` refers to the same
ball in both.

Right now `NUM_PARTICLES` is `1`, so there is exactly one ball and
`positions[0]` is all you need. No loops required yet.

### Each entry is a pair of numbers

A position isn't a single number, it's an x and a y bundled together in a numpy
array:

```python
positions[0]        # something like [411.8  556.3]
positions[0][0]     # 411.8, the x
positions[0][1]     # 556.3, the y
```

You can work one component at a time if that feels clearer:

```python
positions[0][1] = positions[0][1] + velocities[0][1] * dt
```

Or you can do the maths on both at once, which is the nice thing about numpy
arrays. Adding two of them adds the x's and the y's for you, and multiplying by
a plain number scales both:

```python
positions[0] = positions[0] + velocities[0] * dt
```

Both lines do the same job. The second is shorter and reads closer to the maths
in the PDF.

Two more that will come in handy. Subtracting one position from another gives
you the arrow pointing from the second to the first, and `np.linalg.norm` gives
you the length of an arrow, so together they measure a distance:

```python
offset = positions[0] - BOWL_CENTER              # the arrow from centre to ball
distance = np.linalg.norm(positions[0] - BOWL_CENTER)   # how far out it is
```

### Once there is more than one ball

When you bump `NUM_PARTICLES` up, you'll want to do the same thing to every
ball rather than to `positions[0]` alone. `len(positions)` tells you how many
there are, and a loop walks through them:

```python
for i in range(len(positions)):
    # positions[i] and velocities[i] are the ball being handled this time round
```

For ball-to-ball collisions you need every *pair* of balls, which takes two
loops rather than one. Worth thinking about how to avoid checking the same pair
twice, and how to avoid checking a ball against itself.

Submission details will be announced separately, so don't worry about that part
for now.
