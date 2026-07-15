"""
Data Loader — reads all 4 product Excel files and returns a unified DataFrame.

Handles:
  - Different column names across products (normalizes to unified schema)
  - Cohort sheet name quirks (AtRisk vs At Risk)
  - VM naming errors (Hall Pass columns in VM sheets)
  - Computed phase durations with cleaning (negatives → NaN, >365 → NaN)
"""

import pandas as pd
import numpy as np
import streamlit as st
import os

# ─── Configuration ────────────────────────────────────────────────
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

PRODUCTS = {
    "Dismissal": {
        "file": "Dismissal Onboarding Time Data.xlsx",
        "cohort_sheets": {
            "Onboarding": "Onboarding",
            "Retention": "Retention",
            "At Risk": "At Risk",
            "Cancelled": "Cancelled",
        },
        "column_map": {
            "Contract Start Date (SF)": "Contract Date",
            "Kick Off Call Date": "Kick Off Date",
            "Dismissal Student Journey Training Date": "Training Date",
            "Dismissal Launch Date": "Launch Date",
            "Post Launch Session Date": "Post Launch Date",
            "Dismissal Portal Set Up Call Date": "Portal Setup Date",
            "Dismissal PreLaunch Call Date": "PreLaunch Call Date",
        },
    },
    "Hall Pass": {
        "file": "Hall Pass Onboarding Time Data.xlsx",
        "cohort_sheets": {
            "Onboarding": "Onboarding",
            "Retention": "Retention",
            "At Risk": "At Risk",
            "Cancelled": "Cancelled",
        },
        "column_map": {
            "Contract Start Date (SF)": "Contract Date",
            "Kick Off Call Date": "Kick Off Date",
            "Hall Pass Training Session": "Training Date",
            "Hall Pass Launch Date": "Launch Date",
            "Post Launch Session Date": "Post Launch Date",
        },
    },
    "Reunification": {
        "file": "Reunification Onboarding Time Data.xlsx",
        "cohort_sheets": {
            "Onboarding": "Onboarding",
            "Retention": "Retention",
            "At Risk": "AtRisk",  # quirk: no space
            "Cancelled": "Cancelled",
        },
        "column_map": {
            "Contract Start Date (SF)": "Contract Date",
            "Kick Off Call Date": "Kick Off Date",
            # No training date for Reunification
            "Reunification Launch Date": "Launch Date",
            "Post Launch Session Date": "Post Launch Date",
        },
    },
    "Visitor Management": {
        "file": "Visitor Management Onboarding Time Data.xlsx",
        "cohort_sheets": {
            "Onboarding": "Onboarding",
            "Retention": "Retention",
            "At Risk": "At Risk",
            "Cancelled": "Cancelled",
        },
        "column_map": {
            "Contract Start Date (SF)": "Contract Date",
            "Kick Off Call Date": "Kick Off Date",
            "Visitor Management Training Session": "Training Date",
            "Visitor Management Launch Date": "Launch Date",
            "Post Launch Session Date": "Post Launch Date",
        },
    },
}

# Unified date columns (in pipeline order)
DATE_COLS = [
    "Contract Date", 
    "Kick Off Date", 
    "Portal Setup Date", 
    "Training Date", 
    "PreLaunch Call Date", 
    "Launch Date", 
    "Post Launch Date"
]

# Phase definitions (from → to)
PHASES = [
    ("Contract → Kick Off", "Contract Date", "Kick Off Date"),
    ("Kick Off → Training", "Kick Off Date", "Training Date"),
    ("Training → Launch", "Training Date", "Launch Date"),
    ("Kick Off → Launch", "Kick Off Date", "Launch Date"),
    ("Launch → Post Launch", "Launch Date", "Post Launch Date"),
]

# Identity / metadata columns to keep
KEEP_COLS = [
    "External ID", "Name", "Onboarding Stage", "School Status (CS)",
    "Tags", "Owner", "Product", "Cohort",
    "Quarter Signed", "Year Signed", "Quarter Launch", "Year Launch",
]


# ─── Loader ───────────────────────────────────────────────────────

@st.cache_data(ttl=3600, show_spinner="Loading onboarding data…")
def load_all_data() -> pd.DataFrame:
    """Load and unify all 4 product datasets into a single DataFrame."""
    frames = []

    for product_name, config in PRODUCTS.items():
        filepath = os.path.join(DATA_DIR, config["file"])
        if not os.path.exists(filepath):
            st.warning(f"⚠ Data file not found: {config['file']}")
            continue

        xls = pd.ExcelFile(filepath)

        for cohort_label, sheet_name in config["cohort_sheets"].items():
            if sheet_name not in xls.sheet_names:
                continue

            df = pd.read_excel(xls, sheet_name=sheet_name)

            # Normalize column names using product-specific map
            rename_map = {}
            for orig_col, unified_col in config["column_map"].items():
                if orig_col in df.columns:
                    rename_map[orig_col] = unified_col
            df = df.rename(columns=rename_map)

            # Add product & cohort identifiers
            df["Product"] = product_name
            df["Cohort"] = cohort_label

            frames.append(df)

    if not frames:
        return pd.DataFrame()

    master = pd.concat(frames, ignore_index=True)

    # ── Parse dates ──
    for col in DATE_COLS:
        if col in master.columns:
            master[col] = pd.to_datetime(master[col], errors="coerce")

    # Also parse Start Date if present
    if "Start Date" in master.columns:
        master["Start Date"] = pd.to_datetime(master["Start Date"], errors="coerce")

    # ── Compute phase durations (days) ──
    for phase_name, start_col, end_col in PHASES:
        if start_col in master.columns and end_col in master.columns:
            master[phase_name] = (master[end_col] - master[start_col]).dt.days
        else:
            master[phase_name] = np.nan

    # ── Data cleaning ──
    phase_cols = [p[0] for p in PHASES]
    for col in phase_cols:
        if col in master.columns:
            # Negative durations → NaN (data-entry errors)
            master.loc[master[col] < 0, f"{col}_raw"] = master.loc[master[col] < 0, col]
            master.loc[master[col] < 0, col] = np.nan
            # Extreme outliers (>365 days) → NaN
            master.loc[master[col] > 365, f"{col}_raw"] = master.loc[master[col] > 365, col]
            master.loc[master[col] > 365, col] = np.nan

    # ── Extract stage number ──
    if "Onboarding Stage" in master.columns:
        master["Stage Number"] = (
            master["Onboarding Stage"]
            .astype(str)
            .str.extract(r"^(\d)")
            .astype(float)
        )

    # ── Compute signing quarter/year if not present ──
    if "Contract Date" in master.columns:
        if "Year Signed" not in master.columns:
            master["Year Signed"] = master["Contract Date"].dt.year
        else:
            master["Year Signed"] = master["Year Signed"].fillna(master["Contract Date"].dt.year)
            
        if "Quarter Signed" not in master.columns:
            master["Quarter Signed"] = master["Contract Date"].dt.quarter
        else:
            master["Quarter Signed"] = master["Quarter Signed"].fillna(master["Contract Date"].dt.quarter)

    # ── Compute launch quarter/year ──
    if "Launch Date" in master.columns:
        master["Launch Year"] = master["Launch Date"].dt.year
        master["Launch Quarter"] = master["Launch Date"].dt.quarter
        master["Launch QY"] = master.apply(
            lambda r: f"Q{int(r['Launch Quarter'])} {int(r['Launch Year'])}"
            if pd.notna(r["Launch Quarter"]) and pd.notna(r["Launch Year"])
            else None,
            axis=1,
        )

    return master


def get_phase_columns() -> list[str]:
    """Return the list of computed phase duration column names."""
    return [p[0] for p in PHASES]


def get_date_columns() -> list[str]:
    """Return the ordered list of unified date column names."""
    return DATE_COLS.copy()


def get_products() -> list[str]:
    """Return list of product names."""
    return list(PRODUCTS.keys())


def get_cohorts() -> list[str]:
    """Return the standard cohort order."""
    return ["Onboarding", "Retention", "At Risk", "Cancelled"]


def get_expected_date_columns(product: str) -> list[str]:
    """Return the list of expected date columns for a specific product."""
    if product not in PRODUCTS:
        return []
    expected = []
    for unified_col in PRODUCTS[product]["column_map"].values():
        if unified_col in DATE_COLS and unified_col not in expected:
            expected.append(unified_col)
    
    # Sort them in pipeline order
    return [col for col in DATE_COLS if col in expected]
