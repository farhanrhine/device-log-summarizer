"""Unit tests for sensor readings sanitization."""

import unittest
from src.sanitizer import clean_sensor_readings


class TestCleanSensorReadings(unittest.TestCase):
    """Test suite verifying type conversion, filtering, clipping, and edge cases."""

    def test_mixed_inputs_conversion_and_filtering(self):
        """Test conversion of valid numeric forms, dropping negatives, None, and text."""
        raw_inputs = [
            25.5,
            "42.0",
            "100",
            -1.0,        # negative error flag -> dropped
            -999,        # negative error flag -> dropped
            None,        # null -> dropped
            "invalid",   # unparseable -> dropped
            "N/A",       # unparseable -> dropped
            0.0,         # zero is non-negative -> preserved
            12,          # integer -> converted to float
        ]
        expected = [25.5, 42.0, 100.0, 0.0, 12.0]
        result = clean_sensor_readings(raw_inputs)
        self.assertEqual(result, expected)

    def test_clipping_above_500(self):
        """Test that values strictly greater than 500.0 are capped at 500.0."""
        raw_inputs = [499.9, 500.0, 500.1, 750, "999.99", 500.0001]
        expected = [499.9, 500.0, 500.0, 500.0, 500.0, 500.0]
        result = clean_sensor_readings(raw_inputs)
        self.assertEqual(result, expected)

    def test_edge_cases_empty_and_all_invalid(self):
        """Test empty lists, None input, and completely invalid lists return empty lists."""
        self.assertEqual(clean_sensor_readings([]), [])
        self.assertEqual(clean_sensor_readings(None), [])
        self.assertEqual(
            clean_sensor_readings([None, "error", -15.2, -100, True, False, ""]),
            [],
        )


if __name__ == "__main__":
    unittest.main()
