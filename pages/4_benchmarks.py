"""
Page 4: Benchmarks & SLAs
Performance thresholds, compliance rates, and trends over time.
"""

import streamlit as st
import pandas as pd
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.data_loader import load_all_data, get_products, PHASES
from utils.benchmarks import BENCHMARKS, classify_phase, get_benchmark_emoji
from utils.charts import benchmark_compliance_donut, trend_line, product_comparison_bar

st.set_page_config(page_title="Benchmarks & SLAs", page_icon="📏", layout="wide")
st.title("📏 Benchmarks & SLAs")

df = load_all_data()
if df.empty:
    st.error("No data loaded."); st.stop()

# ── Sidebar ──
with st.sidebar:
    st.header("Filters")
    selected_products = st.multiselect("Products", get_products(), default=get_products())
    filtered = df[df["Product"].isin(selected_products)]

# ── Benchmark Reference Table ──
st.subheader("📋 Benchmark Definitions")
st.caption("Thresholds derived from historical onboarding data analysis")

bench_rows = []
for phase, config in BENCHMARKS.items():
    bench_rows.append({
        "Phase": phase,
        "🟢 Healthy": f"≤ {config['healthy']} days",
        "🟡 Caution": f"{config['healthy']+1}–{config['caution']} days",
        "🔴 Critical": f"> {config['caution']} days",
        "Description": config["description"],
    })

st.dataframe(pd.DataFrame(bench_rows), use_container_width=True, hide_index=True)

st.divider()

# ── SLA Compliance Donuts ──
st.subheader("✅ SLA Compliance Rates")
st.caption("What percentage of schools meet each benchmark?")

phases_to_show = [p for p in BENCHMARKS.keys() if p in filtered.columns]

# Display in a 3-column grid
cols_per_row = 3
for i in range(0, len(phases_to_show), cols_per_row):
    cols = st.columns(cols_per_row)
    for j, phase in enumerate(phases_to_show[i:i+cols_per_row]):
        with cols[j]:
            st.plotly_chart(
                benchmark_compliance_donut(filtered, phase, BENCHMARKS),
                use_container_width=True,
            )

st.divider()

# ── Product Comparison ──
st.subheader("🔄 Product Comparison")
st.caption("How does each product compare on the same benchmark?")

comparison_phase = st.selectbox(
    "Select phase to compare",
    phases_to_show,
    index=0,
)

st.plotly_chart(
    product_comparison_bar(filtered, comparison_phase),
    use_container_width=True,
)

st.divider()

# ── Trend Over Time ──
st.subheader("📈 Trend Over Time")
st.caption("Is onboarding getting faster or slower?")

trend_phase = st.selectbox(
    "Select phase for trend analysis",
    phases_to_show,
    index=0,
    key="trend_phase",
)

st.plotly_chart(
    trend_line(filtered, trend_phase),
    use_container_width=True,
)

# ── Per-product trends ──
with st.expander("📊 Per-Product Trends", expanded=False):
    for product in selected_products:
        sub = filtered[filtered["Product"] == product]
        if sub[trend_phase].notna().any():
            st.plotly_chart(
                trend_line(sub, trend_phase, f"{product} — {trend_phase}"),
                use_container_width=True,
            )
