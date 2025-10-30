# Pac-Man (pygame)

A lightweight Pac-Man-inspired arcade game implemented in Python with
[pygame](https://www.pygame.org/).

## Features

- Classic pellet-collecting gameplay with a fixed maze layout.
- Keyboard controls (arrow keys) to guide Pac-Man.
- Two roaming ghosts with simple AI to chase and bounce around the maze.
- Score tracking and win/lose messages.

## Requirements

- Python 3.8+
- pygame (installed automatically by the setup script)

## Setting up a virtual environment

Create an isolated environment with the Python interpreter of your choice (3.8+):

```bash
python setup_env.py
```

This generates a `.venv` folder and installs the dependencies listed in
`requirements.txt`. If you want to rebuild the environment from scratch, pass
`--recreate` when running the script.

Activate the environment before running the game:

```bash
source .venv/bin/activate  # On Windows use: .venv\Scripts\activate
```

## Running the game

```bash
python pacman.py
```

Press the arrow keys to move. Collect all pellets to win while avoiding the
ghosts. Press `Esc` or close the window to exit.
