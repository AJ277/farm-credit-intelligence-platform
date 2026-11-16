
"""USDA corn-yield forecasting research prototype."""

import csv
from pathlib import Path

import mlflow
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "components/usda-data-engineering/data/raw/usda_state_crop_clean.csv"
OUTPUT = ROOT / "output/forecasting"


def load_data():
    df = pd.read_csv(SOURCE)

    df = df[
        (df["commodity_desc"].str.upper() == "CORN")
        & (df["statisticcat_desc"].str.upper() == "YIELD")
        & (df["unit_desc"].str.upper().str.replace(" ", "") == "BU/ACRE")
        & (df["state_name"].str.upper() != "OTHER STATES")
    ].copy()

    df["value"] = pd.to_numeric(df["value"], errors="raise")
    df["year"] = pd.to_numeric(df["year"], errors="raise").astype(int)

    if df.duplicated(["state_name", "year"]).any():
        raise ValueError("Duplicate state-year observations")

    if df["value"].isna().any() or (df["value"] <= 0).any():
        raise ValueError("Invalid corn-yield values")

    df = df.sort_values(["state_name", "year"])

    for lag in (1, 2):
        df[f"lag{lag}"] = df.groupby("state_name")["value"].shift(lag)
        df[f"year_lag{lag}"] = df.groupby("state_name")["year"].shift(lag)

    # Only use observations from consecutive prior years.
    df = df[
        (df["year_lag1"] == df["year"] - 1)
        & (df["year_lag2"] == df["year"] - 2)
    ].copy()

    df["two_year_average"] = (df["lag1"] + df["lag2"]) / 2

    return df


def evaluate(df, year):
    train = df[df["year"] < year]
    test = df[df["year"] == year]

    if train.empty or test.empty:
        raise ValueError(f"Insufficient data for validation year {year}")

    features = ["lag1", "two_year_average"]

    model = LinearRegression()
    model.fit(train[features], train["value"])

    predicted = model.predict(test[features])
    baseline = test["lag1"].to_numpy()

    metrics = {
        "model_mae": mean_absolute_error(test["value"], predicted),
        "baseline_mae": mean_absolute_error(test["value"], baseline),
        "model_rmse": np.sqrt(mean_squared_error(test["value"], predicted)),
        "baseline_rmse": np.sqrt(mean_squared_error(test["value"], baseline)),
    }

    return metrics


def forecast_next_year(df):
    features = ["lag1", "two_year_average"]

    model = LinearRegression()
    model.fit(df[features], df["value"])

    latest = df[df["year"] == 2025].copy()

    if latest.empty:
        raise ValueError("2025 observations are required")

    # Shift the known 2025 and 2024 yields into the
    # features needed to estimate 2026 yield.
    latest["two_year_average"] = (
        latest["value"] + latest["lag1"]
    ) / 2
    latest["lag1"] = latest["value"]

    latest["forecast_2026"] = model.predict(latest[features])

    return latest[["state_name", "forecast_2026"]].sort_values(
        "state_name"
    )


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)

    df = load_data()
    print(f"Eligible feature rows: {len(df)}")
    print(f"State series: {df['state_name'].nunique()}")

    # Local-only MLflow tracking.
    mlflow.set_tracking_uri("sqlite:///" + str((OUTPUT / "mlflow.db").resolve()))
    mlflow.set_experiment("Farm Credit Corn Yield Forecasting")

    with mlflow.start_run(run_name="linear_regression_walk_forward"):
        mlflow.log_param("model", "LinearRegression")
        mlflow.log_param("features", "lag1,two_year_average")
        mlflow.log_param("validation_years", "2023,2024")
        mlflow.log_param("source", "USDA historical data 2020-2025")

        for year in (2023, 2024):
            metrics = evaluate(df, year)

            print(f"\nValidation year: {year}")
            for name, value in metrics.items():
                print(f"  {name}: {value:.3f}")
                mlflow.log_metric(f"{name}_{year}", float(value))

        # 2025 has already been examined during earlier model
        # development. It is not an untouched final test set.
        exploratory = evaluate(df, 2025)
        print("\n2025 exploratory evaluation:")
        for name, value in exploratory.items():
            print(f"  {name}: {value:.3f}")
            mlflow.log_metric(f"exploratory_{name}_2025", float(value))

    forecast = forecast_next_year(df)

    path = OUTPUT / "corn_yield_2026_experimental.csv"
    forecast.to_csv(path, index=False)

    print(f"\n2026 experimental estimates: {len(forecast)} states")
    print(f"Forecast file: {path}")
    print("FORECASTING WORKFLOW PASSED")
    print("Estimates are experimental, not official USDA forecasts.")


if __name__ == "__main__":
    main()
