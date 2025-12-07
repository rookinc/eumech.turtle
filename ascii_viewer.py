#!/usr/bin/env python3
"""
Euclidean Arcade UI — auto-scaled for the current terminal.

Layout (top → bottom):

  [Scoreboard HUD]       (2 lines)
  [Euclidean Frame]      (N x N square, auto-chosen to fit screen)
  [Control Panel]        (2–3 lines)

The frame size is chosen at runtime so it fits your terminal vertically
and horizontally, which is especially important on a phone screen.
"""

from __future__ import annotations

import shutil
import sys
from dataclasses import dataclass
from typing import List


FILL_CHAR = " "


# ---------------------------------------------------------
# Terminal helpers
# ---------------------------------------------------------
def clear_screen() -> None:
    sys.stdout.write("\x1b[2J\x1b[H")
    sys.stdout.flush()


def get_terminal_size() -> tuple[int, int]:
    """Return (columns, lines) for the current terminal."""
    size = shutil.get_terminal_size(fallback=(80, 24))
    return size.columns, size.lines


# ---------------------------------------------------------
# Core Euclidean Frame
# ---------------------------------------------------------
class EuclideanFrame:
    def __init__(self, size: int):
        self.size = size
        self.field = self._empty_field()

    def _empty_field(self) -> List[List[str]]:
        return [[FILL_CHAR for _ in range(self.size)]
                for _ in range(self.size)]

    def reset(self) -> None:
        self.field = self._empty_field()

    def stamp(self, x: int, y: int, char: str) -> None:
        """Place a character inside the frame bounds."""
        if 0 <= x < self.size and 0 <= y < self.size:
            self.field[y][x] = char

    def write_text_center(self, msg: str) -> None:
        """Center text horizontally in the frame."""
        y = self.size // 2
        x_start = max(0, (self.size - len(msg)) // 2)
        for i, ch in enumerate(msg):
            x = x_start + i
            if 0 <= x < self.size:
                self.field[y][x] = ch

    def render_lines_centered(self, total_width: int) -> List[str]:
        """Render the frame as lines, centered within total_width."""
        left_pad = max(0, (total_width - self.size) // 2)
        right_pad = max(0, total_width - left_pad - self.size)

        lines: List[str] = []
        for row in self.field:
            core = "".join(row)
            line = (" " * left_pad) + core + (" " * right_pad)
            lines.append(line)
        return lines


# ---------------------------------------------------------
# Scoreboard HUD
# ---------------------------------------------------------
@dataclass
class ScoreBoard:
    score: int = 0
    lives: int = 3
    mode: str = "DEMO"
    frame_size: int = 0  # will be set at runtime

    def render_lines(self, width: int) -> List[str]:
        title = "EUCLIDEAN ARCADE"
        line1 = title.center(width)

        info = (
            f"SCORE: {self.score:06d}   "
            f"LIVES: {self.lives}   "
            f"MODE: {self.mode}   "
            f"FRAME: {self.frame_size}x{self.frame_size}"
        )
        line2 = info.ljust(width)

        return [line1, line2]


# ---------------------------------------------------------
# Control panel / widgets area
# ---------------------------------------------------------
@dataclass
class ControlPanel:
    def render_lines(self, width: int) -> List[str]:
        lines: List[str] = []
        lines.append("Controls (demo only, no input yet)".ljust(width))
        lines.append("A/D: rotate   W/S: thrust   SPACE: fire".ljust(width))
        lines.append("Q: quit".ljust(width))
        return lines


# ---------------------------------------------------------
# UI Orchestrator
# ---------------------------------------------------------
class EuclideanArcadeUI:
    def __init__(self):
        cols, rows = get_terminal_size()

        # Layout accounting
        hud_lines = 2
        panel_lines = 3
        padding = 2  # small extra breathing room

        # Vertical space available for the square frame
        available_for_frame = max(4, rows - (hud_lines + panel_lines + padding))

        # Choose a square frame that fits both width and height.
        # Clamp max to 40 so it doesn't get huge on big terminals.
        frame_size = min(40, cols, available_for_frame)

        self.screen_width = cols
        self.frame_size = frame_size

        self.frame = EuclideanFrame(size=frame_size)
        self.hud = ScoreBoard(frame_size=frame_size)
        self.panel = ControlPanel()

    def build_scene(self) -> List[str]:
        # Populate frame content
        self.frame.reset()
        self.frame.write_text_center("Hello, Euclidean Frame!")

        hud_lines = self.hud.render_lines(self.screen_width)
        frame_lines = self.frame.render_lines_centered(self.screen_width)
        panel_lines = self.panel.render_lines(self.screen_width)

        # Assemble: HUD, frame, panel — minimal spacers so it fits small screens
        lines: List[str] = []
        lines.extend(hud_lines)
        lines.extend(frame_lines)
        lines.append("")  # spacer before panel
        lines.extend(panel_lines)
        return lines

    def render(self) -> None:
        clear_screen()
        for line in self.build_scene():
            print(line)


# ---------------------------------------------------------
# Main entry
# ---------------------------------------------------------
def main() -> int:
    ui = EuclideanArcadeUI()
    ui.render()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
