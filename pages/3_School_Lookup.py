"""
Page 3: School Lookup
Search for any school and see its full onboarding journey + benchmark comparison.
"""

import streamlit as st
import pandas as pd
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.data_loader import load_all_data, get_date_columns, PHASES
from utils.benchmarks import BENCHMARKS, classify_phase, get_benchmark_emoji
from utils.charts import school_timeline

st.set_page_config(page_title="School Lookup", page_icon="🔎", layout="wide")
st.title("🔎 School Lookup")

df = load_all_data()
if df.empty:
    st.error("No data loaded."); st.stop()

# ── Search ──
school_names = sorted(df["Name"].dropna().unique())
selected = st.selectbox("Search for a school", school_names, index=None,
                        placeholder="Start typing a school name…")

if selected is None:
    st.info("Select a school from the dropdown above to view its onboarding journey.")
    st.stop()

# ── Get school data (may appear in multiple products) ──
school_rows = df[df["Name"] == selected]

if len(school_rows) == 0:
    st.warning("School not found."); st.stop()

# If the school appears in multiple products, let user select
if school_rows["Product"].nunique() > 1:
    product = st.selectbox("This school has data for multiple products — select one:",
                           school_rows["Product"].unique())
    school_rows = school_rows[school_rows["Product"] == product]

row = school_rows.iloc[0]

# ── School Info Card ──
st.subheader(f"📋 {row['Name']}")

info_cols = st.columns(3)
info_cols[0].markdown(f"""
**External ID:** {row.get('External ID', '—')}
**Product:** {row.get('Product', '—')}
""")
info_cols[1].markdown(f"""
**Cohort:** {row.get('Cohort', '—')}
**Onboarding Stage:** {row.get('Onboarding Stage', '—')}
""")
info_cols[2].markdown(f"""
**Account Manager:** {row.get('Owner', 'Not available')}
**School Status:** {row.get('School Status (CS)', '—')}
""")

st.divider()

# ── Timeline Visualization ──
st.subheader("📅 Onboarding Timeline")
st.plotly_chart(school_timeline(row), use_container_width=True)

# ── Milestone Dates Table ──
date_cols = get_date_columns()
date_data = []
for col in date_cols:
    if col in row.index and pd.notna(row[col]):
        date_data.append({"Milestone": col, "Date": pd.Timestamp(row[col]).strftime("%b %d, %Y")})
    else:
        date_data.append({"Milestone": col, "Date": "⚠️ Missing"})

st.dataframe(pd.DataFrame(date_data), use_container_width=True, hide_index=True)

st.divider()

# ── Benchmark Comparison ──
st.subheader("📊 Benchmark Comparison")
st.caption("How this school's phase durations compare to SLA thresholds")

bench_data = []
for phase_name, start_col, end_col in PHASES:
    if phase_name in row.index and pd.notna(row[phase_name]):
        days = row[phase_name]
        classification = classify_phase(phase_name, days)
        emoji = get_benchmark_emoji(classification)
        bench = BENCHMARKS.get(phase_name, {})
        healthy = bench.get("healthy", "—")
        caution = bench.get("caution", "—")

        bench_data.append({
            "Phase": phase_name,
            "This School": f"{days:.0f} days",
            "Status": f"{emoji} {classification}",
            "Healthy (≤)": f"{healthy}d" if healthy != "—" else "—",
            "Caution (≤)": f"{caution}d" if caution != "—" else "—",
        })

if bench_data:
    st.dataframe(pd.DataFrame(bench_data), use_container_width=True, hide_index=True)
else:
    st.info("No phase duration data available for benchmark comparison.")

st.divider()

# ── Similar Schools ──
st.subheader("🔗 Similar Schools")
st.caption(f"Schools in the same product ({row['Product']}) and cohort ({row['Cohort']})")

same = df[(df["Product"] == row["Product"]) & (df["Cohort"] == row["Cohort"]) & (df["Name"] != selected)]

if len(same) > 0:
    # Show a compact table of similar schools
    display_cols = ["Name", "Onboarding Stage", "Owner"]
    phase_cols_available = [p for p, _, _ in PHASES if p in same.columns and same[p].notna().any()]
    display_cols += phase_cols_available[:3]
    display_cols = [c for c in display_cols if c in same.columns]

    st.dataframe(
        same[display_cols].head(10).reset_index(drop=True),
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info("No other schools found in this product + cohort combination.")
