"""
Page 6: Data Quality Audit
Missing values, negative durations, and outliers across products and cohorts.
"""

import streamlit as st
import pandas as pd
import numpy as np
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.data_loader import load_all_data, get_products, get_cohorts, get_date_columns, PHASES
from utils.charts import missing_values_heatmap

st.set_page_config(page_title="Data Quality", page_icon="🔬", layout="wide")
st.title("🔬 Data Quality Audit")
st.caption("Transparency into data completeness, anomalies, and cleaning applied")

df = load_all_data()
if df.empty:
    st.error("No data loaded."); st.stop()

# We need the RAW data (before cleaning) to report on negatives and outliers
# The loader stores raw values in *_raw columns when it cleans them

date_cols = get_date_columns()
phase_names = [p[0] for p in PHASES]

# ══════════════════════════════════════════════════════════════════
#  OVERALL DATA HEALTH SCORE
# ══════════════════════════════════════════════════════════════════
st.subheader("📊 Overall Data Health Score")

total_cells = 0
valid_cells = 0
for col in date_cols:
    if col in df.columns:
        total_cells += len(df)
        valid_cells += df[col].notna().sum()

health_pct = valid_cells / total_cells * 100 if total_cells > 0 else 0

c1, c2, c3 = st.columns(3)
c1.metric("Total Date Fields", f"{total_cells:,}")
c2.metric("Valid (Non-Null)", f"{valid_cells:,}")
c3.metric("Data Health Score", f"{health_pct:.1f}%")

# Color-coded health bar
if health_pct >= 80:
    st.success(f"🟢 **Good** — {health_pct:.1f}% of date fields are populated")
elif health_pct >= 60:
    st.warning(f"🟡 **Fair** — {health_pct:.1f}% of date fields are populated. Some columns have significant gaps.")
else:
    st.error(f"🔴 **Poor** — {health_pct:.1f}% of date fields are populated. Major data gaps exist.")

st.divider()

# ══════════════════════════════════════════════════════════════════
#  MISSING VALUES BY PRODUCT
# ══════════════════════════════════════════════════════════════════
st.subheader("📋 Missing Values by Product")
st.caption("Percentage of records with data present (higher = better)")

product_completeness = []
for product in get_products():
    sub = df[df["Product"] == product]
    n = len(sub)
    if n == 0:
        continue
    row = {"Product": product, "Schools": n}
    for col in date_cols:
        if col in sub.columns:
            pct = (1 - sub[col].isna().sum() / n) * 100
            row[col] = round(pct, 1)
        else:
            row[col] = 0.0
    product_completeness.append(row)

pc_df = pd.DataFrame(product_completeness).set_index("Product")

# Display as styled table with color coding
schools_col = pc_df[["Schools"]]
pct_cols = pc_df.drop(columns=["Schools"])

st.plotly_chart(
    missing_values_heatmap(pct_cols, "Data Completeness by Product (% Present)"),
    use_container_width=True,
)

st.divider()

# ══════════════════════════════════════════════════════════════════
#  MISSING VALUES BY COHORT
# ══════════════════════════════════════════════════════════════════
st.subheader("📋 Missing Values by Product × Cohort")
st.caption("Drill down to see which cohorts have the worst data gaps")

selected_product = st.selectbox("Select Product", get_products(), key="dq_product")

cohort_completeness = []
sub_p = df[df["Product"] == selected_product]
for cohort in get_cohorts():
    sub = sub_p[sub_p["Cohort"] == cohort]
    n = len(sub)
    if n == 0:
        continue
    row = {"Cohort": cohort, "Schools": n}
    for col in date_cols:
        if col in sub.columns:
            present = sub[col].notna().sum()
            row[f"{col} — Present"] = present
            row[f"{col} — Missing"] = n - present
            row[f"{col} — % Present"] = round(present / n * 100, 1)
        else:
            row[f"{col} — Present"] = 0
            row[f"{col} — Missing"] = n
            row[f"{col} — % Present"] = 0.0
    cohort_completeness.append(row)

if cohort_completeness:
    cc_df = pd.DataFrame(cohort_completeness)
    # Show the percentage view
    pct_view = cc_df[["Cohort", "Schools"] + [c for c in cc_df.columns if "% Present" in c]]
    pct_view.columns = [c.replace(" — % Present", "") for c in pct_view.columns]
    heatmap_df = pct_view.set_index("Cohort").drop(columns=["Schools"])
    st.plotly_chart(
        missing_values_heatmap(heatmap_df, f"{selected_product} — Completeness by Cohort"),
        use_container_width=True,
    )

st.divider()

# ══════════════════════════════════════════════════════════════════
#  NEGATIVE DURATIONS
# ══════════════════════════════════════════════════════════════════
st.subheader("⚠️ Negative Durations")
st.caption(
    "Negative phase durations mean milestone dates were recorded out of order "
    "(e.g., Launch Date before Kick Off Date). These are excluded from all analysis."
)

neg_data = []
for product in get_products():
    sub = df[df["Product"] == product]
    for phase in phase_names:
        raw_col = f"{phase}_raw"
        if raw_col in sub.columns:
            neg_count = (sub[raw_col] < 0).sum()
        else:
            neg_count = 0
        if neg_count > 0:
            neg_data.append({
                "Product": product,
                "Phase": phase,
                "Negative Count": neg_count,
                "% of Product": f"{neg_count / len(sub) * 100:.1f}%",
            })

if neg_data:
    st.dataframe(pd.DataFrame(neg_data), use_container_width=True, hide_index=True)
else:
    st.success("✅ No negative durations found in the dataset.")

st.divider()

# ══════════════════════════════════════════════════════════════════
#  OUTLIERS (> 365 DAYS)
# ══════════════════════════════════════════════════════════════════
st.subheader("📐 Outliers (> 365 Days)")
st.caption(
    "Phase durations exceeding one year are treated as data anomalies and excluded from analysis."
)

outlier_data = []
for product in get_products():
    sub = df[df["Product"] == product]
    for phase in phase_names:
        raw_col = f"{phase}_raw"
        if raw_col in sub.columns:
            outlier_count = (sub[raw_col] > 365).sum()
        else:
            outlier_count = 0
        if outlier_count > 0:
            outlier_data.append({
                "Product": product,
                "Phase": phase,
                "Outlier Count (>365d)": outlier_count,
                "% of Product": f"{outlier_count / len(sub) * 100:.1f}%",
            })

if outlier_data:
    st.dataframe(pd.DataFrame(outlier_data), use_container_width=True, hide_index=True)
else:
    st.success("✅ No extreme outliers (>365 days) found in the dataset.")

st.divider()

# ══════════════════════════════════════════════════════════════════
#  PER-COLUMN DETAIL (Expandable)
# ══════════════════════════════════════════════════════════════════
st.subheader("📊 Per-Column Detail")
st.caption("Expandable detail for each product")

for product in get_products():
    with st.expander(f"📁 {product}", expanded=False):
        sub = df[df["Product"] == product]
        n = len(sub)

        detail_rows = []
        for col in date_cols:
            if col in sub.columns:
                present = sub[col].notna().sum()
                missing = n - present
                pct_missing = missing / n * 100 if n > 0 else 0
                detail_rows.append({
                    "Column": col,
                    "Total Records": n,
                    "Present": present,
                    "Missing": missing,
                    "% Missing": f"{pct_missing:.1f}%",
                })

        for phase in phase_names:
            if phase in sub.columns:
                valid = sub[phase].notna().sum()
                raw_col = f"{phase}_raw"
                neg = int((sub[raw_col] < 0).sum()) if raw_col in sub.columns else 0
                outlier = int((sub[raw_col] > 365).sum()) if raw_col in sub.columns else 0
                detail_rows.append({
                    "Column": f"[Phase] {phase}",
                    "Total Records": n,
                    "Present": valid,
                    "Missing": n - valid,
                    "% Missing": f"{(n - valid) / n * 100:.1f}%",
                    "Negatives": neg,
                    "Outliers (>365d)": outlier,
                })

        st.dataframe(pd.DataFrame(detail_rows), use_container_width=True, hide_index=True)
