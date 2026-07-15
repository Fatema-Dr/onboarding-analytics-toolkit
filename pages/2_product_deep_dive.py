"""
Page 2: Product Deep Dive
Select a product and get the full interactive analysis.
"""

import streamlit as st
import pandas as pd
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.data_loader import load_all_data, get_products, get_cohorts
from utils.charts import (
    cohort_donut, phase_bar, phase_boxplots, stage_funnel,
    ko_launch_scatter, quarterly_launches, owner_workload, owner_performance,
)

st.set_page_config(page_title="Product Deep Dive", page_icon="🔍", layout="wide")
st.title("🔍 Product Deep Dive")

df = load_all_data()
if df.empty:
    st.error("No data loaded."); st.stop()

# ── Sidebar ──
with st.sidebar:
    st.header("Filters")
    product = st.selectbox("Select Product", get_products())
    selected_cohorts = st.multiselect("Cohorts", get_cohorts(), default=get_cohorts())

    product_df = df[(df["Product"] == product) & (df["Cohort"].isin(selected_cohorts))]

    # Owner filter (only if owner data exists)
    has_owner = "Owner" in product_df.columns and product_df["Owner"].notna().any()
    if has_owner:
        owners = sorted(product_df["Owner"].dropna().unique())
        selected_owners = st.multiselect("Owners", owners, default=owners)
        product_df = product_df[product_df["Owner"].isin(selected_owners)]

    # Year filter
    years = sorted(product_df["Year Signed"].dropna().unique())
    years = [int(y) for y in years if y > 2000]
    if years:
        year_range = st.slider("Year Signed", min(years), max(years), (min(years), max(years)))
        product_df = product_df[
            (product_df["Year Signed"] >= year_range[0]) &
            (product_df["Year Signed"] <= year_range[1])
        ]

filtered = product_df
st.caption(f"Showing **{len(filtered)}** schools for **{product}**")

# ── Determine available phases ──
if product == "Reunification":
    phases = ["Contract → Kick Off", "Kick Off → Launch", "Launch → Post Launch"]
    detail_phases = ["Contract → Kick Off", "Kick Off → Launch", "Launch → Post Launch"]
elif product == "Dismissal":
    phases = ["Contract → Kick Off", "Kick Off → Training", "Training → Launch", "Launch → Post Launch"]
    detail_phases = phases
else:
    phases = ["Contract → Kick Off", "Kick Off → Training", "Training → Launch", "Launch → Post Launch"]
    detail_phases = phases

# ── KPI Cards ──
total = len(filtered)
if total > 0:
    ontrack = len(filtered[filtered["Cohort"].isin(["Onboarding", "Retention"])])
    churn = len(filtered[filtered["Cohort"].isin(["At Risk", "Cancelled"])])
    med_e2e = filtered["Kick Off → Launch"].median()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Schools", total)
    c2.metric("On-Track", f"{ontrack} ({ontrack/total*100:.0f}%)")
    c3.metric("Churn-Threat", f"{churn} ({churn/total*100:.0f}%)")
    c4.metric("Median KO→Launch", f"{med_e2e:.0f}d" if pd.notna(med_e2e) else "—")

st.divider()

# ── Cohort Distribution ──
col1, col2 = st.columns(2)
with col1:
    st.plotly_chart(
        cohort_donut(filtered, f"{product} — Cohort Distribution"),
        use_container_width=True,
    )
with col2:
    st.plotly_chart(
        stage_funnel(filtered, f"{product} — Stage Distribution"),
        use_container_width=True,
    )

st.divider()

# ── Phase Durations ──
st.subheader("⏱ Phase Duration Analysis")

st.plotly_chart(
    phase_bar(filtered, phases, f"{product} — Median Phase Durations"),
    use_container_width=True,
)

# Boxplots in expandable section
with st.expander("📊 Phase Duration Distributions (boxplots)", expanded=False):
    box_cols = st.columns(2)
    for i, phase in enumerate(detail_phases):
        with box_cols[i % 2]:
            if phase in filtered.columns and filtered[phase].notna().any():
                st.plotly_chart(phase_boxplots(filtered, phase), use_container_width=True)

st.divider()

# ── Early Engagement Scatter ──
st.subheader("🎯 Early Engagement vs Deployment Speed")
st.plotly_chart(
    ko_launch_scatter(filtered, f"{product} — Contract→KO vs KO→Launch"),
    use_container_width=True,
)

st.divider()

# ── Quarterly Launches ──
st.subheader("📅 Launch Volume by Quarter")
st.plotly_chart(
    quarterly_launches(filtered, f"{product} — Launches by Quarter"),
    use_container_width=True,
)

st.divider()

# ── Owner Analysis ──
if has_owner:
    st.subheader("👤 Owner / CSM Analysis")
    col_o1, col_o2 = st.columns(2)
    with col_o1:
        st.plotly_chart(owner_workload(filtered), use_container_width=True)
    with col_o2:
        st.plotly_chart(owner_performance(filtered), use_container_width=True)
else:
    st.info(f"ℹ️ Owner data is not available for {product}. Owner analysis is only shown for Hall Pass, Reunification, and Visitor Management.")
