"""Left component library."""

from PySide2.QtCore import QSize, Qt, Signal
from PySide2.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
)

from . import icons, theme
from .device_specs import DEVICE_SPECS, PALETTE_ORDER
from .widgets import PaletteCard


class ComponentPalette(QFrame):
    componentActivated = Signal(str)
    pipeRequested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setFixedWidth(232)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        kicker = QLabel("LIBRARY")
        kicker.setObjectName("SectionKicker")
        layout.addWidget(kicker)

        title_row = QHBoxLayout()
        title = QLabel("组件库")
        title.setStyleSheet(f"color: {theme.TEXT}; font-size: 16px; font-weight: 700;")
        count = QLabel("5 类")
        count.setObjectName("Tiny")
        title_row.addWidget(title)
        title_row.addStretch(1)
        title_row.addWidget(count)
        layout.addLayout(title_row)

        hint = QLabel("拖拽元件至画布，或单击快速添加")
        hint.setObjectName("Hint")
        hint.setWordWrap(True)
        layout.addWidget(hint)
        layout.addSpacing(2)

        grid = QGridLayout()
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(8)
        self._cards = {}
        for index, key in enumerate(PALETTE_ORDER):
            card = PaletteCard(key)
            card.activated.connect(self.componentActivated)
            grid.addWidget(card, index // 2, index % 2)
            self._cards[key] = card
        self.pipe_button = QToolButton()
        self.pipe_button.setObjectName("PipeCard")
        self.pipe_button.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.pipe_button.setIcon(icons.make_icon("pipe", theme.CYAN, 34))
        self.pipe_button.setIconSize(QSize(36, 36))
        self.pipe_button.setText("管道")
        self.pipe_button.setToolTip("管道连接 · 依次点击两个端点")
        self.pipe_button.setCheckable(True)
        self.pipe_button.setCursor(Qt.PointingHandCursor)
        self.pipe_button.setFixedHeight(84)
        self.pipe_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.pipe_button.setStyleSheet(
            f"""
            QToolButton#PipeCard {{
                background: #101d30;
                border: 1px solid {theme.BORDER};
                border-radius: 11px;
                color: #c7d5e6;
                padding-top: 8px;
                padding-bottom: 7px;
                font-size: 11px;
                font-weight: 600;
            }}
            QToolButton#PipeCard:hover {{
                background: #172941;
                border-color: rgba(34, 211, 238, 0.55);
                color: {theme.TEXT};
            }}
            QToolButton#PipeCard:checked {{
                background: rgba(34, 211, 238, 0.12);
                border-color: {theme.CYAN};
                color: {theme.CYAN_SOFT};
            }}
            """
        )
        self.pipe_button.clicked.connect(self._pipe_clicked)
        grid.addWidget(self.pipe_button, len(PALETTE_ORDER) // 2, len(PALETTE_ORDER) % 2)

        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        layout.addLayout(grid)

        pipe_hint = QLabel("管道：依次点击两个端点；腔室之间必须经插板阀隔离。")
        pipe_hint.setObjectName("Tiny")
        pipe_hint.setWordWrap(True)
        layout.addWidget(pipe_hint)

        layout.addStretch(1)

        rule = QFrame()
        rule.setObjectName("InsetCard")
        rule_layout = QVBoxLayout(rule)
        rule_layout.setContentsMargins(12, 11, 12, 11)
        rule_layout.setSpacing(6)
        rule_title_row = QHBoxLayout()
        dot = QLabel("●")
        dot.setStyleSheet(f"color: {theme.VIOLET}; font-size: 7px;")
        rule_title = QLabel("连接规则")
        rule_title.setObjectName("SectionTitle")
        rule_title_row.addWidget(dot)
        rule_title_row.addWidget(rule_title)
        rule_title_row.addStretch(1)
        rule_layout.addLayout(rule_title_row)
        for line in (
            "泵、阀、腔室均可接入管道",
            "腔室直连被禁止",
            "双腔之间需经插板阀",
        ):
            label = QLabel("·  " + line)
            label.setObjectName("Tiny")
            label.setWordWrap(True)
            rule_layout.addWidget(label)
        layout.addWidget(rule)

    def _pipe_clicked(self, checked):
        self.pipeRequested.emit()

    def set_pipe_checked(self, checked):
        self.pipe_button.setChecked(bool(checked))
