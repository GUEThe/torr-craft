"""Rendering for gate valves mounted directly between chamber flanges."""

import math

from PySide2.QtCore import QPointF, Qt
from PySide2.QtGui import QColor, QPen, QPolygonF

from .. import theme
from .pipe import orthogonal_points


def _c(hex_value, alpha=None):
    color = QColor(hex_value)
    if alpha is not None:
        color.setAlpha(alpha)
    return color


def _segment(a, b):
    dx = b.x() - a.x()
    dy = b.y() - a.y()
    length = math.hypot(dx, dy)
    if length <= 0.1:
        return None
    return dx / length, dy / length, length


def _draw_collar(p, point, ux, uy, color, active):
    """Draw a flange plate perpendicular to the local flange axis."""
    nx, ny = -uy, ux
    half = 8.0
    a = QPointF(point.x() - nx * half, point.y() - ny * half)
    b = QPointF(point.x() + nx * half, point.y() + ny * half)
    p.setPen(QPen(_c(theme.VIOLET, 205 if active else 125), 3.4))
    p.drawLine(a, b)
    p.setPen(QPen(QColor("#0b1626"), 1.0))
    p.drawLine(a, b)
    p.setBrush(color)
    p.setPen(Qt.NoPen)
    for factor in (-0.62, 0.62):
        p.drawEllipse(
            QPointF(point.x() + nx * half * factor, point.y() + ny * half * factor),
            1.25,
            1.25,
        )


def paint_flange_link(painter, gate_rect, chamber_rect, active=False, highlighted=False):
    """Draw a flanged bellows link; deliberately unlike a flowing pipe."""
    points = orthogonal_points(gate_rect, chamber_rect)
    if len(points) < 2:
        return

    accent_alpha = 210 if highlighted else (155 if active else 95)
    polygon = QPolygonF(points)

    if highlighted:
        halo = _c(theme.VIOLET, 26)
        pen = QPen(halo, 14)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawPolyline(polygon)

    shadow = QPen(QColor(0, 0, 0, 95), 9.0)
    shadow.setCapStyle(Qt.RoundCap)
    shadow.setJoinStyle(Qt.RoundJoin)
    painter.setPen(shadow)
    painter.drawPolyline(polygon)

    band = QPen(QColor("#121d2d" if not active else "#172033"), 7.0)
    band.setCapStyle(Qt.RoundCap)
    band.setJoinStyle(Qt.RoundJoin)
    painter.setPen(band)
    painter.drawPolyline(polygon)

    center = QPen(_c(theme.VIOLET, accent_alpha), 1.5)
    center.setCapStyle(Qt.RoundCap)
    center.setJoinStyle(Qt.RoundJoin)
    painter.setPen(center)
    painter.drawPolyline(polygon)

    # Bellows ribs make the inline flange visually distinct from piping.
    painter.setPen(QPen(_c(theme.VIOLET, accent_alpha - 45), 1.0))
    for index in range(len(points) - 1):
        a = points[index]
        b = points[index + 1]
        result = _segment(a, b)
        if result is None:
            continue
        ux, uy, length = result
        nx, ny = -uy, ux
        distance = 7.0
        while distance < length - 5.0:
            cx = a.x() + ux * distance
            cy = a.y() + uy * distance
            painter.drawLine(
                QPointF(cx - nx * 3.4, cy - ny * 3.4),
                QPointF(cx + nx * 3.4, cy + ny * 3.4),
            )
            distance += 10.0

    bolt_color = _c(theme.VIOLET, 225 if active else 145)
    first = _segment(points[0], points[1])
    last = _segment(points[-2], points[-1])
    if first:
        _draw_collar(painter, points[0], first[0], first[1], bolt_color, active)
    if last:
        _draw_collar(painter, points[-1], last[0], last[1], bolt_color, active)

    # A small double-ring at each end signals a bolted flange, not a weld/pipe.
    for point in (points[0], points[-1]):
        painter.setBrush(QColor("#08131f"))
        painter.setPen(QPen(_c(theme.VIOLET, 215 if active else 125), 1.1))
        painter.drawEllipse(point, 3.2, 3.2)
