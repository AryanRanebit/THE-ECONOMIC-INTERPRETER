"""
Economic News Module
====================
Handles retrieval, validation, cleaning, and deduplication of economic news
articles from live providers and offline development fallbacks.

Key Features:
- Live retrieval via Google News RSS (zero-key open access).
- Support for API-key-based providers (NewsAPI.org) when configured.
- Offline sample dataset fallback (data/sample_news.csv).
- URL and title-based article deduplication.
- Robust error handling for network failures, empty responses, and timeouts.
- Strict isolation of API keys (reads from environment variables or Streamlit secrets).
"""

import html
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
import xml.etree.ElementTree as ET

import pandas as pd
import requests

try:
    import streamlit as st
    cache_data_news = st.cache_data(ttl=1800, show_spinner=False)
except Exception:
    def cache_data_news(func):
        return func

# Base path for local sample data
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
SAMPLE_NEWS_PATH = DATA_DIR / "sample_news.csv"


def get_news_api_key() -> Optional[str]:
    """
    Retrieve optional News API key securely from environment variables or Streamlit secrets.
    Never exposes keys in logs, exceptions, or user interfaces.
    """
    key = os.getenv("NEWS_API_KEY")
    if key and key.strip():
        return key.strip()

    try:
        if "st" in globals() and hasattr(st, "secrets") and "NEWS_API_KEY" in st.secrets:
            sec_key = st.secrets["NEWS_API_KEY"]
            if sec_key and str(sec_key).strip():
                return str(sec_key).strip()
    except Exception:
        pass

    return None


def fetch_newsapi_org(
    query: str = "India economy inflation GDP",
    api_key: Optional[str] = None,
    timeout_seconds: int = 10,
) -> pd.DataFrame:
    """
    Fetch live economic news from NewsAPI.org when a valid API key is provided.

    Parameters:
        query: Search keywords.
        api_key: NewsAPI authentication key.
        timeout_seconds: Network request timeout.

    Returns:
        pd.DataFrame: Cleaned and deduplicated DataFrame of live news articles.
    """
    if not api_key:
        return pd.DataFrame(columns=["title", "source", "published_at", "description", "url", "is_sample"])

    url = "https://newsapi.org/v2/everything"
    params = {
        "q": query,
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": 50,
    }
    headers = {
        "X-Api-Key": api_key,
        "User-Agent": "TheEconomicInterpreter/1.0",
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=timeout_seconds)
        response.raise_for_status()
        data = response.json()

        if data.get("status") != "ok" or "articles" not in data:
            return pd.DataFrame(columns=["title", "source", "published_at", "description", "url", "is_sample"])

        records: List[Dict[str, Any]] = []
        for art in data.get("articles", []):
            if not isinstance(art, dict):
                continue
            title = clean_html_text(art.get("title", ""))
            desc = clean_html_text(art.get("description", ""))
            source_dict = art.get("source", {})
            source_name = source_dict.get("name", "NewsAPI") if isinstance(source_dict, dict) else "NewsAPI"
            pub_date = str(art.get("publishedAt", ""))[:10]

            if not desc:
                desc = title

            records.append({
                "title": title,
                "source": source_name,
                "published_at": pub_date or "Recent",
                "description": desc,
                "url": art.get("url", ""),
                "is_sample": False,
            })

        if not records:
            return pd.DataFrame(columns=["title", "source", "published_at", "description", "url", "is_sample"])

        df = pd.DataFrame(records)
        return deduplicate_articles(df)

    except requests.exceptions.RequestException as err:
        print(f"[Warning] NewsAPI request failed: {err}")
        return pd.DataFrame(columns=["title", "source", "published_at", "description", "url", "is_sample"])



def clean_html_text(raw_html: Optional[str]) -> str:
    """Strip HTML tags and unescape HTML entities from a string."""
    if not isinstance(raw_html, str) or not raw_html.strip():
        return ""
    # Strip HTML tags like <b> or <a>
    clean_text = re.sub(r"<[^>]+>", "", raw_html)
    # Unescape HTML entities like &quot;, &#39;, &amp;
    return html.unescape(clean_text).strip()


def deduplicate_articles(df: pd.DataFrame) -> pd.DataFrame:
    """
    Remove duplicate news articles based on URL and normalized title.

    Parameters:
        df: DataFrame containing news records.

    Returns:
        pd.DataFrame: Deduplicated DataFrame.
    """
    if df.empty or "title" not in df.columns:
        return df

    df = df.copy()

    # First pass: Deduplicate by exact URL (only for non-empty, non-null URLs)
    if "url" in df.columns:
        has_url = df["url"].notna() & (df["url"].astype(str).str.strip().str.lower() != "none") & (df["url"].astype(str).str.strip() != "")
        df_with_url = df[has_url].drop_duplicates(subset=["url"], keep="first")
        df_no_url = df[~has_url]
        df = pd.concat([df_with_url, df_no_url], ignore_index=True)

    # Second pass: Deduplicate by lowercased, stripped title
    df["title_normalized"] = df["title"].astype(str).str.lower().str.strip()
    df = df.drop_duplicates(subset=["title_normalized"], keep="first")
    df = df.drop(columns=["title_normalized"])

    return df.reset_index(drop=True)


def load_sample_news() -> pd.DataFrame:
    """
    Load the offline sample news dataset for development, testing, or offline use.
    Guarantees 'is_sample' is marked True.
    """
    if not SAMPLE_NEWS_PATH.exists():
        print(f"[Warning] Sample news file not found at: {SAMPLE_NEWS_PATH}")
        return pd.DataFrame(columns=["title", "source", "published_at", "description", "url", "is_sample"])

    try:
        df = pd.read_csv(SAMPLE_NEWS_PATH)
        df["is_sample"] = True
        return deduplicate_articles(df)
    except Exception as err:
        print(f"[Error] Failed to load sample news: {err}")
        return pd.DataFrame(columns=["title", "source", "published_at", "description", "url", "is_sample"])


def fetch_google_news_rss(
    query: str = "India economy inflation GDP",
    timeout_seconds: int = 10,
) -> pd.DataFrame:
    """
    Fetch live economic news from Google News RSS feed without requiring an API key.

    Parameters:
        query: Search query for economic topics.
        timeout_seconds: Network timeout.

    Returns:
        pd.DataFrame: DataFrame of live articles.
    """
    encoded_query = requests.utils.quote(query)
    rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-IN&gl=IN&ceid=IN:en"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
    }

    try:
        response = requests.get(rss_url, headers=headers, timeout=timeout_seconds)
        response.raise_for_status()

        root = ET.fromstring(response.content)
        items = root.findall("./channel/item")

        records: List[Dict[str, Any]] = []
        for item in items:
            title_elem = item.find("title")
            link_elem = item.find("link")
            pub_elem = item.find("pubDate")
            desc_elem = item.find("description")
            source_elem = item.find("source")

            raw_title = title_elem.text if title_elem is not None else ""
            raw_link = link_elem.text if link_elem is not None else ""
            raw_pub = pub_elem.text if pub_elem is not None else ""
            raw_desc = desc_elem.text if desc_elem is not None else ""
            source_name = source_elem.text if source_elem is not None else "Google News"

            # In Google News RSS titles often end with '- Source Name'
            # If source_elem is missing, try splitting from title
            cleaned_title = clean_html_text(raw_title)
            if " - " in cleaned_title and (not source_name or source_name == "Google News"):
                parts = cleaned_title.rsplit(" - ", 1)
                cleaned_title = parts[0].strip()
                source_name = parts[1].strip()

            cleaned_desc = clean_html_text(raw_desc)
            if not cleaned_desc:
                cleaned_desc = cleaned_title

            records.append({
                "title": cleaned_title,
                "source": source_name,
                "published_at": raw_pub[:16] if raw_pub else "Recent",
                "description": cleaned_desc,
                "url": raw_link,
                "is_sample": False,
            })

        if not records:
            return pd.DataFrame(columns=["title", "source", "published_at", "description", "url", "is_sample"])

        df = pd.DataFrame(records)
        return deduplicate_articles(df)

    except requests.exceptions.RequestException as err:
        print(f"[Warning] Live news request failed: {err}")
        return pd.DataFrame(columns=["title", "source", "published_at", "description", "url", "is_sample"])
    except ET.ParseError as err:
        print(f"[Warning] XML parsing error in RSS response: {err}")
        return pd.DataFrame(columns=["title", "source", "published_at", "description", "url", "is_sample"])


@cache_data_news
def get_economic_news(
    query: str = "India economy inflation GDP unemployment",
    use_sample_data: bool = False,
) -> Dict[str, Any]:
    """
    Unified news provider interface with caching.

    Parameters:
        query: Search keywords.
        use_sample_data: If True, forces loading from local sample dataset.

    Returns:
        Dict containing:
            - 'articles': pd.DataFrame
            - 'source_type': 'Live News Feed' or 'Sample Dataset'
            - 'is_sample': bool
            - 'error': Optional[str]
    """
    if use_sample_data:
        df = load_sample_news()
        return {
            "articles": df,
            "source_type": "Sample Dataset (Offline Mode)",
            "is_sample": True,
            "error": None,
        }

    # Attempt live retrieval
    api_key = get_news_api_key()
    if api_key:
        df_live = fetch_newsapi_org(query=query, api_key=api_key)
        live_label = "Live News Feed (NewsAPI.org)"
    else:
        df_live = fetch_google_news_rss(query=query)
        live_label = "Live News Feed (Google News RSS)"

    if not df_live.empty:
        return {
            "articles": df_live,
            "source_type": live_label,
            "is_sample": False,
            "error": None,
        }

    # If live retrieval failed (e.g., no internet or rate limit), fall back gracefully
    df_fallback = load_sample_news()
    return {
        "articles": df_fallback,
        "source_type": "Sample Dataset (Automatic Fallback)",
        "is_sample": True,
        "error": "Live news feed could not be retrieved. Loaded local sample archive instead.",
    }
