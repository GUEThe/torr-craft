"""Main application window and editor orchestration."""

import re
from pathlib import Path

from PySide2.QtCore import QSize, QTimer, Qt
from PySide2.QtGui import QKeySequence
from PySide2.QtWidgets import (
    QAction,
    QButtonGroup,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QScrollArea,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from . import __version__, icons, theme
from .components.canvas import Canvas
from .demo import load_demo
from .inspector import InspectorPanel
from .palette import ComponentPalette
from .ui_io import UiFormatError, read_ui_file, write_ui_file
from .widgets import BrandMark, Dot


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Torr Craft · 真空系统低代码平台")
        self.setWindowIcon(icons.app_icon())
        self.resize(1520, 940)
        self.setMinimumSize(1180, 760)

        self._current_path = None
        self._dirty = False
        self._loading_document = False
        self._tick_count = 0
        self._status_reset_timer = QTimer(self)
        self._status_reset_timer.setSingleShot(True)
        self._status_reset_timer.timeout.connect(self._reset_status)

        self._build_actions()
        self._build_ui()
        self._wire_canvas()
        self._build_shortcuts()

        self._sim_timer = QTimer(self)
        self._sim_timer.setInterval(50)
        self._sim_timer.timeout.connect(self._on_tick)
        self._sim_timer.start()

        self._load_initial_demo()

    # -------------------------------------------------------------------- ui
    def _build_ui(self):
        root = QWidget()
        root.setObjectName("Root")
        self.setCentralWidget(root)
        outer = QVBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        outer.addWidget(self._build_top_bar())

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)

        self.palette = ComponentPalette()
        body.addWidget(self.palette)

        center = QWidget()
        center_layout = QVBoxLayout(center)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(0)
        self.canvas = Canvas()
        center_layout.addWidget(self._build_canvas_toolbar())
        self.canvas_scroll = QScrollArea()
        self.canvas_scroll.setWidget(self.canvas)
        self.canvas_scroll.setWidgetResizable(False)
        self.canvas_scroll.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.canvas_scroll.setFrameShape(QFrame.NoFrame)
        self.canvas_scroll.setStyleSheet(
            "QScrollArea { background: #07101c; border: none; }"
            "QScrollArea > QWidget > QWidget { background: #07101c; }"
        )
        center_layout.addWidget(self.canvas_scroll, 1)
        body.addWidget(center, 1)

        self.inspector = InspectorPanel()
        self.inspector.set_canvas(self.canvas)
        body.addWidget(self.inspector)

        outer.addLayout(body, 1)
        outer.addWidget(self._build_status_bar())

    def _build_top_bar(self):
        bar = QFrame()
        bar.setObjectName("TopBar")
        bar.setFixedHeight(68)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(18, 0, 16, 0)
        layout.setSpacing(12)

        logo = BrandMark(size=40)
        layout.addWidget(logo)

        brand_col = QVBoxLayout()
        brand_col.setSpacing(0)
        brand = QLabel("TORR CRAFT")
        brand.setObjectName("Brand")
        sub = QLabel("VACUUM SYSTEM STUDIO")
        sub.setObjectName("BrandSub")
        brand_col.addWidget(brand)
        brand_col.addWidget(sub)
        layout.addLayout(brand_col)

        layout.addSpacing(8)
        layout.addWidget(self._vline(34))
        layout.addSpacing(6)

        self._dirty_dot = Dot(theme.AMBER, size=7)
        self._dirty_dot.setVisible(False)
        layout.addWidget(self._dirty_dot)

        project_col = QVBoxLayout()
        project_col.setSpacing(1)
        self._project_name = QLabel("双腔真空系统")
        self._project_name.setObjectName("ProjectName")
        self._project_meta = QLabel("示例工程 · 未保存")
        self._project_meta.setObjectName("ProjectMeta")
        project_col.addWidget(self._project_name)
        project_col.addWidget(self._project_meta)
        layout.addLayout(project_col)

        layout.addStretch(1)

        self._sim_pill = QToolButton()
        self._sim_pill.setObjectName("SimPill")
        self._sim_pill.setCheckable(True)
        self._sim_pill.setChecked(True)
        self._sim_pill.setText("●  模拟遥测")
        self._sim_pill.setCursor(Qt.PointingHandCursor)
        self._sim_pill.setToolTip("启用/暂停本地设备遥测模拟")
        self._sim_pill.toggled.connect(self._toggle_simulation)
        layout.addWidget(self._sim_pill)

        layout.addSpacing(2)

        import_btn = QToolButton()
        import_btn.setObjectName("HeaderAction")
        import_btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        import_btn.setIcon(icons.make_icon("import", theme.MUTED, 17))
        import_btn.setIconSize(QSize(17, 17))
        import_btn.setText("导入 .ui")
        import_btn.setToolTip("导入 Qt UI 图纸 (Ctrl+O)")
        import_btn.clicked.connect(self.open_document)
        layout.addWidget(import_btn)

        export_btn = QToolButton()
        export_btn.setProperty("role", "primary")
        export_btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        export_btn.setIcon(icons.make_icon("export", "#041420", 17))
        export_btn.setText("导出 .ui")
        export_btn.setToolTip("导出 Qt UI 图纸 (Ctrl+S)")
        export_btn.clicked.connect(self.export_document)
        layout.addWidget(export_btn)

        more = QToolButton()
        more.setObjectName("HeaderAction")
        more.setIcon(icons.make_icon("more", theme.MUTED, 18))
        more.setPopupMode(QToolButton.InstantPopup)
        more.setToolTip("更多操作")
        menu = QMenuBuilder(self)
        menu.addAction(self._new_action)
        menu.addAction(self._demo_action)
        menu.addAction(self._rename_action)
        menu.addSeparator()
        menu.addAction(self._save_as_action)
        menu.addSeparator()
        menu.addAction(self._about_action)
        more.setMenu(menu.menu)
        self._more_menu = menu.menu
        layout.addWidget(more)

        return bar

    def _build_canvas_toolbar(self):
        bar = QFrame()
        bar.setObjectName("CanvasToolbar")
        bar.setFixedHeight(50)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(14, 0, 14, 0)
        layout.setSpacing(4)

        self._select_btn = QToolButton()
        self._select_btn.setIcon(icons.make_icon("cursor", theme.CYAN, 17))
        self._select_btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self._select_btn.setText("选择")
        self._select_btn.setCheckable(True)
        self._select_btn.setChecked(True)
        self._select_btn.setToolTip("选择 / 移动 / 缩放元件")

        self._pipe_btn = QToolButton()
        self._pipe_btn.setIcon(icons.make_icon("pipe", theme.MUTED, 17))
        self._pipe_btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self._pipe_btn.setText("管道")
        self._pipe_btn.setCheckable(True)
        self._pipe_btn.setToolTip("依次点击两个端点建立管道")

        group = QButtonGroup(self)
        group.setExclusive(True)
        group.addButton(self._select_btn)
        group.addButton(self._pipe_btn)
        self._select_btn.clicked.connect(lambda checked=False: self.canvas.set_connect_mode(False))
        self._pipe_btn.toggled.connect(self._pipe_toggled)
        layout.addWidget(self._select_btn)
        layout.addWidget(self._pipe_btn)

        layout.addWidget(self._vline(22))
        layout.addSpacing(4)

        self._delete_btn = QToolButton()
        self._delete_btn.setIcon(icons.make_icon("delete", theme.MUTED, 17))
        self._delete_btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self._delete_btn.setText("删除")
        self._delete_btn.setToolTip("删除选中对象")
        self._delete_btn.setEnabled(False)
        self._delete_btn.clicked.connect(lambda checked=False: self.canvas.delete_selected())
        layout.addWidget(self._delete_btn)

        layout.addStretch(1)

        hint = QLabel("拖拽移动  ·  边角缩放  ·  双击切换状态")
        hint.setObjectName("Tiny")
        layout.addWidget(hint)
        layout.addSpacing(4)
        layout.addWidget(self._vline(22))

        self._lock_btn = QToolButton()
        self._lock_btn.setDefaultAction(self._lock_action)
        self._lock_btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        layout.addWidget(self._lock_btn)

        self._grid_btn = QToolButton()
        self._grid_btn.setDefaultAction(self._grid_action)
        self._grid_btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        layout.addWidget(self._grid_btn)

        return bar

    def _build_status_bar(self):
        bar = QFrame()
        bar.setObjectName("StatusBar")
        bar.setFixedHeight(30)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(14, 0, 14, 0)
        layout.setSpacing(8)

        self._status_dot = Dot(theme.GREEN, size=7)
        self._status_label = QLabel("就绪 · 拖拽元件到画布开始组态")
        self._status_label.setObjectName("Tiny")
        layout.addWidget(self._status_dot)
        layout.addWidget(self._status_label)

        layout.addStretch(1)
        self._coords = QLabel("X 0   Y 0")
        self._coords.setObjectName("Tiny")
        layout.addWidget(self._coords)
        layout.addWidget(self._vline(14))
        self._counts = QLabel("0 元件  ·  0 管道")
        self._counts.setObjectName("Tiny")
        layout.addWidget(self._counts)
        layout.addWidget(self._vline(14))
        schema = QLabel("UI SCHEMA 1.0")
        schema.setObjectName("Tiny")
        layout.addWidget(schema)

        return bar

    @staticmethod
    def _vline(height=24):
        line = QFrame()
        line.setFixedSize(1, height)
        line.setStyleSheet(f"background: {theme.BORDER_SOFT}; border: none;")
        return line

    # --------------------------------------------------------------- actions
    def _build_actions(self):
        self._new_action = QAction(icons.make_icon("new", theme.MUTED, 18), "新建图纸", self)
        self._new_action.setShortcut(QKeySequence.New)
        self._new_action.triggered.connect(self.new_document)

        self._open_action = QAction(icons.make_icon("import", theme.MUTED, 18), "打开 / 导入 .ui", self)
        self._open_action.setShortcut(QKeySequence.Open)
        self._open_action.triggered.connect(self.open_document)

        self._save_action = QAction(icons.make_icon("export", theme.MUTED, 18), "保存", self)
        self._save_action.setShortcut(QKeySequence.Save)
        self._save_action.triggered.connect(self.save_document)

        self._save_as_action = QAction("另存为 / 导出 .ui…", self)
        self._save_as_action.setShortcut(QKeySequence("Ctrl+Shift+S"))
        self._save_as_action.triggered.connect(self.export_document)

        self._demo_action = QAction(icons.make_icon("demo", theme.MUTED, 18), "加载示例工程", self)
        self._demo_action.triggered.connect(self.load_demo_document)

        self._rename_action = QAction("重命名工程…", self)
        self._rename_action.triggered.connect(self.rename_project)

        self._lock_action = QAction(icons.make_icon("lock", theme.MUTED, 17), "锁定", self)
        self._lock_action.setCheckable(True)
        self._lock_action.setToolTip("锁定画布，避免演示时误移动")
        self._lock_action.toggled.connect(self._toggle_lock)

        self._grid_action = QAction(icons.make_icon("grid", theme.MUTED, 17), "吸附", self)
        self._grid_action.setCheckable(True)
        self._grid_action.setChecked(True)
        self._grid_action.setToolTip("移动与缩放时吸附到 10px 网格")
        self._grid_action.toggled.connect(self._toggle_grid)

        self._about_action = QAction(icons.make_icon("help", theme.MUTED, 18), "关于 Torr Craft", self)
        self._about_action.triggered.connect(self.show_about)

        for action in (
            self._new_action,
            self._open_action,
            self._save_action,
            self._save_as_action,
            self._demo_action,
            self._rename_action,
        ):
            self.addAction(action)

    def _build_shortcuts(self):
        self._lock_action.setShortcut(QKeySequence("Ctrl+L"))
        self._grid_action.setShortcut(QKeySequence("Ctrl+G"))
        self.addAction(self._lock_action)
        self.addAction(self._grid_action)

    def _wire_canvas(self):
        self.canvas.selectionChanged.connect(self._on_selection_changed)
        self.canvas.documentChanged.connect(self._on_document_changed)
        self.canvas.countsChanged.connect(self._on_counts_changed)
        self.canvas.statusMessage.connect(self._set_status)
        self.canvas.connectModeChanged.connect(self._on_connect_mode_changed)
        self.canvas.cursorMoved.connect(self._on_cursor_moved)
        self.palette.componentActivated.connect(self._add_component)
        self.palette.pipeRequested.connect(self._palette_pipe_requested)

    # --------------------------------------------------------------- documents
    def _load_initial_demo(self):
        self._loading_document = True
        load_demo(self.canvas)
        self.canvas.set_project_name("双腔真空系统")
        self.canvas_scroll.horizontalScrollBar().setValue(0)
        self.canvas_scroll.verticalScrollBar().setValue(0)
        self._loading_document = False
        self._dirty = False
        self._current_path = None
        self._update_title()
        self._set_status("示例工程已就绪 · 拖拽元件体验组态，Ctrl+N 新建空白图纸")

    def new_document(self):
        if not self._confirm_discard():
            return
        self._loading_document = True
        self.canvas.clear_document(emit=False)
        self.canvas.set_project_name("未命名工程")
        self.canvas.set_connect_mode(False)
        self._loading_document = False
        self._current_path = None
        self._dirty = False
        self._set_connect_ui(False)
        self._update_title()
        self._set_status("已新建空白图纸 · 从左侧拖入元件开始组态")
        self.canvas_scroll.horizontalScrollBar().setValue(0)
        self.canvas_scroll.verticalScrollBar().setValue(0)

    def load_demo_document(self):
        if not self._confirm_discard():
            return
        self._loading_document = True
        load_demo(self.canvas)
        self.canvas.set_project_name("双腔真空系统")
        self.canvas.set_connect_mode(False)
        self.canvas_scroll.horizontalScrollBar().setValue(0)
        self.canvas_scroll.verticalScrollBar().setValue(0)
        self._loading_document = False
        self._current_path = None
        self._dirty = False
        self._set_connect_ui(False)
        self._update_title()
        self._set_status("示例工程已加载 · 腔室经插板阀隔离，分子泵与干泵已接入")

    def open_document(self):
        if not self._confirm_discard():
            return
        start = str(self._current_path.parent) if self._current_path else str(Path.cwd())
        path, _ = QFileDialog.getOpenFileName(
            self,
            "导入 Qt UI 文件",
            start,
            "Qt UI 文件 (*.ui);;所有文件 (*.*)",
        )
        if not path:
            return
        try:
            document = read_ui_file(path)
        except (UiFormatError, OSError) as exc:
            QMessageBox.warning(self, "无法导入", str(exc))
            self._set_status("导入失败 · " + str(exc), error=True)
            return
        self._apply_loaded_document(document, Path(path))
        if document.warnings:
            message = "\n".join("· " + item for item in document.warnings[:8])
            if len(document.warnings) > 8:
                message += f"\n… 另有 {len(document.warnings) - 8} 条提示"
            QMessageBox.information(
                self,
                "导入完成（含提示）",
                "图纸已载入，但有部分内容被跳过：\n\n" + message,
            )

    def _apply_loaded_document(self, document, path=None):
        self._loading_document = True
        self.canvas.apply_document(document)
        self.canvas.set_project_name(document.project_name)
        self.canvas.set_connect_mode(False)
        self.canvas_scroll.horizontalScrollBar().setValue(0)
        self.canvas_scroll.verticalScrollBar().setValue(0)
        self._loading_document = False
        self._current_path = Path(path) if path else None
        self._dirty = False
        self._set_connect_ui(False)
        self._update_title()
        name = self._current_path.name if self._current_path else "未命名工程"
        self._set_status(
            f"已导入 {name} · {len(self.canvas.devices)} 个元件 / {len(self.canvas.pipes)} 条管道"
        )

    def save_document(self):
        if self._current_path is None:
            return self.export_document()
        return self._write_to(self._current_path)

    def export_document(self):
        default_name = self._safe_filename(self.canvas.project_name) + ".ui"
        start_dir = self._current_path.parent if self._current_path else Path.cwd()
        path, _ = QFileDialog.getSaveFileName(
            self,
            "导出 Qt UI 文件",
            str(start_dir / default_name),
            "Qt UI 文件 (*.ui)",
        )
        if not path:
            return False
        if not path.lower().endswith(".ui"):
            path += ".ui"
        return self._write_to(Path(path))

    def _write_to(self, path):
        document = self.canvas.snapshot()
        document.project_name = self.canvas.project_name
        try:
            written = write_ui_file(document, path)
        except (UiFormatError, OSError) as exc:
            QMessageBox.warning(self, "导出失败", str(exc))
            self._set_status("导出失败 · " + str(exc), error=True)
            return False
        self._current_path = Path(written)
        self._dirty = False
        self._update_title()
        self._set_status(f"已导出 {self._current_path.name} · Qt UI 格式可直接导入本平台")
        return True

    def _confirm_discard(self):
        if not self._dirty:
            return True
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Question)
        box.setWindowTitle("保存当前图纸？")
        box.setText("当前图纸有未保存的修改。")
        box.setInformativeText("是否在继续前保存为 Qt .ui 文件？")
        box.setStandardButtons(QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
        box.setDefaultButton(QMessageBox.Save)
        result = box.exec_()
        if result == QMessageBox.Save:
            return bool(self.save_document())
        if result == QMessageBox.Cancel:
            return False
        return True

    def rename_project(self):
        name, ok = QInputDialog.getText(
            self,
            "重命名工程",
            "工程名称",
            text=self.canvas.project_name,
        )
        if ok and name.strip():
            self.canvas.set_project_name(name.strip()[:80])
            self._dirty = True
            self._update_title()
            self._set_status("工程已重命名")

    @staticmethod
    def _safe_filename(name):
        cleaned = re.sub(r'[\\/:*?"<>|]+', "_", name or "vacuum_system").strip(" .")
        return cleaned or "vacuum_system"

    def closeEvent(self, event):
        if not self._confirm_discard():
            event.ignore()
            return
        self._sim_timer.stop()
        event.accept()

    # ------------------------------------------------------------------ state
    def _on_document_changed(self, reason):
        if self._loading_document:
            return
        self._dirty = True
        self._update_title()
        self._set_status(f"{reason} · 图纸已修改")

    def _update_title(self):
        name = self.canvas.project_name
        meta_parts = []
        if self._current_path:
            meta_parts.append(self._current_path.name)
        else:
            meta_parts.append("未保存")
        if self._dirty:
            meta_parts.append("已修改")
        meta_parts.append("Qt .ui")
        self._project_name.setText(name)
        self._project_meta.setText(" · ".join(meta_parts))
        self._dirty_dot.setVisible(self._dirty)
        marker = " *" if self._dirty else ""
        self.setWindowTitle(f"{name}{marker} · Torr Craft")
        self._save_action.setEnabled(True)

    def _on_counts_changed(self, devices, pipes):
        self._counts.setText(f"{devices} 元件  ·  {pipes} 管道")

    def _on_selection_changed(self, obj):
        self._delete_btn.setEnabled(obj is not None and not self._lock_action.isChecked())
        if obj is None:
            self._set_status("未选择对象 · 双击元件可切换状态")
        self.inspector.show_selection(obj)

    def _on_cursor_moved(self, x, y):
        self._coords.setText(f"X {x:>4}   Y {y:>3}")

    def _set_status(self, message, error=False):
        self._status_label.setText(message)
        color = theme.ROSE if error or any(token in message for token in ("拒绝", "失败", "无法", "错误")) else theme.MUTED
        self._status_label.setStyleSheet(f"color: {color}; font-size: 10px;")
        self._status_dot.set_color(theme.ROSE if color == theme.ROSE else theme.GREEN)
        self._status_reset_timer.start(9000 if not error else 12000)

    def _reset_status(self):
        if self.canvas.devices:
            message = (
                f"就绪 · {len(self.canvas.devices)} 个元件 / {len(self.canvas.pipes)} 条管道"
            )
        else:
            message = "就绪 · 从左侧拖入元件开始组态"
        self._status_label.setText(message)
        self._status_label.setStyleSheet(f"color: {theme.MUTED}; font-size: 10px;")
        self._status_dot.set_color(theme.GREEN)

    # -------------------------------------------------------------- components
    def _add_component(self, device_key):
        if self._lock_action.isChecked():
            self._set_status("画布已锁定，解锁后再添加元件")
            return
        if self.canvas.connect_mode:
            self.canvas.set_connect_mode(False)
        self.canvas.add_device_at_center(device_key)

    def _palette_pipe_requested(self):
        if self._lock_action.isChecked():
            self._set_status("画布已锁定，解锁后再连接管道")
            return
        self.canvas.set_connect_mode(not self.canvas.connect_mode)

    def _pipe_toggled(self, checked):
        if checked:
            self.canvas.set_connect_mode(True)
        else:
            self.canvas.set_connect_mode(False)

    def _on_connect_mode_changed(self, enabled):
        self._set_connect_ui(enabled)

    def _set_connect_ui(self, enabled):
        for button in (self._select_btn, self._pipe_btn):
            button.blockSignals(True)
        self._select_btn.setChecked(not enabled)
        self._pipe_btn.setChecked(enabled)
        for button in (self._select_btn, self._pipe_btn):
            button.blockSignals(False)
        self.palette.set_pipe_checked(enabled)
        self.canvas.setCursor(Qt.CrossCursor if enabled else Qt.ArrowCursor)

    def _toggle_lock(self, checked):
        self.canvas.set_editing_locked(checked)
        self._select_btn.setEnabled(not checked)
        self._pipe_btn.setEnabled(not checked)
        self.palette.pipe_button.setEnabled(not checked)
        self._delete_btn.setEnabled(not checked and self.canvas.selection() is not None)
        self._set_status("画布已锁定 · 仅可查看与模拟运行" if checked else "画布已解锁 · 可继续编辑")
        if checked:
            self._set_connect_ui(False)

    def _toggle_grid(self, checked):
        self.canvas.set_snap_enabled(checked)
        self._set_status("网格吸附已开启" if checked else "网格吸附已关闭 · 自由定位")

    # -------------------------------------------------------------- simulation
    def _toggle_simulation(self, running):
        if running:
            self._sim_timer.start()
            self._sim_pill.setText("●  模拟遥测")
            self._set_status("模拟遥测运行中 · 状态与转速来自本地仿真")
        else:
            self._sim_timer.stop()
            self._sim_pill.setText("○  模拟已暂停")
            self._set_status("模拟遥测已暂停 · 当前值保持不变")

    def _on_tick(self):
        self.canvas.tick(0.05)
        self._tick_count += 1
        if self._tick_count % 5 == 0:
            self.inspector.refresh_runtime()

    # ---------------------------------------------------------------- dialogs
    def show_about(self):
        QMessageBox.about(
            self,
            "关于 Torr Craft",
            (
                f"<b>Torr Craft {__version__}</b><br>"
                "基于 PySide2 的真空系统监控低代码平台<br><br>"
                "· 分子泵 / 干泵 / 角阀 / 插板阀 / 腔室 / 管道<br>"
                "· 拖拽组态、边角缩放、自动正交布线<br>"
                "· 开关状态、软件连接、转速与压力遥测<br>"
                "· 导入 / 导出 Qt Designer .ui 文件<br><br>"
                "<span style='color:#8497ae'>当前为本地模拟遥测版本，"
                "设备通信适配层可替换为 Modbus / TCP / 串口。</span>"
            ),
        )


class QMenuBuilder:
    """Tiny helper that keeps a strong reference to the popped-up QMenu."""

    def __init__(self, parent):
        from PySide2.QtWidgets import QMenu

        self.menu = QMenu(parent)

    def addAction(self, action):
        self.menu.addAction(action)

    def addSeparator(self):
        self.menu.addSeparator()
