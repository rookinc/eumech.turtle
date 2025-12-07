#!/usr/bin/env python3
"""
EuMech Turtle Viewer — ASCII / terminal mode

Usage (after `pip install .`):
    eumech-turtle-ascii --trace trace.json

This does NOT use tkinter/turtle. It:
  - loads a EuMech trace
  - projects coords to a terminal-sized grid
  - animates the turtle as '@' with trail '.'
"""

import argparse
import json
import shutil
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple, Union

State = Dict[str, Any]


def load_trace(path: Union[str, Path]) -> List[State]:
    """Load a EuMech trace from JSON (same format as GUI viewer)."""
    path = Path(path)
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, dict) and "states" in data:
        states = data["states"]
    elif isinstance(data, list):
        states = data
    else:
        raise ValueError(
            "Unrecognized trace format. Expected list or object with 'states' key."
        )

    cleaned: List[State] = []
    for idx, s in enumerate(states):
        if "coords" not in s:
            raise ValueError(f"State {idx} missing 'coords'.")
        coords = s["coords"]
        if not isinstance(coords, list) or len(coords) < 2:
            raise ValueError(
                f"State {idx} has invalid 'coords': need at least [x, y]."
            )
        cleaned.append(s)

    if not cleaned:
        raise ValueError("Trace contains no states.")
    return cleaned


def compute_bounds(states: List[State], scale: float) -> Tuple[float, float, float, float]:
    """Return (min_x, max_x, min_y, max_y) after scaling."""
    xs: List[float] = []
    ys: List[float] = []
    for s in states:
        x = s["coords"][0] * scale
        y = s["coords"][1] * scale
        xs.append(x)
        ys.append(y)
    return min(xs), max(xs), min(ys), max(ys)


def project_point(
    x: float,
    y: float,
    bounds: Tuple[float, float, float, float],
    width: int,
    height: int,
) -> Tuple[int, int]:
    """Project (x,y) in world coords into integer grid coords."""
    min_x, max_x, min_y, max_y = bounds

    if max_x == min_x:
        max_x = min_x + 1.0
    if max_y == min_y:
        max_y = min_y + 1.0

    nx = (x - min_x) / (max_x - min_x)  # 0..1
    ny = (y - min_y) / (max_y - min_y)  # 0..1

    gx = int(nx * (width - 1))
    gy = int((1.0 - ny) * (height - 1))  # invert y for screen coordinates
    return gx, gy


def clear_screen() -> None:
    """ANSI clear + home."""
    print("\x1b[2J\x1b[H", end="")


def draw_frame(
    width: int,
    height: int,
    trail: List[List[bool]],
    turtle_pos: Tuple[int, int],
    step: int,
) -> None:
    """Render one frame of the ASCII world to the terminal."""
    clear_screen()

    grid = [[" " for _ in range(width)] for _ in range(height)]

    # trail as '.'
    for j in range(height):
        for i in range(width):
            if trail[j][i]:
                grid[j][i] = "."

    # turtle as '@'
    tx, ty = turtle_pos
    if 0 <= tx < width and 0 <= ty < height:
        grid[ty][tx] = "@"

    # print grid
    for row in grid:
        print("".join(row))

    print(f"\nstep: {step}")


def ascii_run(
    states: List[State],
    scale: float,
    delay: float,
    static_only: bool,
    max_width: int,
    max_height: int,
    skip: int,
) -> None:
    """Main animation loop."""
    # terminal size
    term_cols, term_rows = shutil.get_terminal_size((80, 24))
    width = min(max_width, term_cols)
    # reserve 2 rows for status
    height = min(max_height, max(4, term_rows - 2))

    bounds = compute_bounds(states, scale)

    # trail grid
    trail = [[False for _ in range(width)] for _ in range(height)]

    for idx, state in enumerate(states):
        if skip > 1 and (idx % skip != 0):
            continue

        x = state["coords"][0] * scale
        y = state["coords"][1] * scale
        gx, gy = project_point(x, y, bounds, width, height)

        # mark trail
        if 0 <= gx < width and 0 <= gy < height:
            trail[gy][gx] = True

        if static_only:
            continue

        step = state.get("step", idx)
        draw_frame(width, height, trail, (gx, gy), step)
        time.sleep(delay)

    if static_only:
        # final static frame
        gx, gy = project_point(
            states[-1]["coords"][0] * scale,
            states[-1]["coords"][1] * scale,
            bounds,
            width,
            height,
        )
        step = states[-1].get("step", len(states) - 1)
        draw_frame(width, height, trail, (gx, gy), step)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="EuMech Turtle Viewer — ASCII / terminal"
    )
    parser.add_argument(
        "--trace",
        "-t",
        required=True,
        help="Path to EuMech trace.json file",
    )
    parser.add_argument(
        "--scale",
        "-s",
        type=float,
        default=1.0,
        help="Scale factor for coords → world (default: 1.0)",
    )
    parser.add_argument(
        "--delay",
        "-d",
        type=float,
        default=0.05,
        help="Delay between frames in seconds (default: 0.05)",
    )
    parser.add_argument(
        "--static",
        action="store_true",
        help="Do not animate; render only final path.",
    )
    parser.add_argument(
        "--max-width",
        type=int,
        default=80,
        help="Maximum grid width (default: 80)",
    )
    parser.add_argument(
        "--max-height",
        type=int,
        default=24,
        help="Maximum grid height (default: 24)",
    )
    parser.add_argument(
        "--skip",
        type=int,
        default=1,
        help="Only draw every Nth state (default: 1 = all states)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    states = load_trace(args.trace)
    ascii_run(
        states=states,
        scale=args.scale,
        delay=args.delay,
        static_only=args.static,
        max_width=args.max_width,
        max_height=args.max_height,
        skip=args.skip,
    )


if __name__ == "__main__":
    main()
