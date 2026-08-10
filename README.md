# OPTIEO / EOSSP — Native Desktop App

A pure PyQt6 desktop application (no browser/HTML/JS involved) — physics engine
and UI both live in Python, so there's no bridge to get out of sync.

## Run it
```bash
pip install -r requirements.txt
python main.py
```

## What changed from your uploaded files
Your project had two different, half-finished implementations mixed together:

1. `main.py` / `main_hybrid.py` / `ui.html` — a Qt **WebEngine** approach (Python
   backend + HTML/JS frontend via QWebChannel). This is the one your screenshots
   show running, and it was broken because the JS side never got built out to
   actually render the received data (mapping diagrams, charts, and the output
   panel were empty shells).
2. `model.py`, `theme.py`, `starfield.py`, `param_panel.py`, `output_grid.py`,
   `dependency.py`, `charts.py` — a **native PyQt6 widgets** approach. This one
   was already well-built (the dependency-diagram code in particular is close
   to your Visio reference) but had no `main_window.py` tying it together and
   no working entry point, so it had never actually been run end-to-end.

This build keeps approach #2 (native widgets) and finishes it:

- **`optieo/main_window.py`** (new) — the missing glue: sidebar nav, starfield
  background, and wiring so slider moves → `compute_all()` → dashboard,
  output cards, dependency diagrams, and charts all update together.
- **`optieo/widgets/dashboard.py`** (new) — the Overview page was completely
  missing. Added a painted (no external image/network dependency) animated
  Earth + orbiting satellite, live GSD/SNR/Revisit stat cards, and an animated
  mission-efficiency ring + breakdown bars.
- **`optieo/widgets/dependency.py`** (fixed) — `QGraphicsView.DragMode.ScrollHandDrag`
  was swallowing mouse clicks before they reached nodes, so clicking never
  highlighted anything; switched to `NoDrag` (scrollbars/wheel-zoom still work).
  Also added per-edge "bus lane" routing so parallel connectors fan out into
  distinguishable rows instead of stacking exactly on top of each other, plus
  tooltips, a Clear-selection button and a Fit-view button.
- **`optieo/widgets/charts.py`** (fixed) — `backend_qt5agg` hard-imports PyQt5
  and doesn't work under PyQt6; switched to the binding-agnostic `backend_qtagg`.
  Also fixed a bug where `ax.twinx()` was called on every single update without
  removing the previous twin axis, so the SNR axis and legend kept duplicating
  and stacking on top of itself on every slider move. Added a third live
  "Efficiency Breakdown" bar chart.
- **`optieo/model.py`** — added the `ENGINES` list (id/number/name/color per
  engine) the UI needs for tab labels; your compute engine itself was already
  correct and is untouched.
- Clicking an output card in **Outputs** now jumps straight to that metric's
  node in **Dependency Mapping**, pre-selected and highlighted.

## Pages
- **Overview** — animated hero + live headline metrics + efficiency gauge
- **Control Deck** — all 23 input sliders, grouped exactly like your workbook
- **Outputs** — 39 computed metrics as cards, one tab per engine
- **Dependency Mapping** — the family-tree diagrams, one tab per engine.
  Click any node (input *or* output) to highlight everything connected to it.
- **Charts** — Altitude/Aperture trade-off curves + live efficiency bars
