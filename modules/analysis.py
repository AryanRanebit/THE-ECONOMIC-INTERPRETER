"""
Economic Interpretation & Analysis Module
=========================================
Generates evidence-based, deterministic educational explanations connecting
observed indicator trends with retrieved economic news topics.

Adheres strictly to GEMINI.md Section 4 (Feature D):
1. Observed trend: Calculated from actual World Bank observations.
2. Relevant news: Retrieved articles matching related topic categories.
3. Possible explanation: Educational economic mechanisms connecting topic and indicator.
4. Limitations & uncertainty: Explicit disclaimers against assuming causation from correlation.
"""

from typing import Any, Dict, List, Optional
import pandas as pd

# Mapping between economic indicators and related news categories
INDICATOR_TO_NEWS_CATEGORIES: Dict[str, List[str]] = {
    "inflation": ["Inflation", "Monetary Policy"],
    "unemployment": ["Employment"],
    "gdp_growth": ["GDP and Economic Growth", "Monetary Policy"],
}

# General analytical limitation statement applied across interpretations
STANDARD_LIMITATION = (
    "Analytical Boundaries & Limitations: World Bank observations represent annual national "
    "aggregates, whereas retrieved news reflects recent short-term events. Correlation in timing "
    "does not establish direct causation. Numerous unobserved factors—including international trade shocks, "
    "currency exchange fluctuations, fiscal policies, and weather anomalies—simultaneously influence "
    "macroeconomic trends beyond the events covered in these specific news articles."
)


def get_trend_direction(change: Optional[float], threshold: float = 0.05) -> str:
    """
    Determine the qualitative direction of an indicator change.

    Parameters:
        change: Period-over-period difference (latest - previous).
        threshold: Small margin within which change is considered steady.

    Returns:
        str: 'increased', 'decreased', or 'remained steady'.
    """
    if change is None or pd.isna(change):
        return "insufficient data"
    if change > threshold:
        return "increased"
    elif change < -threshold:
        return "decreased"
    else:
        return "remained steady"


def get_economic_mechanism_explanation(indicator_key: str, direction: str) -> str:
    """
    Provide textbook economic mechanism explanations connecting trends to foundational principles.
    """
    mechanisms = {
        "inflation": {
            "increased": (
                "Possible Economic Mechanism: Inflation typically accelerates when aggregate demand "
                "outpaces supply capacity (demand-pull), or when input costs—such as petroleum, food commodities, "
                "or imported materials—rise sharply (cost-push). If businesses pass these rising costs onto consumers, "
                "the headline Consumer Price Index registers faster growth."
            ),
            "decreased": (
                "Possible Economic Mechanism: Inflation moderation often reflects cooling food or fuel prices, "
                "improved domestic supply chains, or the lagged impact of past central bank monetary tightening "
                "(higher interest rates dampening credit expansion). As price increases slow down, purchasing power stabilizes."
            ),
            "remained steady": (
                "Possible Economic Mechanism: Steady inflation indicates balanced price conditions where cost increases "
                "in certain consumer sectors are offset by price stability or discounts in others, aligning with steady supply and demand."
            ),
            "insufficient data": "Insufficient historical data available to evaluate macroeconomic mechanisms.",
        },
        "unemployment": {
            "increased": (
                "Possible Economic Mechanism: An uptick in unemployment can indicate cyclical softening in economic "
                "activity, reduced business hiring, or seasonal transitions in informal/agricultural labor markets "
                "where work availability fluctuates after harvest seasons."
            ),
            "decreased": (
                "Possible Economic Mechanism: A decline in the unemployment rate suggests rising labor absorption, "
                "supported by business expansion, service sector recruitment, or public infrastructure investments "
                "that create direct and indirect jobs."
            ),
            "remained steady": (
                "Possible Economic Mechanism: A steady unemployment rate suggests that the rate of new job creation is "
                "broadly keeping pace with the inflow of new job-seekers entering the active labor force."
            ),
            "insufficient data": "Insufficient historical data available to evaluate labor market mechanisms.",
        },
        "gdp_growth": {
            "increased": (
                "Possible Economic Mechanism: Accelerating real GDP growth typically reflects strong domestic consumption, "
                "elevated capital expenditure (capex) in infrastructure and manufacturing, and robust service exports, "
                "which expand the total inflation-adjusted output of goods and services."
            ),
            "decreased": (
                "Possible Economic Mechanism: Moderating GDP growth often reflects tighter domestic credit conditions, "
                "subdued external export demand from key trading partners, or a statistical high-base effect from "
                "an exceptionally strong prior reporting year."
            ),
            "remained steady": (
                "Possible Economic Mechanism: Steady GDP growth indicates consistent economic expansion, maintaining "
                "predictable output growth year-over-year."
            ),
            "insufficient data": "Insufficient historical data available to evaluate growth mechanisms.",
        },
    }

    return mechanisms.get(indicator_key, {}).get(
        direction,
        "General economic principles suggest that macroeconomic shifts are driven by changing balances in supply, demand, and fiscal or monetary policies."
    )


def generate_single_interpretation(
    indicator_key: str,
    indicator_info: Dict[str, Any],
    categorized_news_df: pd.DataFrame,
) -> Dict[str, Any]:
    """
    Generate an interpretation for a single economic indicator based on actual observations
    and matching retrieved news topics.
    """
    meta = indicator_info.get("metadata", {})
    summary = indicator_info.get("summary", {})

    name = meta.get("name", indicator_key.title())
    unit = meta.get("unit", "%")

    if not summary.get("has_data") or summary.get("latest_value") is None or pd.isna(summary.get("latest_value")):
        return {
            "indicator_key": indicator_key,
            "indicator_name": name,
            "has_data": False,
            "observed_trend": f"No historical observations available for {name}.",
            "relevant_news": [],
            "possible_explanation": "Cannot generate explanation due to absent indicator data.",
            "limitations": STANDARD_LIMITATION,
        }

    latest_val = summary["latest_value"]
    latest_yr = summary["latest_year"]
    prev_val = summary.get("previous_value")
    prev_yr = summary.get("previous_year")
    change = summary.get("change")
    direction = get_trend_direction(change)

    # 1. Observed Trend (Fact-based statement)
    if (
        prev_val is not None
        and not pd.isna(prev_val)
        and prev_yr is not None
        and change is not None
        and not pd.isna(change)
    ):
        observed_trend = (
            f"Observed Trend: {name} stood at {latest_val:.2f}{unit} in {latest_yr}. "
            f"Compared to {prev_val:.2f}{unit} in {prev_yr}, the indicator has {direction} "
            f"by {abs(change):.2f} percentage points."
        )
    else:
        observed_trend = f"Observed Trend: Latest recorded value for {name} is {latest_val:.2f}{unit} in {latest_yr}."

    # 2. Relevant News Matching
    matched_articles: List[Dict[str, str]] = []
    if not categorized_news_df.empty and "category" in categorized_news_df.columns:
        relevant_categories = INDICATOR_TO_NEWS_CATEGORIES.get(indicator_key, [])
        filtered_news = categorized_news_df[categorized_news_df["category"].isin(relevant_categories)]

        for _, row in filtered_news.head(3).iterrows():
            url_val = row.get("url", "")
            clean_url = str(url_val).strip() if pd.notna(url_val) and str(url_val).strip().lower() != "none" else ""
            matched_articles.append({
                "title": str(row.get("title", "")),
                "source": str(row.get("source", "")),
                "url": clean_url,
                "category": str(row.get("category", "")),
                "published_at": str(row.get("published_at", "")),
            })

    # 3. Possible Economic Mechanism
    possible_explanation = get_economic_mechanism_explanation(indicator_key, direction)

    return {
        "indicator_key": indicator_key,
        "indicator_name": name,
        "has_data": True,
        "latest_year": latest_yr,
        "latest_value": latest_val,
        "previous_year": prev_yr,
        "previous_value": prev_val,
        "change": change,
        "direction": direction,
        "observed_trend": observed_trend,
        "relevant_news": matched_articles,
        "possible_explanation": possible_explanation,
        "limitations": STANDARD_LIMITATION,
    }


def generate_all_interpretations(
    economic_data: Dict[str, Dict[str, Any]],
    categorized_news_df: pd.DataFrame,
) -> Dict[str, Dict[str, Any]]:
    """
    Generate comprehensive educational interpretations for all primary indicators.

    Returns:
        Dict mapping indicator keys ('inflation', 'unemployment', 'gdp_growth')
        to their structured 4-part interpretation dictionary.
    """
    interpretations: Dict[str, Dict[str, Any]] = {}

    for key, info in economic_data.items():
        interpretations[key] = generate_single_interpretation(
            indicator_key=key,
            indicator_info=info,
            categorized_news_df=categorized_news_df,
        )

    return interpretations
