"""
Pikmykid Onboarding Analytics Toolkit
Main entry point — configures the app and sidebar.
"""

import streamlit as st

st.set_page_config(
    page_title="Pikmykid Onboarding Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Landing page ──
st.title("📊 Pikmykid Onboarding Analytics Toolkit")
st.markdown(
    """
    Welcome to the **Onboarding Analytics Toolkit** — a unified, interactive dashboard
    for analyzing school onboarding performance across all four Pikmykid products.

    ### How to Use
    Use the **sidebar** to navigate between pages:

    | Page | What It Shows |
    |---|---|
    | **Portfolio Overview** | Cross-product KPIs, portfolio health, seasonality |
    | **Product Deep Dive** | Per-product analysis with interactive charts |
    | **School Lookup** | Search any school — see its timeline and benchmark comparison |
    | **Benchmarks & SLAs** | Performance thresholds, compliance rates, trends |
    | **Churn Analysis** | At-Risk and Cancelled deep dive |
    | **Data Quality** | Missing values, outliers, and negative durations audit |

    ### Data
    The dashboard reads from **4 Excel files** in the `data/` folder.
    To update, simply replace the files and refresh the page.

    ---
    *Built by Fatema | Pikmykid Internship — July 2026*
    """
)
