"""EM Spectrum strip — shows where the currently selected band(s) sit across
the electromagnetic spectrum, and renders an approximate real color swatch
for the central wavelength when it falls in the visible range."""

from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QLinearGradient, QFont
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy

from .. import theme

# Visible-range boundaries used throughout (nm)
UV_END = 380
VIS_END = 700
NIR_END = 1100
SPAN_MIN = 250
SPAN_MAX = 2500


def wavelength_to_rgb(nm):
    """Approximate visible-light RGB for a wavelength in nm (Dan Bruton's
    algorithm). Wavelengths outside 380-700nm return a dim UV/IR tint."""
    if nm < UV_END:
        return QColor(70, 20, 110)          # UV -> dim violet/black
    if nm > NIR_END:
        return QColor(60, 24, 20)           # far IR -> dim ember
    if nm > VIS_END:
        # near-IR: fade the last visible red down toward a dark ember
        t = (nm - VIS_END) / (NIR_END - VIS_END)
        r = 255 * (1 - 0.6 * t)
        return QColor(int(r), int(20 * (1 - t)), int(20 * (1 - t)))

    w = nm
    if w < 440:
        r, g, b = -(w - 440) / (440 - 380), 0.0, 1.0
    elif w < 490:
        r, g, b = 0.0, (w - 440) / (490 - 440), 1.0
    elif w < 510:
        r, g, b = 0.0, 1.0, -(w - 510) / (510 - 490)
    elif w < 580:
        r, g, b = (w - 510) / (580 - 510), 1.0, 0.0
    elif w < 645:
        r, g, b = 1.0, -(w - 645) / (645 - 580), 0.0
    else:
        r, g, b = 1.0, 0.0, 0.0

    # intensity taper near the visible edges
    if w < 420:
        factor = 0.3 + 0.7 * (w - 380) / (420 - 380)
    elif w > 645:
        factor = 0.3 + 0.7 * (700 - w) / (700 - 645)
    else:
        factor = 1.0

    gamma = 0.8
    to255 = lambda c: int(max(0, min(1, c * factor)) ** gamma * 255)
    return QColor(to255(r), to255(g), to255(b))


class SpectrumBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(74)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.central = 625.0
        self.bandwidth = 350.0
        self.lo = 450.0
        self.hi = 800.0

    def set_band(self, central, bandwidth, lo, hi):
        self.central = central
        self.bandwidth = bandwidth
        self.lo = lo
        self.hi = hi
        self.update()

    def _x_of(self, nm, w, margin):
        frac = (nm - SPAN_MIN) / (SPAN_MAX - SPAN_MIN)
        return margin + frac * (w - 2 * margin)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        margin = 10
        bar_top, bar_h = 22, 26
        bar_rect = QRectF(margin, bar_top, w - 2 * margin, bar_h)

        # continuous gradient across the whole span
        grad = QLinearGradient(bar_rect.left(), 0, bar_rect.right(), 0)
        steps = 60
        for i in range(steps + 1):
            nm = SPAN_MIN + (SPAN_MAX - SPAN_MIN) * i / steps
            grad.setColorAt(i / steps, wavelength_to_rgb(nm))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(grad))
        p.drawRoundedRect(bar_rect, 5, 5)

        # sensor's overall spectral coverage (faint overlay box)
        x_lo = self._x_of(self.lo, w, margin)
        x_hi = self._x_of(self.hi, w, margin)
        p.setPen(QPen(QColor(theme.TEXT), 1.2, Qt.PenStyle.DashLine))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRect(QRectF(x_lo, bar_top - 4, max(2.0, x_hi - x_lo), bar_h + 8))

        # highlighted active band (central +/- bandwidth/2)
        b_lo = self._x_of(self.central - self.bandwidth / 2, w, margin)
        b_hi = self._x_of(self.central + self.bandwidth / 2, w, margin)
        p.setPen(QPen(QColor(theme.CYAN), 2))
        col = QColor(theme.CYAN)
        col.setAlpha(60)
        p.setBrush(QBrush(col))
        p.drawRect(QRectF(b_lo, bar_top - 4, max(2.0, b_hi - b_lo), bar_h + 8))

        # central wavelength marker (triangle)
        cx = self._x_of(self.central, w, margin)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(theme.TEXT))
        tri = [QPointF(cx - 5, bar_top - 6), QPointF(cx + 5, bar_top - 6), QPointF(cx, bar_top + 2)]
        p.drawPolygon(*tri)

        # axis ticks / labels
        p.setPen(QColor(theme.TEXT_FAINT))
        f = QFont(theme.FONT_FAMILY.split(",")[0].strip(), 8)
        p.setFont(f)
        for nm, lbl in [(UV_END, "UV"), (VIS_END, "700"), (NIR_END, "NIR"), (2000, "SWIR")]:
            x = self._x_of(nm, w, margin)
            p.drawLine(QPointF(x, bar_top + bar_h + 2), QPointF(x, bar_top + bar_h + 6))
            p.drawText(QRectF(x - 20, bar_top + bar_h + 6, 40, 14), Qt.AlignmentFlag.AlignHCenter, lbl)

        p.end()


class ColorSwatch(QWidget):
    """Shows the approximate perceived color of the current central
    wavelength as a solid tile, so it reads as 'this band looks like this'."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(56, 56)
        self._color = QColor(255, 255, 255)

    def set_wavelength(self, nm):
        self._color = wavelength_to_rgb(nm)
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(QPen(QColor(theme.LINE), 1.5))
        p.setBrush(QBrush(self._color))
        p.drawRoundedRect(QRectF(1, 1, self.width() - 2, self.height() - 2), 10, 10)
        p.end()


class SpectrumWidget(QWidget):
    """Composite: title row + color swatch + gradient bar, all driven by the
    active spectral-band inputs (central wavelength, bandwidth, min/max)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(6)

        head = QHBoxLayout()
        tag = QLabel("EM SPECTRUM — ACTIVE BAND")
        tag.setProperty("role", "tag")
        head.addWidget(tag)
        head.addStretch()
        self.readout = QLabel("")
        self.readout.setStyleSheet(f"color:{theme.CYAN}; font-size:11px; font-weight:700; "
                                    f"font-family:{theme.MONO_FAMILY};")
        head.addWidget(self.readout)
        outer.addLayout(head)

        row = QHBoxLayout()
        row.setSpacing(12)
        self.swatch = ColorSwatch()
        row.addWidget(self.swatch)
        self.bar = SpectrumBar()
        row.addWidget(self.bar, 1)
        outer.addLayout(row)

    def update_from_state(self, P):
        central = P['centralWavelength']
        bw = P['bandwidth']
        lo = P['minWavelength']
        hi = P['maxWavelength']
        self.bar.set_band(central, bw, lo, hi)
        self.swatch.set_wavelength(central)
        tag = "visible" if UV_END <= central <= VIS_END else ("near-IR" if central > VIS_END else "UV")
        self.readout.setText(f"{central:.0f} nm ({tag}) · Δλ {bw:.0f} nm · coverage {lo:.0f}–{hi:.0f} nm")
