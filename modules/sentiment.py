"""
News Pulse — Sentiment Analysis Module
======================================
Scores the emotional tone (positive / neutral / negative) of every news
headline and description using VADER (Valence Aware Dictionary and sEntiment
Reasoner).

Why VADER:
- Runs fully offline and locally: no API keys, no network calls, no cost.
- Deterministic: the same text always produces the same score.
- Transparent: based on a published, inspectable sentiment lexicon
  (Hutto & Gilbert, 2014) rather than a black-box model.

In accordance with GEMINI.md:
- No fabricated data: if VADER is unavailable, scores are reported as
  neutral and the UI explicitly notes the fallback instead of inventing tone.
- Every score is shown to the user alongside its plain-English label.
"""

from typing import Any, Dict, List
import pandas as pd

try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    _ANALYZER = SentimentIntensityAnalyzer()
    VADER_AVAILABLE = True
except Exception:
    _ANALYZER = None
    VADER_AVAILABLE = False

# Compound score thresholds recommended by the VADER authors
POSITIVE_THRESHOLD = 0.05
NEGATIVE_THRESHOLD = -0.05


def score_sentiment(text: str) -> Dict[str, Any]:
    """
    Score the sentiment of a single piece of text.

    Parameters:
        text: Headline or combined headline + description text.

    Returns:
        dict with:
            - 'score': VADER compound score in [-1.0, 1.0].
            - 'label': 'Positive', 'Negative', or 'Neutral'.
            - 'vader_used': True when the real VADER lexicon produced the score.
    """
    if not isinstance(text, str) or not text.strip():
        return {"score": 0.0, "label": "Neutral", "vader_used": False}

    if not VADER_AVAILABLE or _ANALYZER is None:
        # Honest fallback: report neutral rather than guessing a tone.
        return {"score": 0.0, "label": "Neutral", "vader_used": False}

    compound = _ANALYZER.polarity_scores(text)["compound"]
    return {
        "score": round(float(compound), 3),
        "label": sentiment_label(compound),
        "vader_used": True,
    }


def sentiment_label(score: float) -> str:
    """
    Convert a VADER compound score into a plain-English label.

    Parameters:
        score: Compound sentiment score in [-1.0, 1.0].

    Returns:
        str: 'Positive', 'Negative', or 'Neutral'.
    """
    if score >= POSITIVE_THRESHOLD:
        return "Positive"
    if score <= NEGATIVE_THRESHOLD:
        return "Negative"
    return "Neutral"


def add_sentiment_scores(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add News Pulse sentiment columns to a news articles DataFrame.

    Adds columns:
        - 'sentiment_score': compound score in [-1.0, 1.0].
        - 'sentiment_label': 'Positive' / 'Negative' / 'Neutral'.

    Missing titles or descriptions are handled safely. An empty DataFrame
    returns empty with the new columns present.
    """
    df_copy = df.copy()

    if df_copy.empty:
        df_copy["sentiment_score"] = pd.Series(dtype="float64")
        df_copy["sentiment_label"] = pd.Series(dtype="str")
        return df_copy

    scores: List[float] = []
    labels: List[str] = []

    for _, row in df_copy.iterrows():
        title_val = row.get("title", "")
        desc_val = row.get("description", "")
        title = str(title_val) if pd.notna(title_val) and str(title_val).lower() != "none" else ""
        desc = str(desc_val) if pd.notna(desc_val) and str(desc_val).lower() != "none" else ""
        combined = f"{title} {desc}".strip()

        result = score_sentiment(combined)
        scores.append(result["score"])
        labels.append(result["label"])

    df_copy["sentiment_score"] = scores
    df_copy["sentiment_label"] = labels
    return df_copy


def aggregate_mood(df: pd.DataFrame, group_col: str = "category") -> pd.DataFrame:
    """
    Aggregate News Pulse scores into an overall mood per topic.

    Parameters:
        df: DataFrame with 'sentiment_score' and the grouping column.
        group_col: Column to group by (default: news topic 'category').

    Returns:
        pd.DataFrame with columns [group_col, 'article_count', 'avg_score',
        'mood_label'] sorted by article count descending. Empty input returns
        an empty DataFrame with the same columns.
    """
    columns = [group_col, "article_count", "avg_score", "mood_label"]

    if df.empty or "sentiment_score" not in df.columns or group_col not in df.columns:
        return pd.DataFrame(columns=columns)

    grouped = (
        df.groupby(group_col)["sentiment_score"]
        .agg(article_count="count", avg_score="mean")
        .reset_index()
        .sort_values(by="article_count", ascending=False)
        .reset_index(drop=True)
    )
    grouped["avg_score"] = grouped["avg_score"].round(3)
    grouped["mood_label"] = grouped["avg_score"].apply(sentiment_label)
    return grouped[columns]


def overall_mood(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Compute one headline mood summary across all scored articles.

    Returns:
        dict with 'avg_score', 'mood_label', 'article_count', and
        'vader_used'. When no scored articles exist, 'mood_label' is
        'No data'.
    """
    if df.empty or "sentiment_score" not in df.columns:
        return {"avg_score": None, "mood_label": "No data", "article_count": 0, "vader_used": VADER_AVAILABLE}

    avg = float(df["sentiment_score"].mean())
    return {
        "avg_score": round(avg, 3),
        "mood_label": sentiment_label(avg),
        "article_count": int(len(df)),
        "vader_used": VADER_AVAILABLE,
    }
