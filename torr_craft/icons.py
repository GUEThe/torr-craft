"""Vector icons drawn with QPainter so the app stays dependency-free."""

import math

from PySide2.QtCore import QPointF, QRectF, Qt
from PySide2.QtGui import (
    QColor,
    QIcon,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
    QPolygonF,
)

from . import theme


def _pen(painter, color, width=2.0):
    pen = QPen(QColor(color))
    pen.setWidthF(width)
    pen.setCapStyle(Qt.RoundCap)
    pen.setJoinStyle(Qt.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(Qt.NoBrush)
    return pen


def _fill(painter, color, alpha=36):
    c = QColor(color)
    c.setAlpha(alpha)
    painter.setBrush(c)
    painter.setPen(Qt.NoPen)


def draw_component_glyph(painter, kind, rect, accent, stroke=2.0):
    """Draw a 48x48 design-space glyph scaled into *rect*."""
    painter.save()
    painter.setRenderHint(QPainter.Antialiasing, True)
    painter.translate(rect.topLeft())
    scale = min(rect.width(), rect.height()) / 48.0
    painter.scale(scale, scale)

    c = QColor(accent)
    soft = QColor(accent)
    soft.setAlpha(30)

    if kind == "chamber":
        _fill(painter, accent, 26)
        _pen(painter, accent, stroke)
        painter.drawRoundedRect(QRectF(6, 9, 36, 29), 5, 5)
        painter.setPen(QPen(QColor(accent), stroke * 0.7))
        painter.drawRoundedRect(QRectF(11, 14, 19, 19), 3, 3)
        painter.setBrush(QColor(accent))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPointF(35, 23.5), 2.5, 2.5)
        painter.setPen(QPen(QColor(accent), stroke))
        painter.drawLine(QPointF(2, 23.5), QPointF(6, 23.5))
        painter.drawLine(QPointF(42, 23.5), QPointF(46, 23.5))
        painter.drawLine(QPointF(24, 38), QPointF(24, 43))
        painter.drawLine(QPointF(17, 43), QPointF(31, 43))
        painter.drawLine(QPointF(14, 9), QPointF(14, 6))
        painter.drawLine(QPointF(34, 9), QPointF(34, 6))

    elif kind == "turbo":
        _fill(painter, accent, 24)
        _pen(painter, accent, stroke)
        painter.drawRoundedRect(QRectF(5, 19, 35, 18), 5, 5)
        painter.drawEllipse(QPointF(17, 28), 8.0, 8.0)
        painter.setPen(QPen(QColor(accent), stroke * 0.7))
        for i in range(6):
            angle = math.radians(i * 60 + 15)
            painter.drawLine(
                QPointF(17 + math.cos(angle) * 3.2, 28 + math.sin(angle) * 3.2),
                QPointF(17 + math.cos(angle) * 7.0, 28 + math.sin(angle) * 7.0),
            )
        painter.setPen(QPen(QColor(accent), stroke))
        painter.drawLine(QPointF(31, 19), QPointF(31, 13))
        painter.drawLine(QPointF(27, 13), QPointF(35, 13))
        painter.drawLine(QPointF(40, 24), QPointF(45, 24))
        painter.drawLine(QPointF(11, 37), QPointF(11, 41))
        painter.drawLine(QPointF(34, 37), QPointF(34, 41))
        painter.drawLine(QPointF(7, 41), QPointF(38, 41))

    elif kind == "dry":
        _fill(painter, accent, 24)
        _pen(painter, accent, stroke)
        painter.drawRoundedRect(QRectF(5, 20, 37, 17), 5, 5)
        painter.drawEllipse(QPointF(17, 28.5), 7.2, 7.2)
        painter.drawEllipse(QPointF(30, 28.5), 7.2, 7.2)
        painter.setPen(QPen(QColor(accent), stroke * 0.6))
        painter.drawEllipse(QPointF(17, 28.5), 2.6, 2.6)
        painter.drawEllipse(QPointF(30, 28.5), 2.6, 2.6)
        painter.setPen(QPen(QColor(accent), stroke))
        painter.drawLine(QPointF(12, 20), QPointF(12, 14))
        painter.drawLine(QPointF(8, 14), QPointF(16, 14))
        painter.drawLine(QPointF(35, 20), QPointF(41, 20))
        painter.drawLine(QPointF(9, 37), QPointF(9, 41))
        painter.drawLine(QPointF(38, 37), QPointF(38, 41))

    elif kind == "angle":
        _fill(painter, accent, 24)
        _pen(painter, accent, stroke)
        painter.drawLine(QPointF(3, 31), QPointF(14, 31))
        painter.drawLine(QPointF(34, 31), QPointF(45, 31))
        body = QPolygonF(
            [
                QPointF(14, 23),
                QPointF(24, 31),
                QPointF(14, 39),
                QPointF(14, 23),
            ]
        )
        painter.drawPolygon(body)
        body2 = QPolygonF(
            [
                QPointF(34, 23),
                QPointF(24, 31),
                QPointF(34, 39),
                QPointF(34, 23),
            ]
        )
        painter.drawPolygon(body2)
        painter.drawLine(QPointF(24, 31), QPointF(24, 18))
        painter.drawLine(QPointF(19, 18), QPointF(29, 18))
        painter.setBrush(QColor(accent))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPointF(24, 31), 2.0, 2.0)

    elif kind == "gate":
        _fill(painter, accent, 24)
        _pen(painter, accent, stroke)
        painter.drawLine(QPointF(3, 30), QPointF(14, 30))
        painter.drawLine(QPointF(34, 30), QPointF(45, 30))
        painter.drawRect(QRectF(13, 20, 5, 20))
        painter.drawRect(QRectF(30, 20, 5, 20))
        painter.drawLine(QPointF(18, 20), QPointF(30, 20))
        painter.drawLine(QPointF(18, 40), QPointF(30, 40))
        painter.drawLine(QPointF(24, 20), QPointF(24, 13))
        painter.drawLine(QPointF(18, 13), QPointF(30, 13))
        painter.setBrush(QColor(accent))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPointF(24, 30), 2.0, 2.0)

    elif kind == "pipe":
        _pen(painter, accent, stroke + 0.4)
        path = QPainterPath(QPointF(5, 13))
        path.lineTo(22, 13)
        path.lineTo(22, 33)
        path.lineTo(43, 33)
        painter.drawPath(path)
        painter.setBrush(QColor(accent))
        painter.setPen(QPen(QColor("#07101d"), 1.5))
        painter.drawEllipse(QPointF(5, 13), 4.0, 4.0)
        painter.drawEllipse(QPointF(43, 33), 4.0, 4.0)
        painter.setPen(QPen(QColor(accent), stroke * 0.7))
        painter.drawLine(QPointF(22, 22), QPointF(22, 28))

    else:
        _pen(painter, accent, stroke)
        painter.drawRoundedRect(QRectF(9, 9, 30, 30), 6, 6)

    painter.restore()


def component_pixmap(kind, accent, size=56):
    pix = QPixmap(size, size)
    pix.fill(Qt.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.Antialiasing, True)
    draw_component_glyph(p, kind, QRectF(4, 4, size - 8, size - 8), accent, 2.0)
    p.end()
    return pix


def _tool_glyph(painter, kind, c):
    accent = QColor(c)
    _pen(painter, accent, 2.0)

    if kind == "cursor":
        path = QPolygonF(
            [
                QPointF(10, 7),
                QPointF(33, 22),
                QPointF(23, 24),
                QPointF(29, 36),
                QPointF(24, 38),
                QPointF(18, 26),
                QPointF(10, 33),
            ]
        )
        painter.setBrush(QColor(c))
        painter.setPen(QPen(QColor("#07101d"), 1.2))
        painter.drawPolygon(path)

    elif kind == "pipe":
        path = QPainterPath(QPointF(8, 13))
        path.lineTo(23, 13)
        path.lineTo(23, 31)
        path.lineTo(40, 31)
        painter.drawPath(path)
        painter.setBrush(accent)
        painter.setPen(QPen(QColor("#07101d"), 1.2))
        painter.drawEllipse(QPointF(8, 13), 3.5, 3.5)
        painter.drawEllipse(QPointF(40, 31), 3.5, 3.5)
        painter.drawLine(QPointF(23, 22), QPointF(23, 27))

    elif kind == "delete":
        painter.drawLine(QPointF(13, 15), QPointF(35, 15))
        painter.drawLine(QPointF(18, 10), QPointF(30, 10))
        painter.drawRoundedRect(QRectF(16, 15, 16, 23), 3, 3)
        painter.drawLine(QPointF(21, 20), QPointF(21, 32))
        painter.drawLine(QPointF(27, 20), QPointF(27, 32))

    elif kind == "import":
        painter.drawLine(QPointF(24, 7), QPointF(24, 28))
        painter.drawLine(QPointF(16, 20), QPointF(24, 28))
        painter.drawLine(QPointF(32, 20), QPointF(24, 28))
        painter.drawLine(QPointF(9, 30), QPointF(9, 38))
        painter.drawLine(QPointF(9, 38), QPointF(39, 38))
        painter.drawLine(QPointF(39, 30), QPointF(39, 38))

    elif kind == "export":
        painter.drawLine(QPointF(24, 29), QPointF(24, 8))
        painter.drawLine(QPointF(16, 16), QPointF(24, 8))
        painter.drawLine(QPointF(32, 16), QPointF(24, 8))
        painter.drawLine(QPointF(9, 30), QPointF(9, 38))
        painter.drawLine(QPointF(9, 38), QPointF(39, 38))
        painter.drawLine(QPointF(39, 30), QPointF(39, 38))

    elif kind == "new":
        painter.drawRoundedRect(QRectF(11, 8, 25, 32), 3, 3)
        painter.drawLine(QPointF(29, 8), QPointF(36, 15))
        painter.drawLine(QPointF(29, 8), QPointF(29, 15))
        painter.drawLine(QPointF(29, 15), QPointF(36, 15))
        painter.drawLine(QPointF(17, 24), QPointF(30, 24))
        painter.drawLine(QPointF(17, 30), QPointF(27, 30))

    elif kind == "demo":
        painter.drawRect(QRectF(8, 12, 25, 23))
        painter.drawLine(QPointF(33, 18), QPointF(40, 14))
        painter.drawLine(QPointF(40, 14), QPointF(40, 33))
        painter.drawLine(QPointF(40, 33), QPointF(33, 29))
        painter.setBrush(accent)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPointF(15, 37), 2.8, 2.8)
        painter.drawEllipse(QPointF(33, 37), 2.8, 2.8)

    elif kind == "lock":
        painter.drawRoundedRect(QRectF(12, 21, 24, 18), 4, 4)
        path = QPainterPath(QPointF(17, 21))
        path.lineTo(17, 16)
        path.cubicTo(17, 8, 31, 8, 31, 16)
        path.lineTo(31, 21)
        painter.drawPath(path)
        painter.setBrush(accent)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPointF(24, 29), 2.2, 2.2)

    elif kind == "grid":
        painter.drawRect(QRectF(9, 9, 30, 30))
        painter.drawLine(QPointF(19, 9), QPointF(19, 39))
        painter.drawLine(QPointF(29, 9), QPointF(29, 39))
        painter.drawLine(QPointF(9, 19), QPointF(39, 19))
        painter.drawLine(QPointF(9, 29), QPointF(39, 29))

    elif kind == "play":
        painter.setBrush(accent)
        painter.setPen(Qt.NoPen)
        painter.drawPolygon(
            QPolygonF([QPointF(17, 10), QPointF(37, 24), QPointF(17, 38)])
        )

    elif kind == "pause":
        painter.setBrush(accent)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(QRectF(14, 10, 6, 28), 2, 2)
        painter.drawRoundedRect(QRectF(28, 10, 6, 28), 2, 2)

    elif kind == "more":
        painter.setBrush(accent)
        painter.setPen(Qt.NoPen)
        for x in (13, 24, 35):
            painter.drawEllipse(QPointF(x, 24), 2.4, 2.4)

    elif kind == "plus":
        painter.drawLine(QPointF(24, 9), QPointF(24, 39))
        painter.drawLine(QPointF(9, 24), QPointF(39, 24))

    elif kind == "fit":
        painter.drawLine(QPointF(9, 17), QPointF(9, 9))
        painter.drawLine(QPointF(9, 9), QPointF(17, 9))
        painter.drawLine(QPointF(31, 9), QPointF(39, 9))
        painter.drawLine(QPointF(39, 9), QPointF(39, 17))
        painter.drawLine(QPointF(39, 31), QPointF(39, 39))
        painter.drawLine(QPointF(39, 39), QPointF(31, 39))
        painter.drawLine(QPointF(17, 39), QPointF(9, 39))
        painter.drawLine(QPointF(9, 39), QPointF(9, 31))
        painter.drawRect(QRectF(18, 18, 12, 12))

    elif kind == "help":
        painter.drawEllipse(QRectF(9, 9, 30, 30))
        painter.drawLine(QPointF(18, 18), QPointF(22, 15))
        painter.drawLine(QPointF(22, 15), QPointF(27, 17))
        painter.drawLine(QPointF(27, 17), QPointF(27, 22))
        painter.drawLine(QPointF(27, 22), QPointF(24, 25))
        painter.drawLine(QPointF(24, 25), QPointF(24, 28))
        painter.setBrush(accent)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPointF(24, 34), 1.7, 1.7)

    else:
        painter.drawEllipse(QRectF(10, 10, 28, 28))


def make_icon(kind, color=theme.MUTED, size=20):
    pix = QPixmap(size, size)
    pix.fill(Qt.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.Antialiasing, True)
    p.scale(size / 48.0, size / 48.0)
    _tool_glyph(p, kind, color)
    p.end()
    return QIcon(pix)


def app_icon(size=128):
    pix = QPixmap(size, size)
    pix.fill(Qt.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.Antialiasing, True)
    p.scale(size / 128.0, size / 128.0)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor("#0b1a2c"))
    p.drawRoundedRect(QRectF(2, 2, 124, 124), 26, 26)
    pen = QPen(QColor(theme.CYAN), 5.0)
    pen.setJoinStyle(Qt.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.NoBrush)
    p.drawPolyline(
        QPolygonF(
            [
                QPointF(28, 52),
                QPointF(50, 30),
                QPointF(78, 30),
                QPointF(100, 52),
                QPointF(100, 77),
                QPointF(78, 99),
                QPointF(50, 99),
                QPointF(28, 77),
                QPointF(28, 52),
            ]
        )
    )
    p.setPen(QPen(QColor(theme.CYAN), 7.0))
    p.drawLine(QPointF(44, 48), QPointF(84, 48))
    p.drawLine(QPointF(64, 48), QPointF(64, 84))
    p.setPen(QPen(QColor(theme.GREEN), 5.0))
    p.drawEllipse(QPointF(84, 76), 6, 6)
    p.end()
    return QIcon(pix)
