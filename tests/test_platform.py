"""Headless regression tests for geometry, connection rules and .ui round-trip."""

import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
if os.name == "nt":
    os.environ.setdefault("QT_QPA_FONTDIR", r"C:\Windows\Fonts")

from PySide2.QtCore import QEvent, QPointF, QRect, Qt  # noqa: E402
from PySide2.QtGui import QMouseEvent  # noqa: E402
from PySide2.QtWidgets import QApplication  # noqa: E402

from torr_craft.components.canvas import Canvas  # noqa: E402
from torr_craft.demo import demo_document  # noqa: E402
from torr_craft.inspector import InspectorPanel  # noqa: E402
from torr_craft.ui_io import (  # noqa: E402
    UiFormatError,
    dumps_ui,
    loads_ui,
    read_ui_file,
    write_ui_file,
)


class PlatformTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def make_canvas(self):
        canvas = Canvas()
        first = canvas.add_device("chamber", x=80, y=100, select=False)
        gate = canvas.add_device("gate", x=420, y=130, select=False)
        second = canvas.add_device("chamber", x=660, y=100, select=False)
        return canvas, first, gate, second

    def test_component_resize_and_minimum(self):
        canvas = Canvas()
        pump = canvas.add_device("turbo", x=100, y=100)
        pump.set_geometry_rect(QRect(120, 140, 280, 150), notify=True)
        self.assertEqual((pump.x(), pump.y(), pump.width(), pump.height()), (120, 140, 280, 150))
        pump.set_geometry_rect(QRect(130, 150, 10, 10))
        self.assertGreaterEqual(pump.width(), pump.spec.min_size[0])
        self.assertGreaterEqual(pump.height(), pump.spec.min_size[1])

    def test_handle_resize_with_mouse_events(self):
        canvas = Canvas()
        canvas.show()
        pump = canvas.add_device("turbo", x=100, y=100)
        canvas.select(pump)
        self.app.processEvents()
        start = QPointF(pump.width() - 2, pump.height() - 2)
        end = start + QPointF(40, 20)
        global_start = QPointF(pump.mapToGlobal(start.toPoint()))
        global_end = QPointF(pump.mapToGlobal(end.toPoint()))

        def send(kind, pos, global_pos, button, buttons):
            event = QMouseEvent(kind, pos, global_pos, button, buttons, Qt.NoModifier)
            QApplication.sendEvent(pump, event)

        send(QEvent.MouseButtonPress, start, global_start, Qt.LeftButton, Qt.LeftButton)
        send(QEvent.MouseMove, end, global_end, Qt.NoButton, Qt.LeftButton)
        send(QEvent.MouseButtonRelease, end, global_end, Qt.LeftButton, Qt.NoButton)
        self.assertGreater(pump.width(), 234)
        self.assertGreater(pump.height(), 128)
        canvas.close()

    def test_inspector_exposes_online_and_switch_controls(self):
        canvas = Canvas()
        pump = canvas.add_device("turbo", x=100, y=100)
        panel = InspectorPanel()
        panel.set_canvas(canvas)
        panel.show()
        canvas.select(pump)
        self.app.processEvents()
        self.assertIsNotNone(panel._state_section.parentWidget())
        self.assertTrue(panel._online_switch.isVisible())
        self.assertTrue(panel._power_switch.isVisible())
        panel._online_switch.setChecked(False)
        self.assertFalse(pump.online)
        panel._power_switch.setChecked(False)
        self.assertFalse(pump.switched_on)
        panel.close()
        canvas.close()

    def test_chamber_to_chamber_requires_inline_gate_valve(self):
        canvas, first, gate, second = self.make_canvas()
        self.assertIsNone(canvas.create_pipe(first, second))
        self.assertIsNone(canvas.create_pipe(first, gate))
        self.assertIsNone(canvas.create_pipe(gate, second))
        self.assertEqual(len(canvas.pipes), 0)

        self.assertTrue(
            canvas.mount_gate(gate, first.device_id, second.device_id)
        )
        self.assertEqual(gate.flange_a_id, first.device_id)
        self.assertEqual(gate.flange_b_id, second.device_id)
        self.assertEqual(canvas.inline_gate_count(), 1)
        self.assertEqual(len(canvas.pipes), 0)

    def test_inspector_gate_inline_flange_controls(self):
        canvas, first, gate, second = self.make_canvas()
        panel = InspectorPanel()
        panel.set_canvas(canvas)
        panel.show()
        canvas.select(gate)
        self.app.processEvents()
        self.assertTrue(panel._flange_section.isVisible())
        self.assertFalse(panel._links_section.isVisible())
        self.assertEqual(panel._flange_a_combo.count(), 3)
        self.assertTrue(panel._auto_mount_btn.isEnabled())

        panel._flange_a_combo.setCurrentIndex(
            panel._flange_a_combo.findData(first.device_id)
        )
        panel._flange_b_combo.setCurrentIndex(
            panel._flange_b_combo.findData(second.device_id)
        )
        self.app.processEvents()
        self.assertEqual(gate.flange_a_id, first.device_id)
        self.assertEqual(gate.flange_b_id, second.device_id)
        self.assertEqual(canvas.inline_gate_count(), 1)
        panel.close()
        canvas.close()

    def test_auto_mount_picks_chambers_on_both_sides(self):
        canvas, first, gate, second = self.make_canvas()
        self.assertTrue(canvas.auto_mount_gate(gate))
        self.assertEqual(gate.flange_a_id, first.device_id)
        self.assertEqual(gate.flange_b_id, second.device_id)
        self.assertEqual(canvas.inline_gate_count(), 1)

    def test_inline_gate_rejects_invalid_targets(self):
        canvas, first, gate, second = self.make_canvas()
        pump = canvas.add_device("turbo", x=360, y=300, select=False)
        self.assertFalse(canvas.mount_gate(gate, first.device_id, pump.device_id))
        self.assertFalse(canvas.mount_gate(gate, first.device_id, first.device_id))
        self.assertTrue(canvas.set_gate_flange(gate, "a", first.device_id))
        self.assertFalse(canvas.set_gate_flange(gate, "b", first.device_id))
        self.assertEqual(gate.flange_b_id, "")

    def test_indirect_chamber_bypass_is_rejected(self):
        canvas, first, gate, second = self.make_canvas()
        valve = canvas.add_device("angle", x=360, y=300, select=False)
        self.assertIsNotNone(canvas.create_pipe(first, valve))
        self.assertIsNone(canvas.create_pipe(valve, second))
        self.assertEqual(len(canvas.pipes), 1)

    def test_duplicate_connection_rejected(self):
        canvas, first, gate, second = self.make_canvas()
        valve = canvas.add_device("angle", x=360, y=300, select=False)
        self.assertIsNotNone(canvas.create_pipe(first, valve))
        self.assertIsNone(canvas.create_pipe(valve, first))
        self.assertEqual(len(canvas.pipes), 1)

    def test_pipe_route_modes_and_custom_bends(self):
        canvas = Canvas()
        chamber = canvas.add_device("chamber", x=80, y=100, select=False)
        valve = canvas.add_device("angle", x=500, y=300, select=False)
        pipe = canvas.create_pipe(chamber, valve)
        self.assertIsNotNone(pipe)
        self.assertEqual(pipe.route_mode, "auto")
        self.assertEqual(len(canvas.pipe_points(pipe)), 4)

        canvas.set_pipe_route_mode(pipe, "custom")
        self.assertEqual(pipe.route_mode, "custom")
        self.assertGreaterEqual(len(pipe.bend_points), 2)
        before = len(pipe.bend_points)
        self.assertTrue(canvas.add_pipe_bend(pipe, QPointF(420, 250)))
        self.assertEqual(len(pipe.bend_points), before + 1)
        self.assertTrue(canvas.remove_pipe_bend(pipe, 0))
        self.assertEqual(len(pipe.bend_points), before)
        self.assertTrue(canvas.clear_pipe_bends(pipe))
        self.assertEqual(pipe.bend_points, [])

        canvas.set_pipe_route_mode(pipe, "straight")
        self.assertEqual(pipe.route_mode, "straight")
        self.assertEqual(len(canvas.pipe_points(pipe)), 2)

    def test_custom_bend_can_be_dragged(self):
        canvas = Canvas()
        canvas.show()
        chamber = canvas.add_device("chamber", x=80, y=100, select=False)
        valve = canvas.add_device("angle", x=500, y=300, select=False)
        pipe = canvas.create_pipe(chamber, valve)
        canvas.set_pipe_route_mode(pipe, "custom")
        self.assertTrue(canvas.add_pipe_bend(pipe, QPointF(370, 250)))
        canvas.select(pipe)
        self.app.processEvents()
        self.assertGreaterEqual(len(pipe.bend_points), 1)
        original = pipe.bend_points[0]
        start = QPointF(*original)
        end = start + QPointF(40, 30)
        global_start = QPointF(canvas.mapToGlobal(start.toPoint()))
        global_end = QPointF(canvas.mapToGlobal(end.toPoint()))

        def send(kind, pos, global_pos, button, buttons):
            event = QMouseEvent(kind, pos, global_pos, button, buttons, Qt.NoModifier)
            QApplication.sendEvent(canvas, event)

        send(QEvent.MouseButtonPress, start, global_start, Qt.LeftButton, Qt.LeftButton)
        send(QEvent.MouseMove, end, global_end, Qt.NoButton, Qt.LeftButton)
        send(QEvent.MouseButtonRelease, end, global_end, Qt.LeftButton, Qt.NoButton)
        self.assertNotEqual(pipe.bend_points[0], original)
        canvas.close()

    def test_inspector_pipe_routing_controls(self):
        canvas = Canvas()
        chamber = canvas.add_device("chamber", x=80, y=100, select=False)
        valve = canvas.add_device("angle", x=500, y=300, select=False)
        pipe = canvas.create_pipe(chamber, valve)
        panel = InspectorPanel()
        panel.set_canvas(canvas)
        panel.show()
        canvas.select(pipe)
        self.app.processEvents()
        self.assertEqual(panel._pipe_route_combo.currentData(), "auto")

        straight_index = panel._pipe_route_combo.findData("straight")
        panel._pipe_route_combo.setCurrentIndex(straight_index)
        self.assertEqual(pipe.route_mode, "straight")
        panel._pipe_add_bend_btn.click()
        self.assertEqual(pipe.route_mode, "custom")
        self.assertGreater(len(pipe.bend_points), 0)
        self.assertIn("拐点", panel._pipe_bend_count.text())
        panel.close()
        canvas.close()

    def test_pump_telemetry_ramps_and_spins_down(self):
        canvas = Canvas()
        pump = canvas.add_device("turbo", x=100, y=100)
        pump.online = True
        pump.switched_on = True
        pump.target_speed = 42000
        for _ in range(200):
            pump.tick(0.05)
        self.assertGreater(pump.display_speed, 1000)
        pump.switched_on = False
        for _ in range(200):
            pump.tick(0.05)
        self.assertLess(pump.display_speed, 1000)

    def test_deleting_chamber_clears_inline_gate_flange(self):
        canvas, first, gate, second = self.make_canvas()
        canvas.mount_gate(gate, first.device_id, second.device_id)
        self.assertEqual(canvas.inline_gate_count(), 1)
        canvas._delete_device(first)
        self.assertEqual(gate.flange_a_id, "")
        self.assertEqual(canvas.inline_gate_count(), 0)
        self.assertEqual(len(canvas.devices), 2)

    def test_ui_round_trip_preserves_properties(self):
        document = demo_document()
        xml = dumps_ui(document)
        self.assertIn("<ui version=\"4.0\">", xml)
        self.assertIn("MolecularPumpWidget", xml)
        self.assertIn("sourceId", xml)
        self.assertIn("flangeAId", xml)
        self.assertIn("flangeBId", xml)

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "system.ui"
            written = write_ui_file(document, path)
            loaded = read_ui_file(written)

        self.assertEqual(loaded.project_name, document.project_name)
        self.assertEqual(len(loaded.components), len(document.components))
        self.assertEqual(len(loaded.pipes), len(document.pipes))
        by_id = {c.object_id: c for c in loaded.components}
        original = {c.object_id: c for c in document.components}
        for object_id, source in original.items():
            target = by_id[object_id]
            self.assertEqual(target.device_type, source.device_type)
            self.assertEqual(target.label, source.label)
            self.assertEqual((target.x, target.y, target.width, target.height),
                             (source.x, source.y, source.width, source.height))
            self.assertEqual(target.online, source.online)
            self.assertEqual(target.switched_on, source.switched_on)
            self.assertEqual(target.speed, source.speed)
            self.assertAlmostEqual(target.pressure, source.pressure)
            self.assertEqual(target.flange_a_id, source.flange_a_id)
            self.assertEqual(target.flange_b_id, source.flange_b_id)

        canvas = Canvas()
        canvas.apply_document(loaded)
        self.assertEqual(len(canvas.devices), 6)
        self.assertEqual(len(canvas.pipes), 3)
        self.assertEqual(canvas.inline_gate_count(), 1)
        self.assertIn("turbo_1", canvas.devices)
        turbo = canvas.devices["turbo_1"]
        self.assertTrue(turbo.switched_on)
        self.assertEqual(turbo.target_speed, 42000)
        gate = canvas.devices["gate_1"]
        self.assertEqual(gate.flange_a_id, "chamber_1")
        self.assertEqual(gate.flange_b_id, "chamber_2")

    def test_ui_round_trip_preserves_pipe_routes(self):
        document = demo_document()
        document.pipes[0].route_mode = "custom"
        document.pipes[0].bend_points = [(145, 380), (320, 380)]
        document.pipes[1].route_mode = "straight"
        loaded = loads_ui(dumps_ui(document))
        self.assertEqual(loaded.pipes[0].route_mode, "custom")
        self.assertEqual(loaded.pipes[0].bend_points, [(145, 380), (320, 380)])
        self.assertEqual(loaded.pipes[1].route_mode, "straight")

        canvas = Canvas()
        canvas.apply_document(loaded)
        self.assertEqual(canvas.pipes[0].route_mode, "custom")
        self.assertEqual(canvas.pipes[0].bend_points, [(145, 380), (320, 380)])
        self.assertEqual(canvas.pipes[1].route_mode, "straight")

    def test_bundled_example_ui_is_valid(self):
        sample = Path(__file__).resolve().parents[1] / "examples" / "demo_system.ui"
        loaded = read_ui_file(sample)
        self.assertEqual(loaded.project_name, "双腔真空系统")
        self.assertEqual(len(loaded.components), 6)
        self.assertEqual(len(loaded.pipes), 3)
        self.assertFalse(loaded.warnings)
        gate = next(c for c in loaded.components if c.device_type == "gate")
        self.assertEqual(gate.flange_a_id, "chamber_1")
        self.assertEqual(gate.flange_b_id, "chamber_2")

    def test_import_rejects_unrelated_ui(self):
        with self.assertRaises(UiFormatError):
            loads_ui("<ui version=\"4.0\"><class>X</class><widget class=\"QWidget\" name=\"X\"/></ui>")

    def test_import_drops_unsafe_chamber_pipe(self):
        document = demo_document()
        document.pipes.append(
            type(document.pipes[0])("pipe_bad", "chamber_1", "chamber_2")
        )
        loaded = loads_ui(dumps_ui(document))
        self.assertFalse(any(
            {p.source_id, p.target_id} == {"chamber_1", "chamber_2"} for p in loaded.pipes
        ))
        self.assertTrue(loaded.warnings)

    def test_import_drops_indirect_isolation_bypass(self):
        from torr_craft.document import PipeData

        document = demo_document()
        document.pipes.append(PipeData("pipe_bypass", "angle_1", "chamber_2"))
        loaded = loads_ui(dumps_ui(document))
        self.assertFalse(any(
            {p.source_id, p.target_id} == {"angle_1", "chamber_2"} for p in loaded.pipes
        ))
        self.assertTrue(any("插板阀" in warning for warning in loaded.warnings))

    def test_import_rejects_non_chamber_gate_flange(self):
        document = demo_document()
        gate = next(c for c in document.components if c.device_type == "gate")
        gate.flange_b_id = "turbo_1"
        loaded = loads_ui(dumps_ui(document))
        imported_gate = next(c for c in loaded.components if c.device_type == "gate")
        self.assertEqual(imported_gate.flange_a_id, "chamber_1")
        self.assertEqual(imported_gate.flange_b_id, "")
        self.assertTrue(any("法兰" in warning for warning in loaded.warnings))

    def test_import_skips_legacy_gate_pipes(self):
        from torr_craft.document import PipeData

        document = demo_document()
        document.pipes.append(PipeData("pipe_old", "chamber_1", "gate_1"))
        loaded = loads_ui(dumps_ui(document))
        self.assertFalse(any(
            "gate_1" in (p.source_id, p.target_id) for p in loaded.pipes
        ))
        self.assertTrue(any("内联法兰" in warning for warning in loaded.warnings))
        gate = next(c for c in loaded.components if c.device_type == "gate")
        self.assertEqual(gate.flange_a_id, "chamber_1")


if __name__ == "__main__":
    unittest.main()
