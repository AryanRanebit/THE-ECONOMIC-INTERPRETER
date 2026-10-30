# Audit Remediation & Reliability Hardening Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Remediate all major architectural, documentation, and reliability findings identified in the project audit to achieve strict 100% compliance with GEMINI.md specifications.

**Architecture:** Implement dual-provider news retrieval (optional authenticated NewsAPI + open Google News RSS), eliminate silent fallback data substitution in favor of explicit user consent, dynamically derive UI topic categories from text processing dictionaries, expose temporal horizon boundaries in economic synthesis, and clarify the dual-track Streamlit/Vercel architecture in documentation.

**Tech Stack:** Python 3.10+, Streamlit, Pandas, NumPy, Plotly, Requests, Pytest.

---

### Task 1: Add Optional REST News API Key Support & Align News Documentation

**Files:**
- Modify: `modules/news_data.py`
- Modify: `.env.example`
- Test: `tests/test_components.py`

**Step 1: Write the failing test**

Add `test_news_api_key_retrieval_and_provider_selection()` in `tests/test_components.py`:

```python
def test_news_api_key_retrieval(monkeypatch):
    """Verify that NEWS_API_KEY is retrieved securely from environment variables."""
    from modules.news_data import get_news_api_key
    monkeypatch.setenv("NEWS_API_KEY", "test_key_12345")
    assert get_news_api_key() == "test_key_12345"
    
    monkeypatch.delenv("NEWS_API_KEY", raising=False)
    assert get_news_api_key() is None
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_components.py -k test_news_api_key_retrieval`  
Expected: FAIL with `ImportError: cannot import name 'get_news_api_key'`

**Step 3: Implement minimal code**

In `modules/news_data.py`:
1. Add `get_news_api_key() -> Optional[str]` checking `os.getenv("NEWS_API_KEY")` and `st.secrets["NEWS_API_KEY"]`.
2. Add `fetch_newsapi_org(query: str, api_key: str, timeout_seconds: int = 10) -> pd.DataFrame` hitting `https://newsapi.org/v2/everything`.
3. In `get_economic_news()`, prioritize `fetch_newsapi_org` if key is present, fallback to `fetch_google_news_rss` if no key is present.
4. Update the docstring to accurately state that `NEWS_API_KEY` is supported but optional.
5. In `.env.example`, document `NEWS_API_KEY=your_optional_newsapi_key_here`.

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_components.py -k test_news_api_key_retrieval`  
Expected: PASS

**Step 5: Commit**

```bash
git add modules/news_data.py .env.example tests/test_components.py
git commit -m "feat(news): implement optional NewsAPI key retrieval and provider hierarchy"
```

---

### Task 2: Decouple Automatic News Fallback to Prevent Silent Data Substitution

**Files:**
- Modify: `modules/news_data.py:203-221`
- Modify: `app.py:385-410`
- Test: `tests/test_components.py`

**Step 1: Write the failing test**

Add `test_live_news_failure_does_not_silently_substitute_sample_data()` in `tests/test_components.py`:

```python
def test_live_news_failure_does_not_silently_substitute(monkeypatch):
    """Verify that live news failure returns an empty DataFrame and error message, not sample data."""
    from modules import news_data
    
    # Mock both providers to return empty
    monkeypatch.setattr(news_data, "fetch_google_news_rss", lambda **kwargs: pd.DataFrame())
    monkeypatch.setattr(news_data, "get_news_api_key", lambda: None)
    
    payload = news_data.get_economic_news(query="test", use_sample_data=False)
    assert payload["is_sample"] is False
    assert payload["articles"].empty
    assert payload["error"] is not None
    assert "Live news feed could not be retrieved" in payload["error"]
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_components.py -k test_live_news_failure_does_not_silently_substitute`  
Expected: FAIL because `payload["is_sample"]` currently evaluates to `True` (automatic sample fallback).

**Step 3: Implement minimal code**

1. In `modules/news_data.py`, update `get_economic_news()`:
```python
    if not df_live.empty:
        return {
            "articles": df_live,
            "source_type": live_source_label,
            "is_sample": False,
            "error": None,
        }

    # Do NOT silently substitute sample data per GEMINI.md Section 7
    return {
        "articles": pd.DataFrame(columns=["title", "source", "published_at", "description", "url", "is_sample"]),
        "source_type": "Live News Feed (Unavailable)",
        "is_sample": False,
        "error": "Live news feed could not be retrieved (network drop, timeout, or rate-limiting). Please click 'Load Offline Sample Archive' to load verified sample data.",
    }
```
2. In `app.py`, update Section 2:
   If `articles_df.empty` and `news_payload.get("error")`:
   - Render `st.error(news_payload["error"])`
   - Render button `if st.button("📁 Load Offline Sample Dataset"):` that sets `st.session_state["use_sample_news"] = True` and reruns.

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_components.py -k test_live_news_failure_does_not_silently_substitute`  
Expected: PASS

**Step 5: Commit**

```bash
git add modules/news_data.py app.py tests/test_components.py
git commit -m "fix(news): eliminate silent sample news substitution on live fetch failure"
```

---

### Task 3: Dynamically Link Topic Categories in Streamlit UI

**Files:**
- Modify: `app.py:430-445`
- Test: `tests/test_components.py`

**Step 1: Write the failing test**

Add `test_ui_topic_categories_derived_from_nlp_registry()` in `tests/test_components.py`:

```python
def test_ui_topic_categories_match_nlp_module():
    """Verify topic categories in UI match text processing single-source-of-truth."""
    from modules.text_processing import TOPIC_KEYWORDS, DEFAULT_CATEGORY
    expected_categories = ["All Topics"] + list(TOPIC_KEYWORDS.keys()) + [DEFAULT_CATEGORY]
    assert len(expected_categories) == 6
    assert "Inflation" in expected_categories
    assert "Monetary Policy" in expected_categories
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_components.py -k test_ui_topic_categories_match_nlp_module`  
Expected: PASS (as baseline structure check)

**Step 3: Implement minimal code**

In `app.py`:
1. Import `TOPIC_KEYWORDS` and `DEFAULT_CATEGORY` from `modules.text_processing`.
2. Replace hardcoded `topic_options = [...]` with:
```python
topic_options = ["All Topics"] + list(TOPIC_KEYWORDS.keys()) + [DEFAULT_CATEGORY]
```

**Step 4: Run all tests to verify no regressions**

Run: `python -m pytest tests/test_components.py`  
Expected: PASS

**Step 5: Commit**

```bash
git add app.py
git commit -m "refactor(ui): dynamically derive topic filter categories from NLP module"
```

---

### Task 4: Add Temporal Horizon Indicators in Economic Interpretation View

**Files:**
- Modify: `modules/analysis.py:120-205`
- Modify: `app.py:520-547`
- Test: `tests/test_components.py`

**Step 1: Write the failing test**

Add `test_interpretation_contains_temporal_horizon_metadata()` in `tests/test_components.py`:

```python
def test_interpretation_temporal_horizons():
    """Verify interpretations explicitly distinguish between historical annual indicator period and real-time news."""
    from modules.analysis import generate_single_interpretation
    info = {
        "metadata": {"name": "Inflation", "unit": "%"},
        "summary": {"has_data": True, "latest_year": 2023, "latest_value": 5.4, "previous_year": 2022, "previous_value": 6.7, "change": -1.3}
    }
    interp = generate_single_interpretation("inflation", info, pd.DataFrame())
    assert "indicator_period" in interp
    assert interp["indicator_period"] == "2023 Annual Aggregate"
    assert "news_period" in interp
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_components.py -k test_interpretation_temporal_horizons`  
Expected: FAIL with `KeyError: 'indicator_period'`

**Step 3: Implement minimal code**

1. In `modules/analysis.py`, add `indicator_period` and `news_period` to the returned dictionary in `generate_single_interpretation()`:
```python
"indicator_period": f"{latest_yr} Annual Aggregate" if latest_yr else "Unknown Period",
"news_period": "Contemporary News Coverage (Last 24-48 Hours)" if not categorized_news_df.empty else "No Active News",
```
2. In `app.py`, render an explicit temporal badge at the top of each interpretation tab:
```python
st.caption(f"⏱️ **Data Time Horizon:** Macro Indicator: `{item.get('indicator_period')}` | News Coverage: `{item.get('news_period')}`")
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_components.py -k test_interpretation_temporal_horizons`  
Expected: PASS

**Step 5: Commit**

```bash
git add modules/analysis.py app.py tests/test_components.py
git commit -m "feat(analysis): expose explicit temporal horizon metadata in interpretations"
```

---

### Task 5: Clarify Dual-Track Architecture & Alignment in Documentation

**Files:**
- Modify: `README.md`
- Modify: `DEPLOYMENT.md`

**Step 1: Update README.md and DEPLOYMENT.md**

1. In `README.md`, add an explicit section:
   **"Architecture & Dual-Track Deployment Specification"**
   - **Primary Academic Reference (Canonical):** `app.py` (Streamlit Community Cloud). Single-tier, reactive Python dashboard matching course specifications.
   - **Static & Serverless Alternative:** `index.html` + `api/index.py` (Vercel). Provided as a high-performance demonstration of headless REST architecture using the identical underlying analytical modules.
2. Verify that all instructions for local launch (`python dev_server.py 8000` vs `streamlit run app.py`) are clearly demarcated.

**Step 2: Verify formatting and links**

Ensure markdown tables and relative file paths are strictly valid.

**Step 3: Commit**

```bash
git add README.md DEPLOYMENT.md
git commit -m "docs: clarify canonical Streamlit reference vs optional Vercel static architecture"
```

---

### Task 6: Comprehensive Automated Test Suite Execution & Verification

**Files:**
- Modify: `tests/test_components.py`

**Step 1: Execute complete pytest suite**

Run: `python -m pytest tests/test_components.py -v`  
Expected: 15+ tests passing with 100% success rate across all 10 GEMINI.md criteria and the new remediation tests.

**Step 2: Verify local server and Streamlit compilation**

Run: `python -c "import app; print('app.py OK')"`  
Run: `python -c "from api.index import handler; print('api/index.py OK')"`  
Expected: Code 0 with no syntax or import errors.

**Step 3: Final Commit**

```bash
git add tests/test_components.py
git commit -m "test: verify complete remediation suite across all criteria"
```

