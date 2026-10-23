"""
Text Processing & NLP Module
============================
Provides lightweight, transparent, and explainable Natural Language Processing
(NLP) utilities for cleaning text and categorizing economic articles.

In accordance with GEMINI.md:
- Rule-based keyword matching (transparent and easy to explain).
- No black-box machine learning or complex deep learning pipelines.
- Explains why an article was categorized by returning matched keywords.
"""

import re
import string
from typing import Dict, List, Set, Tuple
import pandas as pd

# Core economic topics and transparent keyword dictionaries
TOPIC_KEYWORDS: Dict[str, List[str]] = {
    "Inflation": [
        "inflation", "cpi", "price", "prices", "food inflation", "retail inflation",
        "wholesale price", "wpi", "cost of living", "fuel price", "costly",
        "price rise", "price hike", "deflation", "headline inflation", "core inflation",
    ],
    "Employment": [
        "employment", "unemployment", "job", "jobs", "hiring", "layoff", "layoffs",
        "labor", "labour", "workforce", "payroll", "workers", "wage", "wages",
        "recruitment", "staffing", "labor force", "ilo",
    ],
    "GDP and Economic Growth": [
        "gdp", "growth", "gross domestic product", "expansion", "output",
        "industrial production", "manufacturing", "services pmi", "economy expands",
        "recession", "contraction", "capital expenditure", "capex", "exports",
        "trade deficit", "economic activity",
    ],
    "Monetary Policy": [
        "repo rate", "interest rate", "interest rates", "monetary policy",
        "rbi", "reserve bank", "central bank", "rate cut", "rate hike",
        "policy stance", "mpc", "basis points", "bps", "liquidity",
        "tightening", "easing",
    ],
}

DEFAULT_CATEGORY = "Other Economic News"

# Standard English stopwords for lightweight keyword extraction
BASIC_STOPWORDS: Set[str] = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
    "any", "are", "as", "at", "be", "because", "been", "before", "being", "below",
    "between", "both", "but", "by", "could", "did", "do", "does", "doing", "down",
    "during", "each", "few", "for", "from", "further", "had", "has", "have",
    "having", "he", "her", "here", "hers", "herself", "him", "himself", "his",
    "how", "i", "if", "in", "into", "is", "it", "its", "itself", "just", "me",
    "more", "most", "my", "myself", "no", "nor", "not", "now", "of", "off", "on",
    "once", "only", "or", "other", "ought", "our", "ours", "ourselves", "out",
    "over", "own", "same", "she", "should", "so", "some", "such", "than", "that",
    "the", "their", "theirs", "them", "themselves", "then", "there", "these",
    "they", "this", "those", "through", "to", "too", "under", "until", "up",
    "very", "was", "we", "were", "what", "when", "where", "which", "while",
    "who", "whom", "why", "with", "would", "you", "your", "yours", "yourself",
}


def normalize_text(text: str) -> str:
    """
    Normalize text by lowercasing, stripping extra whitespace,
    and removing non-alphanumeric punctuation.

    Parameters:
        text: Raw input text.

    Returns:
        str: Normalized text string.
    """
    if not isinstance(text, str):
        return ""

    # Convert to lowercase
    text = text.lower()

    # Replace punctuation characters with spaces to avoid merging words
    for char in string.punctuation:
        text = text.replace(char, " ")

    # Collapse multiple spaces into one and strip edges
    return re.sub(r"\s+", " ", text).strip()


def tokenize(text: str) -> List[str]:
    """
    Tokenize text into lowercase words of length >= 2, excluding common stopwords.
    """
    normalized = normalize_text(text)
    words = re.findall(r"\b[a-z]{2,}\b", normalized)
    return [w for w in words if w not in BASIC_STOPWORDS]


def categorize_article_text(text: str) -> Tuple[str, List[str]]:
    """
    Categorize text using transparent keyword matching.

    Parameters:
        text: The headline or full article text to classify.

    Returns:
        Tuple[str, List[str]]:
            - Assigned topic name.
            - List of specific keywords that triggered the classification.
    """
    normalized = normalize_text(text)
    if not normalized:
        return DEFAULT_CATEGORY, []

    category_scores: Dict[str, List[str]] = {}

    for category, keywords in TOPIC_KEYWORDS.items():
        matched_for_cat: List[str] = []
        for kw in keywords:
            # Match keyword as whole word or phrase using word boundaries
            pattern = r"\b" + re.escape(kw) + r"\b"
            if re.search(pattern, normalized):
                matched_for_cat.append(kw)

        if matched_for_cat:
            category_scores[category] = matched_for_cat

    # If no economic keywords matched, assign default category
    if not category_scores:
        return DEFAULT_CATEGORY, []

    # Select the category with the highest number of matched keywords
    # In case of tie, prioritize order: Inflation > Monetary Policy > GDP > Employment
    best_category = max(
        category_scores.keys(),
        key=lambda cat: len(category_scores[cat]),
    )

    return best_category, category_scores[best_category]


def categorize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply text processing and topic categorization to a DataFrame of news articles.

    Expects columns 'title' and optional 'description'.
    Adds columns:
        - 'category': The classified topic name.
        - 'matched_keywords': Comma-separated string of triggering keywords.

    Returns:
        pd.DataFrame: Augmented DataFrame.
    """
    if df.empty:
        df_copy = df.copy()
        df_copy["category"] = pd.Series(dtype="str")
        df_copy["matched_keywords"] = pd.Series(dtype="str")
        return df_copy

    df_copy = df.copy()

    categories: List[str] = []
    keywords_list: List[str] = []

    for _, row in df_copy.iterrows():
        title = str(row.get("title", ""))
        desc = str(row.get("description", ""))
        combined_text = f"{title} {desc}"

        category, matched = categorize_article_text(combined_text)
        categories.append(category)
        keywords_list.append(", ".join(matched) if matched else "None")

    df_copy["category"] = categories
    df_copy["matched_keywords"] = keywords_list
    return df_copy
