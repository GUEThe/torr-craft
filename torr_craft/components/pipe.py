"""Data model and renderer for vacuum piping and routing modes."""

import math
from dataclasses import dataclass, field
from typing import List, Tuple

from PySide2.QtCore import QPointF, QRectF, Qt
from PySide2.QtGui import QColor, QPainter, QPen, QPolygonF
from PySide2.QtWidgets import QWidget

from .. import theme

ROUTE_MODES = ("auto", "straight", "custom")


@dataclass
class PipeModel:
    pipe_id: str
    source_id: str
    target_id: str
    route_mode: str = "auto"
    bend_points: List[Tuple[int, int]] = field(default_factory=list)


def orthogonal_points(a_rect, b_rect):
    """Route a clean orthogonal path between two rectangles."""
    a = QRectF(a_rect)
    b = QRectF(b_rect)
    ac = a.center()
    bc = b.center()
    dx = bc.x() - ac.x()
    dy = bc.y() - ac.y()

    if abs(dx) >= abs(dy):
        if dx >= 0:
            start = QPointF(a.right(), ac.y())
            end = QPointF(b.left(), bc.y())
        else:
            start = QPointF(a.left(), ac.y())
            end = QPointF(b.right(), bc.y())
        if abs(start.y() - end.y()) < 1.0:
            return [start, end]
        mid_x = (start.x() + end.x()) / 2.0
        return [start, QPointF(mid_x, start.y()), QPointF(mid_x, end.y()), end]

    if dy >= 0:
        start = QPointF(ac.x(), a.bottom())
        end = QPointF(bc.x(), b.top())
    else:
        start = QPointF(ac.x(), a.top())
        end = QPointF(bc.x(), b.bottom())
    if abs(start.x() - end.x()) < 1.0:
        return [start, end]
    mid_y = (start.y() + end.y()) / 2.0
    return [start, QPointF(start.x(), mid_y), QPointF(end.x(), mid_y), end]


def boundary_point(rect, toward):
    """Return where a ray from the rectangle centre to *toward* exits it."""
    r = QRectF(rect)
    center = r.center()
    dx = toward.x() - center.x()
    dy = toward.y() - center.y()
    if abs(dx) < 1e-9 and abs(dy) < 1e-9:
        return QPointF(center)

    factors = []
    if abs(dx) > 1e-9:
        factors.append((r.width() / 2.0) / abs(dx))
    if abs(dy) > 1e-9:
        factors.append((r.height() / 2.0) / abs(dy))
    factor = min(factors)
    return QPointF(center.x() + dx * factor, center.y() + dy * factor)


def straight_points(a_rect, b_rect):
    """Attach a direct centre-to-centre line to both rectangle boundaries."""
    a = QRectF(a_rect)
    b = QRectF(b_rect)
    return [boundary_point(a, b.center()), boundary_point(b, a.center())]


def custom_route_points(a_rect, b_rect, bend_points):
    """Build a free-form polyline through user-defined bend points."""
    bends = [QPointF(float(x), float(y)) for x, y in bend_points]
    if not bends:
        return straight_points(a_rect, b_rect)
    start = boundary_point(QRectF(a_rect), bends[0])
    end = boundary_point(QRectF(b_rect), bends[-1])
    points = [start] + bends + [end]
    cleaned = []
    for point in points:
        if cleaned and abs(point.x() - cleaned[-1].x()) < 0.01 and abs(
            point.y() - cleaned[-1].y()
        ) < 0.01:
            continue
        cleaned.append(point)
    return cleaned


def compute_pipe_points(route_mode, bend_points, a_rect, b_rect):
    if route_mode == "straight":
        return straight_points(a_rect, b_rect)
    if route_mode == "custom":
        return custom_route_points(a_rect, b_rect, bend_points)
    return orthogonal_points(a_rect, b_rect)


def encode_bend_points(points):
    return ";".join(f"{int(round(x))},{int(round(y))}" for x, y in points)


def decode_bend_points(text, limit=64):
    points = []
    for token in (text or "").split(";"):
        token = token.strip()
        if not token:
            continue
        parts = token.split(",")
        if len(parts) != 2:
            continue
        try:
            x = int(float(parts[0].strip()))
            y = int(float(parts[1].strip()))
        except (TypeError, ValueError):
            continue
        points.append((x, y))
        if len(points) >= limit:
            break
    return points


def distance_to_segment(point, start, end):
    px, py = point.x(), point.y()
    x1, y1 = start.x(), start.y()
    x2, y2 = end.x(), end.y()
    dx = x2 - x1
    dy = y2 - y1
    if dx == 0 and dy == 0:
        return math.hypot(px - x1, py - y1)
    t = ((px - x1) * dx + (py - y1) * dy) / float(dx * dx + dy * dy)
    t = max(0.0, min(1.0, t))
    return math.hypot(px - (x1 + t * dx), py - (y1 + t * dy))


def distance_to_path(point, points):
    if len(points) < 2:
        return float("inf")
    return min(
        distance_to_segment(point, points[i], points[i + 1])
        for i in range(len(points) - 1)
    )


class VacuumPipe(QWidget):
    """Qt Designer loadable placeholder for a pipe.

    Torr Craft itself paints pipes inside the canvas, but exporting a real
    QWidget class keeps the generated ``pyside2-uic`` module importable.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WA_NoSystemBackground, True)

    def _property(self, name, default=""):
        value = self.property(name)
        return default if value is None else str(value)

    def _endpoint(self, object_name):
        parent = self.parentWidget()
        if parent is None:
            return None
        target = parent.findChild(QWidget, object_name)
        if target is None:
            return None
        return QRectF(target.geometry())

    def paintEvent(self, event):
        source = self._endpoint(self._property("sourceId"))
        target = self._endpoint(self._property("targetId"))
        if source is None or target is None:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        source = source.translated(-self.x(), -self.y())
        target = target.translated(-self.x(), -self.y())
        mode = self._property("routeMode", "auto")
        bends = decode_bend_points(self._property("bendPoints", ""))
        points = compute_pipe_points(mode, bends, source, target)
        if len(points) < 2:
            return
        pen = QPen(QColor(theme.CYAN), 4.0)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        p.setPen(pen)
        p.drawPolyline(QPolygonF(points))


def paint_pipe(painter, points, selected=False, hovered=False, active=False, phase=0.0):
    if len(points) < 2:
        return
    polygon = QPolygonF(points)
    accent = QColor(theme.CYAN)
    if selected:
        halo = QColor(theme.CYAN)
        halo.setAlpha(32)
        pen = QPen(halo, 13)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawPolyline(polygon)

    shadow = QPen(QColor(0, 0, 0, 90), 8.0)
    shadow.setCapStyle(Qt.RoundCap)
    shadow.setJoinStyle(Qt.RoundJoin)
    painter.setPen(shadow)
    painter.drawPolyline(polygon)

    outer_color = QColor(theme.CYAN if (selected or hovered) else "#2a3d56")
    if selected:
        outer_color.setAlpha(220)
    outer = QPen(outer_color, 5.0 if (selected or hovered) else 4.4)
    outer.setCapStyle(Qt.RoundCap)
    outer.setJoinStyle(Qt.RoundJoin)
    painter.setPen(outer)
    painter.drawPolyline(polygon)

    inner_color = QColor(theme.CYAN if (selected or hovered) else "#455b74")
    if selected:
        inner_color.setAlpha(230)
    inner = QPen(inner_color, 1.6 if not (selected or hovered) else 2.0)
    inner.setCapStyle(Qt.RoundCap)
    inner.setJoinStyle(Qt.RoundJoin)
    painter.setPen(inner)
    painter.drawPolyline(polygon)

    if active:
        flow = QPen(accent, 2.2)
        flow.setCapStyle(Qt.RoundCap)
        flow.setJoinStyle(Qt.RoundJoin)
        flow.setDashPattern([2.2, 7.0])
        flow.setDashOffset(-phase)
        painter.setPen(flow)
        painter.drawPolyline(polygon)

    for point in (points[0], points[-1]):
        painter.setBrush(QColor("#08131f"))
        painter.setPen(QPen(QColor(theme.CYAN if active else "#5e748e"), 1.4))
        painter.drawEllipse(point, 4.0, 4.0)
        painter.setBrush(QColor(theme.CYAN if active else "#8aa0b8"))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(point, 1.6, 1.6)
