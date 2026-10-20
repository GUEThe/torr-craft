"""Plain document dataclasses shared by the canvas and the .ui codec."""

from dataclasses import dataclass, field
from typing import List

CANVAS_WIDTH = 1440
CANVAS_HEIGHT = 900


@dataclass
class ComponentData:
    device_type: str
    object_id: str
    x: int
    y: int
    width: int
    height: int
    label: str
    online: bool = True
    switched_on: bool = False
    speed: int = 0
    pressure: float = 1.0e-5
    # Gate valves are mounted inline, with one chamber flange on each side.
    flange_a_id: str = ""
    flange_b_id: str = ""


@dataclass
class PipeData:
    pipe_id: str
    source_id: str
    target_id: str


@dataclass
class DocumentData:
    project_name: str = "未命名工程"
    components: List[ComponentData] = field(default_factory=list)
    pipes: List[PipeData] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
