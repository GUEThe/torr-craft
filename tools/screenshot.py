"""Render a deterministic preview of the studio with the offscreen Qt platform."""

import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
if os.name == "nt":
    os.environ.setdefault("QT_QPA_FONTDIR", r"C:\Windows\Fonts")

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from torr_craft.app import create_application  # noqa: E402
from torr_craft.main_window import MainWindow  # noqa: E402


def main():
    app = create_application([])
    window = MainWindow()
    window.resize(1520, 940)
    window.show()
    app.processEvents()

    for _ in range(80):
        window.canvas.tick(0.05)
        app.processEvents()

    gate = window.canvas.devices.get("gate_1")
    if gate is not None:
        window.canvas.select(gate)
        window.inspector.refresh_runtime()
        window.inspector.show_selection(gate)
    app.processEvents()

    output_dir = ROOT / "artifacts"
    output_dir.mkdir(exist_ok=True)
    output = output_dir / "torr-craft-preview.png"
    pixmap = window.grab()
    if not pixmap.save(str(output), "PNG"):
        raise SystemExit(f"Could not write {output}")
    print(output)

    if window.canvas.pipes:
        pipe = window.canvas.pipes[0]
        window.canvas.set_pipe_route_mode(pipe, "custom")
        window.canvas.add_pipe_bend(pipe, None)
        window.canvas.select(pipe)
        window.inspector.show_selection(pipe)
        app.processEvents()
        pipe_output = output_dir / "pipe-routing-preview.png"
        pipe_pixmap = window.grab()
        if not pipe_pixmap.save(str(pipe_output), "PNG"):
            raise SystemExit(f"Could not write {pipe_output}")
        print(pipe_output)

    app.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
