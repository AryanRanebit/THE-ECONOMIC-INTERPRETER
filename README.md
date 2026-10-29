# 📈 The Economic Interpreter

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-Academic%20%2F%20MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Code style: clean](https://img.shields.io/badge/code%20style-beginner--friendly-orange.svg)]()

**The Economic Interpreter** is a beginner-friendly data science web application that helps students, researchers, and general citizens understand the relationship between macroeconomic indicators (**Inflation**, **Unemployment**, and **Real GDP Growth**) and contemporary economic news.

The application retrieves real historical observations from public data APIs, aggregates relevant economic headlines, applies explainable rule-based Natural Language Processing (NLP), and presents interactive visualizations alongside evidence-based educational interpretations.

---

## 🏛️ Main Features

1. **Macroeconomic Dashboard:**
   - Real-time indicator cards showing latest available observations, reporting periods, and period-over-period changes ($\Delta$).
   - Interactive **Plotly** time-series charts (combined comparison and focused indicator views with hover tooltips).
   - Historical time-range filter (2000–2025) and country selection (defaulting to **India 🇮🇳**, with support for comparative economies).
2. **Economic News & Topic Categorization:**
   - Live economic news retrieval via Google News RSS (zero-key open access).
   - Offline fallback sample archive (`data/sample_news.csv`) for offline development or testing without network access.
   - Two-pass deduplication algorithm by URL and normalized headline.
   - Full-text keyword search and category filtering.
3. **Transparent & Explainable NLP:**
   - Lightweight text processing: lowercase normalization, punctuation removal, and stopword stripping.
   - Rule-based keyword matching across 5 core topics:
     - 🔥 **Inflation**
     - 👥 **Employment**
     - 📈 **GDP and Economic Growth**
     - 🏦 **Monetary Policy**
     - 📰 **Other Economic News**
   - Displays exact matched keywords below each article for educational transparency.
4. **Structured Educational Interpretation Engine:**
   - Generates deterministic 4-part explanations strictly rooted in empirical data:
     1. **Observed Trend:** Fact-based change computed from actual World Bank data.
     2. **Relevant News:** Matched articles discussing related economic themes.
     3. **Possible Mechanism:** Textbook economic theory explaining potential links.
     4. **Analytical Limitations:** Explicit boundaries reminding users that correlation does not imply causation.

---

## 🗂️ Project Architecture & Structure

```text
THE-ECONOMIC-INTERPRETER/
├── app.py                      # Streamlit application layout & UI orchestration
├── requirements.txt            # Python dependency specifications
├── .env.example                # Safe environment configuration template
├── .gitignore                  # Git exclusion rules (secrets, caches, bytecode)
├── GEMINI.md                   # Complete project specifications & design rules
├── README.md                   # Project documentation & deployment guide
├── data/
│   └── sample_news.csv         # Labelled offline development sample news archive
├── modules/
│   ├── __init__.py             # Python package initializer
│   ├── economic_data.py        # World Bank API fetcher, cleaner & caching
│   ├── news_data.py            # News provider integration, deduplication & fallback
│   ├── text_processing.py      # Explainable NLP text processing & topic classification
│   └── analysis.py             # 4-part educational interpretation engine
└── tests/
    ├── __init__.py             # Test package initializer
    └── test_components.py      # Automated test suite (10/10 GEMINI.md requirements)
```

---

## 📊 Data Sources & Indicator Registry

| Indicator Name | World Bank Indicator Code | Units | Description |
| :--- | :--- | :--- | :--- |
| **Inflation (Consumer Prices)** | `FP.CPI.TOTL.ZG` | `% (Annual)` | Annual percentage change in the cost of a consumer basket of goods and services. |
| **Unemployment Rate** | `SL.UEM.TOTL.ZS` | `% of Labor Force` | Share of the labor force without work, available for and seeking employment (modeled ILO). |
| **Real GDP Growth** | `NY.GDP.MKTP.KD.ZG` | `% (Annual)` | Annual percentage growth rate of GDP at market prices based on constant local currency. |

- **Economic Data Provider:** [World Bank Open Data Indicators API](https://data.worldbank.org/) (Public, open access, no API key required).
- **News Provider:** Public Economic News RSS feeds & local offline dataset fallback.

---

## ⚙️ Methodology & Analytical Limitations

- **Preservation of Missing Observations:** Missing reporting years are retained as `NaN`/`None` and explicitly communicated in the UI rather than coerced to an artificial `0.0`.
- **Deduplication:** Repeated press releases or identical syndicated articles are eliminated using exact URL matching followed by case-insensitive title normalization.
- **Explainable NLP:** To avoid black-box hallucinations, articles are categorized using deterministic keyword dictionaries. Each classified headline displays the triggering terms (e.g., `['food inflation', 'prices']`).
- **Causality vs Correlation:** Macroeconomic indicators are published as annual national aggregates, whereas media reports capture short-term events. Timing overlap **does not prove causation**. This application is strictly an educational tool and does not provide financial or economic forecasting advice.

---

## 🚀 Local Installation & Execution

### Prerequisites
- Python 3.10, 3.11, 3.12, or 3.13 installed.
- Git installed.

### Step 1: Clone the Repository
```bash
git clone https://github.com/AryanRanebit/THE-ECONOMIC-INTERPRETER.git
cd THE-ECONOMIC-INTERPRETER
```

### Step 2: (Optional) Set up a Virtual Environment
```bash
python -m venv .venv

# On Windows (PowerShell):
.venv\Scripts\Activate.ps1

# On macOS / Linux:
source .venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Launch on Localhost

#### Option A: Redesigned High-Converting Dashboard & Design System (Port 8000)
```bash
python dev_server.py 8000
```
Open your browser at **`http://localhost:8000`** to view the redesigned light-blue dashboard with live interactive Chart.js time-series, debounced news search, 5-minute caching store, and the serverless JSON API at `/api`.

#### Option B: Streamlit Web Application (Port 8501)
```bash
streamlit run app.py
```
The application will open automatically in your browser at `http://localhost:8501`.

---

## 🧪 Running the Automated Test Suite

A complete test suite is provided in `tests/test_components.py` verifying all 10 criteria specified in Section 9 of `GEMINI.md`:

```bash
pytest tests/test_components.py -v
```

Expected output:
```text
tests/test_components.py::test_economic_indicator_requests PASSED        [ 10%]
tests/test_components.py::test_missing_observations_handling PASSED      [ 20%]
tests/test_components.py::test_indicator_changes_calculation PASSED      [ 30%]
tests/test_components.py::test_empty_news_responses PASSED               [ 40%]
tests/test_components.py::test_duplicate_articles_removal PASSED         [ 50%]
tests/test_components.py::test_articles_categorization_rules PASSED      [ 60%]
tests/test_components.py::test_missing_article_fields_safety PASSED      [ 70%]
tests/test_components.py::test_economic_explanations_match_data PASSED   [ 80%]
tests/test_components.py::test_api_failures_produce_understandable_messages PASSED [ 90%]
tests/test_components.py::test_streamlit_app_compilation PASSED          [100%]

============================= 10 passed in 6.76s ==============================
```

---

## ☁️ Deployment Guide: Streamlit Community Cloud

The Economic Interpreter is built specifically to deploy seamlessly on **Streamlit Community Cloud** with zero external server dependencies.

### Step-by-Step Deployment:
1. **GitHub Repository:** Ensure the repository is pushed to your GitHub account:
   `https://github.com/AryanRanebit/THE-ECONOMIC-INTERPRETER`
2. **Access Streamlit Cloud:** Go to [share.streamlit.io](https://share.streamlit.io) and log in with your GitHub account.
3. **Create New App:**
   - Click **"New app"**.
   - **Repository:** `AryanRanebit/THE-ECONOMIC-INTERPRETER`
   - **Branch:** `main`
   - **Main file path:** `app.py`
4. **Deploy:** Click **"Deploy!"**.
   - Streamlit Cloud will automatically detect `requirements.txt`, install dependencies, and launch your live public web application with a shareable URL!

---

## 📜 Academic Attribution & License

- **Author:** Aryan Rane
- **Academic Context:** Developed as an educational data science application to demystify macroeconomic relationships.
- **License:** Open Source under the MIT License.
