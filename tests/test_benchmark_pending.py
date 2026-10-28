import importlib.util
import unittest
from pathlib import Path


spec = importlib.util.spec_from_file_location(
    "benchmarks_pending", Path(__file__).resolve().parents[1] / "scripts/gen-benchmarks.py"
)
benchmarks = importlib.util.module_from_spec(spec)
spec.loader.exec_module(benchmarks)


class PendingWorkloadsTests(unittest.TestCase):
    def test_source_without_measurements_is_explicitly_pending(self):
        sources = {"http_concurrent": {"xu": "@main"}}
        platforms = {"macos-arm64": {"benches": [{"name": "startup", "xu_wall_ms": 1}]}}
        for en in (False, True):
            rendered = benchmarks.render_pending_workloads(sources, platforms, en)
            self.assertIn('id="pending-workloads"', rendered)
            self.assertIn("openBenchCodeModal('http_concurrent'", rendered)
        self.assertEqual(len(platforms["macos-arm64"]["benches"]), 1)

    def test_measurements_replace_pending_notice(self):
        sources = {"http_concurrent": {"xu": "@main"}}
        platforms = {"macos-arm64": {"benches": [{"name": "http_concurrent", "xu_wall_ms": 4}]}}
        self.assertEqual(benchmarks.render_pending_workloads(sources, platforms, True), "")
        self.assertEqual(benchmarks.render_pending_workloads({}, {}, False), "")
