"""
Shock Radar — Anomaly Detection Module
======================================
Automatically flags unusual movements in macroeconomic indicator time series
using z-scores computed on year-over-year changes.

Method (deliberately simple and explainable):
1. Compute the year-over-year change of the indicator.
2. Compute the mean and standard deviation of those changes.
3. A change with |z-score| >= threshold is flagged as an unusual movement.

In accordance with GEMINI.md:
- Deterministic statistics only; no black-box models.
- Every flag shows the actual observed value and change — nothing invented.
- Series that are too short for meaningful statistics produce no flags and
  the UI says why, rather than guessing.
"""

from typing import Any, Dict, List
import numpy as np
import pandas as pd

# A year-over-year change at least this many standard deviations from the
# average change is considered unusual.
DEFAULT_Z_THRESHOLD = 2.0

# Minimum number of recorded observations needed before z-scores are
# statistically meaningful for a beginner-facing tool.
MIN_OBSERVATIONS = 6


def detect_anomalies(
    df: pd.DataFrame,
    indicator_name: str = "Indicator",
    z_threshold: float = DEFAULT_Z_THRESHOLD,
) -> Dict[str, Any]:
    """
    Flag unusual year-over-year movements in one indicator time series.

    Parameters:
        df: DataFrame with 'year' and 'value' columns (NaN allowed).
        indicator_name: Human-readable indicator name for notes.
        z_threshold: Absolute z-score cutoff for flagging a change.

    Returns:
        dict with:
            - 'flags': list of dicts (year, value, change, z_score,
              direction, note), sorted by |z| descending.
            - 'has_flags': bool.
            - 'reason': plain-English explanation when no flags exist.
    """
    result: Dict[str, Any] = {"flags": [], "has_flags": False, "reason": ""}

    if df.empty or "year" not in df.columns or "value" not in df.columns:
        result["reason"] = f"No observations are available for {indicator_name}, so Shock Radar has nothing to scan."
        return result

    valid = df.dropna(subset=["value"]).sort_values(by="year").reset_index(drop=True)

    if len(valid) < MIN_OBSERVATIONS:
        result["reason"] = (
            f"Only {len(valid)} recorded observations are available for {indicator_name}. "
            f"Shock Radar needs at least {MIN_OBSERVATIONS} to judge what 'unusual' means, so no flags were raised."
        )
        return result

    changes = valid["value"].diff()
    mean_change = float(changes.mean())
    std_change = float(changes.std(ddof=1))

    # A perfectly flat series has zero spread: every change is 'usual'.
    if std_change == 0 or np.isnan(std_change):
        result["reason"] = f"{indicator_name} barely moved over the observed period, so no unusual movements stand out."
        return result

    flags: List[Dict[str, Any]] = []
    for idx in range(1, len(valid)):
        change = float(changes.iloc[idx])
        z_score = (change - mean_change) / std_change

        if abs(z_score) >= z_threshold:
            year = int(valid["year"].iloc[idx])
            value = float(valid["value"].iloc[idx])
            prev_year = int(valid["year"].iloc[idx - 1])
            direction = "spike" if change > 0 else "drop"
            note = (
                f"In {year}, {indicator_name} {('rose' if change > 0 else 'fell')} by "
                f"{abs(change):.2f} points versus {prev_year} — an unusually sharp {direction} "
                f"({abs(z_score):.1f}× the typical year-to-year swing). Worth checking what "
                f"happened that year (policy shifts, crises, or one-off events)."
            )
            flags.append({
                "year": year,
                "value": round(value, 2),
                "change": round(change, 2),
                "z_score": round(float(z_score), 2),
                "direction": direction,
                "note": note,
            })

    flags.sort(key=lambda f: abs(f["z_score"]), reverse=True)
    result["flags"] = flags
    result["has_flags"] = len(flags) > 0
    if not flags:
        result["reason"] = f"No unusually sharp movements detected in {indicator_name} over the selected period. All year-to-year changes stayed within the normal range."
    return result


def detect_all_anomalies(
    economic_data: Dict[str, Dict[str, Any]],
    z_threshold: float = DEFAULT_Z_THRESHOLD,
) -> Dict[str, Dict[str, Any]]:
    """
    Run Shock Radar across every indicator in the standard economic data bundle.

    Parameters:
        economic_data: Output of modules.economic_data.load_all_economic_data.
        z_threshold: Absolute z-score cutoff.

    Returns:
        Dict mapping indicator keys to their detect_anomalies result,
        with 'indicator_name' added for display.
    """
    results: Dict[str, Dict[str, Any]] = {}
    for key, item in economic_data.items():
        name = item.get("metadata", {}).get("name", key.title())
        detection = detect_anomalies(
            df=item.get("data", pd.DataFrame()),
            indicator_name=name,
            z_threshold=z_threshold,
        )
        detection["indicator_name"] = name
        results[key] = detection
    return results
