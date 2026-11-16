
"""Generate a combined FCA financial and USDA agricultural research report."""

import csv
import math
import subprocess
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

LAUNCHER = ROOT / "scripts/platform.sh"

USDA = (
    ROOT
    / "components"
    / "usda-data-engineering"
    / "data"
    / "raw"
    / "usda_state_crop_clean.csv"
)

FORECAST = (
    ROOT
    / "output"
    / "forecasting"
    / "corn_yield_2026_experimental.csv"
)

REPORT = ROOT / "output" / "combined_report.md"


def get_data(*arguments):
    """Retrieve JSON data using the unified platform launcher."""

    result = subprocess.run(
        [str(LAUNCHER), *arguments],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
        timeout=120,
    )

    return json.loads(result.stdout)


def load_usda_yields():
    """Load actual 2025 corn-yield observations."""

    if not USDA.is_file():
        raise FileNotFoundError(
            f"USDA dataset missing: {USDA}"
        )

    with USDA.open(
        encoding="utf-8-sig",
        newline="",
    ) as file:

        reader = csv.DictReader(file)

        yields = []

        for row in reader:

            if (
                row["year"] == "2025"
                and row["commodity_desc"].upper() == "CORN"
                and row["statisticcat_desc"].upper() == "YIELD"
                and row["unit_desc"].upper().replace(" ", "")
                == "BU/ACRE"
                and row["state_name"].upper() != "OTHER STATES"
            ):

                yields.append(
                    (
                        row["state_name"],
                        float(row["value"].replace(",", "")),
                    )
                )

    if len(yields) != 41:
        raise ValueError(
            f"Expected 41 USDA state observations, found {len(yields)}"
        )

    if len({state for state, _ in yields}) != len(yields):
        raise ValueError("Duplicate USDA state observations")

    if any(not math.isfinite(value) or value <= 0 for _, value in yields):
        raise ValueError("Invalid USDA yield observation")

    return yields


def load_forecasts(historical_yields):
    """Load and validate experimental 2026 estimates."""

    if not FORECAST.is_file():
        raise FileNotFoundError(
            "Forecast data missing. "
            "Run ./scripts/platform.sh forecast first."
        )

    with FORECAST.open(
        encoding="utf-8-sig",
        newline="",
    ) as file:

        forecasts = list(csv.DictReader(file))

    if len(forecasts) != 41:
        raise ValueError(
            f"Expected 41 forecasts, found {len(forecasts)}"
        )

    names = [row["state_name"] for row in forecasts]

    if len(set(names)) != 41:
        raise ValueError("Duplicate forecast states")

    historical_states = {
        state for state, _ in historical_yields
    }

    if set(names) != historical_states:
        raise ValueError(
            "Forecast states do not match historical USDA states"
        )

    result = []

    for row in forecasts:

        value = float(row["forecast_2026"])

        if not math.isfinite(value) or value <= 0:
            raise ValueError(
                f"Invalid forecast for {row['state_name']}"
            )

        result.append(
            (
                row["state_name"],
                value,
            )
        )

    return result


def main():
    """Generate the combined research report."""

    # --------------------------------------------------
    # 1. FCA financial research
    # --------------------------------------------------

    financial = get_data(
        "finance",
        "--limit",
        "5",
    )

    if len(financial) != 5:
        raise ValueError(
            "Expected five FCA financial records"
        )

    quarters = {
        row["quarter"]
        for row in financial
    }

    if quarters != {"2026Q3"}:
        raise ValueError(
            "Unexpected FCA financial reporting quarter"
        )

    # --------------------------------------------------
    # 2. FCA document evidence
    # --------------------------------------------------

    documents = get_data(
        "documents",
        "Farm Credit System funding conditions",
        "--mode",
        "lexical",
    )

    if not documents:
        raise ValueError(
            "No FCA document evidence retrieved"
        )

    # --------------------------------------------------
    # 3. USDA historical and forecast data
    # --------------------------------------------------

    yields = load_usda_yields()

    forecasts = load_forecasts(yields)

    # Validate forecast provenance before generating a report.
    import hashlib

    metadata_path = ROOT / "output/forecasting/forecast_metadata.json"
    if not metadata_path.is_file():
        raise FileNotFoundError("Forecast metadata missing. Rerun forecast.")

    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()

    if metadata.get("source") != str(USDA.relative_to(ROOT)):
        raise ValueError("Forecast source path does not match USDA source")
    if digest(USDA) != metadata.get("source_sha256"):
        raise ValueError("USDA source fingerprint mismatch")
    if digest(FORECAST) != metadata.get("forecast_sha256"):
        raise ValueError("Forecast fingerprint mismatch")
    if metadata.get("forecast_year") != 2026:
        raise ValueError("Unexpected forecast year")
    if metadata.get("forecast_states") != len(forecasts):
        raise ValueError("Forecast row-count mismatch")

    metrics = metadata.get("validation_metrics", {})
    if set(metrics) != {"2023", "2024"}:
        raise ValueError("Missing development validation metrics")

    average_mae = float(metadata["development_average_mae"])
    actual_average = sum(float(metrics[y]["model_mae"]) for y in ("2023", "2024")) / 2
    if not math.isfinite(average_mae) or not math.isclose(average_mae, actual_average, rel_tol=1e-9):
        raise ValueError("Validation MAE metadata mismatch")

    # --------------------------------------------------
    # 4. Report header and financial indicators
    # --------------------------------------------------

    lines = [
        "# Combined Farm Credit and Agricultural Research Report",
        "",
        "## FCA Financial Screening — 2026Q3",
        "",
        "| Institution | Nonaccrual / Net Loans |",
        "|---|---:|",
    ]

    for row in financial:

        lines.append(
            f"| {row['institution_name']} | "
            f"{row['nonaccrual_netloans_pct']:.3f}% |"
        )

    lines += [
        "",
        "Source: https://www.fca.gov/bank-oversight/call-report-data-for-download",
        "",
    ]

    # --------------------------------------------------
    # 5. Historical USDA agricultural indicators
    # --------------------------------------------------

    lines += [
        "## USDA Agricultural Indicators — 2025",
        "",
        "| State | Corn Yield (BU/ACRE) |",
        "|---|---:|",
    ]

    for state, value in sorted(
        yields,
        key=lambda item: item[1],
        reverse=True,
    )[:5]:

        lines.append(
            f"| {state} | {value:.2f} |"
        )

    lines += [
        "",
        "Source: https://quickstats.nass.usda.gov/",
        "",
    ]

    # --------------------------------------------------
    # 6. Experimental corn-yield forecasts
    # --------------------------------------------------

    lines += [
        "## Experimental 2026 Corn-Yield Estimates",
        "",
        "| State | Estimated Yield (BU/ACRE) |",
        "|---|---:|",
    ]

    for state, value in sorted(
        forecasts,
        key=lambda item: item[1],
        reverse=True,
    )[:10]:

        lines.append(
            f"| {state} | {value:.2f} |"
        )

    lines += [
        "",
        "**Model:** Two-feature Linear Regression using historical lagged yields.",
        "",
        f"**Development-validation average MAE (2023-2024):** {average_mae:.2f} BU/ACRE.",
        "",
        "**2025 evaluation:** Exploratory; not an untouched final test.",
        "",
        "**Forecast horizon:** 2026, based on historical observations through 2025.",
        "",
        "**Forecast limitations:** These are experimental estimates, "
        "not official USDA forecasts.",
        "",
        "The model does not incorporate weather conditions, commodity "
        "prices, soil characteristics, or institution-level lending exposures.",
        "",
    ]

    # --------------------------------------------------
    # 7. FCA documentary evidence
    # --------------------------------------------------

    lines += [
        "## FCA Document References",
        "",
    ]

    for document in documents:

        title = document.get("title")
        url = document.get("url")
        page = document.get("page")

        if title and url and page is not None:

            lines.append(
                f"- {title}, page {page}: {url}"
            )

    # --------------------------------------------------
    # 8. Interpretation and limitations
    # --------------------------------------------------

    lines += [
        "",
        "## Interpretation and Limitations",
        "",
        "Financial and agricultural indicators come from separate datasets.",
        "",
        "No institution-specific geographic or commodity exposure is inferred.",
        "",
        "The agricultural forecasts are experimental model estimates "
        "and should not be treated as official USDA predictions.",
        "",
        "Nonaccrual ratios and statistical anomaly indicators are "
        "not default probabilities or official credit ratings.",
        "",
        "The historical validation sample is limited, and the "
        "2025 exploratory evaluation is not an untouched final test.",
        "",
        "This is an independent educational research project, "
        "not an official Farm Credit Administration application.",
    ]

    # --------------------------------------------------
    # 9. Write report
    # --------------------------------------------------

    REPORT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    REPORT.write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )

    print(
        f"COMBINED REPORT GENERATED: {REPORT}"
    )


if __name__ == "__main__":
    main()
