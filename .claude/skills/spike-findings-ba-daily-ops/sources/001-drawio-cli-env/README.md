---
spike: 001
name: drawio-cli-env
type: standard
validates: "Given draw.io desktop on this Windows machine, when exporting a .drawio headless, then SVG/PNG files are produced without error"
verdict: VALIDATED
related: [002, 003]
tags: [drawio, render, cli, windows, bpmn, plugin-ba-make-diagram]
---

# Spike 001: draw.io CLI Environment

## What This Validates
Given draw.io desktop installed on this Windows machine, when `.drawio` is exported headless via the CLI, then SVG/PNG image files are produced without error. This is the kill-switch for the `ba-make-diagram` (BPMN) plugin — no working export CLI = no plugin.

## How to Run
```
DRAWIO="/c/Program Files/draw.io/draw.io.exe"
"$DRAWIO" -x -f svg -o hello.svg hello.drawio --no-sandbox
"$DRAWIO" -x -f png -s 2 -o hello.png hello.drawio --no-sandbox
```

## What to Expect
`hello.drawio -> hello.svg` line, exit 0, real SVG/PNG files containing the diagram text.

## Results
**VALIDATED.** draw.io.exe present at `C:\Program Files\draw.io\draw.io.exe`. Headless export succeeded (exit 0) for both SVG (14.5 KB) and PNG (13.6 KB, scale 2). PNG visually confirmed: two styled boxes + connecting arrow rendered correctly. `--no-sandbox` flag used; export completed well under the 90s timeout with no GUI interaction.

### Findings
- draw.io desktop is NOT on PATH — invoke by absolute path (`C:\Program Files\draw.io\draw.io.exe`). The plugin must resolve it via flag/env/known-paths, not assume PATH (consistent with CLAUDE.md render-CLI resolution chain).
- `-x -f <fmt> -o <out> <in> --no-sandbox` works headless on Windows. `-s 2` doubles resolution.
- Short flags (`-x -f -o -s`) confirmed working (long forms `--export --format --output --scale` equivalent per CLAUDE.md).
