"""
PDF Report Export Module
========================
Builds a one-click, deterministic PDF report of the current analysis:
latest indicator observations, honest interpretations, and news topic
summary. No AI text generation - the report assembles the same template
sentences the app already displays.

The PDF uses fpdf2's built-in core fonts and ASCII-safe text so it renders
identically everywhere (no font downloads, no network calls).
"""

import re
from datetime import datetime, timezone
from typing import Any, Dict, List

try:
    from fpdf import FPDF
    FPDF_AVAILABLE = True
except Exception:
    FPDF_AVAILABLE = False


def _ascii_safe(text: Any) -> str:
    """Replace characters outside Latin-1 with ASCII equivalents for core fonts."""
    if text is None:
        return ""
    cleaned = str(text)
    replacements = {
        "\u2013": "-", "\u2014": "-", "\u2018": "'", "\u2019": "'",
        "\u201c": '"', "\u201d": '"', "\u2026": "...", "\u00a0": " ",
        "\u2192": "->", "\u20b9": "Rs.", "\u00d7": "x",
    }
    for src, dst in replacements.items():
        cleaned = cleaned.replace(src, dst)
    return cleaned.encode("latin-1", errors="replace").decode("latin-1")


def _strip_heading_prefix(text: str) -> str:
    """Remove template prefixes like 'Observed Trend:' for compact report lines."""
    return re.sub(r"^(Observed Trend|Possible Economic Mechanism|Analytical Boundaries & Limitations)\s*:\s*", "", text or "")


def build_pdf_report(
    country_name: str,
    economic_data: Dict[str, Dict[str, Any]],
    interpretations: Dict[str, Dict[str, Any]],
    articles_df=None,
) -> bytes:
    """
    Render the current analysis as a deterministic PDF report.

    Parameters:
        country_name: Display name of the selected country.
        economic_data: load_all_economic_data() result.
        interpretations: generate_all_interpretations() result.
        articles_df: Optional categorized news DataFrame for the topic summary.

    Returns:
        bytes: The PDF file contents.

    Raises:
        RuntimeError: If fpdf2 is not installed.
    """
    if not FPDF_AVAILABLE:
        raise RuntimeError("fpdf2 is not installed; PDF export is unavailable.")

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # --- Header ---
    pdf.set_font("helvetica", style="B", size=18)
    pdf.cell(0, 10, _ascii_safe("The Economic Interpreter"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", size=12)
    pdf.cell(0, 8, _ascii_safe(f"Economic Analysis Report - {country_name}"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", size=9)
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    pdf.cell(0, 6, _ascii_safe(
        f"Generated: {generated} | Data source: World Bank Indicators API (annual observations)"
    ), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # --- Section 1: Latest observations ---
    pdf.set_font("helvetica", style="B", size=13)
    pdf.cell(0, 8, "1. Latest Recorded Observations", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", size=10)
    for key, item in economic_data.items():
        meta = item.get("metadata", {})
        summary = item.get("summary", {})
        name = meta.get("name", key)
        unit = meta.get("unit", "%")
        if summary.get("has_data"):
            change = summary.get("change")
            prev_year = summary.get("previous_year")
            change_txt = (
                f" | Change: {change:+.2f} pts vs {prev_year}"
                if change is not None and prev_year is not None else ""
            )
            line = (
                f"{name}: {summary['latest_value']:.2f} {unit} "
                f"(reporting year {summary['latest_year']}){change_txt}"
            )
        else:
            line = f"{name}: no recorded observations in the selected range."
        pdf.multi_cell(0, 6, _ascii_safe(line), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    # --- Section 2: Interpretations ---
    pdf.set_font("helvetica", style="B", size=13)
    pdf.cell(0, 8, "2. Interpretation & Evidence", new_x="LMARGIN", new_y="NEXT")
    for key, interp in interpretations.items():
        pdf.set_font("helvetica", style="B", size=11)
        pdf.cell(0, 7, _ascii_safe(interp.get("indicator_name", key)), new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("helvetica", size=10)
        if not interp.get("has_data"):
            pdf.multi_cell(0, 6, _ascii_safe(interp.get("observed_trend", "Data unavailable.")), new_x="LMARGIN", new_y="NEXT")
            pdf.ln(2)
            continue

        pdf.multi_cell(0, 6, _ascii_safe(f"Observed trend: {_strip_heading_prefix(interp.get('observed_trend'))}"), new_x="LMARGIN", new_y="NEXT")
        pdf.multi_cell(0, 6, _ascii_safe(f"Possible mechanism: {_strip_heading_prefix(interp.get('possible_explanation'))}"), new_x="LMARGIN", new_y="NEXT")

        related = interp.get("relevant_news", [])
        if related:
            pdf.multi_cell(0, 6, _ascii_safe("Potentially related news headlines:"), new_x="LMARGIN", new_y="NEXT")
            for art in related:
                title = art.get("title", "")
                source = art.get("source", "")
                pdf.multi_cell(0, 6, _ascii_safe(f"  - {title} ({source})"), new_x="LMARGIN", new_y="NEXT")
        else:
            pdf.multi_cell(0, 6, _ascii_safe("No matching news topics were found in the current feed."), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)

    # --- Section 3: News topic summary ---
    pdf.set_font("helvetica", style="B", size=13)
    pdf.cell(0, 8, "3. News Topic Summary", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", size=10)
    if articles_df is not None and not articles_df.empty and "category" in articles_df.columns:
        counts = articles_df["category"].value_counts().to_dict()
        total = len(articles_df)
        pdf.multi_cell(0, 6, _ascii_safe(f"{total} deduplicated articles were categorized with transparent TF-IDF-weighted keyword matching:"), new_x="LMARGIN", new_y="NEXT")
        for category, count in counts.items():
            pdf.multi_cell(0, 6, _ascii_safe(f"  - {category}: {count} article(s)"), new_x="LMARGIN", new_y="NEXT")
    else:
        pdf.multi_cell(0, 6, _ascii_safe("No news articles were available when this report was generated."), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    # --- Section 4: Methodology & limitations ---
    pdf.set_font("helvetica", style="B", size=13)
    pdf.cell(0, 8, "4. Methodology & Limitations", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", size=9)
    for line in [
        "Indicator values are annual World Bank observations; missing years are reported as missing, never filled.",
        "News is categorized by TF-IDF-weighted keyword matching over a fixed, published topic list - fully deterministic.",
        "Explanations are educational templates: they describe possible mechanisms, not proven causes.",
        "Correlation in timing does not establish causation; annual national aggregates cannot prove why events happened.",
        "This report is for education only - not financial, investment, or policy advice.",
    ]:
        pdf.multi_cell(0, 5, _ascii_safe(f"- {line}"), new_x="LMARGIN", new_y="NEXT")

    return bytes(pdf.output())
