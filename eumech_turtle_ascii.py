#!/usr/bin/env python3
"""
EuMech Turtle Viewer — ASCII / terminal mode

Usage:
    python eumech_turtle_ascii.py --trace file.json [options]

Supports:
  1. Kernel Traces:
        { "states": [ {"coords": [x, y, ...], "step": n}, ... ] }

  2. X-Mode Spiral Traces:
        {
          "triangles": [
             {"coords": [x1,y1,x2,y2,x3,y3], "step": n},
             ...
          ]
        }

In X-mode traces, each triangle is reduced to its *centroid*
so the viewer plots a single turtle path.
"""

import argparse
import json
import shutil
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple, Union

State = Dict[str, Any]


# ---------------------------------------------------------------------------
# TRACE LOADER — supports kernel traces & X-mode spiral traces
# ---------------------------------------------------------------------------
def load_trace(path: Union[str, Path]) -> List[State]:
    """Load a EuMech trace from JSON and return states with coords[0:2].

    Allowed formats:

    1. {"states": [ {...}, ... ]}
       → coords[0], coords[1] are used directly

    2. {"triangles": [ {...}, ... ]}
       → convert each triangle to centroid (x,y)

    3. [ {...}, ... ]
       → treated as states already
    """
    path = Path(path)
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    # -----------------------------------------------------
    # CASE 1: kernel-style {"states": [...]}
    # -----------------------------------------------------
    if isinstance(data, dict) and "states" in data:
        states = data["states"]

    # -----------------------------------------------------
    # CASE 2: X-mode-style {"triangles": [...]}
    # -----------------------------------------------------
    elif isinstance(data, dict) and "triangles" in data:
        triangles = data["triangles"]
        if not isinstance(triangles, list):
            raise ValueError("'triangles' must be a list.")

        states = []
        for idx, tri in enumerate(triangles):
            if "coords" not in tri:
                raise ValueError(f"Triangle {idx} missing 'coords'.")
            coords = tri["coords"]

            if not isinstance(coords, list) or len(coords) < 6:
                raise ValueError(
                    f"Triangle {idx} has invalid 'coords' — expected at least 6 numbers."
                )

            # Extract first triangle only (3 vertices)
            x1, y1, x2, y2, x3, y3 = coords[:6]

            # Compute centroid
            cx = (x1 + x2 + x3) / 3.0
            cy = (y1 + y2 + y3) / 3.0

            step = tri.get("step", idx)
            states.append({"step": step, "coords": [cx, cy]})

    # -----------------------------------------------------
    # CASE 3: raw list
    # -----------------------------------------------------
    elif isinstance(data, list):
        states = data

    else:
        raise ValueError(
            "Unrecognized trace format.\n"
            "Expected:\n"
            "  - list\n"
            "  - object with 'states'\n"
            "  - object with 'triangles'"
        )

    # -----------------------------------------------------
    # VALIDATE STATES
    # -----------------------------------------------------
    cleaned = []
    for idx, s in enumerate(states):
        if "coords" not in s:
            raise ValueError(f"State {idx} missing 'coords'.")
        coords = s["coords"]
        if not isinstance(coords, list) or len(coords) < 2:
            raise ValueError(f"State {idx}: coords must contain at least [x, y].")
        cleaned.append(s)

    if not cleaned:
        raise ValueError("Trace produced no usable states.")

    return cleaned


# ---------------------------------------------------------------------------
# PROJECTION + VIEWER
# ---------------------------------------------------------------------------
def compute_bounds(states: List[State], scale: float) -> Tuple[float, float, float, float]:
    xs = []
    ys = []
    for s in states:
        xs.append(s["coords"][0] * scale)
        ys.append(s["coords"][1] * scale)
    return min(xs), max(xs), min(ys), max(ys)


def project_point(
    x: float,
    y: float,
    bounds: Tuple[float, float, float, float],
    width: int,
    height: int,
) -> Tuple[int, int]:
    min_x, max_x, min_y, max_y = bounds

    if max_x == min_x:
        max_x = min_x + 1.0
    if max_y == min_y:
        max_y = min_y + 1.0

    nx = (x - min_x) / (max_x - min_x)
    ny = (y - min_y) / (max_y - min_y)

    gx = int(nx * (width - 1))
    gy = int((1.0 - ny) * (height - 1))  # inverted y
    return gx, gy


def clear_screen() -> None:
    print("\x1b[2J\x1b[H", end="")


def draw_frame(
    width: int,
    height: int,
    trail: List[List[bool]],
    turtle_pos: Tuple[int, int],
    step: int,
) -> None:
    clear_screen()

    grid = [[" " for _ in range(width)] for _ in range(height)]

    # Draw trail
    for j in range(height):
        for i in range(width):
            if trail[j][i]:
                grid[j][i] = "."

    # Draw turtle
    tx, ty = turtle_pos
    if 0 <= tx < width and 0 <= ty < height:
        grid[ty][tx] = "@"

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

    term_cols, term_rows = shutil.get_terminal_size((80, 24))
    width = min(max_width, term_cols)
    height = min(max_height, max(4, term_rows - 2))

    bounds = compute_bounds(states, scale)

    trail = [[False for _ in range(width)] for _ in range(height)]

    for idx, state in enumerate(states):
        if skip > 1 and (idx % skip != 0):
            continue

        x = state["coords"][0] * scale
        y = state["coords"][1] * scale
        gx, gy = project_point(x, y, bounds, width, height)

        if 0 <= gx < width and 0 <= gy < height:
            trail[gy][gx] = True

        if static_only:
            continue

        step = state.get("step", idx)
        draw_frame(width, height, trail, (gx, gy), step)
        time.sleep(delay)

    # Final static render
    if static_only:
        x = states[-1]["coords"][0] * scale
        y = states[-1]["coords"][1] * scale
        gx, gy = project_point(x, y, bounds, width, height)
        step = states[-1].get("step", len(states) - 1)
        draw_frame(width, height, trail, (gx, gy), step)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="EuMech Turtle Viewer — ASCII / terminal"
    )
    parser.add_argument(
        "--trace", "-t",
        required=True,
        help="Path to EuMech trace.json (kernel or X-mode)",
    )
    parser.add_argument(
        "--scale", "-s",
        type=float,
        default=1.0,
        help="World scaling factor",
    )
    parser.add_argument(
        "--delay", "-d",
        type=float,
        default=0.05,
        help="Animation delay",
    )
    parser.add_argument("--static", action="store_true", help="Render final result only.")
    parser.add_argument("--max-width", type=int, default=80)
    parser.add_argument("--max-height", type=int, default=24)
    parser.add_argument("--skip", type=int, default=1)
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

