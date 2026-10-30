# 🚀 The Economic Interpreter — Deployment Guide

This guide provides complete, step-by-step instructions for deploying **The Economic Interpreter**.

Because this project is submitted for academic evaluation, it is configured with a **Dual-Deployment Architecture**:
1. **Primary Deployment — Streamlit Community Cloud:** Hosts the native, stateful interactive Streamlit web application (`app.py`) with real-time Plotly charts, interactive sliders, and persistent WebSocket connections.
2. **Serverless Cloud Portal — Vercel:** Hosts the lightweight, serverless HTTP REST API (`api/index.py`) and a modern static web dashboard (`public/index.html`).

---

## 🏛️ 1. Architecture Summary

```text
                               ┌─────────────────────────────────────────────────────────────┐
                               │                    GitHub Repository                        │
                               │        AryanRanebit/THE-ECONOMIC-INTERPRETER                │
                               └──────────────────────────────┬──────────────────────────────┘
                                                              │
                              ┌───────────────────────────────┴──────────────────────────────┐
                              ▼                                                              ▼
             ┌───────────────────────────────────┐                          ┌───────────────────────────────────┐
             │     Streamlit Community Cloud     │                          │          Vercel Platform          │
             │       (Native Stateful App)       │                          │        (Serverless Portal)        │
             ├───────────────────────────────────┤                          ├───────────────────────────────────┤
             │ • Entry Point: app.py             │                          │ • Static UI: public/index.html    │
             │ • Runtime: Python 3.10+           │                          │ • Serverless API: api/index.py    │
             │ • Protocol: WebSockets (ws://)    │                          │ • Protocol: Stateless HTTPS REST  │
             │ • Interactive Plotly charts       │                          │ • Fast global CDN caching         │
             │ • Official GEMINI.md target       │                          │ • College submission URL ready    │
             └───────────────────────────────────┘                          └───────────────────────────────────┘
```

---

## 🔑 2. Required External Services & Accounts

You only need free accounts:
1. **GitHub Account:** To host your code repository (`https://github.com`).
2. **Vercel Account:** Free Hobby tier ([vercel.com](https://vercel.com)) linked to your GitHub.
3. **Streamlit Community Cloud Account:** Free tier ([share.streamlit.io](https://share.streamlit.io)) linked to your GitHub.
4. **External API Keys:** **None required!**
   - The World Bank Indicators API is 100% public and open.
   - Google News RSS is 100% open and requires zero API keys.

---

## 📦 3. Preparing Your GitHub Repository

Before deploying, ensure your latest code is committed and pushed to GitHub:

```bash
# 1. Check status
git status

# 2. Add changes
git add .

# 3. Commit changes
git commit -m "feat: add Vercel serverless wrapper, static portal, and deployment configs"

# 4. Push to main branch
git push origin main
```

Verify that your repository on GitHub (`https://github.com/AryanRanebit/THE-ECONOMIC-INTERPRETER`) shows the latest files:
- `app.py`
- `vercel.json`
- `api/index.py`
- `public/index.html`
- `.streamlit/config.toml`
- `requirements.txt`

---

## ⚡ 4. Deploying to Vercel (Serverless Portal)

### Step 1: Sign in to Vercel
1. Go to [vercel.com](https://vercel.com) and log in using your **GitHub** account.

### Step 2: Import Your Repository
1. Click the **"Add New..."** button on your Vercel Dashboard and select **"Project"**.
2. Find `THE-ECONOMIC-INTERPRETER` under your GitHub repositories and click **"Import"**.

### Step 3: Configure Project Settings
In the Vercel configuration screen:
- **Project Name:** `the-economic-interpreter` (or your preferred name).
- **Framework Preset:** Select **"Other"**.
- **Root Directory:** `./` (Leave as default project root).
- **Build and Output Settings:**
  - **Build Command:** Leave **OFF / Empty** (no build command required).
  - **Output Directory:** Leave **OFF / Empty**.
  - **Install Command:** Leave default (`@vercel/python` automatically reads dependencies from `api/requirements.txt` to keep the serverless bundle size minimal).

### Step 4: Environment Variables
- **No environment variables are required** for standard operation because the application uses open public APIs.
- If you have an optional news provider API key, you can add it in Vercel settings as `NEWS_API_KEY`.

### Step 5: Click Deploy
1. Click **"Deploy"**.
2. Vercel will install dependencies from `api/requirements.txt`, detect `api/index.py` as a Python Serverless Function, and publish `public/index.html` as the live static web portal.
3. Once finished (typically 45–90 seconds), Vercel will assign you a live production URL (e.g., `https://the-economic-interpreter.vercel.app`).

### Step 6: Verify Live Vercel Deployment
Test the following URLs on your live Vercel domain:
- **Web Portal:** `https://your-app.vercel.app/`
- **Health Endpoint:** `https://your-app.vercel.app/api/index?action=health`
- **Indicators API:** `https://your-app.vercel.app/api/index?action=indicators&country=IN&range=2015:2025`
- **News API:** `https://your-app.vercel.app/api/index?action=news`
- **Interpretation API:** `https://your-app.vercel.app/api/index?action=interpret&country=IN&range=2015:2025`

---

## 🎈 5. Deploying to Streamlit Community Cloud (Native Interactive App)

To experience the full interactive dashboard with Plotly charts and live sliders:

### Step 1: Sign in to Streamlit Cloud
1. Go to [share.streamlit.io](https://share.streamlit.io) and log in with your GitHub account.

### Step 2: Create New App
1. Click **"Create app"** or **"New app"**.
2. Fill in the repository details:
   - **Repository:** `AryanRanebit/THE-ECONOMIC-INTERPRETER`
   - **Branch:** `main`
   - **Main file path:** `app.py`
   - **App URL (optional):** Choose a custom subdomain (e.g., `economic-interpreter.streamlit.app`).

### Step 3: Deploy!
1. Click **"Deploy!"**.
2. Streamlit Cloud will read `requirements.txt`, launch the Tornado Python server, and open your live dashboard in under 2 minutes.

---

## 🗄️ 6. Database and Backend Considerations

- **Is a database required?** No. Per project guidelines (`GEMINI.md`), data is fetched on-demand from the World Bank API and cached in memory. There are no user accounts, passwords, or persistent transactional records.
- **CORS Configuration:** Handled automatically in `api/index.py` via `Access-Control-Allow-Origin: *` headers, and in `.streamlit/config.toml` for the Streamlit server.
- **Serverless Timeouts:** The World Bank HTTP requests are configured with a strict 6–10 second timeout to ensure requests complete well within Vercel's 10-second free tier ceiling.

---

## 🛠️ 7. Troubleshooting Common Deployment Errors

| Issue | Cause | Solution |
| :--- | :--- | :--- |
| **Vercel: 404 Not Found on `/`** | Route configuration missing static folder pointer. | Ensure `vercel.json` contains `"handle": "filesystem"` before catch-all routes. |
| **Vercel: 504 Gateway Timeout** | World Bank API took longer than 10 seconds to respond. | The API automatically catches timeouts and returns fallback data without crashing. Refresh or select a shorter year range. |
| **Streamlit: ModuleNotFoundError** | A dependency was not listed in `requirements.txt`. | Ensure all imported libraries (`streamlit`, `pandas`, `numpy`, `plotly`, `requests`, `python-dotenv`) are listed in `requirements.txt`. |
| **Streamlit: WebSocket Disconnect** | Browser network interruption or strict corporate firewall. | Hard refresh the browser (`Ctrl+F5` or `Cmd+Shift+R`). |

---

## 🔄 8. Automatic Redeployment on Future Changes

Both **Vercel** and **Streamlit Community Cloud** are linked to your GitHub repository.
Whenever you push a new commit to the `main` branch:
```bash
git add .
git commit -m "docs: update project analysis"
git push origin main
```
Both platforms will automatically detect the push, rebuild, and redeploy your latest changes with zero downtime!

---

## 🎓 9. How to Present This in Your College Evaluation

When presenting this project to your professor or evaluator:
1. **Explain the Architecture:** Explain why you implemented a **dual-deployment architecture**:
   - Vercel demonstrates your understanding of **Serverless Edge Computing**, RESTful micro-endpoints, and decoupled web portals.
   - Streamlit Cloud demonstrates your understanding of **Stateful Reactive Computing** and live data science dashboarding.
2. **Highlight Data Integrity:** Point out that missing observations are preserved as `NaN`/`None` rather than fabricated zeroes, and that interpretations strictly avoid claiming direct causality from correlation.
3. **Showcase Automated Testing:** Run `pytest tests/test_components.py -v` to prove that 12 automated unit tests pass with 100% reliability.
