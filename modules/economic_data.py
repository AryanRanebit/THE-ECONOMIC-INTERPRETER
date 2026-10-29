"""
Economic Data Module
====================
Handles retrieval, validation, cleaning, and preparation of macroeconomic
indicators from the World Bank Indicators API.

Indicators Supported:
- Inflation (Consumer Prices annual %): FP.CPI.TOTL.ZG
- Unemployment (% of total labor force): SL.UEM.TOTL.ZS
- Real GDP Growth (annual %): NY.GDP.MKTP.KD.ZG
"""

from typing import Any, Dict, Optional
import pandas as pd
import requests

try:
    import streamlit as st
    cache_data_econ = st.cache_data(ttl=3600, show_spinner=False)
except Exception:
    def cache_data_econ(func):
        return func

# World Bank API Base URL
WORLD_BANK_BASE_URL = "https://api.worldbank.org/v2"

# Metadata for supported economic indicators
INDICATOR_METADATA: Dict[str, Dict[str, str]] = {
    "inflation": {
        "code": "FP.CPI.TOTL.ZG",
        "name": "Inflation (Consumer Prices)",
        "unit": "% (Annual)",
        "description": "Measures the annual percentage change in the cost to the average consumer of acquiring a basket of goods and services.",
    },
    "unemployment": {
        "code": "SL.UEM.TOTL.ZS",
        "name": "Unemployment Rate",
        "unit": "% of Labor Force",
        "description": "The share of the labor force that is without work but available for and seeking employment.",
    },
    "gdp_growth": {
        "code": "NY.GDP.MKTP.KD.ZG",
        "name": "Real GDP Growth",
        "unit": "% (Annual)",
        "description": "Annual percentage growth rate of GDP at market prices based on constant local currency.",
    },
}


def fetch_indicator_series(
    country_code: str,
    indicator_code: str,
    date_range: str = "2000:2025",
    timeout_seconds: int = 10,
) -> pd.DataFrame:
    """
    Fetch historical time series for an indicator from the World Bank API.

    Parameters:
        country_code: ISO-2 or ISO-3 country code (e.g., 'IN' for India).
        indicator_code: World Bank indicator identifier.
        date_range: Colon-separated year range, e.g., '2000:2025'.
        timeout_seconds: HTTP request timeout in seconds.

    Returns:
        pd.DataFrame: Cleaned DataFrame with columns ['year', 'value', 'indicator_code']
                      sorted chronologically by year ascending. Returns an empty DataFrame
                      if the request fails or no data is found.
    """
    url = f"{WORLD_BANK_BASE_URL}/country/{country_code}/indicator/{indicator_code}"
    params = {
        "format": "json",
        "date": date_range,
        "per_page": 100,  # Ensure we capture all years in the range in one page
    }

    try:
        response = requests.get(url, params=params, timeout=timeout_seconds)
        response.raise_for_status()
        data = response.json()

        # Validate World Bank API structure: Expecting a list with [metadata_dict, observations_list]
        if not isinstance(data, list) or len(data) < 2 or not isinstance(data[1], list):
            return pd.DataFrame(columns=["year", "value", "indicator_code"])

        observations = data[1]
        records = []

        for item in observations:
            if not isinstance(item, dict):
                continue

            raw_date = item.get("date")
            raw_value = item.get("value")

            # Parse year safely
            try:
                year = int(raw_date)
            except (ValueError, TypeError):
                continue

            # Note: We do NOT convert None to 0. A missing observation is kept as None/NaN.
            try:
                value = float(raw_value) if raw_value is not None else None
            except (ValueError, TypeError):
                value = None

            records.append({
                "year": year,
                "value": value,
                "indicator_code": indicator_code,
            })

        if not records:
            return pd.DataFrame(columns=["year", "value", "indicator_code"])

        df = pd.DataFrame(records)

        # Sort chronologically (oldest to newest)
        df = df.sort_values(by="year", ascending=True).reset_index(drop=True)
        return df

    except requests.exceptions.RequestException as err:
        # Graceful handling: Log warning, return empty DataFrame rather than crashing
        print(f"[Warning] Failed to fetch {indicator_code} for {country_code}: {err}")
        return pd.DataFrame(columns=["year", "value", "indicator_code"])
    except (ValueError, KeyError) as err:
        print(f"[Warning] Error parsing API response for {indicator_code}: {err}")
        return pd.DataFrame(columns=["year", "value", "indicator_code"])


def get_indicator_summary(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Extract the most recent observation and calculate the change from the prior period.

    Parameters:
        df: DataFrame containing at least 'year' and 'value' columns.

    Returns:
        dict: Containing 'has_data', 'latest_year', 'latest_value', 'previous_year',
              'previous_value', and 'change'.
    """
    summary: Dict[str, Any] = {
        "has_data": False,
        "latest_year": None,
        "latest_value": None,
        "previous_year": None,
        "previous_value": None,
        "change": None,
    }

    if df.empty or "value" not in df.columns or "year" not in df.columns:
        return summary

    # Filter out missing/NaN values to find actual recorded observations
    valid_df = df[pd.to_numeric(df["value"], errors="coerce").notna()].copy()
    valid_df["value"] = pd.to_numeric(valid_df["value"])
    valid_df = valid_df.sort_values(by="year", ascending=True)

    if valid_df.empty:
        return summary

    summary["has_data"] = True

    # Latest recorded observation
    latest_row = valid_df.iloc[-1]
    summary["latest_year"] = int(latest_row["year"])
    summary["latest_value"] = round(float(latest_row["value"]), 2)

    # Previous recorded observation (if available)
    if len(valid_df) >= 2:
        prev_row = valid_df.iloc[-2]
        summary["previous_year"] = int(prev_row["year"])
        summary["previous_value"] = round(float(prev_row["value"]), 2)
        summary["change"] = round(summary["latest_value"] - summary["previous_value"], 2)

    return summary


@cache_data_econ
def load_all_economic_data(
    country_code: str = "IN",
    date_range: str = "2000:2025",
) -> Dict[str, Dict[str, Any]]:
    """
    Fetch all primary economic indicators for a country with Streamlit caching.

    Returns:
        Dict mapping indicator keys ('inflation', 'unemployment', 'gdp_growth')
        to a dictionary containing metadata, time-series DataFrame, and summary stats.
    """
    results: Dict[str, Dict[str, Any]] = {}

    for key, meta in INDICATOR_METADATA.items():
        df = fetch_indicator_series(country_code, meta["code"], date_range)
        summary = get_indicator_summary(df)

        results[key] = {
            "metadata": meta,
            "data": df,
            "summary": summary,
        }

    return results
