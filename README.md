# 🐢 EuMech Turtle Viewer

Standalone turtle viewer for **EuMech** traces.

This app is **not** the EuMech engine.  
It only reads a `trace.json` file produced by EuMech and visualizes the path
using Python's `turtle` graphics.

---

## Install (local)

From inside this directory:

```bash
pip install .
```

This will install a command:

```bash
eumech-turtle
```

---

## Usage

First, generate a EuMech trace on a system that has `eumech` installed, e.g.:

```bash
eumech run --config path/to/config.json --out trace.json
```

Then run the turtle viewer:

```bash
eumech-turtle --trace trace.json
```

Options:

```bash
eumech-turtle --trace trace.json \
              --scale 50 \
              --speed 0 \
              --pen-size 2 \
              --dot-every 10
```

- `--trace` / `-t`  – path to the trace file (JSON)
- `--scale` / `-s`  – multiply coordinates before drawing
- `--speed`         – turtle speed 0–10 (0 = fastest)
- `--pen-size`      – line thickness
- `--dot-every`     – draw a dot every N steps (0 = never)

---

## Trace format

The viewer accepts either:

```json
{
  "engine": "eumech",
  "version": "1.0.0",
  "states": [
    { "step": 0, "coords": [1.0, 1.0, 1.0, 1.0, 1.0] },
    { "step": 1, "coords": [1.1, 1.1, 1.1, 1.1, 1.1] }
  ]
}
```

or a bare list:

```json
[
  { "step": 0, "coords": [1.0, 1.0, 1.0, 1.0, 1.0] },
  { "step": 1, "coords": [1.1, 1.1, 1.1, 1.1, 1.1] }
]
```

Only `coords[0]` (x) and `coords[1]` (y) are used for drawing; the remaining
dimensions are still available for coloring / styling.

---

## Dev notes

This repo is deliberately simple:

- no dependency on the EuMech Python package
- standard library only (`json`, `argparse`, `turtle`, etc.)
- can be dropped onto any machine with Python and a GUI

You just need EuMech **somewhere** to generate `trace.json`.
