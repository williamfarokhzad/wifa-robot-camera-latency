import json
from pathlib import Path
import subprocess
import sys
import unittest

from align import replay

ROOT = Path(__file__).resolve().parents[1]


def example(name):
    return json.loads((ROOT / "examples" / f"{name}.json").read_text())


class ReplayTests(unittest.TestCase):
    def test_known_landmark_and_velocity_times_delay(self):
        a, b = replay(example("moving"), 80, 50)
        self.assertEqual([r["target_at_capture_mm"] for r in (a, b)], [100, 100])
        self.assertEqual([r["target_using_arrival_mm"] for r in (a, b)], [112, 104])
        self.assertEqual([r["arrival_bias_mm"] for r in (a, b)], [12, 4])

    def test_stationary_control(self):
        row, = replay(example("stationary"), 80, 50)
        self.assertEqual(row["age_ms"], 65)
        self.assertEqual(row["arrival_bias_mm"], 0)

    def test_reject_reasons_and_optional_arrival_diagnostic(self):
        a, b, c, d = replay(example("rejected"), 80, 50)
        self.assertEqual([r["status"] for r in (a, b, c, d)],
                         ["stale", "pose_gap_too_large", "outside_pose_history", "ok"])
        self.assertNotIn("target_at_capture_mm", b)
        self.assertEqual(d["target_at_capture_mm"], 100)
        self.assertIsNone(d["target_using_arrival_mm"])

    def test_thresholds_are_inclusive(self):
        record = example("moving")
        self.assertEqual(replay(record, 60, 40)[0]["status"], "ok")
        self.assertEqual(replay(record, 59, 40)[0]["status"], "stale")
        self.assertEqual(replay(record, 60, 39)[0]["status"], "pose_gap_too_large")

    def test_negative_velocity_changes_bias_sign(self):
        record = example("moving")
        for pose in record["poses"]:
            pose["camera_x_mm"] *= -1
        for frame in record["frames"]:
            frame["target_from_camera_mm"] = 200 - frame["target_from_camera_mm"]
        row = replay(record, 80, 50)[0]
        self.assertEqual(row["target_at_capture_mm"], 100)
        self.assertEqual(row["arrival_bias_mm"], -12)

    def test_reject_bad_inputs(self):
        for broken in ("clock", "duplicate", "nan", "bool"):
            with self.subTest(broken=broken):
                record = example("moving")
                if broken == "clock":
                    record["frames"][0]["arrival_ms"] = 2
                elif broken == "duplicate":
                    record["poses"][1]["time_ms"] = 0
                elif broken == "nan":
                    record["poses"][1]["camera_x_mm"] = float("nan")
                else:
                    record["frames"][0]["capture_ms"] = True
                with self.assertRaises(ValueError):
                    replay(record, 80, 50)

    def test_cli_reports_invalid_gap_without_traceback(self):
        result = subprocess.run([sys.executable, "align.py", "examples/moving.json",
                                 "--max-gap-ms", "0"], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn("max_gap_ms must be positive", result.stderr)
        self.assertNotIn("Traceback", result.stderr)
