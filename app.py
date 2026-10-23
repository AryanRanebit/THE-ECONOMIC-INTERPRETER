"""
The Economic Interpreter
========================
A beginner-friendly data science application that helps users understand
the relationship between macroeconomic indicators (inflation, unemployment,
GDP growth) and economic news.

Author: Aryan Rane
License: Academic / Educational
"""

import streamlit as st


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
        Welcome to **The Economic Interpreter**. This educational platform connects 
        macroeconomic indicators—**Inflation**, **Unemployment**, and **Real GDP Growth**—with 
        contemporary economic news using basic Natural Language Processing (NLP).
        """
    )

    # 3. Sidebar Configuration (Parameters & Metadata)
    with st.sidebar:
        st.header("⚙️ Controls & Parameters")
        st.markdown(
            """
            **Default Country:** India 🇮🇳  
            **Data Source:** World Bank API  
            **Current Phase:** Phase 1 (Baseline Setup)
            """
        )
        st.divider()
        st.info(
            "💡 **Tip for Learners:** Economic indicators reflect past observations. "
            "News articles discuss current developments. Correlation does not imply causation!"
        )

    # 4. Dashboard Sections Outline
    st.divider()

    # Section 1: Economic Overview
    st.header("1. Economic Overview")
    st.info(
        "📊 **Phase 2 Target:** Live indicator cards and interactive Plotly trend "
        "charts for Inflation, Unemployment, and GDP growth will appear here."
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Inflation (Consumer Prices)", value="Fetching...", help="World Bank code: FP.CPI.TOTL.ZG")
    with col2:
        st.metric(label="Unemployment Rate", value="Fetching...", help="World Bank code: SL.UEM.TOTL.ZS")
    with col3:
        st.metric(label="Real GDP Growth", value="Fetching...", help="World Bank code: NY.GDP.MKTP.KD.ZG")

    st.divider()

    # Section 2: Economic News
    st.header("2. Economic News & Categorization")
    st.info(
        "📰 **Phase 4 & 5 Target:** Economic news feed with lightweight NLP topic categorization "
        "(Inflation, Employment, GDP, Monetary Policy) will appear here."
    )

    st.divider()

    # Section 3: Interpretation & Analysis
    st.header("3. Economic Interpretation & Synthesis")
    st.info(
        "🧠 **Phase 6 Target:** Objective, evidence-based synthesis connecting observed indicator changes "
        "with news topics, complete with stated analytical limitations."
    )

    # 5. Footer & Methodology Reference
    st.divider()
    st.caption(
        "Data Sources: World Bank Open Data API. Designed for educational and academic use. "
        "Not intended for financial or investment advice."
    )


if __name__ == "__main__":
    main()
