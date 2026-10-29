# Accessibility

SemDriftBD's user-facing parts are its two Streamlit dashboards (`src/dashboard.py` and `src/live_dashboard.py`) and this documentation.

## What we aim for

- Every result shown in a chart is also available as a table or CSV in `data/`, so it can be read with a screen reader or other tools.
- Alerts are labelled in text, not shown by colour alone.
- Documentation uses plain language, headings and tables that screen readers can navigate.

## Supported environments

- The dashboards run in any modern browser (Chrome, Firefox, Safari, Edge) at `localhost:8501` and `localhost:8502`.
- Streamlit and Plotly provide the keyboard navigation and screen-reader support; we have not run a formal accessibility audit.

## Known limitations

- Plotly charts are only partly readable by screen readers. Use the CSV files in `data/` for the underlying numbers.
- Some chart colours may be hard to tell apart for people with colour-vision deficiencies.
- The live dashboard refreshes automatically, which can interrupt screen-reader reading.

## Reporting a barrier

If something in the dashboards or docs is hard to use, open an issue with the **Bug report** template and describe what you tried and what assistive technology you use.
