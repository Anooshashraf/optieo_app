from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QWidget, QGridLayout, QFrame, QVBoxLayout, QLabel
from .. import theme
from ..model import OUT_DEFS, fmt

class MetricCard(QFrame):
    clicked = pyqtSignal(str)
    def __init__(self, key, label, color, parent=None):
        super().__init__(parent)
        self.key = key
        self.setProperty("role", "card")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(f"""
            QFrame[role='card'] {{ border-left: 3px solid {color}; }}
            QFrame[role='card']:hover {{ border: 1px solid {color}; }}
        """)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 10, 12, 10)
        self.lbl = QLabel(label)
        self.lbl.setStyleSheet(f"color:{theme.TEXT_DIM}; font-size:11px; font-weight:600;")
        self.lbl.setWordWrap(True)
        lay.addWidget(self.lbl)
        self.val = QLabel("—")
        self.val.setStyleSheet(f"color:{theme.TEXT}; font-size:19px; font-weight:700; font-family:{theme.MONO_FAMILY};")
        lay.addWidget(self.val)
        self.unit = QLabel("")
        self.unit.setStyleSheet(f"color:{color}; font-size:10px; font-weight:600;")
        lay.addWidget(self.unit)

    def set_value(self, value, unit, sci):
        self.val.setText(fmt(value, sci))
        self.unit.setText(unit)

    def mousePressEvent(self, event):
        self.clicked.emit(self.key)
        super().mousePressEvent(event)

class OutputGrid(QWidget):
    cardClicked = pyqtSignal(str)
    def __init__(self, engine_id, parent=None):
        super().__init__(parent)
        self.engine_id = engine_id
        self.cards = {}
        color = theme.ENGINE_COLORS[engine_id]
        grid = QGridLayout(self)
        grid.setSpacing(10)
        defs = [d for d in OUT_DEFS if d['eng'] == engine_id]
        for i, d in enumerate(defs):
            card = MetricCard(d['k'], d['label'], color)
            card.clicked.connect(self.cardClicked)
            grid.addWidget(card, i // 4, i % 4)
            self.cards[d['k']] = card

    def update_values(self, O):
        defs = {d['k']: d for d in OUT_DEFS if d['eng'] == self.engine_id}
        for key, card in self.cards.items():
            d = defs[key]
            v = O.get(key)
            if v is not None and d.get('mult'):
                v = v * d['mult']
            card.set_value(v, d['unit'], d.get('sci', False))