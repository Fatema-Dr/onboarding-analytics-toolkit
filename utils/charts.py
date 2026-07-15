"""
Chart Library — all Plotly chart builder functions for the dashboard.

Each function takes a filtered DataFrame and returns a plotly Figure.
"""

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

# ─── Color Palette ────────────────────────────────────────────────
COHORT_COLORS = {
    "Onboarding": "#4361EE",
    "Retention": "#2A9D8F",
    "At Risk": "#E9C46A",
    "Cancelled": "#E76F51",
}

PRODUCT_COLORS = {
    "Dismissal": "#4361EE",
    "Hall Pass": "#7209B7",
    "Reunification": "#2A9D8F",
    "Visitor Management": "#F77F00",
}

BENCHMARK_COLORS = {
    "Healthy": "#2A9D8F",
    "Caution": "#E9C46A",
    "Critical": "#E76F51",
}

COHORT_ORDER = ["Onboarding", "Retention", "At Risk", "Cancelled"]
PRODUCT_ORDER = ["Dismissal", "Hall Pass", "Reunification", "Visitor Management"]

_LAYOUT_DEFAULTS = dict(
    paper_bgcolor="white",
    plot_bgcolor="#F7F9FC",
    font=dict(family="Segoe UI, DejaVu Sans, sans-serif", color="#1A1A2E"),
    margin=dict(l=40, r=40, t=60, b=40),
    legend=dict(bgcolor="rgba(247,249,252,0.8)", bordercolor="#D0D8E4", borderwidth=1),
)


def _apply_layout(fig, **kwargs):
    """Apply default layout settings to a figure."""
    fig.update_layout(**{**_LAYOUT_DEFAULTS, **kwargs})
    fig.update_xaxes(gridcolor="#E8ECF1", gridwidth=1)
    fig.update_yaxes(gridcolor="#E8ECF1", gridwidth=1)
    return fig


# ═══════════════════════════════════════════════════════════════════
#  DONUT CHARTS
# ═══════════════════════════════════════════════════════════════════

def cohort_donut(df: pd.DataFrame, title: str = "Portfolio Health by Cohort") -> go.Figure:
    """Donut chart showing cohort distribution."""
    counts = df["Cohort"].value_counts().reindex(COHORT_ORDER, fill_value=0)
    fig = go.Figure(go.Pie(
        labels=counts.index,
        values=counts.values,
        hole=0.5,
        marker=dict(colors=[COHORT_COLORS[c] for c in counts.index],
                    line=dict(color="white", width=2)),
        textinfo="label+percent",
        textposition="outside",
        textfont=dict(size=12),
        hovertemplate="<b>%{label}</b><br>%{value} schools (%{percent})<extra></extra>",
    ))
    total = counts.sum()
    fig.add_annotation(text=f"<b>{total}</b><br>schools", x=0.5, y=0.5,
                       font=dict(size=18, color="#1A1A2E"), showarrow=False)
    return _apply_layout(fig, title=dict(text=title, font=dict(size=16)), height=420)


def product_donut(df: pd.DataFrame, title: str = "Volume by Product") -> go.Figure:
    """Donut chart showing product distribution."""
    counts = df["Product"].value_counts().reindex(PRODUCT_ORDER, fill_value=0)
    fig = go.Figure(go.Pie(
        labels=counts.index,
        values=counts.values,
        hole=0.5,
        marker=dict(colors=[PRODUCT_COLORS[p] for p in counts.index],
                    line=dict(color="white", width=2)),
        textinfo="label+percent",
        textposition="outside",
        textfont=dict(size=12),
        hovertemplate="<b>%{label}</b><br>%{value} schools (%{percent})<extra></extra>",
    ))
    total = counts.sum()
    fig.add_annotation(text=f"<b>{total}</b><br>schools", x=0.5, y=0.5,
                       font=dict(size=18, color="#1A1A2E"), showarrow=False)
    return _apply_layout(fig, title=dict(text=title, font=dict(size=16)), height=420)


# ═══════════════════════════════════════════════════════════════════
#  BAR CHARTS
# ═══════════════════════════════════════════════════════════════════

def phase_bar(df: pd.DataFrame, phases: list[str],
              title: str = "Median Phase Durations by Cohort") -> go.Figure:
    """Grouped bar chart of median phase durations per cohort."""
    data = []
    for cohort in COHORT_ORDER:
        sub = df[df["Cohort"] == cohort]
        for phase in phases:
            if phase in sub.columns:
                valid = sub[phase].dropna()
                med = valid.median() if len(valid) > 0 else None
                data.append({"Cohort": cohort, "Phase": phase, "Median Days": med})

    pdf = pd.DataFrame(data)
    if pdf.empty:
        return _empty_figure("No phase data available")

    fig = px.bar(
        pdf, x="Phase", y="Median Days", color="Cohort", barmode="group",
        color_discrete_map=COHORT_COLORS,
        text="Median Days",
        category_orders={"Cohort": COHORT_ORDER},
    )
    fig.update_traces(
        texttemplate="%{text:.0f}d",
        textposition="outside",
        textfont=dict(size=10),
    )
    return _apply_layout(fig, title=dict(text=title, font=dict(size=16)), height=480)


def phase_boxplots(df: pd.DataFrame, phase: str,
                   title: str | None = None) -> go.Figure:
    """Box plot of a single phase duration, split by cohort."""
    if title is None:
        title = f"{phase} — Distribution by Cohort"

    valid = df[df[phase].notna()].copy()
    if valid.empty:
        return _empty_figure(f"No data for {phase}")

    fig = px.box(
        valid, x="Cohort", y=phase, color="Cohort",
        color_discrete_map=COHORT_COLORS,
        category_orders={"Cohort": COHORT_ORDER},
        points="all",
    )
    fig.update_traces(marker=dict(opacity=0.5, size=5))
    fig.update_yaxes(title_text="Days")
    return _apply_layout(fig, title=dict(text=title, font=dict(size=16)),
                         height=450, showlegend=False)


def stage_funnel(df: pd.DataFrame,
                 title: str = "Onboarding Stage Distribution") -> go.Figure:
    """Horizontal stacked bar of onboarding stage by cohort."""
    if "Onboarding Stage" not in df.columns:
        return _empty_figure("No stage data available")

    ct = pd.crosstab(df["Onboarding Stage"], df["Cohort"])
    # Reindex to cohort order
    for c in COHORT_ORDER:
        if c not in ct.columns:
            ct[c] = 0
    ct = ct[COHORT_ORDER]
    ct = ct.sort_index()

    # Shorten stage labels
    short = ct.index.map(lambda s: s.split(". ", 1)[-1][:30] if isinstance(s, str) else str(s))

    fig = go.Figure()
    for cohort in COHORT_ORDER:
        fig.add_trace(go.Bar(
            y=short, x=ct[cohort], name=cohort, orientation="h",
            marker_color=COHORT_COLORS[cohort],
            text=ct[cohort].apply(lambda v: str(v) if v > 0 else ""),
            textposition="inside", textfont=dict(color="white", size=10),
        ))

    fig.update_layout(barmode="stack")
    fig.update_yaxes(autorange="reversed")
    fig.update_xaxes(title_text="Number of Schools")
    return _apply_layout(fig, title=dict(text=title, font=dict(size=16)), height=450)


def ko_launch_scatter(df: pd.DataFrame,
                      title: str = "Early Engagement vs Deployment Speed") -> go.Figure:
    """Scatter: Contract→KO vs KO→Launch, colored by cohort."""
    x_col = "Contract → Kick Off"
    y_col = "Kick Off → Launch"

    valid = df.dropna(subset=[x_col, y_col]).copy()
    if valid.empty:
        return _empty_figure("No data for scatter plot")

    fig = px.scatter(
        valid, x=x_col, y=y_col, color="Cohort",
        color_discrete_map=COHORT_COLORS,
        category_orders={"Cohort": COHORT_ORDER},
        hover_data=["Name", "Product"],
        opacity=0.7,
    )
    fig.update_traces(marker=dict(size=8, line=dict(width=1, color="white")))
    fig.update_xaxes(title_text="Contract → Kick Off (days)")
    fig.update_yaxes(title_text="Kick Off → Launch (days)")

    # Add 14-day SLA line
    fig.add_vline(x=14, line_dash="dash", line_color="#E76F51", opacity=0.5,
                  annotation_text="14-day SLA", annotation_position="top right")
    return _apply_layout(fig, title=dict(text=title, font=dict(size=16)), height=500)


def quarterly_launches(df: pd.DataFrame,
                       title: str = "Launch Volume by Quarter") -> go.Figure:
    """Stacked bar of launches by quarter, colored by cohort."""
    valid = df.dropna(subset=["Launch QY"]).copy()
    if valid.empty:
        return _empty_figure("No launch date data available")

    # Sort by year-quarter
    valid["_sort"] = valid["Launch Year"] * 10 + valid["Launch Quarter"]
    ct = pd.crosstab(valid["Launch QY"], valid["Cohort"])
    for c in COHORT_ORDER:
        if c not in ct.columns:
            ct[c] = 0
    ct = ct[COHORT_ORDER]

    # Sort index by year-quarter
    order = sorted(ct.index, key=lambda x: (int(x.split()[1]), int(x[1])))
    ct = ct.reindex(order)

    fig = go.Figure()
    for cohort in COHORT_ORDER:
        fig.add_trace(go.Bar(
            x=ct.index, y=ct[cohort], name=cohort,
            marker_color=COHORT_COLORS[cohort],
            text=ct[cohort].apply(lambda v: str(v) if v > 0 else ""),
            textposition="inside", textfont=dict(color="white", size=9),
        ))

    fig.update_layout(barmode="stack")
    fig.update_xaxes(title_text="Quarter", tickangle=45)
    fig.update_yaxes(title_text="Number of Launches")
    return _apply_layout(fig, title=dict(text=title, font=dict(size=16)), height=450)


def owner_workload(df: pd.DataFrame,
                   title: str = "Account Manager Portfolio — Cohort Mix") -> go.Figure:
    """Stacked horizontal bar showing each owner's school count by cohort."""
    if "Owner" not in df.columns or df["Owner"].isna().all():
        return _empty_figure("Account Manager data not available for this selection")

    ct = pd.crosstab(df["Owner"], df["Cohort"])
    for c in COHORT_ORDER:
        if c not in ct.columns:
            ct[c] = 0
    ct = ct[COHORT_ORDER]
    ct["Total"] = ct.sum(axis=1)
    ct = ct.sort_values("Total", ascending=True)

    fig = go.Figure()
    for cohort in COHORT_ORDER:
        fig.add_trace(go.Bar(
            y=ct.index, x=ct[cohort], name=cohort, orientation="h",
            marker_color=COHORT_COLORS[cohort],
            text=ct[cohort].apply(lambda v: str(v) if v > 0 else ""),
            textposition="inside", textfont=dict(color="white", size=9),
        ))

    fig.update_layout(barmode="stack")
    fig.update_xaxes(title_text="Number of Schools")
    return _apply_layout(fig, title=dict(text=title, font=dict(size=16)),
                         height=max(350, len(ct) * 35 + 100))


def owner_performance(df: pd.DataFrame,
                      title: str = "Account Manager Performance: Median Kick Off → Launch") -> go.Figure:
    """Horizontal bar of median KO→Launch per owner, color-coded by benchmark."""
    if "Owner" not in df.columns or df["Owner"].isna().all():
        return _empty_figure("Account Manager data not available for this selection")

    phase = "Kick Off → Launch"
    if phase not in df.columns:
        return _empty_figure("Kick Off → Launch data not available")

    owners = df.groupby("Owner")[phase].agg(["median", "count"]).dropna()
    owners = owners[owners["count"] >= 3].sort_values("median", ascending=True)

    if owners.empty:
        return _empty_figure("Not enough data for Account Manager performance (need ≥3 schools each)")

    colors = ["#2A9D8F" if m <= 42 else "#E9C46A" if m <= 70 else "#E76F51"
              for m in owners["median"]]

    fig = go.Figure(go.Bar(
        y=owners.index, x=owners["median"], orientation="h",
        marker_color=colors,
        text=[f'{m:.0f}d (n={int(c)})' for m, c in zip(owners["median"], owners["count"])],
        textposition="outside", textfont=dict(size=10),
    ))

    fig.add_vline(x=42, line_dash="dash", line_color="#2A9D8F", opacity=0.4)
    fig.add_vline(x=70, line_dash="dash", line_color="#E76F51", opacity=0.4)
    fig.update_xaxes(title_text="Median Days")
    return _apply_layout(fig, title=dict(text=title, font=dict(size=16)),
                         height=max(350, len(owners) * 35 + 100), showlegend=False)


# ═══════════════════════════════════════════════════════════════════
#  CHURN CHARTS
# ═══════════════════════════════════════════════════════════════════

def churn_donut(df: pd.DataFrame,
                title: str = "Churn Timing: Pre vs Post Graduation") -> go.Figure:
    """Donut showing pre-completion vs post-graduation churn."""
    cancelled = df[df["Cohort"] == "Cancelled"].copy()
    if cancelled.empty:
        return _empty_figure("No cancelled schools in selection")

    grad_stages = [5, 6, 7]
    cancelled["Churn Type"] = cancelled["Stage Number"].apply(
        lambda s: "Post-Graduation" if s in grad_stages else "Pre-Completion"
    )
    counts = cancelled["Churn Type"].value_counts()

    fig = go.Figure(go.Pie(
        labels=counts.index, values=counts.values, hole=0.5,
        marker=dict(colors=["#E76F51", "#4361EE"],
                    line=dict(color="white", width=2)),
        textinfo="label+percent+value",
        textposition="outside",
        hovertemplate="<b>%{label}</b><br>%{value} schools (%{percent})<extra></extra>",
    ))
    return _apply_layout(fig, title=dict(text=title, font=dict(size=16)), height=400)


def churn_by_stage(df: pd.DataFrame,
                   title: str = "Churn by Onboarding Stage") -> go.Figure:
    """Horizontal bar of At-Risk + Cancelled schools by onboarding stage."""
    churn = df[df["Cohort"].isin(["At Risk", "Cancelled"])].copy()
    if churn.empty:
        return _empty_figure("No at-risk or cancelled schools in selection")

    ct = pd.crosstab(churn["Onboarding Stage"], churn["Cohort"])
    for c in ["At Risk", "Cancelled"]:
        if c not in ct.columns:
            ct[c] = 0
    ct = ct[["At Risk", "Cancelled"]]
    ct = ct.sort_index()

    short = ct.index.map(lambda s: s.split(". ", 1)[-1][:30] if isinstance(s, str) else str(s))

    fig = go.Figure()
    for cohort in ["At Risk", "Cancelled"]:
        fig.add_trace(go.Bar(
            y=short, x=ct[cohort], name=cohort, orientation="h",
            marker_color=COHORT_COLORS[cohort],
            text=ct[cohort].apply(lambda v: str(v) if v > 0 else ""),
            textposition="inside", textfont=dict(color="white", size=10),
        ))

    fig.update_layout(barmode="stack")
    fig.update_yaxes(autorange="reversed")
    fig.update_xaxes(title_text="Number of Schools")
    return _apply_layout(fig, title=dict(text=title, font=dict(size=16)), height=420)


def cancellation_substatus(df: pd.DataFrame,
                           title: str = "Cancellation Sub-Status Breakdown") -> go.Figure:
    """Bar chart of School Status values for Cancelled schools."""
    cancelled = df[df["Cohort"] == "Cancelled"].copy()
    if cancelled.empty or "School Status (CS)" not in cancelled.columns:
        return _empty_figure("No cancellation status data")

    counts = cancelled["School Status (CS)"].value_counts()

    fig = go.Figure(go.Bar(
        y=counts.index, x=counts.values, orientation="h",
        marker_color="#E76F51",
        text=counts.values, textposition="outside", textfont=dict(size=10),
    ))
    fig.update_yaxes(autorange="reversed")
    fig.update_xaxes(title_text="Number of Schools")
    return _apply_layout(fig, title=dict(text=title, font=dict(size=16)),
                         height=max(300, len(counts) * 30 + 100), showlegend=False)


# ═══════════════════════════════════════════════════════════════════
#  BENCHMARK CHARTS
# ═══════════════════════════════════════════════════════════════════

def benchmark_compliance_donut(df: pd.DataFrame, phase: str,
                               benchmarks: dict) -> go.Figure:
    """Donut showing % of schools in Healthy/Caution/Critical for a phase."""
    from utils.benchmarks import classify_phase

    valid = df[phase].dropna()
    if valid.empty:
        return _empty_figure(f"No data for {phase}")

    classifications = valid.apply(lambda d: classify_phase(phase, d))
    counts = classifications.value_counts().reindex(["Healthy", "Caution", "Critical"], fill_value=0)

    fig = go.Figure(go.Pie(
        labels=counts.index, values=counts.values, hole=0.5,
        marker=dict(colors=[BENCHMARK_COLORS[c] for c in counts.index],
                    line=dict(color="white", width=2)),
        textinfo="label+percent",
        textposition="outside",
    ))
    total = counts.sum()
    healthy_pct = counts.get("Healthy", 0) / total * 100 if total > 0 else 0
    fig.add_annotation(text=f"<b>{healthy_pct:.0f}%</b><br>on track", x=0.5, y=0.5,
                       font=dict(size=14), showarrow=False)
    return _apply_layout(fig, title=dict(text=phase, font=dict(size=14)), height=320,
                         margin=dict(l=20, r=20, t=50, b=20))


def trend_line(df: pd.DataFrame, phase: str,
               title: str | None = None) -> go.Figure:
    """Line chart: median phase duration per year signed."""
    if title is None:
        title = f"Trend: Median {phase} Over Time"

    if "Year Signed" not in df.columns:
        return _empty_figure("No Year Signed data")

    valid = df[df[phase].notna() & df["Year Signed"].notna()].copy()
    valid = valid[valid["Year Signed"] > 2000]
    if valid.empty:
        return _empty_figure(f"No valid data for {phase} trend")

    trend = valid.groupby("Year Signed")[phase].agg(["median", "count"])
    trend = trend[trend["count"] >= 3].dropna()

    if trend.empty:
        return _empty_figure(f"Not enough data points for trend (need ≥3 schools per year)")

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=trend.index, y=trend["median"], mode="lines+markers+text",
        line=dict(color="#4361EE", width=3),
        marker=dict(size=10, color="#4361EE"),
        text=[f'{m:.0f}d' for m in trend["median"]],
        textposition="top center", textfont=dict(size=11),
        hovertemplate="Year: %{x}<br>Median: %{y:.0f} days<br>n=%{customdata}<extra></extra>",
        customdata=trend["count"].values,
    ))

    fig.update_xaxes(title_text="Year Signed", dtick=1)
    fig.update_yaxes(title_text="Median Days")
    return _apply_layout(fig, title=dict(text=title, font=dict(size=16)), height=400,
                         showlegend=False)


def product_comparison_bar(df: pd.DataFrame, phase: str,
                           title: str | None = None) -> go.Figure:
    """Grouped bar comparing the same phase across products."""
    if title is None:
        title = f"{phase} — Product Comparison"

    data = []
    for product in PRODUCT_ORDER:
        sub = df[df["Product"] == product]
        if phase in sub.columns:
            valid = sub[phase].dropna()
            med = valid.median() if len(valid) > 0 else None
            data.append({"Product": product, "Median Days": med})

    pdf = pd.DataFrame(data)
    if pdf.empty or pdf["Median Days"].isna().all():
        return _empty_figure(f"No data for {phase}")

    fig = px.bar(
        pdf, x="Product", y="Median Days", color="Product",
        color_discrete_map=PRODUCT_COLORS,
        text="Median Days",
    )
    fig.update_traces(texttemplate="%{text:.0f}d", textposition="outside")
    fig.update_yaxes(title_text="Median Days")
    return _apply_layout(fig, title=dict(text=title, font=dict(size=16)),
                         height=400, showlegend=False)


# ═══════════════════════════════════════════════════════════════════
#  SCHOOL TIMELINE
# ═══════════════════════════════════════════════════════════════════

def school_timeline(school_row: pd.Series) -> go.Figure:
    """Horizontal timeline showing a school's milestone dates."""
    from utils.benchmarks import classify_phase, get_benchmark_color
    from utils.data_loader import DATE_COLS, PHASES

    milestones = []
    for col in DATE_COLS:
        if col in school_row.index and pd.notna(school_row[col]):
            milestones.append({"Milestone": col.replace(" Date", ""), "Date": school_row[col]})

    if not milestones:
        return _empty_figure("No milestone dates available for this school")

    mdf = pd.DataFrame(milestones)
    mdf["Date"] = pd.to_datetime(mdf["Date"])
    mdf = mdf.sort_values("Date")

    colors = []
    for i, row in mdf.iterrows():
        colors.append("#4361EE")

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=mdf["Date"], y=[1] * len(mdf), mode="markers+text",
        marker=dict(size=16, color=colors, line=dict(width=2, color="white")),
        text=mdf["Milestone"],
        textposition="top center", textfont=dict(size=10),
        hovertemplate="<b>%{text}</b><br>%{x|%b %d, %Y}<extra></extra>",
    ))

    # Add connecting line
    fig.add_trace(go.Scatter(
        x=mdf["Date"], y=[1] * len(mdf), mode="lines",
        line=dict(color="#D0D8E4", width=2),
        showlegend=False, hoverinfo="skip",
    ))

    fig.update_yaxes(visible=False, range=[0.5, 1.8])
    fig.update_xaxes(title_text="")
    return _apply_layout(fig, title=dict(text="Onboarding Timeline", font=dict(size=14)),
                         height=200, showlegend=False,
                         margin=dict(l=20, r=20, t=50, b=20))


# ═══════════════════════════════════════════════════════════════════
#  DATA QUALITY CHARTS
# ═══════════════════════════════════════════════════════════════════

def missing_values_heatmap(summary_df: pd.DataFrame,
                           title: str = "Data Completeness (% Present)") -> go.Figure:
    """Heatmap of data completeness (% non-null) per product × column."""
    if summary_df.empty:
        return _empty_figure("No data quality summary available")

    fig = px.imshow(
        summary_df.values,
        x=summary_df.columns.tolist(),
        y=summary_df.index.tolist(),
        color_continuous_scale=["#E76F51", "#E9C46A", "#2A9D8F"],
        zmin=0, zmax=100,
        text_auto=".0f",
        aspect="auto",
    )
    fig.update_layout(coloraxis_colorbar=dict(title="% Present"))
    return _apply_layout(fig, title=dict(text=title, font=dict(size=16)),
                         height=max(300, len(summary_df) * 40 + 100))


# ═══════════════════════════════════════════════════════════════════
#  UTILITY
# ═══════════════════════════════════════════════════════════════════

def _empty_figure(message: str) -> go.Figure:
    """Return a placeholder figure with a message when no data is available."""
    fig = go.Figure()
    fig.add_annotation(
        text=message, x=0.5, y=0.5, xref="paper", yref="paper",
        showarrow=False, font=dict(size=16, color="#ADB5BD"),
    )
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return _apply_layout(fig, height=300)
