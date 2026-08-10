from PyQt6.QtCore import Qt, QRectF, pyqtSignal, QTimer
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QPainterPath, QFont
from PyQt6.QtWidgets import (QGraphicsView, QGraphicsScene, QGraphicsItem,
                              QGraphicsPathItem, QWidget, QVBoxLayout, QHBoxLayout,
                              QLabel, QPushButton, QGraphicsDropShadowEffect)
from .. import theme
from ..model import dependency_edges_for_engine, node_label

NODE_W, NODE_H, COL_GAP, ROW_GAP = 172, 46, 26, 70
DIM_OPACITY, EDGE_DIM = 0.14, 0.09
LANES = 16  # number of distinct "bus" horizontal levels used to fan out edges


class NodeItem(QGraphicsItem):
    def __init__(self, key, label, color, is_input, diagram):
        super().__init__()
        self.key, self.label, self.color = key, label, QColor(color)
        self.is_input, self.diagram = is_input, diagram
        self.setAcceptHoverEvents(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip(label)
        self._hover, self._opacity, self._highlighted = False, 1.0, False
        eff = QGraphicsDropShadowEffect()
        eff.setBlurRadius(18)
        eff.setOffset(0, 0)
        eff.setColor(QColor(self.color.red(), self.color.green(), self.color.blue(), 140))
        self.setGraphicsEffect(eff)

    def boundingRect(self):
        return QRectF(0, 0, NODE_W, NODE_H)

    def set_state(self, dim, highlighted):
        self._opacity = DIM_OPACITY if dim else 1.0
        self._highlighted = highlighted
        self.update()

    def hoverEnterEvent(self, event):
        self._hover = True
        self.update()

    def hoverLeaveEvent(self, event):
        self._hover = False
        self.update()

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.boundingRect()
        painter.setOpacity(self._opacity)
        base = QColor(14, 20, 36, 235) if self.is_input else QColor(10, 15, 27, 235)
        border = self.color if (self._highlighted or self._hover or not self.diagram.has_selection) else QColor(theme.LINE)
        border_w = 2.4 if self._highlighted else 1.3

        path = QPainterPath()
        path.addRoundedRect(rect, 10, 10)
        painter.fillPath(path, QBrush(base))

        accent = QRectF(0, 0, 4, NODE_H)
        accent_path = QPainterPath()
        accent_path.addRoundedRect(accent, 2, 2)
        painter.fillPath(accent_path, QBrush(self.color))

        painter.setPen(QPen(border, border_w))
        painter.drawPath(path)

        painter.setPen(QColor(theme.TEXT if (self._highlighted or not self.diagram.has_selection or self._hover) else theme.TEXT_DIM))
        font = QFont(theme.FONT_FAMILY.split(",")[0].strip(), 9)
        font.setBold(self._highlighted)
        painter.setFont(font)
        painter.drawText(rect.adjusted(12, 4, -8, -4),
                          Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft | Qt.TextFlag.TextWordWrap,
                          self.label)
        painter.setOpacity(1.0)

    def mousePressEvent(self, event):
        self.diagram.select_node(self.key)
        event.accept()


class EdgeItem(QGraphicsPathItem):
    def __init__(self, src_key, dst_key, color):
        super().__init__()
        self.src_key, self.dst_key, self.base_color = src_key, dst_key, QColor(color)
        self.setZValue(-1)

    def set_state(self, dim, highlighted):
        col = QColor(self.base_color)
        if highlighted:
            col.setAlpha(235)
            self.setPen(QPen(col, 2.6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        elif dim:
            col.setAlpha(int(255 * EDGE_DIM))
            self.setPen(QPen(col, 1.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        else:
            col.setAlpha(110)
            self.setPen(QPen(col, 1.3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        self.setZValue(3 if highlighted else -1)


class DependencyDiagramView(QGraphicsView):
    nodeSelected = pyqtSignal(str)

    def __init__(self, engine_id, parent=None):
        super().__init__(parent)
        self.engine_id, self.scene_ = engine_id, QGraphicsScene(self)
        self.setScene(self.scene_)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        # NoDrag (not ScrollHandDrag) so single clicks always reach nodes reliably;
        # panning is still available via the scrollbars / shift+wheel.
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setFrameShape(QGraphicsView.Shape.NoFrame)
        self.setStyleSheet("background: transparent;")
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.nodes, self.edges, self.adjacency = {}, [], {}
        self.selected_key, self.has_selection = None, False
        self._build()

    def _build(self):
        color = theme.ENGINE_COLORS[self.engine_id]
        in_keys, out_keys, edges_list = dependency_edges_for_engine(self.engine_id)

        for i, key in enumerate(in_keys):
            item = NodeItem(key, node_label(key), theme.TEXT_DIM, True, self)
            item.setPos(i * (NODE_W + COL_GAP), 0)
            self.scene_.addItem(item)
            self.nodes[key] = item

        cols = min(6, max(1, len(out_keys)))
        for idx, key in enumerate(out_keys):
            r, c = idx // cols, idx % cols
            item = NodeItem(key, node_label(key), color, False, self)
            item.setPos(c * (NODE_W + COL_GAP), NODE_H + ROW_GAP + r * (NODE_H + ROW_GAP * 0.6))
            self.scene_.addItem(item)
            self.nodes[key] = item

        self.adjacency = {k: set() for k in self.nodes}
        for src, dst in edges_list:
            if src not in self.nodes or dst not in self.nodes:
                continue
            self.adjacency[src].add(dst)
            self.adjacency[dst].add(src)
            e = EdgeItem(src, dst, color)
            self.scene_.addItem(e)
            self.edges.append(e)

        self._route_edges()
        self._apply_states()
        rect = self.scene_.itemsBoundingRect().adjusted(-40, -40, 40, 40)
        self.scene_.setSceneRect(rect)

    def _route_edges(self):
        """Orthogonal 'auto-bus' routing: each edge gets its own horizontal
        lane between the source row and the destination row so that parallel
        connectors fan out instead of drawing exactly on top of each other."""
        for i, e in enumerate(self.edges):
            src, dst = self.nodes[e.src_key], self.nodes[e.dst_key]
            top, bottom = (src, dst) if src.pos().y() <= dst.pos().y() else (dst, src)
            x1, y1 = top.pos().x() + NODE_W / 2, top.pos().y() + NODE_H
            x2, y2 = bottom.pos().x() + NODE_W / 2, bottom.pos().y()
            gap = max(y2 - y1, 12)
            lane = (i * 2654435761) % LANES  # simple hash spread, stable per edge
            frac = 0.16 + (lane / max(LANES - 1, 1)) * 0.68
            mid_y = y1 + gap * frac
            path = QPainterPath()
            path.moveTo(x1, y1)
            path.lineTo(x1, mid_y)
            path.lineTo(x2, mid_y)
            path.lineTo(x2, y2)
            e.setPath(path)

    def select_node(self, key):
        self.selected_key = None if self.selected_key == key else key
        self.has_selection = self.selected_key is not None
        # defer to next event-loop tick to avoid re-entrant paint issues
        QTimer.singleShot(0, self._apply_states)
        if key:
            self.nodeSelected.emit(key)

    def clear_selection(self):
        self.selected_key = None
        self.has_selection = False
        self._apply_states()

    def _apply_states(self):
        if not self.has_selection:
            for n in self.nodes.values():
                n.set_state(False, False)
            for e in self.edges:
                e.set_state(False, False)
            return
        related = self.adjacency.get(self.selected_key, set())
        keep = related | {self.selected_key}
        for k, n in self.nodes.items():
            n.set_state(k not in keep, k == self.selected_key)
        for e in self.edges:
            touches = self.selected_key in (e.src_key, e.dst_key)
            e.set_state(not touches, touches)

    def wheelEvent(self, event):
        factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        self.scale(factor, factor)

    def fit_view(self):
        self.resetTransform()
        rect = self.scene_.itemsBoundingRect()
        self.fitInView(rect, Qt.AspectRatioMode.KeepAspectRatio)


class DependencyDiagramWidget(QWidget):
    """One engine's interactive family-tree / dependency map, with a small
    header (legend + reset + clear-selection controls)."""
    nodeSelected = pyqtSignal(str)

    def __init__(self, engine_id, parent=None):
        super().__init__(parent)
        color = theme.ENGINE_COLORS[engine_id]
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(8)

        header = QHBoxLayout()
        legend_in = QLabel("●  Input parameter")
        legend_in.setStyleSheet(f"color:{theme.TEXT_DIM}; font-size:11px; font-weight:600;")
        legend_out = QLabel("●  Computed output")
        legend_out.setStyleSheet(f"color:{color}; font-size:11px; font-weight:600;")
        hint = QLabel("click a node to trace its connections  ·  scroll to zoom")
        hint.setStyleSheet(f"color:{theme.TEXT_FAINT}; font-size:11px;")
        header.addWidget(legend_in)
        header.addSpacing(14)
        header.addWidget(legend_out)
        header.addStretch()
        header.addWidget(hint)
        header.addSpacing(10)
        clear_btn = QPushButton("Clear selection")
        clear_btn.setProperty("role", "ghost")
        clear_btn.setFixedHeight(26)
        fit_btn = QPushButton("Fit view")
        fit_btn.setProperty("role", "ghost")
        fit_btn.setFixedHeight(26)
        header.addWidget(clear_btn)
        header.addWidget(fit_btn)
        outer.addLayout(header)

        self.view = DependencyDiagramView(engine_id, self)
        self.view.nodeSelected.connect(self.nodeSelected)
        outer.addWidget(self.view)

        clear_btn.clicked.connect(self.view.clear_selection)
        fit_btn.clicked.connect(self.view.fit_view)

    def select_key(self, key):
        """Programmatically select a node (e.g. from an Outputs-tab click)."""
        if key in self.view.nodes:
            self.view.selected_key = key
            self.view.has_selection = True
            self.view._apply_states()
