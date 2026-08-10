# starfield.py
import math, random
from PyQt6.QtCore import Qt, QTimer, QPointF
from PyQt6.QtGui import QPainter, QColor, QRadialGradient, QBrush
from PyQt6.QtWidgets import QWidget

class StarfieldWidget(QWidget):
    def __init__(self, parent=None, n_stars=180):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self._stars = []
        rnd = random.Random(42)
        for _ in range(n_stars):
            self._stars.append({
                "x": rnd.random(), "y": rnd.random(), "r": rnd.uniform(0.6, 2.2),
                "phase": rnd.uniform(0, 6.283), "speed": rnd.uniform(0.6, 1.8),
                "drift": rnd.uniform(0.0015, 0.006),
            })
        self._t = 0.0
        self._shooting = None
        self._shoot_timer = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(45)

    def _tick(self):
        self._t += 0.045
        self._shoot_timer -= 1
        if self._shoot_timer <= 0 and self._shooting is None and random.random() < 0.02:
            self._shooting = {"x": random.uniform(0.1, 0.6), "y": random.uniform(0.0, 0.3), "life": 0.0}
        if self._shooting is not None:
            self._shooting["life"] += 0.06
            if self._shooting["life"] > 1.0:
                self._shooting = None
                self._shoot_timer = random.randint(60, 200)
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        
        grad = QRadialGradient(w * 0.72, h * -0.05, max(w, h) * 1.15)
        grad.setColorAt(0.0, QColor(15, 26, 48))
        grad.setColorAt(0.45, QColor(6, 10, 20))
        grad.setColorAt(1.0, QColor(2, 4, 9))
        p.fillRect(self.rect(), QBrush(grad))
        
        for (cx, cy, col, rad) in [
            (0.18 + 0.01 * (self._t * 0.02 % 1), 0.22, QColor(77, 216, 255, 26), 0.55),
            (0.85 - 0.01 * (self._t * 0.015 % 1), 0.72, QColor(155, 140, 255, 22), 0.5),
        ]:
            g = QRadialGradient(w * cx, h * cy, max(w, h) * rad)
            g.setColorAt(0.0, col)
            g.setColorAt(1.0, QColor(col.red(), col.green(), col.blue(), 0))
            p.setBrush(QBrush(g))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRect(self.rect())

        for s in self._stars:
            tw = 0.55 + 0.45 * abs(math.sin(self._t * s["speed"] + s["phase"]))
            x = (s["x"] * w) % w
            y = (s["y"] * h) % h
            r = s["r"] * (0.85 + 0.3 * tw)
            alpha = int(90 + 165 * tw)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(231, 237, 247, alpha))
            p.drawEllipse(QPointF(x, y), r, r)

        if self._shooting is not None:
            life = self._shooting["life"]
            x0 = self._shooting["x"] * w + life * w * 0.28
            y0 = self._shooting["y"] * h + life * h * 0.22
            alpha = int(255 * (1 - life))
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(200, 230, 255, max(alpha, 0)))
            p.drawEllipse(QPointF(x0, y0), 2.0, 2.0)
        p.end()