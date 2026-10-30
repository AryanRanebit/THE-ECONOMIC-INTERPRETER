"""
LinkLens — News-to-Economy Correlation Module
=============================================
Explores whether the tone and volume of economic news move together with
changes in macroeconomic indicators.

Method (deliberately simple and explainable):
1. Parse each article's publication date and group articles by calendar
   year, computing the average News Pulse sentiment score and the article
   count per year.
2. Compute the year-over-year change of each indicator.
3. Where years overlap, compute the Pearson correlation coefficient (r).

Honesty rules (in accordance with GEMINI.md):
- Live news feeds usually cover only the last few days, while World Bank
  indicators are annual. When fewer than MIN_OVERLAP_YEARS overlap, LinkLens
  says so plainly instead of producing a meaningless coefficient.
- News is aggregated DOWN to the annual periods the World Bank actually
  reports. Annual indicator values are never upsampled, repeated, or
  interpolated into months: every point in the comparison is a genuinely
  observed period. The overlap count and time range are always displayed
  next to any result.
- Every result carries the reminder that correlation does not imply
  causation, in plain English.
"""

from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd

# Minimum overlapping observed periods (years) before a correlation is
# statistically presentable. Below this, LinkLens shows an honest
# "not enough data yet" state instead of a chart.
MIN_OVERLAP_YEARS = 8

CORRELATION_DISCLAIMER = (
    "Correlation does not imply causation: even a strong statistical link between news tone "
    "and an indicator does not prove one causes the other. Both may be driven by third factors "
    "(policy decisions, global events, data revisions). Treat LinkLens as a conversation "
    "starter, not evidence."
)


def parse_publication_year(raw_date: Any) -> Optional[int]:
    """
    Extract a 4-digit year from the many date formats news providers use.

    Handles 'YYYY-MM-DD', RFC-822 RSS dates ('Fri, 14 Feb 2025 07:30:00 GMT'),
    and returns None for unparseable values such as 'Recent'.
    """
    if raw_date is None or (isinstance(raw_date, float) and np.isnan(raw_date)):
        return None

    text = str(raw_date).strip()
    if not text or text.lower() == "none":
        return None

    parsed = pd.to_datetime(text, errors="coerce", utc=True)
    if pd.isna(parsed):
        return None

    year = int(parsed.year)
    # Sanity guard against parsing accidents far outside a plausible news window
    if year < 1990 or year > 2100:
        return None
    return year


def aggregate_sentiment_by_year(df: pd.DataFrame) -> pd.DataFrame:
    """
    Group sentiment-scored articles into yearly averages and counts.

    Parameters:
        df: News DataFrame with 'published_at' and 'sentiment_score' columns.

    Returns:
        pd.DataFrame with ['year', 'avg_sentiment', 'article_count'], sorted
        ascending by year. Articles with unparseable dates are excluded.
    """
    columns = ["year", "avg_sentiment", "article_count"]

    if df.empty or "sentiment_score" not in df.columns or "published_at" not in df.columns:
        return pd.DataFrame(columns=columns)

    df_copy = df.copy()
    df_copy["_year"] = df_copy["published_at"].apply(parse_publication_year)
    df_copy = df_copy.dropna(subset=["_year"])

    if df_copy.empty:
        return pd.DataFrame(columns=columns)

    df_copy["_year"] = df_copy["_year"].astype(int)
    grouped = (
        df_copy.groupby("_year")["sentiment_score"]
        .agg(avg_sentiment="mean", article_count="count")
        .reset_index()
        .rename(columns={"_year": "year"})
        .sort_values(by="year")
        .reset_index(drop=True)
    )
    grouped["avg_sentiment"] = grouped["avg_sentiment"].round(3)
    return grouped[columns]


def indicator_yearly_changes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute year-over-year changes for one indicator series.

    Returns:
        pd.DataFrame with ['year', 'value', 'change']; the first recorded
        year has a NaN change and is dropped from the returned frame.
    """
    columns = ["year", "value", "change"]
    if df.empty or "year" not in df.columns or "value" not in df.columns:
        return pd.DataFrame(columns=columns)

    valid = df.dropna(subset=["value"]).sort_values(by="year").reset_index(drop=True)
    valid = valid[["year", "value"]].copy()
    valid["change"] = valid["value"].diff()
    valid = valid.dropna(subset=["change"]).reset_index(drop=True)
    valid["year"] = valid["year"].astype(int)
    return valid[columns]


def _pearson(x: pd.Series, y: pd.Series) -> Optional[float]:
    """Pearson r with guards against zero variance and NaNs."""
    if len(x) < 2 or float(x.std()) == 0.0 or float(y.std()) == 0.0:
        return None
    r = float(np.corrcoef(x, y)[0, 1])
    if np.isnan(r):
        return None
    return round(r, 3)


def describe_correlation(r: Optional[float], what: str, indicator_name: str) -> str:
    """Plain-English reading of one correlation coefficient."""
    if r is None:
        return f"The available data is too flat to measure a link between {what} and {indicator_name}."

    strength = "weak"
    if abs(r) >= 0.7:
        strength = "strong"
    elif abs(r) >= 0.4:
        strength = "moderate"

    direction = "together" if r > 0 else "in opposite directions"
    return (
        f"Over the overlapping years, {what} and changes in {indicator_name} show a "
        f"{strength} link (r = {r:+.2f}) — they tended to move {direction}."
    )


def compute_linklens(
    news_df: pd.DataFrame,
    indicator_df: pd.DataFrame,
    indicator_name: str,
) -> Dict[str, Any]:
    """
    Correlate news sentiment/volume with year-over-year indicator changes.

    Parameters:
        news_df: News DataFrame with 'published_at' and 'sentiment_score'.
        indicator_df: Indicator DataFrame with 'year' and 'value'.
        indicator_name: Human-readable indicator name.

    Returns:
        dict with:
            - 'has_result': True when enough years overlap to report r.
            - 'n_overlap': number of overlapping years.
            - 'overlap_range': 'YYYY–YYYY' span of the overlapping years,
              or None when there is no overlap.
            - 'overlap': merged per-year DataFrame (year, avg_sentiment,
              article_count, indicator_change). Contains only genuinely
              observed periods — never interpolated or repeated points.
            - 'r_sentiment', 'r_volume': Pearson coefficients or None.
            - 'interpretation': list of plain-English sentences.
            - 'reason': explanation when has_result is False.
            - 'disclaimer': CORRELATION_DISCLAIMER.
    """
    result: Dict[str, Any] = {
        "has_result": False,
        "n_overlap": 0,
        "overlap_range": None,
        "overlap": pd.DataFrame(columns=["year", "avg_sentiment", "article_count", "indicator_change"]),
        "r_sentiment": None,
        "r_volume": None,
        "interpretation": [],
        "reason": "",
        "disclaimer": CORRELATION_DISCLAIMER,
    }

    yearly_news = aggregate_sentiment_by_year(news_df)
    changes = indicator_yearly_changes(indicator_df)

    if yearly_news.empty:
        result["reason"] = (
            "None of the current articles carry a usable publication date, so LinkLens "
            "cannot line the news up with the historical indicator timeline."
        )
        return result

    if changes.empty:
        result["reason"] = f"No recorded {indicator_name} observations are available to compare against."
        return result

    merged = pd.merge(
        yearly_news,
        changes[["year", "change"]].rename(columns={"change": "indicator_change"}),
        on="year",
        how="inner",
    ).sort_values(by="year").reset_index(drop=True)

    result["n_overlap"] = int(len(merged))
    result["overlap"] = merged
    if not merged.empty:
        result["overlap_range"] = f"{int(merged['year'].min())}–{int(merged['year'].max())}"

    if len(merged) < MIN_OVERLAP_YEARS:
        years_seen = ", ".join(str(int(y)) for y in merged["year"]) if not merged.empty else "none"
        result["reason"] = (
            f"Not enough data yet to estimate this relationship: the current news covers "
            f"{len(merged)} calendar year(s) ({years_seen}), while {indicator_name} is reported "
            f"annually. LinkLens only compares periods that genuinely overlap — it never stretches "
            f"annual data into months — and needs at least {MIN_OVERLAP_YEARS} overlapping years "
            f"before a correlation is meaningful. This is a data-coverage limit, not a finding."
        )
        return result

    r_sent = _pearson(merged["avg_sentiment"], merged["indicator_change"])
    r_vol = _pearson(merged["article_count"], merged["indicator_change"])

    result["has_result"] = True
    result["r_sentiment"] = r_sent
    result["r_volume"] = r_vol
    result["interpretation"] = [
        describe_correlation(r_sent, "average news sentiment", indicator_name),
        describe_correlation(r_vol, "news volume (number of articles)", indicator_name),
    ]
    return result


def compute_all_linklens(
    news_df: pd.DataFrame,
    economic_data: Dict[str, Dict[str, Any]],
) -> Dict[str, Dict[str, Any]]:
    """
    Run LinkLens for every indicator against the current news bundle.

    Returns:
        Dict mapping indicator keys to compute_linklens results, with
        'indicator_name' added for display.
    """
    results: Dict[str, Dict[str, Any]] = {}
    for key, item in economic_data.items():
        name = item.get("metadata", {}).get("name", key.title())
        res = compute_linklens(
            news_df=news_df,
            indicator_df=item.get("data", pd.DataFrame()),
            indicator_name=name,
        )
        res["indicator_name"] = name
        results[key] = res
    return results
