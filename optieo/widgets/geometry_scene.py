"""Pseudo-3D scan-geometry diagram: satellite, look-angle cone, IFOV/FOV,
altitude, swath, and along-track/cross-track axes — redrawn live from the
current mission parameters. Mirrors the two classic push-broom-scanner
reference diagrams (rotating mirror + FOV/IFOV, and the along/cross-track
pyramid view), combined into one animated widget."""

import math

from PyQt6.QtCore import Qt, QTimer, QRectF, QPointF, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QLinearGradient, QFont, QPainterPath
from PyQt6.QtWidgets import (QWidget, QSizePolicy, QHBoxLayout, QVBoxLayout, QLabel,
                              QSlider, QDoubleSpinBox)

from .. import theme


def _lerp(a, b, t):
    return a + (b - a) * t


class ScanGeometryScene(QWidget):
    #: emitted when the user drags one of this widget's own embedded
    #: controls — (param_key, new_value) — so the host window can push the
    #: change into the shared parameter state and keep everything in sync.
    paramChanged = pyqtSignal(str, float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(340)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._t = 0.0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(30)

        # live parameters (sensible defaults, overwritten by update_from_state)
        self.altitude = 617.0       # km
        self.look_angle = 20.0      # deg, off-nadir tilt
        self.tfov_deg = 2.0         # total FOV, deg
        self.ifov_deg = 0.02        # instantaneous FOV of one pixel, deg
        self.swath_km = 120.0
        self.gsd_m = 0.5

    def _tick(self):
        self._t += 0.012
        self.update()

    def update_from_state(self, P, O):
        self.altitude = P['altitude']
        self.look_angle = P['lookAngle']
        self.tfov_deg = O['TFOV'] * 180.0 / math.pi
        self.ifov_deg = O['IFOV'] * 180.0 / math.pi
        self.swath_km = O['swathWidth']
        self.gsd_m = O['GSD']
        self.update()
        # keep the embedded sliders in sync without re-triggering paramChanged
        if hasattr(self, '_alt_slider'):
            self._set_slider_silent(self._alt_slider, self._alt_spin, self.altitude)
            self._set_slider_silent(self._look_slider, self._look_spin, self.look_angle)

    # ------------------------------------------------------------------
    # Embedded interactive controls — lets a judge/user drag altitude and
    # look angle directly on the diagram itself, on the main Overview page,
    # instead of having to go to the Control Deck.
    def build_controls(self):
        box = QWidget()
        row = QHBoxLayout(box)
        row.setContentsMargins(4, 4, 4, 0)
        row.setSpacing(28)

        self._alt_slider, self._alt_spin = self._make_control(
            row, "Altitude", "km", 300, 1200, self.altitude,
            lambda v: self._on_control_change('altitude', v))
        self._look_slider, self._look_spin = self._make_control(
            row, "Look Angle", "deg", -45, 45, self.look_angle,
            lambda v: self._on_control_change('lookAngle', v))
        row.addStretch()
        return box

    def _make_control(self, parent_layout, label, unit, lo, hi, default, on_change):
        wrap = QVBoxLayout()
        wrap.setSpacing(3)
        top = QHBoxLayout()
        lbl = QLabel(label)
        lbl.setStyleSheet(f"color:{theme.TEXT_DIM}; font-size:11px; font-weight:600;")
        top.addWidget(lbl)
        spin = QDoubleSpinBox()
        spin.setRange(lo, hi)
        spin.setDecimals(1)
        spin.setSuffix(f" {unit}")
        spin.setFixedWidth(100)
        spin.setValue(default)
        top.addWidget(spin)
        wrap.addLayout(top)

        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setMinimum(int(lo * 10))
        slider.setMaximum(int(hi * 10))
        slider.setValue(int(default * 10))
        slider.setFixedWidth(220)
        wrap.addWidget(slider)

        def slider_moved(v):
            val = v / 10.0
            spin.blockSignals(True)
            spin.setValue(val)
            spin.blockSignals(False)
            on_change(val)

        def spin_edited(val):
            slider.blockSignals(True)
            slider.setValue(int(val * 10))
            slider.blockSignals(False)
            on_change(val)

        slider.valueChanged.connect(slider_moved)
        spin.valueChanged.connect(spin_edited)
        parent_layout.addLayout(wrap)
        return slider, spin

    def _on_control_change(self, key, value):
        if key == 'altitude':
            self.altitude = value
        elif key == 'lookAngle':
            self.look_angle = value
        self.update()
        self.paramChanged.emit(key, value)

    def _set_slider_silent(self, slider, spin, value):
        slider.blockSignals(True)
        spin.blockSignals(True)
        slider.setValue(int(value * 10))
        spin.setValue(value)
        slider.blockSignals(False)
        spin.blockSignals(False)

    # ------------------------------------------------------------------
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        # --- normalize altitude & swath onto a fixed drawing envelope so the
        # picture always reads clearly regardless of the raw km values ---
        sat_y = h * 0.14
        ground_y = h * 0.86
        cx = w * 0.5

        alt_frac = max(0.0, min(1.0, (self.altitude - 300) / (1200 - 300)))
        sat_x_offset = 0  # satellite stays centered; look angle tilts the cone instead

        # swath half-width on screen, exaggerated with sqrt so small/large
        # swaths both stay legible, and modulated by look angle asymmetry
        swath_screen_half = _lerp(70, w * 0.42, math.sqrt(max(1.0, self.swath_km)) / math.sqrt(400.0))
        swath_screen_half = min(swath_screen_half, w * 0.44)

        look_rad = math.radians(self.look_angle)
        tilt_px = math.tan(look_rad) * (ground_y - sat_y) * 0.35

        sat_pt = QPointF(cx + sat_x_offset, sat_y)
        ground_l = QPointF(cx - swath_screen_half + tilt_px, ground_y)
        ground_r = QPointF(cx + swath_screen_half + tilt_px, ground_y)
        ground_c = QPointF(cx + tilt_px, ground_y)

        # ---- ground plane (earth surface segment) ----
        ground_grad = QLinearGradient(0, ground_y - 10, 0, h)
        ground_grad.setColorAt(0.0, QColor(13, 58, 92, 210))
        ground_grad.setColorAt(1.0, QColor(4, 18, 32, 230))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(ground_grad))
        p.drawRect(QRectF(0, ground_y, w, h - ground_y))
        p.setPen(QPen(QColor(theme.LINE), 1.4))
        p.drawLine(QPointF(0, ground_y), QPointF(w, ground_y))

        # ---- FOV cone (the full scan swath, like the pyramid reference) ----
        cone = QPainterPath()
        cone.moveTo(sat_pt)
        cone.lineTo(ground_l)
        cone.lineTo(ground_r)
        cone.closeSubpath()
        cone_col = QColor(theme.CYAN)
        cone_col.setAlpha(28)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(cone_col))
        p.drawPath(cone)
        p.setPen(QPen(QColor(theme.CYAN), 1.3))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawLine(sat_pt, ground_l)
        p.drawLine(sat_pt, ground_r)

        # ---- IFOV cone (single-pixel instantaneous FOV, centered in swath) ----
        ifov_half = max(4.0, swath_screen_half * 0.035)
        ifov_l = QPointF(ground_c.x() - ifov_half, ground_y)
        ifov_r = QPointF(ground_c.x() + ifov_half, ground_y)
        p.setPen(QPen(QColor(theme.AMBER), 1.6, Qt.PenStyle.DashLine))
        p.drawLine(sat_pt, ifov_l)
        p.drawLine(sat_pt, ifov_r)
        amber = QColor(theme.AMBER)
        amber.setAlpha(70)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(amber))
        p.drawRect(QRectF(ifov_l.x(), ground_y - 4, max(2.0, ifov_r.x() - ifov_l.x()), 8))

        # ---- altitude line (h), left margin ----
        alt_x = w * 0.08
        p.setPen(QPen(QColor(theme.TEXT_DIM), 1.2, Qt.PenStyle.DashDotLine))
        p.drawLine(QPointF(alt_x, sat_y), QPointF(alt_x, ground_y))
        p.drawLine(QPointF(alt_x - 5, sat_y), QPointF(alt_x + 5, sat_y))
        p.drawLine(QPointF(alt_x - 5, ground_y), QPointF(alt_x + 5, ground_y))
        p.setPen(QColor(theme.TEXT_DIM))
        f = QFont(theme.FONT_FAMILY.split(",")[0].strip(), 9)
        p.setFont(f)
        p.save()
        p.translate(alt_x - 10, (sat_y + ground_y) / 2)
        p.rotate(-90)
        p.drawText(QRectF(-60, -10, 120, 20), Qt.AlignmentFlag.AlignCenter, f"h = {self.altitude:.0f} km")
        p.restore()

        # ---- look angle arc at the satellite ----
        p.setPen(QPen(QColor(theme.VIOLET), 1.3))
        nadir_end = QPointF(sat_pt.x(), sat_pt.y() + 34)
        p.drawLine(sat_pt, nadir_end)
        arc_rect = QRectF(sat_pt.x() - 22, sat_pt.y(), 44, 44)
        start_angle = -90 * 16
        span_angle = int(-self.look_angle * 16) if tilt_px >= 0 else int(self.look_angle * 16)
        p.drawArc(arc_rect, start_angle, span_angle)
        p.drawText(QRectF(sat_pt.x() + 6, sat_pt.y() + 6, 90, 16), Qt.AlignmentFlag.AlignLeft,
                   f"θ = {self.look_angle:.1f}°")

        # ---- satellite body ----
        p.save()
        p.translate(sat_pt)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(216, 222, 232))
        p.drawRoundedRect(QRectF(-7, -5, 14, 10), 2, 2)
        p.setBrush(QColor(26, 61, 107))
        p.drawRect(QRectF(-26, -1.8, 17, 3.6))
        p.drawRect(QRectF(9, -1.8, 17, 3.6))
        p.setPen(QPen(QColor(120, 170, 220), 0.8))
        for k in range(-3, 4):
            p.drawLine(QPointF(-26 + k * 4.8, -1.8), QPointF(-26 + k * 4.8, 1.8))
            p.drawLine(QPointF(9 + k * 4.8, -1.8), QPointF(9 + k * 4.8, 1.8))
        p.restore()

        # ---- animated scan-line sweeping across the swath (push-broom) ----
        sweep_t = (math.sin(self._t) + 1) / 2  # 0..1..0
        sweep_x = _lerp(ground_l.x(), ground_r.x(), sweep_t)
        p.setPen(QPen(QColor(theme.GREEN), 2.2))
        p.drawLine(QPointF(sweep_x, ground_y - 6), QPointF(sweep_x, ground_y + 6))
        glow = QColor(theme.GREEN)
        glow.setAlpha(50)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(glow))
        p.drawEllipse(QPointF(sweep_x, ground_y), 9, 5)

        # ---- swath width label + end caps ----
        p.setPen(QPen(QColor(theme.CYAN), 1.2))
        cap_y = ground_y + 16
        p.drawLine(QPointF(ground_l.x(), cap_y - 5), QPointF(ground_l.x(), cap_y + 5))
        p.drawLine(QPointF(ground_r.x(), cap_y - 5), QPointF(ground_r.x(), cap_y + 5))
        p.drawLine(QPointF(ground_l.x(), cap_y), QPointF(ground_r.x(), cap_y))
        p.setPen(QColor(theme.TEXT))
        p.drawText(QRectF(ground_l.x(), cap_y + 4, ground_r.x() - ground_l.x(), 16),
                   Qt.AlignmentFlag.AlignCenter, f"Swath = {self.swath_km:.1f} km")

        # ---- cross-track / along-track compass, bottom-right ----
        ax, ay = w - 70, h - 34
        p.setPen(QPen(QColor(theme.TEXT_DIM), 1.4))
        p.drawLine(QPointF(ax, ay), QPointF(ax + 40, ay))
        p.drawLine(QPointF(ax, ay), QPointF(ax, ay - 24))
        p.setPen(QColor(theme.TEXT_FAINT))
        f2 = QFont(theme.FONT_FAMILY.split(",")[0].strip(), 8)
        p.setFont(f2)
        p.drawText(QRectF(ax + 4, ay - 14, 60, 14), Qt.AlignmentFlag.AlignLeft, "Cross-track")
        p.save()
        p.translate(ax - 2, ay - 26)
        p.rotate(-90)
        p.drawText(QRectF(-40, -12, 80, 14), Qt.AlignmentFlag.AlignCenter, "Along-track")
        p.restore()

        # ---- IFOV / FOV readout, top-left ----
        p.setPen(QColor(theme.AMBER))
        p.setFont(QFont(theme.FONT_FAMILY.split(",")[0].strip(), 9))
        p.drawText(QRectF(10, 6, 220, 16), Qt.AlignmentFlag.AlignLeft,
                   f"IFOV = {self.ifov_deg*1000:.2f} mdeg   GSD = {self.gsd_m:.2f} m")
        p.setPen(QColor(theme.CYAN))
        p.drawText(QRectF(10, 22, 220, 16), Qt.AlignmentFlag.AlignLeft,
                   f"Total FOV = {self.tfov_deg:.2f}°")

        p.end()
