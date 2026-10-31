"""
Vercel Serverless Function Handler
==================================
Provides an HTTP JSON API wrapper around The Economic Interpreter modules
for serverless deployment on Vercel (@vercel/python).

Supported Endpoints:
- GET /api/index?action=health
- GET /api/index?action=indicators&country=IN&range=2015:2025
- GET /api/index?action=news
- GET /api/index?action=interpret&country=IN&range=2015:2025
- GET /api/index?action=compare&countries=IN,US&range=2015:2025
- GET /api/index?action=analytics&country=IN&range=2015:2025
"""

import json
import os
import sys
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import parse_qs, urlparse

# Ensure project root is in sys.path so modules can be imported in serverless runtime
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import numpy as np
import pandas as pd

from modules.analysis import generate_all_interpretations
from modules.anomaly import detect_all_anomalies
from modules.correlation import compute_all_linklens
from modules.economic_data import (
    INDICATOR_METADATA,
    SUPPORTED_COUNTRIES,
    load_all_economic_data,
)
from modules.forecast import forecast_all_indicators
from modules.news_data import get_economic_news
from modules.sentiment import add_sentiment_scores, aggregate_mood, overall_mood
from modules.text_processing import categorize_dataframe_tfidf


def clean_for_json(obj):
    """Recursively sanitize NumPy/Pandas types and NaN values for standard JSON."""
    if isinstance(obj, dict):
        return {k: clean_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_for_json(v) for v in obj]
    elif isinstance(obj, float) and (np.isnan(obj) or np.isinf(obj)):
        return None
    elif isinstance(obj, (np.integer, np.int64)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64)):
        return round(float(obj), 4)
    elif isinstance(obj, pd.DataFrame):
        records = obj.replace({np.nan: None}).to_dict(orient="records")
        return clean_for_json(records)
    return obj


class handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        """Suppress standard logging in serverless environment."""
        pass

    def _send_json_response(self, status_code: int, data: dict):
        if not hasattr(self, "request_version"):
            self.request_version = "HTTP/1.1"
        if not hasattr(self, "requestline"):
            self.requestline = f"GET {getattr(self, 'path', '/')} HTTP/1.1"

        body = json.dumps(clean_for_json(data), ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        action = params.get("action", ["health"])[0].lower()
        country = params.get("country", ["IN"])[0].upper()
        date_range = params.get("range", ["2015:2025"])[0]

        try:
            if action == "health":
                self._send_json_response(200, {
                    "status": "healthy",
                    "service": "The Economic Interpreter Serverless API",
                    "runtime": "Vercel Python Serverless (@vercel/python)",
                    "endpoints": [
                        "?action=health",
                        "?action=indicators&country=IN&range=2015:2025",
                        "?action=news",
                        "?action=interpret&country=IN&range=2015:2025",
                        "?action=compare&countries=IN,US&range=2015:2025",
                        "?action=analytics&country=IN&range=2015:2025",
                    ],
                })

            elif action == "indicators":
                data = load_all_economic_data(country_code=country, date_range=date_range)
                serialized = {}
                for key, item in data.items():
                    serialized[key] = {
                        "metadata": item.get("metadata", {}),
                        "summary": item.get("summary", {}),
                        "records": item.get("data", pd.DataFrame()),
                    }
                self._send_json_response(200, {
                    "country": country,
                    "date_range": date_range,
                    "indicators": serialized,
                })

            elif action == "news":
                use_sample = params.get("use_sample", ["false"])[0].lower() == "true"
                news_payload = get_economic_news(use_sample_data=use_sample)
                categorized_df = categorize_dataframe_tfidf(news_payload.get("articles", pd.DataFrame()))

                self._send_json_response(200, {
                    "source_type": news_payload.get("source_type"),
                    "is_sample": news_payload.get("is_sample"),
                    "article_count": len(categorized_df),
                    "articles": categorized_df,
                })

            elif action == "interpret":
                use_sample = params.get("use_sample", ["false"])[0].lower() == "true"
                econ_data = load_all_economic_data(country_code=country, date_range=date_range)
                news_payload = get_economic_news(use_sample_data=use_sample)
                categorized_df = categorize_dataframe_tfidf(news_payload.get("articles", pd.DataFrame()))
                interpretations = generate_all_interpretations(econ_data, categorized_df)

                self._send_json_response(200, {
                    "country": country,
                    "date_range": date_range,
                    "interpretations": interpretations,
                })

            elif action == "compare":
                raw_countries = params.get("countries", ["IN,US"])[0]
                codes = [c.strip().upper() for c in raw_countries.split(",") if c.strip()]
                codes = [c for c in codes if c in SUPPORTED_COUNTRIES][:2]
                if len(codes) < 2:
                    self._send_json_response(400, {
                        "error": "Comparison needs two valid country codes, e.g. ?action=compare&countries=IN,US",
                        "supported": sorted(SUPPORTED_COUNTRIES.keys()),
                    })
                    return
                comparison = {}
                for code in codes:
                    data = load_all_economic_data(country_code=code, date_range=date_range)
                    comparison[code] = {
                        key: {
                            "metadata": item.get("metadata", {}),
                            "summary": item.get("summary", {}),
                            "records": item.get("data", pd.DataFrame()),
                        }
                        for key, item in data.items()
                    }
                self._send_json_response(200, {
                    "countries": codes,
                    "country_names": {c: SUPPORTED_COUNTRIES[c] for c in codes},
                    "date_range": date_range,
                    "comparison": comparison,
                })

            elif action == "analytics":
                use_sample = params.get("use_sample", ["false"])[0].lower() == "true"
                econ_data = load_all_economic_data(country_code=country, date_range=date_range)
                news_payload = get_economic_news(use_sample_data=use_sample)
                articles_df = categorize_dataframe_tfidf(news_payload.get("articles", pd.DataFrame()))
                articles_df = add_sentiment_scores(articles_df)

                self._send_json_response(200, {
                    "country": country,
                    "date_range": date_range,
                    "news_pulse": {
                        "overall": overall_mood(articles_df) if not articles_df.empty else None,
                        "by_topic": aggregate_mood(articles_df) if not articles_df.empty else pd.DataFrame(),
                    },
                    "shock_radar": detect_all_anomalies(econ_data),
                    "outlook": forecast_all_indicators(econ_data),
                    "linklens": compute_all_linklens(articles_df, econ_data),
                    "article_count": len(articles_df),
                    "is_sample": news_payload.get("is_sample"),
                })

            else:
                self._send_json_response(400, {
                    "error": f"Unknown action: '{action}'. Expected 'health', 'indicators', 'news', 'interpret', 'compare', or 'analytics'."
                })

        except Exception as err:
            self._send_json_response(500, {
                "error": "Internal server error during data processing",
                "details": str(err),
            })
