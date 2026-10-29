# Contributing to SemDriftBD

Thanks for your interest. Bug reports, reproducibility questions and improvements are all welcome.

## Before you start

- For bugs or questions, open an issue using one of the templates.
- For larger changes (a new drift metric, a new baseline, changes to the pipeline), open an issue first so we can agree on the approach.
- Please follow the [Code of Conduct](CODE_OF_CONDUCT.md).

## Setting up

Follow the **Setup** section of the [README](README.md): Python 3.10+, Java 11+, Docker, then `pip install -r requirements.txt`.

## Making a change

1. Fork the repo and create a branch from `main`, e.g. `fix/kafka-consumer-offsets`.
2. Keep each pull request focused on one change.
3. If your change affects drift scores, say so in the pull request, and include before/after numbers from `src/compute_all_drift.py` and `src/adaptive_threshold.py`. The published results (IEEE SoftCOM 2026) come from this code, so changes to `src/drift.py` and `src/adaptive_threshold.py` need extra care.
4. Do not commit large generated files (embeddings, Parquet, Delta tables, checkpoints). `.gitignore` already excludes them.
5. Open a pull request and fill in the template.

## Code style

- Python, following PEP 8.
- Use clear function and variable names, and add a short docstring to new functions.
- Keep file paths relative to the repo root so scripts work on any machine.

## Reporting results issues

If you cannot reproduce a number from the paper or README, open a bug report and include your environment (`pip freeze`, Spark version, OS) and the exact commands you ran.
