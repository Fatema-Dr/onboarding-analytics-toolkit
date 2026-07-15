"""
Page 5: Churn Analysis
Deep dive into At-Risk and Cancelled schools.
"""

import streamlit as st
import pandas as pd
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.data_loader import load_all_data, get_products, get_cohorts
from utils.charts import (
    churn_donut, churn_by_stage, cancellation_substatus,
    cohort_donut, phase_bar,
)

st.set_page_config(page_title="Churn Analysis", page_icon="⚠️", layout="wide")
st.title("⚠️ Churn Analysis")

df = load_all_data()
if df.empty:
    st.error("No data loaded."); st.stop()

# ── Sidebar ──
with st.sidebar:
    st.header("Filters")
    selected_products = st.multiselect("Products", get_products(), default=get_products())
    filtered = df[df["Product"].isin(selected_products)]

# ── Churn KPIs ──
total = len(filtered)
at_risk = len(filtered[filtered["Cohort"] == "At Risk"])
cancelled = len(filtered[filtered["Cohort"] == "Cancelled"])
churn_total = at_risk + cancelled
churn_rate = churn_total / total * 100 if total > 0 else 0

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total At Risk", at_risk)
c2.metric("Total Cancelled", cancelled)
c3.metric("Combined Churn-Threat", churn_total)
c4.metric("Churn-Threat Rate", f"{churn_rate:.1f}%")

st.divider()

# ── Churn Timing & Stage ──
col1, col2 = st.columns(2)
with col1:
    st.plotly_chart(
        churn_donut(filtered, "When Do Schools Churn?"),
        use_container_width=True,
    )
with col2:
    st.plotly_chart(
        churn_by_stage(filtered, "Churn by Onboarding Stage"),
        use_container_width=True,
    )

st.divider()

# ── Cancellation Sub-Status ──
st.subheader("📋 Cancellation Sub-Status Breakdown")
st.plotly_chart(
    cancellation_substatus(filtered),
    use_container_width=True,
)

st.divider()

# ── Churn Timing by Product ──
st.subheader("🔄 Churn Timing by Product")
st.caption("Pre-completion vs post-graduation churn for each product")

product_cols = st.columns(len(selected_products))
for i, product in enumerate(selected_products):
    with product_cols[i]:
        sub = filtered[filtered["Product"] == product]
        st.plotly_chart(
            churn_donut(sub, product),
            use_container_width=True,
        )

st.divider()

# ── Leading Indicators ──
st.subheader("📊 Leading Indicators — At Risk vs Healthy")
st.caption("How do At-Risk school metrics compare to On-Track schools?")

phases = ["Contract → Kick Off", "Kick Off → Launch", "Launch → Post Launch"]

indicator_data = []
for phase in phases:
    if phase not in filtered.columns:
        continue
    ontrack = filtered[filtered["Cohort"].isin(["Onboarding", "Retention"])]
    atrisk = filtered[filtered["Cohort"] == "At Risk"]

    med_ontrack = ontrack[phase].median()
    med_atrisk = atrisk[phase].median()

    ratio = med_atrisk / med_ontrack if pd.notna(med_ontrack) and med_ontrack > 0 and pd.notna(med_atrisk) else None

    indicator_data.append({
        "Phase": phase,
        "On-Track Median": f"{med_ontrack:.0f}d" if pd.notna(med_ontrack) else "—",
        "At-Risk Median": f"{med_atrisk:.0f}d" if pd.notna(med_atrisk) else "—",
        "Ratio (At-Risk ÷ On-Track)": f"{ratio:.1f}×" if ratio is not None else "—",
        "Signal Strength": "🔴 Strong" if ratio and ratio >= 2.0 else ("🟡 Moderate" if ratio and ratio >= 1.5 else "🟢 Weak") if ratio else "—",
    })

if indicator_data:
    st.dataframe(pd.DataFrame(indicator_data), use_container_width=True, hide_index=True)

    st.info("""
    **How to read this table:**
    - **Ratio** shows how many times slower At-Risk schools are compared to On-Track schools
    - A ratio of 2.0× or higher means At-Risk schools take at least double the time — a strong churn signal
    - **Contract → Kick Off** is consistently the strongest leading indicator across all products
    """)
else:
    st.info("No phase data available for leading indicators.")
