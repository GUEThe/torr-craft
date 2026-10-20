"""Right-hand property inspector for devices and pipes."""

from PySide2.QtCore import Qt
from PySide2.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from . import theme
from .components.base import BaseDevice
from .components.pipe import PipeModel, normalize_anchor, parse_anchor
from .device_specs import DEVICE_SPECS
from .widgets import ToggleSwitch, TypeGlyph


class InspectorPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Inspector")
        self.setFixedWidth(304)
        self.canvas = None
        self._selected = None
        self._loading = False

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        header = QFrame()
        header.setObjectName("InspectorHeader")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(18, 15, 18, 13)
        header_layout.setSpacing(2)
        kicker = QLabel("INSPECTOR")
        kicker.setObjectName("SectionKicker")
        title = QLabel("属性检查器")
        title.setObjectName("SectionTitle")
        header_layout.addWidget(kicker)
        header_layout.addWidget(title)
        root.addWidget(header)

        self._stack = QStackedWidget()
        self._stack.setObjectName("InspectorPage")
        root.addWidget(self._stack, 1)

        self._empty_page = self._build_empty_page()
        self._device_page, self._device_scroll = self._build_device_page()
        self._pipe_page = self._build_pipe_page()
        self._stack.addWidget(self._empty_page)
        self._stack.addWidget(self._device_scroll)
        self._stack.addWidget(self._pipe_page)
        self._stack.setCurrentWidget(self._empty_page)

        footer = QFrame()
        footer.setObjectName("InspectorFooter")
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(18, 9, 18, 9)
        footer_layout.setSpacing(7)
        dot = QLabel("●")
        dot.setStyleSheet(f"color: {theme.VIOLET}; font-size: 8px;")
        hint = QLabel("插板阀通过两侧内联法兰隔离腔室")
        hint.setObjectName("Tiny")
        footer_layout.addWidget(dot)
        footer_layout.addWidget(hint, 1)
        root.addWidget(footer)

    # ------------------------------------------------------------------ setup
    def set_canvas(self, canvas):
        self.canvas = canvas
        canvas.selectionChanged.connect(self.show_selection)
        canvas.geometryEdited.connect(self.sync_geometry)
        canvas.countsChanged.connect(self._on_counts_changed)
        canvas.pipeRouteChanged.connect(self._on_pipe_route_changed)

    def _build_empty_page(self):
        page = QWidget()
        page.setObjectName("InspectorPage")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 22, 20, 18)
        layout.setSpacing(12)
        layout.setAlignment(Qt.AlignTop)

        glyph = TypeGlyph("chamber", theme.CYAN, size=54)
        glyph_row = QHBoxLayout()
        glyph_row.addWidget(glyph)
        glyph_row.addStretch(1)
        layout.addLayout(glyph_row)

        title = QLabel("未选择任何对象")
        title.setStyleSheet(f"color: {theme.TEXT}; font-size: 16px; font-weight: 700;")
        layout.addWidget(title)

        text = QLabel(
            "从画布中选择一个元件或管道，这里会显示它的运行状态、尺寸与连接属性。"
        )
        text.setObjectName("Muted")
        text.setWordWrap(True)
        text.setStyleSheet(f"color: {theme.MUTED}; font-size: 11px; line-height: 1.5;")
        layout.addWidget(text)

        layout.addSpacing(8)
        card = QFrame()
        card.setObjectName("InsetCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(14, 13, 14, 13)
        card_layout.setSpacing(8)
        card_title = QLabel("组态提示")
        card_title.setObjectName("SectionTitle")
        card_layout.addWidget(card_title)
        for line in (
            "拖拽左侧元件到画布，或单击快速添加",
            "选中元件后拖动边角控制点调整尺寸",
            "双击泵或阀门可切换运行 / 开关状态",
            "插板阀在检查器中绑定两侧腔室法兰",
        ):
            label = QLabel("·  " + line)
            label.setObjectName("Hint")
            label.setWordWrap(True)
            card_layout.addWidget(label)
        layout.addWidget(card)
        layout.addStretch(1)
        return page

    def _section(self, title, kicker=None):
        wrapper = QWidget()
        wrapper.setObjectName("InspectorPage")
        layout = QVBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(7)
        if kicker:
            kicker_label = QLabel(kicker)
            kicker_label.setObjectName("SectionKicker")
            layout.addWidget(kicker_label)
        title_label = QLabel(title)
        title_label.setObjectName("SectionTitle")
        layout.addWidget(title_label)
        return wrapper, layout

    def _build_device_page(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        content = QWidget()
        content.setObjectName("InspectorPage")
        scroll.setWidget(content)
        layout = QVBoxLayout(content)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(13)

        identity_row = QHBoxLayout()
        identity_row.setSpacing(11)
        self._device_glyph = TypeGlyph("chamber", theme.SKY, size=46)
        identity_row.addWidget(self._device_glyph)
        identity_labels = QVBoxLayout()
        identity_labels.setSpacing(1)
        self._device_kind = QLabel("腔室")
        self._device_kind.setStyleSheet(f"color: {theme.TEXT}; font-size: 14px; font-weight: 700;")
        self._device_id = QLabel("chamber_1")
        self._device_id.setObjectName("Tiny")
        identity_labels.addWidget(self._device_kind)
        identity_labels.addWidget(self._device_id)
        identity_row.addLayout(identity_labels, 1)
        layout.addLayout(identity_row)

        name_section, name_layout = self._section("身份")
        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("元件名称")
        self._name_edit.editingFinished.connect(self._apply_name)
        name_layout.addWidget(self._name_edit)
        layout.addWidget(name_section)

        self._state_section, state_layout = self._section("运行状态", "TELEMETRY")
        state_card = QFrame()
        state_card.setObjectName("InsetCard")
        card_layout = QVBoxLayout(state_card)
        card_layout.setContentsMargins(12, 6, 12, 6)
        card_layout.setSpacing(0)

        self._online_row, self._online_switch = self._switch_row("软件连接")
        self._online_switch.toggled.connect(self._apply_online)
        card_layout.addWidget(self._online_row)

        self._power_row, self._power_switch = self._switch_row("运行状态")
        self._power_label = self._power_row.findChildren(QLabel)[-1]
        self._power_switch.toggled.connect(self._apply_switch)
        card_layout.addWidget(self._power_row)
        state_layout.addWidget(state_card)
        layout.addWidget(self._state_section)

        self._flange_section, flange_layout = self._section("内联法兰", "INLINE MOUNT")
        flange_card = QFrame()
        flange_card.setObjectName("InsetCard")
        flange_card_layout = QVBoxLayout(flange_card)
        flange_card_layout.setContentsMargins(12, 10, 12, 10)
        flange_card_layout.setSpacing(7)

        flange_help = QLabel("插板阀直接夹装在两个腔室之间，无需管道。")
        flange_help.setObjectName("Hint")
        flange_help.setWordWrap(True)
        flange_card_layout.addWidget(flange_help)

        self._flange_a_combo = self._flange_combo()
        self._flange_b_combo = self._flange_combo()
        for side, combo in (("A", self._flange_a_combo), ("B", self._flange_b_combo)):
            row = QHBoxLayout()
            row.setSpacing(8)
            side_label = QLabel(f"{side} 侧")
            side_label.setObjectName("FieldLabel")
            side_label.setFixedWidth(30)
            row.addWidget(side_label)
            row.addWidget(combo, 1)
            flange_card_layout.addLayout(row)
        self._flange_a_combo.currentIndexChanged.connect(
            lambda index: self._apply_flange("a")
        )
        self._flange_b_combo.currentIndexChanged.connect(
            lambda index: self._apply_flange("b")
        )

        self._flange_hint = QLabel("为两侧法兰选择腔室")
        self._flange_hint.setObjectName("Tiny")
        self._flange_hint.setWordWrap(True)
        flange_card_layout.addWidget(self._flange_hint)

        self._auto_mount_btn = QPushButton("自动贴装相邻腔室")
        self._auto_mount_btn.setObjectName("AutoMountButton")
        self._auto_mount_btn.clicked.connect(self._auto_mount_gate)
        flange_card_layout.addWidget(self._auto_mount_btn)
        flange_layout.addWidget(flange_card)
        layout.addWidget(self._flange_section)

        self._speed_section, speed_layout = self._section("转速", "ROTATION")
        speed_card = QFrame()
        speed_card.setObjectName("InsetCard")
        speed_card_layout = QVBoxLayout(speed_card)
        speed_card_layout.setContentsMargins(13, 9, 13, 9)
        speed_card_layout.setSpacing(6)
        current_row = QHBoxLayout()
        current_label = QLabel("当前")
        current_label.setObjectName("FieldLabel")
        self._current_speed = QLabel("0")
        self._current_speed.setStyleSheet(
            f"color: {theme.TEXT}; font-family: 'Consolas'; font-size: 23px; font-weight: 700;"
        )
        self._current_unit = QLabel("RPM")
        self._current_unit.setObjectName("Tiny")
        current_row.addWidget(current_label)
        current_row.addStretch(1)
        current_row.addWidget(self._current_speed, 0, Qt.AlignBottom)
        current_row.addWidget(self._current_unit, 0, Qt.AlignBottom)
        speed_card_layout.addLayout(current_row)

        target_row = QHBoxLayout()
        target_label = QLabel("目标转速")
        target_label.setObjectName("FieldLabel")
        self._speed_spin = QSpinBox()
        self._speed_spin.setRange(0, 90000)
        self._speed_spin.setSingleStep(100)
        self._speed_spin.setSuffix(" RPM")
        self._speed_spin.setKeyboardTracking(False)
        self._speed_spin.valueChanged.connect(self._apply_speed)
        target_row.addWidget(target_label)
        target_row.addStretch(1)
        target_row.addWidget(self._speed_spin, 1)
        speed_card_layout.addLayout(target_row)
        speed_layout.addWidget(speed_card)
        layout.addWidget(self._speed_section)

        self._pressure_section, pressure_layout = self._section("腔室压力", "VACUUM")
        self._pressure_spin = QDoubleSpinBox()
        self._pressure_spin.setRange(0.0, 1.0e6)
        self._pressure_spin.setDecimals(8)
        self._pressure_spin.setSingleStep(0.000001)
        self._pressure_spin.setSuffix(" mbar")
        self._pressure_spin.setKeyboardTracking(False)
        self._pressure_spin.valueChanged.connect(self._apply_pressure)
        pressure_layout.addWidget(self._pressure_spin)
        layout.addWidget(self._pressure_section)

        geometry_section, geometry_layout = self._section("几何与位置", "GEOMETRY")
        grid = QGridLayout()
        grid.setHorizontalSpacing(9)
        grid.setVerticalSpacing(8)
        self._x_spin = self._make_geometry_spin()
        self._y_spin = self._make_geometry_spin()
        self._w_spin = self._make_geometry_spin()
        self._h_spin = self._make_geometry_spin()
        for spin in (self._x_spin, self._y_spin, self._w_spin, self._h_spin):
            spin.valueChanged.connect(self._apply_geometry)
        fields = (
            ("X", self._x_spin),
            ("Y", self._y_spin),
            ("宽", self._w_spin),
            ("高", self._h_spin),
        )
        for index, (label_text, spin) in enumerate(fields):
            label = QLabel(label_text)
            label.setObjectName("FieldLabel")
            row = index // 2
            col = (index % 2) * 2
            grid.addWidget(label, row, col)
            grid.addWidget(spin, row, col + 1)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(3, 1)
        geometry_layout.addLayout(grid)
        layout.addWidget(geometry_section)

        self._links_section, links_layout = self._section("连接", "NETWORK")
        links_card = QFrame()
        links_card.setObjectName("InsetCard")
        links_card_layout = QVBoxLayout(links_card)
        links_card_layout.setContentsMargins(13, 11, 13, 11)
        links_card_layout.setSpacing(5)
        self._links_count = QLabel("0 条管道")
        self._links_count.setObjectName("Tiny")
        self._links_value = QLabel("尚未连接管道")
        self._links_value.setStyleSheet(f"color: {theme.TEXT}; font-size: 11px;")
        self._links_value.setWordWrap(True)
        links_card_layout.addWidget(self._links_count)
        links_card_layout.addWidget(self._links_value)
        links_layout.addWidget(links_card)
        layout.addWidget(self._links_section)

        action_row = QHBoxLayout()
        action_row.setSpacing(8)
        duplicate = QPushButton("复制元件")
        duplicate.setProperty("role", "ghost")
        duplicate.clicked.connect(self._duplicate)
        delete = QPushButton("删除元件")
        delete.setProperty("role", "danger")
        delete.clicked.connect(self._delete_selected)
        action_row.addWidget(duplicate)
        action_row.addWidget(delete, 1)
        layout.addLayout(action_row)
        layout.addStretch(1)
        return content, scroll

    def _build_pipe_page(self):
        page = QWidget()
        page.setObjectName("InspectorPage")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(18, 16, 18, 18)
        layout.setSpacing(17)

        identity_row = QHBoxLayout()
        identity_row.setSpacing(11)
        self._pipe_glyph = TypeGlyph("pipe", theme.CYAN, size=46)
        identity_row.addWidget(self._pipe_glyph)
        labels = QVBoxLayout()
        labels.setSpacing(1)
        self._pipe_kind = QLabel("真空管道")
        self._pipe_kind.setStyleSheet(f"color: {theme.TEXT}; font-size: 14px; font-weight: 700;")
        self._pipe_id = QLabel("pipe_1")
        self._pipe_id.setObjectName("Tiny")
        labels.addWidget(self._pipe_kind)
        labels.addWidget(self._pipe_id)
        identity_row.addLayout(labels, 1)
        layout.addLayout(identity_row)

        section, section_layout = self._section("连接端点", "ROUTING")
        card = QFrame()
        card.setObjectName("InsetCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(13, 11, 13, 11)
        card_layout.setSpacing(6)
        self._pipe_source = QLabel("—")
        self._pipe_source.setStyleSheet(f"color: {theme.TEXT}; font-size: 12px; font-weight: 600;")
        self._pipe_target = QLabel("—")
        self._pipe_target.setStyleSheet(f"color: {theme.TEXT}; font-size: 12px; font-weight: 600;")
        self._pipe_source_anchor_combo = self._anchor_combo()
        self._pipe_target_anchor_combo = self._anchor_combo()
        self._pipe_source_anchor_combo.currentIndexChanged.connect(
            lambda index: self._apply_pipe_anchor("source")
        )
        self._pipe_target_anchor_combo.currentIndexChanged.connect(
            lambda index: self._apply_pipe_anchor("target")
        )
        source_row = QHBoxLayout()
        source_key = QLabel("A")
        source_key.setObjectName("Tiny")
        source_row.addWidget(source_key)
        source_row.addWidget(self._pipe_source, 1)
        source_row.addWidget(self._pipe_source_anchor_combo)
        target_row = QHBoxLayout()
        target_key = QLabel("B")
        target_key.setObjectName("Tiny")
        target_row.addWidget(target_key)
        target_row.addWidget(self._pipe_target, 1)
        target_row.addWidget(self._pipe_target_anchor_combo)
        card_layout.addLayout(source_row)
        card_layout.addLayout(target_row)
        self._pipe_anchor_hint = QLabel("A 自动 · B 自动")
        self._pipe_anchor_hint.setObjectName("Tiny")
        self._pipe_anchor_hint.setWordWrap(True)
        card_layout.addWidget(self._pipe_anchor_hint)
        section_layout.addWidget(card)

        endpoint_hint = QLabel(
            "端点默认自动吸附；可在右侧固定方位，或拖动画布上的琥珀色菱形。"
            "右键 / 双击端点可恢复自动。"
        )
        endpoint_hint.setObjectName("Hint")
        endpoint_hint.setWordWrap(True)
        section_layout.addWidget(endpoint_hint)
        layout.addWidget(section)

        route_section, route_layout = self._section("路由方式", "PIPE ROUTING")
        route_card = QFrame()
        route_card.setObjectName("InsetCard")
        route_card_layout = QVBoxLayout(route_card)
        route_card_layout.setContentsMargins(12, 10, 12, 10)
        route_card_layout.setSpacing(7)

        self._pipe_route_combo = QComboBox()
        self._pipe_route_combo.addItem("自动正交", "auto")
        self._pipe_route_combo.addItem("直线", "straight")
        self._pipe_route_combo.addItem("自定义拐点", "custom")
        self._pipe_route_combo.setMinimumHeight(32)
        self._pipe_route_combo.currentIndexChanged.connect(self._apply_pipe_route)
        route_card_layout.addWidget(self._pipe_route_combo)

        self._pipe_route_hint = QLabel(
            "自动正交布线，移动元件后拐点会自动重排。"
        )
        self._pipe_route_hint.setObjectName("Hint")
        self._pipe_route_hint.setWordWrap(True)
        route_card_layout.addWidget(self._pipe_route_hint)

        bend_row = QHBoxLayout()
        bend_row.setSpacing(8)
        self._pipe_bend_count = QLabel("0 个拐点")
        self._pipe_bend_count.setObjectName("Tiny")
        self._pipe_add_bend_btn = QPushButton("添加拐点")
        self._pipe_add_bend_btn.setToolTip("在最长管段的中点添加一个可拖动拐点")
        self._pipe_add_bend_btn.clicked.connect(self._add_pipe_bend)
        self._pipe_clear_bends_btn = QPushButton("清除")
        self._pipe_clear_bends_btn.setProperty("role", "ghost")
        self._pipe_clear_bends_btn.setToolTip("清除该管道的全部自定义拐点")
        self._pipe_clear_bends_btn.clicked.connect(self._clear_pipe_bends)
        bend_row.addWidget(self._pipe_bend_count)
        bend_row.addStretch(1)
        bend_row.addWidget(self._pipe_clear_bends_btn)
        bend_row.addWidget(self._pipe_add_bend_btn)
        route_card_layout.addLayout(bend_row)
        route_layout.addWidget(route_card)
        layout.addWidget(route_section)

        layout.addSpacing(2)
        delete = QPushButton("删除管道")
        delete.setProperty("role", "danger")
        delete.clicked.connect(self._delete_selected)
        layout.addWidget(delete)
        layout.addStretch(1)
        return page

    def _switch_row(self, label_text):
        row = QWidget()
        row.setObjectName("InspectorPage")
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 5, 0, 5)
        row_layout.setSpacing(8)
        label = QLabel(label_text)
        label.setStyleSheet(f"color: {theme.MUTED}; font-size: 11px;")
        switch = ToggleSwitch(False, accent=theme.GREEN)
        row_layout.addWidget(label)
        row_layout.addStretch(1)
        row_layout.addWidget(switch)
        return row, switch

    def _anchor_combo(self):
        combo = QComboBox()
        combo.setFixedWidth(82)
        combo.setToolTip("端点连接点：自动吸附、固定边中点，或自定义位置")
        combo.addItem("自动", "auto")
        combo.addItem("左侧", "left:0.500")
        combo.addItem("右侧", "right:0.500")
        combo.addItem("顶部", "top:0.500")
        combo.addItem("底部", "bottom:0.500")
        combo.addItem("自定义", "custom")
        return combo

    def _make_geometry_spin(self):
        spin = QSpinBox()
        spin.setRange(0, 1440)
        spin.setSingleStep(10)
        spin.setKeyboardTracking(False)
        return spin

    # ----------------------------------------------------------------- binding
    def show_selection(self, obj):
        self._selected = obj
        if isinstance(obj, BaseDevice):
            self._loading = True
            self._populate_device(obj)
            self._loading = False
            self._stack.setCurrentWidget(self._device_scroll)
            self._device_scroll.verticalScrollBar().setValue(0)
        elif isinstance(obj, PipeModel):
            self._loading = True
            self._populate_pipe(obj)
            self._loading = False
            self._stack.setCurrentWidget(self._pipe_page)
        else:
            self._selected = None
            self._stack.setCurrentWidget(self._empty_page)

    def _populate_device(self, device):
        spec = device.spec
        self._device_glyph.set_type(spec.icon, spec.accent)
        self._device_kind.setText(spec.label)
        self._device_id.setText(device.device_id)
        self._name_edit.setText(device.label)

        has_state = spec.has_online or spec.has_switch
        self._state_section.setVisible(has_state)
        self._online_row.setVisible(spec.has_online)
        self._power_row.setVisible(spec.has_switch)
        self._online_switch.setChecked(device.online)
        self._power_switch.setChecked(device.switched_on)
        self._power_label.setText(
            "阀门状态" if spec.key in ("angle", "gate") else "运行状态"
        )

        is_gate = spec.key == "gate"
        self._flange_section.setVisible(is_gate)
        self._links_section.setVisible(not is_gate)
        if is_gate:
            self._populate_flange_combos(device)

        self._speed_section.setVisible(spec.has_speed)
        self._speed_spin.setRange(0, spec.max_speed)
        self._speed_spin.setValue(int(device.target_speed))
        self._current_unit.setText(spec.speed_unit)

        self._pressure_section.setVisible(spec.has_pressure)
        self._pressure_spin.setValue(float(device.pressure))

        self._x_spin.setRange(0, self.canvas.width() - 10 if self.canvas else 1440)
        self._y_spin.setRange(0, self.canvas.height() - 10 if self.canvas else 900)
        self._w_spin.setRange(spec.min_size[0], self.canvas.width() if self.canvas else 1440)
        self._h_spin.setRange(spec.min_size[1], self.canvas.height() if self.canvas else 900)
        self._write_geometry(device)
        if not is_gate:
            self._update_links(device)
        self.refresh_runtime()

    def _update_links(self, device):
        if self.canvas is None:
            return
        peers = []
        for pipe in self.canvas.pipes:
            if pipe.source_id == device.device_id:
                peer = self.canvas.devices.get(pipe.target_id)
            elif pipe.target_id == device.device_id:
                peer = self.canvas.devices.get(pipe.source_id)
            else:
                continue
            if peer is not None:
                peers.append(peer.label)
        self._links_count.setText(f"{len(peers)} 条管道")
        if peers:
            shown = peers[:4]
            text = "\n".join("↔  " + name for name in shown)
            if len(peers) > len(shown):
                text += f"\n+ {len(peers) - len(shown)} 条"
            self._links_value.setText(text)
        else:
            self._links_value.setText("尚未连接管道")

    def _on_counts_changed(self, devices, pipes):
        if not isinstance(self._selected, BaseDevice):
            return
        if self._selected.device_type == "gate":
            self._populate_flange_combos(self._selected)
        else:
            self._update_links(self._selected)

    def _flange_combo(self):
        combo = QComboBox()
        combo.setMinimumHeight(32)
        return combo

    def _populate_flange_combos(self, gate):
        if self.canvas is None:
            return
        was_loading = self._loading
        self._loading = True
        try:
            chambers = [
                device
                for device in self.canvas.devices.values()
                if device.device_type == "chamber"
            ]
            gate_center = gate.geometry().center()

            def distance(chamber):
                center = chamber.geometry().center()
                return (center.x() - gate_center.x()) ** 2 + (
                    center.y() - gate_center.y()
                ) ** 2

            chambers.sort(key=distance)
            for combo, selected_id in (
                (self._flange_a_combo, gate.flange_a_id),
                (self._flange_b_combo, gate.flange_b_id),
            ):
                combo.blockSignals(True)
                combo.clear()
                combo.addItem("未连接", "")
                for chamber in chambers:
                    combo.addItem(chamber.label, chamber.device_id)
                index = combo.findData(selected_id)
                combo.setCurrentIndex(index if index >= 0 else 0)
                combo.blockSignals(False)

            chamber_a = self.canvas.devices.get(gate.flange_a_id)
            chamber_b = self.canvas.devices.get(gate.flange_b_id)
            if chamber_a is not None and chamber_b is not None:
                text = f"已隔离：{chamber_a.label} ↔ {chamber_b.label}"
                color = theme.GREEN
            elif chamber_a is not None or chamber_b is not None:
                text = "已安装一侧，选择另一侧腔室完成隔离"
                color = theme.AMBER
            elif len(chambers) < 2:
                text = "至少需要两个腔室才能形成内联隔离"
                color = theme.MUTED
            else:
                text = "为两侧法兰选择不同腔室，无需管道"
                color = theme.MUTED
            self._flange_hint.setText(text)
            self._flange_hint.setStyleSheet(f"color: {color}; font-size: 10px;")
            self._auto_mount_btn.setEnabled(
                len(chambers) >= 2 and not self.canvas.editing_locked
            )
        finally:
            self._loading = was_loading

    def _populate_pipe(self, pipe):
        self._pipe_id.setText(pipe.pipe_id)
        if self.canvas is None:
            return
        a = self.canvas.devices.get(pipe.source_id)
        b = self.canvas.devices.get(pipe.target_id)
        self._pipe_source.setText(a.label if a else "—")
        self._pipe_target.setText(b.label if b else "—")
        self._refresh_pipe_anchor_combos(pipe)
        self._refresh_pipe_route(pipe)

    @staticmethod
    def _anchor_display(anchor):
        normalized = normalize_anchor(anchor)
        if normalized == "auto":
            return "自动"
        parsed = parse_anchor(normalized)
        if parsed is None:
            return "自动"
        side, fraction = parsed
        side_label = {
            "left": "左侧",
            "right": "右侧",
            "top": "顶部",
            "bottom": "底部",
        }.get(side, side)
        return f"{side_label} {fraction * 100:.0f}%"

    def _refresh_pipe_anchor_combos(self, pipe):
        was_loading = self._loading
        self._loading = True
        try:
            for combo, anchor in (
                (self._pipe_source_anchor_combo, pipe.source_anchor),
                (self._pipe_target_anchor_combo, pipe.target_anchor),
            ):
                normalized = normalize_anchor(anchor)
                if normalized == "auto":
                    data = "auto"
                else:
                    parsed = parse_anchor(normalized)
                    side, fraction = parsed
                    data = (
                        f"{side}:0.500"
                        if abs(fraction - 0.5) < 0.001
                        else "custom"
                    )
                index = combo.findData(data)
                combo.setCurrentIndex(index if index >= 0 else 0)
            source_text = self._anchor_display(pipe.source_anchor)
            target_text = self._anchor_display(pipe.target_anchor)
            self._pipe_anchor_hint.setText(f"A  {source_text}   ·   B  {target_text}")
            custom = (
                normalize_anchor(pipe.source_anchor) != "auto"
                or normalize_anchor(pipe.target_anchor) != "auto"
            )
            self._pipe_anchor_hint.setStyleSheet(
                f"color: {theme.AMBER if custom else theme.MUTED}; font-size: 10px;"
            )
        finally:
            self._loading = was_loading

    def _apply_pipe_anchor(self, end):
        if (
            self._loading
            or self.canvas is None
            or not isinstance(self._selected, PipeModel)
        ):
            return
        combo = (
            self._pipe_source_anchor_combo
            if end == "source"
            else self._pipe_target_anchor_combo
        )
        data = combo.currentData()
        if data == "custom":
            self.canvas.customize_pipe_endpoint(self._selected, end)
        else:
            self.canvas.set_pipe_endpoint_anchor(self._selected, end, data)
        self._refresh_pipe_anchor_combos(self._selected)

    def _refresh_pipe_route(self, pipe):
        was_loading = self._loading
        self._loading = True
        try:
            index = self._pipe_route_combo.findData(pipe.route_mode)
            self._pipe_route_combo.setCurrentIndex(index if index >= 0 else 0)
            bend_count = len(pipe.bend_points)
            self._pipe_bend_count.setText(f"{bend_count} 个拐点")
            hints = {
                "auto": "自动正交布线，移动元件后拐点会自动重排。",
                "straight": "从两端法兰口拉一条直线，不再生成正交折点。",
                "custom": (
                    "拖动画布上的青色方形控制点调整拐点；双击管段可直接添加，"
                    "右键控制点可删除。"
                ),
            }
            hint = hints.get(pipe.route_mode, hints["auto"])
            if pipe.route_mode != "custom" and bend_count:
                hint += f"\n已保留 {bend_count} 个自定义拐点，切换“自定义拐点”即可恢复。"
            self._pipe_route_hint.setText(hint)
            locked = self.canvas is not None and self.canvas.editing_locked
            self._pipe_add_bend_btn.setEnabled(not locked)
            self._pipe_clear_bends_btn.setEnabled(not locked and bend_count > 0)
        finally:
            self._loading = was_loading

    def _on_pipe_route_changed(self, pipe):
        if isinstance(self._selected, PipeModel) and self._selected is pipe:
            self._refresh_pipe_route(pipe)
            self._refresh_pipe_anchor_combos(pipe)

    def _apply_pipe_route(self, index=None):
        if (
            self._loading
            or self.canvas is None
            or not isinstance(self._selected, PipeModel)
        ):
            return
        mode = self._pipe_route_combo.currentData()
        if self.canvas.set_pipe_route_mode(self._selected, mode):
            self._refresh_pipe_route(self._selected)

    def _add_pipe_bend(self, checked=False):
        if self.canvas is None or not isinstance(self._selected, PipeModel):
            return
        if self.canvas.add_pipe_bend(self._selected):
            self._refresh_pipe_route(self._selected)

    def _clear_pipe_bends(self, checked=False):
        if self.canvas is None or not isinstance(self._selected, PipeModel):
            return
        if self.canvas.clear_pipe_bends(self._selected):
            self._refresh_pipe_route(self._selected)

    def _write_geometry(self, device):
        self._loading = True
        self._x_spin.setValue(device.x())
        self._y_spin.setValue(device.y())
        self._w_spin.setValue(device.width())
        self._h_spin.setValue(device.height())
        self._loading = False

    def sync_geometry(self, device):
        if self._loading or self._selected is not device:
            return
        self._write_geometry(device)

    def refresh_runtime(self):
        device = self._selected
        if not isinstance(device, BaseDevice):
            return
        if device.spec.has_speed:
            if device.online:
                text = f"{int(round(device.display_speed)):,}"
                color = theme.TEXT
            else:
                text = "--"
                color = theme.DIM
            self._current_speed.setText(text)
            self._current_speed.setStyleSheet(
                f"color: {color}; font-family: 'Consolas'; font-size: 23px; font-weight: 700;"
            )
        # External toggles (context menu / double click) must stay in sync.
        if self._online_switch.isChecked() != bool(device.online):
            self._loading = True
            self._online_switch.setChecked(bool(device.online))
            self._loading = False
        if self._power_switch.isChecked() != bool(device.switched_on):
            self._loading = True
            self._power_switch.setChecked(bool(device.switched_on))
            self._loading = False
        if device.spec.has_speed and self._speed_spin.value() != int(device.target_speed):
            self._loading = True
            self._speed_spin.setValue(int(device.target_speed))
            self._loading = False
        if device.spec.has_pressure and abs(self._pressure_spin.value() - float(device.pressure)) > 1e-12:
            self._loading = True
            self._pressure_spin.setValue(float(device.pressure))
            self._loading = False

    # ------------------------------------------------------------------ actions
    def _apply_name(self):
        if self._loading or not isinstance(self._selected, BaseDevice):
            return
        if self.canvas is not None and self.canvas.editing_locked:
            self._name_edit.setText(self._selected.label)
            self.canvas.statusMessage.emit("画布已锁定，解锁后可修改元件名称")
            return
        name = self._name_edit.text().strip()
        if not name:
            self._name_edit.setText(self._selected.label)
            return
        if name != self._selected.label:
            self._selected.set_label(name)
            self.canvas.mark_changed("修改元件名称")
            self.canvas.update()

    def _apply_online(self, checked):
        if self._loading or not isinstance(self._selected, BaseDevice):
            return
        self._selected.set_online(checked)
        self.canvas.mark_changed("修改软件连接")
        self.canvas.update()

    def _apply_switch(self, checked):
        if self._loading or not isinstance(self._selected, BaseDevice):
            return
        self._selected.set_switched_on(checked)
        self.canvas.mark_changed("切换设备状态")
        self.canvas.update()

    def _apply_speed(self, value):
        if self._loading or not isinstance(self._selected, BaseDevice):
            return
        self._selected.set_target_speed(value)
        self.canvas.mark_changed("修改目标转速")
        self.canvas.update()

    def _apply_pressure(self, value):
        if self._loading or not isinstance(self._selected, BaseDevice):
            return
        self._selected.set_pressure(value)
        self.canvas.mark_changed("修改腔室压力")
        self.canvas.update()

    def _apply_flange(self, side):
        if (
            self._loading
            or self.canvas is None
            or not isinstance(self._selected, BaseDevice)
            or self._selected.device_type != "gate"
        ):
            return
        combo = self._flange_a_combo if side == "a" else self._flange_b_combo
        chamber_id = combo.currentData() or ""
        if not self.canvas.set_gate_flange(self._selected, side, chamber_id):
            self._populate_flange_combos(self._selected)
            return
        self._populate_flange_combos(self._selected)

    def _auto_mount_gate(self, checked=False):
        if (
            self._loading
            or self.canvas is None
            or not isinstance(self._selected, BaseDevice)
            or self._selected.device_type != "gate"
        ):
            return
        if self.canvas.auto_mount_gate(self._selected):
            self._populate_flange_combos(self._selected)

    def _apply_geometry(self, value=None):
        if self._loading or not isinstance(self._selected, BaseDevice) or self.canvas is None:
            return
        if self.canvas.editing_locked:
            self._write_geometry(self._selected)
            self.canvas.statusMessage.emit("画布已锁定，解锁后可调整几何")
            return
        device = self._selected
        x = self._x_spin.value()
        y = self._y_spin.value()
        w = self._w_spin.value()
        h = self._h_spin.value()
        from PySide2.QtCore import QRect

        device.set_geometry_rect(QRect(x, y, w, h), notify=True)
        self._write_geometry(device)
        self.canvas.mark_changed("调整元件几何")
        self.canvas.update()

    def _duplicate(self):
        if self.canvas is not None:
            self.canvas.duplicate_selected()

    def _delete_selected(self):
        if self.canvas is not None:
            self.canvas.delete_selected()
