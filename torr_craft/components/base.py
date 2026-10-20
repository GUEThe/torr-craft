"""Base class for all vacuum components drawn on the canvas."""

from PySide2.QtCore import QPoint, QPointF, QRect, QRectF, Qt, Signal
from PySide2.QtGui import (
    QColor,
    QFont,
    QFontMetrics,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
)
from PySide2.QtWidgets import QWidget

from .. import theme
from ..device_specs import DeviceSpec


def _c(hex_value, alpha=None):
    c = QColor(hex_value)
    if alpha is not None:
        c.setAlpha(alpha)
    return c


class BaseDevice(QWidget):
    """Movable / resizable component with selection handles and status chrome."""

    clicked = Signal(object, object)
    doubleClicked = Signal(object)
    contextRequested = Signal(object, QPoint)
    geometryEdited = Signal(object)
    editCommitted = Signal(object, str)

    HANDLE_SIZE = 8
    HANDLES = (
        "top-left",
        "top",
        "top-right",
        "right",
        "bottom-right",
        "bottom",
        "bottom-left",
        "left",
    )

    def __init__(self, spec: DeviceSpec, parent=None):
        super().__init__(parent)
        self.spec = spec
        self.device_type = spec.key
        self.device_id = ""
        self.label = spec.default_label
        self.online = True
        self.switched_on = False
        self.target_speed = spec.default_speed
        self.display_speed = 0
        self.pressure = 1.0e-3
        self.canvas = parent
        self._selected = False
        self._hover = False
        self._mode = None
        self._start_rect = QRect()
        self._press_global = QPoint()
        self._did_interact = False
        self._phase = 0.0
        self._connect_source = False
        self._open_phase = 0.0
        self.setMinimumSize(*spec.min_size)
        self.setMouseTracking(True)
        self.setAttribute(Qt.WA_Hover, True)
        self.setFocusPolicy(Qt.NoFocus)
        self.setCursor(Qt.OpenHandCursor)

    # ------------------------------------------------------------------ state
    @property
    def selected(self):
        return self._selected

    def set_selected(self, value):
        value = bool(value)
        if value != self._selected:
            self._selected = value
            self.update()

    def set_connect_source(self, value):
        value = bool(value)
        if value != self._connect_source:
            self._connect_source = value
            self.update()

    def set_online(self, value):
        self.online = bool(value)
        self.update()

    def set_switched_on(self, value):
        self.switched_on = bool(value)
        self.update()

    def set_target_speed(self, value):
        self.target_speed = max(0, int(value))
        self.update()

    def set_pressure(self, value):
        self.pressure = float(value)
        self.update()

    def set_label(self, value):
        self.label = str(value)
        self.update()

    def set_geometry_rect(self, rect, notify=False):
        rect = QRect(rect)
        rect.setWidth(max(self.spec.min_size[0], rect.width()))
        rect.setHeight(max(self.spec.min_size[1], rect.height()))
        if self.canvas is not None:
            rect.moveLeft(max(0, min(rect.left(), self.canvas.width() - rect.width())))
            rect.moveTop(max(0, min(rect.top(), self.canvas.height() - rect.height())))
        self.setGeometry(rect)
        self.update()
        if notify:
            self.geometryEdited.emit(self)

    def tick(self, dt):
        pass

    # --------------------------------------------------------------- painting
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        r = QRectF(self.rect()).adjusted(1.5, 1.5, -1.5, -1.5)
        self.paint_device(p, r)

        if self._selected:
            pen = QPen(_c(self.spec.accent), 1.6)
            p.setPen(pen)
            p.setBrush(Qt.NoBrush)
            p.drawRoundedRect(r.adjusted(-0.5, -0.5, 0.5, 0.5), 13, 13)
            if self.canvas is None or not getattr(self.canvas, "editing_locked", False):
                self._paint_handles(p)
        elif self._connect_source:
            pen = QPen(_c(theme.AMBER), 2.0)
            pen.setStyle(Qt.DashLine)
            p.setPen(pen)
            p.setBrush(_c(theme.AMBER, 14))
            p.drawRoundedRect(r, 12, 12)
        elif self._hover:
            if self.canvas is not None and getattr(self.canvas, "connect_mode", False):
                pen = QPen(_c(self.spec.accent), 1.5)
                pen.setStyle(Qt.DashLine)
                p.setPen(pen)
                p.setBrush(_c(self.spec.accent, 13))
                p.drawRoundedRect(r, 12, 12)
            else:
                p.setPen(QPen(_c(self.spec.accent, 70), 1.1))
                p.setBrush(Qt.NoBrush)
                p.drawRoundedRect(r, 12, 12)

    def paint_device(self, painter, rect):
        self._paint_surface(painter, rect)

    # -- shared chrome ---------------------------------------------------------
    def _paint_surface(self, p, r):
        accent = QColor(self.spec.accent)

        p.setPen(Qt.NoPen)
        p.setBrush(QColor(0, 0, 0, 75))
        p.drawRoundedRect(r.translated(0, 2.4), 13, 13)

        gradient = QLinearGradient(r.topLeft(), r.bottomLeft())
        gradient.setColorAt(0.0, QColor("#18263b"))
        gradient.setColorAt(0.55, QColor("#111e31"))
        gradient.setColorAt(1.0, QColor("#0c1727"))
        p.setBrush(gradient)
        border = QColor("#31445d")
        p.setPen(QPen(border, 1.0))
        p.drawRoundedRect(r, 12, 12)

        inner = QLinearGradient(r.topLeft(), r.topRight())
        inner.setColorAt(0.0, _c(self.spec.accent, 22))
        inner.setColorAt(0.32, _c(self.spec.accent, 0))
        p.setBrush(inner)
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(r.adjusted(1, 1, -1, -1), 11, 11)

        tab = QRectF(r.left() + 12, r.top() + 11, 3.0, min(20.0, r.height() - 22))
        p.setBrush(accent)
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(tab, 1.5, 1.5)

    def _paint_identity(self, p, r, compact=False):
        accent = QColor(self.spec.accent)
        x = r.left() + 22
        top = r.top() + 9 if compact else r.top() + 10
        type_font = theme.font(7, QFont.DemiBold)
        type_font.setLetterSpacing(QFont.AbsoluteSpacing, 1.1)
        p.setFont(type_font)
        p.setPen(_c(self.spec.accent, 210))

        online_w = 0
        if self.spec.has_online:
            online_text = "在线" if self.online else "离线"
            state_color = _c(theme.GREEN) if self.online else _c(theme.DIM)
            f = theme.font(8, QFont.DemiBold)
            p.setFont(f)
            online_w = QFontMetrics(f).horizontalAdvance(online_text) + 16
            p.setPen(state_color)
            p.drawText(
                QRectF(r.right() - online_w - 5, top - 1, online_w, 13),
                Qt.AlignRight | Qt.AlignVCenter,
                online_text,
            )
            p.setBrush(state_color)
            p.setPen(Qt.NoPen)
            p.drawEllipse(
                QPointF(r.right() - online_w - 1, top + 5.2),
                2.6,
                2.6,
            )
            if self.online:
                p.setBrush(_c(theme.GREEN, 40))
                p.drawEllipse(
                    QPointF(r.right() - online_w - 1, top + 5.2),
                    5.2,
                    5.2,
                )

        reserve = online_w or (56 if (not self.spec.has_online and self.spec.has_pressure) else 0)
        available = r.width() - 44 - reserve
        p.setFont(type_font)
        p.setPen(_c(self.spec.accent, 210))
        english_text = self.spec.english
        if r.width() < 190:
            english_text = {
                "chamber": "CHAMBER",
                "angle": "ANGLE",
                "gate": "GATE",
                "turbo": "TURBO",
                "dry": "DRY",
            }.get(self.spec.key, english_text)
        if available >= 22:
            english = QFontMetrics(type_font).elidedText(english_text, Qt.ElideRight, int(available))
            p.drawText(QRectF(x, top, available, 12), Qt.AlignLeft | Qt.AlignVCenter, english)

        name_font = theme.font(10 if compact else 12, QFont.DemiBold)
        name_text = QFontMetrics(name_font).elidedText(self.label, Qt.ElideRight, int(max(30, r.width() - 40)))
        p.setFont(name_font)
        p.setPen(QColor(theme.TEXT))
        p.drawText(
            QRectF(x, top + 14, r.width() - 36, 20 if not compact else 16),
            Qt.AlignLeft | Qt.AlignVCenter,
            name_text,
        )

    def _paint_chip(self, p, rect, text, active=True, color=None):
        if color is None:
            color = theme.GREEN if active else "#94a3b8"
        bg = _c(color, 28)
        border = _c(color, 80)
        p.setBrush(bg)
        p.setPen(QPen(border, 1.0))
        p.drawRoundedRect(rect, rect.height() / 2.0, rect.height() / 2.0)
        p.setPen(QColor(color))
        p.setFont(theme.font(8, QFont.DemiBold))
        p.drawText(rect, Qt.AlignCenter, text)

    def _paint_handles(self, p):
        p.setBrush(QColor("#07111f"))
        p.setPen(QPen(_c(self.spec.accent), 1.2))
        for rect in self._handle_rects().values():
            p.drawRect(rect)

    def _handle_rects(self):
        w = self.width()
        h = self.height()
        inset = 2.0
        s = self.HANDLE_SIZE
        pts = {
            "top-left": (inset, inset),
            "top": (w / 2.0, inset),
            "top-right": (w - inset, inset),
            "right": (w - inset, h / 2.0),
            "bottom-right": (w - inset, h - inset),
            "bottom": (w / 2.0, h - inset),
            "bottom-left": (inset, h - inset),
            "left": (inset, h / 2.0),
        }
        return {
            name: QRectF(x - s / 2.0, y - s / 2.0, s, s)
            for name, (x, y) in pts.items()
        }

    # ------------------------------------------------------------ interaction
    def _handle_at(self, pos):
        if not self._selected:
            return None
        for name, rect in self._handle_rects().items():
            if rect.adjusted(-3, -3, 3, 3).contains(QPoint(pos)):
                return name
        return None

    @staticmethod
    def _cursor_for_handle(name):
        if name in ("top-left", "bottom-right"):
            return Qt.SizeFDiagCursor
        if name in ("top-right", "bottom-left"):
            return Qt.SizeBDiagCursor
        if name in ("left", "right"):
            return Qt.SizeHorCursor
        if name in ("top", "bottom"):
            return Qt.SizeVerCursor
        return Qt.OpenHandCursor

    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton:
            super().mousePressEvent(event)
            return

        canvas = self.canvas
        if canvas is not None and getattr(canvas, "connect_mode", False):
            canvas.handle_device_clicked(self)
            event.accept()
            return

        self.clicked.emit(self, event.modifiers())
        if canvas is not None:
            canvas.setFocus()

        if canvas is not None and getattr(canvas, "editing_locked", False):
            event.accept()
            return

        handle = self._handle_at(event.pos())
        self._mode = handle if handle else "move"
        self._start_rect = QRect(self.geometry())
        self._press_global = event.globalPos()
        self._did_interact = False
        self.setCursor(self._cursor_for_handle(handle or "move"))
        event.accept()

    def mouseMoveEvent(self, event):
        if self._mode is None:
            if self._selected and not (self.canvas and getattr(self.canvas, "editing_locked", False)):
                handle = self._handle_at(event.pos())
                self.setCursor(self._cursor_for_handle(handle) if handle else Qt.OpenHandCursor)
            event.accept()
            return

        if self.canvas is None:
            return
        delta = event.globalPos() - self._press_global
        if abs(delta.x()) + abs(delta.y()) > 0:
            self._did_interact = True

        snap = getattr(self.canvas, "snap_enabled", True) and not (event.modifiers() & Qt.AltModifier)
        step = 10 if snap else 1
        start = QRect(self._start_rect)
        canvas_w = self.canvas.width()
        canvas_h = self.canvas.height()

        if self._mode == "move":
            x = start.x() + delta.x()
            y = start.y() + delta.y()
            x = max(0, min(x, canvas_w - start.width()))
            y = max(0, min(y, canvas_h - start.height()))
            if snap:
                x = int(round(x / step) * step)
                y = int(round(y / step) * step)
                x = max(0, min(x, canvas_w - start.width()))
                y = max(0, min(y, canvas_h - start.height()))
            self.move(x, y)
        else:
            left = start.left()
            top = start.top()
            right = start.right()
            bottom = start.bottom()
            if "left" in self._mode:
                left = start.left() + delta.x()
            if "right" in self._mode:
                right = start.right() + delta.x()
            if "top" in self._mode:
                top = start.top() + delta.y()
            if "bottom" in self._mode:
                bottom = start.bottom() + delta.y()

            if snap:
                left = int(round(left / step) * step)
                top = int(round(top / step) * step)
                right = int(round(right / step) * step)
                bottom = int(round(bottom / step) * step)

            min_w, min_h = self.spec.min_size
            left = max(0, min(left, canvas_w - min_w))
            top = max(0, min(top, canvas_h - min_h))
            right = max(left + min_w, min(right, canvas_w - 1))
            bottom = max(top + min_h, min(bottom, canvas_h - 1))
            self.setGeometry(left, top, right - left + 1, bottom - top + 1)

        self.geometryEdited.emit(self)
        if self.canvas is not None:
            self.canvas.update()
        event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self._mode is not None:
            mode = self._mode
            self._mode = None
            self.setCursor(Qt.OpenHandCursor)
            if self._did_interact:
                self.geometryEdited.emit(self)
                self.editCommitted.emit(self, "调整元件几何" if mode != "move" else "移动元件")
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.canvas is not None and getattr(self.canvas, "connect_mode", False):
                self.canvas.handle_device_clicked(self)
            else:
                self.doubleClicked.emit(self)
            event.accept()
            return
        super().mouseDoubleClickEvent(event)

    def enterEvent(self, event):
        self._hover = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hover = False
        if self._mode is None:
            self.setCursor(Qt.OpenHandCursor)
        self.update()
        super().leaveEvent(event)

    def contextMenuEvent(self, event):
        if self.canvas is not None and getattr(self.canvas, "connect_mode", False):
            return
        self.clicked.emit(self, Qt.NoModifier)
        self.contextRequested.emit(self, event.globalPos())
        event.accept()


class PumpBase(BaseDevice):
    """Shared rendering and spin-up simulation for both pump types."""

    def __init__(self, spec, parent=None):
        super().__init__(spec, parent)
        self.target_speed = spec.default_speed
        self.display_speed = 0.0
        self.switched_on = False
        self.online = True

    def seed_display_speed(self):
        self.display_speed = float(self.target_speed) if (self.switched_on and self.online) else 0.0

    def tick(self, dt):
        if self.online:
            goal = float(self.target_speed if self.switched_on else 0)
            current = float(self.display_speed)
            if current < goal:
                rate = max(450.0, goal * 0.35)
                current = min(goal, current + rate * dt)
            elif current > goal:
                rate = max(700.0, current * 0.55)
                current = max(goal, current - rate * dt)
            self.display_speed = current
            if current > 1:
                speed_factor = max(0.3, current / max(1.0, float(self.target_speed or self.spec.default_speed)))
                self._phase = (self._phase + dt * (85.0 + 300.0 * speed_factor)) % 360.0
        self.update()

    def paint_device(self, p, r):
        self._paint_surface(p, r)
        self._paint_identity(p, r, compact=self.width() < 190)

        accent = QColor(self.spec.accent)
        rotor_d = min(52.0, r.height() * 0.44)
        has_rotor = self.width() >= 198 and self.height() >= 110
        if has_rotor:
            rotor_rect = QRectF(
                r.right() - rotor_d - 17,
                r.top() + (r.height() - rotor_d) / 2.0 + 4,
                rotor_d,
                rotor_d,
            )
            self._paint_rotors(p, rotor_rect, accent)
            speed_right = rotor_rect.left() - 8
        else:
            speed_right = r.right() - 14

        chip_text = self.spec.switch_on_text if self.switched_on else self.spec.switch_off_text
        chip_w = max(46.0, QFontMetrics(theme.font(8, QFont.DemiBold)).horizontalAdvance(chip_text) + 18)
        chip = QRectF(r.left() + 22, r.top() + 51, chip_w, 19)
        self._paint_chip(p, chip, chip_text, self.switched_on and self.online)

        speed_font = theme.font(20 if self.width() > 190 else 17, QFont.Bold, mono=True)
        p.setFont(speed_font)
        if self.online:
            speed_text = f"{int(round(self.display_speed)):,}"
            p.setPen(_c(theme.TEXT) if self.switched_on else _c("#aebed0"))
        else:
            speed_text = "--"
            p.setPen(_c(theme.DIM))
        number_rect = QRectF(r.left() + 20, r.bottom() - 34, max(40, speed_right - r.left() - 20), 25)
        p.drawText(number_rect, Qt.AlignLeft | Qt.AlignVCenter, speed_text)

        unit_font = theme.font(7, QFont.DemiBold)
        p.setFont(unit_font)
        p.setPen(_c(self.spec.accent, 190))
        unit_x = number_rect.left() + QFontMetrics(speed_font).horizontalAdvance(speed_text) + 5
        p.drawText(
            QRectF(unit_x, r.bottom() - 28, 34, 12),
            Qt.AlignLeft | Qt.AlignVCenter,
            self.spec.speed_unit,
        )

    def _paint_rotors(self, p, rect, accent):
        pass

    def _rotor(self, p, rect, accent, blades=6, phase=0.0):
        active = self.switched_on and self.online and self.display_speed > 1
        p.setPen(Qt.NoPen)
        ring = QColor(accent)
        ring.setAlpha(34 if not active else 42)
        p.setBrush(ring)
        p.drawEllipse(rect)
        p.setBrush(QColor("#0a1524"))
        p.setPen(QPen(_c(self.spec.accent, 95 if active else 45), 1.2))
        p.drawEllipse(rect.adjusted(3, 3, -3, -3))

        import math

        center = rect.center()
        radius = rect.width() * 0.31
        p.setPen(QPen(_c(self.spec.accent, 190 if active else 65), 1.4))
        for i in range(blades):
            angle = math.radians(i * (360.0 / blades) + self._phase)
            p.drawLine(
                center,
                QPointF(center.x() + math.cos(angle) * radius, center.y() + math.sin(angle) * radius),
            )
        p.setBrush(_c(self.spec.accent, 190 if active else 70))
        p.setPen(Qt.NoPen)
        p.drawEllipse(center, 3.4, 3.4)
        p.setBrush(_c(self.spec.accent, 35 if active else 12))
        p.drawEllipse(center, radius + 2, radius + 2)
