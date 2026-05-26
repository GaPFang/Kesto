"""Kesto puzzle editor — paint a grid, then save to puzzles.py."""
import re
import sys
import datetime
from pathlib import Path

import pygame

# ── palette (matches main.py) ─────────────────────────────────────────────────
BG            = (22, 23, 27)
GRID_BG       = (16, 17, 20)
CELL_EMPTY    = (34, 35, 40)
CELL_OBST     = (70, 70, 76)
CELL_ORANGE   = (240, 162, 48)
TARGET_BORDER = (91, 142, 230)
CELL_SOLVED   = (76, 175, 80)
TEXT_BRIGHT   = (240, 240, 245)
TEXT_DIM      = (90, 92, 100)
BTN_IDLE      = (42, 43, 50)
BTN_HOVER     = (58, 60, 68)

CELL_PX  = 56
GAP      = 4
GRID_PAD = 12
BORDER_R = 7
BORDER_W = 3
TOOLBAR_H = 54
BOTTOM_H  = 56

PUZZLES_PATH = Path(__file__).parent / "puzzles.py"

MODES       = ["obstacle", "orange", "target"]
MODE_LABELS = ["Obstacle  1", "Orange  2", "Target  3"]
MODE_COLORS = [CELL_OBST, CELL_ORANGE, TARGET_BORDER]


# ── helpers ───────────────────────────────────────────────────────────────────

def grid_dims(rows: int, cols: int) -> tuple[int, int]:
    w = GRID_PAD * 2 + cols * (CELL_PX + GAP) - GAP
    h = GRID_PAD * 2 + rows * (CELL_PX + GAP) - GAP
    return w, h


def window_size(rows: int, cols: int) -> tuple[int, int]:
    gw, gh = grid_dims(rows, cols)
    return max(500, gw + 40), TOOLBAR_H + gh + BOTTOM_H


def cell_at(mx: int, my: int, grid_x: int, grid_y: int,
            rows: int, cols: int) -> tuple[int, int] | None:
    """Return (row, col) for the cell under the mouse, or None."""
    ox = mx - grid_x - GRID_PAD
    oy = my - grid_y - GRID_PAD
    step = CELL_PX + GAP
    c, cx = divmod(ox, step)
    r, cy = divmod(oy, step)
    if 0 <= r < rows and 0 <= c < cols and cx < CELL_PX and cy < CELL_PX:
        return r, c
    return None


def fmt_coords(coords: set) -> str:
    return "[" + ",".join(f"({r},{c})" for r, c in sorted(coords)) + "]"


def save_puzzle(puzzle_id: str, rows: int, cols: int,
                obstacles: set, oranges: set, targets: set) -> None:
    entry = (
        f'    "{puzzle_id}": {{\n'
        f'        "rows": {rows},\n'
        f'        "cols": {cols},\n'
        f'        "obstacles": {fmt_coords(obstacles)},\n'
        f'        "oranges":   {fmt_coords(oranges)},\n'
        f'        "targets":   {fmt_coords(targets)},\n'
        f'    }},\n'
    )
    content = PUZZLES_PATH.read_text()
    pattern = rf'    "{re.escape(puzzle_id)}": \{{.*?\n    \}},\n'
    if re.search(pattern, content, re.DOTALL):
        content = re.sub(pattern, entry, content, flags=re.DOTALL)
    else:
        # Insert at the top of the PUZZLES dict
        content = re.sub(
            r"(PUZZLES: dict\[str, dict\] = \{\n)",
            r"\g<1>" + entry,
            content,
        )
    PUZZLES_PATH.write_text(content)


def apply_drag(pos: tuple, mode: str, action: str,
               obstacles: set, oranges: set, targets: set) -> None:
    """Paint or erase a single cell according to the ongoing drag action."""
    if action == "erase":
        obstacles.discard(pos)
        oranges.discard(pos)
        targets.discard(pos)
    elif action == "add":
        if mode == "obstacle":
            obstacles.add(pos)
            oranges.discard(pos)
            targets.discard(pos)
        elif mode == "orange":
            oranges.add(pos)
            obstacles.discard(pos)
        elif mode == "target":
            targets.add(pos)
            obstacles.discard(pos)
    elif action == "remove":
        if mode == "obstacle":
            obstacles.discard(pos)
        elif mode == "orange":
            oranges.discard(pos)
        elif mode == "target":
            targets.discard(pos)


def draw_button(surf: pygame.Surface, label: str,
                rect: pygame.Rect, color, font: pygame.font.Font) -> None:
    pygame.draw.rect(surf, color, rect, border_radius=16)
    txt = font.render(label, True, TEXT_BRIGHT)
    surf.blit(txt, txt.get_rect(center=rect.center))


# ── main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    rows, cols = 8, 8
    obstacles: set[tuple[int, int]] = set()
    oranges:   set[tuple[int, int]] = set()
    targets:   set[tuple[int, int]] = set()

    mode_idx    = 0
    today       = datetime.date.today().strftime("%Y%m%d")
    save_msg    = ""
    save_msg_ts = 0

    dragging    = False
    drag_btn    = 0
    drag_action = ""
    drag_seen: set[tuple[int, int]] = set()

    pygame.init()
    ww, wh = window_size(rows, cols)
    surf = pygame.display.set_mode((ww, wh))
    pygame.display.set_caption("Kesto – Puzzle Editor")
    clock = pygame.time.Clock()

    font_title = pygame.font.SysFont("Arial", 20, bold=True)
    font_sub   = pygame.font.SysFont("Arial", 12)
    font_btn   = pygame.font.SysFont("Arial", 13, bold=True)
    font_hint  = pygame.font.SysFont("Arial", 11)

    while True:
        mouse = pygame.mouse.get_pos()
        now   = pygame.time.get_ticks()
        mods  = pygame.key.get_mods()

        ww, wh = window_size(rows, cols)
        gw, gh = grid_dims(rows, cols)
        grid_x = (ww - gw) // 2
        grid_y = TOOLBAR_H + 4

        btn_y  = grid_y + gh + 12
        btn_h  = 30
        btn_w  = 116
        mode_rects = [
            pygame.Rect(14 + i * (btn_w + 6), btn_y, btn_w, btn_h)
            for i in range(len(MODES))
        ]
        save_rect  = pygame.Rect(ww - 108, btn_y, 94, btn_h)
        clear_rect = pygame.Rect(ww - 108 - 94 - 8, btn_y, 86, btn_h)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    mode_idx = 0
                elif event.key == pygame.K_2:
                    mode_idx = 1
                elif event.key == pygame.K_3:
                    mode_idx = 2
                elif event.key == pygame.K_s and (mods & (pygame.KMOD_CTRL | pygame.KMOD_META)):
                    save_puzzle(today, rows, cols, obstacles, oranges, targets)
                    save_msg    = f"Saved  #{today}"
                    save_msg_ts = now
                # Resize rows
                elif event.key == pygame.K_EQUALS and not (mods & pygame.KMOD_SHIFT):
                    rows = min(rows + 1, 16)
                    surf = pygame.display.set_mode(window_size(rows, cols))
                elif event.key == pygame.K_MINUS and not (mods & pygame.KMOD_SHIFT):
                    rows = max(rows - 1, 3)
                    obstacles = {p for p in obstacles if p[0] < rows}
                    oranges   = {p for p in oranges   if p[0] < rows}
                    targets   = {p for p in targets   if p[0] < rows}
                    surf = pygame.display.set_mode(window_size(rows, cols))
                # Resize cols (Shift + / -)
                elif event.key == pygame.K_EQUALS and (mods & pygame.KMOD_SHIFT):
                    cols = min(cols + 1, 16)
                    surf = pygame.display.set_mode(window_size(rows, cols))
                elif event.key == pygame.K_MINUS and (mods & pygame.KMOD_SHIFT):
                    cols = max(cols - 1, 3)
                    obstacles = {p for p in obstacles if p[1] < cols}
                    oranges   = {p for p in oranges   if p[1] < cols}
                    targets   = {p for p in targets   if p[1] < cols}
                    surf = pygame.display.set_mode(window_size(rows, cols))

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button in (1, 3):
                dragging  = True
                drag_btn  = event.button
                drag_seen = set()

                # Button clicks (only left)
                if event.button == 1:
                    for i, r in enumerate(mode_rects):
                        if r.collidepoint(mouse):
                            mode_idx = i
                    if save_rect.collidepoint(mouse):
                        save_puzzle(today, rows, cols, obstacles, oranges, targets)
                        save_msg    = f"Saved  #{today}"
                        save_msg_ts = now
                    if clear_rect.collidepoint(mouse):
                        obstacles.clear()
                        oranges.clear()
                        targets.clear()

                # Grid cell
                cell = cell_at(*mouse, grid_x, grid_y, rows, cols)
                if cell:
                    mode = MODES[mode_idx]
                    if event.button == 3:
                        drag_action = "erase"
                    elif mode == "obstacle":
                        drag_action = "remove" if cell in obstacles else "add"
                    elif mode == "orange":
                        drag_action = "remove" if cell in oranges else "add"
                    else:
                        drag_action = "remove" if cell in targets else "add"
                    apply_drag(cell, mode, drag_action, obstacles, oranges, targets)
                    drag_seen.add(cell)

            elif event.type == pygame.MOUSEBUTTONUP and event.button in (1, 3):
                dragging = False

            elif event.type == pygame.MOUSEMOTION and dragging:
                cell = cell_at(*mouse, grid_x, grid_y, rows, cols)
                if cell and cell not in drag_seen:
                    apply_drag(cell, MODES[mode_idx], drag_action,
                               obstacles, oranges, targets)
                    drag_seen.add(cell)

        # ── draw ─────────────────────────────────────────────────────────────
        surf.fill(BG)

        # Toolbar
        surf.blit(font_title.render("Puzzle Editor", True, TEXT_BRIGHT), (14, 12))
        surf.blit(font_sub.render(f"#{today}  ·  {rows}×{cols}", True, TEXT_DIM), (14, 38))
        resize_hint = font_sub.render(
            "+/−  rows     Shift +/−  cols", True, TEXT_DIM)
        surf.blit(resize_hint, (ww - resize_hint.get_width() - 14, 38))

        # Grid background
        pygame.draw.rect(surf, GRID_BG,
                         pygame.Rect(grid_x, grid_y, gw, gh), border_radius=14)

        # Cells
        for r in range(rows):
            for c in range(cols):
                x    = grid_x + GRID_PAD + c * (CELL_PX + GAP)
                y    = grid_y + GRID_PAD + r * (CELL_PX + GAP)
                rect = pygame.Rect(x, y, CELL_PX, CELL_PX)
                pos  = (r, c)

                if pos in obstacles:
                    pygame.draw.rect(surf, CELL_OBST, rect, border_radius=BORDER_R)
                elif pos in oranges:
                    pygame.draw.rect(surf, CELL_ORANGE, rect, border_radius=BORDER_R)
                    if pos in targets:
                        pygame.draw.rect(surf, TARGET_BORDER, rect,
                                         width=BORDER_W, border_radius=BORDER_R)
                elif pos in targets:
                    pygame.draw.rect(surf, CELL_EMPTY, rect, border_radius=BORDER_R)
                    pygame.draw.rect(surf, TARGET_BORDER, rect,
                                     width=BORDER_W, border_radius=BORDER_R)
                else:
                    pygame.draw.rect(surf, CELL_EMPTY, rect, border_radius=BORDER_R)

        # Mode buttons
        for i, (label, mrect) in enumerate(zip(MODE_LABELS, mode_rects)):
            active = i == mode_idx
            color  = MODE_COLORS[i] if active else (
                BTN_HOVER if mrect.collidepoint(mouse) else BTN_IDLE)
            draw_button(surf, label, mrect, color, font_btn)

        # Clear / Save buttons
        draw_button(surf, "Clear",
                    clear_rect,
                    BTN_HOVER if clear_rect.collidepoint(mouse) else BTN_IDLE,
                    font_btn)
        draw_button(surf, "Save  ⌘S",
                    save_rect,
                    BTN_HOVER if save_rect.collidepoint(mouse) else BTN_IDLE,
                    font_btn)

        # Bottom row: save feedback + hint
        hint_y = btn_y + btn_h + 8
        if save_msg and now - save_msg_ts < 2500:
            saved_surf = font_hint.render(save_msg, True, CELL_SOLVED)
            surf.blit(saved_surf, saved_surf.get_rect(centerx=ww // 2, top=hint_y))
        hint = font_hint.render(
            "Left-drag = paint   Right-drag = erase   1/2/3 = switch mode",
            True, TEXT_DIM)
        surf.blit(hint, hint.get_rect(centerx=ww // 2,
                                      top=hint_y + (14 if save_msg and now - save_msg_ts < 2500 else 0)))

        pygame.display.flip()
        clock.tick(60)


if __name__ == "__main__":
    main()
