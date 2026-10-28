"""Sensor reading sanitization module.

Provides functionality to clean, filter, and normalize raw sensor telemetry.
"""

from typing import Any, Sequence
import math


def clean_sensor_readings(readings: Sequence[Any] | None) -> list[float]:
    """Clean and normalize a list of mixed sensor readings.

    Rules applied:
    1. Type Conversion & Filtering:
       - Converts valid numeric values and numeric strings to floats.
       - Skips None, booleans, and unparseable values without raising errors.
       - Drops negative readings (< 0.0) as invalid error flags.
       - Drops NaN and infinite float values.
    2. Clipping:
       - Caps/limits any reading > 500.0 to 500.0.
    3. Edge Case Handling:
       - Returns an empty list for None, empty lists, or collections of entirely invalid data.

    Args:
        readings: A sequence of mixed sensor inputs (int, float, str, None, etc.).

    Returns:
        A list of cleaned and clamped floats.
    """
    if readings is None:
        return []

    cleaned: list[float] = []

    for item in readings:
        # None values are dropped
        if item is None:
            continue

        # In Python, bool is a subclass of int (isinstance(True, int) is True).
        # Sensor data should not treat boolean values as numeric telemetry.
        if isinstance(item, bool):
            continue

        try:
            val = float(item)
        except (ValueError, TypeError):
            continue

        # Drop NaN or Infinite values
        if math.isnan(val) or math.isinf(val):
            continue

        # Drop negative readings (sensor error flags)
        if val < 0.0:
            continue

        # Clip values exceeding 500.0
        if val > 500.0:
            val = 500.0

        cleaned.append(val)

    return cleaned
