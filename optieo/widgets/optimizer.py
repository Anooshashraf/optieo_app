"""Professional payload optimizer.

For every input parameter the user picks one of three modes:
  - Static  : a single fixed value (business as usual)
  - Range   : give a min/max; the tool sweeps it and plots how the key
              outputs respond across that range
  - Auto    : let the tool search this parameter's full allowed span itself
              and report back the value that gives the best feasible design

"Best" = highest overall Mission Efficiency Index (see model.efficiency)
among every design that satisfies the acceptance criteria the user set for
GSD / SNR / Revisit / Dynamic Range / Swath. If nothing satisfies every
criterion, the closest-to-feasible design (by efficiency) is still reported,
clearly flagged as not fully meeting the criteria.
"""

import matplotlib
matplotlib.use('QtAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
                              QFrame, QComboBox, QDoubleSpinBox, QCheckBox, QPushButton,
                              QScrollArea, QStackedWidget, QSizePolicy, QToolButton)

from .. import theme
from ..model import GROUPS, ALL_PARAMS, CRITERIA_OUTPUTS, run_optimizer, node_label, compute_all, efficiency


class ModeRow(QWidget):
    """One parameter's mode selector: Static value / Range / Auto."""

    def __init__(self, param, color, parent=None):
        super().__init__(parent)
        self.param = param
        outer = QVBoxLayout(self)
        outer.setContentsMargins(2, 5, 2, 5)
        outer.setSpacing(4)

        top = QHBoxLayout()
        name = QLabel(param['label'])
        name.setStyleSheet(f"color:{theme.TEXT}; font-weight:600; font-size:12px;")
        name.setFixedWidth(168)
        top.addWidget(name)

        self.combo = QComboBox()
        self.combo.addItems(["Static", "Range", "Auto (best-fit)"])
        self.combo.setFixedWidth(128)
        top.addWidget(self.combo)
        top.addStretch()
        outer.addLayout(top)

        self.stack = QStackedWidget()
        self.stack.setFixedHeight(34)

        # page 0: static single value
        static_page = QWidget()
        sp_lay = QHBoxLayout(static_page)
        sp_lay.setContentsMargins(0, 0, 0, 0)
        self.static_spin = QDoubleSpinBox()
        self.static_spin.setRange(param['min'], param['max'])
        self.static_spin.setDecimals(param.get('decimals', 2))
        self.static_spin.setSingleStep(param['step'])
        self.static_spin.setValue(param['def'])
        self.static_spin.setSuffix(f" {param['unit']}" if param['unit'] else "")
        sp_lay.addWidget(QLabel("value:"))
        sp_lay.addWidget(self.static_spin, 1)
        self.stack.addWidget(static_page)

        # page 1: range (lo/hi) -- also used for 'auto'
        range_page = QWidget()
        rp_lay = QHBoxLayout(range_page)
        rp_lay.setContentsMargins(0, 0, 0, 0)
        self.lo_spin = QDoubleSpinBox()
        self.hi_spin = QDoubleSpinBox()
        for sp, default in ((self.lo_spin, param['min']), (self.hi_spin, param['max'])):
            sp.setRange(param['min'], param['max'])
            sp.setDecimals(param.get('decimals', 2))
            sp.setSingleStep(param['step'])
            sp.setValue(default)
            sp.setSuffix(f" {param['unit']}" if param['unit'] else "")
        rp_lay.addWidget(QLabel("min:"))
        rp_lay.addWidget(self.lo_spin, 1)
        rp_lay.addWidget(QLabel("max:"))
        rp_lay.addWidget(self.hi_spin, 1)
        self.stack.addWidget(range_page)

        outer.addWidget(self.stack)
        border = QFrame()
        border.setFixedHeight(1)
        border.setStyleSheet(f"background:{theme.LINE};")
        outer.addWidget(border)

        self.combo.currentIndexChanged.connect(self._on_mode_change)

    def _on_mode_change(self, idx):
        self.stack.setCurrentIndex(0 if idx == 0 else 1)

    def set_static_value(self, v):
        self.static_spin.setValue(v)

    def config(self):
        idx = self.combo.currentIndex()
        if idx == 0:
            return {'mode': 'static', 'value': self.static_spin.value()}
        mode = 'range' if idx == 1 else 'auto'
        lo, hi = self.lo_spin.value(), self.hi_spin.value()
        if lo > hi:
            lo, hi = hi, lo
        return {'mode': mode, 'lo': lo, 'hi': hi}


class CriteriaRow(QWidget):
    def __init__(self, spec, parent=None):
        super().__init__(parent)
        self.spec = spec
        lay = QHBoxLayout(self)
        lay.setContentsMargins(2, 4, 2, 4)
        name = QLabel(spec['label'])
        name.setStyleSheet(f"color:{theme.TEXT}; font-weight:600; font-size:12px;")
        name.setFixedWidth(150)
        lay.addWidget(name)

        better = QLabel("(lower is better)" if spec['better'] == 'lower' else "(higher is better)")
        better.setStyleSheet(f"color:{theme.TEXT_FAINT}; font-size:10px;")
        better.setFixedWidth(96)
        lay.addWidget(better)

        self.min_chk = QCheckBox("min")
        self.min_spin = QDoubleSpinBox()
        self.min_spin.setRange(-1e9, 1e9)
        self.min_spin.setDecimals(3)
        self.min_spin.setEnabled(False)
        self.min_chk.toggled.connect(self.min_spin.setEnabled)
        lay.addWidget(self.min_chk)
        lay.addWidget(self.min_spin)

        self.max_chk = QCheckBox("max")
        self.max_spin = QDoubleSpinBox()
        self.max_spin.setRange(-1e9, 1e9)
        self.max_spin.setDecimals(3)
        self.max_spin.setEnabled(False)
        self.max_chk.toggled.connect(self.max_spin.setEnabled)
        lay.addWidget(self.max_chk)
        lay.addWidget(self.max_spin)
        lay.addWidget(QLabel(spec['unit']))
        lay.addStretch()

    def bounds(self):
        lo = self.min_spin.value() if self.min_chk.isChecked() else None
        hi = self.max_spin.value() if self.max_chk.isChecked() else None
        return lo, hi

    def set_reference_value(self, current_value):
        """Pre-fill the (currently unchecked) min/max spinboxes around the
        design's current value, so ticking the box starts from something
        meaningful instead of 0."""
        if not self.min_chk.isChecked():
            self.min_spin.setValue(current_value * 0.8 if self.spec['better'] == 'higher' else current_value)
        if not self.max_chk.isChecked():
            self.max_spin.setValue(current_value if self.spec['better'] == 'higher' else current_value * 1.3)


class CollapsibleSection(QFrame):
    def __init__(self, title, color, parent=None):
        super().__init__(parent)
        self.setProperty("role", "card")
        self.setStyleSheet(f"QFrame[role='card'] {{ border-left: 3px solid {color}; }}")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 10, 12, 10)
        header = QHBoxLayout()
        dot = QLabel("●")
        dot.setStyleSheet(f"color:{color}; font-size:10px;")
        header.addWidget(dot)
        lbl = QLabel(title)
        lbl.setStyleSheet(f"color:{theme.TEXT}; font-weight:700; font-size:13px;")
        header.addWidget(lbl)
        header.addStretch()
        self.toggle_btn = QToolButton()
        self.toggle_btn.setText("▾")
        self.toggle_btn.setStyleSheet(f"border:none; color:{theme.TEXT_DIM}; font-size:14px;")
        self.toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        header.addWidget(self.toggle_btn)
        outer.addLayout(header)
        self.body = QWidget()
        self.body_layout = QVBoxLayout(self.body)
        self.body_layout.setContentsMargins(0, 6, 0, 0)
        outer.addWidget(self.body)
        self.toggle_btn.clicked.connect(self._toggle)
        self._collapsed = False

    def _toggle(self):
        self._collapsed = not self._collapsed
        self.body.setVisible(not self._collapsed)
        self.toggle_btn.setText("▸" if self._collapsed else "▾")

    def add_row(self, w):
        self.body_layout.addWidget(w)


class OptimizerWidget(QWidget):
    #: emitted with the full best-design parameter dict when the user
    #: clicks "Apply best design to Control Deck"
    applyRequested = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.rows = {}
        self.crit_rows = {}
        self._last_result = None

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(16)

        # ---------------- left: parameter mode configuration ----------------
        left_panel = QFrame()
        left_panel.setProperty("role", "panel")
        left_panel.setMinimumWidth(440)
        left_panel.setMaximumWidth(520)
        left_v = QVBoxLayout(left_panel)
        left_v.setContentsMargins(16, 16, 16, 16)
        left_v.setSpacing(8)

        head = QHBoxLayout()
        h1 = QLabel("PARAMETER MODE")
        h1.setProperty("role", "tag")
        head.addWidget(h1)
        head.addStretch()
        left_v.addLayout(head)
        hint = QLabel("Static = fixed value · Range = sweep + graph it · Auto = let the optimizer pick it")
        hint.setWordWrap(True)
        hint.setStyleSheet(f"color:{theme.TEXT_FAINT}; font-size:10.5px; font-style:italic;")
        left_v.addWidget(hint)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        inner = QWidget()
        inner_lay = QVBoxLayout(inner)
        inner_lay.setContentsMargins(2, 2, 8, 2)
        for group in GROUPS:
            sec = CollapsibleSection(group['label'], group['color'])
            for p in group['params']:
                row = ModeRow(p, group['color'])
                sec.add_row(row)
                self.rows[p['k']] = row
            inner_lay.addWidget(sec)
        inner_lay.addStretch()
        scroll.setWidget(inner)
        left_v.addWidget(scroll, 1)
        root.addWidget(left_panel, 0)

        # ---------------- right: criteria, run, results ----------------
        right_col = QVBoxLayout()
        right_col.setSpacing(14)

        crit_frame = QFrame()
        crit_frame.setProperty("role", "panel")
        crit_lay = QVBoxLayout(crit_frame)
        crit_lay.setContentsMargins(20, 16, 20, 16)
        crit_lay.setSpacing(4)
        ct = QLabel("ACCEPTANCE CRITERIA")
        ct.setProperty("role", "tag")
        crit_lay.addWidget(ct)
        chint = QLabel("Optional — leave everything unticked to impose no constraints at all. Tick \u201cmin\u201d "
                        "and/or \u201cmax\u201d on a row to require it; the optimizer only calls a design "
                        "\u201cfeasible\u201d if it satisfies every box you've ticked below. Boxes are pre-filled "
                        "around your current design's own numbers as a starting point.")
        chint.setWordWrap(True)
        chint.setStyleSheet(f"color:{theme.TEXT_FAINT}; font-size:10.5px; font-style:italic;")
        crit_lay.addWidget(chint)
        for spec in CRITERIA_OUTPUTS:
            row = CriteriaRow(spec)
            crit_lay.addWidget(row)
            self.crit_rows[spec['k']] = row
        right_col.addWidget(crit_frame)

        run_row = QHBoxLayout()
        self.run_btn = QPushButton("Run Optimizer")
        self.run_btn.clicked.connect(self._run)
        run_row.addWidget(self.run_btn)
        self.apply_btn = QPushButton("Apply Best Design to Control Deck")
        self.apply_btn.setProperty("role", "ghost")
        self.apply_btn.setEnabled(False)
        self.apply_btn.clicked.connect(self._apply)
        run_row.addWidget(self.apply_btn)
        run_row.addStretch()
        self.status_lbl = QLabel("")
        self.status_lbl.setStyleSheet(f"color:{theme.TEXT_DIM}; font-size:11px;")
        run_row.addWidget(self.status_lbl)
        right_col.addLayout(run_row)

        # results: summary + best design table
        res_frame = QFrame()
        res_frame.setProperty("role", "panel")
        res_lay = QVBoxLayout(res_frame)
        res_lay.setContentsMargins(20, 16, 20, 16)
        res_lay.setSpacing(8)
        rt = QLabel("BEST DESIGN FOUND")
        rt.setProperty("role", "tag")
        res_lay.addWidget(rt)
        self.summary_lbl = QLabel("Configure parameter modes on the left, then click \u201cRun Optimizer\u201d.")
        self.summary_lbl.setWordWrap(True)
        self.summary_lbl.setStyleSheet(f"color:{theme.TEXT_DIM}; font-size:12px;")
        res_lay.addWidget(self.summary_lbl)
        self.result_grid = QGridLayout()
        self.result_grid.setHorizontalSpacing(24)
        self.result_grid.setVerticalSpacing(4)
        res_body = QHBoxLayout()
        res_body.addLayout(self.result_grid, 1)
        plt.style.use('dark_background')
        self.eff_figure = plt.figure(figsize=(3.4, 2.6))
        self.eff_figure.patch.set_facecolor(theme.PANEL_2)
        self.eff_canvas = FigureCanvas(self.eff_figure)
        self.eff_canvas.setMinimumWidth(260)
        res_body.addWidget(self.eff_canvas)
        res_lay.addLayout(res_body)
        right_col.addWidget(res_frame)

        # trade-study graphs — a scrollable grid so this stays legible no
        # matter how many parameters are set to "Range"
        graph_frame = QFrame()
        graph_frame.setProperty("role", "panel")
        graph_lay = QVBoxLayout(graph_frame)
        graph_lay.setContentsMargins(16, 14, 16, 14)
        gt = QLabel("TRADE-STUDY GRAPHS  (one per parameter set to \u201cRange\u201d)")
        gt.setProperty("role", "tag")
        graph_lay.addWidget(gt)
        plt.style.use('dark_background')
        self.graph_scroll = QScrollArea()
        self.graph_scroll.setWidgetResizable(True)
        self.graph_scroll.setMinimumHeight(280)
        self.graph_inner = QWidget()
        self.graph_grid = QGridLayout(self.graph_inner)
        self.graph_grid.setSpacing(18)
        self.graph_scroll.setWidget(self.graph_inner)
        graph_lay.addWidget(self.graph_scroll, 1)
        right_col.addWidget(graph_frame, 1)

        root.addLayout(right_col, 1)

    # ------------------------------------------------------------------
    def sync_from_state(self, P):
        """Refresh every row's Static default to match the live Control Deck
        values, and pre-fill (unchecked) acceptance-criteria bounds around
        the current design's own performance (called whenever the Optimizer
        page is opened)."""
        for k, row in self.rows.items():
            if k in P:
                row.set_static_value(P[k])
        O = compute_all(P)
        for k, row in self.crit_rows.items():
            if k in O:
                row.set_reference_value(O[k])

    def _run(self):
        base_P = {k: ALL_PARAMS[k]['def'] for k in ALL_PARAMS}
        modes = {}
        for k, row in self.rows.items():
            cfg = row.config()
            modes[k] = cfg
            if cfg['mode'] == 'static':
                base_P[k] = cfg['value']

        criteria = {}
        for k, row in self.crit_rows.items():
            lo, hi = row.bounds()
            if lo is not None or hi is not None:
                criteria[k] = (lo, hi)

        n_free = sum(1 for m in modes.values() if m['mode'] in ('range', 'auto'))
        if n_free == 0:
            self.status_lbl.setText("No Range/Auto parameters set — evaluating your static design as-is.")
        else:
            self.status_lbl.setText("Running…")
        res = run_optimizer(base_P, modes, criteria, max_combinations=3000)
        self._last_result = res
        self._render_result(res, modes)

    def _render_result(self, res, modes):
        O = res['best_outputs']
        feas = res['best_is_feasible']
        color = theme.GREEN if feas else theme.AMBER
        tag = "meets all acceptance criteria" if feas else "closest match — did NOT satisfy every criterion"
        self.summary_lbl.setText(
            f"<span style='color:{color}; font-weight:700;'>Mission Efficiency {res['best_score']:.0f}/100</span>"
            f" &nbsp;·&nbsp; {tag} &nbsp;·&nbsp; {res['feasible_count']}/{res['total_evaluated']} "
            f"combinations evaluated were feasible."
        )
        self.status_lbl.setText(f"Done — {res['total_evaluated']} combination(s) checked.")
        self.apply_btn.setEnabled(True)

        # clear previous result grid
        while self.result_grid.count():
            item = self.result_grid.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        free_keys = [k for k, m in modes.items() if m['mode'] in ('range', 'auto')]
        r = 0
        head1 = QLabel("RECOMMENDED PARAMETER VALUES")
        head1.setStyleSheet(f"color:{theme.CYAN}; font-size:11px; font-weight:700;")
        self.result_grid.addWidget(head1, r, 0, 1, 2)
        r += 1
        if not free_keys:
            note = QLabel("(all parameters were Static — this is your current design, unchanged)")
            note.setStyleSheet(f"color:{theme.TEXT_FAINT}; font-size:10.5px; font-style:italic;")
            self.result_grid.addWidget(note, r, 0, 1, 2)
            r += 1
        for k in free_keys:
            p = ALL_PARAMS[k]
            lbl = QLabel(p['label'])
            lbl.setStyleSheet(f"color:{theme.TEXT_DIM}; font-size:11.5px;")
            val = QLabel(f"{res['best_P'][k]:.3g} {p['unit']}")
            val.setStyleSheet(f"color:{theme.TEXT}; font-size:11.5px; font-weight:700; font-family:{theme.MONO_FAMILY};")
            self.result_grid.addWidget(lbl, r, 0)
            self.result_grid.addWidget(val, r, 1)
            r += 1

        head2 = QLabel("RESULTING PERFORMANCE")
        head2.setStyleSheet(f"color:{theme.CYAN}; font-size:11px; font-weight:700;")
        self.result_grid.addWidget(head2, 0, 2, 1, 2)
        r2 = 1
        for spec in CRITERIA_OUTPUTS:
            lbl = QLabel(spec['label'])
            lbl.setStyleSheet(f"color:{theme.TEXT_DIM}; font-size:11.5px;")
            val = QLabel(f"{O[spec['k']]:.3g} {spec['unit']}")
            val.setStyleSheet(f"color:{theme.TEXT}; font-size:11.5px; font-weight:700; font-family:{theme.MONO_FAMILY};")
            self.result_grid.addWidget(lbl, r2, 2)
            self.result_grid.addWidget(val, r2, 3)
            r2 += 1

        self._render_graphs(res)
        self._render_efficiency_chart(res)

    def _render_efficiency_chart(self, res):
        """Instant efficiency breakdown for the best/current design, right
        here on the Optimizer page — no need to Apply or visit Charts to see
        how balanced/efficient the resulting system is."""
        O = res['best_outputs']
        eff = efficiency(O)
        labels = ["Spatial", "Radio-\nmetric", "Temporal", "Dynamic"]
        vals = [eff['spatial'], eff['radiometric'], eff['temporal'], eff['dynamic']]
        colors = [theme.SPATIAL, theme.RADIOMETRIC, theme.ORBITAL, theme.VIOLET]
        self.eff_figure.clear()
        ax = self.eff_figure.add_subplot(111)
        ax.set_facecolor(theme.PANEL_2)
        ax.set_title(f"Efficiency Breakdown ({eff['overall']:.0f}/100)", color=theme.TEXT,
                     fontsize=9.5, fontweight='bold')
        bars = ax.bar(labels, vals, color=colors, width=0.6)
        for b, v in zip(bars, vals):
            ax.text(b.get_x() + b.get_width() / 2, v + 2, f"{v:.0f}", ha='center',
                    color=theme.TEXT, fontsize=8, fontweight='bold')
        ax.set_ylim(0, 110)
        ax.tick_params(axis='x', colors=theme.TEXT_DIM, labelsize=7.5)
        ax.tick_params(axis='y', colors=theme.TEXT_DIM, labelsize=7.5)
        for spine in ('top', 'right'):
            ax.spines[spine].set_visible(False)
        for spine in ('left', 'bottom'):
            ax.spines[spine].set_color(theme.LINE)
        self.eff_figure.tight_layout(pad=1.0)
        self.eff_canvas.draw_idle()

    def _render_graphs(self, res):
        # clear previous canvases
        while self.graph_grid.count():
            item = self.graph_grid.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        sweeps = res['sweeps']
        keys = list(sweeps.keys())
        if not keys:
            note = QLabel("No parameters set to \u201cRange\u201d — nothing to graph.\n"
                           "Set one or more parameters to Range to see trade-study curves here.")
            note.setStyleSheet(f"color:{theme.TEXT_DIM}; font-size:11px;")
            note.setWordWrap(True)
            self.graph_grid.addWidget(note, 0, 0)
            return

        cols = 2 if len(keys) > 1 else 1
        for i, k in enumerate(keys):
            row, col = divmod(i, cols)
            card = QFrame()
            card.setProperty("role", "card")
            card.setMinimumHeight(260)
            card.setStyleSheet(f"QFrame[role='card'] {{ border: 1px solid {theme.LINE}; border-radius: 8px; }}")
            card_lay = QVBoxLayout(card)
            card_lay.setContentsMargins(8, 8, 8, 8)

            sweep = sweeps[k]
            pts = sweep['points']
            if sweep['flat']:
                warn = QLabel(f"\u26a0 {ALL_PARAMS[k]['label']} has little/no measurable effect on your "
                               f"criteria in this model — any value in range performs about the same.")
                warn.setWordWrap(True)
                warn.setStyleSheet(f"color:{theme.AMBER}; font-size:10px; font-style:italic;")
                card_lay.addWidget(warn)

            fig = plt.figure(figsize=(5.0, 3.0))
            fig.patch.set_facecolor(theme.PANEL_2)
            canvas = FigureCanvas(fig)
            ax = fig.add_subplot(111)
            ax.set_facecolor(theme.PANEL_2)
            xs = [pt['x'] for pt in pts]
            eff = [pt['score'] for pt in pts]
            gsd = [pt['outputs']['GSD'] for pt in pts]
            ax.plot(xs, eff, color=theme.CYAN, marker='o', ms=3, label="Efficiency")
            ax.set_title(node_label(k), color=theme.TEXT, fontsize=10, fontweight='bold')
            ax.set_xlabel(f"{ALL_PARAMS[k]['label']} ({ALL_PARAMS[k]['unit']})", color=theme.TEXT_DIM, fontsize=8)
            ax.set_ylabel("Efficiency", color=theme.CYAN, fontsize=8)
            ax.tick_params(axis='both', colors=theme.TEXT_DIM, labelsize=7)
            twin = ax.twinx()
            twin.set_facecolor('none')
            twin.plot(xs, gsd, color=theme.CORAL, marker='s', ms=3, ls='--', label="GSD")
            twin.set_ylabel("GSD (m)", color=theme.CORAL, fontsize=8)
            twin.tick_params(axis='y', colors=theme.CORAL, labelsize=7)
            for spine in ax.spines.values():
                spine.set_color(theme.LINE)
            for spine in twin.spines.values():
                spine.set_color(theme.LINE)
            fig.tight_layout(pad=1.2)
            card_lay.addWidget(canvas)
            self.graph_grid.addWidget(card, row, col)

    def _apply(self):
        if self._last_result and self._last_result['best_P']:
            self.applyRequested.emit(self._last_result['best_P'])
