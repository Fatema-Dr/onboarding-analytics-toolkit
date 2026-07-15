"""
Page 1: Portfolio Overview
Cross-product executive snapshot with KPIs, donuts, and seasonality.
"""

import streamlit as st
import pandas as pd
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.data_loader import load_all_data, get_phase_columns, get_products, get_cohorts
from utils.charts import cohort_donut, product_donut, phase_bar, quarterly_launches

st.set_page_config(page_title="Portfolio Overview", page_icon="🏠", layout="wide")
st.title("🏠 Portfolio Overview")

# ── Load data ──
df = load_all_data()

if df.empty:
    st.error("No data loaded. Check that Excel files are in the `data/` folder.")
    st.stop()

# ── Sidebar filters ──
with st.sidebar:
    st.header("Filters")
    selected_products = st.multiselect(
        "Products", get_products(), default=get_products()
    )
    years = sorted(df["Year Signed"].dropna().unique())
    years = [int(y) for y in years if y > 2000]
    if years:
        year_range = st.slider("Year Signed", min(years), max(years), (min(years), max(years)))
    else:
        year_range = None

# ── Apply filters ──
mask = df["Product"].isin(selected_products)
if year_range:
    mask &= (df["Year Signed"] >= year_range[0]) & (df["Year Signed"] <= year_range[1])
filtered = df[mask]

# ── KPI Cards ──
total = len(filtered)
ontrack = len(filtered[filtered["Cohort"].isin(["Onboarding", "Retention"])])
churn_threat = len(filtered[filtered["Cohort"].isin(["At Risk", "Cancelled"])])
med_ko_launch = filtered["Kick Off → Launch"].median()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Schools", f"{total:,}")
col2.metric("On-Track Rate", f"{ontrack/total*100:.1f}%" if total > 0 else "—",
            help="Onboarding + Retention as % of total")
col3.metric("Churn-Threat Rate", f"{churn_threat/total*100:.1f}%" if total > 0 else "—",
            help="At Risk + Cancelled as % of total")
col4.metric("Median KO → Launch", f"{med_ko_launch:.0f} days" if pd.notna(med_ko_launch) else "—",
            help="Median Kick Off to Launch across all products")

st.divider()

# ── Donut Charts ──
col_left, col_right = st.columns(2)
with col_left:
    st.plotly_chart(product_donut(filtered), use_container_width=True)
with col_right:
    st.plotly_chart(cohort_donut(filtered), use_container_width=True)

st.divider()

# ── Cross-Product Comparison Table ──
st.subheader("📋 Cross-Product Comparison")

comparison_rows = []
for product in get_products():
    sub = filtered[filtered["Product"] == product]
    n = len(sub)
    if n == 0:
        continue
    ontrack_pct = len(sub[sub["Cohort"].isin(["Onboarding", "Retention"])]) / n * 100
    churn_pct = len(sub[sub["Cohort"].isin(["At Risk", "Cancelled"])]) / n * 100
    med_cko = sub["Contract → Kick Off"].median()
    med_kol = sub["Kick Off → Launch"].median()

    # Q3 concentration
    q3 = sub[sub["Launch Quarter"] == 3] if "Launch Quarter" in sub.columns else pd.DataFrame()
    launched = sub.dropna(subset=["Launch Quarter"]) if "Launch Quarter" in sub.columns else pd.DataFrame()
    q3_pct = len(q3) / len(launched) * 100 if len(launched) > 0 else 0

    comparison_rows.append({
        "Product": product,
        "Schools": n,
        "On-Track %": f"{ontrack_pct:.1f}%",
        "Churn-Threat %": f"{churn_pct:.1f}%",
        "Median Contract→KO (days)": f"{med_cko:.0f}" if pd.notna(med_cko) else "—",
        "Median KO→Launch (days)": f"{med_kol:.0f}" if pd.notna(med_kol) else "—",
        "Q3 Launch Concentration": f"{q3_pct:.0f}%",
    })

st.dataframe(pd.DataFrame(comparison_rows), use_container_width=True, hide_index=True)

st.divider()

# ── Phase Duration Comparison ──
st.subheader("⏱ Median Phase Durations by Cohort")
phases = ["Contract → Kick Off", "Kick Off → Launch", "Launch → Post Launch"]
st.plotly_chart(phase_bar(filtered, phases), use_container_width=True)

st.divider()

# ── Seasonality ──
st.subheader("📅 Launch Seasonality")
st.plotly_chart(quarterly_launches(filtered), use_container_width=True)
