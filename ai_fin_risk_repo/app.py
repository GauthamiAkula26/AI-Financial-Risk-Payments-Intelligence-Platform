from __future__ import annotations

import re
from typing import Any

import pandas as pd
import plotly.express as px
import streamlit as st

from src.analytics import AnalyticsEngine
from src.config import APP_SUBTITLE, APP_TITLE, DEFAULT_DATA_PATH, HIGH_RISK_THRESHOLD
from src.data_loader import load_transactions
from src.knowledge_base import KNOWLEDGE_DOCS
from src.query_engine import QueryEngine
from src.retriever import LocalRetriever

st.set_page_config(page_title=APP_TITLE, layout="wide")


# -----------------------------
# Helpers
# -----------------------------
REQUIRED_MIN_COLUMNS = ["transaction_id", "amount", "payment_type", "risk_score"]


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    rename_map = {}
    for col in df.columns:
        c = col.strip().lower()
        if c in {"txn_id", "txnid", "txnid", "id"}:
            rename_map[col] = "transaction_id"
        elif c in {"paymentrail", "rail", "payment_rail"}:
            rename_map[col] = "payment_type"
        elif c in {"fraud", "is_fraud", "fraudlabel", "fraud_label"}:
            rename_map[col] = "fraud_flag"
    return df.rename(columns=rename_map)


def validate_columns(df: pd.DataFrame) -> list[str]:
    missing = [c for c in REQUIRED_MIN_COLUMNS if c not in df.columns]
    return missing


@st.cache_data
def load_default_df() -> pd.DataFrame:
    df = load_transactions(DEFAULT_DATA_PATH)
    return normalize_columns(df)


@st.cache_data
def load_uploaded_df(file) -> pd.DataFrame:
    df = pd.read_csv(file)
    return normalize_columns(df)


@st.cache_resource
def build_retriever():
    return LocalRetriever(KNOWLEDGE_DOCS)


@st.cache_resource
def build_query_engine():
    retriever = build_retriever()
    return QueryEngine(retriever=retriever)


def safe_col(df: pd.DataFrame, col: str, default: Any = None):
    return df[col] if col in df.columns else default


def has_col(df: pd.DataFrame, col: str) -> bool:
    return col in df.columns


def coerce_numeric(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    out = df.copy()
    for c in cols:
        if c in out.columns:
            out[c] = pd.to_numeric(out[c], errors="coerce")
    return out


def ensure_datetime(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for c in ["transaction_date", "date", "created_at", "timestamp"]:
        if c in out.columns:
            out[c] = pd.to_datetime(out[c], errors="coerce")
            if c != "transaction_date":
                out["transaction_date"] = out[c]
            break
    return out


def get_risk_signals(row: pd.Series) -> list[str]:
    signals = []

    risk_score = float(row.get("risk_score", 0) or 0)
    amount = float(row.get("amount", 0) or 0)
    status = str(row.get("status", "")).lower()
    payment_type = str(row.get("payment_type", "")).lower()
    device = str(row.get("device", "")).lower()
    geo = str(row.get("geo", row.get("geography", ""))).lower()
    failed_count = float(row.get("failed_attempts", 0) or 0)

    if risk_score >= HIGH_RISK_THRESHOLD:
        signals.append("High risk score")
    if amount >= 10000:
        signals.append("High amount")
    if status == "flagged":
        signals.append("Flagged status")
    if payment_type == "wire":
        signals.append("Wire transfer risk")
    if "new" in device:
        signals.append("New device")
    if "mismatch" in geo:
        signals.append("Geo mismatch")
    if failed_count >= 2:
        signals.append("Repeated failed attempts")

    return signals or ["Standard monitoring"]


def get_recommended_action(row: pd.Series) -> str:
    risk = float(row.get("risk_score", 0) or 0)
    amount = float(row.get("amount", 0) or 0)
    payment_type = str(row.get("payment_type", "")).lower()

    if risk >= 90:
        return "Escalate immediately and hold transaction"
    if risk >= 80:
        return "Send for manual review"
    if risk >= HIGH_RISK_THRESHOLD:
        return "Review supporting signals"
    if payment_type == "wire" and amount >= 10000:
        return "Validate beneficiary and approval chain"
    if amount >= 10000:
        return "Validate transaction details"
    return "Monitor"


def get_priority(risk_score: float) -> str:
    if risk_score >= 90:
        return "Critical"
    if risk_score >= 80:
        return "High"
    if risk_score >= HIGH_RISK_THRESHOLD:
        return "Medium"
    return "Low"


def filter_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    filtered = df.copy()

    st.sidebar.markdown("## Risk Filters")

    if has_col(filtered, "payment_type"):
        payment_options = sorted(filtered["payment_type"].dropna().astype(str).unique().tolist())
        selected_payment_types = st.sidebar.multiselect("Payment Type", payment_options)
        if selected_payment_types:
            filtered = filtered[filtered["payment_type"].astype(str).isin(selected_payment_types)]

    if has_col(filtered, "status"):
        status_options = sorted(filtered["status"].dropna().astype(str).unique().tolist())
        selected_status = st.sidebar.multiselect("Status", status_options)
        if selected_status:
            filtered = filtered[filtered["status"].astype(str).isin(selected_status)]

    if has_col(filtered, "risk_score"):
        min_risk = int(filtered["risk_score"].fillna(0).min())
        max_risk = int(filtered["risk_score"].fillna(100).max())
        risk_range = st.sidebar.slider("Risk Score", min_risk, max_risk, (min_risk, max_risk))
        filtered = filtered[
            filtered["risk_score"].fillna(0).between(risk_range[0], risk_range[1], inclusive="both")
        ]

    if has_col(filtered, "amount"):
        min_amt = float(filtered["amount"].fillna(0).min())
        max_amt = float(filtered["amount"].fillna(0).max())
        amount_range = st.sidebar.slider(
            "Amount Range",
            min_value=float(min_amt),
            max_value=float(max_amt if max_amt > min_amt else min_amt + 1),
            value=(float(min_amt), float(max_amt if max_amt > min_amt else min_amt + 1)),
        )
        filtered = filtered[
            filtered["amount"].fillna(0).between(amount_range[0], amount_range[1], inclusive="both")
        ]

    if has_col(filtered, "fraud_flag"):
        fraud_only = st.sidebar.checkbox("Fraud Only")
        if fraud_only:
            filtered = filtered[filtered["fraud_flag"].astype(str).isin(["1", "True", "true", "Y", "Yes"]) | (filtered["fraud_flag"] == 1)]

    return filtered


def find_transaction(df: pd.DataFrame, transaction_id: str) -> pd.DataFrame:
    if not transaction_id or "transaction_id" not in df.columns:
        return pd.DataFrame()
    return df[df["transaction_id"].astype(str).str.lower() == transaction_id.strip().lower()]


def derive_investigation_results(question: str, df: pd.DataFrame) -> tuple[str, pd.DataFrame]:
    q = (question or "").strip().lower()
    if not q:
        return "Enter a question to investigate.", pd.DataFrame()

    result_df = df.copy()

    tx_match = re.search(r"(txn[-\s]?\d+)", q, re.IGNORECASE)
    if tx_match and "transaction_id" in result_df.columns:
        txid = tx_match.group(1).replace(" ", "").upper()
        result_df = result_df[result_df["transaction_id"].astype(str).str.upper() == txid]
        if len(result_df) > 0:
            row = result_df.iloc[0]
            signals = ", ".join(get_risk_signals(row))
            action = get_recommended_action(row)
            summary = (
                f"Transaction {txid} appears in the dataset with risk score "
                f"{row.get('risk_score', 'N/A')}. Signals: {signals}. "
                f"Recommended action: {action}."
            )
            return summary, result_df

    if "high-risk ach" in q or ("high" in q and "ach" in q):
        if "payment_type" in result_df.columns:
            result_df = result_df[result_df["payment_type"].astype(str).str.lower() == "ach"]
        if "risk_score" in result_df.columns:
            result_df = result_df[result_df["risk_score"] >= HIGH_RISK_THRESHOLD]
        return f"Found {len(result_df)} high-risk ACH transactions.", result_df.head(50)

    if "manual review" in q:
        if "risk_score" in result_df.columns:
            result_df = result_df[result_df["risk_score"] >= HIGH_RISK_THRESHOLD]
        return f"Found {len(result_df)} transactions that may need manual review.", result_df.head(50)

    if "highest fraud rate" in q or "most fraud" in q:
        if "payment_type" in result_df.columns and "fraud_flag" in result_df.columns:
            grouped = (
                result_df.groupby("payment_type", dropna=False)["fraud_flag"]
                .mean()
                .reset_index()
                .sort_values("fraud_flag", ascending=False)
            )
            if len(grouped) > 0:
                top = grouped.iloc[0]
                return (
                    f"{top['payment_type']} has the highest fraud rate in the current dataset "
                    f"at {top['fraud_flag']:.2%}.",
                    grouped,
                )

    if "suspicious pattern" in q or "summarize" in q:
        high_risk_count = int((result_df["risk_score"] >= HIGH_RISK_THRESHOLD).sum()) if "risk_score" in result_df.columns else 0
        flagged_count = int((result_df["status"].astype(str).str.lower() == "flagged").sum()) if "status" in result_df.columns else 0
        top_payment = None
        if "payment_type" in result_df.columns:
            top_payment = result_df["payment_type"].astype(str).value_counts().idxmax()
        summary = (
            f"Dataset summary: {len(result_df)} transactions reviewed, "
            f"{high_risk_count} high-risk transactions, "
            f"{flagged_count} flagged items"
        )
        if top_payment:
            summary += f", with {top_payment} as the most common payment type."
        summary += " Review high-risk and flagged items first."
        return summary, result_df.head(25)

    if "high-risk" in q or "high risk" in q:
        if "risk_score" in result_df.columns:
            result_df = result_df[result_df["risk_score"] >= HIGH_RISK_THRESHOLD]
        return f"Found {len(result_df)} high-risk transactions.", result_df.head(50)

    if "flagged" in q:
        if "status" in result_df.columns:
            result_df = result_df[result_df["status"].astype(str).str.lower() == "flagged"]
        return f"Found {len(result_df)} flagged transactions.", result_df.head(50)

    return "No specific rule matched the question. Showing a sample of current filtered transactions.", result_df.head(25)


def render_transaction_detail(row: pd.Series):
    st.markdown("### Transaction Detail")
    c1, c2, c3 = st.columns(3)
    c1.metric("Transaction ID", str(row.get("transaction_id", "N/A")))
    c2.metric("Amount", f"${float(row.get('amount', 0) or 0):,.2f}")
    c3.metric("Risk Score", f"{float(row.get('risk_score', 0) or 0):.0f}")

    c4, c5, c6 = st.columns(3)
    c4.write(f"**Payment Type:** {row.get('payment_type', 'N/A')}")
    c5.write(f"**Status:** {row.get('status', 'N/A')}")
    c6.write(f"**Priority:** {get_priority(float(row.get('risk_score', 0) or 0))}")

    st.write("**Signals Triggered:**")
    for signal in get_risk_signals(row):
        st.write(f"- {signal}")

    st.write(f"**Recommended Action:** {get_recommended_action(row)}")


# -----------------------------
# Sidebar
# -----------------------------
st.sidebar.markdown("# Dataset")
uploaded_file = st.sidebar.file_uploader("Upload transaction CSV", type=["csv"])
use_sample_data = st.sidebar.checkbox("Use built-in sample dataset", value=True)

# -----------------------------
# Load data
# -----------------------------
try:
    if uploaded_file is not None:
        df = load_uploaded_df(uploaded_file)
        dataset_label = f"Uploaded file: {uploaded_file.name}"
    elif use_sample_data:
        df = load_default_df()
        dataset_label = "Built-in sample dataset"
    else:
        st.warning("Upload a CSV or enable the sample dataset.")
        st.stop()

    df = coerce_numeric(df, ["amount", "risk_score", "fraud_flag", "failed_attempts"])
    df = ensure_datetime(df)

    missing_columns = validate_columns(df)
    if missing_columns:
        st.error(f"Missing required columns: {', '.join(missing_columns)}")
        st.stop()

except Exception as e:
    st.error(f"Unable to load dataset: {e}")
    st.stop()

filtered_df = filter_dataframe(df)

# engines
analytics_engine = AnalyticsEngine(filtered_df)
query_engine = build_query_engine()

# -----------------------------
# Header
# -----------------------------
st.title(APP_TITLE)
st.caption(APP_SUBTITLE)
st.write(f"**Loaded dataset:** {dataset_label}")

tab1, tab2, tab3, tab4 = st.tabs(
    ["📊 Overview", "🔎 Transaction Explorer", "🧠 Investigation Assistant", "📋 Manual Review Queue"]
)

# -----------------------------
# Tab 1 - Overview
# -----------------------------
with tab1:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Transactions", f"{len(filtered_df):,}")
    c2.metric(
        "High Risk",
        f"{len(filtered_df[filtered_df['risk_score'] >= HIGH_RISK_THRESHOLD]):,}",
    )
    fraud_total = int(filtered_df["fraud_flag"].fillna(0).sum()) if "fraud_flag" in filtered_df.columns else 0
    c3.metric("Fraud Cases", f"{fraud_total:,}")
    avg_amt = filtered_df["amount"].mean() if "amount" in filtered_df.columns else 0
    c4.metric("Avg Amount", f"${avg_amt:,.2f}")

    left, right = st.columns(2)

    with left:
        if "payment_type" in filtered_df.columns and "fraud_flag" in filtered_df.columns:
            fraud_by_type = (
                filtered_df.groupby("payment_type", dropna=False)["fraud_flag"]
                .sum()
                .reset_index()
                .sort_values("fraud_flag", ascending=False)
            )
            fig = px.bar(
                fraud_by_type,
                x="payment_type",
                y="fraud_flag",
                title="Fraud Cases by Payment Type",
            )
            st.plotly_chart(fig, use_container_width=True)

        if "risk_score" in filtered_df.columns:
            fig = px.histogram(
                filtered_df,
                x="risk_score",
                nbins=20,
                title="Risk Score Distribution",
            )
            st.plotly_chart(fig, use_container_width=True)

    with right:
        if "amount" in filtered_df.columns and "risk_score" in filtered_df.columns:
            fig = px.scatter(
                filtered_df,
                x="amount",
                y="risk_score",
                color="payment_type" if "payment_type" in filtered_df.columns else None,
                title="Amount vs Risk Score",
                hover_data=["transaction_id"] if "transaction_id" in filtered_df.columns else None,
            )
            st.plotly_chart(fig, use_container_width=True)

        if "status" in filtered_df.columns:
            status_counts = (
                filtered_df.groupby("status", dropna=False)
                .size()
                .reset_index(name="count")
                .sort_values("count", ascending=False)
            )
            fig = px.bar(status_counts, x="status", y="count", title="Transactions by Status")
            st.plotly_chart(fig, use_container_width=True)

    with st.expander("Data Dictionary"):
        st.write("- **transaction_id**: unique transaction identifier")
        st.write("- **amount**: transaction amount")
        st.write("- **payment_type**: ACH, Wire, Card, RTP, etc.")
        st.write("- **risk_score**: numeric score indicating risk level")
        st.write("- **status**: processing or investigation status")
        st.write("- **fraud_flag**: fraud indicator if available")

# -----------------------------
# Tab 2 - Explorer
# -----------------------------
with tab2:
    st.markdown("### Transaction Explorer")

    search_txn = st.text_input("Search by Transaction ID")
    explorer_df = filtered_df.copy()

    if search_txn:
        explorer_df = find_transaction(explorer_df, search_txn)

    st.dataframe(explorer_df, use_container_width=True, height=420)

    if len(explorer_df) > 0:
        selected_index = st.number_input(
            "Select row number to inspect",
            min_value=0,
            max_value=max(len(explorer_df) - 1, 0),
            value=0,
            step=1,
        )
        selected_row = explorer_df.reset_index(drop=True).iloc[int(selected_index)]
        render_transaction_detail(selected_row)
    else:
        st.info("No records match the current filters.")

# -----------------------------
# Tab 3 - Investigation Assistant
# -----------------------------
with tab3:
    st.markdown("### Investigation Assistant")
    st.caption("Ask analyst-style questions about flagged transactions, risk patterns, and review priorities.")

    st.markdown("**Example prompts**")
    p1, p2, p3, p4, p5 = st.columns(5)
    btn1 = p1.button("Why was TXN-10012 flagged?")
    btn2 = p2.button("Show high-risk ACH transactions")
    btn3 = p3.button("Which payment type has highest fraud rate?")
    btn4 = p4.button("Show transactions needing manual review")
    btn5 = p5.button("Summarize suspicious patterns")

    default_prompt = ""
    if btn1:
        default_prompt = "Why was transaction TXN-10012 flagged?"
    elif btn2:
        default_prompt = "Show high-risk ACH transactions"
    elif btn3:
        default_prompt = "Which payment type has highest fraud rate?"
    elif btn4:
        default_prompt = "Show transactions needing manual review"
    elif btn5:
        default_prompt = "Summarize suspicious patterns in this dataset"

    question = st.text_input("Ask a question", value=default_prompt, placeholder="Type your investigation question here")

    if st.button("Run Investigation", type="primary") or question:
        summary, result_df = derive_investigation_results(question, filtered_df)

        st.markdown("#### Findings")
        st.info(summary)

        try:
            kb_response = query_engine.answer(question)
            if kb_response:
                st.markdown("#### Knowledge Context")
                st.write(kb_response)
        except Exception:
            pass

        if len(result_df) > 0:
            st.markdown("#### Matching Records")
            st.dataframe(result_df, use_container_width=True, height=320)

            if "transaction_id" in result_df.columns and "risk_score" in result_df.columns:
                top_row = result_df.reset_index(drop=True).iloc[0]
                st.markdown("#### Recommended Action")
                st.success(get_recommended_action(top_row))

                st.markdown("#### Signals Triggered")
                for signal in get_risk_signals(top_row):
                    st.write(f"- {signal}")
        else:
            st.warning("No matching records found for that question.")

# -----------------------------
# Tab 4 - Manual Review Queue
# -----------------------------
with tab4:
    st.markdown("### Manual Review Queue")

    review_df = filtered_df.copy()
    if "status" in review_df.columns:
        flagged_mask = review_df["status"].astype(str).str.lower() == "flagged"
    else:
        flagged_mask = pd.Series([False] * len(review_df), index=review_df.index)

    review_df = review_df[(review_df["risk_score"] >= HIGH_RISK_THRESHOLD) | flagged_mask].copy()

    if len(review_df) > 0:
        review_df["priority"] = review_df["risk_score"].fillna(0).apply(get_priority)
        review_df["recommended_action"] = review_df.apply(get_recommended_action, axis=1)
        review_df["signals"] = review_df.apply(lambda r: ", ".join(get_risk_signals(r)), axis=1)

        display_cols = [
            c for c in [
                "transaction_id",
                "payment_type",
                "amount",
                "risk_score",
                "status",
                "priority",
                "recommended_action",
                "signals",
            ]
            if c in review_df.columns
        ]
        st.dataframe(
            review_df[display_cols].sort_values(["risk_score"], ascending=False),
            use_container_width=True,
            height=420,
        )
    else:
        st.info("No transactions currently meet the manual review threshold.")
