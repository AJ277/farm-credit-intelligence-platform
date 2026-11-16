
"""Data loading and integrity validation for the FCA dashboard."""

import hashlib
import json
import math
from pathlib import Path

import pandas as pd


def sha256_file(path):
    """Calculate the SHA-256 fingerprint of a file."""
    path = Path(path)
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_forecast_data(forecast_csv, metadata_json, usda_csv):
    """Load validated agricultural forecasting datasets."""

    forecast_csv = Path(forecast_csv)
    metadata_json = Path(metadata_json)
    usda_csv = Path(usda_csv)

    # 1. Confirm all required files exist.
    for path in (forecast_csv, metadata_json, usda_csv):
        if not path.is_file():
            raise FileNotFoundError(
                f"Required dashboard data file missing: {path}"
            )

    # 2. Load forecast metadata.
    metadata = json.loads(
        metadata_json.read_text(encoding="utf-8")
    )

    # 3. Verify file integrity.
    if sha256_file(forecast_csv) != metadata["forecast_sha256"]:
        raise ValueError("Forecast CSV fingerprint mismatch")

    if sha256_file(usda_csv) != metadata["source_sha256"]:
        raise ValueError("USDA source fingerprint mismatch")

    # 4. Verify forecast reporting period.
    if metadata["forecast_year"] != 2026:
        raise ValueError("Unexpected forecast year")

    # 5. Load CSV datasets.
    forecast = pd.read_csv(forecast_csv)
    historical = pd.read_csv(usda_csv)

    # 6. Verify forecast completeness.
    if len(forecast) != metadata["forecast_states"]:
        raise ValueError("Forecast row-count mismatch")

    if forecast["state_name"].isna().any():
        raise ValueError("Forecast contains missing state names")

    if forecast["state_name"].duplicated().any():
        raise ValueError("Duplicate forecast states")

    # 7. Check forecast values.
    values = pd.to_numeric(
        forecast["forecast_2026"],
        errors="coerce",
    )

    if not values.map(
        lambda value: math.isfinite(value) and value > 0
    ).all():
        raise ValueError("Invalid 2026 forecast values")

    # 8. Verify model validation metadata.
    validation = metadata["validation_metrics"]

    if set(validation) != {"2023", "2024"}:
        raise ValueError("Unexpected validation years")

    actual_average = sum(
        float(validation[year]["model_mae"])
        for year in ("2023", "2024")
    ) / 2

    reported_average = float(
        metadata["development_average_mae"]
    )

    if (
        not math.isfinite(reported_average)
        or not math.isclose(
            actual_average,
            reported_average,
            rel_tol=1e-9,
        )
    ):
        raise ValueError(
            "Development-validation MAE mismatch"
        )

    return forecast, historical, metadata
