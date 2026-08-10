from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QListWidget, QListWidgetItem, QStackedWidget, QTabWidget,
                              QScrollArea, QFrame, QSizePolicy)

from . import theme
from .model import default_inputs, compute_all, ENGINES
from .widgets.starfield import StarfieldWidget
from .widgets.dashboard import DashboardWidget
from .widgets.param_panel import ParamPanel
from .widgets.output_grid import OutputGrid
from .widgets.dependency import DependencyDiagramWidget
from .widgets.charts import ChartsWidget


def _scrollable(widget):
    sc = QScrollArea()
    sc.setWidgetResizable(True)
    sc.setWidget(widget)
    return sc


class MainWindow(QMainWindow):
    PAGES = ["Overview", "Control Deck", "Dependency Mapping", "Charts"]

    def __init__(self):
        super().__init__()
        self.setWindowTitle("OPTIEO / EOSSP — Earth Observation Sensor System Performance Tool")
        self.resize(1560, 960)
        self.setStyleSheet(theme.STYLESHEET)

        self.P = default_inputs()

        root = QWidget()
        root.setObjectName("RootBg")
        self.setCentralWidget(root)
        root_stack = QVBoxLayout(root)
        root_stack.setContentsMargins(0, 0, 0, 0)
        root_stack.setSpacing(0)

        # starfield fills the whole window; everything else floats on top
        self.starfield = StarfieldWidget(root)
        self.starfield.lower()

        body = QWidget()
        body.setStyleSheet("background: transparent;")
        body_lay = QHBoxLayout(body)
        body_lay.setContentsMargins(18, 18, 18, 18)
        body_lay.setSpacing(16)
        root_stack.addWidget(body)

        # ── sidebar ──
        sidebar = QFrame()
        sidebar.setProperty("role", "panel")
        sidebar.setFixedWidth(230)
        side_lay = QVBoxLayout(sidebar)
        side_lay.setContentsMargins(16, 20, 16, 20)
        side_lay.setSpacing(4)

        brand_row = QHBoxLayout()
        dot = QLabel("●")
        dot.setStyleSheet(f"color:{theme.CYAN}; font-size:14px;")
        brand_row.addWidget(dot)
        brand = QLabel("OPTIEO")
        brand.setStyleSheet(f"color:{theme.TEXT}; font-size:16px; font-weight:800; letter-spacing:2px;")
        brand_row.addWidget(brand)
        brand_row.addStretch()
        side_lay.addLayout(brand_row)
        sub = QLabel("EOSSP PERFORMANCE TOOL")
        sub.setStyleSheet(f"color:{theme.TEXT_FAINT}; font-size:9.5px; font-weight:600; letter-spacing:1px;")
        side_lay.addWidget(sub)
        side_lay.addSpacing(18)

        self.nav = QListWidget()
        self.nav.setSpacing(2)
        for name in self.PAGES:
            self.nav.addItem(QListWidgetItem(name))
        self.nav.setCurrentRow(0)
        self.nav.currentRowChanged.connect(self._on_nav)
        side_lay.addWidget(self.nav)
        side_lay.addStretch()

        status_row = QHBoxLayout()
        sdot = QLabel("●")
        sdot.setStyleSheet(f"color:{theme.GREEN}; font-size:9px;")
        status_row.addWidget(sdot)
        slbl = QLabel("LIVE MODEL")
        slbl.setStyleSheet(f"color:{theme.GREEN}; font-size:10px; font-weight:700; letter-spacing:1px; font-family:{theme.MONO_FAMILY};")
        status_row.addWidget(slbl)
        status_row.addStretch()
        side_lay.addLayout(status_row)

        body_lay.addWidget(sidebar)

        # ── page stack ──
        self.stack = QStackedWidget()
        body_lay.addWidget(self.stack, 1)

        # Overview
        self.dashboard = DashboardWidget()
        self.stack.addWidget(_wrap_panel(self.dashboard, "Overview"))

        # Control Deck + Engine Outputs, side by side so you can watch outputs
        # update live while dragging any slider
        self.param_panel = ParamPanel()
        self.param_panel.valueChanged.connect(self._on_param_changed)

        self.output_tabs = QTabWidget()
        self.output_grids = {}
        for eng in ENGINES:
            grid = OutputGrid(eng["id"])
            grid.cardClicked.connect(lambda key, e=eng["id"]: self._on_output_clicked(e, key))
            self.output_grids[eng["id"]] = grid
            self.output_tabs.addTab(_scrollable(grid), f"{eng['no']} {eng['name']}")

        workbench = QFrame()
        workbench.setStyleSheet("background: transparent;")
        wb_lay = QHBoxLayout(workbench)
        wb_lay.setContentsMargins(0, 0, 0, 0)
        wb_lay.setSpacing(16)

        left_col = QFrame()
        left_col.setProperty("role", "panel")
        left_col.setMinimumWidth(430)
        left_col.setMaximumWidth(520)
        left_lay = QVBoxLayout(left_col)
        left_lay.setContentsMargins(16, 16, 16, 16)
        left_lay.setSpacing(8)
        left_head = QLabel("INPUT PARAMETERS")
        left_head.setProperty("role", "tag")
        left_lay.addWidget(left_head)
        left_lay.addWidget(self.param_panel, 1)
        wb_lay.addWidget(left_col, 0)

        right_col = QFrame()
        right_col.setProperty("role", "panel")
        right_lay = QVBoxLayout(right_col)
        right_lay.setContentsMargins(16, 16, 16, 16)
        right_lay.setSpacing(8)
        right_head_row = QHBoxLayout()
        right_head = QLabel("LIVE TELEMETRY")
        right_head.setProperty("role", "tag")
        right_head_row.addWidget(right_head)
        right_head_row.addStretch()
        move_hint = QLabel("move any slider →")
        move_hint.setStyleSheet(f"color:{theme.TEXT_FAINT}; font-size:10px; font-style:italic;")
        right_head_row.addWidget(move_hint)
        right_lay.addLayout(right_head_row)
        right_lay.addWidget(self.output_tabs, 1)
        wb_lay.addWidget(right_col, 1)

        self.stack.addWidget(_wrap_panel(workbench, "Control Deck",
                                          desc="Adjust any of the 26 raw inputs on the left and watch all 39 "
                                               "computed outputs update instantly on the right. Click an output "
                                               "card to trace it in Dependency Mapping."))

        # Dependency Mapping (one tab per engine)
        self.map_tabs = QTabWidget()
        self.dep_widgets = {}
        for eng in ENGINES:
            dep = DependencyDiagramWidget(eng["id"])
            self.dep_widgets[eng["id"]] = dep
            self.map_tabs.addTab(dep, f"{eng['no']} {eng['name']}")
        self.stack.addWidget(_wrap_panel(self.map_tabs, "Dependency Mapping",
                                          desc="Family-tree view of the real formula graph. Click any node to "
                                               "highlight exactly which inputs and outputs it connects to."))

        # Charts
        self.charts = ChartsWidget()
        self.stack.addWidget(_wrap_panel(self.charts, "Analysis Charts",
                                          desc="How key outputs respond to altitude and aperture sweeps, plus the "
                                               "live efficiency breakdown for the current configuration."))

        self._recompute_and_refresh()

    # ------------------------------------------------------------------
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.starfield.setGeometry(self.centralWidget().rect())

    def _on_nav(self, row):
        self.stack.setCurrentIndex(row)

    def _on_param_changed(self, key, value):
        self.P[key] = value
        self._recompute_and_refresh()

    def _on_output_clicked(self, engine_id, key):
        # jump to the Dependency Mapping page, correct engine tab, and select the node
        self.nav.setCurrentRow(self.PAGES.index("Dependency Mapping"))
        idx = list(self.dep_widgets.keys()).index(engine_id)
        self.map_tabs.setCurrentIndex(idx)
        self.dep_widgets[engine_id].select_key(key)

    def _recompute_and_refresh(self):
        O = compute_all(self.P)
        self.dashboard.update_from_state(self.P)
        for eng_id, grid in self.output_grids.items():
            grid.update_values(O)
        self.charts.update_charts(self.P)


def _wrap_panel(widget, title, desc=None):
    frame = QFrame()
    frame.setStyleSheet("background: transparent;")
    lay = QVBoxLayout(frame)
    lay.setContentsMargins(2, 2, 2, 2)
    lay.setSpacing(10)
    head = QLabel(title)
    head.setProperty("role", "h1")
    lay.addWidget(head)
    if desc:
        d = QLabel(desc)
        d.setWordWrap(True)
        d.setStyleSheet(f"color:{theme.TEXT_DIM}; font-size:12px; margin-bottom:4px;")
        lay.addWidget(d)
    widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
    lay.addWidget(widget, 1)
    return frame
