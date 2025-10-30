"""Simple Pac-Man clone built with pygame.

Use the arrow keys to control Pac-Man. Collect all pellets while avoiding
ghosts. If a ghost touches Pac-Man the game ends. Clearing all pellets wins the
round. Close the window or press Escape to quit.
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence, Set, Tuple

import pygame

# --- Configuration constants -------------------------------------------------

TILE_SIZE = 24
PLAYER_SPEED = 2
GHOST_SPEED = 2
GHOST_TURN_COOLDOWN = 30  # frames
FPS = 60

LEVEL_LAYOUT: Sequence[str] = (
    "###################",
    "#.................#",
    "#.###.#####.###.#.#",
    "#.#.#.....#.#.#.#.#",
    "#.#.#.###.#.#.#.#.#",
    "#.#...#G#...#...#.#",
    "#.###.#.#.#.#.###.#",
    "#.....#.#.#.#.....#",
    "#####.#.#.#.#.#####",
    "#.....#.#.#.#.....#",
    "#.###.#.#.#.#.###.#",
    "#.#...#...#...#.#.#",
    "#.#.#.###P###.#.#.#",
    "#.#.#.#.....#.#.#.#",
    "#.#.#.#.###.#.#.#.#",
    "#.#.#.#.#.#.#.#.#.#",
    "#G..#...#.#...#..G#",
    "#.###.###.###.###.#",
    "#.................#",
    "###################",
)

# --- Helper data structures --------------------------------------------------


@dataclass
class Sprite:
    """Base class for simple rectangle-based sprites."""

    rect: pygame.Rect
    color: pygame.Color

    def draw(self, surface: pygame.Surface) -> None:
        pygame.draw.rect(surface, self.color, self.rect)


class Player(Sprite):
    def __init__(self, position: Tuple[int, int]) -> None:
        rect = pygame.Rect(position[0], position[1], TILE_SIZE, TILE_SIZE)
        super().__init__(rect, pygame.Color("yellow"))
        self.direction = pygame.Vector2(0, 0)
        self.next_direction = pygame.Vector2(0, 0)
        self.speed = PLAYER_SPEED

    def set_direction(self, direction: pygame.Vector2) -> None:
        self.next_direction = direction

    def can_move(self, direction: pygame.Vector2, walls: Iterable[pygame.Rect]) -> bool:
        if direction.length_squared() == 0:
            return False

        test_rect = self.rect.move(direction.x, direction.y)
        for wall in walls:
            if test_rect.colliderect(wall):
                return False
        return True

    def update(self, walls: Iterable[pygame.Rect]) -> None:
        if self.can_move(self.next_direction * self.speed, walls):
            self.direction = self.next_direction
        if not self.can_move(self.direction * self.speed, walls):
            return
        self.move(self.direction, walls)

    def move(self, direction: pygame.Vector2, walls: Iterable[pygame.Rect]) -> None:
        for _ in range(self.speed):
            if direction.x:
                step = pygame.Vector2(direction.x / abs(direction.x), 0)
            elif direction.y:
                step = pygame.Vector2(0, direction.y / abs(direction.y))
            else:
                step = pygame.Vector2(0, 0)

            if not step.length_squared():
                return

            next_rect = self.rect.move(step.x, step.y)
            if any(next_rect.colliderect(wall) for wall in walls):
                return
            self.rect = next_rect


class Ghost(Sprite):
    def __init__(self, position: Tuple[int, int]) -> None:
        rect = pygame.Rect(position[0], position[1], TILE_SIZE, TILE_SIZE)
        super().__init__(rect, pygame.Color("red"))
        self.direction = random.choice([
            pygame.Vector2(1, 0),
            pygame.Vector2(-1, 0),
            pygame.Vector2(0, 1),
            pygame.Vector2(0, -1),
        ])
        self.speed = GHOST_SPEED
        self.turn_cooldown = 0

    def update(self, walls: Iterable[pygame.Rect]) -> None:
        if self.turn_cooldown <= 0:
            self.choose_new_direction(walls)
            self.turn_cooldown = GHOST_TURN_COOLDOWN
        else:
            self.turn_cooldown -= 1

        self.move(self.direction, walls)

    def move(self, direction: pygame.Vector2, walls: Iterable[pygame.Rect]) -> None:
        for _ in range(self.speed):
            step = pygame.Vector2(direction.x, direction.y)
            next_rect = self.rect.move(step.x, step.y)
            if any(next_rect.colliderect(wall) for wall in walls):
                self.direction *= -1  # simple bounce
                return
            self.rect = next_rect

    def choose_new_direction(self, walls: Iterable[pygame.Rect]) -> None:
        possible_directions = [
            pygame.Vector2(1, 0),
            pygame.Vector2(-1, 0),
            pygame.Vector2(0, 1),
            pygame.Vector2(0, -1),
        ]
        random.shuffle(possible_directions)
        for direction in possible_directions:
            next_rect = self.rect.move(direction.x * TILE_SIZE, direction.y * TILE_SIZE)
            if not any(next_rect.colliderect(wall) for wall in walls):
                self.direction = direction
                return


# --- Level parsing -----------------------------------------------------------


def load_level(layout: Sequence[str]) -> Tuple[List[pygame.Rect], Set[Tuple[int, int]], Tuple[int, int], List[Tuple[int, int]]]:
    walls: List[pygame.Rect] = []
    pellets: Set[Tuple[int, int]] = set()
    player_start = (0, 0)
    ghost_starts: List[Tuple[int, int]] = []

    for y, row in enumerate(layout):
        for x, char in enumerate(row):
            rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
            if char == "#":
                walls.append(rect)
            elif char == ".":
                pellets.add((x, y))
            elif char.upper() == "P":
                player_start = (rect.x, rect.y)
            elif char.upper() == "G":
                ghost_starts.append((rect.x, rect.y))
            elif char == "-":
                # Horizontal tunnel: treat as pellet-free empty space
                continue

    # If no explicit player start marker, use first open tile
    if player_start == (0, 0):
        for x, y in pellets:
            player_start = (x * TILE_SIZE, y * TILE_SIZE)
            pellets.discard((x, y))
            break

    if not ghost_starts:
        ghost_starts.append(player_start)

    return walls, pellets, player_start, ghost_starts


# --- Drawing helpers ---------------------------------------------------------


def draw_grid(
    surface: pygame.Surface,
    layout: Sequence[str],
    pellets: Set[Tuple[int, int]],
) -> None:
    walls_color = pygame.Color(33, 33, 222)

    for y, row in enumerate(layout):
        for x, char in enumerate(row):
            rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
            if char == "#":
                pygame.draw.rect(surface, walls_color, rect)

    pellet_color = pygame.Color(255, 255, 102)
    for x, y in pellets:
        rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
        pygame.draw.circle(surface, pellet_color, rect.center, TILE_SIZE // 8)


# --- Game loop ---------------------------------------------------------------


def run() -> None:
    pygame.init()
    walls, pellets, player_start, ghost_starts = load_level(LEVEL_LAYOUT)
    width = len(LEVEL_LAYOUT[0]) * TILE_SIZE
    height = len(LEVEL_LAYOUT) * TILE_SIZE
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("Pac-Man (pygame)")
    clock = pygame.time.Clock()

    player = Player(player_start)
    ghosts = [Ghost(pos) for pos in ghost_starts]

    font_path = Path(pygame.font.get_default_font())
    font = pygame.font.Font(font_path, 18)
    large_font = pygame.font.Font(font_path, 32)

    running = True
    game_over = False
    win = False
    score = 0

    while running:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_LEFT:
                    player.set_direction(pygame.Vector2(-1, 0))
                elif event.key == pygame.K_RIGHT:
                    player.set_direction(pygame.Vector2(1, 0))
                elif event.key == pygame.K_UP:
                    player.set_direction(pygame.Vector2(0, -1))
                elif event.key == pygame.K_DOWN:
                    player.set_direction(pygame.Vector2(0, 1))

        if not game_over:
            player.update(walls)
            for ghost in ghosts:
                ghost.update(walls)

            player_tile = (player.rect.centerx // TILE_SIZE, player.rect.centery // TILE_SIZE)
            if player_tile in pellets:
                pellets.remove(player_tile)
                score += 10
                if not pellets:
                    win = True
                    game_over = True

            for ghost in ghosts:
                if player.rect.colliderect(ghost.rect):
                    game_over = True
                    win = False
                    break

        # Drawing
        screen.fill((0, 0, 0))
        draw_grid(screen, LEVEL_LAYOUT, pellets)
        for ghost in ghosts:
            ghost.draw(screen)
        player.draw(screen)

        score_surface = font.render(f"Score: {score}", True, pygame.Color("white"))
        screen.blit(score_surface, (10, height - 30))

        if game_over:
            message = "You Win!" if win else "Game Over"
            text_surface = large_font.render(message, True, pygame.Color("white"))
            text_rect = text_surface.get_rect(center=(width // 2, height // 2))
            screen.blit(text_surface, text_rect)

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    run()
