"""A representative two-chamber vacuum system used for demos and previews."""

from .document import ComponentData, DocumentData, PipeData


def demo_document():
    components = [
        ComponentData(
            device_type="chamber",
            object_id="chamber_1",
            x=90,
            y=170,
            width=260,
            height=168,
            label="工艺腔",
            online=True,
            switched_on=False,
            speed=0,
            pressure=3.2e-7,
        ),
        ComponentData(
            device_type="gate",
            object_id="gate_1",
            x=390,
            y=200,
            width=146,
            height=106,
            label="插板阀 01",
            online=True,
            switched_on=True,
            pressure=1.0e-5,
        ),
        ComponentData(
            device_type="chamber",
            object_id="chamber_2",
            x=580,
            y=170,
            width=280,
            height=168,
            label="传输腔",
            online=True,
            switched_on=False,
            speed=0,
            pressure=4.8e-5,
        ),
        ComponentData(
            device_type="turbo",
            object_id="turbo_1",
            x=120,
            y=560,
            width=234,
            height=128,
            label="分子泵 01",
            online=True,
            switched_on=True,
            speed=42000,
            pressure=1.0e-5,
        ),
        ComponentData(
            device_type="dry",
            object_id="dry_1",
            x=430,
            y=560,
            width=216,
            height=118,
            label="干泵 01",
            online=True,
            switched_on=True,
            speed=1800,
            pressure=1.0e-5,
        ),
        ComponentData(
            device_type="angle",
            object_id="angle_1",
            x=180,
            y=424,
            width=126,
            height=96,
            label="角阀 01",
            online=True,
            switched_on=True,
            pressure=1.0e-5,
        ),
    ]
    pipes = [
        PipeData("pipe_1", "chamber_1", "gate_1"),
        PipeData("pipe_2", "gate_1", "chamber_2"),
        PipeData("pipe_3", "chamber_1", "angle_1"),
        PipeData("pipe_4", "angle_1", "turbo_1"),
        PipeData("pipe_5", "turbo_1", "dry_1"),
    ]
    return DocumentData(project_name="双腔真空系统", components=components, pipes=pipes)


def load_demo(canvas):
    canvas.apply_document(demo_document())
    for device in canvas.devices.values():
        if hasattr(device, "seed_display_speed"):
            device.seed_display_speed()
        if hasattr(device, "seed_open_phase"):
            device.seed_open_phase()
        device.update()
    canvas._status("示例工程已加载 · 拖拽元件体验组态，或按 Ctrl+N 新建空白图纸")
    canvas.update()
