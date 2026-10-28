"""Unit tests for telemetry data processing and summarization."""

import json
from pathlib import Path
import tempfile
import unittest

from src.summarizer import export_to_json, process_telemetry_csv


class TestSummarizer(unittest.TestCase):
    """Test suite verifying CSV ingestion, metrics, filtering, and JSON export."""

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.test_dir.cleanup)

    def test_process_telemetry_csv_aggregation_and_filtering(self):
        """Test standard aggregation and filtering of devices with avg temp > 80.0."""
        csv_content = (
            "device_id,status,temperature\n"
            "DEV_A,ACTIVE,60.0\n"
            "DEV_A,WARNING,70.0\n"
            "DEV_A,ERROR,80.0\n"          # DEV_A avg: 70.0, errors: 1 -> KEPT
            "DEV_HOT,ACTIVE,85.0\n"
            "DEV_HOT,ERROR,95.0\n"         # DEV_HOT avg: 90.0, errors: 1 -> FILTERED OUT (>80)
            "DEV_B,ACTIVE,50.0\n"
            "DEV_B,ACTIVE,52.0\n"          # DEV_B avg: 51.0, errors: 0 -> KEPT
        )
        csv_path = Path(self.test_dir.name) / "telemetry.csv"
        csv_path.write_text(csv_content, encoding="utf-8")

        results = process_telemetry_csv(csv_path)

        self.assertEqual(len(results), 2)
        dev_a = next(r for r in results if r["device_id"] == "DEV_A")
        self.assertEqual(dev_a["total_records"], 3)
        self.assertAlmostEqual(dev_a["average_temperature"], 70.0)
        self.assertEqual(dev_a["error_count"], 1)

        dev_b = next(r for r in results if r["device_id"] == "DEV_B")
        self.assertEqual(dev_b["total_records"], 2)
        self.assertAlmostEqual(dev_b["average_temperature"], 51.0)
        self.assertEqual(dev_b["error_count"], 0)

        # Confirm DEV_HOT is filtered out
        self.assertFalse(any(r["device_id"] == "DEV_HOT" for r in results))

    def test_file_not_found(self):
        """Test raising FileNotFoundError for missing CSV files."""
        non_existent = Path(self.test_dir.name) / "does_not_exist.csv"
        with self.assertRaises(FileNotFoundError):
            process_telemetry_csv(non_existent)

    def test_malformed_rows_graceful_skipping(self):
        """Test that malformed rows (bad temperature, missing ID) are safely skipped."""
        csv_content = (
            "device_id,status,temperature\n"
            "DEV_OK,ACTIVE,65.0\n"
            "DEV_OK,ACTIVE,corrupted_temp\n"  # should skip
            ",ERROR,70.0\n"                   # missing device_id -> skip
            "DEV_OK,ERROR,75.0\n"
        )
        csv_path = Path(self.test_dir.name) / "corrupt.csv"
        csv_path.write_text(csv_content, encoding="utf-8")

        results = process_telemetry_csv(csv_path)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["device_id"], "DEV_OK")
        self.assertEqual(results[0]["total_records"], 2)
        self.assertAlmostEqual(results[0]["average_temperature"], 70.0)
        self.assertEqual(results[0]["error_count"], 1)

    def test_utf8_bom_support(self):
        """Test that CSV files with UTF-8 BOM are handled without parsing errors."""
        csv_content = (
            "\ufeffdevice_id,status,temperature\n"
            "DEV_BOM,ACTIVE,62.0\n"
        )
        csv_path = Path(self.test_dir.name) / "bom.csv"
        csv_path.write_text(csv_content, encoding="utf-8")

        results = process_telemetry_csv(csv_path)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["device_id"], "DEV_BOM")

    def test_export_to_json(self):
        """Test exporting structured data to JSON format."""
        data = [
            {
                "device_id": "DEV_A",
                "total_records": 4,
                "average_temperature": 67.25,
                "error_count": 0,
            }
        ]
        out_path = Path(self.test_dir.name) / "output.json"
        export_to_json(data, out_path)

        self.assertTrue(out_path.is_file())
        with out_path.open("r", encoding="utf-8") as f:
            loaded = json.load(f)
        self.assertEqual(loaded, data)


if __name__ == "__main__":
    unittest.main()
