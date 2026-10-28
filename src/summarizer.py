"""Core data processing and telemetry summarization module.

Handles CSV ingestion, aggregation by device, filtering, JSON export,
and terminal table rendering.
"""

from collections import defaultdict
import csv
import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def process_telemetry_csv(
    file_path: str | Path,
    temperature_threshold: float = 80.0,
) -> list[dict[str, Any]]:
    """Ingest device telemetry from CSV, aggregate metrics, and filter devices.

    Args:
        file_path: Path to the CSV file.
        temperature_threshold: Maximum allowable average temperature. Devices with
            an average temperature strictly greater than this value are filtered out.

    Returns:
        List of aggregated device summaries matching the schema:
        [
            {
                "device_id": str,
                "total_records": int,
                "average_temperature": float,
                "error_count": int,
            },
            ...
        ]

    Raises:
        FileNotFoundError: If the input CSV file does not exist.
        ValueError: If the file is not a valid CSV or is missing required columns.
    """
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Telemetry file not found at: {path.resolve()}")

    # Aggregation accumulators: device_id -> metrics
    # Using float sum and count avoids holding all raw records in memory
    device_data: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"total_records": 0, "temperature_sum": 0.0, "error_count": 0}
    )

    with path.open(mode="r", encoding="utf-8-sig", newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        if not reader.fieldnames:
            raise ValueError(f"CSV file at {path} is empty or has no header.")

        required_cols = {"device_id", "status", "temperature"}
        actual_cols = {col.strip() for col in reader.fieldnames if col}
        if not required_cols.issubset(actual_cols):
            missing = required_cols - actual_cols
            raise ValueError(
                f"CSV header missing required columns: {sorted(missing)}. Found: {sorted(actual_cols)}"
            )

        for line_number, row in enumerate(reader, start=2):
            device_id = row.get("device_id", "").strip() if row.get("device_id") else ""
            status = row.get("status", "").strip().upper() if row.get("status") else ""
            temp_raw = row.get("temperature", "").strip() if row.get("temperature") else ""

            if not device_id:
                logger.warning("Line %d: Missing device_id. Skipping row.", line_number)
                continue

            try:
                temperature = float(temp_raw)
            except (ValueError, TypeError):
                logger.warning(
                    "Line %d: Invalid temperature '%s' for device '%s'. Skipping row.",
                    line_number,
                    temp_raw,
                    device_id,
                )
                continue

            stats = device_data[device_id]
            stats["total_records"] += 1
            stats["temperature_sum"] += temperature
            if status == "ERROR":
                stats["error_count"] += 1

    # Finalize aggregation and filter out devices with average_temperature > threshold
    aggregated: list[dict[str, Any]] = []
    for device_id, stats in sorted(device_data.items()):
        total = stats["total_records"]
        if total == 0:
            continue
        avg_temp = round(stats["temperature_sum"] / total, 2)

        # Exclude devices with average temperature above threshold
        if avg_temp > temperature_threshold:
            logger.info(
                "Filtering out %s: average temperature %.2f exceeds threshold %.2f",
                device_id,
                avg_temp,
                temperature_threshold,
            )
            continue

        aggregated.append(
            {
                "device_id": device_id,
                "total_records": total,
                "average_temperature": avg_temp,
                "error_count": stats["error_count"],
            }
        )

    return aggregated


def export_to_json(data: list[dict[str, Any]], output_path: str | Path) -> None:
    """Save aggregated telemetry results to a formatted JSON file."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def print_summary_table(data: list[dict[str, Any]], threshold: float = 80.0) -> None:
    """Print a clean formatted terminal table of aggregated telemetry."""
    if not data:
        print("\nNo devices met the inclusion criteria (all filtered or no data).")
        return

    headers = ("Device ID", "Total Records", "Avg Temp (deg C)", "Error Count")
    col_widths = (12, 15, 18, 13)

    header_row = (
        f"{headers[0]:<{col_widths[0]}} | "
        f"{headers[1]:>{col_widths[1]}} | "
        f"{headers[2]:>{col_widths[2]}} | "
        f"{headers[3]:>{col_widths[3]}}"
    )
    separator = "-" * len(header_row)

    print("\n" + separator)
    print(f"DEVICE TELEMETRY SUMMARY (Filtered: Avg Temp <= {threshold:.1f} deg C)")
    print(separator)
    print(header_row)
    print(separator)

    for item in data:
        print(
            f"{item['device_id']:<{col_widths[0]}} | "
            f"{item['total_records']:>{col_widths[1]}} | "
            f"{item['average_temperature']:>{col_widths[2]}.2f} | "
            f"{item['error_count']:>{col_widths[3]}}"
        )

    print(separator + "\n")
