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
from typing import Dict, List, Optional, Set, Tuple
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
        title_val = row.get("title", "")
        desc_val = row.get("description", "")
        title = str(title_val) if pd.notna(title_val) and str(title_val).lower() != "none" else ""
        desc = str(desc_val) if pd.notna(desc_val) and str(desc_val).lower() != "none" else ""
        combined_text = f"{title} {desc}".strip()

        category, matched = categorize_article_text(combined_text)
        categories.append(category)
        keywords_list.append(", ".join(matched) if matched else "None")

    df_copy["category"] = categories
    df_copy["matched_keywords"] = keywords_list
    return df_copy


# ---------------------------------------------------------------------------
# TF-IDF upgrade (Feature: smarter news tagging)
# ---------------------------------------------------------------------------
# The original matcher ranked topics by raw keyword COUNT. That overvalues
# common words ("price" appears everywhere). TF-IDF (term frequency-inverse
# document frequency) fixes this transparently: a term's weight rises with
# how often it appears in the article and falls with how many articles in
# the current feed contain it. Rare, specific terms like "repo rate" or
# "layoffs" therefore outweigh generic ones like "price".
#
# Everything below is plain arithmetic on the article corpus - deterministic,
# offline, and easy to explain in a viva. No external NLP library is added.

import math


def compute_corpus_tfidf(documents: List[str]) -> List[Dict[str, float]]:
    """
    Compute TF-IDF weights for every token of every document.

    Parameters:
        documents: Raw document texts (title + description per article).

    Returns:
        List[Dict[str, float]]: One dict per document mapping token -> TF-IDF
        weight. Tokens come from tokenize() (lowercase, stopwords removed).
        TF = token count / document length; IDF = ln((1 + N) / (1 + df)) + 1,
        the standard smoothed variant, so a term in every document still gets
        a small positive weight instead of zero.
    """
    tokenized = [tokenize(doc) for doc in documents]
    n_docs = len(tokenized)

    # Document frequency per token
    doc_freq: Dict[str, int] = {}
    for tokens in tokenized:
        for token in set(tokens):
            doc_freq[token] = doc_freq.get(token, 0) + 1

    tfidf_maps: List[Dict[str, float]] = []
    for tokens in tokenized:
        weights: Dict[str, float] = {}
        if tokens:
            length = len(tokens)
            for token in set(tokens):
                tf = tokens.count(token) / length
                idf = math.log((1 + n_docs) / (1 + doc_freq.get(token, 0))) + 1.0
                weights[token] = round(tf * idf, 6)
        tfidf_maps.append(weights)

    return tfidf_maps


def extract_key_terms(tfidf_map: Dict[str, float], top_n: int = 5) -> List[str]:
    """
    Return the highest-weighted terms of a document - its TF-IDF key terms.

    Parameters:
        tfidf_map: Token -> TF-IDF weight for one document.
        top_n: How many terms to return.

    Returns:
        List[str]: Terms sorted by descending weight (ties alphabetical).
    """
    if not tfidf_map or top_n <= 0:
        return []
    ordered = sorted(tfidf_map.items(), key=lambda kv: (-kv[1], kv[0]))
    return [term for term, _ in ordered[:top_n]]


def _keyword_tfidf_weight(keyword: str, tfidf_map: Dict[str, float]) -> float:
    """Weight of a matched keyword = summed TF-IDF of its tokens (1.0 per unknown token)."""
    tokens = [t for t in tokenize(keyword)]
    if not tokens:
        return 0.0
    return sum(tfidf_map.get(token, 1.0) for token in tokens)


def categorize_article_text_tfidf(
    text: str,
    tfidf_map: Optional[Dict[str, float]] = None,
) -> Tuple[str, List[str]]:
    """
    Categorize text with TF-IDF-weighted keyword matching.

    Same transparent keyword lists as categorize_article_text(), but the
    winning topic is chosen by summed TF-IDF weight of its matched keywords
    instead of raw match count. Rare, specific terms dominate - e.g. an
    article mentioning both "price" and "repo rate" is scored as Monetary
    Policy because "repo rate" is far more distinctive than "price".

    Parameters:
        text: Headline or article text.
        tfidf_map: Token weights for this document (from compute_corpus_tfidf).
                   Pass None or {} to fall back to raw match counting.

    Returns:
        Tuple[str, List[str]]: (topic name, matched keywords that triggered it).
    """
    normalized = normalize_text(text)
    if not normalized:
        return DEFAULT_CATEGORY, []

    if not tfidf_map:
        return categorize_article_text(text)

    category_scores: Dict[str, float] = {}
    category_keywords: Dict[str, List[str]] = {}

    for category, keywords in TOPIC_KEYWORDS.items():
        matched_for_cat: List[str] = []
        weight = 0.0
        for kw in keywords:
            pattern = r"\b" + re.escape(kw) + r"\b"
            if re.search(pattern, normalized):
                matched_for_cat.append(kw)
                weight += _keyword_tfidf_weight(kw, tfidf_map)
        if matched_for_cat:
            category_scores[category] = weight
            category_keywords[category] = matched_for_cat

    if not category_scores:
        return DEFAULT_CATEGORY, []

    best_category = max(category_scores.keys(), key=lambda cat: category_scores[cat])
    return best_category, category_keywords[best_category]


def categorize_dataframe_tfidf(df: pd.DataFrame) -> pd.DataFrame:
    """
    Categorize articles with TF-IDF-weighted matching and tag key terms.

    Same output columns as categorize_dataframe() plus:
        - 'key_terms': comma-separated top TF-IDF terms of the article.

    Falls back to raw count matching when the corpus has fewer than two
    usable documents (IDF needs a corpus to be meaningful).
    """
    base = categorize_dataframe(df)
    if base.empty:
        base["key_terms"] = pd.Series(dtype="str")
        return base

    documents: List[str] = []
    for _, row in base.iterrows():
        title_val = row.get("title", "")
        desc_val = row.get("description", "")
        title = str(title_val) if pd.notna(title_val) and str(title_val).lower() != "none" else ""
        desc = str(desc_val) if pd.notna(desc_val) and str(desc_val).lower() != "none" else ""
        documents.append(f"{title} {desc}".strip())

    usable = [d for d in documents if d]
    if len(usable) < 2:
        base["key_terms"] = [", ".join(tokenize(d)[:5]) if d else "None" for d in documents]
        return base

    tfidf_maps = compute_corpus_tfidf(documents)

    categories: List[str] = []
    keywords_list: List[str] = []
    key_terms_list: List[str] = []

    for doc, tfidf_map in zip(documents, tfidf_maps):
        category, matched = categorize_article_text_tfidf(doc, tfidf_map)
        categories.append(category)
        keywords_list.append(", ".join(matched) if matched else "None")
        terms = extract_key_terms(tfidf_map, top_n=5)
        key_terms_list.append(", ".join(terms) if terms else "None")

    base["category"] = categories
    base["matched_keywords"] = keywords_list
    base["key_terms"] = key_terms_list
    return base
