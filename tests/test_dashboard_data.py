
"""Tests for dashboard data integrity and validation."""

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from dashboard.data import load_forecast_data


def fingerprint(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class DashboardDataTests(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)

        self.root = Path(self.temp.name)
        self.forecast = self.root / "forecast.csv"
        self.usda = self.root / "usda.csv"
        self.metadata = self.root / "metadata.json"

        self.forecast_data = pd.DataFrame({
            "state_name": ["IOWA", "ILLINOIS"],
            "forecast_2026": [200.0, 210.0],
        })

        self.usda_data = pd.DataFrame({
            "state_name": ["IOWA", "ILLINOIS"],
            "year": [2025, 2025],
            "value": [195.0, 205.0],
        })

        self.forecast_data.to_csv(self.forecast, index=False)
        self.usda_data.to_csv(self.usda, index=False)

        self.info = {
            "forecast_year": 2026,
            "forecast_states": 2,
            "forecast_sha256": fingerprint(self.forecast),
            "source_sha256": fingerprint(self.usda),
            "validation_metrics": {
                "2023": {"model_mae": 14.0},
                "2024": {"model_mae": 16.0},
            },
            "development_average_mae": 15.0,
        }

        self.save_metadata()

    def save_metadata(self):
        self.metadata.write_text(
            json.dumps(self.info, indent=2),
            encoding="utf-8",
        )

    def load(self):
        return load_forecast_data(
            self.forecast,
            self.metadata,
            self.usda,
        )

    def test_valid_data_loads(self):
        forecast, historical, metadata = self.load()

        self.assertEqual(len(forecast), 2)
        self.assertEqual(len(historical), 2)
        self.assertEqual(metadata["forecast_year"], 2026)

    def test_modified_forecast_rejected(self):
        self.forecast.write_text(
            self.forecast.read_text() + "\n",
            encoding="utf-8",
        )

        with self.assertRaisesRegex(
            ValueError,
            "Forecast CSV fingerprint mismatch",
        ):
            self.load()

    def test_modified_usda_source_rejected(self):
        self.usda.write_text(
            self.usda.read_text() + "\n",
            encoding="utf-8",
        )

        with self.assertRaisesRegex(
            ValueError,
            "USDA source fingerprint mismatch",
        ):
            self.load()

    def test_duplicate_states_rejected(self):
        duplicated = pd.DataFrame({
            "state_name": ["IOWA", "IOWA"],
            "forecast_2026": [200.0, 210.0],
        })

        duplicated.to_csv(self.forecast, index=False)

        self.info["forecast_sha256"] = fingerprint(self.forecast)
        self.save_metadata()

        with self.assertRaisesRegex(
            ValueError,
            "Duplicate forecast states",
        ):
            self.load()

    def test_incorrect_validation_mae_rejected(self):
        self.info["development_average_mae"] = 99.0
        self.save_metadata()

        with self.assertRaisesRegex(
            ValueError,
            "Development-validation MAE mismatch",
        ):
            self.load()

    def test_missing_forecast_rejected(self):
        self.forecast.unlink()

        with self.assertRaises(FileNotFoundError):
            self.load()


if __name__ == "__main__":
    unittest.main()
