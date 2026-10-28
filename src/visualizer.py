"""Visualization module for device telemetry.

Generates presentation-ready Matplotlib bar charts comparing average temperatures
across devices.
"""

import json
import logging
from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")  # Use headless Agg backend for robust CLI/CI rendering without Tkinter
import matplotlib.pyplot as plt

logger = logging.getLogger(__name__)


def generate_temperature_chart(
    json_path: str | Path,
    output_image_path: str | Path = "temperature_chart.png",
) -> Path:
    """Generate and save a bar chart comparing average temperature per device.

    Args:
        json_path: Path to the JSON summary file produced by the summarizer.
        output_image_path: Destination path for the saved chart image.

    Returns:
        Path to the generated chart image file.

    Raises:
        FileNotFoundError: If the input JSON file does not exist.
        ValueError: If JSON data is malformed or invalid.
    """
    in_path = Path(json_path)
    out_path = Path(output_image_path)

    if not in_path.is_file():
        raise FileNotFoundError(f"Summary JSON not found at: {in_path.resolve()}")

    with in_path.open("r", encoding="utf-8") as f:
        data: list[dict[str, Any]] = json.load(f)

    if not isinstance(data, list):
        raise ValueError("Expected JSON summary to contain a list of device records.")

    # Prepare figure
    fig, ax = plt.subplots(figsize=(8, 5), dpi=300)

    if not data:
        # Gracefully handle empty dataset without unhandled exceptions
        ax.text(
            0.5,
            0.5,
            "No devices to display\n(all devices exceeded threshold or no data available)",
            horizontalalignment="center",
            verticalalignment="center",
            transform=ax.transAxes,
            fontsize=12,
            color="dimgray",
        )
        ax.set_axis_off()
    else:
        devices = [item["device_id"] for item in data]
        temperatures = [item["average_temperature"] for item in data]

        # Use an accessible, professional color palette
        bar_color = "#2b5c8f"
        bars = ax.bar(devices, temperatures, color=bar_color, width=0.55, edgecolor="#1a365d")

        # Add numerical labels directly above each bar for clarity
        for bar in bars:
            height = bar.get_height()
            ax.annotate(
                f"{height:.2f}°C",
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 4),  # 4 points vertical offset
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=10,
                fontweight="bold",
                color="#1a202c",
            )

        # Labels and title
        ax.set_title("Average Temperature by Device", fontsize=14, fontweight="bold", pad=15)
        ax.set_xlabel("Device ID", fontsize=11, fontweight="bold", labelpad=8)
        ax.set_ylabel("Average Temperature (°C)", fontsize=11, fontweight="bold", labelpad=8)

        # Y-axis bounds with headroom for annotations
        max_temp = max(temperatures)
        ax.set_ylim(0, max_temp * 1.18)

        # Subtle horizontal grid lines for readability
        ax.grid(axis="y", linestyle="--", alpha=0.5, zorder=0)
        ax.set_axisbelow(True)

    # Prevent label clipping on smaller canvases
    plt.tight_layout()

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=300)
    plt.close(fig)

    logger.info("Temperature chart successfully saved to: %s", out_path.resolve())
    return out_path
