"""
Country Comparison Module
=========================
Builds honest side-by-side comparisons of the same World Bank indicators
across two countries.

Honesty rules (per GEMINI.md):
- Only genuinely observed annual values are compared; missing years stay
  missing (never zero-filled, never interpolated).
- Each value is shown with its own reporting year, because the latest
  available year can differ between countries and indicators.
"""

from typing import Any, Dict, List, Optional
import pandas as pd


def build_comparison_table(
    data_by_country: Dict[str, Dict[str, Dict[str, Any]]],
    country_names: Optional[Dict[str, str]] = None,
) -> pd.DataFrame:
    """
    Build a latest-value comparison table across countries.

    Parameters:
        data_by_country: Mapping of country code -> load_all_economic_data() result.
        country_names: Optional mapping of country code -> display name.

    Returns:
        pd.DataFrame with one row per indicator and, per country, columns for
        the latest observed value, its reporting year, and the year-over-year
        change. Missing data appears as None (rendered as N/A by callers).
    """
    names = country_names or {}
    rows: List[Dict[str, Any]] = []

    # Indicator order follows the first country's data; fall back gracefully.
    indicator_keys: List[str] = []
    for country_data in data_by_country.values():
        indicator_keys = list(country_data.keys())
        break

    for key in indicator_keys:
        row: Dict[str, Any] = {"indicator_key": key}
        indicator_name = key
        unit = "%"

        for code, country_data in data_by_country.items():
            item = country_data.get(key, {})
            meta = item.get("metadata", {})
            summary = item.get("summary", {})
            indicator_name = meta.get("name", indicator_name)
            unit = meta.get("unit", unit)

            label = names.get(code, code)
            if summary.get("has_data"):
                row[f"{label} Value"] = summary.get("latest_value")
                row[f"{label} Year"] = summary.get("latest_year")
                row[f"{label} Change (pp)"] = summary.get("change")
            else:
                row[f"{label} Value"] = None
                row[f"{label} Year"] = None
                row[f"{label} Change (pp)"] = None

        row["indicator_name"] = indicator_name
        row["unit"] = unit
        rows.append(row)

    return pd.DataFrame(rows)


def align_series_for_years(
    df_a: pd.DataFrame,
    df_b: pd.DataFrame,
) -> pd.DataFrame:
    """
    Align two indicator series on their UNION of observed years for charting.

    Parameters:
        df_a, df_b: DataFrames with 'year' and 'value' columns.

    Returns:
        pd.DataFrame with columns ['year', 'value_a', 'value_b'] sorted by
        year. Years where one country has no observation keep NaN for that
        country - the chart shows a gap instead of an invented value.
    """
    cols = ["year", "value_a", "value_b"]
    a = df_a[["year", "value"]].rename(columns={"value": "value_a"}) if not df_a.empty else pd.DataFrame(columns=["year", "value_a"])
    b = df_b[["year", "value"]].rename(columns={"value": "value_b"}) if not df_b.empty else pd.DataFrame(columns=["year", "value_b"])

    if a.empty and b.empty:
        return pd.DataFrame(columns=cols)

    merged = pd.merge(a, b, on="year", how="outer").sort_values(by="year").reset_index(drop=True)
    return merged[cols]
