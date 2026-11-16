
"""Negative tests for forecast integrity safeguards."""

import csv
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import combined_report


class ForecastIntegrityTests(unittest.TestCase):

    def test_modified_forecast_is_rejected(self):
        original = combined_report.FORECAST
        self.assertTrue(original.is_file())

        with tempfile.TemporaryDirectory() as directory:
            modified = Path(directory) / "modified_forecast.csv"
            shutil.copy2(original, modified)

            with modified.open(newline="", encoding="utf-8") as file:
                reader = csv.DictReader(file)
                fields = reader.fieldnames
                rows = list(reader)

            # Change one prediction while retaining valid CSV structure.
            rows[0]["forecast_2026"] = str(
                float(rows[0]["forecast_2026"]) + 1
            )

            with modified.open("w", newline="", encoding="utf-8") as file:
                writer = csv.DictWriter(file, fieldnames=fields)
                writer.writeheader()
                writer.writerows(rows)

            # The changed file must no longer match its fingerprint.
            with patch.object(combined_report, "FORECAST", modified):
                with self.assertRaisesRegex(
                    ValueError, "Forecast fingerprint mismatch"
                ):
                    combined_report.main()


if __name__ == "__main__":
    unittest.main()
