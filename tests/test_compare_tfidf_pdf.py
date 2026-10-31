"""
Tests for the four improvement features
========================================
1. TF-IDF news tagging upgrade (text_processing).
2. Country comparison helpers (modules/comparison.py).
3. PDF report export (modules/report.py).
4. Expanded countries & indicators (modules/economic_data.py).
"""

import pandas as pd
import pytest

from modules.economic_data import (
    INDICATOR_METADATA,
    SUPPORTED_COUNTRIES,
    DEFAULT_COUNTRY,
    get_indicator_summary,
)
from modules.text_processing import (
    categorize_article_text,
    categorize_article_text_tfidf,
    categorize_dataframe_tfidf,
    compute_corpus_tfidf,
    extract_key_terms,
    TOPIC_KEYWORDS,
    DEFAULT_CATEGORY,
)
from modules.comparison import build_comparison_table, align_series_for_years
from modules.analysis import (
    generate_all_interpretations,
    get_economic_mechanism_explanation,
    INDICATOR_TO_NEWS_CATEGORIES,
)


# ---------------------------------------------------------------------------
# 4a. Expanded indicators and countries
# ---------------------------------------------------------------------------
def test_expanded_indicator_metadata():
    """All six indicators have valid World Bank codes and display metadata."""
    expected = {
        "inflation",
        "unemployment",
        "gdp_growth",
        "gdp_per_capita_growth",
        "exports_gdp",
        "fdi_inflows_gdp",
    }
    assert set(INDICATOR_METADATA.keys()) == expected
    for key, meta in INDICATOR_METADATA.items():
        assert meta["code"], f"{key} missing World Bank code"
        assert "." in meta["code"], f"{key} code does not look like a World Bank indicator code"
        assert meta["name"]
        assert meta["unit"]
        assert meta["description"]


def test_expanded_country_list():
    """India remains the default; the major economies asked for are present."""
    assert DEFAULT_COUNTRY == "IN"
    for code in ["IN", "US", "CN", "GB", "DE", "JP", "AE", "SG"]:
        assert code in SUPPORTED_COUNTRIES
    assert len(SUPPORTED_COUNTRIES) == 8


def test_new_indicators_have_interpretation_support():
    """Every indicator has a news-topic mapping and mechanism explanations."""
    for key in INDICATOR_METADATA.keys():
        assert key in INDICATOR_TO_NEWS_CATEGORIES, f"{key} missing news category mapping"
        assert INDICATOR_TO_NEWS_CATEGORIES[key], f"{key} maps to no news categories"
        for direction in ["increased", "decreased", "remained steady", "insufficient data"]:
            text = get_economic_mechanism_explanation(key, direction)
            assert isinstance(text, str) and len(text) > 20


# ---------------------------------------------------------------------------
# 1. TF-IDF tagging
# ---------------------------------------------------------------------------
def test_tfidf_weights_distinctive_terms_higher():
    """At equal in-document frequency, a rare term outweighs a common one."""
    docs = [
        "repo decision today",
        "price hike today",
        "price levels today",
    ]
    maps = compute_corpus_tfidf(docs)
    assert len(maps) == 3
    # Both appear once in their own document, but "price" appears in two
    # documents and "repo" in only one, so repo's IDF is higher.
    assert maps[0]["repo"] > maps[1]["price"]


def test_tfidf_categorization_uses_weights():
    """TF-IDF ranking prefers the distinctive monetary term over generic 'price'."""
    # Article mentions generic 'price' (Inflation list) several times and the
    # distinctive 'repo rate' once; TF-IDF should score Monetary Policy higher
    # because 'price' is common across the corpus.
    docs = [
        "price price price repo rate decision by the central bank",
        "price of food and consumer goods",
        "price levels in retail markets",
    ]
    maps = compute_corpus_tfidf(docs)
    category, matched = categorize_article_text_tfidf(docs[0], maps[0])
    assert category == "Monetary Policy"
    assert "repo rate" in matched


def test_tfidf_fallback_without_corpus_matches_count_based():
    """With no TF-IDF map the classifier falls back to raw count matching."""
    text = "Vegetable food prices surge, lifting consumer retail inflation."
    assert categorize_article_text_tfidf(text, None) == categorize_article_text(text)
    assert categorize_article_text_tfidf(text, {}) == categorize_article_text(text)


def test_categorize_dataframe_tfidf_columns_and_consistency():
    """DataFrame categorization adds key_terms and keeps categories sensible."""
    df = pd.DataFrame([
        {"title": "RBI keeps repo rate unchanged", "description": "Reserve Bank MPC holds rates.", "url": "a"},
        {"title": "Retail inflation cools as food prices fall", "description": "Consumer inflation eases.", "url": "b"},
        {"title": "New metro line opens downtown", "description": "A transit project is inaugurated.", "url": "c"},
    ])
    out = categorize_dataframe_tfidf(df)
    assert "key_terms" in out.columns
    assert out.iloc[0]["category"] == "Monetary Policy"
    assert out.iloc[1]["category"] == "Inflation"
    assert out.iloc[2]["category"] == DEFAULT_CATEGORY
    # Key terms are real words from the article
    assert out.iloc[0]["key_terms"] != "None"
    assert any(term in out.iloc[0]["key_terms"] for term in ["repo", "rate", "mpc", "bank"])


def test_categorize_dataframe_tfidf_empty_and_single():
    """Empty and single-article corpora do not crash and stay consistent."""
    empty = pd.DataFrame(columns=["title", "description", "url"])
    out = categorize_dataframe_tfidf(empty)
    assert out.empty
    assert "key_terms" in out.columns

    single = pd.DataFrame([
        {"title": "Reserve Bank cuts repo rate", "description": "Monetary easing begins.", "url": "x"},
    ])
    out1 = categorize_dataframe_tfidf(single)
    assert out1.iloc[0]["category"] == "Monetary Policy"


def test_extract_key_terms():
    """Top-N extraction is sorted and bounded."""
    terms = extract_key_terms({"b": 0.5, "a": 0.5, "c": 0.9}, top_n=2)
    assert terms == ["c", "a"]  # descending weight, ties alphabetical
    assert extract_key_terms({}, top_n=3) == []
    assert extract_key_terms({"a": 1.0}, top_n=0) == []


# ---------------------------------------------------------------------------
# 2. Country comparison helpers
# ---------------------------------------------------------------------------
def _mk_indicator_data(values_by_year):
    df = pd.DataFrame({
        "year": list(values_by_year.keys()),
        "value": list(values_by_year.values()),
        "indicator_code": ["TEST"] * len(values_by_year),
    })
    return {
        "inflation": {
            "metadata": {"name": "Inflation (Consumer Prices)", "unit": "% (Annual)", "code": "FP.CPI.TOTL.ZG"},
            "data": df,
            "summary": get_indicator_summary(df),
        }
    }


def test_build_comparison_table_values_and_missing():
    """Latest values carry their own reporting year; missing stays missing."""
    data = {
        "IN": _mk_indicator_data({2022: 5.0, 2023: 6.0}),
        "US": _mk_indicator_data({2022: 3.0, 2023: None}),
    }
    table = build_comparison_table(data, {"IN": "India", "US": "United States"})
    row = table.iloc[0]
    assert row["indicator_name"] == "Inflation (Consumer Prices)"
    assert row["India Value"] == 6.0
    assert row["India Year"] == 2023
    # US latest valid observation is 2022 (None in 2023 is not zero-filled)
    assert row["United States Value"] == 3.0
    assert row["United States Year"] == 2022


def test_align_series_for_years_keeps_gaps():
    """Union of years; unobserved country-years stay NaN (never zero)."""
    a = pd.DataFrame({"year": [2021, 2022], "value": [1.0, 2.0]})
    b = pd.DataFrame({"year": [2022, 2023], "value": [3.0, 4.0]})
    aligned = align_series_for_years(a, b)
    assert list(aligned["year"]) == [2021, 2022, 2023]
    assert pd.isna(aligned.loc[aligned["year"] == 2021, "value_b"]).all()
    assert pd.isna(aligned.loc[aligned["year"] == 2023, "value_a"]).all()
    assert aligned.loc[aligned["year"] == 2022, "value_a"].iloc[0] == 2.0
    assert aligned.loc[aligned["year"] == 2022, "value_b"].iloc[0] == 3.0


def test_align_series_empty_inputs():
    """Two empty series produce an empty aligned frame with stable columns."""
    aligned = align_series_for_years(pd.DataFrame(), pd.DataFrame())
    assert list(aligned.columns) == ["year", "value_a", "value_b"]
    assert aligned.empty


# ---------------------------------------------------------------------------
# 3. PDF report export
# ---------------------------------------------------------------------------
def test_pdf_report_builds_and_mentions_country():
    """The report is a real PDF whose text layer mentions the country and data."""
    from modules.report import build_pdf_report, FPDF_AVAILABLE
    if not FPDF_AVAILABLE:
        pytest.skip("fpdf2 not installed")

    econ = _mk_indicator_data({2022: 5.0, 2023: 6.5})
    interps = generate_all_interpretations(econ, pd.DataFrame(columns=["category", "title", "source", "url", "published_at"]))
    articles = pd.DataFrame({"category": ["Inflation", "Inflation", "Employment"]})

    pdf_bytes = build_pdf_report("India", econ, interps, articles)
    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes.startswith(b"%PDF")
    assert len(pdf_bytes) > 1000  # a real multi-section document, not an empty shell


def test_pdf_report_handles_missing_data():
    """No indicator data -> report still builds with honest 'no observations' text."""
    from modules.report import build_pdf_report, FPDF_AVAILABLE
    if not FPDF_AVAILABLE:
        pytest.skip("fpdf2 not installed")

    empty_item = {
        "inflation": {
            "metadata": {"name": "Inflation (Consumer Prices)", "unit": "% (Annual)", "code": "FP.CPI.TOTL.ZG"},
            "data": pd.DataFrame(columns=["year", "value", "indicator_code"]),
            "summary": {"has_data": False},
        }
    }
    interps = generate_all_interpretations(empty_item, pd.DataFrame(columns=["category"]))
    pdf_bytes = build_pdf_report("India", empty_item, interps, None)
    assert pdf_bytes.startswith(b"%PDF")


def test_pdf_report_unicode_safe():
    """Non-ASCII characters in titles do not crash the core-font PDF."""
    from modules.report import build_pdf_report, FPDF_AVAILABLE
    if not FPDF_AVAILABLE:
        pytest.skip("fpdf2 not installed")

    econ = _mk_indicator_data({2023: 4.2})
    interps = generate_all_interpretations(econ, pd.DataFrame(columns=["category", "title", "source", "url", "published_at"]))
    articles = pd.DataFrame({"category": ["Inflation"]})
    pdf_bytes = build_pdf_report("India — ₹ test “quotes”", econ, interps, articles)
    assert pdf_bytes.startswith(b"%PDF")
