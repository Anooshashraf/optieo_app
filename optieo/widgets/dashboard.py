import math

from PyQt6.QtCore import Qt, QTimer, QRectF, QPointF
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QRadialGradient, QFont, QPainterPath
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
                              QGridLayout, QSizePolicy)

from .. import theme
from ..model import compute_all, efficiency, fmt


class OrbitScene(QWidget):
    """Painted animated hero visual: a rotating Earth with a satellite tracing
    an inclined elliptical orbit, a faint ground-track ring, and a subtle
    scan-sweep. Pure QPainter -- no external images/network required."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(320)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._t = 0.0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(30)

    def _tick(self):
        self._t += 0.018
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        cx, cy = w * 0.5, h * 0.54
        R = min(w, h) * 0.26

        # soft glow behind earth
        glow = QRadialGradient(cx, cy, R * 2.3)
        glow.setColorAt(0.0, QColor(77, 216, 255, 40))
        glow.setColorAt(1.0, QColor(77, 216, 255, 0))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(glow))
        p.drawEllipse(QPointF(cx, cy), R * 2.3, R * 2.3)

        # earth sphere
        earth_grad = QRadialGradient(cx - R * 0.35, cy - R * 0.35, R * 1.6)
        earth_grad.setColorAt(0.0, QColor(40, 110, 160))
        earth_grad.setColorAt(0.55, QColor(13, 58, 92))
        earth_grad.setColorAt(1.0, QColor(4, 18, 32))
        p.setBrush(QBrush(earth_grad))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QPointF(cx, cy), R, R)

        # rotating faint longitude lines (clipped to circle)
        p.save()
        clip = QPainterPath()
        clip.addEllipse(QPointF(cx, cy), R, R)
        p.setClipPath(clip)
        pen = QPen(QColor(120, 190, 230, 55), 1)
        p.setPen(pen)
        for i in range(8):
            ang = self._t * 8 + i * (math.pi / 4)
            rx = abs(math.cos(ang)) * R
            p.drawEllipse(QPointF(cx, cy), rx, R)
        for j in range(-2, 3):
            yy = cy + j * R * 0.35
            p.drawLine(QPointF(cx - R, yy), QPointF(cx + R, yy))
        p.restore()

        # terminator / atmosphere rim
        p.setPen(QPen(QColor(120, 200, 255, 130), 2))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(QPointF(cx, cy), R + 2, R + 2)

        # orbit ellipse (inclined)
        orbit_rx, orbit_ry = R * 1.85, R * 0.72
        p.save()
        p.translate(cx, cy)
        p.rotate(-18)
        pen2 = QPen(QColor(77, 216, 255, 90), 1.4, Qt.PenStyle.DashLine)
        p.setPen(pen2)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(QPointF(0, 0), orbit_rx, orbit_ry)

        # satellite position along orbit
        ang = self._t * 1.15
        sx = math.cos(ang) * orbit_rx
        sy = math.sin(ang) * orbit_ry
        # trailing ground-track glow
        trail_grad = QRadialGradient(sx, sy, 26)
        trail_grad.setColorAt(0.0, QColor(255, 180, 84, 130))
        trail_grad.setColorAt(1.0, QColor(255, 180, 84, 0))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(trail_grad))
        p.drawEllipse(QPointF(sx, sy), 26, 26)

        # satellite body (simple bus + 2 panels), oriented along velocity vector
        vx = -math.sin(ang) * orbit_rx
        vy = math.cos(ang) * orbit_ry
        heading = math.atan2(vy, vx)
        p.translate(sx, sy)
        p.rotate(math.degrees(heading))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(216, 222, 232))
        p.drawRoundedRect(QRectF(-6, -4, 12, 8), 2, 2)
        p.setBrush(QColor(26, 61, 107))
        p.drawRect(QRectF(-24, -1.6, 16, 3.2))
        p.drawRect(QRectF(8, -1.6, 16, 3.2))
        p.setPen(QPen(QColor(120, 170, 220), 0.8))
        for k in range(-3, 4):
            p.drawLine(QPointF(-24 + k * 4.5, -1.6), QPointF(-24 + k * 4.5, 1.6))
            p.drawLine(QPointF(8 + k * 4.5, -1.6), QPointF(8 + k * 4.5, 1.6))
        p.restore()

        p.end()


class RingGauge(QWidget):
    """Circular 'mission efficiency' gauge with an animated needle-satellite
    marker riding the arc, matching the composite-score idea from the
    original workbook."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(190, 190)
        self._value = 0.0
        self._display = 0.0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate)
        self._timer.start(16)

    def set_value(self, v):
        self._value = max(0.0, min(100.0, v))

    def _animate(self):
        d = self._value - self._display
        if abs(d) > 0.05:
            self._display += d * 0.12
            self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        cx, cy = w / 2, h / 2
        R = min(w, h) / 2 - 14

        p.setPen(QPen(QColor(theme.LINE), 10, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawArc(QRectF(cx - R, cy - R, 2 * R, 2 * R), 0, 360 * 16)

        frac = self._display / 100.0
        col = QColor(theme.CYAN) if frac > 0.5 else (QColor(theme.AMBER) if frac > 0.25 else QColor(theme.CORAL))
        pen = QPen(col, 10, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        span = int(-frac * 360 * 16)
        p.drawArc(QRectF(cx - R, cy - R, 2 * R, 2 * R), 90 * 16, span)

        ang = math.radians(90 - frac * 360)
        mx, my = cx + math.cos(ang) * R, cy - math.sin(ang) * R
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(255, 255, 255))
        p.drawEllipse(QPointF(mx, my), 6, 6)
        p.setBrush(col)
        p.drawEllipse(QPointF(mx, my), 3.2, 3.2)

        p.setPen(QColor(theme.TEXT))
        f = QFont(theme.FONT_FAMILY.split(",")[0].strip(), 28)
        f.setBold(True)
        p.setFont(f)
        p.drawText(QRectF(0, cy - 26, w, 36), Qt.AlignmentFlag.AlignCenter, f"{self._display:.0f}")
        p.setPen(QColor(theme.TEXT_DIM))
        f2 = QFont(theme.FONT_FAMILY.split(",")[0].strip(), 9)
        p.setFont(f2)
        p.drawText(QRectF(0, cy + 6, w, 20), Qt.AlignmentFlag.AlignCenter, "MISSION SCORE")
        p.end()


class StatCard(QFrame):
    def __init__(self, label, color, parent=None):
        super().__init__(parent)
        self.setProperty("role", "card")
        self.setStyleSheet(f"QFrame[role='card'] {{ border-top: 3px solid {color}; }}")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 14, 16, 14)
        tag = QLabel(label)
        tag.setStyleSheet(f"color:{theme.TEXT_DIM}; font-size:11px; font-weight:700; letter-spacing:1px;")
        lay.addWidget(tag)
        self.val = QLabel("—")
        self.val.setStyleSheet(f"color:{theme.TEXT}; font-size:26px; font-weight:700; font-family:{theme.MONO_FAMILY};")
        lay.addWidget(self.val)
        self.unit = QLabel("")
        self.unit.setStyleSheet(f"color:{color}; font-size:11px; font-weight:600;")
        lay.addWidget(self.unit)

    def set_value(self, value, unit, sci=False):
        self.val.setText(fmt(value, sci))
        self.unit.setText(unit)


class DashboardWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(18)

        hero = QFrame()
        hero.setProperty("role", "panel")
        hero_lay = QHBoxLayout(hero)
        hero_lay.setContentsMargins(28, 24, 28, 24)
        hero_lay.setSpacing(24)

        left = QVBoxLayout()
        tag = QLabel("MISSION OVERVIEW")
        tag.setProperty("role", "tag")
        left.addWidget(tag)
        title = QLabel("Tune the payload.\nWatch the Earth answer.")
        title.setProperty("role", "h1")
        title.setStyleSheet(f"font-size:26px; font-weight:800; color:{theme.TEXT};")
        left.addWidget(title)
        desc = QLabel("OPTIEO / EOSSP is a live physics model of an optical Earth-observation "
                       "payload — 26 inputs across five subsystems drive 39 recomputed outputs "
                       "across four engines: Spatial, Orbital/Temporal, Spectral and Radiometric.")
        desc.setWordWrap(True)
        desc.setStyleSheet(f"color:{theme.TEXT_DIM}; font-size:12.5px; margin-top:6px;")
        left.addWidget(desc)

        stats_row = QHBoxLayout()
        stats_row.setSpacing(12)
        self.card_gsd = StatCard("GROUND SAMPLE DISTANCE", theme.SPATIAL)
        self.card_snr = StatCard("FINAL SNR", theme.RADIOMETRIC)
        self.card_revisit = StatCard("ACTUAL REVISIT TIME", theme.ORBITAL)
        for c in (self.card_gsd, self.card_snr, self.card_revisit):
            stats_row.addWidget(c)
        left.addSpacing(10)
        left.addLayout(stats_row)
        left.addStretch()
        hero_lay.addLayout(left, 3)

        right = QVBoxLayout()
        self.orbit_scene = OrbitScene()
        right.addWidget(self.orbit_scene)
        hero_lay.addLayout(right, 2)

        outer.addWidget(hero)

        # efficiency band
        eff_frame = QFrame()
        eff_frame.setProperty("role", "panel")
        eff_lay = QHBoxLayout(eff_frame)
        eff_lay.setContentsMargins(28, 22, 28, 22)
        eff_lay.setSpacing(26)
        eff_title_box = QVBoxLayout()
        et = QLabel("SYSTEM HEALTH")
        et.setProperty("role", "tag")
        eff_title_box.addWidget(et)
        et2 = QLabel("Mission Efficiency Index")
        et2.setProperty("role", "h2")
        eff_title_box.addWidget(et2)
        eff_title_box.addStretch()
        eff_lay.addLayout(eff_title_box, 1)

        self.ring = RingGauge()
        eff_lay.addWidget(self.ring)

        breakdown = QGridLayout()
        breakdown.setHorizontalSpacing(18)
        breakdown.setVerticalSpacing(10)
        self.bars = {}
        for i, (key, label, color) in enumerate([
            ("spatial", "Spatial Resolution", theme.SPATIAL),
            ("radiometric", "Radiometric SNR", theme.RADIOMETRIC),
            ("temporal", "Revisit Cadence", theme.ORBITAL),
            ("dynamic", "Dynamic Range", theme.VIOLET),
        ]):
            lbl = QLabel(label)
            lbl.setStyleSheet(f"color:{theme.TEXT_DIM}; font-size:11px; font-weight:600;")
            track = QFrame()
            track.setFixedHeight(8)
            track.setStyleSheet(f"background:{theme.LINE}; border-radius:4px;")
            fill = QFrame(track)
            fill.setStyleSheet(f"background:{color}; border-radius:4px;")
            fill.setGeometry(0, 0, 0, 8)
            val_lbl = QLabel("0")
            val_lbl.setStyleSheet(f"color:{color}; font-size:11px; font-weight:700; font-family:{theme.MONO_FAMILY};")
            row = QHBoxLayout()
            row.addWidget(lbl)
            row.addStretch()
            row.addWidget(val_lbl)
            breakdown.addLayout(row, i, 0)
            breakdown.addWidget(track, i, 1)
            self.bars[key] = (track, fill, val_lbl)
        eff_lay.addLayout(breakdown, 2)
        outer.addWidget(eff_frame)
        outer.addStretch()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        for track, fill, _ in self.bars.values():
            frac = fill.property("frac") or 0
            fill.setGeometry(0, 0, int(track.width() * frac), 8)

    def update_from_state(self, P):
        O = compute_all(P)
        self.card_gsd.set_value(O["GSD"], "m")
        self.card_snr.set_value(O["finalSNR"], "")
        self.card_revisit.set_value(O["actualRevisit"], "days")
        eff = efficiency(O)
        self.ring.set_value(eff["overall"])
        for key in ("spatial", "radiometric", "temporal", "dynamic"):
            track, fill, val_lbl = self.bars[key]
            frac = max(0.0, min(1.0, eff[key] / 100.0))
            fill.setProperty("frac", frac)
            fill.setGeometry(0, 0, int(track.width() * frac), 8)
            val_lbl.setText(f"{eff[key]:.0f}")
