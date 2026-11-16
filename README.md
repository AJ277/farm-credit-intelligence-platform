# Farm Credit Intelligence & Analytics Platform

Independent data science and AI engineering portfolio project integrating financial analytics, agricultural data engineering, document intelligence, and autonomous research.

## Platform Components

1. **Financial Risk Analytics:** FCA financial ratios, credit-quality indicators, and unsupervised anomaly screening.
2. **USDA Data Engineering:** PySpark, Spark SQL, Delta Lake, incremental processing, and agricultural analytics.
3. **FCA Document Intelligence:** Hybrid retrieval, local RAG, and citation validation.
4. **Autonomous Research Agent:** LangGraph, Ollama, Databricks SQL, and evidence-validated research reports.

## Technologies

Python, PySpark, Databricks, Delta Lake, SQL, SQLite, scikit-learn, LangGraph, LangChain, Ollama, RAG, pytest.

## Architecture

The four components are maintained as Git submodules. A shared launcher provides access to financial and document research commands. USDA integration and platform-wide tests are being expanded.

## Installation

Clone with submodules:

    git clone --recurse-submodules https://github.com/AJ277/farm-credit-intelligence-platform.git

Configure local data paths and Python environments using config/platform.env.example.

## Current Validation

- Financial SQLite retrieval: verified.
- FCA document retrieval: verified.
- USDA preflight: 252 observations validated.
- USDA automated tests: 8 passed.
- Autonomous agent: 50 tests passed in its separate project.

## Development Roadmap

- Shared cross-component integration tests.
- USDA pipeline commands in the master launcher.
- Agricultural and financial forecasting.
- Unified analytics dashboard.

## Disclaimer

Independent educational portfolio project. Not affiliated with or endorsed by the Farm Credit Administration or USDA. Statistical anomaly flags are not default probabilities or regulatory findings. This platform is not a production regulatory decision system.
