
"""Farm Credit Intelligence Platform — Analytics Dashboard."""

import hashlib
import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st
from dashboard.data import load_forecast_data


ROOT = Path(__file__).resolve().parents[1]

FORECAST_DIR = ROOT / "output" / "forecasting"
FORECAST_CSV = FORECAST_DIR / "corn_yield_2026_experimental.csv"
METADATA_JSON = FORECAST_DIR / "forecast_metadata.json"

USDA_CSV = (
    ROOT
    / "components"
    / "usda-data-engineering"
    / "data"
    / "raw"
    / "usda_state_crop_clean.csv"
)


@st.cache_data
def load_data():
    return load_forecast_data(FORECAST_CSV, METADATA_JSON, USDA_CSV)


st.set_page_config(
    page_title="Farm Credit Intelligence",
    page_icon="🌽",
    layout="wide",
)

st.title("Farm Credit Intelligence & Analytics Platform")
st.caption(
    "Independent research dashboard | "
    "FCA financial analytics and USDA agricultural intelligence"
)

try:
    forecast, historical, metadata = load_data()
except (FileNotFoundError, ValueError, KeyError, json.JSONDecodeError) as error:
    st.error(str(error))
    st.stop()


st.subheader("2026 Experimental Corn-Yield Forecasting")

mae = metadata["development_average_mae"]

col1, col2, col3 = st.columns(3)

col1.metric("Forecast States", len(forecast))
col2.metric("Development MAE", f"{mae:.2f} BU/ACRE")
col3.metric("Forecast Year", metadata["forecast_year"])

st.info(
    "These are experimental machine-learning estimates, "
    "not official USDA forecasts. "
    "Development validation covers 2023–2024; "
    "2025 evaluation was exploratory."
)

selected_states = st.multiselect(
    "Select states",
    options=sorted(forecast["state_name"].unique()),
    default=[state for state in ["IOWA", "ILLINOIS", "NEBRASKA", "INDIANA", "MINNESOTA"] if state in set(forecast["state_name"])],
)

filtered = forecast[
    forecast["state_name"].isin(selected_states)
].copy()

filtered = filtered.sort_values(
    "forecast_2026",
    ascending=False,
)

st.subheader("Forecast Yield by State")

if filtered.empty:
    st.warning("Select at least one state.")
else:
    chart = px.bar(
        filtered,
        x="state_name",
        y="forecast_2026",
        title="Experimental 2026 Corn-Yield Estimates",
        labels={
            "state_name": "State",
            "forecast_2026": "Estimated Bushels per Acre",
        },
    )

    st.plotly_chart(chart, width="stretch")

    st.dataframe(
        filtered,
        width="stretch",
        hide_index=True,
    )


st.subheader("Historical USDA Corn Yields")

history = historical[
    (historical["commodity_desc"].str.upper() == "CORN")
    & (historical["statisticcat_desc"].str.upper() == "YIELD")
    & (
        historical["unit_desc"]
        .str.upper()
        .str.replace(" ", "", regex=False)
        == "BU/ACRE"
    )
    & (historical["state_name"].str.upper() != "OTHER STATES")
].copy()

history["value"] = pd.to_numeric(
    history["value"].astype(str).str.replace(",", "", regex=False),
    errors="coerce",
)

history["year"] = pd.to_numeric(history["year"], errors="coerce")

history = history.dropna(subset=["year", "value"])

historical_selected = history[
    history["state_name"].isin(selected_states)
]

if historical_selected.empty:
    st.warning("No historical observations for the selected states.")
else:
    trend = px.line(
        historical_selected.sort_values("year"),
        x="year",
        y="value",
        color="state_name",
        markers=True,
        title="Historical USDA Corn Yield by State",
        labels={
            "year": "Year",
            "value": "Bushels per Acre",
            "state_name": "State",
        },
    )

    st.plotly_chart(trend, width="stretch")


st.subheader("Model Validation and Data Lineage")

validation = pd.DataFrame.from_dict(
    metadata["validation_metrics"],
    orient="index",
)

validation.index.name = "Validation Year"
st.dataframe(validation, width="stretch")

with st.expander("Reproducibility metadata"):
    st.json(metadata)

st.caption(
    "Financial and agricultural indicators are separate datasets. "
    "This dashboard does not infer institution-specific commodity "
    "exposures or default probabilities."
)


# --------------------------------------------------
# FCA financial and documentary intelligence
# --------------------------------------------------

import subprocess


@st.cache_data(ttl=300)
def load_fca_data():
    """Retrieve validated data from the platform launcher."""

    launcher = ROOT / "scripts" / "platform.sh"

    def run_component(*arguments):
        result = subprocess.run(
            [str(launcher), *arguments],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
            timeout=120,
        )
        return json.loads(result.stdout)

    financial = run_component(
        "finance", "--limit", "5"
    )

    documents = run_component(
        "documents",
        "Farm Credit System funding conditions",
        "--mode",
        "lexical",
    )

    return pd.DataFrame(financial), documents


st.divider()
st.header("FCA Financial Risk Analytics")

try:
    financial_df, documents = load_fca_data()

except (
    subprocess.CalledProcessError,
    subprocess.TimeoutExpired,
    ValueError,
    OSError,
) as error:
    st.error(f"FCA component retrieval failed: {error}")
    st.info(
        "Check FCA_SQLITE_PATH and FCA_DOC_REPO "
        "in the terminal running Streamlit."
    )
    st.stop()

if financial_df.empty:
    st.warning("No FCA financial records available.")
else:
    quarter = financial_df["quarter"].iloc[0]

    st.caption(
        f"Financial reporting period: {quarter}"
    )

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Institutions Screened",
        len(financial_df),
    )

    c2.metric(
        "Highest Nonaccrual Ratio",
        f"{financial_df['nonaccrual_netloans_pct'].max():.3f}%",
    )

    c3.metric(
        "Median Equity / Assets",
        f"{financial_df['equity_assets_pct'].median():.3f}%",
    )

    financial_chart = px.bar(
        financial_df.sort_values(
            "nonaccrual_netloans_pct",
            ascending=False,
        ),
        x="institution_name",
        y="nonaccrual_netloans_pct",
        title="Nonaccrual Loans / Net Loans",
        labels={
            "institution_name": "Farm Credit Institution",
            "nonaccrual_netloans_pct": "Nonaccrual / Net Loans (%)",
        },
    )

    st.plotly_chart(
        financial_chart,
        width="stretch",
    )

    st.subheader("Institution Financial Indicators")

    st.dataframe(
        financial_df,
        width="stretch",
        hide_index=True,
    )

    st.caption(
        "These are screening indicators, not default "
        "probabilities or official FCA institution ratings."
    )


st.divider()
st.header("FCA Document Intelligence")

st.caption(
    "Document excerpts retrieved through the existing "
    "FCA document-search component."
)

if not documents:
    st.warning("No matching FCA documents found.")
else:
    for index, document in enumerate(documents, start=1):
        title = document.get("title", "Untitled FCA Document")
        page = document.get("page", "Unknown")
        score = document.get("score")
        url = document.get("url")
        excerpt = document.get("text", "")

        with st.expander(f"{index}. {title} — Page {page}"):
            if score is not None:
                st.write(
                    f"Lexical relevance score: {float(score):.4f}"
                )

            st.write(excerpt)

            if url and str(url).startswith(
                ("https://", "http://")
            ):
                st.link_button(
                    "Open FCA Source Document",
                    url,
                )

st.caption(
    "Document retrieval scores indicate search relevance; "
    "they do not establish the correctness of a claim."
)

