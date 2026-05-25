"""Kesto puzzle game — interactive pygame UI."""
import sys
import pygame
from game import KestoGame
from puzzles import PUZZLES

# ── palette ──────────────────────────────────────────────────────────────────
BG           = (22, 23, 27)
GRID_BG      = (16, 17, 20)
CELL_EMPTY   = (34, 35, 40)
CELL_OBST    = (70, 70, 76)
CELL_ORANGE  = (240, 162, 48)
CELL_SOLVED  = (76, 175, 80)
TARGET_BORDER= (91, 142, 230)
TEXT_BRIGHT  = (240, 240, 245)
TEXT_DIM     = ( 90,  92, 100)
BTN_IDLE     = ( 42,  43,  50)
BTN_HOVER    = ( 58,  60,  68)

# ── layout ───────────────────────────────────────────────────────────────────
CELL        = 60        # cell size in px
GAP         = 5         # gap between cells
GRID_PAD    = 14        # padding inside grid background
BORDER_R    = 8         # cell corner radius
BORDER_W    = 3         # target border width

WIN_W       = 560
WIN_H       = 680


def cell_rect(grid_x: int, grid_y: int, row: int, col: int) -> pygame.Rect:
    x = grid_x + GRID_PAD + col * (CELL + GAP)
    y = grid_y + GRID_PAD + row * (CELL + GAP)
    return pygame.Rect(x, y, CELL, CELL)


def draw_grid(surf: pygame.Surface, game: KestoGame,
              grid_x: int, grid_y: int) -> None:
    grid_w = GRID_PAD * 2 + game.cols * (CELL + GAP) - GAP
    grid_h = GRID_PAD * 2 + game.rows * (CELL + GAP) - GAP
    pygame.draw.rect(surf, GRID_BG,
                     pygame.Rect(grid_x, grid_y, grid_w, grid_h),
                     border_radius=14)

    orange_set = set(game.oranges)

    for r in range(game.rows):
        for c in range(game.cols):
            rect = cell_rect(grid_x, grid_y, r, c)
            pos  = (r, c)

            is_orange   = pos in orange_set
            is_target   = pos in game.targets
            is_obstacle = pos in game.obstacles

            if is_obstacle:
                pygame.draw.rect(surf, CELL_OBST, rect, border_radius=BORDER_R)

            elif is_orange:
                color = CELL_SOLVED if game.solved else CELL_ORANGE
                pygame.draw.rect(surf, color, rect, border_radius=BORDER_R)
                if is_target:
                    pygame.draw.rect(surf, TARGET_BORDER, rect,
                                     width=BORDER_W, border_radius=BORDER_R)

            elif is_target:
                pygame.draw.rect(surf, CELL_EMPTY, rect, border_radius=BORDER_R)
                pygame.draw.rect(surf, TARGET_BORDER, rect,
                                 width=BORDER_W, border_radius=BORDER_R)

            else:
                pygame.draw.rect(surf, CELL_EMPTY, rect, border_radius=BORDER_R)


def draw_button(surf: pygame.Surface, label: str,
                rect: pygame.Rect, hovered: bool, font: pygame.font.Font) -> None:
    color = BTN_HOVER if hovered else BTN_IDLE
    pygame.draw.rect(surf, color, rect, border_radius=20)
    txt = font.render(label, True, TEXT_BRIGHT)
    surf.blit(txt, txt.get_rect(center=rect.center))


def main() -> None:
    puzzle_id = list(PUZZLES.keys())[0]
    game      = KestoGame(puzzle_id)

    pygame.init()
    surf  = pygame.display.set_mode((WIN_W, WIN_H))
    pygame.display.set_caption("Kesto")
    clock = pygame.time.Clock()

    font_title  = pygame.font.SysFont("Arial", 28, bold=True)
    font_sub    = pygame.font.SysFont("Arial", 13)
    font_moves  = pygame.font.SysFont("Arial", 26, bold=True)
    font_btn    = pygame.font.SysFont("Arial", 16)
    font_hint   = pygame.font.SysFont("Arial", 12)

    # Grid centering
    grid_w = GRID_PAD * 2 + game.cols * (CELL + GAP) - GAP
    grid_h = GRID_PAD * 2 + game.rows * (CELL + GAP) - GAP
    grid_x = (WIN_W - grid_w) // 2
    grid_y = 100

    # Buttons  (undo / reset)
    btn_size   = pygame.Rect(0, 0, 36, 36)
    btn_undo   = btn_size.copy(); btn_undo.topright   = (WIN_W - 14, 18)
    btn_reset  = btn_size.copy(); btn_reset.topright  = (btn_undo.left - 8, 18)
    moves_rect = pygame.Rect(0, 18, 50, 36)
    moves_rect.right = btn_reset.left - 12

    key_repeat_delay = 180   # ms before key-repeat kicks in
    key_repeat_rate  = 100   # ms between repeats
    key_held: dict[int, int] = {}   # key → time first pressed (ms)

    dir_map = {
        pygame.K_UP: "up", pygame.K_DOWN: "down",
        pygame.K_LEFT: "left", pygame.K_RIGHT: "right",
    }

    while True:
        mouse = pygame.mouse.get_pos()
        now   = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            elif event.type == pygame.KEYDOWN:
                if event.key in dir_map:
                    game.move(dir_map[event.key])
                    key_held[event.key] = now
                elif event.key == pygame.K_z:
                    game.undo()
                elif event.key == pygame.K_r:
                    game.reset()

            elif event.type == pygame.KEYUP:
                key_held.pop(event.key, None)

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if btn_undo.collidepoint(mouse):
                    game.undo()
                elif btn_reset.collidepoint(mouse):
                    game.reset()

        # Key-repeat for held arrow keys
        for key, first_time in list(key_held.items()):
            elapsed = now - first_time
            if elapsed >= key_repeat_delay:
                repeats = (elapsed - key_repeat_delay) // key_repeat_rate
                expected_time = first_time + key_repeat_delay + repeats * key_repeat_rate
                if now >= expected_time:
                    game.move(dir_map[key])
                    key_held[key] = first_time  # keep base time; next check advances

        # ── draw ─────────────────────────────────────────────────────────────
        surf.fill(BG)

        # Title
        t = font_title.render("Kesto", True, TEXT_BRIGHT)
        surf.blit(t, (18, 18))
        s = font_sub.render(f"#{puzzle_id}", True, TEXT_DIM)
        surf.blit(s, (20, 52))

        # Move counter
        m = font_moves.render(str(game.moves), True, TEXT_BRIGHT)
        surf.blit(m, m.get_rect(midright=(moves_rect.right, moves_rect.centery)))

        # Buttons
        draw_button(surf, "↩", btn_undo,  btn_undo.collidepoint(mouse),  font_btn)
        draw_button(surf, "↺", btn_reset, btn_reset.collidepoint(mouse), font_btn)

        draw_grid(surf, game, grid_x, grid_y)

        # Status / hint bar
        status_y = grid_y + grid_h + 18
        if game.solved:
            msg = font_moves.render("Solved!", True, CELL_SOLVED)
            surf.blit(msg, msg.get_rect(centerx=WIN_W // 2, top=status_y))
        else:
            hint = font_hint.render(
                "Arrow keys  |  Z = undo  |  R = reset",
                True, TEXT_DIM)
            surf.blit(hint, hint.get_rect(centerx=WIN_W // 2, top=status_y))

        pygame.display.flip()
        clock.tick(60)


if __name__ == "__main__":
    main()
