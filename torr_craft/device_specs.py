"""Device catalogue shared by the palette, canvas, inspector and .ui serializer."""

from dataclasses import dataclass
from typing import Dict, Tuple

from . import theme


@dataclass(frozen=True)
class DeviceSpec:
    key: str
    class_name: str
    label: str
    english: str
    icon: str
    accent: str
    default_size: Tuple[int, int]
    min_size: Tuple[int, int]
    default_label: str
    has_online: bool = True
    has_switch: bool = True
    has_speed: bool = False
    has_pressure: bool = False
    switch_on_text: str = "运行中"
    switch_off_text: str = "已停止"
    default_speed: int = 0
    max_speed: int = 60000
    speed_unit: str = "RPM"


DEVICE_SPECS: Dict[str, DeviceSpec] = {
    "chamber": DeviceSpec(
        key="chamber",
        class_name="ChamberWidget",
        label="腔室",
        english="VACUUM CHAMBER",
        icon="chamber",
        accent=theme.SKY,
        default_size=(260, 168),
        min_size=(176, 124),
        default_label="工艺腔",
        has_online=False,
        has_switch=False,
        has_pressure=True,
    ),
    "turbo": DeviceSpec(
        key="turbo",
        class_name="MolecularPumpWidget",
        label="分子泵",
        english="TURBO PUMP",
        icon="turbo",
        accent=theme.GREEN,
        default_size=(234, 128),
        min_size=(174, 106),
        default_label="分子泵 01",
        has_speed=True,
        default_speed=42000,
        max_speed=90000,
    ),
    "dry": DeviceSpec(
        key="dry",
        class_name="DryPumpWidget",
        label="干泵",
        english="DRY PUMP",
        icon="dry",
        accent=theme.AMBER,
        default_size=(216, 118),
        min_size=(166, 98),
        default_label="干泵 01",
        has_speed=True,
        default_speed=1800,
        max_speed=12000,
    ),
    "angle": DeviceSpec(
        key="angle",
        class_name="AngleValveWidget",
        label="角阀",
        english="ANGLE VALVE",
        icon="angle",
        accent=theme.ORANGE,
        default_size=(126, 96),
        min_size=(96, 76),
        default_label="角阀 01",
        switch_on_text="已开启",
        switch_off_text="已关闭",
    ),
    "gate": DeviceSpec(
        key="gate",
        class_name="GateValveWidget",
        label="插板阀",
        english="GATE VALVE",
        icon="gate",
        accent=theme.VIOLET,
        default_size=(146, 106),
        min_size=(112, 84),
        default_label="插板阀 01",
        switch_on_text="已开启",
        switch_off_text="已关闭",
    ),
}

CLASS_TO_KEY = {spec.class_name: key for key, spec in DEVICE_SPECS.items()}
PALETTE_ORDER = ("chamber", "turbo", "dry", "angle", "gate")
