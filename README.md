# Pikmykid Onboarding Analytics Toolkit

An interactive Streamlit dashboard for analyzing school onboarding performance
across **Dismissal**, **Hall Pass**, **Reunification**, and **Visitor Management** products.

---

## Quick Start

### 1. Activate the virtual environment

```bash
source venv/bin/activate
```

### 2. Run the dashboard

```bash
streamlit run app.py
```

The app opens at [http://localhost:8501](http://localhost:8501).

---

## Pages

| Page | What It Shows |
|---|---|
| **Portfolio Overview** | Cross-product KPIs, cohort/product donuts, comparison table, seasonality |
| **Product Deep Dive** | Select any product → full interactive analysis (phases, boxplots, scatter, owner analysis) |
| **School Lookup** | Search any school → timeline, milestone dates, benchmark comparison |
| **Benchmarks & SLAs** | SLA thresholds, compliance rates (% Healthy/Caution/Critical), trends over time |
| **Churn Analysis** | At-Risk/Cancelled deep dive — pre vs post-graduation churn, leading indicators |
| **Data Quality** | Missing values heatmaps, negative durations, outliers, per-column detail |

---

## Updating Data

1. Get updated Excel exports from the Pikmykid CRM
2. Replace the files in `data/` (keep the same filenames):
   - `Dismissal Onboarding Time Data.xlsx`
   - `Hall Pass Onboarding Time Data.xlsx`
   - `Reunification Onboarding Time Data.xlsx`
   - `Visitor Management Onboarding Time Data.xlsx`
3. Refresh the browser — the dashboard reloads automatically

The Excel files must have the same sheet structure (Onboarding, Retention, At Risk, Cancelled cohort tabs).

---

## Data Notes

- **969 schools** total across 4 products
- **Dismissal** does not have an Owner column — owner analysis is excluded for Dismissal
- **Reunification** has no Training phase — it goes Contract → Kick Off → Launch → Post Launch
- **Visitor Management** has naming errors in some sheets (columns say "Hall Pass" instead of "Visitor Management") — the loader handles this automatically
- Phase durations with **negative values** (data entry errors) and **>365 days** (outliers) are excluded from analysis but tracked in the Data Quality page

---

## Benchmarks

| Phase | 🟢 Healthy | 🟡 Caution | 🔴 Critical |
|---|---|---|---|
| Contract → Kick Off | ≤ 14 days | 15–30 days | > 30 days |
| Kick Off → Training | ≤ 7 days | 8–21 days | > 21 days |
| Training → Launch | ≤ 14 days | 15–30 days | > 30 days |
| Kick Off → Launch (E2E) | ≤ 42 days | 43–70 days | > 70 days |
| Launch → Post Launch | ≤ 30 days | 31–60 days | > 60 days |

These thresholds are configurable in `utils/benchmarks.py`.

---

## Project Structure

```
onboarding_toolkit/
├── app.py                    # Main entry point
├── pages/
│   ├── 1_portfolio_overview.py
│   ├── 2_product_deep_dive.py
│   ├── 3_school_lookup.py
│   ├── 4_benchmarks.py
│   ├── 5_churn_analysis.py
│   └── 6_data_quality.py
├── utils/
│   ├── data_loader.py        # Unified data loading + cleaning
│   ├── benchmarks.py         # SLA threshold definitions
│   └── charts.py             # Plotly chart builders
├── data/                     # Excel data files (drop replacements here)
├── .streamlit/config.toml    # Theme configuration
├── requirements.txt
├── venv/                     # Python virtual environment
└── README.md
```

---

## Tech Stack

- **Python 3.13** + **Streamlit 1.59**
- **Plotly** for interactive charts
- **Pandas** for data processing
- **openpyxl** for Excel reading

---

*Built by Fatema | Pikmykid Internship — July 2026*
