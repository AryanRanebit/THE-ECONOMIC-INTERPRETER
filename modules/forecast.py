"""
Outlook Engine — Trend Forecast Module
======================================
Produces a simple, transparent linear-trend forecast for each macroeconomic
indicator, with a prediction interval that honestly widens the further ahead
it looks.

Method (deliberately simple and explainable):
1. Fit an ordinary least-squares straight line (value ~ year) to the
   recorded observations.
2. Extend that line a few years into the future.
3. Wrap it in an approximate 95% prediction interval derived from the
   regression residuals.

In accordance with GEMINI.md:
- Deterministic statistics only (NumPy least squares) — no AI models.
- Forecasts are labelled 'illustrative only' and are never presented as
  investment or policy advice.
- Series that are too short produce no forecast and the UI says why.
"""

from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd

# Minimum recorded observations before a trend line is meaningful.
MIN_OBSERVATIONS = 5

# Approximate 95% normal multiplier for the prediction interval.
Z_95 = 1.96

FORECAST_DISCLAIMER = (
    "Illustrative only: Outlook Engine simply extends the historical straight-line trend "
    "and its past variability. Real economies are shaped by policy decisions, global events, "
    "and shocks that a trend line cannot see. This is not investment, policy, or financial advice."
)


def forecast_indicator(
    df: pd.DataFrame,
    years_ahead: int = 3,
    indicator_name: str = "Indicator",
) -> Dict[str, Any]:
    """
    Forecast an indicator with a linear trend and prediction interval.

    Parameters:
        df: DataFrame with 'year' and 'value' columns (NaN allowed).
        years_ahead: Number of future years to project.
        indicator_name: Human-readable name used in the summary text.

    Returns:
        dict with:
            - 'has_forecast': bool.
            - 'forecast': DataFrame with ['year', 'predicted', 'lower', 'upper'].
            - 'slope': trend change per year.
            - 'r_squared': goodness of fit of the trend line.
            - 'summary': plain-English one-liner about the trend.
            - 'reason': explanation when no forecast is possible.
            - 'disclaimer': FORECAST_DISCLAIMER.
    """
    result: Dict[str, Any] = {
        "has_forecast": False,
        "forecast": pd.DataFrame(columns=["year", "predicted", "lower", "upper"]),
        "slope": None,
        "r_squared": None,
        "summary": "",
        "reason": "",
        "disclaimer": FORECAST_DISCLAIMER,
    }

    if df.empty or "year" not in df.columns or "value" not in df.columns:
        result["reason"] = f"No recorded observations are available for {indicator_name}, so no outlook can be drawn."
        return result

    valid = df.dropna(subset=["value"]).sort_values(by="year").reset_index(drop=True)

    if len(valid) < MIN_OBSERVATIONS:
        result["reason"] = (
            f"Only {len(valid)} recorded observations are available for {indicator_name}. "
            f"Outlook Engine needs at least {MIN_OBSERVATIONS} years of data before drawing a trend."
        )
        return result

    x = valid["year"].to_numpy(dtype=float)
    y = valid["value"].to_numpy(dtype=float)

    # Least-squares line: y = slope * x + intercept
    slope, intercept = np.polyfit(x, y, 1)
    fitted = slope * x + intercept
    residuals = y - fitted

    # Goodness of fit (R^2); guard against zero variance
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    ss_res = float(np.sum(residuals ** 2))
    r_squared = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0

    # Approximate prediction interval from residual spread
    n = len(valid)
    residual_std = float(np.sqrt(ss_res / (n - 2))) if n > 2 else 0.0
    x_mean = float(x.mean())
    sxx = float(np.sum((x - x_mean) ** 2))

    last_year = int(valid["year"].max())
    future_years = np.arange(last_year + 1, last_year + years_ahead + 1, dtype=float)

    rows: List[Dict[str, float]] = []
    for yr in future_years:
        predicted = slope * yr + intercept
        # Prediction interval widens with distance from the observed mean
        leverage = 1.0 + 1.0 / n + ((yr - x_mean) ** 2 / sxx if sxx > 0 else 0.0)
        margin = Z_95 * residual_std * np.sqrt(leverage)
        rows.append({
            "year": int(yr),
            "predicted": round(float(predicted), 2),
            "lower": round(float(predicted - margin), 2),
            "upper": round(float(predicted + margin), 2),
        })

    forecast_df = pd.DataFrame(rows)

    direction_word = "rising" if slope > 0.05 else ("falling" if slope < -0.05 else "flat")
    result.update({
        "has_forecast": True,
        "forecast": forecast_df,
        "slope": round(float(slope), 3),
        "r_squared": round(r_squared, 3),
        "summary": (
            f"The long-term trend for {indicator_name} has been {direction_word} by about "
            f"{abs(slope):.2f} points per year over the recorded period. If — and only if — that "
            f"historical pattern continued unchanged, the shaded band shows the range the trend "
            f"would suggest for the next {years_ahead} years."
        ),
        "reason": "",
    })
    return result


def forecast_all_indicators(
    economic_data: Dict[str, Dict[str, Any]],
    years_ahead: int = 3,
) -> Dict[str, Dict[str, Any]]:
    """
    Run Outlook Engine across every indicator in the standard economic data bundle.

    Returns:
        Dict mapping indicator keys to their forecast_indicator result,
        with 'indicator_name' and 'unit' added for display.
    """
    results: Dict[str, Dict[str, Any]] = {}
    for key, item in economic_data.items():
        name = item.get("metadata", {}).get("name", key.title())
        fc = forecast_indicator(
            df=item.get("data", pd.DataFrame()),
            years_ahead=years_ahead,
            indicator_name=name,
        )
        fc["indicator_name"] = name
        fc["unit"] = item.get("metadata", {}).get("unit", "%")
        results[key] = fc
    return results
