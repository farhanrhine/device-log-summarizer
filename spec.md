# Device Log Summarizer - Specification

## 1. Project Overview & Objective
Build a lightweight, robust command-line interface (CLI) tool in Python to clean sensor data, ingest and aggregate device telemetry CSV logs, export filtered metrics to JSON, and visualize results with an AI-assisted Matplotlib script.

---

## 2. Technology Stack & Design Decisions
- **Language**: Python 3.10+
- **Project & Package Manager**: `uv`
- **Core Processing**: Python Standard Library (`csv`, `json`, `argparse`, `pathlib`, `typing`, `unittest`)
  - *Rationale*: Zero external dependencies for data processing, sub-50ms CLI startup latency, streaming memory efficiency ($O(U)$ space complexity for $U$ unique devices), and explicit validation without silent coercion bugs.
- **Visualization**: `matplotlib` (installed via `uv add matplotlib`)
- **No Heavy Frameworks**: No `pandas` or `numpy` for data ingestion to maintain minimal binary footprint and demonstrate fundamental software engineering principles.

---

## 3. Project Structure
```text
device-log-summarizer/
├── src/
│   ├── __init__.py
│   ├── sanitizer.py       # Section 1: clean_sensor_readings function
│   ├── summarizer.py      # Section 2: CSV streaming ingest, aggregation, and JSON export
│   ├── visualizer.py      # Section 3: AI-assisted Matplotlib chart generation
│   └── cli.py             # CLI entry point with argparse
├── tests/
│   ├── __init__.py
│   └── test_sanitizer.py  # Section 1 unit tests
├── device_telemetry.csv   # Sample input CSV
├── summary.json           # Sample output JSON
├── temperature_chart.png  # Generated bar chart
├── PROMPT_LOG.md          # Section 3 AI collaboration log
├── README.md              # Setup, usage, and architectural notes
├── pyproject.toml         # uv project metadata and dependencies
└── spec.md                # This specification
```

---

## 4. Detailed Requirements by Section

### Section 1: Coding Logic & Sanitization
- **Function Signature**: `clean_sensor_readings(readings: list[any]) -> list[float]` in `src/sanitizer.py`.
- **Transformation Rules**:
  1. **Type Conversion & Filtering**: Convert valid elements to `float`. Drop values that cannot be converted (e.g., malformed strings), are `None`, or are negative ($< 0.0$).
  2. **Clipping**: If a valid float exceeds `500.0`, clamp it to `500.0`.
  3. **Edge Case Handling**: Empty lists or lists containing only invalid inputs must return `[]` without raising unhandled exceptions.
- **Testing**:
  - Test suite in `tests/test_sanitizer.py` covering standard cases, string floats, non-numeric values, `None`, negative values, clipping at 500.0, and empty/all-invalid inputs.
  - Runnable via `uv run pytest` or `python -m unittest discover tests`.

### Section 2: CSV Processing & Aggregation
- **Input File**: `device_telemetry.csv` with header: `device_id,status,temperature`.
  - Must include statuses: `ACTIVE`, `WARNING`, and `ERROR`.
  - Must include at least one device with an average temperature $> 80.0$.
- **Ingestion & Aggregation (`src/summarizer.py`)**:
  - Read CSV using standard `csv.DictReader` in a single pass.
  - Group records by `device_id`.
  - Calculate per device:
    - `total_records`: Integer count of all valid records for this device.
    - `average_temperature`: Float mean temperature, rounded to 2 decimal places.
    - `error_count`: Integer count of records where `status == "ERROR"`.
- **Filtering**:
  - Exclude any device where `average_temperature > 80.0`.
- **Export & Terminal Display**:
  - Export remaining devices to a formatted JSON file (`indent=2`).
  - Print a cleanly formatted summary table to `stdout`.
- **JSON Schema**:
  ```json
  [
    {
      "device_id": "DEV_A",
      "total_records": 10,
      "average_temperature": 68.45,
      "error_count": 1
    }
  ]
  ```
- **Robustness Guarantees**:
  - Return clear, user-friendly error messages if the input file does not exist (`FileNotFoundError`) or cannot be read.
  - Skip malformed rows (missing columns, invalid floats) with a warning rather than crashing.

### Section 3: AI Prompting & Visualization
- **Visualization Script (`src/visualizer.py`)**:
  - Loads the generated JSON output from Section 2.
  - Produces a clear, readable bar chart comparing the `average_temperature` per device using Matplotlib.
  - Saves the figure to an image file (e.g., `temperature_chart.png`).
- **Prompt Log Deliverable (`PROMPT_LOG.md`)**:
  - Document the AI collaboration process covering:
    1. **Initial Prompt**: The exact prompt given to the AI.
    2. **AI Mistake / Flaw**: A concrete formatting or layout issue produced in the first attempt (e.g., overlapping device labels, missing axis titles/units, unreadable contrast, unhandled empty JSON).
    3. **Follow-up Prompt**: The prompt used to diagnose and fix the flaw.

---

## 5. CLI Interface Design
- **Entry Point**: `src/cli.py`
- **Arguments**:
  - `--input`, `-i`: Path to the input CSV file (default: `device_telemetry.csv`).
  - `--output`, `-o`: Path to save the aggregated JSON summary (default: `summary.json`).
  - `--plot`, `-p`: Path to save the visualization chart (default: `temperature_chart.png`).
  - `--skip-plot`: Flag to run ingestion and JSON export without generating the chart.
  - `--demo-sanitizer`: Optional flag to run a demonstration of the Section 1 data cleaner.

---

## 6. Submission Deliverables Checklist
- [ ] Source code organized cleanly in `src/`.
- [ ] Unit tests for Section 1 in `tests/test_sanitizer.py`.
- [ ] Sample input file `device_telemetry.csv`.
- [ ] Sample output file `summary.json`.
- [ ] Output chart image `temperature_chart.png`.
- [ ] Complete `PROMPT_LOG.md` documenting AI interactions.
- [ ] `README.md` with setup instructions (`uv sync` / `uv run`), CLI commands, and test execution instructions.
