from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from src.analytics import AnalyticsEngine
from src.config import APP_SUBTITLE, APP_TITLE, DEFAULT_DATA_PATH
from src.data_loader import load_transactions
from src.knowledge_base import KNOWLEDGE_DOCS
from src.query_engine import QueryEngine
from src.retriever import LocalRetriever


st.set_page_config(page_title=APP_TITLE, layout="wide")


@st.cache_data
def load_default_df() -> pd.DataFrame:
    return load_transactions(DEFAULT_DATA_PATH)


@st.cache_data
def load_uploaded_df(uploaded_file) -> pd.DataFrame:
    return load_transactions(uploaded_file)


st.title(APP_TITLE)
st.caption(APP_SUBTITLE)

with st.sidebar:
    st.header("Data")
    uploaded_file = st.file_uploader("Upload transaction CSV", type=["csv"])
    use_sample = st.checkbox("Use built-in sample dataset", value=uploaded_file is None)

    st.markdown("---")
    st.header("Filters")

if uploaded_file is not None:
    df = load_uploaded_df(uploaded_file)
elif use_sample:
    df = load_default_df()
else:
    st.warning("Upload a CSV or choose the sample dataset.")
    st.stop()

analytics = AnalyticsEngine(df)
retriever = LocalRetriever(KNOWLEDGE_DOCS)
query_engine = QueryEngine(analytics, retriever)
metrics = analytics.summary_metrics()

rail_options = ["ALL"] + sorted(df["payment_rail"].dropna().unique().tolist())
status_options = ["ALL"] + sorted(df["status"].dropna().unique().tolist())
risk_options = ["ALL"] + sorted(analytics.df["risk_band"].dropna().unique().tolist())

with st.sidebar:
    selected_rail = st.selectbox("Payment rail", rail_options)
    selected_status = st.selectbox("Status", status_options)
    selected_risk = st.selectbox("Risk band", risk_options)

filtered_df = analytics.filter_transactions(selected_rail, selected_status, selected_risk)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total txns", f"{metrics['total_transactions']:,}")
c2.metric("Failed", f"{metrics['failed_transactions']:,}", f"{metrics['failure_rate']}%")
c3.metric("Fraud labeled", f"{metrics['fraud_flagged']:,}", f"{metrics['fraud_rate']}%")
c4.metric("High risk", f"{metrics['high_risk_transactions']:,}")

st.markdown("## Investigation Console")
user_query = st.text_input(
    "Ask a question",
    placeholder="Why was transaction TXN-10012 flagged?",
)

example_queries = [
    "Why was transaction TXN-10012 flagged?",
    "Show ACH failures",
    "Which payment rail has the highest failure rate?",
    "What are the top risk patterns in the data?",
    "Explain geo mismatch risk",
]

selected_example = st.selectbox("Example prompts", [""] + example_queries)
query_to_run = user_query or selected_example

if query_to_run:
    result = query_engine.answer(query_to_run)
    st.success(result["answer"])

    if result.get("docs"):
        with st.expander("Retrieved context"):
            for doc in result["docs"]:
                st.markdown(f"**{doc['title']}**")
                st.write(doc["content"])

    if "table" in result:
        st.dataframe(result["table"], use_container_width=True)

st.markdown("## Payments & Risk Analytics")
left, right = st.columns(2)

with left:
    rail_df = analytics.failures_by_rail()
    fig_rail = px.bar(
        rail_df,
        x="payment_rail",
        y="failure_rate_pct",
        title="Failure Rate by Payment Rail",
        text="failure_rate_pct",
    )
    st.plotly_chart(fig_rail, use_container_width=True)

with right:
    pattern_df = analytics.risk_patterns()
    fig_pattern = px.bar(
        pattern_df,
        x="pattern",
        y="count",
        title="Observed Risk Patterns",
        text="count",
    )
    st.plotly_chart(fig_pattern, use_container_width=True)

st.markdown("## Filtered Transactions")
show_cols = [
    "transaction_id",
    "timestamp",
    "payment_rail",
    "amount",
    "currency",
    "status",
    "risk_score",
    "risk_band",
    "risk_reasons",
]
st.dataframe(filtered_df[show_cols], use_container_width=True, height=420)

st.markdown("## How to demo this project")
st.markdown(
    """
1. Start with the KPI cards and explain the overall payments health.
2. Show failure-rate differences across ACH, WIRE, CARD, and RTP.
3. Ask why a transaction was flagged and walk through the rule-based explanation.
4. Show top risk patterns to demonstrate analyst-style decision support.
5. Explain how this can evolve into an enterprise RAG + rules + case management platform.
"""
)
