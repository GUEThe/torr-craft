"""The schematic canvas: component placement, resizing, piping and selection."""

from PySide2.QtCore import QPoint, QPointF, QRect, QRectF, Qt, Signal
from PySide2.QtGui import (
    QColor,
    QFont,
    QFontMetrics,
    QLinearGradient,
    QPainter,
    QPen,
)
from PySide2.QtWidgets import QAction, QMenu, QWidget

from .. import theme
from ..device_specs import DEVICE_SPECS
from ..document import (
    CANVAS_HEIGHT,
    CANVAS_WIDTH,
    ComponentData,
    DocumentData,
    PipeData,
)
from ..topology import unisolated_chamber_pair
from ..widgets import COMPONENT_MIME
from .base import BaseDevice
from .devices import TYPE_CLASSES
from .pipe import (
    PipeModel,
    distance_to_path,
    orthogonal_points,
    paint_pipe,
)


class Canvas(QWidget):
    selectionChanged = Signal(object)
    documentChanged = Signal(str)
    geometryEdited = Signal(object)
    countsChanged = Signal(int, int)
    statusMessage = Signal(str)
    connectModeChanged = Signal(bool)
    cursorMoved = Signal(int, int)

    CANVAS_SIZE = (CANVAS_WIDTH, CANVAS_HEIGHT)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("VacuumCanvas")
        self.setFixedSize(*self.CANVAS_SIZE)
        self.setAcceptDrops(True)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setAttribute(Qt.WA_OpaquePaintEvent, True)

        self.devices = {}
        self.pipes = []
        self.project_name = "未命名工程"
        self.connect_mode = False
        self.editing_locked = False
        self.snap_enabled = True

        self._selected = None
        self._connect_source = None
        self._hovered_pipe = None
        self._flow_phase = 0.0
        self._next_numbers = {}

    # ------------------------------------------------------------------ basics
    def sizeHint(self):
        from PySide2.QtCore import QSize

        return QSize(*self.CANVAS_SIZE)

    def selection(self):
        return self._selected

    def set_project_name(self, name):
        self.project_name = name or "未命名工程"

    def mark_changed(self, reason="编辑图纸"):
        self.documentChanged.emit(reason)

    def _status(self, text):
        self.statusMessage.emit(text)

    # --------------------------------------------------------------- rendering
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, False)
        bg = QLinearGradient(0, 0, 0, self.height())
        bg.setColorAt(0.0, QColor("#091321"))
        bg.setColorAt(1.0, QColor("#07101c"))
        p.fillRect(self.rect(), bg)

        self._paint_grid(p)
        p.setRenderHint(QPainter.Antialiasing, True)

        for pipe in self.pipes:
            points = self.pipe_points(pipe)
            if len(points) < 2:
                continue
            paint_pipe(
                p,
                points,
                selected=self._selected is pipe,
                hovered=self._hovered_pipe is pipe,
                active=self._pipe_active(pipe),
                phase=self._flow_phase,
            )

        if not self.devices and not self.pipes:
            self._paint_empty_state(p)

        p.setPen(QColor(theme.DIM))
        p.setFont(theme.font(8, QFont.DemiBold))
        p.drawText(
            QRectF(self.width() - 150, self.height() - 23, 132, 14),
            Qt.AlignRight | Qt.AlignVCenter,
            f"CANVAS · {self.width()} × {self.height()}",
        )

    def _paint_grid(self, p):
        w = self.width()
        h = self.height()
        minor = QPen(QColor(22, 38, 58, 120), 1.0)
        p.setPen(minor)
        for x in range(20, w, 20):
            if x % 100 != 0:
                p.drawLine(x, 0, x, h)
        for y in range(20, h, 20):
            if y % 100 != 0:
                p.drawLine(0, y, w, y)

        major = QPen(QColor(32, 55, 82, 155), 1.0)
        p.setPen(major)
        for x in range(100, w, 100):
            p.drawLine(x, 0, x, h)
        for y in range(100, h, 100):
            p.drawLine(0, y, w, y)

        p.setPen(Qt.NoPen)
        p.setBrush(QColor(70, 110, 150, 90))
        for x in range(100, w, 100):
            for y in range(100, h, 100):
                p.drawEllipse(QPointF(x, y), 1.1, 1.1)

        p.setPen(QPen(QColor(44, 70, 100, 170), 1.0))
        p.setBrush(Qt.NoBrush)
        p.drawRect(QRectF(0.5, 0.5, w - 1, h - 1))

    def _paint_empty_state(self, p):
        card_w = 456
        card_h = 190
        x = min(self.width() / 2.0 - card_w / 2.0, 430.0)
        y = 238.0
        card = QRectF(x, y, card_w, card_h)
        p.setBrush(QColor(10, 20, 34, 165))
        pen = QPen(QColor(58, 86, 115, 170), 1.2)
        pen.setStyle(Qt.DashLine)
        p.setPen(pen)
        p.drawRoundedRect(card, 16, 16)

        icon_ring = QRectF(card.center().x() - 25, y + 28, 50, 50)
        p.setBrush(QColor(34, 211, 238, 18))
        p.setPen(QPen(QColor(34, 211, 238, 85), 1.0))
        p.drawEllipse(icon_ring)
        p.setPen(QPen(QColor(theme.CYAN), 2.0))
        p.drawLine(QPointF(card.center().x() - 9, y + 53), QPointF(card.center().x() + 9, y + 53))
        p.drawLine(QPointF(card.center().x(), y + 44), QPointF(card.center().x(), y + 62))

        p.setPen(QColor(theme.TEXT))
        p.setFont(theme.font(15, QFont.DemiBold))
        p.drawText(
            QRectF(x + 20, y + 88, card_w - 40, 24),
            Qt.AlignCenter,
            "从左侧组件库开始搭建",
        )
        p.setPen(QColor(theme.MUTED))
        p.setFont(theme.font(10))
        p.drawText(
            QRectF(x + 30, y + 114, card_w - 60, 20),
            Qt.AlignCenter,
            "拖入腔室、泵与阀门，再用管道建立真空回路",
        )

        chips = ("拖拽元件", "连接管道", "导入 .ui")
        chip_font = theme.font(8, QFont.DemiBold)
        p.setFont(chip_font)
        widths = [QFontMetrics(chip_font).horizontalAdvance(t) + 22 for t in chips]
        total = sum(widths) + 14 * (len(chips) - 1)
        cx = card.center().x() - total / 2.0
        for text, cw in zip(chips, widths):
            chip = QRectF(cx, y + 146, cw, 22)
            p.setPen(QPen(QColor(47, 72, 98), 1.0))
            p.setBrush(QColor(20, 35, 54, 170))
            p.drawRoundedRect(chip, 11, 11)
            p.setPen(QColor(theme.DIM))
            p.drawText(chip, Qt.AlignCenter, text)
            cx += cw + 14

    # ------------------------------------------------------------------- pipes
    def pipe_points(self, pipe):
        a = self.devices.get(pipe.source_id)
        b = self.devices.get(pipe.target_id)
        if a is None or b is None:
            return []
        return orthogonal_points(a.geometry(), b.geometry())

    def pipe_text(self, pipe):
        a = self.devices.get(pipe.source_id)
        b = self.devices.get(pipe.target_id)
        if a is None or b is None:
            return "已断开"
        return f"{a.label}  ↔  {b.label}"

    def _pipe_active(self, pipe):
        a = self.devices.get(pipe.source_id)
        b = self.devices.get(pipe.target_id)
        if a is None or b is None:
            return False
        return self._endpoint_flowing(a) and self._endpoint_flowing(b)

    @staticmethod
    def _endpoint_flowing(device):
        if device.spec.has_online and not device.online:
            return False
        if device.spec.has_speed and not device.switched_on:
            return False
        if device.spec.key in ("angle", "gate") and not device.switched_on:
            return False
        return True

    def _hit_pipe(self, pos):
        best = None
        best_distance = 8.0
        for pipe in reversed(self.pipes):
            points = self.pipe_points(pipe)
            if len(points) < 2:
                continue
            distance = distance_to_path(QPointF(pos), points)
            if distance <= best_distance:
                best = pipe
                best_distance = distance
        return best

    def _active_pipe_exists(self):
        return any(self._pipe_active(pipe) for pipe in self.pipes)

    # -------------------------------------------------------------- components
    def _unique_id(self, prefix):
        index = 1
        while True:
            candidate = f"{prefix}_{index}"
            if candidate not in self.devices and all(p.pipe_id != candidate for p in self.pipes):
                return candidate
            index += 1

    def _label_for(self, spec):
        number = self._next_numbers.get(spec.key, 0) + 1
        self._next_numbers[spec.key] = number
        if spec.key == "chamber":
            return spec.default_label if number == 1 else f"腔室 {number:02d}"
        base = spec.default_label.rsplit(" ", 1)[0]
        return f"{base} {number:02d}"

    def add_device(
        self,
        device_type,
        x=None,
        y=None,
        select=True,
        object_id=None,
        label=None,
        silent=False,
    ):
        if device_type not in TYPE_CLASSES:
            raise ValueError(f"未知元件类型: {device_type}")
        spec = DEVICE_SPECS[device_type]
        widget = TYPE_CLASSES[device_type](self)
        widget.canvas = self
        widget.device_id = object_id or self._unique_id(device_type)
        if widget.device_id in self.devices:
            widget.device_id = self._unique_id(device_type)
        widget.setObjectName(widget.device_id)
        widget.label = label if label is not None else self._label_for(spec)
        widget.online = True
        widget.switched_on = False
        widget.target_speed = spec.default_speed
        widget.display_speed = 0.0

        w, h = spec.default_size
        if x is None:
            x = 84 + (len(self.devices) % 6) * 28
        if y is None:
            y = 126 + (len(self.devices) % 5) * 26
        x = int(round(x / 10.0) * 10)
        y = int(round(y / 10.0) * 10)
        x = max(0, min(x, self.width() - w))
        y = max(0, min(y, self.height() - h))
        widget.setGeometry(QRect(x, y, w, h))

        widget.clicked.connect(self._on_device_clicked)
        widget.doubleClicked.connect(self._on_device_double_clicked)
        widget.contextRequested.connect(self._show_device_menu)
        widget.geometryEdited.connect(self._on_geometry_edited)
        widget.editCommitted.connect(self._on_edit_committed)

        self.devices[widget.device_id] = widget
        widget.show()
        widget.raise_()
        self._emit_counts()
        if select:
            self.select(widget)
        if not silent:
            self._status(f"已添加 {widget.label} · 拖动移动，选中后拖拽边角缩放")
        self.update()
        return widget

    def visible_canvas_center(self):
        parent = self.parentWidget()
        if parent is not None:
            center = parent.rect().center()
            return self.mapFromGlobal(parent.mapToGlobal(center))
        return QPoint(self.width() // 2, self.height() // 2)

    def add_device_at_center(self, device_type):
        spec = DEVICE_SPECS[device_type]
        center = self.visible_canvas_center()
        w, h = spec.default_size
        x = center.x() - w // 2
        y = center.y() - h // 2
        x, y = self._find_free_position(x, y, w, h)
        return self.add_device(device_type, x=x, y=y, select=True)

    def _find_free_position(self, x, y, w, h):
        x = max(10, min(x, self.width() - w - 10))
        y = max(10, min(y, self.height() - h - 10))
        for _ in range(9):
            candidate = QRect(x, y, w, h)
            if not any(candidate.intersects(dev.geometry()) for dev in self.devices.values()):
                return x, y
            x = min(x + 32, self.width() - w - 10)
            y = min(y + 32, self.height() - h - 10)
        return x, y

    def _on_device_clicked(self, device, modifiers):
        if self.connect_mode:
            return
        self.select(device)

    def _on_device_double_clicked(self, device):
        if not device.spec.has_switch:
            return
        if self.editing_locked:
            self._status("画布已锁定，解锁后可切换设备状态")
            return
        device.set_switched_on(not device.switched_on)
        state = device.spec.switch_on_text if device.switched_on else device.spec.switch_off_text
        self._status(f"{device.label} · {state}")
        self.documentChanged.emit("切换设备状态")
        self.update()

    def _on_geometry_edited(self, device):
        self.geometryEdited.emit(device)
        self.update()

    def _on_edit_committed(self, device, reason):
        self.documentChanged.emit(reason)
        self._status(f"{device.label} · {device.width()} × {device.height()} px")

    def _emit_counts(self):
        self.countsChanged.emit(len(self.devices), len(self.pipes))

    # -------------------------------------------------------------- connection
    def set_connect_mode(self, enabled):
        enabled = bool(enabled) and not self.editing_locked
        if enabled == self.connect_mode:
            return
        self.connect_mode = enabled
        self._cancel_connect_source()
        self.setCursor(Qt.CrossCursor if enabled else Qt.ArrowCursor)
        if enabled:
            self.clear_selection()
            self._status("管道模式 · 依次点击两个端点；腔室之间必须经插板阀隔离")
        else:
            self._status("已退出管道模式")
        for device in self.devices.values():
            device.setCursor(Qt.CrossCursor if enabled else Qt.OpenHandCursor)
            device.update()
        self.connectModeChanged.emit(enabled)

    def handle_device_clicked(self, device):
        if not self.connect_mode:
            return
        if self._connect_source is None:
            self._connect_source = device
            device.set_connect_source(True)
            self._status(f"起点：{device.label} · 请选择第二个端点")
            return
        if self._connect_source is device:
            self._cancel_connect_source()
            self._status("已取消起点，请重新选择")
            return
        source = self._connect_source
        pipe = self.create_pipe(source, device)
        if pipe is not None:
            self._connect_source = None
            source.set_connect_source(False)
            device.set_connect_source(False)
            self.select(pipe)
            self._status(f"已连接 · {self.pipe_text(pipe)}；继续选择端点或按 Esc 退出")
        self.update()

    def _cancel_connect_source(self):
        if self._connect_source is not None:
            self._connect_source.set_connect_source(False)
            self._connect_source = None

    def validate_connection(self, source, target):
        if source is None or target is None:
            return False, "连接端点不存在"
        if source is target or source.device_id == target.device_id:
            return False, "不能把元件连接到自身"
        if source.device_type == "chamber" and target.device_type == "chamber":
            return False, "两个腔室之间必须经插板阀隔离，不能直接用管道连接"
        for pipe in self.pipes:
            if {pipe.source_id, pipe.target_id} == {source.device_id, target.device_id}:
                return False, "这两个元件之间已经存在管道"

        # Every path between two chambers must cross a gate valve.  Check the
        # candidate graph after removing gate-valve nodes, so indirect bypasses
        # (e.g. chamber → angle valve → chamber) are rejected too.
        types = {device.device_id: device.device_type for device in self.devices.values()}
        edges = [(pipe.source_id, pipe.target_id) for pipe in self.pipes]
        edges.append((source.device_id, target.device_id))
        pair = unisolated_chamber_pair(types, edges)
        if pair is not None:
            first = self.devices.get(pair[0])
            second = self.devices.get(pair[1])
            names = " ↔ ".join(
                device.label if device else object_id
                for device, object_id in ((first, pair[0]), (second, pair[1]))
            )
            return False, f"两个腔室之间必须经插板阀隔离（{names}）"
        return True, ""

    def create_pipe(self, source, target, pipe_id=None, bypass_validation=False, mark=True):
        if not bypass_validation:
            ok, message = self.validate_connection(source, target)
            if not ok:
                self._status("连接被拒绝 · " + message)
                return None
        model = PipeModel(
            pipe_id=pipe_id or self._unique_id("pipe"),
            source_id=source.device_id,
            target_id=target.device_id,
        )
        if any(p.pipe_id == model.pipe_id for p in self.pipes):
            model.pipe_id = self._unique_id("pipe")
        self.pipes.append(model)
        self._emit_counts()
        self.update()
        if mark:
            self.documentChanged.emit("连接管道")
        return model

    def connect_devices(self, source_id, target_id):
        source = self.devices.get(source_id)
        target = self.devices.get(target_id)
        if source is None or target is None:
            return None
        return self.create_pipe(source, target)

    # ---------------------------------------------------------------- selection
    def select(self, obj):
        if obj is not None and not isinstance(obj, PipeModel) and obj not in self.devices.values():
            obj = None
        if obj is self._selected:
            self.selectionChanged.emit(obj)
            return
        if isinstance(self._selected, BaseDevice):
            self._selected.set_selected(False)
        self._selected = obj
        if isinstance(obj, BaseDevice):
            obj.set_selected(True)
            obj.raise_()
            self._status(f"已选择 {obj.label} · 双击切换状态，边角控制点可缩放")
        elif isinstance(obj, PipeModel):
            self._status(f"已选择管道 · {self.pipe_text(obj)}")
        self.update()
        self.selectionChanged.emit(obj)
        self.setFocus()

    def clear_selection(self):
        if self._selected is None:
            return
        if isinstance(self._selected, BaseDevice):
            self._selected.set_selected(False)
        self._selected = None
        self.update()
        self.selectionChanged.emit(None)

    # -------------------------------------------------------------- deletion
    def delete_selected(self):
        if self.editing_locked:
            self._status("画布已锁定，解锁后可删除对象")
            return
        if self._selected is None:
            self._status("没有选中的对象")
            return
        if isinstance(self._selected, BaseDevice):
            self._delete_device(self._selected)
        elif isinstance(self._selected, PipeModel):
            self._delete_pipe(self._selected)

    def _delete_device(self, device):
        if self.editing_locked:
            self._status("画布已锁定，解锁后可删除对象")
            return
        if device not in self.devices.values():
            return
        for pipe in list(self.pipes):
            if device.device_id in (pipe.source_id, pipe.target_id):
                self.pipes.remove(pipe)
        self.devices.pop(device.device_id, None)
        if self._connect_source is device:
            self._connect_source = None
        if self._selected is device:
            self._selected = None
            self.selectionChanged.emit(None)
        device.hide()
        device.deleteLater()
        self._emit_counts()
        self.update()
        self.documentChanged.emit("删除元件")
        self._status(f"已删除 {device.label}")

    def _delete_pipe(self, pipe):
        if pipe in self.pipes:
            self.pipes.remove(pipe)
            if self._selected is pipe:
                self._selected = None
                self.selectionChanged.emit(None)
            if self._hovered_pipe is pipe:
                self._hovered_pipe = None
            self._emit_counts()
            self.update()
            self.documentChanged.emit("删除管道")
            self._status("已删除管道")

    def duplicate_selected(self):
        if self.editing_locked:
            self._status("画布已锁定，解锁后可复制元件")
            return
        if not isinstance(self._selected, BaseDevice):
            return
        source = self._selected
        clone = self.add_device(
            source.device_type,
            x=source.x() + 30,
            y=source.y() + 30,
            select=True,
            label=source.label + " 副本",
            silent=True,
        )
        clone.online = source.online
        clone.switched_on = source.switched_on
        clone.target_speed = source.target_speed
        clone.pressure = source.pressure
        if hasattr(clone, "seed_display_speed"):
            clone.seed_display_speed()
        if hasattr(clone, "seed_open_phase"):
            clone.seed_open_phase()
        clone.update()
        self.documentChanged.emit("复制元件")
        self._status(f"已复制 {source.label}")

    def clear_document(self, emit=False):
        for device in list(self.devices.values()):
            device.hide()
            device.deleteLater()
        self.devices.clear()
        self.pipes.clear()
        self._selected = None
        self._connect_source = None
        self._hovered_pipe = None
        self._next_numbers.clear()
        self.selectionChanged.emit(None)
        self._emit_counts()
        self.update()
        if emit:
            self.documentChanged.emit("清空图纸")

    # -------------------------------------------------------------- document io
    def snapshot(self):
        components = []
        for device in self.devices.values():
            components.append(
                ComponentData(
                    device_type=device.device_type,
                    object_id=device.device_id,
                    x=device.x(),
                    y=device.y(),
                    width=device.width(),
                    height=device.height(),
                    label=device.label,
                    online=bool(device.online),
                    switched_on=bool(device.switched_on),
                    speed=int(device.target_speed),
                    pressure=float(device.pressure),
                )
            )
        pipes = [
            PipeData(pipe_id=p.pipe_id, source_id=p.source_id, target_id=p.target_id)
            for p in self.pipes
        ]
        return DocumentData(project_name=self.project_name, components=components, pipes=pipes)

    def apply_document(self, document):
        self.clear_document(emit=False)
        self.set_project_name(document.project_name)
        id_map = {}
        for component in document.components:
            if component.device_type not in TYPE_CLASSES:
                continue
            widget = self.add_device(
                component.device_type,
                x=component.x,
                y=component.y,
                select=False,
                object_id=component.object_id,
                label=component.label,
                silent=True,
            )
            id_map[component.object_id] = widget.device_id
            widget.set_geometry_rect(
                QRect(component.x, component.y, component.width, component.height)
            )
            widget.online = bool(component.online)
            widget.switched_on = bool(component.switched_on)
            widget.target_speed = max(0, int(component.speed))
            widget.pressure = float(component.pressure)
            if hasattr(widget, "seed_display_speed"):
                widget.seed_display_speed()
            if hasattr(widget, "seed_open_phase"):
                widget.seed_open_phase()
            widget.update()

        for pipe in document.pipes:
            source = self.devices.get(id_map.get(pipe.source_id, pipe.source_id))
            target = self.devices.get(id_map.get(pipe.target_id, pipe.target_id))
            if source is None or target is None:
                continue
            self.create_pipe(
                source,
                target,
                pipe_id=pipe.pipe_id,
                bypass_validation=True,
                mark=False,
            )
        self._next_numbers.clear()
        for widget in self.devices.values():
            self._next_numbers[widget.device_type] = (
                self._next_numbers.get(widget.device_type, 0) + 1
            )
            suffix = widget.label.rsplit(" ", 1)[-1]
            if suffix.isdigit():
                self._next_numbers[widget.device_type] = max(
                    self._next_numbers[widget.device_type], int(suffix)
                )
        self.select(None)
        self._emit_counts()
        self.update()

    # ------------------------------------------------------------------- events
    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat(COMPONENT_MIME):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat(COMPONENT_MIME):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        if not event.mimeData().hasFormat(COMPONENT_MIME):
            event.ignore()
            return
        device_type = bytes(event.mimeData().data(COMPONENT_MIME)).decode("utf-8")
        if device_type not in DEVICE_SPECS:
            event.ignore()
            return
        spec = DEVICE_SPECS[device_type]
        w, h = spec.default_size
        x = event.pos().x() - w // 2
        y = event.pos().y() - h // 2
        x, y = self._find_free_position(x, y, w, h)
        self.add_device(device_type, x=x, y=y, select=True)
        event.acceptProposedAction()

    def mousePressEvent(self, event):
        self.setFocus()
        if event.button() == Qt.LeftButton:
            pipe = self._hit_pipe(event.pos())
            if pipe is not None:
                self.select(pipe)
            else:
                self.clear_selection()
            event.accept()
            return
        if event.button() == Qt.RightButton:
            pipe = self._hit_pipe(event.pos())
            if pipe is not None:
                self.select(pipe)
                menu = QMenu(self)
                delete_action = QAction("删除管道", menu)
                delete_action.triggered.connect(lambda checked=False, p=pipe: self._delete_pipe(p))
                menu.addAction(delete_action)
                menu.exec_(event.globalPos())
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        self.cursorMoved.emit(event.pos().x(), event.pos().y())
        if self.connect_mode:
            self.setCursor(Qt.CrossCursor)
            return
        pipe = self._hit_pipe(event.pos())
        if pipe is not self._hovered_pipe:
            self._hovered_pipe = pipe
            self.setCursor(Qt.PointingHandCursor if pipe is not None else Qt.ArrowCursor)
            self.update()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Delete, Qt.Key_Backspace):
            self.delete_selected()
            event.accept()
            return
        if event.key() == Qt.Key_Escape:
            if self.connect_mode:
                self.set_connect_mode(False)
            else:
                self.clear_selection()
            event.accept()
            return
        super().keyPressEvent(event)

    def tick(self, dt):
        for device in self.devices.values():
            device.tick(dt)
        if self._active_pipe_exists():
            self._flow_phase = (self._flow_phase + dt * 38.0) % 360.0
            self.update()

    # --------------------------------------------------------------- appearance
    def set_editing_locked(self, locked):
        self.editing_locked = bool(locked)
        if self.editing_locked:
            self.set_connect_mode(False)
            self.clear_selection()
            self.setCursor(Qt.ArrowCursor)
        for device in self.devices.values():
            device.setCursor(Qt.ArrowCursor if self.editing_locked else Qt.OpenHandCursor)
            device.update()

    def set_snap_enabled(self, enabled):
        self.snap_enabled = bool(enabled)

    # ------------------------------------------------------------------ menus
    def _show_device_menu(self, device, global_pos):
        menu = QMenu(self)
        if device.spec.has_switch:
            switch_text = "关闭" if device.switched_on else "开启"
            switch_action = QAction(f"{switch_text} {device.label}", menu)
            switch_action.triggered.connect(
                lambda checked=False, d=device: self._toggle_from_menu(d)
            )
            menu.addAction(switch_action)
        if device.spec.has_online:
            online_text = "标记为离线" if device.online else "标记为在线"
            online_action = QAction(online_text, menu)
            online_action.triggered.connect(
                lambda checked=False, d=device: self._toggle_online_from_menu(d)
            )
            menu.addAction(online_action)
        if device.spec.has_switch or device.spec.has_online:
            menu.addSeparator()
        duplicate = QAction("复制元件", menu)
        duplicate.triggered.connect(lambda checked=False: self.duplicate_selected())
        menu.addAction(duplicate)
        delete = QAction("删除元件", menu)
        delete.triggered.connect(lambda checked=False, d=device: self._delete_device(d))
        menu.addAction(delete)
        menu.exec_(global_pos)

    def _toggle_from_menu(self, device):
        self.select(device)
        self._on_device_double_clicked(device)

    def _toggle_online_from_menu(self, device):
        device.set_online(not device.online)
        self.select(device)
        self.documentChanged.emit("切换软件连接")
        self._status(f"{device.label} · {'在线' if device.online else '离线'}")
        self.update()
