"""
Benchmark definitions — SLA thresholds and classification logic.

Thresholds are derived from existing analysis findings:
  - 14-day Contract→KO SLA from consolidated report
  - Other thresholds based on Onboarding/Retention cohort medians
"""

# ─── Threshold Definitions ────────────────────────────────────────
# Each phase: (healthy_max, caution_max) — anything above caution_max is critical

BENCHMARKS = {
    "Contract → Kick Off": {
        "healthy": 14,
        "caution": 30,
        "unit": "days",
        "description": "Time from contract signing to first kick-off call",
    },
    "Kick Off → Training": {
        "healthy": 7,
        "caution": 21,
        "unit": "days",
        "description": "Time from kick-off to training session",
    },
    "Training → Launch": {
        "healthy": 14,
        "caution": 30,
        "unit": "days",
        "description": "Time from training completion to product go-live",
    },
    "Kick Off → Launch": {
        "healthy": 42,
        "caution": 70,
        "unit": "days",
        "description": "Total deployment time (kick-off to go-live)",
    },
    "Launch → Post Launch": {
        "healthy": 30,
        "caution": 60,
        "unit": "days",
        "description": "Time from go-live to post-launch check-in",
    },
}


def classify_phase(phase_name: str, days: float) -> str:
    """
    Classify a phase duration as Healthy / Caution / Critical.

    Returns:
        "Healthy", "Caution", or "Critical"
    """
    if phase_name not in BENCHMARKS:
        return "Unknown"

    import math
    if math.isnan(days):
        return "Unknown"

    bench = BENCHMARKS[phase_name]
    if days <= bench["healthy"]:
        return "Healthy"
    elif days <= bench["caution"]:
        return "Caution"
    else:
        return "Critical"


def get_benchmark_color(classification: str) -> str:
    """Return the display color for a benchmark classification."""
    return {
        "Healthy": "#2A9D8F",
        "Caution": "#E9C46A",
        "Critical": "#E76F51",
        "Unknown": "#ADB5BD",
    }.get(classification, "#ADB5BD")


def get_benchmark_emoji(classification: str) -> str:
    """Return an emoji indicator for a benchmark classification."""
    return {
        "Healthy": "🟢",
        "Caution": "🟡",
        "Critical": "🔴",
        "Unknown": "⚪",
    }.get(classification, "⚪")
