import sys
import os
import pandas as pd

# Add workspace to path
sys.path.insert(0, os.getcwd())

from modules.analysis import (
    get_trend_direction,
    get_economic_mechanism_explanation,
    generate_single_interpretation,
    generate_all_interpretations,
    STANDARD_LIMITATION,
    INDICATOR_TO_NEWS_CATEGORIES,
)

results = []

def record(test_name, condition, details=""):
    status = "PASS" if condition else "FAIL"
    results.append((test_name, status, details))
    if not condition:
        print(f"FAILED: {test_name} - {details}")

# -------------------------------------------------------------
# Test 1: Trend direction determination (Threshold testing)
# -------------------------------------------------------------
record("Direction: Positive (> 0.05)", get_trend_direction(0.12) == "increased", "0.12 -> increased")
record("Direction: Negative (< -0.05)", get_trend_direction(-0.25) == "decreased", "-0.25 -> decreased")
record("Direction: Stable positive", get_trend_direction(0.03) == "remained steady", "0.03 -> remained steady")
record("Direction: Stable negative", get_trend_direction(-0.04) == "remained steady", "-0.04 -> remained steady")
record("Direction: Zero change", get_trend_direction(0.0) == "remained steady", "0.0 -> remained steady")
record("Direction: None input", get_trend_direction(None) == "insufficient data", "None -> insufficient data")

# -------------------------------------------------------------
# Test 2: Case A - Increasing Indicator (Inflation)
# -------------------------------------------------------------
info_increasing = {
    "metadata": {"name": "Inflation (Consumer Prices)", "unit": "%"},
    "summary": {
        "has_data": True,
        "latest_year": 2024,
        "latest_value": 6.5,
        "previous_year": 2023,
        "previous_value": 4.4,
        "change": 2.1,
    },
}
interp_inc = generate_single_interpretation("inflation", info_increasing, pd.DataFrame())
record("Increasing: Direction field", interp_inc["direction"] == "increased")
record("Increasing: Observed trend wording", "increased by 2.10 percentage points" in interp_inc["observed_trend"])
record("Increasing: Mechanism text", "demand-pull" in interp_inc["possible_explanation"] or "input costs" in interp_inc["possible_explanation"])
record("Increasing: Limitations included", interp_inc["limitations"] == STANDARD_LIMITATION)

# -------------------------------------------------------------
# Test 3: Case B - Decreasing Indicator (Unemployment)
# -------------------------------------------------------------
info_decreasing = {
    "metadata": {"name": "Unemployment Rate", "unit": "%"},
    "summary": {
        "has_data": True,
        "latest_year": 2024,
        "latest_value": 4.1,
        "previous_year": 2023,
        "previous_value": 5.3,
        "change": -1.2,
    },
}
interp_dec = generate_single_interpretation("unemployment", info_decreasing, pd.DataFrame())
record("Decreasing: Direction field", interp_dec["direction"] == "decreased")
record("Decreasing: Observed trend wording", "decreased by 1.20 percentage points" in interp_dec["observed_trend"])
record("Decreasing: Mechanism text", "labor absorption" in interp_dec["possible_explanation"] or "recruitment" in interp_dec["possible_explanation"])

# -------------------------------------------------------------
# Test 4: Case C - Stable Indicator (GDP Growth)
# -------------------------------------------------------------
info_stable = {
    "metadata": {"name": "Real GDP Growth", "unit": "%"},
    "summary": {
        "has_data": True,
        "latest_year": 2024,
        "latest_value": 7.02,
        "previous_year": 2023,
        "previous_value": 7.00,
        "change": 0.02,
    },
}
interp_stable = generate_single_interpretation("gdp_growth", info_stable, pd.DataFrame())
record("Stable: Direction field", interp_stable["direction"] == "remained steady")
record("Stable: Observed trend wording", "remained steady by 0.02 percentage points" in interp_stable["observed_trend"])
record("Stable: Mechanism text", "consistent economic expansion" in interp_stable["possible_explanation"])

# -------------------------------------------------------------
# Test 5: Case D - Missing / Absent Indicator Data
# -------------------------------------------------------------
info_missing = {
    "metadata": {"name": "Real GDP Growth", "unit": "%"},
    "summary": {
        "has_data": False,
        "latest_year": None,
        "latest_value": None,
        "previous_year": None,
        "previous_value": None,
        "change": None,
    },
}
interp_missing = generate_single_interpretation("gdp_growth", info_missing, pd.DataFrame())
record("Missing Data: has_data flag", interp_missing["has_data"] is False)
record("Missing Data: Observed trend message", "No historical observations available" in interp_missing["observed_trend"])
record("Missing Data: Explanation message", "Cannot generate explanation due to absent indicator data" in interp_missing["possible_explanation"])
record("Missing Data: Empty news list", interp_missing["relevant_news"] == [])

# -------------------------------------------------------------
# Test 6: Case E - Only 1 Data Point (No previous comparison)
# -------------------------------------------------------------
info_single_pt = {
    "metadata": {"name": "Inflation (Consumer Prices)", "unit": "%"},
    "summary": {
        "has_data": True,
        "latest_year": 2024,
        "latest_value": 5.0,
        "previous_year": None,
        "previous_value": None,
        "change": None,
    },
}
interp_single_pt = generate_single_interpretation("inflation", info_single_pt, pd.DataFrame())
record("Single Data Point: has_data flag", interp_single_pt["has_data"] is True)
record("Single Data Point: Trend text", "Latest recorded value for Inflation (Consumer Prices) is 5.00% in 2024" in interp_single_pt["observed_trend"])

# -------------------------------------------------------------
# Test 7: Relevant News Matching vs News Unavailable
# -------------------------------------------------------------
sample_news_df = pd.DataFrame([
    {"title": "Food Prices Rise in July", "source": "News A", "url": "https://a.com", "category": "Inflation", "published_at": "2024-07-01"},
    {"title": "RBI Considers Rate Cut", "source": "News B", "url": "https://b.com", "category": "Monetary Policy", "published_at": "2024-07-02"},
    {"title": "Factory Hiring Expands", "source": "News C", "url": "https://c.com", "category": "Employment", "published_at": "2024-07-03"},
    {"title": "New City Bridge Opened", "source": "News D", "url": "https://d.com", "category": "Other Economic News", "published_at": "2024-07-04"},
])

# Inflation maps to ['Inflation', 'Monetary Policy']
interp_with_news = generate_single_interpretation("inflation", info_increasing, sample_news_df)
matched_cats = [art["category"] for art in interp_with_news["relevant_news"]]
record("News Matching: Category mapping", set(matched_cats).issubset({"Inflation", "Monetary Policy"}), str(matched_cats))
record("News Matching: Count capped at 3", len(interp_with_news["relevant_news"]) <= 3)

# When news DataFrame is empty
interp_empty_news = generate_single_interpretation("inflation", info_increasing, pd.DataFrame())
record("News Unavailable: Returns empty list cleanly", interp_empty_news["relevant_news"] == [])

# When news has no matching categories (e.g. only "Other Economic News" for Unemployment)
irrelevant_news_df = pd.DataFrame([
    {"title": "Unrelated topic", "source": "X", "url": "https://x.com", "category": "Other Economic News", "published_at": "2024-07-01"}
])
interp_irrelevant_news = generate_single_interpretation("unemployment", info_decreasing, irrelevant_news_df)
record("Irrelevant News: Correctly excludes non-matching articles", interp_irrelevant_news["relevant_news"] == [])

# -------------------------------------------------------------
# Test 8: generate_all_interpretations for full indicator suite
# -------------------------------------------------------------
all_econ_data = {
    "inflation": info_increasing,
    "unemployment": info_decreasing,
    "gdp_growth": info_stable,
}
all_interps = generate_all_interpretations(all_econ_data, sample_news_df)
record("All Interpretations: Keys match", set(all_interps.keys()) == {"inflation", "unemployment", "gdp_growth"})
record("All Interpretations: Inflation has data", all_interps["inflation"]["has_data"] is True)
record("All Interpretations: Unemployment has data", all_interps["unemployment"]["has_data"] is True)
record("All Interpretations: GDP growth has data", all_interps["gdp_growth"]["has_data"] is True)

# -------------------------------------------------------------
# Summary Display
# -------------------------------------------------------------
print()
print("=" * 70)
print(f"{'TEST NAME':<45} {'STATUS':<8} DETAILS")
print("=" * 70)
fail_count = 0
for name, status, detail in results:
    print(f"{name:<45} {status:<8} {detail}")
    if status == "FAIL":
        fail_count += 1
print("=" * 70)
print(f"Total: {len(results)} assertions | Failures: {fail_count}")

if fail_count > 0:
    sys.exit(1)
