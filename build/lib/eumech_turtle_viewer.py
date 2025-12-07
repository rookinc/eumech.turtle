#!/usr/bin/env python3
"""EuMech Turtle Viewer (standalone)

Usage (after pip install .):
    eumech-turtle --trace trace.json

Usage (direct):
    python eumech_turtle_viewer.py --trace trace.json
"""

import argparse
import json
import math
from pathlib import Path
from typing import Any, Dict, List, Union

import turtle

State = Dict[str, Any]


def load_trace(path: Union[str, Path]) -> List[State]:
    """Load a EuMech trace from JSON.

    Supported formats:

    1) Object with "states" key:
       {
         "engine": "eumech",
         "version": "1.0.0",
         "states": [ ... ]
       }

    2) Plain list:
       [
         { "step": 0, "coords": [...] },
         { "step": 1, "coords": [...] }
       ]
    """
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


class EuMechTurtleViewer:
    def __init__(
        self,
        states: List[State],
        scale: float = 1.0,
        pen_size: int = 2,
        speed: int = 0,
        dot_every: int = 0,
    ) -> None:
        self.states = states
        self.scale = scale
        self.pen_size = pen_size
        self.speed = speed
        self.dot_every = dot_every

        # Setup screen
        self.screen = turtle.Screen()
        self.screen.title("EuMech Turtle Viewer")
        self.screen.bgcolor("white")

        # Ensure we can use 0–1 float colors
        turtle.colormode(1.0)

        # Main drawing turtle
        self.t = turtle.Turtle()
        self.t.hideturtle()
        self.t.speed(speed)  # 0 = fastest
        self.t.pensize(pen_size)
        self.t.penup()

    def _project(self, coords: List[float]) -> tuple[float, float]:
        """Map 5D coords -> 2D screen coords.

        Default: x = coords[0], y = coords[1], both scaled.
        """
        x = coords[0] * self.scale
        y = coords[1] * self.scale
        return x, y

    def _color_for_state(self, state: State) -> tuple[float, float, float]:
        """Simple coloring scheme based on vector norm of coords."""
        coords = state["coords"]
        norm = math.sqrt(sum(c * c for c in coords))
        shade = min(1.0, norm / 10.0)  # clamp to [0,1]
        # purple-ish gradient: low norm = dark purple, high = light magenta
        return (shade, 0.0, 1.0 - shade)

    def draw(self) -> None:
        """Draw the full trace using turtle graphics."""
        if not self.states:
            print("No states to draw.")
            return

        # Start at first state without drawing
        first = self.states[0]
        x0, y0 = self._project(first["coords"])
        self.t.penup()
        self.t.goto(x0, y0)
        self.t.pendown()
        self.t.showturtle()

        for i, state in enumerate(self.states[1:], start=1):
            coords = state["coords"]
            x, y = self._project(coords)

            # Color pen
            r, g, b = self._color_for_state(state)
            self.t.pencolor(r, g, b)

            self.t.goto(x, y)

            step = state.get("step", i)
            if self.dot_every and (step % self.dot_every == 0):
                self.t.dot(self.pen_size * 2)

        turtle.done()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="EuMech Turtle Viewer — standalone trace visualizer"
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
        help="Scale factor for coords → screen (default: 1.0)",
    )
    parser.add_argument(
        "--pen-size",
        type=int,
        default=2,
        help="Pen thickness (default: 2)",
    )
    parser.add_argument(
        "--speed",
        type=int,
        default=0,
        help="Turtle speed 0–10 (0 = fastest, default: 0)",
    )
    parser.add_argument(
        "--dot-every",
        type=int,
        default=0,
        help="Draw a dot every N steps (0 = never)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    states = load_trace(args.trace)
    viewer = EuMechTurtleViewer(
        states=states,
        scale=args.scale,
        pen_size=args.pen_size,
        speed=args.speed,
        dot_every=args.dot_every,
    )
    viewer.draw()


if __name__ == "__main__":
    main()
