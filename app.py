"""
The Economic Interpreter
========================
A beginner-friendly data science application that helps users understand
the relationship between macroeconomic indicators (inflation, unemployment,
GDP growth, trade and investment flows) and economic news.

Author: Open Source Academic Research
License: Academic / Educational
"""

from typing import Dict, Any, List, Optional
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

from modules.economic_data import (
    load_all_economic_data,
    load_comparison_data,
    INDICATOR_METADATA,
    SUPPORTED_COUNTRIES,
    DEFAULT_COUNTRY,
)
from modules.news_data import get_economic_news
from modules.text_processing import (
    categorize_dataframe_tfidf,
    TOPIC_KEYWORDS,
    DEFAULT_CATEGORY,
)
from modules.analysis import generate_all_interpretations
from modules.comparison import build_comparison_table, align_series_for_years
from modules.report import build_pdf_report, FPDF_AVAILABLE
from modules.sentiment import (
    add_sentiment_scores,
    aggregate_mood,
    overall_mood,
    VADER_AVAILABLE,
)
from modules.correlation import compute_all_linklens
from modules.anomaly import detect_all_anomalies
from modules.forecast import forecast_all_indicators

# Flag emoji for each supported country (display only; codes come from the data module)
COUNTRY_FLAGS = {
    "IN": "🇮🇳",
    "US": "🇺🇸",
    "CN": "🇨🇳",
    "GB": "🇬🇧",
    "DE": "🇩🇪",
    "JP": "🇯🇵",
    "AE": "🇦🇪",
    "SG": "🇸🇬",
}


def country_label(code: str) -> str:
    """Display label for a country code, e.g. 'India 🇮🇳'."""
    return f"{SUPPORTED_COUNTRIES.get(code, code)} {COUNTRY_FLAGS.get(code, '')}".strip()


# Color palette for clear, accessible chart rendering
INDICATOR_COLORS = {
    "inflation": "#e74c3c",             # Warm red / coral
    "unemployment": "#e67e22",          # Amber / orange
    "gdp_growth": "#2ecc71",            # Emerald green
    "gdp_per_capita_growth": "#16a085", # Teal
    "exports_gdp": "#2980b9",           # Blue
    "fdi_inflows_gdp": "#8e44ad",       # Purple
}

INDICATOR_ICONS = {
    "inflation": "🔥",
    "unemployment": "👥",
    "gdp_growth": "📈",
    "gdp_per_capita_growth": "🧑‍🤝‍🧑",
    "exports_gdp": "🚢",
    "fdi_inflows_gdp": "💰",
}

# Plain color cues for News Pulse tone labels
SENTIMENT_EMOJIS = {
    "Positive": "🟢",
    "Negative": "🔴",
    "Neutral": "⚪",
}


@st.cache_data(show_spinner=False)
def compute_news_pulse(articles_df: pd.DataFrame) -> pd.DataFrame:
    """Score every article's tone with News Pulse (cached per news fetch)."""
    return add_sentiment_scores(articles_df)


@st.cache_data(show_spinner=False)
def compute_shock_radar(economic_data: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Flag unusual indicator movements with Shock Radar (cached per data fetch)."""
    return detect_all_anomalies(economic_data)


@st.cache_data(show_spinner=False)
def compute_outlook(economic_data: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Project illustrative trend outlooks with Outlook Engine (cached per data fetch)."""
    return forecast_all_indicators(economic_data)


@st.cache_data(show_spinner=False)
def compute_linklens_bundle(
    articles_df: pd.DataFrame,
    economic_data: Dict[str, Dict[str, Any]],
) -> Dict[str, Dict[str, Any]]:
    """Correlate news tone/volume with indicator changes (cached per fetch)."""
    return compute_all_linklens(articles_df, economic_data)


def build_linklens_chart(overlap_df: pd.DataFrame, indicator_name: str) -> go.Figure:
    """Dual-axis LinkLens chart: news tone bars vs indicator change line."""
    from plotly.subplots import make_subplots

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Bar(
            x=overlap_df["year"],
            y=overlap_df["avg_sentiment"],
            name="Average news tone (News Pulse)",
            marker_color="#9b59b6",
            opacity=0.75,
            hovertemplate="Year %{x}<br>Average tone: %{y:+.2f}<extra></extra>",
        ),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=overlap_df["year"],
            y=overlap_df["indicator_change"],
            name=f"{indicator_name} yearly change",
            mode="lines+markers",
            line=dict(width=2.5, color="#2c3e50"),
            marker=dict(size=7),
            hovertemplate="Year %{x}<br>Change: %{y:+.2f} pts<extra></extra>",
        ),
        secondary_y=True,
    )
    fig.update_layout(
        title=f"LinkLens: News Tone vs {indicator_name} Change",
        template="plotly_white",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=40, r=40, t=60, b=40),
        height=400,
    )
    fig.update_yaxes(title_text="Average news tone (-1 to +1)", secondary_y=False)
    fig.update_yaxes(title_text="Indicator change (points per year)", secondary_y=True)
    return fig


def build_outlook_chart(
    history_df: pd.DataFrame,
    forecast_result: Dict[str, Any],
    color: str,
) -> go.Figure:
    """History line + dashed trend forecast with a shaded prediction band."""
    fig = go.Figure()

    valid = history_df.dropna(subset=["value"]).sort_values(by="year")
    fig.add_trace(
        go.Scatter(
            x=valid["year"],
            y=valid["value"],
            mode="lines+markers",
            name="Recorded history",
            line=dict(width=2.5, color=color),
            marker=dict(size=6),
            hovertemplate="Year %{x}<br>Recorded: %{y:.2f}<extra></extra>",
        )
    )

    fc_df = forecast_result["forecast"]
    if not fc_df.empty:
        # Bridge the gap between the last recorded year and the first forecast year
        bridge_x = [int(valid["year"].iloc[-1])] + list(fc_df["year"])
        bridge_y = [float(valid["value"].iloc[-1])] + list(fc_df["predicted"])

        fig.add_trace(
            go.Scatter(
                x=list(fc_df["year"]) + list(fc_df["year"])[::-1],
                y=list(fc_df["upper"]) + list(fc_df["lower"])[::-1],
                fill="toself",
                fillcolor="rgba(52, 152, 219, 0.15)",
                line=dict(color="rgba(255, 255, 255, 0)"),
                name="Likely range (approx. 95%)",
                hoverinfo="skip",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=bridge_x,
                y=bridge_y,
                mode="lines+markers",
                name="Trend outlook (illustrative)",
                line=dict(width=2.5, color="#3498db", dash="dash"),
                marker=dict(size=7, symbol="diamond"),
                hovertemplate="Year %{x}<br>Outlook: %{y:.2f}<extra></extra>",
            )
        )

    fig.update_layout(
        title=f"{forecast_result.get('indicator_name', 'Indicator')} — Trend Outlook",
        xaxis_title="Year",
        yaxis_title=forecast_result.get("unit", "%"),
        template="plotly_white",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=40, r=40, t=60, b=40),
        height=420,
    )
    return fig


def build_combined_trend_chart(indicators_data: Dict[str, Dict[str, Any]]) -> go.Figure:
    """
    Build an interactive multi-line Plotly chart displaying all indicators.

    Parameters:
        indicators_data: Output dictionary from load_all_economic_data.

    Returns:
        go.Figure: Styled Plotly figure.
    """
    fig = go.Figure()

    for key, item in indicators_data.items():
        meta = item["metadata"]
        df = item["data"]

        if df.empty or df["value"].dropna().empty:
            continue

        fig.add_trace(
            go.Scatter(
                x=df["year"],
                y=df["value"],
                mode="lines+markers",
                name=meta["name"],
                line=dict(width=2.5, color=INDICATOR_COLORS.get(key, "#3498db")),
                marker=dict(size=6),
                hovertemplate="<b>%{fullData.name}</b><br>Year: %{x}<br>Value: %{y:.2f}%<extra></extra>",
            )
        )

    fig.update_layout(
        title="Historical Economic Trends Comparison",
        xaxis_title="Reporting Year",
        yaxis_title="Annual Rate (%)",
        template="plotly_white",
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
        margin=dict(l=40, r=40, t=60, b=40),
        height=450,
    )

    # Add a subtle reference line at 0%
    fig.add_hline(y=0, line_dash="dash", line_color="rgba(128, 128, 128, 0.4)")
    return fig


def build_single_indicator_chart(
    df: pd.DataFrame,
    indicator_name: str,
    unit: str,
    color: str,
    anomalies: Optional[List[Dict[str, Any]]] = None,
) -> go.Figure:
    """
    Build a focused line chart for an individual indicator with descriptive annotations.
    Optionally marks Shock Radar flags as red triangles on the flagged years.
    """
    fig = go.Figure()

    if not df.empty and not df["value"].dropna().empty:
        valid_df = df.dropna(subset=["value"])

        fig.add_trace(
            go.Scatter(
                x=valid_df["year"],
                y=valid_df["value"],
                mode="lines+markers",
                name=indicator_name,
                line=dict(width=3, color=color),
                marker=dict(size=7, color=color),
                fill="tozeroy",
                fillcolor=f"rgba({int(color[1:3], 16)}, {int(color[3:5], 16)}, {int(color[5:7], 16)}, 0.08)",
                hovertemplate=f"<b>{indicator_name}</b><br>Year: %{{x}}<br>Rate: %{{y:.2f}} {unit}<extra></extra>",
            )
        )

        # Highlight latest point
        latest_row = valid_df.iloc[-1]
        fig.add_annotation(
            x=latest_row["year"],
            y=latest_row["value"],
            text=f"Latest: {latest_row['value']:.2f}% ({int(latest_row['year'])})",
            showarrow=True,
            arrowhead=2,
            arrowsize=1,
            arrowcolor=color,
            ax=0,
            ay=-35,
            font=dict(size=12, color=color, family="Arial, sans-serif"),
            bgcolor="rgba(255, 255, 255, 0.9)",
            bordercolor=color,
            borderwidth=1,
            borderpad=4,
        )

    if anomalies:
        fig.add_trace(
            go.Scatter(
                x=[a["year"] for a in anomalies],
                y=[a["value"] for a in anomalies],
                mode="markers",
                name="Shock Radar flag",
                marker=dict(symbol="triangle-up", size=14, color="#c0392b", line=dict(width=1, color="white")),
                hovertemplate="<b>🚨 Shock Radar flag</b><br>Year: %{x}<br>Value: %{y:.2f}<extra></extra>",
            )
        )

    fig.update_layout(
        title=f"{indicator_name} ({unit})",
        xaxis_title="Year",
        yaxis_title=unit,
        template="plotly_white",
        margin=dict(l=40, r=40, t=50, b=40),
        height=380,
    )

    fig.add_hline(y=0, line_dash="dash", line_color="rgba(150, 150, 150, 0.3)")
    return fig


def build_comparison_chart(
    aligned_df: pd.DataFrame,
    label_a: str,
    label_b: str,
    indicator_name: str,
    unit: str,
) -> go.Figure:
    """
    Two-country overlay chart for one indicator, drawn only from genuinely
    observed years. Missing years show as gaps, never invented values.
    """
    fig = go.Figure()

    if aligned_df.empty:
        return fig

    fig.add_trace(
        go.Scatter(
            x=aligned_df["year"],
            y=aligned_df["value_a"],
            mode="lines+markers",
            name=label_a,
            line=dict(width=2.8, color="#be123c"),
            marker=dict(size=6),
            connectgaps=False,
            hovertemplate=f"<b>{label_a}</b><br>Year: %{{x}}<br>Value: %{{y:.2f}} {unit}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=aligned_df["year"],
            y=aligned_df["value_b"],
            mode="lines+markers",
            name=label_b,
            line=dict(width=2.8, color="#1d4ed8", dash="dot"),
            marker=dict(size=6, symbol="diamond"),
            connectgaps=False,
            hovertemplate=f"<b>{label_b}</b><br>Year: %{{x}}<br>Value: %{{y:.2f}} {unit}<extra></extra>",
        )
    )

    fig.update_layout(
        title=f"{indicator_name} — {label_a} vs {label_b}",
        xaxis_title="Year",
        yaxis_title=unit,
        template="plotly_white",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=40, r=40, t=60, b=40),
        height=400,
    )
    fig.add_hline(y=0, line_dash="dash", line_color="rgba(150, 150, 150, 0.3)")
    return fig


def main() -> None:
    """Main application entry point for The Economic Interpreter."""
    # 1. Page Configuration
    st.set_page_config(
        page_title="The Economic Interpreter",
        page_icon="📈",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # 2. Header and Introduction
    st.title("📈 The Economic Interpreter")
    st.subheader("Demystifying Macroeconomic Trends and News")
    st.markdown(
        """
        Welcome to **The Economic Interpreter**. This educational tool connects 
        macroeconomic indicators—**Inflation**, **Unemployment**, **Real GDP Growth**, 
        **GDP per Capita**, **Exports** and **Foreign Direct Investment**—with 
        contemporary economic news using transparent Natural Language Processing (NLP).
        """
    )

    # 3. Sidebar Controls & Parameters
    with st.sidebar:
        st.header("⚙️ Controls & Parameters")

        country_codes = list(SUPPORTED_COUNTRIES.keys())
        selected_country_code = st.selectbox(
            "Select Country",
            options=country_codes,
            format_func=country_label,
            index=country_codes.index(DEFAULT_COUNTRY),
            help="Per project requirements, India is the default country.",
        )

        selected_years = st.slider(
            "Historical Time Range",
            min_value=2000,
            max_value=2025,
            value=(2010, 2025),
            step=1,
            help="Filter historical observations returned by the World Bank API.",
        )

        st.caption(f"Querying observations from **{selected_years[0]}** to **{selected_years[1]}**.")

        st.divider()
        st.subheader("🆚 Country Comparison")
        compare_options = [c for c in country_codes if c != selected_country_code]
        compare_country_code = st.selectbox(
            "Compare against (optional)",
            options=[None] + compare_options,
            format_func=lambda c: "— No comparison —" if c is None else country_label(c),
            help="Pick a second country to see the same indicators side-by-side.",
        )

        st.divider()
        st.subheader("📰 News Feed Settings")
        if "news_mode_override" not in st.session_state:
            st.session_state["news_mode_override"] = None

        default_news_idx = 1 if st.session_state.get("news_mode_override") == "Sample Dataset (Offline)" else 0
        news_mode = st.radio(
            "News Source",
            options=["Live News Feed", "Sample Dataset (Offline)"],
            index=default_news_idx,
            help="Live feed retrieves current articles via Google News RSS or NewsAPI. Sample dataset provides guaranteed offline articles.",
        )
        if news_mode == "Live News Feed" and st.session_state.get("news_mode_override") == "Sample Dataset (Offline)":
            st.session_state["news_mode_override"] = None
        use_sample_news = (news_mode == "Sample Dataset (Offline)")

        st.divider()
        if st.button("🔄 Refresh All Data Cache"):
            st.cache_data.clear()
            st.success("Cache cleared! Re-fetching fresh data.")
            st.rerun()

        st.divider()
        st.info(
            "💡 **Tip for Learners:** Economic indicators reflect historical observations. "
            "News articles reflect current developments. Correlation does not imply causation!"
        )

    # 4. Fetch Economic Data
    date_range_query = f"{selected_years[0]}:{selected_years[1]}"
    with st.spinner(f"Retrieving World Bank indicators for {country_label(selected_country_code)}..."):
        economic_data = load_all_economic_data(
            country_code=selected_country_code,
            date_range=date_range_query,
        )

    # Optional comparison country (fetched only when selected)
    comparison_data = None
    if compare_country_code is not None:
        with st.spinner(f"Retrieving comparison indicators for {country_label(compare_country_code)}..."):
            comparison_data = load_comparison_data(
                country_codes=(selected_country_code, compare_country_code),
                date_range=date_range_query,
            )

    # Shock Radar scans the same observations for unusually sharp movements
    shock_radar = compute_shock_radar(economic_data)

    # 5. Section 1: Economic Overview Dashboard
    st.divider()
    st.header(f"1. Economic Overview — {country_label(selected_country_code)}")
    st.markdown(
        "Key macroeconomic health signals retrieved live from the **World Bank Indicators API**."
    )

    # 5.1 Indicator Metric Cards (3 per row, all supported indicators)
    indicator_keys = list(economic_data.keys())
    delta_color_by_key = {
        "inflation": "inverse",
        "unemployment": "inverse",
    }
    for row_start in range(0, len(indicator_keys), 3):
        row_keys = indicator_keys[row_start:row_start + 3]
        cols = st.columns(3)
        for col, key in zip(cols, row_keys):
            item = economic_data.get(key, {})
            summary = item.get("summary", {})
            meta = item.get("metadata", {})
            with col:
                if summary.get("has_data"):
                    val = f"{summary['latest_value']:.2f}%"
                    chg = summary.get("change")
                    prev_yr = summary.get("previous_year")
                    delta_label = f"{chg:+.2f} pp vs {prev_yr}" if chg is not None else None
                    st.metric(
                        label=meta.get("name", key),
                        value=val,
                        delta=delta_label,
                        delta_color=delta_color_by_key.get(key, "normal"),
                        help=meta.get("description", ""),
                    )
                    st.caption(f"📅 **Reporting Period:** {summary['latest_year']} | Code: `{meta.get('code', 'N/A')}`")
                else:
                    st.warning(f"{meta.get('name', key)} data unavailable for selected range.")

    # 5.2 Interactive Plotly Visualizations
    st.subheader("Historical Indicator Trends")

    tab_labels = ["📊 Combined Trends"] + [
        f"{INDICATOR_ICONS.get(key, '📉')} {economic_data[key]['metadata'].get('name', key)}"
        for key in indicator_keys
    ] + ["📋 Data Table"]
    tabs = st.tabs(tab_labels)

    with tabs[0]:
        combined_fig = build_combined_trend_chart(economic_data)
        st.plotly_chart(combined_fig, use_container_width=True)

    for tab, key in zip(tabs[1:-1], indicator_keys):
        item = economic_data[key]
        meta = item.get("metadata", {})
        with tab:
            fig = build_single_indicator_chart(
                df=item.get("data", pd.DataFrame()),
                indicator_name=meta.get("name", key),
                unit=meta.get("unit", "%"),
                color=INDICATOR_COLORS.get(key, "#3498db"),
                anomalies=shock_radar.get(key, {}).get("flags", []),
            )
            st.plotly_chart(fig, use_container_width=True)
            st.info(f"**About this indicator:** {meta.get('description')}")

    with tabs[-1]:
        st.markdown("#### Tabular Observations (World Bank Open Data)")
        # Merge available data for tabular viewing
        table_frames = []
        for key, item in economic_data.items():
            df = item["data"]
            if not df.empty:
                renamed = df[["year", "value"]].rename(columns={"value": item["metadata"]["name"]})
                table_frames.append(renamed)

        if table_frames:
            merged_table = table_frames[0]
            for other in table_frames[1:]:
                merged_table = pd.merge(merged_table, other, on="year", how="outer")
            merged_table = merged_table.sort_values(by="year", ascending=False).reset_index(drop=True)
            st.dataframe(
                merged_table.style.format(
                    {col: "{:.2f}%" for col in merged_table.columns if col != "year"},
                    na_rep="N/A",
                ),
                use_container_width=True,
            )
        else:
            st.write("No tabular observations to display.")

    # 5.3 Country Comparison View
    if comparison_data is not None:
        st.divider()
        label_a = country_label(selected_country_code)
        label_b = country_label(compare_country_code)
        st.header(f"1B. Country Comparison — {label_a} vs {label_b}")
        st.markdown(
            "The **same indicators** for both countries, drawn only from genuinely recorded "
            "World Bank observations. Where one country has no value for a year, the chart "
            "shows a gap rather than an invented number."
        )

        comp_tabs = st.tabs([
            f"{INDICATOR_ICONS.get(key, '📉')} {INDICATOR_METADATA[key].get('name', key)}"
            for key in indicator_keys
        ] + ["📋 Latest Values Table"])

        for tab, key in zip(comp_tabs[:-1], indicator_keys):
            with tab:
                df_a = comparison_data[selected_country_code][key]["data"]
                df_b = comparison_data[compare_country_code][key]["data"]
                aligned = align_series_for_years(df_a, df_b)
                meta = INDICATOR_METADATA[key]
                if aligned.empty:
                    st.info("No recorded observations for either country in this range.")
                else:
                    st.plotly_chart(
                        build_comparison_chart(aligned, label_a, label_b, meta.get("name", key), meta.get("unit", "%")),
                        use_container_width=True,
                    )
                    observed_years_a = int(aligned["value_a"].notna().sum())
                    observed_years_b = int(aligned["value_b"].notna().sum())
                    st.caption(
                        f"Observed years: {label_a} {observed_years_a}, {label_b} {observed_years_b} "
                        f"(annual data, gaps are years without a recorded observation)"
                    )

        with comp_tabs[-1]:
            comp_table = build_comparison_table(
                comparison_data,
                {selected_country_code: SUPPORTED_COUNTRIES[selected_country_code],
                 compare_country_code: SUPPORTED_COUNTRIES[compare_country_code]},
            )
            display_cols = ["indicator_name", "unit"] + [
                c for c in comp_table.columns if c not in ("indicator_key", "indicator_name", "unit")
            ]
            st.dataframe(
                comp_table[display_cols].rename(columns={"indicator_name": "Indicator", "unit": "Unit"}),
                use_container_width=True,
                hide_index=True,
            )
            st.caption(
                "Each value carries its own reporting year — the latest available year can differ "
                "between countries and indicators."
            )

    # 6. Section 2: Economic News
    st.divider()
    st.header(f"2. Economic News — {country_label(selected_country_code)}")
    st.markdown(
        "Current reporting and economic news coverage from verified public sources."
    )

    country_short_name = SUPPORTED_COUNTRIES[selected_country_code].split()[0]
    news_search_query = f"{country_short_name} economy inflation GDP unemployment"

    with st.spinner("Retrieving economic news articles..."):
        news_payload = get_economic_news(
            query=news_search_query,
            use_sample_data=use_sample_news,
        )

    articles_raw = news_payload["articles"]
    is_sample_news = news_payload["is_sample"]
    source_label = news_payload["source_type"]

    # TF-IDF-weighted NLP categorization (transparent and deterministic)
    articles_df = categorize_dataframe_tfidf(articles_raw)

    # News Pulse: score the tone of every article (local VADER lexicon)
    articles_df = compute_news_pulse(articles_df)

    # Status / Transparency Disclaimer per GEMINI.md
    if is_sample_news:
        st.warning(
            "⚠️ **Development Mode (Sample Dataset):** Displaying sample archived articles for offline testing. "
            "These articles are for development purposes and are not live news."
        )
    elif not articles_df.empty:
        st.success(f"🟢 **{source_label}**: Retrieved and categorized {len(articles_df)} deduplicated articles.")
    else:
        st.error(f"🔴 **{source_label}**: {news_payload.get('error', 'No articles could be retrieved.')}")
        if st.button("📁 Load Offline Sample Dataset"):
            st.session_state["news_mode_override"] = "Sample Dataset (Offline)"
            st.rerun()

    if news_payload.get("error") and not articles_df.empty:
        st.info(f"ℹ️ {news_payload['error']}")

    # 6.1 News Pulse — The Mood of the News (Sentiment Analysis)
    if not articles_df.empty and "sentiment_label" in articles_df.columns:
        st.markdown("##### 📰 News Pulse — The Mood of Today's Economic News")
        st.caption(
            "**What is this?** News Pulse reads the tone of every headline — 🟢 positive, ⚪ neutral, or 🔴 negative — "
            "using VADER, a published word-based sentiment lexicon that runs fully offline (no AI, no API keys). "
            "It is deterministic: the same text always gets the same score."
        )
        mood = overall_mood(articles_df)
        mood_by_topic = aggregate_mood(articles_df)

        pulse_cols = st.columns(len(mood_by_topic) + 1)
        with pulse_cols[0]:
            st.metric(
                label="🌍 Overall mood",
                value=f"{SENTIMENT_EMOJIS.get(mood['mood_label'], '⚪')} {mood['mood_label']}",
                help=f"Average tone across {mood['article_count']} articles: {mood['avg_score']:+.3f} on a -1 (very negative) to +1 (very positive) scale.",
            )
        for col, (_, topic_row) in zip(pulse_cols[1:], mood_by_topic.iterrows()):
            with col:
                st.metric(
                    label=str(topic_row["category"]),
                    value=f"{SENTIMENT_EMOJIS.get(topic_row['mood_label'], '⚪')} {topic_row['mood_label']}",
                    help=f"Average tone across {int(topic_row['article_count'])} articles in this topic: {topic_row['avg_score']:+.3f}",
                )
        if not VADER_AVAILABLE:
            st.info(
                "ℹ️ The VADER sentiment lexicon is not installed in this environment, so all tones show as neutral. "
                "Install `vaderSentiment` to enable News Pulse scoring."
            )
        st.write("")

    # 6.2 Topic Distribution Summary (NLP Educational Insight)
    if not articles_df.empty and "category" in articles_df.columns:
        cat_counts = articles_df["category"].value_counts().to_dict()
        st.markdown("##### 🏷️ Topic Categorization Distribution (TF-IDF-Weighted NLP)")
        st.caption(
            "Articles are tagged with the published topic keyword lists, but topics now win by **TF-IDF weight** "
            "instead of raw keyword count: rare, specific terms like *repo rate* outweigh common words like *price*. "
            "The arithmetic is shown per article under *Key terms*."
        )

        stat_cols = st.columns(5)
        stat_categories = [
            ("Inflation", "🔥"),
            ("Employment", "👥"),
            ("GDP and Economic Growth", "📈"),
            ("Monetary Policy", "🏦"),
            ("Other Economic News", "📰"),
        ]
        for col, (cat_name, cat_icon) in zip(stat_cols, stat_categories):
            count = cat_counts.get(cat_name, 0)
            with col:
                st.metric(label=f"{cat_icon} {cat_name.split()[0]}", value=f"{count} articles")

    st.write("")

    # 6.2 Dual Filter Controls (Category Dropdown + Keyword Search)
    filter_col1, filter_col2 = st.columns([1, 2])
    with filter_col1:
        topic_options = ["All Topics"] + list(TOPIC_KEYWORDS.keys()) + [DEFAULT_CATEGORY]
        selected_topic = st.selectbox(
            "Filter by Economic Topic:",
            options=topic_options,
            index=0,
            help="Filter articles categorized by our TF-IDF-weighted keyword matcher.",
        )

    with filter_col2:
        search_query = st.text_input(
            "Filter by Free-Text Keyword:",
            "",
            placeholder="e.g. food, repo rate, manufacturing, budget...",
        )

    # Apply Filters
    filtered_df = articles_df
    if selected_topic != "All Topics":
        filtered_df = filtered_df[filtered_df["category"] == selected_topic]

    if search_query:
        kw = search_query.strip().lower()
        filtered_df = filtered_df[
            filtered_df["title"].str.lower().str.contains(kw) |
            filtered_df["description"].str.lower().str.contains(kw)
        ]

    # 6.3 Article Cards Display
    if filtered_df.empty:
        st.info("No articles match your selected topic and keyword filter.")
    else:
        st.caption(f"Showing **{min(len(filtered_df), 12)}** of **{len(filtered_df)}** matching articles.")
        for _, article in filtered_df.head(12).iterrows():
            with st.container():
                st.markdown(f"##### [{article['title']}]({article['url']})")
                
                # Category and metadata line
                cat_badge = article.get("category", "General")
                kw_tags = article.get("matched_keywords", "None")
                key_terms = article.get("key_terms", "None")
                senti_label = article.get("sentiment_label", "Neutral")
                senti_score = article.get("sentiment_score", 0.0)
                senti_badge = f"{SENTIMENT_EMOJIS.get(senti_label, '⚪')} **Tone:** {senti_label} ({float(senti_score):+.2f})"
                st.markdown(
                    f"🏷️ **Category:** `{cat_badge}` &nbsp;|&nbsp; {senti_badge} &nbsp;|&nbsp; "
                    f"📰 **Source:** {article['source']} &nbsp;|&nbsp; "
                    f"🕒 **Published:** {article['published_at']}"
                )
                
                st.write(article["description"])
                if kw_tags and kw_tags != "None":
                    st.caption(f"💡 *Triggered by economic keywords:* `{kw_tags}`")
                if key_terms and key_terms != "None":
                    st.caption(f"🔑 *Key terms (highest TF-IDF weight):* `{key_terms}`")
                st.divider()

    # 7. Section 3: Interpretation & Analysis
    st.divider()
    st.header(f"3. Economic Interpretation & Synthesis — {country_label(selected_country_code)}")
    st.markdown(
        """
        This section connects the **empirical indicator observations** from Section 1 with the 
        **thematic news coverage** from Section 2 using deterministic educational explanation templates.
        """
    )

    with st.spinner("Synthesizing economic trends with news topics..."):
        interpretations = generate_all_interpretations(
            economic_data=economic_data,
            categorized_news_df=articles_df,
        )

    # Indicator Interpretations Tabs (all supported indicators)
    interp_tabs = st.tabs([
        f"{INDICATOR_ICONS.get(key, '📉')} {INDICATOR_METADATA[key].get('name', key)}"
        for key in indicator_keys
    ])

    for tab, key in zip(interp_tabs, indicator_keys):
        item = interpretations.get(key, {})
        icon = INDICATOR_ICONS.get(key, "📉")
        with tab:
            st.subheader(f"{icon} {item.get('indicator_name', key.title())}")

            if not item.get("has_data"):
                st.warning(item.get("observed_trend", "Data unavailable."))
            else:
                st.caption(
                    f"⏱️ **Data Time Horizons:** Indicator Observation: `{item.get('indicator_period', 'Annual')}` &nbsp;|&nbsp; "
                    f"News Feed: `{item.get('news_period', 'Recent')}`"
                )

                # 1. Observed Trend
                st.markdown(f"##### 1. 🔍 {item.get('observed_trend')}")

                # 2. Relevant News
                st.markdown("##### 2. 📰 Potentially Related News Articles")
                rel_news = item.get("relevant_news", [])
                if rel_news:
                    for article in rel_news:
                        st.markdown(
                            f"- **[{article['title']}]({article['url']})**  \n"
                            f"  *Source: {article['source']} | Topic: `{article['category']}` | Date: {article['published_at']}*"
                        )
                else:
                    st.info("No articles matching this topic were identified in the current news feed sample.")

                # 3. Possible Economic Mechanism
                st.markdown(f"##### 3. 💡 {item.get('possible_explanation')}")

                # 4. Limitations & Uncertainty
                st.info(f"⚠️ **{item.get('limitations')}**")

    # 7.1 PDF Report Export
    st.subheader("📄 Export This Analysis as a PDF Report")
    st.caption(
        "One click downloads the sections above — latest observations, interpretations, related headlines "
        "and the methodology notes — as a tidy PDF you can attach to a submission or share."
    )
    if FPDF_AVAILABLE:
        try:
            pdf_bytes = build_pdf_report(
                country_name=SUPPORTED_COUNTRIES[selected_country_code],
                economic_data=economic_data,
                interpretations=interpretations,
                articles_df=articles_df,
            )
            st.download_button(
                label="⬇️ Download PDF Report",
                data=pdf_bytes,
                file_name=f"economic_interpreter_report_{selected_country_code.lower()}.pdf",
                mime="application/pdf",
            )
        except Exception as err:
            st.error(f"PDF report could not be generated: {err}")
    else:
        st.info("ℹ️ PDF export needs the `fpdf2` package, which is not installed in this environment.")

    # 8. Section 4: LinkLens — News vs. Economy Correlation
    st.divider()
    st.header("4. LinkLens — Does News Mood Track the Economy? 🔗")
    st.markdown(
        "**What is this?** LinkLens lines up the tone of economic news (from News Pulse) with changes in the "
        "big economic numbers, year by year, and checks whether they tend to move together. It only compares "
        "periods that genuinely overlap — annual data is never stretched into months."
    )

    with st.spinner("Lining up news tone with indicator history..."):
        linklens_results = compute_linklens_bundle(articles_df, economic_data)

    lens_tabs = st.tabs([
        f"{INDICATOR_ICONS.get(key, '📉')} {INDICATOR_METADATA[key].get('name', key)} Link"
        for key in indicator_keys
    ])

    for tab, key in zip(lens_tabs, indicator_keys):
        lens = linklens_results.get(key, {})
        with tab:
            st.subheader(f"News vs {lens.get('indicator_name', key.title())}")
            if lens.get("has_result"):
                m1, m2, m3 = st.columns(3)
                with m1:
                    r_sent = lens.get("r_sentiment")
                    st.metric(
                        label="Tone link (r)",
                        value=f"{r_sent:+.2f}" if r_sent is not None else "Not measurable",
                        help="Pearson correlation between average yearly news tone and yearly indicator change. -1 = move opposite, +1 = move together, 0 = no link.",
                    )
                with m2:
                    r_vol = lens.get("r_volume")
                    st.metric(
                        label="News volume link (r)",
                        value=f"{r_vol:+.2f}" if r_vol is not None else "Not measurable",
                        help="Pearson correlation between the number of articles per year and yearly indicator change.",
                    )
                with m3:
                    st.metric(
                        label="Overlapping years",
                        value=f"{lens.get('n_overlap', 0)} ({lens.get('overlap_range', 'n/a')})",
                        help="Only genuinely observed periods are compared — no estimated or stretched data points.",
                    )

                st.plotly_chart(
                    build_linklens_chart(lens["overlap"], lens.get("indicator_name", key.title())),
                    use_container_width=True,
                )
                for sentence in lens.get("interpretation", []):
                    st.markdown(f"- {sentence}")
            else:
                st.info(f"ℹ️ {lens.get('reason', 'Not enough overlapping data for this comparison.')}")

            st.caption(f"⚠️ {lens.get('disclaimer', '')}")

    # 9. Section 5: Shock Radar — Unusual Movement Detector
    st.divider()
    st.header("5. Shock Radar — Unusual Movement Detector 🚨")
    st.markdown(
        "**What is this?** Shock Radar scans each indicator's recorded history and flags years where the jump "
        "was unusually sharp compared with that indicator's own typical year-to-year swings (a simple z-score "
        "rule — nothing is hidden). Flagged years also appear as ▲ red triangles on the charts in Section 1."
    )

    radar_cols = st.columns(3)
    for col, key in zip(radar_cols, indicator_keys):
        detection = shock_radar.get(key, {})
        icon = INDICATOR_ICONS.get(key, "📉")
        with col:
            st.subheader(f"{icon} {detection.get('indicator_name', key.title())}")
            if detection.get("has_flags"):
                for flag in detection["flags"]:
                    arrow = "Spike" if flag["direction"] == "spike" else "Drop"
                    st.warning(
                        f"**🚨 {arrow} in {flag['year']}** — recorded {flag['value']:.2f} "
                        f"({flag['change']:+.2f} pts vs prior year, {abs(flag['z_score']):.1f}× the typical swing)\n\n"
                        f"{flag['note']}"
                    )
            else:
                st.success(detection.get("reason", "No unusual movements detected."))

    if len(indicator_keys) > 3:
        radar_cols_2 = st.columns(3)
        for col, key in zip(radar_cols_2, indicator_keys[3:]):
            detection = shock_radar.get(key, {})
            icon = INDICATOR_ICONS.get(key, "📉")
            with col:
                st.subheader(f"{icon} {detection.get('indicator_name', key.title())}")
                if detection.get("has_flags"):
                    for flag in detection["flags"]:
                        arrow = "Spike" if flag["direction"] == "spike" else "Drop"
                        st.warning(
                            f"**🚨 {arrow} in {flag['year']}** — recorded {flag['value']:.2f} "
                            f"({flag['change']:+.2f} pts vs prior year, {abs(flag['z_score']):.1f}× the typical swing)\n\n"
                            f"{flag['note']}"
                        )
                else:
                    st.success(detection.get("reason", "No unusual movements detected."))

    # 10. Section 6: Outlook Engine — Illustrative Trend Outlook
    st.divider()
    st.header("6. Outlook Engine — Where Might Trends Be Heading? 🔮")
    st.markdown(
        "**What is this?** Outlook Engine extends each indicator's long-term straight-line trend (in years) a "
        "few years forward, with a shaded band showing the range implied by past ups and downs."
    )
    st.warning(
        "⚠️ **Illustrative only, not a prediction:** a trend line cannot see future policy decisions or world "
        "events. This is not investment, policy, or financial advice."
    )

    outlook_results = compute_outlook(economic_data)
    outlook_tabs = st.tabs([
        f"{INDICATOR_ICONS.get(key, '📉')} {INDICATOR_METADATA[key].get('name', key)} Outlook"
        for key in indicator_keys
    ])
    for tab, key in zip(outlook_tabs, indicator_keys):
        fc = outlook_results.get(key, {})
        with tab:
            if not fc.get("has_forecast"):
                st.info(f"ℹ️ {fc.get('reason', 'Not enough recorded data to draw an outlook.')}")
            else:
                st.plotly_chart(
                    build_outlook_chart(
                        economic_data[key]["data"],
                        fc,
                        INDICATOR_COLORS.get(key, "#3498db"),
                    ),
                    use_container_width=True,
                )
                st.markdown(fc.get("summary", ""))
                st.caption(
                    f"Trend fit quality (R² = {fc.get('r_squared', 0):.2f}): how closely past yearly values hugged "
                    f"the straight line. 1.0 = perfect line, near 0 = the line explains little."
                )
                st.caption(f"⚠️ {fc.get('disclaimer', '')}")

    # 11. Concise Methodology & Sources (per GEMINI.md Section 5)
    st.divider()
    with st.expander("📚 Methodology, Data Integrity & Analytical Disclaimers", expanded=False):
        st.markdown(
            """
            ### Project Methodology & Governance
            - **Economic Indicators:** Extracted directly from the **World Bank Indicators API** without interpolation or synthetic substitution. Missing reporting years are retained as `NaN` rather than coerced to zero. Six indicators are tracked: inflation, unemployment, real GDP growth, GDP per capita growth, exports of goods & services (% of GDP), and FDI net inflows (% of GDP), for eight economies.
            - **Country Comparison:** Two countries are compared on the *same* indicator, year by year. Only genuinely observed annual values are plotted; missing years appear as gaps, and every latest value carries its own reporting year.
            - **News Extraction & Deduplication:** Aggregated from public RSS economic news feeds, stripped of HTML artifacts, and deduplicated using URL and normalized headline hashes.
            - **NLP Categorization (TF-IDF-weighted):** Articles are matched against transparent topic keyword lists. Topics are ranked by summed TF-IDF weight of matched keywords — rare, distinctive terms outweigh common ones — instead of raw match counts. Each article also lists its top TF-IDF key terms. Fully deterministic and offline.
            - **News Pulse (Sentiment):** Every headline and description is scored with the published VADER lexicon (compound score from -1 to +1, thresholds ±0.05 for positive/negative). Fully offline and deterministic.
            - **LinkLens (Correlation):** News tone is averaged per calendar year and compared against year-over-year indicator changes using Pearson's r, only over genuinely overlapping observed periods (minimum 8 years). Annual data is never upsampled or interpolated into months.
            - **Shock Radar (Anomaly Detection):** Year-over-year changes with |z-score| ≥ 2 versus the indicator's own historical swings are flagged as unusual movements.
            - **Outlook Engine (Forecast):** An ordinary least-squares straight line over recorded annual observations, extended forward with an approximate 95% prediction interval from regression residuals. Illustrative only.
            - **PDF Report:** The export assembles the same template sentences shown on screen — no text is generated or rewritten for the report.
            - **Causality Disclaimer:** This software is designed strictly for academic demonstration and general economic literacy. Correlation between annual macroeconomic indicators and real-time news headlines **does not prove causality**. This platform does not provide financial, investment, or forecasting advice.
            """
        )

    # 12. Footer & Methodology Reference
    st.divider()
    st.caption(
        "Data Sources: World Bank Open Data API. Designed for educational and academic use. "
        "Not intended for financial or investment advice."
    )


if __name__ == "__main__":
    main()
