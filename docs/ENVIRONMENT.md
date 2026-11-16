
# Python Environment and Dependencies

## Verified Development Environment

- Operating system: Ubuntu under Windows Subsystem for Linux (WSL)
- Python: 3.13.18
- Java: OpenJDK 17 for Spark
- Streamlit: 1.67.0
- Plotly: 6.9.0
- pandas: 2.3.3
- NumPy: 2.5.5
- scikit-learn: 1.9.1
- MLflow: 3.18.0
- PySpark: 4.0.1
- Delta Lake Python package: 4.0.1
- pytest: 9.2.0

## Dependency Files

`requirements-dashboard.txt` contains pinned versions of
the primary dashboard and forecasting dependencies.

`requirements-dashboard-lock.txt` records the full installed
Python package environment at the time of validation.

The full snapshot is a reproducibility reference, not a
guarantee of identical behavior across operating systems.

## Create the Python Environment

Install a compatible Python 3.13 interpreter and uv.

From the master repository:

```bash
uv venv .venv-usda --python 3.13
uv pip install --python .venv-usda/bin/python -r requirements-dashboard-lock.txt
```

Verify installed packages:

```bash
uv pip check --python .venv-usda/bin/python
```

## Local Data Configuration

Copy `.env.example` to `.env` and configure the local
financial database and document repository paths.

The `.env` file is excluded from version control.

## External Component Dependencies

The autonomous research agent uses a separate Python
environment and may require Ollama and Databricks credentials.

Spark workflows require a compatible Java installation.

See the corresponding component repositories for complete
component-specific setup instructions.

## Reproduction Limitations

Cloning the repository does not automatically provide all
FCA financial datasets, USDA input files, document indexes,
MLflow experiments, or generated forecast artifacts.

Those resources must be prepared through the appropriate
component workflows.
```

Save the document with **Ctrl+S** and close Notepad.

## Step 226: Check formatting and Git status

Normalize Windows line endings:

```bash
python3 -c 'from pathlib import Path; p=Path("docs/ENVIRONMENT.md"); p.write_bytes(p.read_bytes().replace(b"\r\n", b"\n"))'
```

Then run:

```bash
git status --short
git diff --check
```

Stage the three files:

```bash
git add requirements-dashboard.txt
git add requirements-dashboard-lock.txt
git add docs/ENVIRONMENT.md
```

Check the staged changes:

```bash
git diff --cached --stat
git diff --cached --check
```

Make sure the lock snapshot contains only package specifications and no embedded credentials or private package URLs before publishing it.

## Step 227: Commit the dependency documentation

```bash
git commit -m "Document reproducible dashboard and forecasting dependencies"
git push origin main
```

Verify:

```bash
git status --short
git log -1 --oneline
```

## What this adds to your FCA Data Scientist portfolio

Your repository will now demonstrate not only the analytical implementation but also environment documentation, dependency management, and reproducibility controls.

One distinction is worth preserving: **the dependency snapshot documents the working environment, but a fresh installation still needs to be tested independently** before claiming that the entire platform is reproducible from a clean machine.

After this commit, the next step is a final technical portfolio review, including the quality of the README, reproducibility, architecture, test coverage, and alignment with the FCA Data Scientist position.

**Next:** Complete Steps 224–227 and share the Git commit output.