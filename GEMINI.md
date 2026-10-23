# The Economic Interpreter â€” Project Instructions

## 1. Project Overview

The Economic Interpreter is a beginner-friendly data science web application that helps students and general users understand the relationship between inflation, unemployment, GDP growth, and economic news.

The application collects economic data from reliable public sources, retrieves relevant news articles, performs basic Natural Language Processing (NLP), and presents economic trends through interactive visualizations and simple explanations.

The primary objective is to build a functional, accurate, easy-to-understand academic project that can be deployed online.

**Important:** Keep the application simple. Do not add unnecessary features or overengineer the architecture.

## 2. Main Objectives

The application must:

1. Display inflation, unemployment, and GDP growth data.
2. Retrieve historical economic indicators from the World Bank API.
3. Retrieve relevant economic news from a permitted news API.
4. Clean and categorize news articles using basic NLP techniques.
5. Compare economic indicator trends with relevant news topics.
6. Present interactive charts and simple educational explanations.
7. Clearly identify data sources, reporting periods, and analytical limitations.
8. Run locally and support deployment through Streamlit Community Cloud.

## 3. Technology Stack

Use the following technologies:

- Programming language: Python
- Web framework: Streamlit
- Data manipulation: Pandas
- Numerical calculations: NumPy, when needed
- Visualization: Plotly
- HTTP requests: Requests
- Configuration: python-dotenv for local development
- Economic data: World Bank Indicators API
- News data: A news provider whose API terms permit the intended application and deployment
- NLP: Python text processing, with NLTK only when necessary
- Version control: Git and GitHub
- Deployment: Streamlit Community Cloud

Do not introduce React, Node.js, a separate backend, a database, Docker, or an AI agent framework unless a specific requirement makes one necessary.

## 4. Core Features

### Feature A: Economic Dashboard

Display three economic indicators:

1. Inflation â€” World Bank indicator code: `FP.CPI.TOTL.ZG`
2. Unemployment â€” World Bank indicator code: `SL.UEM.TOTL.ZS`
3. Real GDP growth â€” World Bank indicator code: `NY.GDP.MKTP.KD.ZG`

Use India as the default country.

Requirements:

- Retrieve historical observations from the World Bank API.
- Display the latest available value for each indicator.
- Show the reporting period beside each value.
- Display historical trends using Plotly line charts.
- Allow users to select a historical time range if practical.
- Handle missing observations without crashing.
- Display appropriate units and descriptions.
- Do not invent values when data is unavailable.
- Clearly distinguish unavailable data from a genuine zero value.

Use documented API endpoints and verify the returned response structure.

The World Bank API does not require an API key for ordinary indicator queries.

### Feature B: Economic News

Retrieve economic news through the configured news provider.

Requirements:

- Search for relevant economic topics.
- Display article headline, source, publication date, description, and original article link when available.
- Categorize articles into relevant topics:
  - Inflation
  - Employment
  - GDP and economic growth
  - Monetary policy
  - Other economic news
- Remove duplicate articles using their URLs or another reliable identifier.
- Handle missing fields and empty responses.
- Handle API errors and rate limits gracefully.
- Clearly communicate when news cannot be retrieved.
- Do not display sample articles as if they were live news.

Respect the selected news provider's API limits, licensing conditions, and permitted use of article content.

Keep the news API key outside the source code.

### Feature C: Basic NLP

Implement lightweight text processing.

Required operations:

- Normalize text.
- Convert text to lowercase where appropriate.
- Tokenize text when necessary.
- Remove irrelevant punctuation.
- Extract relevant economic keywords.
- Categorize articles using transparent keyword-based rules.

Use NLTK only if it provides a clear benefit.

TF-IDF may be introduced later if it improves keyword analysis and remains easy to explain.

Do not implement deep learning, custom model training, or complex language-model pipelines unless explicitly requested.

### Feature D: Economic Interpretation

Create simple explanations based on actual economic observations and relevant news.

Each interpretation should contain:

1. **Observed trend:** What changed in the indicator?
2. **Relevant news:** Which retrieved articles discuss potentially related topics?
3. **Possible explanation:** What economic mechanisms might connect the topic and the indicator?
4. **Limitations:** What cannot be concluded from the available evidence?

Example:

"Inflation increased compared with the previous available observation. Several retrieved articles discuss food prices. Higher food prices can contribute to inflation, but the articles alone do not establish that these events caused the observed change."

This is an illustrative template, not a predetermined result.

Rules:

- Calculate indicator changes from actual observations.
- Compare observations with appropriate previous periods.
- Respect the reporting frequency of each indicator.
- Use article dates and available reporting periods carefully.
- Distinguish facts from possible explanations.
- Never claim causation from correlation or timing alone.
- Never fabricate article contents, statistics, or economic events.
- If relevant evidence is insufficient, state that clearly.
- Prefer deterministic Python templates over generative AI for the initial implementation.

Do not present the application as a professional economic forecasting or financial advice system.

## 5. User Interface

Build a clean, professional, responsive Streamlit dashboard.

Use three main sections:

### Economic Overview
- Three indicator cards.
- Historical trend charts.
- Country selection, initially supporting India.
- Reporting periods and data source information.

### Economic News
- Relevant news articles.
- Publication dates and source names.
- Topic categories.
- Links to original articles.

### Economic Interpretation
- Observed economic changes.
- Relevant news topics and articles.
- Possible economic explanations.
- Limitations and uncertainty.

Include a concise methodology and data sources section.

Design requirements:

- Clear headings and readable text.
- Consistent spacing and typography.
- Simple navigation.
- Appropriate chart labels and tooltips.
- Useful loading indicators.
- Clear error and empty-data messages.
- A layout that remains usable on smaller screens.
- Avoid excessive animations, decorative elements, and unnecessary components.

Prioritize usability and clarity over visual complexity.

## 6. Project Structure

Use this structure unless the existing repository has a reasonable structure that should be preserved:

economic-interpreter/
â”œâ”€â”€ app.py
â”œâ”€â”€ requirements.txt
â”œâ”€â”€ .env
â”œâ”€â”€ .gitignore
â”œâ”€â”€ README.md
â”œâ”€â”€ data/
â”‚   â””â”€â”€ sample_news.csv
â””â”€â”€ modules/
    â”œâ”€â”€ economic_data.py
    â”œâ”€â”€ news_data.py
    â”œâ”€â”€ text_processing.py
    â””â”€â”€ analysis.py

Responsibilities:

- `app.py`: Streamlit interface and application orchestration.
- `modules/economic_data.py`: Retrieve and prepare World Bank indicator data.
- `modules/news_data.py`: Retrieve, validate, and deduplicate news articles.
- `modules/text_processing.py`: Clean article text and categorize topics.
- `modules/analysis.py`: Calculate trends and generate evidence-based explanations.
- `requirements.txt`: List the application's actual dependencies.
- `.env`: Store local development secrets.
- `.gitignore`: Exclude secrets, virtual environments, and generated files.
- `README.md`: Explain setup, architecture, data sources, methodology, limitations, and deployment.
- `data/sample_news.csv`: Optional, clearly labelled sample data for development and testing.

Create modules incrementally. Do not generate every file with unnecessary placeholder code before the core application works.

## 7. Data Handling and Reliability

Follow these rules:

- Use Pandas for tabular data processing.
- Validate API responses before processing them.
- Handle HTTP errors, timeouts, malformed responses, and missing fields.
- Set sensible HTTP request timeouts.
- Avoid unnecessary repeated API requests.
- Use Streamlit caching where appropriate.
- Preserve actual observation dates and reporting periods.
- Avoid silently replacing missing values with zero.
- Keep data retrieval separate from visualization logic.
- Keep API credentials out of logs and error messages.
- Use clear error messages that help users understand what failed.

Never silently substitute fabricated data when a live API fails.

If sample data is used for development, label it clearly and distinguish it from real observations.

## 8. Security and Configuration

Read secrets from environment variables during local development.

For deployment, support Streamlit Community Cloud Secrets.

The news API key must never be hardcoded in Python files or committed to GitHub.

Use `.gitignore` to exclude:

- `.env`
- `.venv/`
- `__pycache__/`
- `*.pyc`

Validate external inputs and avoid exposing stack traces or credentials to users.

Do not add authentication or user accounts unless explicitly requested.

## 9. Testing

Test the application progressively.

At a minimum, verify:

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

Use small unit tests for data processing and analysis functions when practical.

Do not claim that a feature has been tested unless it has actually been tested.

## 10. Deployment

Prepare the application for Streamlit Community Cloud.

Requirements:

- Provide a valid `requirements.txt`.
- Use `app.py` as the entry point.
- Keep credentials in Streamlit Secrets in production.
- Avoid reliance on files that exist only on the developer's computer.
- Handle API failures gracefully.
- Document setup and deployment steps in `README.md`.
- Confirm that the application runs locally before preparing deployment.
- Explain any remaining configuration that requires manual action.

Do not assume that a news API's development plan permits public production deployment. Verify the provider's current terms.

## 11. Development Workflow

Follow this sequence:

Phase 1: Inspect the existing project files and understand the current implementation.

Phase 2: Set up the Streamlit application and dependencies.

Phase 3: Implement World Bank data retrieval.

Phase 4: Display indicator cards and historical charts.

Phase 5: Integrate the news provider.

Phase 6: Implement basic NLP and article categorization.

Phase 7: Implement trend comparisons and educational explanations.

Phase 8: Test error handling, calculations, and the complete workflow.

Phase 9: Prepare GitHub and Streamlit Community Cloud deployment.

After each phase:

- Run the relevant code.
- Check for errors.
- Fix regressions before continuing.
- Summarize the files changed.
- State what has been implemented and tested.
- Identify any remaining manual configuration.

Do not rewrite working components unnecessarily.

## 12. Coding Standards

- Write readable, beginner-friendly Python.
- Use descriptive variable and function names.
- Prefer small functions with clear responsibilities.
- Add type hints where helpful.
- Use docstrings for important functions.
- Avoid unnecessary abstraction and complicated design patterns.
- Keep dependencies to a minimum.
- Do not introduce unused packages.
- Follow the existing project conventions when modifying an established codebase.
- Avoid changing unrelated files.
- Never remove working functionality without a clear reason.

When fixing bugs, identify the underlying cause rather than applying superficial workarounds.

## 13. Explicitly Out of Scope

Do not implement the following unless explicitly requested:

- User authentication and registration.
- Subscription plans or payments.
- A database.
- AI agents.
- A chatbot.
- A custom-trained machine learning model.
- Economic forecasting.
- Complex sentiment-analysis pipelines.
- Real-time financial trading data.
- A separate React frontend.
- A separate Node.js backend.
- Microservices.
- Docker and Kubernetes.
- Complex dashboards with unnecessary charts.
- Automated email notifications.

The priority is a reliable, understandable educational data science application.

## 14. Definition of Done

The project is considered complete when:

- The application launches successfully.
- The dashboard retrieves real economic observations.
- Inflation, unemployment, and GDP growth are displayed with appropriate historical charts.
- The news section displays real articles from a permitted provider when available.
- Basic NLP categorizes relevant articles.
- The interpretation section explains observed changes without inventing evidence.
- Missing data and API failures are handled gracefully.
- API credentials are protected.
- The README explains installation, execution, data sources, limitations, and deployment.
- The application is deployed online and accessible through its published URL.

If an external API cannot be configured, document the limitation and provide a clearly labelled development alternative rather than pretending the integration works.

## Final Instruction

Build the smallest complete version of The Economic Interpreter first.

Prioritize correctness, simplicity, maintainability, and successful deployment.

Do not add features merely to make the project appear more advanced. Every feature must directly support the project's stated objectives.
