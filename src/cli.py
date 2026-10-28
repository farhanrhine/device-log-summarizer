"""Command Line Interface (CLI) for Device Log Summarizer."""

import argparse
import logging
import sys
from pathlib import Path

from src.sanitizer import clean_sensor_readings
from src.summarizer import export_to_json, print_summary_table, process_telemetry_csv
from src.visualizer import generate_temperature_chart


def setup_logging(verbose: bool = False) -> None:
    """Configure console logging level and format."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="[%(levelname)s] %(message)s",
    )


def run_sanitizer_demo() -> None:
    """Demonstrate Section 1 sensor cleaning logic with varied sample inputs."""
    sample_inputs = [
        "45.2",
        -999.0,      # negative error flag -> dropped
        None,        # null value -> dropped
        "invalid",   # unconvertible -> dropped
        550.0,       # > 500.0 -> clipped to 500.0
        "120.5",
        0.0,
        -1.5,        # dropped
        "310.25",
    ]
    print("\n--- Section 1: Sensor Readings Sanitizer Demo ---")
    print(f"Raw Input:     {sample_inputs}")
    cleaned = clean_sensor_readings(sample_inputs)
    print(f"Cleaned Output: {cleaned}\n")


def build_parser() -> argparse.ArgumentParser:
    """Build and return command-line argument parser."""
    parser = argparse.ArgumentParser(
        prog="device-log-summarizer",
        description="Ingest, aggregate, filter, and visualize device telemetry logs.",
    )
    parser.add_argument(
        "-i",
        "--input",
        type=Path,
        default=Path("device_telemetry.csv"),
        help="Path to the input device telemetry CSV file (default: device_telemetry.csv)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("summary.json"),
        help="Path to export the aggregated JSON summary (default: summary.json)",
    )
    parser.add_argument(
        "-p",
        "--plot",
        type=Path,
        default=Path("temperature_chart.png"),
        help="Path to save the generated visualization chart (default: temperature_chart.png)",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=80.0,
        help="Maximum average temperature threshold for devices (default: 80.0)",
    )
    parser.add_argument(
        "--skip-plot",
        action="store_true",
        help="Skip generating the Matplotlib temperature chart",
    )
    parser.add_argument(
        "--demo-sanitizer",
        action="store_true",
        help="Run a demonstration of Section 1 sensor readings cleaner",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose debug logging",
    )
    return parser


def main() -> int:
    """Main execution routine for the CLI."""
    parser = build_parser()
    args = parser.parse_args()
    setup_logging(args.verbose)

    if args.demo_sanitizer:
        run_sanitizer_demo()
        return 0

    try:
        # Step 1: Ingest, aggregate, and filter CSV data
        logging.info("Processing telemetry from: %s", args.input)
        summaries = process_telemetry_csv(args.input, temperature_threshold=args.threshold)

        # Step 2: Print terminal table
        print_summary_table(summaries, threshold=args.threshold)

        # Step 3: Export results to JSON
        export_to_json(summaries, args.output)
        logging.info("Aggregated results exported to: %s", args.output)

        # Step 4: Generate visualization chart unless skipped
        if not args.skip_plot:
            chart_path = generate_temperature_chart(args.output, args.plot)
            logging.info("Temperature comparison chart saved to: %s", chart_path)

        logging.info("Run completed successfully.")
        return 0

    except FileNotFoundError as err:
        logging.error("File error: %s", err)
        return 1
    except ValueError as err:
        logging.error("Data error: %s", err)
        return 1
    except Exception as err:
        logging.error("Unexpected error occurred: %s", err, exc_info=args.verbose)
        return 2


if __name__ == "__main__":
    sys.exit(main())
