"""Concrete vacuum components."""

import math

from PySide2.QtCore import QPointF, QRectF, Qt
from PySide2.QtGui import QColor, QFont, QFontMetrics, QLinearGradient, QPen, QPolygonF

from .. import theme
from ..device_specs import DEVICE_SPECS
from .base import BaseDevice, PumpBase, _c


class MolecularPumpWidget(PumpBase):
    def __init__(self, parent=None):
        super().__init__(DEVICE_SPECS["turbo"], parent)

    def _paint_rotors(self, p, rect, accent):
        self._rotor(p, rect, accent, blades=7)


class DryPumpWidget(PumpBase):
    def __init__(self, parent=None):
        super().__init__(DEVICE_SPECS["dry"], parent)

    def _paint_rotors(self, p, rect, accent):
        d = min(32.0, rect.width() * 0.62)
        left = QRectF(rect.left(), rect.center().y() - d / 2.0, d, d)
        right = QRectF(rect.right() - d, rect.center().y() - d / 2.0, d, d)
        self._rotor(p, left, accent, blades=4)
        self._rotor(p, right, accent, blades=4)


class ValveBase(BaseDevice):
    def __init__(self, spec, parent=None):
        super().__init__(spec, parent)
        self.switched_on = False
        self.online = True
        self._open_phase = 0.0

    def set_switched_on(self, value):
        super().set_switched_on(value)
        if not self.isVisible():
            self._open_phase = 1.0 if value else 0.0

    def seed_open_phase(self):
        self._open_phase = 1.0 if self.switched_on else 0.0

    def tick(self, dt):
        if not self.online:
            return
        goal = 1.0 if self.switched_on else 0.0
        current = self._open_phase
        speed = 5.5
        if current < goal:
            current = min(goal, current + dt * speed)
        elif current > goal:
            current = max(goal, current - dt * speed)
        if abs(current - self._open_phase) > 0.0001:
            self._open_phase = current
            self.update()

    def paint_device(self, p, r):
        self._paint_surface(p, r)
        self._paint_identity(p, r, compact=True)

        symbol = QRectF(r.left() + 17, r.top() + 38, r.width() - 34, max(16.0, r.height() - 64))
        self._paint_valve_symbol(p, symbol)

        chip_text = self.spec.switch_on_text if self.switched_on else self.spec.switch_off_text
        chip_w = max(48.0, QFontMetrics(theme.font(8, QFont.DemiBold)).horizontalAdvance(chip_text) + 20)
        chip = QRectF(r.center().x() - chip_w / 2.0, r.bottom() - 22, chip_w, 16)
        self._paint_chip(p, chip, chip_text, self.switched_on and self.online)

    def _paint_flanges(self, p, symbol):
        center_y = symbol.center().y()
        flange_w = 4.0
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#32445d"))
        p.drawRoundedRect(QRectF(symbol.left() - 1, center_y - 12, flange_w, 24), 1.5, 1.5)
        p.drawRoundedRect(QRectF(symbol.right() - flange_w + 1, center_y - 12, flange_w, 24), 1.5, 1.5)
        p.setPen(QPen(_c(self.spec.accent, 110), 4.0))
        p.drawLine(QPointF(symbol.left() - 12, center_y), QPointF(symbol.left() + 3, center_y))
        p.drawLine(QPointF(symbol.right() - 3, center_y), QPointF(symbol.right() + 12, center_y))

    def _paint_valve_symbol(self, p, symbol):
        pass


class AngleValveWidget(ValveBase):
    def __init__(self, parent=None):
        super().__init__(DEVICE_SPECS["angle"], parent)

    def _paint_valve_symbol(self, p, symbol):
        self._paint_flanges(p, symbol)
        cy = symbol.center().y()
        half = max(10.0, min(17.0, symbol.height() / 2.0))
        cx = symbol.center().x()
        body = QPolygonF(
            [
                QPointF(cx - 18, cy - half),
                QPointF(cx, cy),
                QPointF(cx - 18, cy + half),
                QPointF(cx - 18, cy - half),
            ]
        )
        body2 = QPolygonF(
            [
                QPointF(cx + 18, cy - half),
                QPointF(cx, cy),
                QPointF(cx + 18, cy + half),
                QPointF(cx + 18, cy - half),
            ]
        )
        active = self.switched_on and self.online
        fill = _c(self.spec.accent, 48 if active else 12)
        p.setBrush(fill)
        p.setPen(QPen(_c(self.spec.accent, 230 if active else 120), 1.7))
        p.drawPolygon(body)
        p.drawPolygon(body2)
        p.setBrush(_c(self.spec.accent, 210 if active else 70))
        p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(cx, cy), 3.0, 3.0)

        p.setPen(QPen(_c(self.spec.accent, 120), 1.0))
        p.drawLine(QPointF(cx - 5, cy - 3), QPointF(cx + 5, cy - 3))

        if active:
            p.setBrush(_c(theme.CYAN, 190))
            p.setPen(Qt.NoPen)
            p.drawEllipse(QPointF(cx + 8, cy), 1.8, 1.8)


class GateValveWidget(ValveBase):
    def __init__(self, parent=None):
        super().__init__(DEVICE_SPECS["gate"], parent)

    def _paint_valve_symbol(self, p, symbol):
        self._paint_flanges(p, symbol)
        cy = symbol.center().y()
        cx = symbol.center().x()
        body_h = min(30.0, max(20.0, symbol.height()))
        body = QRectF(cx - 22, cy - body_h / 2.0, 44, body_h)

        p.setBrush(QColor("#0a1524"))
        p.setPen(QPen(_c(self.spec.accent, 140), 1.4))
        p.drawRoundedRect(body, 3, 3)

        center_pen = QPen(_c(self.spec.accent, 95), 3.0)
        p.setPen(center_pen)
        p.drawLine(QPointF(body.left() + 3, cy), QPointF(body.right() - 3, cy))

        p.save()
        p.setClipRect(body.adjusted(1, 1, -1, -1))
        plate_h = body_h + 6
        lift = self._open_phase * (body_h + 9)
        plate = QRectF(cx - 5, body.top() - 3 - lift, 10, plate_h)
        p.setBrush(_c(self.spec.accent, 200 if self.switched_on else 230))
        p.setPen(QPen(_c("#f5f3ff"), 1.0))
        p.drawRoundedRect(plate, 1.5, 1.5)
        p.setPen(QPen(_c("#0b1626", 120), 1.0))
        for offset in (-8, 0, 8):
            p.drawLine(QPointF(cx - 3, cy + offset), QPointF(cx + 3, cy + offset))
        p.restore()

        p.setPen(QPen(_c(self.spec.accent, 170), 1.5))
        p.drawLine(QPointF(body.left() + 8, body.top()), QPointF(body.right() - 8, body.top()))

        if self.switched_on and self.online:
            p.setBrush(_c(theme.GREEN, 210))
            p.setPen(Qt.NoPen)
            p.drawEllipse(QPointF(body.right() + 5, body.top() + 3), 2.0, 2.0)


class ChamberWidget(BaseDevice):
    def __init__(self, parent=None):
        super().__init__(DEVICE_SPECS["chamber"], parent)
        self.pressure = 1.0e-5
        self.setCursor(Qt.OpenHandCursor)

    def paint_device(self, p, r):
        self._paint_surface(p, r)
        accent = QColor(self.spec.accent)

        # pressure vessel wall
        inner = r.adjusted(11, 48, -11, -42)
        if inner.width() > 8 and inner.height() > 8:
            grad = QLinearGradient(inner.topLeft(), inner.bottomRight())
            grad.setColorAt(0.0, QColor("#0a1626"))
            grad.setColorAt(0.62, QColor("#0d1d30"))
            grad.setColorAt(1.0, QColor("#10263a"))
            p.setBrush(grad)
            p.setPen(QPen(_c(self.spec.accent, 58), 1.0))
            p.drawRoundedRect(inner, 8, 8)

            p.setPen(QPen(_c(self.spec.accent, 22), 1.0))
            p.drawLine(QPointF(inner.left() + 8, inner.top() + 1), QPointF(inner.right() - 8, inner.top() + 1))

            bolt = _c(self.spec.accent, 75)
            p.setBrush(bolt)
            p.setPen(Qt.NoPen)
            for bx, by in (
                (inner.left() + 6, inner.top() + 6),
                (inner.right() - 6, inner.top() + 6),
                (inner.left() + 6, inner.bottom() - 6),
                (inner.right() - 6, inner.bottom() - 6),
            ):
                p.drawEllipse(QPointF(bx, by), 1.5, 1.5)

        self._paint_identity(p, r, compact=False)

        # chamber badge replaces the online badge
        badge_font = theme.font(7, QFont.DemiBold)
        p.setFont(badge_font)
        p.setPen(_c(theme.SKY, 210))
        badge = QRectF(r.right() - 70, r.top() + 8, 56, 14)
        p.drawText(badge, Qt.AlignRight | Qt.AlignVCenter, "VESSEL")

        pressure_text = self._format_pressure(self.pressure)
        p.setFont(theme.font(22 if self.width() > 230 else 18, QFont.Bold, mono=True))
        p.setPen(QColor(theme.TEXT))
        p.drawText(
            QRectF(r.left() + 24, r.top() + 58, r.width() * 0.56, 32),
            Qt.AlignLeft | Qt.AlignVCenter,
            pressure_text,
        )

        p.setFont(theme.font(8, QFont.DemiBold))
        p.setPen(_c(theme.MUTED))
        p.drawText(
            QRectF(r.left() + 25, r.top() + 90, 120, 13),
            Qt.AlignLeft | Qt.AlignVCenter,
            "PRESSURE · mbar",
        )

        if self.height() >= 140:
            p.setFont(theme.font(8, QFont.DemiBold))
            p.setPen(_c(theme.SKY, 180))
            state = "READY" if self.pressure < 1.0 else "ROUGH"
            p.drawText(
                QRectF(r.left() + 24, r.bottom() - 31, 80, 14),
                Qt.AlignLeft | Qt.AlignVCenter,
                state,
            )
            p.setBrush(_c(theme.SKY, 150))
            p.setPen(Qt.NoPen)
            p.drawEllipse(QPointF(r.left() + 18, r.bottom() - 24), 2.0, 2.0)

        # viewport / gauge
        if self.width() >= 218 and self.height() >= 150:
            d = min(64.0, inner.height() - 16)
            gauge = QRectF(r.right() - d - 28, inner.center().y() - d / 2.0, d, d)
            p.setBrush(QColor(5, 14, 25))
            p.setPen(QPen(_c(theme.SKY, 65), 4.0))
            p.drawEllipse(gauge)
            p.setPen(QPen(_c(theme.SKY, 110), 1.0))
            p.drawEllipse(gauge.adjusted(9, 9, -9, -9))
            p.setBrush(_c(theme.SKY, 12))
            p.drawEllipse(gauge.adjusted(5, 5, -5, -5))

            p.setPen(QPen(_c(theme.SKY, 110), 1.0))
            for i in range(9):
                angle = math.radians(-220 + i * 27.5)
                outer = gauge.adjusted(9, 9, -9, -9)
                cx, cy = outer.center().x(), outer.center().y()
                radius = outer.width() / 2.0
                inner_r = radius - (4 if i % 2 == 0 else 2)
                p.drawLine(
                    QPointF(cx + math.cos(angle) * radius, cy + math.sin(angle) * radius),
                    QPointF(cx + math.cos(angle) * inner_r, cy + math.sin(angle) * inner_r),
                )
            p.setBrush(_c(theme.SKY, 160))
            p.setPen(Qt.NoPen)
            p.drawEllipse(gauge.center(), 2.5, 2.5)

    @staticmethod
    def _format_pressure(value):
        try:
            value = float(value)
        except (TypeError, ValueError):
            return "—"
        if value <= 0:
            return "—"
        if value < 0.01:
            text = f"{value:.1e}"
            mantissa, exponent = text.split("e")
            return f"{mantissa}e{int(exponent)}"
        if value < 10:
            return f"{value:.3f}"
        return f"{value:.1f}"


TYPE_CLASSES = {
    "chamber": ChamberWidget,
    "turbo": MolecularPumpWidget,
    "dry": DryPumpWidget,
    "angle": AngleValveWidget,
    "gate": GateValveWidget,
}
