import math

from PyQt6.QtCore import Qt, QTimer, QRectF, QPointF, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QRadialGradient, QFont, QPainterPath
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
                              QSizePolicy)

from .. import theme
from ..model import compute_all, fmt
from .spectrum import SpectrumWidget
from .geometry_scene import ScanGeometryScene


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


class DashboardWidget(QWidget):
    #: forwarded from the embedded Scan Geometry controls
    paramChanged = pyqtSignal(str, float)

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
                       "payload — 28 inputs across six subsystems drive 44 recomputed outputs "
                       "across four engines: Spatial, Orbital/Temporal, Spectral and Radiometric.")
        desc.setWordWrap(True)
        desc.setStyleSheet(f"color:{theme.TEXT_DIM}; font-size:12.5px; margin-top:6px;")
        left.addWidget(desc)
        left.addStretch()
        hero_lay.addLayout(left, 3)

        right = QVBoxLayout()
        self.orbit_scene = OrbitScene()
        right.addWidget(self.orbit_scene)
        hero_lay.addLayout(right, 2)

        outer.addWidget(hero)

        # scan geometry — interactive, animated push-broom diagram. Altitude
        # and look angle can be dragged right here and the diagram (and the
        # rest of the app, via the shared parameter state) update live.
        geo_frame = QFrame()
        geo_frame.setProperty("role", "panel")
        geo_lay = QVBoxLayout(geo_frame)
        geo_lay.setContentsMargins(20, 16, 20, 16)
        geo_lay.setSpacing(8)
        geo_tag_row = QHBoxLayout()
        geo_tag = QLabel("SCAN GEOMETRY — INTERACTIVE")
        geo_tag.setProperty("role", "tag")
        geo_tag_row.addWidget(geo_tag)
        geo_tag_row.addStretch()
        geo_hint = QLabel("drag altitude / look angle below, or move Control Deck sliders")
        geo_hint.setStyleSheet(f"color:{theme.TEXT_FAINT}; font-size:10px; font-style:italic;")
        geo_tag_row.addWidget(geo_hint)
        geo_lay.addLayout(geo_tag_row)
        self.geometry_scene = ScanGeometryScene()
        geo_lay.addWidget(self.geometry_scene, 1)
        geo_lay.addWidget(self.geometry_scene.build_controls())
        self.geometry_scene.paramChanged.connect(self.paramChanged)
        outer.addWidget(geo_frame)

        # EM spectrum strip
        spec_frame = QFrame()
        spec_frame.setProperty("role", "panel")
        spec_lay = QVBoxLayout(spec_frame)
        spec_lay.setContentsMargins(20, 16, 20, 16)
        self.spectrum = SpectrumWidget()
        spec_lay.addWidget(self.spectrum)
        outer.addWidget(spec_frame)

        outer.addStretch()

    def update_from_state(self, P):
        O = compute_all(P)
        self.geometry_scene.update_from_state(P, O)
        self.spectrum.update_from_state(P)
