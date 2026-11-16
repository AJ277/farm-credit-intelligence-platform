
import csv
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "scripts/platform.sh"
USDA = ROOT / "components/usda-data-engineering/data/raw/usda_state_crop_clean.csv"


def get_data(*arguments):
    result = subprocess.run(
        [str(LAUNCHER), *arguments],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
        timeout=120,
    )
    return json.loads(result.stdout)


def main():
    financial = get_data("finance", "--limit", "5")
    documents = get_data(
        "documents",
        "Farm Credit System funding conditions",
        "--mode",
        "lexical",
    )

    if len(financial) != 5:
        raise ValueError("Expected five financial records")

    if not USDA.is_file():
        raise FileNotFoundError(f"USDA dataset missing: {USDA}")

    with USDA.open(encoding="utf-8-sig", newline="") as file:
        yields = [
            (r["state_name"], float(r["value"].replace(",", "")))
            for r in csv.DictReader(file)
            if r["year"] == "2025"
            and r["commodity_desc"].upper() == "CORN"
            and r["statisticcat_desc"].upper() == "YIELD"
            and r["unit_desc"].upper().replace(" ", "") == "BU/ACRE"
            and r["state_name"].upper() != "OTHER STATES"
        ]

    if len(yields) < 5:
        raise ValueError("Insufficient USDA yield observations")

    if len({name for name, _ in yields}) != len(yields):
        raise ValueError("Duplicate state observations")

    if not documents:
        raise ValueError("No FCA document evidence retrieved")

    quarters = {row["quarter"] for row in financial}
    if len(quarters) != 1:
        raise ValueError("Financial records span multiple quarters")

    lines = [
        "# Combined Farm Credit and Agricultural Research Report",
        "",
        f"## FCA Financial Screening — {next(iter(quarters))}",
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
        "## USDA Agricultural Indicators — 2025",
        "",
        "| State | Corn Yield (BU/ACRE) |",
        "|---|---:|",
    ]

    for name, value in sorted(yields, key=lambda x: -x[1])[:5]:
        lines.append(f"| {name} | {value:.2f} |")

    lines += [
        "",
        "Source: https://quickstats.nass.usda.gov/",
        "",
        "## FCA Document References",
        "",
    ]

    for doc in documents:
        if doc.get("title") and doc.get("url") and doc.get("page"):
            lines.append(
                f"- {doc['title']}, page {doc['page']}: {doc['url']}"
            )

    lines += [
        "",
        "## Interpretation and Limitations",
        "",
        "Financial and agricultural indicators come from separate datasets.",
        "No institution-specific geographic or commodity exposure is inferred.",
        "Anomaly screening indicators are not default probabilities.",
        "This is an independent educational research project.",
    ]

    output = ROOT / "output/combined_report.md"
    output.parent.mkdir(exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"COMBINED REPORT GENERATED: {output}")


if __name__ == "__main__":
    main()
