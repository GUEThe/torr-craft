"""Small reusable widgets: animated switches, brand mark, palette cards."""

import math

from PySide2.QtCore import (
    QEasingCurve,
    QPoint,
    QPointF,
    QRectF,
    QSize,
    Qt,
    QVariantAnimation,
    Signal,
)
from PySide2.QtGui import (
    QColor,
    QDrag,
    QFont,
    QFontMetrics,
    QLinearGradient,
    QPainter,
    QPen,
    QPixmap,
    QPolygonF,
)
from PySide2.QtWidgets import QAbstractButton, QApplication, QWidget

from . import icons, theme
from .device_specs import DEVICE_SPECS

COMPONENT_MIME = "application/x-torr-component"


class ToggleSwitch(QAbstractButton):
    """A compact animated switch, used for online / power / valve state."""

    def __init__(self, checked=False, parent=None, accent=theme.GREEN):
        super().__init__(parent)
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(42, 24)
        self._accent = QColor(accent)
        self._position = 1.0 if checked else 0.0
        self._animation = QVariantAnimation(self)
        self._animation.setDuration(170)
        self._animation.setEasingCurve(QEasingCurve.InOutCubic)
        self._animation.valueChanged.connect(self._on_animated)
        super().setChecked(checked)
        self.toggled.connect(self._animate)

    def sizeHint(self):
        return QSize(42, 24)

    def _animate(self, checked):
        self._animation.stop()
        self._animation.setStartValue(float(self._position))
        self._animation.setEndValue(1.0 if checked else 0.0)
        self._animation.start()

    def _on_animated(self, value):
        self._position = float(value)
        self.update()

    def setChecked(self, checked):
        super().setChecked(checked)
        if not self._animation.state():
            self._position = 1.0 if checked else 0.0
            self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        r = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        radius = r.height() / 2.0

        if self.isChecked():
            track = QColor(self._accent)
        else:
            track = QColor("#2b3c55")
        if not self.isEnabled():
            track.setAlpha(80)
        p.setPen(Qt.NoPen)
        p.setBrush(track)
        p.drawRoundedRect(r, radius, radius)

        if self.isChecked():
            highlight = QColor(self._accent)
            highlight.setAlpha(75)
            p.setBrush(highlight)
            p.drawRoundedRect(r.adjusted(1, 1, -1, -1), radius - 1, radius - 1)

        knob_size = r.height() - 6
        x = r.left() + 3 + self._position * (r.width() - knob_size - 6)
        knob = QRectF(x, r.top() + 3, knob_size, knob_size)
        p.setBrush(QColor("#04111f") if self.isChecked() else QColor("#b6c6d8"))
        p.setPen(Qt.NoPen)
        p.drawEllipse(knob)
        p.setBrush(QColor("#ffffff") if self.isChecked() else QColor("#eaf2fb"))
        p.drawEllipse(knob.adjusted(2.2, 2.2, -2.2, -2.2))

        if self.hasFocus():
            p.setBrush(Qt.NoBrush)
            p.setPen(QPen(QColor(theme.CYAN), 1))
            p.drawRoundedRect(r.adjusted(-1, -1, 1, 1), radius + 1, radius + 1)


class BrandMark(QWidget):
    def __init__(self, parent=None, size=42):
        super().__init__(parent)
        self.setFixedSize(size, size)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        w = self.width()
        h = self.height()
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#0b1b2e"))
        p.drawRoundedRect(QRectF(1, 1, w - 2, h - 2), w * 0.24, w * 0.24)

        glow = QColor(theme.CYAN)
        glow.setAlpha(28)
        p.setBrush(glow)
        p.drawEllipse(QRectF(w * 0.17, h * 0.17, w * 0.66, h * 0.66))

        pen = QPen(QColor(theme.CYAN), 2.0)
        pen.setJoinStyle(Qt.RoundJoin)
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)
        cx, cy = w / 2.0, h / 2.0
        radius = w * 0.29
        points = []
        for i in range(6):
            angle = math.radians(60 * i - 90)
            points.append(QPointF(cx + math.cos(angle) * radius, cy + math.sin(angle) * radius))
        p.drawPolygon(QPolygonF(points))
        p.setPen(QPen(QColor(theme.CYAN), 2.2))
        p.drawLine(QPointF(cx - radius * 0.45, cy - radius * 0.3), QPointF(cx + radius * 0.45, cy - radius * 0.3))
        p.drawLine(QPointF(cx, cy - radius * 0.3), QPointF(cx, cy + radius * 0.5))
        p.setBrush(QColor(theme.GREEN))
        p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(cx + radius * 0.48, cy + radius * 0.48), w * 0.055, w * 0.055)


class TypeGlyph(QWidget):
    def __init__(self, kind, accent, parent=None, size=46):
        super().__init__(parent)
        self._kind = kind
        self._accent = accent
        self.setFixedSize(size, size)

    def set_type(self, kind, accent):
        self._kind = kind
        self._accent = accent
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        r = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        bg = QColor(self._accent)
        bg.setAlpha(22)
        p.setBrush(bg)
        border = QColor(self._accent)
        border.setAlpha(75)
        p.setPen(QPen(border, 1))
        p.drawRoundedRect(r, 10, 10)
        icons.draw_component_glyph(p, self._kind, r.adjusted(8, 8, -8, -8), self._accent, 1.8)


class PaletteCard(QWidget):
    activated = Signal(str)

    def __init__(self, device_key, parent=None):
        super().__init__(parent)
        self.device_key = device_key
        self.spec = DEVICE_SPECS[device_key]
        self._hover = False
        self._pressed = False
        self._drag_origin = QPoint()
        self.setMinimumSize(88, 82)
        self.setMaximumHeight(86)
        self.setCursor(Qt.OpenHandCursor)
        self.setToolTip(f"{self.spec.label} · {self.spec.english}\n拖入画布，或单击添加到可见区域")
        self.setAttribute(Qt.WA_Hover, True)

    def sizeHint(self):
        return QSize(96, 84)

    def enterEvent(self, event):
        self._hover = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hover = False
        self._pressed = False
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._pressed = True
            self._drag_origin = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
            self.update()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not self._pressed:
            return
        if (event.pos() - self._drag_origin).manhattanLength() < QApplication.startDragDistance():
            return
        self._pressed = False
        self.setCursor(Qt.OpenHandCursor)
        drag = QDrag(self)
        mime = _component_mime(self.device_key)
        drag.setMimeData(mime)
        pix = icons.component_pixmap(self.spec.icon, self.spec.accent, 54)
        drag.setPixmap(pix)
        drag.setHotSpot(QPoint(pix.width() // 2, pix.height() // 2))
        drag.exec_(Qt.CopyAction)
        self._hover = False
        self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self._pressed:
            self._pressed = False
            self.setCursor(Qt.OpenHandCursor)
            if self.rect().contains(event.pos()):
                self.activated.emit(self.device_key)
        self.update()
        super().mouseReleaseEvent(event)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        r = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        accent = QColor(self.spec.accent)

        bg = QLinearGradient(r.topLeft(), r.bottomLeft())
        if self._hover:
            bg.setColorAt(0, QColor("#172941"))
            bg.setColorAt(1, QColor("#101e32"))
        else:
            bg.setColorAt(0, QColor("#101d30"))
            bg.setColorAt(1, QColor("#0c1727"))
        p.setBrush(bg)
        if self._hover or self._pressed:
            border = QColor(accent)
            border.setAlpha(150 if self._pressed else 110)
            p.setPen(QPen(border, 1.2))
        else:
            p.setPen(QPen(QColor(theme.BORDER), 1))
        p.drawRoundedRect(r, 11, 11)

        if self._hover:
            tint = QColor(accent)
            tint.setAlpha(10)
            p.setBrush(tint)
            p.setPen(Qt.NoPen)
            p.drawRoundedRect(r.adjusted(1, 1, -1, -1), 10, 10)

        icon_size = 38
        icon_rect = QRectF((self.width() - icon_size) / 2.0, 9, icon_size, icon_size)
        icons.draw_component_glyph(p, self.spec.icon, icon_rect, self.spec.accent, 2.0)

        p.setPen(QColor(theme.TEXT) if self._hover else QColor("#c7d5e6"))
        p.setFont(theme.font(11, QFont.DemiBold))
        p.drawText(QRectF(4, self.height() - 27, self.width() - 8, 17), Qt.AlignCenter, self.spec.label)

        p.setPen(QColor(accent) if self._hover else QColor(theme.DIM))
        p.setFont(theme.font(7, QFont.DemiBold))
        p.drawText(QRectF(4, self.height() - 12, self.width() - 8, 10), Qt.AlignCenter, self.spec.english)

        p.setBrush(QColor(accent) if self._hover else QColor(theme.BORDER))
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(QRectF(self.width() / 2.0 - 9, 3, 18, 2.2), 1.1, 1.1)


def _component_mime(device_key):
    from PySide2.QtCore import QMimeData

    mime = QMimeData()
    mime.setData(COMPONENT_MIME, device_key.encode("utf-8"))
    mime.setText(device_key)
    return mime


class Dot(QWidget):
    def __init__(self, color=theme.GREEN, parent=None, size=8):
        super().__init__(parent)
        self._color = QColor(color)
        self.setFixedSize(size, size)

    def set_color(self, color):
        self._color = QColor(color)
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        glow = QColor(self._color)
        glow.setAlpha(45)
        p.setPen(Qt.NoPen)
        p.setBrush(glow)
        p.drawEllipse(QRectF(0, 0, self.width(), self.height()))
        p.setBrush(self._color)
        p.drawEllipse(QRectF(2, 2, self.width() - 4, self.height() - 4))


def hline(color=theme.BORDER_SOFT):
    line = QWidget()
    line.setFixedHeight(1)
    line.setStyleSheet(f"background: {color}; border: none;")
    return line


def elide(text, font_obj, width):
    metrics = QFontMetrics(font_obj)
    return metrics.elidedText(text, Qt.ElideRight, int(width))
