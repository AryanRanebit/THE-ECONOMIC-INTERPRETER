"""
Test Suite for the Four Analytics Features
==========================================
Covers News Pulse (sentiment), LinkLens (correlation), Shock Radar
(anomaly detection), and Outlook Engine (trend forecast), following the
same honesty rules as GEMINI.md: no fabricated data, deterministic
methods, and explicit handling of insufficient data.
"""

import numpy as np
import pandas as pd

from modules.sentiment import (
    score_sentiment,
    sentiment_label,
    add_sentiment_scores,
    aggregate_mood,
    overall_mood,
)
from modules.correlation import (
    parse_publication_year,
    aggregate_sentiment_by_year,
    indicator_yearly_changes,
    compute_linklens,
    MIN_OVERLAP_YEARS,
)
from modules.anomaly import detect_anomalies, detect_all_anomalies
from modules.forecast import forecast_indicator, forecast_all_indicators


# ---------------------------------------------------------------------------
# News Pulse — Sentiment Analysis
# ---------------------------------------------------------------------------
def test_sentiment_scores_and_labels():
    """Clearly positive and clearly negative texts receive the right labels."""
    pos = score_sentiment("Economy surges to record growth, jobs boom and wages rise")
    assert pos["label"] == "Positive"
    assert pos["score"] > 0.05

    neg = score_sentiment("Markets crash as recession fears spark panic and layoffs")
    assert neg["label"] == "Negative"
    assert neg["score"] < -0.05

    neutral = score_sentiment("Committee meeting scheduled for Tuesday afternoon")
    assert neutral["label"] == "Neutral"

    # Empty / invalid input never crashes and reports neutral
    assert score_sentiment("")["label"] == "Neutral"
    assert score_sentiment(None)["label"] == "Neutral"


def test_sentiment_dataframe_and_mood_aggregation():
    """DataFrame augmentation adds both columns; aggregation groups by topic."""
    df = pd.DataFrame([
        {"title": "Growth soars as economy booms", "description": "Great momentum", "category": "GDP and Economic Growth"},
        {"title": "Recession fears spark panic selling", "description": "Terrible outlook", "category": "Inflation"},
        {"title": "Routine briefing held", "description": "", "category": "Inflation"},
    ])
    scored = add_sentiment_scores(df)
    assert "sentiment_score" in scored.columns
    assert "sentiment_label" in scored.columns
    assert len(scored) == 3

    mood = aggregate_mood(scored)
    assert set(mood.columns) == {"category", "article_count", "avg_score", "mood_label"}
    inflation_row = mood[mood["category"] == "Inflation"].iloc[0]
    assert inflation_row["article_count"] == 2

    overall = overall_mood(scored)
    assert overall["article_count"] == 3
    assert overall["mood_label"] in {"Positive", "Negative", "Neutral"}

    # Empty frames are safe
    empty = add_sentiment_scores(pd.DataFrame(columns=["title", "description"]))
    assert empty.empty and "sentiment_score" in empty.columns
    assert aggregate_mood(empty).empty
    assert overall_mood(empty)["mood_label"] == "No data"


def test_sentiment_label_thresholds():
    """The published ±0.05 thresholds drive the labels."""
    assert sentiment_label(0.05) == "Positive"
    assert sentiment_label(-0.05) == "Negative"
    assert sentiment_label(0.049) == "Neutral"
    assert sentiment_label(0.0) == "Neutral"


# ---------------------------------------------------------------------------
# LinkLens — Correlation
# ---------------------------------------------------------------------------
def _make_overlapping_inputs(n_years=10):
    """Synthetic news + indicator with n_years of genuine annual overlap."""
    years = list(range(2012, 2012 + n_years))
    news = pd.DataFrame({
        "published_at": [f"{y}-06-15" for y in years],
        "sentiment_score": [0.5, 0.4, 0.1, -0.3, -0.6, 0.2, 0.3, 0.1, -0.2, 0.4][:n_years],
    })
    indicator = pd.DataFrame({
        "year": list(range(2011, 2012 + n_years)),
        "value": [4.8, 5.0, 5.5, 5.8, 5.9, 6.5, 7.5, 6.0, 5.7, 5.4, 5.6][: n_years + 1],
    })
    return news, indicator


def test_linklens_computes_with_sufficient_overlap():
    """With >= MIN_OVERLAP_YEARS overlapping years, coefficients are reported."""
    news, indicator = _make_overlapping_inputs()
    result = compute_linklens(news, indicator, "Inflation (Consumer Prices)")

    assert result["has_result"] is True
    assert result["n_overlap"] >= MIN_OVERLAP_YEARS
    assert result["overlap_range"] is not None
    assert result["r_sentiment"] is not None
    assert -1.0 <= result["r_sentiment"] <= 1.0
    assert len(result["interpretation"]) == 2
    assert "causation" in result["disclaimer"].lower()


def test_linklens_honest_when_overlap_too_small():
    """Sparse recent news yields an honest 'not enough data' state, not a chart."""
    news = pd.DataFrame({
        "published_at": ["2025-02-14", "2025-01-28", "2025-01-15"],
        "sentiment_score": [0.3, -0.2, 0.1],
    })
    _, indicator = _make_overlapping_inputs()
    result = compute_linklens(news, indicator, "Inflation (Consumer Prices)")

    assert result["has_result"] is False
    assert result["r_sentiment"] is None
    assert "Not enough data" in result["reason"]
    assert result["n_overlap"] < MIN_OVERLAP_YEARS


def test_linklens_never_fabricates_periods():
    """No synthetic interpolation: every compared year exists in BOTH sources."""
    news, indicator = _make_overlapping_inputs()
    result = compute_linklens(news, indicator, "Inflation (Consumer Prices)")
    assert result["has_result"] is True

    overlap_years = set(result["overlap"]["year"].astype(int))

    # 1. Every compared year is a genuinely observed indicator year
    observed_indicator_years = set(indicator["year"].astype(int))
    assert overlap_years.issubset(observed_indicator_years)

    # 2. Every compared year has at least one real article dated in it
    article_years = {parse_publication_year(d) for d in news["published_at"]}
    assert overlap_years.issubset(article_years)

    # 3. No gaps were filled: the overlap contains exactly the intersection,
    #    nothing more (no repeated/upsampled points between sparse years)
    change_years = set(indicator_yearly_changes(indicator)["year"].astype(int))
    news_years = set(aggregate_sentiment_by_year(add_sentiment_cols(news))["year"].astype(int))
    assert overlap_years == (change_years & news_years)

    # 4. One row per year — annual resolution only, never monthly
    assert result["overlap"]["year"].is_unique


def add_sentiment_cols(df):
    """Helper: attach deterministic sentiment scores for the interpolation test."""
    return add_sentiment_scores(df.assign(title=df["published_at"], description=""))


def test_publication_year_parsing():
    """Multiple provider date formats parse; unparseable values return None."""
    assert parse_publication_year("2025-02-14") == 2025
    assert parse_publication_year("Fri, 14 Feb 2025 07:30:00 GMT") == 2025
    assert parse_publication_year("Recent") is None
    assert parse_publication_year(None) is None
    assert parse_publication_year("") is None


# ---------------------------------------------------------------------------
# Shock Radar — Anomaly Detection
# ---------------------------------------------------------------------------
def test_shock_radar_flags_unusual_movement():
    """A single sharp spike in an otherwise calm series is flagged with a note."""
    df = pd.DataFrame({
        "year": list(range(2010, 2022)),
        "value": [5.0, 5.2, 4.9, 5.1, 5.0, 5.1, 4.9, 5.0, 9.5, 5.2, 5.0, 5.1],
    })
    result = detect_anomalies(df, "Inflation (Consumer Prices)")

    assert result["has_flags"] is True
    spike_flags = [f for f in result["flags"] if f["year"] == 2018]
    assert len(spike_flags) == 1
    flag = spike_flags[0]
    assert flag["direction"] == "spike"
    assert flag["change"] == 4.5
    assert abs(flag["z_score"]) >= 2.0
    # Plain-English note mentions the year and the size of the move
    assert "2018" in flag["note"]
    assert "4.50" in flag["note"]


def test_shock_radar_calm_series_no_flags():
    """A perfectly steady trend produces no flags and a friendly reason."""
    df = pd.DataFrame({
        "year": list(range(2010, 2022)),
        "value": [5.0 + 0.1 * i for i in range(12)],  # identical +0.1 step every year
    })
    result = detect_anomalies(df, "Unemployment Rate")
    assert result["has_flags"] is False
    assert result["reason"]


def test_shock_radar_insufficient_data_is_honest():
    """Short series produce no flags with an explicit explanation."""
    df = pd.DataFrame({"year": [2022, 2023, 2024], "value": [5.0, 5.5, 9.0]})
    result = detect_anomalies(df, "Real GDP Growth")
    assert result["has_flags"] is False
    assert "at least" in result["reason"]

    empty = detect_anomalies(pd.DataFrame(columns=["year", "value"]), "X")
    assert empty["has_flags"] is False
    assert empty["reason"]


def test_shock_radar_bundle():
    """detect_all_anomalies returns one named result per indicator."""
    econ = {
        "inflation": {
            "metadata": {"name": "Inflation (Consumer Prices)"},
            "data": pd.DataFrame({"year": list(range(2010, 2022)),
                                  "value": [5.0, 5.2, 4.9, 5.1, 5.0, 5.1, 4.9, 5.0, 9.5, 5.2, 5.0, 5.1]}),
        }
    }
    results = detect_all_anomalies(econ)
    assert results["inflation"]["indicator_name"] == "Inflation (Consumer Prices)"
    assert results["inflation"]["has_flags"] is True


# ---------------------------------------------------------------------------
# Outlook Engine — Trend Forecast
# ---------------------------------------------------------------------------
def test_outlook_recovers_linear_trend():
    """On clean linear data the forecast lands on the true continuation."""
    years = list(range(2000, 2021))
    values = [2.0 + 0.3 * (y - 2000) for y in years]  # perfect line, slope 0.3
    df = pd.DataFrame({"year": years, "value": values})

    fc = forecast_indicator(df, years_ahead=3, indicator_name="Inflation (Consumer Prices)")

    assert fc["has_forecast"] is True
    assert abs(fc["slope"] - 0.3) < 0.01
    assert fc["r_squared"] > 0.99
    assert list(fc["forecast"]["year"]) == [2021, 2022, 2023]
    # Perfect fit: prediction equals the true line, tiny interval
    assert abs(fc["forecast"].iloc[0]["predicted"] - (2.0 + 0.3 * 21)) < 0.05
    assert fc["forecast"].iloc[0]["lower"] <= fc["forecast"].iloc[0]["predicted"] <= fc["forecast"].iloc[0]["upper"]


def test_outlook_interval_widens_with_horizon():
    """The prediction band widens the further ahead it looks."""
    rng = np.random.RandomState(42)
    years = list(range(2000, 2021))
    values = [2.0 + 0.2 * (y - 2000) + rng.normal(0, 0.5) for y in years]
    df = pd.DataFrame({"year": years, "value": values})

    fc = forecast_indicator(df, years_ahead=3, indicator_name="Unemployment Rate")
    widths = fc["forecast"]["upper"] - fc["forecast"]["lower"]
    assert widths.iloc[0] < widths.iloc[-1]
    assert (widths > 0).all()


def test_outlook_insufficient_data_is_honest():
    """Short series produce no forecast with an explicit reason and disclaimer."""
    df = pd.DataFrame({"year": [2023, 2024], "value": [5.0, 5.5]})
    fc = forecast_indicator(df, indicator_name="Real GDP Growth")
    assert fc["has_forecast"] is False
    assert "at least" in fc["reason"]
    assert "not investment" in fc["disclaimer"].lower()

    empty = forecast_indicator(pd.DataFrame(columns=["year", "value"]))
    assert empty["has_forecast"] is False


def test_outlook_ignores_missing_years():
    """NaN observations are skipped, never coerced to zero, before fitting."""
    df = pd.DataFrame({
        "year": [2015, 2016, 2017, 2018, 2019, 2020, 2021],
        "value": [4.0, None, 4.4, np.nan, 4.8, 5.0, 5.2],
    })
    fc = forecast_indicator(df, indicator_name="Inflation (Consumer Prices)")
    assert fc["has_forecast"] is True
    # Trend should be positive across the surviving points
    assert fc["slope"] > 0


def test_outlook_bundle():
    """forecast_all_indicators returns named results with units."""
    econ = {
        "gdp_growth": {
            "metadata": {"name": "Real GDP Growth", "unit": "% (Annual)"},
            "data": pd.DataFrame({"year": list(range(2000, 2021)),
                                  "value": [2.0 + 0.1 * (y - 2000) for y in range(2000, 2021)]}),
        }
    }
    results = forecast_all_indicators(econ)
    assert results["gdp_growth"]["has_forecast"] is True
    assert results["gdp_growth"]["unit"] == "% (Annual)"


# ---------------------------------------------------------------------------
# App integration
# ---------------------------------------------------------------------------
def test_app_exposes_new_builders():
    """app.py compiles and exposes the new chart builders and helpers."""
    import app
    assert hasattr(app, "build_linklens_chart")
    assert hasattr(app, "build_outlook_chart")
    assert hasattr(app, "compute_news_pulse")
    assert hasattr(app, "compute_shock_radar")
    assert hasattr(app, "compute_outlook")
    assert hasattr(app, "compute_linklens_bundle")
    assert hasattr(app, "SENTIMENT_EMOJIS")
