
"""Tests for the master platform corn-yield forecasting engine."""

import unittest

from forecasting.corn_yield_forecast import (
    load_data,
    evaluate,
    forecast_next_year,
)


class ForecastingTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.data = load_data()

    def test_feature_data(self):
        self.assertEqual(len(self.data), 164)
        self.assertEqual(self.data["state_name"].nunique(), 41)
        self.assertFalse(
            self.data[["lag1", "lag2", "two_year_average"]]
            .isna().any().any()
        )

    def test_chronological_lags(self):
        self.assertTrue(
            (self.data["year_lag1"] == self.data["year"] - 1).all()
        )
        self.assertTrue(
            (self.data["year_lag2"] == self.data["year"] - 2).all()
        )

    def test_walk_forward_validation(self):
        for year in (2023, 2024):
            metrics = evaluate(self.data, year)

            self.assertGreaterEqual(metrics["model_mae"], 0)
            self.assertGreaterEqual(metrics["baseline_mae"], 0)
            self.assertGreaterEqual(metrics["model_rmse"], 0)

    def test_future_data_not_used_in_2023_validation(self):
        original = evaluate(self.data, 2023)

        modified = self.data.copy()
        modified.loc[modified["year"] == 2025, "value"] *= 10

        revised = evaluate(modified, 2023)

        self.assertAlmostEqual(
            original["model_mae"],
            revised["model_mae"],
        )

    def test_forecast_completeness(self):
        forecast = forecast_next_year(self.data)

        self.assertEqual(len(forecast), 41)
        self.assertEqual(forecast["state_name"].nunique(), 41)
        self.assertFalse(forecast["forecast_2026"].isna().any())


if __name__ == "__main__":
    unittest.main()
