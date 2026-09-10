from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
                              QSlider, QDoubleSpinBox, QScrollArea, QToolButton)
from optieo import theme
from optieo.model import GROUPS

class ParamRow(QWidget):
    valueChanged = pyqtSignal(str, float)
    def __init__(self, param, color, parent=None):
        super().__init__(parent)
        self.param = param
        outer = QVBoxLayout(self)
        outer.setContentsMargins(2, 4, 2, 4)
        outer.setSpacing(4)
        top = QHBoxLayout()
        name = QLabel(param['label'])
        name.setStyleSheet(f"color:{theme.TEXT}; font-weight:600; font-size:12px;")
        top.addWidget(name)
        top.addStretch()
        self.spin = QDoubleSpinBox()
        self.spin.setDecimals(param.get('decimals', 1))
        self.spin.setRange(param['min'], param['max'])
        self.spin.setSingleStep(param['step'])
        self.spin.setValue(param['def'])
        self.spin.setSuffix(f" {param['unit']}" if param['unit'] else "")
        self.spin.setFixedWidth(110)
        self.spin.setAlignment(Qt.AlignmentFlag.AlignRight)
        top.addWidget(self.spin)
        outer.addLayout(top)
        self.slider = QSlider(Qt.Orientation.Horizontal)
        steps = max(1, int(round((param['max'] - param['min']) / param['step'])))
        self.slider.setRange(0, steps)
        self.slider.setValue(int(round((param['def'] - param['min']) / param['step'])))
        outer.addWidget(self.slider)
        self.slider.setStyleSheet(f"QSlider::sub-page:horizontal {{ background: {color}; border-radius:2px; }}")
        self._updating = False
        self.slider.valueChanged.connect(self._from_slider)
        self.spin.valueChanged.connect(self._from_spin)

    def _from_slider(self, v):
        if self._updating: return
        self._updating = True
        val = self.param['min'] + v * self.param['step']
        self.spin.setValue(val)
        self._updating = False
        self.valueChanged.emit(self.param['k'], val)

    def _from_spin(self, val):
        if self._updating: return
        self._updating = True
        steps = int(round((val - self.param['min']) / self.param['step']))
        self.slider.setValue(steps)
        self._updating = False
        self.valueChanged.emit(self.param['k'], val)

    def set_value(self, val):
        self.spin.setValue(val)

class CollapsibleGroup(QFrame):
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
        lbl.setProperty("role", "h2")
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

class ParamPanel(QWidget):
    valueChanged = pyqtSignal(str, float)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.rows = {}
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        inner = QWidget()
        inner_layout = QVBoxLayout(inner)
        inner_layout.setContentsMargins(4, 4, 10, 4)
        for group in GROUPS:
            box = CollapsibleGroup(group['label'], group['color'])
            for p in group['params']:
                row = ParamRow(p, group['color'])
                row.valueChanged.connect(self.valueChanged)
                box.add_row(row)
                self.rows[p['k']] = row
            inner_layout.addWidget(box)
        inner_layout.addStretch()
        scroll.setWidget(inner)
        outer.addWidget(scroll)

    def values(self):
        return {k: r.spin.value() for k, r in self.rows.items()}

    def set_value(self, key, val):
        """Programmatically move a slider/spinbox (e.g. when the value was
        changed from the Overview page's embedded geometry controls). Qt only
        emits valueChanged when the value actually differs, so this is safe
        to call from within a change-handler without causing a feedback loop."""
        row = self.rows.get(key)
        if row is not None:
            row.set_value(val)