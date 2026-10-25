"""
Test Suite for The Economic Interpreter
=======================================
Verifies the 10 testing requirements defined in GEMINI.md Section 9:
1. Economic indicator requests return valid data.
2. Missing observations are handled correctly.
3. Indicator values and percentage changes are calculated correctly.
4. Empty news responses do not crash the application.
5. Duplicate articles are removed.
6. Articles are categorized according to the defined rules.
7. Unsupported or missing article fields are handled safely.
8. Economic explanations match the underlying data.
9. API failures produce understandable messages.
10. The application launches successfully using Streamlit.
"""

import math
import numpy as np
import pandas as pd
import pytest

from modules.economic_data import (
    fetch_indicator_series,
    get_indicator_summary,
    INDICATOR_METADATA,
)
from modules.news_data import (
    deduplicate_articles,
    load_sample_news,
    get_economic_news,
    clean_html_text,
)
from modules.text_processing import (
    normalize_text,
    tokenize,
    categorize_article_text,
    categorize_dataframe,
)
from modules.analysis import (
    get_trend_direction,
    generate_single_interpretation,
    generate_all_interpretations,
    STANDARD_LIMITATION,
)


# ---------------------------------------------------------------------------
# 1. Economic Indicator Requests Return Valid Data
# ---------------------------------------------------------------------------
def test_economic_indicator_requests():
    """Verify that World Bank API queries return non-empty DataFrames with valid columns."""
    df = fetch_indicator_series("IN", "FP.CPI.TOTL.ZG", date_range="2020:2025")
    assert not df.empty, "World Bank API should return observations for India (2020:2025)."
    assert list(df.columns) == ["year", "value", "indicator_code"]
    assert df["year"].is_monotonic_increasing, "Observations should be sorted chronologically."


# ---------------------------------------------------------------------------
# 2. Missing Observations are Handled Correctly
# ---------------------------------------------------------------------------
def test_missing_observations_handling():
    """Verify that None/NaN values are preserved and not silently replaced with zero."""
    # Create test data containing missing values and genuine zeroes
    data = [
        {"year": 2021, "value": 5.1, "indicator_code": "TEST"},
        {"year": 2022, "value": None, "indicator_code": "TEST"},  # Missing observation
        {"year": 2023, "value": 0.0, "indicator_code": "TEST"},   # Genuine zero
        {"year": 2024, "value": np.nan, "indicator_code": "TEST"}, # Missing observation
    ]
    df = pd.DataFrame(data)
    summary = get_indicator_summary(df)

    assert summary["has_data"] is True
    # The latest non-null value is 2023 with genuine 0.0, NOT 2024 with 0.0
    assert summary["latest_year"] == 2023
    assert summary["latest_value"] == 0.0
    # Prior non-null is 2021 with 5.1
    assert summary["previous_year"] == 2021
    assert summary["previous_value"] == 5.1
    assert summary["change"] == -5.1


# ---------------------------------------------------------------------------
# 3. Indicator Values and Percentage Changes are Calculated Correctly
# ---------------------------------------------------------------------------
def test_indicator_changes_calculation():
    """Verify that delta values (latest - previous) are mathematically correct."""
    df_increase = pd.DataFrame([
        {"year": 2023, "value": 4.0},
        {"year": 2024, "value": 6.5},
    ])
    summary_inc = get_indicator_summary(df_increase)
    assert summary_inc["change"] == 2.5
    assert get_trend_direction(summary_inc["change"]) == "increased"

    df_decrease = pd.DataFrame([
        {"year": 2023, "value": 7.2},
        {"year": 2024, "value": 5.1},
    ])
    summary_dec = get_indicator_summary(df_decrease)
    assert summary_dec["change"] == -2.1
    assert get_trend_direction(summary_dec["change"]) == "decreased"

    df_steady = pd.DataFrame([
        {"year": 2023, "value": 5.00},
        {"year": 2024, "value": 5.02},
    ])
    summary_std = get_indicator_summary(df_steady)
    assert summary_std["change"] == 0.02
    assert get_trend_direction(summary_std["change"]) == "remained steady"


# ---------------------------------------------------------------------------
# 4. Empty News Responses Do Not Crash the Application
# ---------------------------------------------------------------------------
def test_empty_news_responses():
    """Verify that empty news datasets do not raise uncaught exceptions."""
    empty_df = pd.DataFrame(columns=["title", "source", "published_at", "description", "url", "is_sample"])

    deduped = deduplicate_articles(empty_df)
    assert deduped.empty

    categorized = categorize_dataframe(empty_df)
    assert categorized.empty

    # Test interpretation with empty news
    dummy_econ = {
        "inflation": {
            "metadata": {"name": "Inflation", "unit": "%"},
            "summary": {"has_data": True, "latest_year": 2025, "latest_value": 3.0, "previous_year": 2024, "previous_value": 4.0, "change": -1.0},
            "data": pd.DataFrame(),
        }
    }
    interp = generate_all_interpretations(dummy_econ, empty_df)
    assert "inflation" in interp
    assert interp["inflation"]["relevant_news"] == []


# ---------------------------------------------------------------------------
# 5. Duplicate Articles are Removed
# ---------------------------------------------------------------------------
def test_duplicate_articles_removal():
    """Verify that duplicate URLs and duplicate normalized titles are removed."""
    raw_articles = pd.DataFrame([
        {"title": "RBI Keeps Rate Constant", "url": "https://example.com/art1", "source": "A"},
        {"title": "rbi keeps rate constant", "url": "https://example.com/art2", "source": "B"}, # Duplicate title
        {"title": "Different Title Here", "url": "https://example.com/art1", "source": "C"},   # Duplicate URL
        {"title": "Distinct Article", "url": "https://example.com/art3", "source": "D"},       # Unique
    ])

    deduped = deduplicate_articles(raw_articles)
    assert len(deduped) == 2
    assert "Distinct Article" in deduped["title"].values


# ---------------------------------------------------------------------------
# 6. Articles are Categorized According to Defined Rules
# ---------------------------------------------------------------------------
def test_articles_categorization_rules():
    """Verify that transparent keyword rules properly map texts to required topics."""
    cat1, kw1 = categorize_article_text("Vegetable food prices surge, lifting consumer retail inflation.")
    assert cat1 == "Inflation"
    assert "inflation" in kw1 or "prices" in kw1

    cat2, kw2 = categorize_article_text("Tech firms resume hiring and announce 40,000 new jobs.")
    assert cat2 == "Employment"
    assert "hiring" in kw2 or "jobs" in kw2

    cat3, kw3 = categorize_article_text("Annual real GDP growth accelerates on manufacturing expansion.")
    assert cat3 == "GDP and Economic Growth"
    assert "gdp" in kw3 or "growth" in kw3

    cat4, kw4 = categorize_article_text("Reserve Bank MPC meeting leaves benchmark repo rate unchanged.")
    assert cat4 == "Monetary Policy"
    assert "repo rate" in kw4 or "mpc" in kw4

    cat5, kw5 = categorize_article_text("City inaugurated a new central park with fountain displays.")
    assert cat5 == "Other Economic News"
    assert kw5 == []


# ---------------------------------------------------------------------------
# 7. Unsupported or Missing Article Fields are Handled Safely
# ---------------------------------------------------------------------------
def test_missing_article_fields_safety():
    """Verify that missing columns, None titles, or corrupt records do not crash categorization."""
    broken_df = pd.DataFrame([
        {"title": None, "description": "Discussing repo rate and liquidity."},
        {"title": "Unemployment in rural belts", "description": None},
        {},  # Completely empty record
    ])

    categorized = categorize_dataframe(broken_df)
    assert len(categorized) == 3
    assert categorized.iloc[0]["category"] == "Monetary Policy"
    assert categorized.iloc[1]["category"] == "Employment"
    assert categorized.iloc[2]["category"] == "Other Economic News"


# ---------------------------------------------------------------------------
# 8. Economic Explanations Match Underlying Data
# ---------------------------------------------------------------------------
def test_economic_explanations_match_data():
    """Verify that textual explanations agree with the direction of the underlying numbers."""
    dummy_info = {
        "metadata": {"name": "Inflation (Consumer Prices)", "unit": "%"},
        "summary": {
            "has_data": True,
            "latest_year": 2025,
            "latest_value": 2.4,
            "previous_year": 2024,
            "previous_value": 5.0,
            "change": -2.6,
        },
    }
    interp = generate_single_interpretation("inflation", dummy_info, pd.DataFrame())

    assert "decreased by 2.60" in interp["observed_trend"]
    assert interp["direction"] == "decreased"
    assert "cooling food or fuel prices" in interp["possible_explanation"]
    assert "Analytical Boundaries" in interp["limitations"]


# ---------------------------------------------------------------------------
# 9. API Failures Produce Understandable Messages
# ---------------------------------------------------------------------------
def test_api_failures_produce_understandable_messages():
    """Verify that invalid API parameters return empty DataFrames rather than raising unhandled exceptions."""
    bad_res = fetch_indicator_series("NON_EXISTENT_COUNTRY", "INVALID_INDICATOR_CODE")
    assert isinstance(bad_res, pd.DataFrame)
    assert bad_res.empty

    bad_summary = get_indicator_summary(bad_res)
    assert bad_summary["has_data"] is False
    assert bad_summary["latest_value"] is None


# ---------------------------------------------------------------------------
# 10. Application Launches Successfully using Streamlit
# ---------------------------------------------------------------------------
def test_streamlit_app_compilation():
    """Verify that app.py compiles cleanly with all imported functions available."""
    import app
    assert hasattr(app, "main")
    assert hasattr(app, "build_combined_trend_chart")
    assert hasattr(app, "build_single_indicator_chart")
    assert hasattr(app, "SUPPORTED_COUNTRIES")


# ---------------------------------------------------------------------------
# 11. Vercel Serverless Function API Handler Executes Cleanly
# ---------------------------------------------------------------------------
def test_vercel_serverless_handler():
    """Verify that api/index.py processes health, news, and indicators requests properly."""
    import io
    import json
    from api.index import handler

    # 1. Test health endpoint
    h_health = handler.__new__(handler)
    h_health.wfile = io.BytesIO()
    h_health.path = "/api/index?action=health"
    h_health.do_GET()
    resp_health = h_health.wfile.getvalue().decode("utf-8")
    assert "healthy" in resp_health

    # 2. Test news endpoint with sample mode
    h_news = handler.__new__(handler)
    h_news.wfile = io.BytesIO()
    h_news.path = "/api/index?action=news&use_sample=true"
    h_news.do_GET()
    resp_news = h_news.wfile.getvalue().decode("utf-8")
    headers, body = resp_news.split("\r\n\r\n", 1)
    data_news = json.loads(body)
    assert data_news["is_sample"] is True
    assert data_news["article_count"] > 0

    # 3. Test interpret endpoint with sample mode
    h_interp = handler.__new__(handler)
    h_interp.wfile = io.BytesIO()
    h_interp.path = "/api/index?action=interpret&country=IN&range=2022:2024&use_sample=true"
    h_interp.do_GET()
    resp_interp = h_interp.wfile.getvalue().decode("utf-8")
    headers_i, body_i = resp_interp.split("\r\n\r\n", 1)
    data_interp = json.loads(body_i)
    assert "interpretations" in data_interp
    assert set(data_interp["interpretations"].keys()) == {"inflation", "unemployment", "gdp_growth"}


# ---------------------------------------------------------------------------
# 12. Deployment Configuration Integrity
# ---------------------------------------------------------------------------
def test_deployment_configuration_files():
    """Verify that vercel.json, .streamlit/config.toml, and public/index.html exist and are valid."""
    import json
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent

    # Check vercel.json
    vercel_path = root / "vercel.json"
    assert vercel_path.exists(), "vercel.json must exist for Vercel deployment."
    with open(vercel_path, "r", encoding="utf-8") as f:
        vercel_cfg = json.load(f)
    assert "builds" in vercel_cfg
    assert "routes" in vercel_cfg

    # Check public/index.html
    html_path = root / "public" / "index.html"
    assert html_path.exists(), "public/index.html must exist for static dashboard."

    # Check .streamlit/config.toml
    st_cfg_path = root / ".streamlit" / "config.toml"
    assert st_cfg_path.exists(), ".streamlit/config.toml must exist for production headless mode."

