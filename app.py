"""
The Economic Interpreter
========================
A beginner-friendly data science application that helps users understand
the relationship between macroeconomic indicators (inflation, unemployment,
GDP growth) and economic news.

Author: Aryan Rane
License: Academic / Educational
"""

from typing import Dict, Any
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

from modules.economic_data import (
    load_all_economic_data,
    INDICATOR_METADATA,
)

# Supported countries with India as default (per GEMINI.md)
SUPPORTED_COUNTRIES = {
    "IN": "India 🇮🇳",
    "US": "United States 🇺🇸",
    "GB": "United Kingdom 🇬🇧",
    "DE": "Germany 🇩🇪",
    "JP": "Japan 🇯🇵",
}

# Color palette for clear, accessible chart rendering
INDICATOR_COLORS = {
    "inflation": "#e74c3c",     # Warm red / coral
    "unemployment": "#e67e22",  # Amber / orange
    "gdp_growth": "#2ecc71",    # Emerald green
}


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
) -> go.Figure:
    """
    Build a focused line chart for an individual indicator with descriptive annotations.
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
        macroeconomic indicators—**Inflation**, **Unemployment**, and **Real GDP Growth**—with 
        contemporary economic news using basic Natural Language Processing (NLP).
        """
    )

    # 3. Sidebar Controls & Parameters
    with st.sidebar:
        st.header("⚙️ Controls & Parameters")

        selected_country_code = st.selectbox(
            "Select Country",
            options=list(SUPPORTED_COUNTRIES.keys()),
            format_func=lambda code: SUPPORTED_COUNTRIES[code],
            index=0,  # Default: India (per GEMINI.md)
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

        if st.button("🔄 Refresh Data Cache"):
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
    with st.spinner(f"Retrieving World Bank indicators for {SUPPORTED_COUNTRIES[selected_country_code]}..."):
        economic_data = load_all_economic_data(
            country_code=selected_country_code,
            date_range=date_range_query,
        )

    # 5. Section 1: Economic Overview Dashboard
    st.divider()
    st.header(f"1. Economic Overview — {SUPPORTED_COUNTRIES[selected_country_code]}")
    st.markdown(
        "Key macroeconomic health signals retrieved live from the **World Bank Indicators API**."
    )

    # 5.1 Indicator Metric Cards
    col_inf, col_uem, col_gdp = st.columns(3)

    # Inflation Card
    inf_item = economic_data.get("inflation", {})
    inf_summary = inf_item.get("summary", {})
    inf_meta = inf_item.get("metadata", {})
    with col_inf:
        if inf_summary.get("has_data"):
            val = f"{inf_summary['latest_value']:.2f}%"
            chg = inf_summary.get("change")
            prev_yr = inf_summary.get("previous_year")
            # Invert delta color: For inflation, an increase is typically higher cost of living
            delta_label = f"{chg:+.2f}% vs {prev_yr}" if chg is not None else None
            st.metric(
                label=inf_meta["name"],
                value=val,
                delta=delta_label,
                delta_color="inverse",
                help=inf_meta["description"],
            )
            st.caption(f"📅 **Reporting Period:** {inf_summary['latest_year']} | Code: `{inf_meta['code']}`")
        else:
            st.warning("Inflation data unavailable for selected range.")

    # Unemployment Card
    uem_item = economic_data.get("unemployment", {})
    uem_summary = uem_item.get("summary", {})
    uem_meta = uem_item.get("metadata", {})
    with col_uem:
        if uem_summary.get("has_data"):
            val = f"{uem_summary['latest_value']:.2f}%"
            chg = uem_summary.get("change")
            prev_yr = uem_summary.get("previous_year")
            delta_label = f"{chg:+.2f}% vs {prev_yr}" if chg is not None else None
            st.metric(
                label=uem_meta["name"],
                value=val,
                delta=delta_label,
                delta_color="inverse",
                help=uem_meta["description"],
            )
            st.caption(f"📅 **Reporting Period:** {uem_summary['latest_year']} | Code: `{uem_meta['code']}`")
        else:
            st.warning("Unemployment data unavailable for selected range.")

    # Real GDP Growth Card
    gdp_item = economic_data.get("gdp_growth", {})
    gdp_summary = gdp_item.get("summary", {})
    gdp_meta = gdp_item.get("metadata", {})
    with col_gdp:
        if gdp_summary.get("has_data"):
            val = f"{gdp_summary['latest_value']:.2f}%"
            chg = gdp_summary.get("change")
            prev_yr = gdp_summary.get("previous_year")
            delta_label = f"{chg:+.2f}% vs {prev_yr}" if chg is not None else None
            st.metric(
                label=gdp_meta["name"],
                value=val,
                delta=delta_label,
                delta_color="normal",
                help=gdp_meta["description"],
            )
            st.caption(f"📅 **Reporting Period:** {gdp_summary['latest_year']} | Code: `{gdp_meta['code']}`")
        else:
            st.warning("GDP Growth data unavailable for selected range.")

    # 5.2 Interactive Plotly Visualizations
    st.subheader("Historical Indicator Trends")

    tab_combined, tab_inf, tab_uem, tab_gdp, tab_data = st.tabs([
        "📊 Combined Trends",
        "🔥 Inflation",
        "👥 Unemployment",
        "📈 Real GDP Growth",
        "📋 Data Table",
    ])

    with tab_combined:
        combined_fig = build_combined_trend_chart(economic_data)
        st.plotly_chart(combined_fig, use_container_width=True)

    with tab_inf:
        inf_fig = build_single_indicator_chart(
            df=inf_item.get("data", pd.DataFrame()),
            indicator_name=inf_meta.get("name", "Inflation"),
            unit=inf_meta.get("unit", "%"),
            color=INDICATOR_COLORS["inflation"],
        )
        st.plotly_chart(inf_fig, use_container_width=True)
        st.info(f"**About this indicator:** {inf_meta.get('description')}")

    with tab_uem:
        uem_fig = build_single_indicator_chart(
            df=uem_item.get("data", pd.DataFrame()),
            indicator_name=uem_meta.get("name", "Unemployment Rate"),
            unit=uem_meta.get("unit", "%"),
            color=INDICATOR_COLORS["unemployment"],
        )
        st.plotly_chart(uem_fig, use_container_width=True)
        st.info(f"**About this indicator:** {uem_meta.get('description')}")

    with tab_gdp:
        gdp_fig = build_single_indicator_chart(
            df=gdp_item.get("data", pd.DataFrame()),
            indicator_name=gdp_meta.get("name", "Real GDP Growth"),
            unit=gdp_meta.get("unit", "%"),
            color=INDICATOR_COLORS["gdp_growth"],
        )
        st.plotly_chart(gdp_fig, use_container_width=True)
        st.info(f"**About this indicator:** {gdp_meta.get('description')}")

    with tab_data:
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
                merged_table.style.format({col: "{:.2f}%" for col in merged_table.columns if col != "year"}),
                use_container_width=True,
            )
        else:
            st.write("No tabular observations to display.")

    # 6. Section 2: Economic News Placeholder
    st.divider()
    st.header("2. Economic News & Categorization")
    st.info(
        "📰 **Phase 4 & 5 Target:** Economic news feed with lightweight NLP topic categorization "
        "(Inflation, Employment, GDP, Monetary Policy) will appear here."
    )

    # 7. Section 3: Interpretation & Analysis Placeholder
    st.divider()
    st.header("3. Economic Interpretation & Synthesis")
    st.info(
        "🧠 **Phase 6 Target:** Objective, evidence-based synthesis connecting observed indicator changes "
        "with news topics, complete with stated analytical limitations."
    )

    # 8. Footer & Methodology Reference
    st.divider()
    st.caption(
        "Data Sources: World Bank Open Data API. Designed for educational and academic use. "
        "Not intended for financial or investment advice."
    )


if __name__ == "__main__":
    main()
