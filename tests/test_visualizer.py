"""Unit tests for the visualization module."""

import json
from pathlib import Path
import tempfile
import unittest

import matplotlib
matplotlib.use("Agg")

from src.visualizer import generate_temperature_chart


class TestVisualizer(unittest.TestCase):
    """Test suite verifying chart generation and edge cases."""

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.test_dir.cleanup)

    def test_generate_temperature_chart_success(self):
        """Test successful generation of bar chart from valid JSON data."""
        data = [
            {"device_id": "DEV_A", "total_records": 5, "average_temperature": 65.5, "error_count": 0},
            {"device_id": "DEV_B", "total_records": 8, "average_temperature": 74.2, "error_count": 1},
        ]
        json_path = Path(self.test_dir.name) / "summary.json"
        json_path.write_text(json.dumps(data), encoding="utf-8")

        output_img = Path(self.test_dir.name) / "test_chart.png"
        result_path = generate_temperature_chart(json_path, output_img)

        self.assertTrue(result_path.is_file())
        self.assertGreater(result_path.stat().st_size, 1000)

    def test_generate_chart_empty_data(self):
        """Test generating chart from empty JSON list handles gracefully without crashing."""
        json_path = Path(self.test_dir.name) / "empty.json"
        json_path.write_text("[]", encoding="utf-8")

        output_img = Path(self.test_dir.name) / "empty_chart.png"
        result_path = generate_temperature_chart(json_path, output_img)

        self.assertTrue(result_path.is_file())
        self.assertGreater(result_path.stat().st_size, 1000)

    def test_generate_chart_missing_file(self):
        """Test raising FileNotFoundError when input JSON is absent."""
        missing_path = Path(self.test_dir.name) / "non_existent.json"
        with self.assertRaises(FileNotFoundError):
            generate_temperature_chart(missing_path)

    def test_generate_chart_invalid_json_structure(self):
        """Test raising ValueError when JSON root is not a list."""
        invalid_path = Path(self.test_dir.name) / "invalid.json"
        invalid_path.write_text('{"device": "DEV_A"}', encoding="utf-8")
        with self.assertRaises(ValueError):
            generate_temperature_chart(invalid_path)


if __name__ == "__main__":
    unittest.main()
