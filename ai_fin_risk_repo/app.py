from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from src.config import (
    APP_SUBTITLE,
    APP_TITLE,
    DEFAULT_DATA_PATH,
    HIGH_RISK_THRESHOLD,
    ROLE_OPTIONS,
    PAGE_OPTIONS,
    REQUIRED_COLUMNS,
)
from src.knowledge_base import KNOWLEDGE_DOCS
from src.query_engine import QueryEngine
from src.retriever import LocalRetriever

st.set_page_config(page_title=APP_TITLE, layout="wide")


def apply_custom_css() -> None:
    st.markdown(
        """
        <style>
        .main {background-color: #f6f8fb;}
        .block-container {padding-top: 1.2rem; padding-bottom: 1rem;}
        .rl-card {
            background: white;
            padding: 16px 18px;
            border-radius: 18px;
            border: 1px solid #e9eef5;
            box-shadow: 0 1px 2px rgba(16,24,40,.04);
            margin-bottom: 12px;
        }
        .rl-title {
            font-size: 2.4rem;
            font-weight: 800;
            color: #182230;
            margin-bottom: 0.2rem;
        }
        .rl-subtitle {
            color: #667085;
            margin-bottom: 1rem;
        }
        .rl-kpi-label {
            color: #667085;
            font-size: 0.9rem;
            margin-bottom: 4px;
        }
        .rl-kpi-value {
            font-size: 1.7rem;
            font-weight: 700;
            color: #101828;
        }
        .rl-kpi-delta {
            color: #475467;
            font-size: 0.85rem;
            margin-top: 4px;
        }
        .rl-section {
            font-size: 1.15rem;
            font-weight: 700;
            color: #182230;
            margin: 0.2rem 0 0.8rem 0;
        }
        .rl-badge {
            display: inline-block;
            padding: 0.25rem 0.55rem;
            border-radius: 999px;
            font-size: 0.8rem;
            font-weight: 600;
            margin-right: 6px;
            margin-bottom: 6px;
        }
        .rl-badge-red {background:#fee4e2;color:#b42318;}
        .rl-badge-amber {background:#fef0c7;color:#b54708;}
        .rl-badge-green {background:#dcfae6;color:#067647;}
        .rl-badge-blue {background:#d1e9ff;color:#175cd3;}
        .rl-small {
            color:#667085;
            font-size:0.9rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def load_transactions(path: str | None = None, uploaded_file=None) -> pd.DataFrame:
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_csv(path or DEFAULT_DATA_PATH)
    return normalize_columns(df)


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    rename_map = {}
    for col in df.columns:
        c = col.strip().lower()
        if c in {"txn_id", "id"}:
            rename_map[col] = "transaction_id"
        elif c in {"paymentrail", "rail"}:
            rename_map[col] = "payment_rail"
        elif c in {"fraud", "fraud_flag"}:
            rename_map[col] = "is_fraud_label"
    df = df.rename(columns=rename_map)
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].astype(str).str.strip()
    return df


def validate_dataframe(df: pd.DataFrame) -> list[str]:
    return [c for c in REQUIRED_COLUMNS if c not in df.columns]


def coerce_types(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    numeric_cols = [
        "amount",
        "risk_score",
        "is_fraud_label",
        "geo_mismatch_flag",
        "velocity_flag",
        "beneficiary_change_flag",
        "customer_txn_count_24h",
        "historical_customer_avg_amount",
    ]
    for c in numeric_cols:
        if c in out.columns:
            out[c] = pd.to_numeric(out[c], errors="coerce").fillna(0)

    if "timestamp" in out.columns:
        out["timestamp"] = pd.to_datetime(out["timestamp"], errors="coerce")

    return out


@st.cache_resource
def build_query_engine() -> QueryEngine:
    retriever = LocalRetriever(KNOWLEDGE_DOCS)
    return QueryEngine(retriever=retriever)


def render_header(role: str) -> None:
    st.markdown(f"<div class='rl-title'>{APP_TITLE}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='rl-subtitle'>{APP_SUBTITLE}</div>", unsafe_allow_html=True)
    st.markdown(
        f"<div class='rl-small'><b>Current role view:</b> {role}</div>",
        unsafe_allow_html=True,
    )


def render_kpi_card(label: str, value: str, delta: str = "") -> None:
    st.markdown(
        f"""
        <div class="rl-card">
            <div class="rl-kpi-label">{label}</div>
            <div class="rl-kpi-value">{value}</div>
            <div class="rl-kpi-delta">{delta}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def add_filter_sidebar(df: pd.DataFrame) -> pd.DataFrame:
    st.sidebar.markdown("## Filters")
    filtered = df.copy()

    if "payment_rail" in filtered.columns:
        rails = sorted(filtered["payment_rail"].dropna().unique().tolist())
        selected_rails = st.sidebar.multiselect("Payment Rail", rails)
        if selected_rails:
            filtered = filtered[filtered["payment_rail"].isin(selected_rails)]

    if "channel" in filtered.columns:
        channels = sorted(filtered["channel"].dropna().unique().tolist())
        selected_channels = st.sidebar.multiselect("Channel", channels)
        if selected_channels:
            filtered = filtered[filtered["channel"].isin(selected_channels)]

    if "status" in filtered.columns:
        statuses = sorted(filtered["status"].dropna().unique().tolist())
        selected_statuses = st.sidebar.multiselect("Status", statuses)
        if selected_statuses:
            filtered = filtered[filtered["status"].isin(selected_statuses)]

    if "risk_score" in filtered.columns:
        min_risk = int(filtered["risk_score"].min())
        max_risk = int(filtered["risk_score"].max())
        risk_range = st.sidebar.slider("Risk Score", min_risk, max_risk, (min_risk, max_risk))
        filtered = filtered[
            filtered["risk_score"].between(risk_range[0], risk_range[1], inclusive="both")
        ]

    if "amount" in filtered.columns:
        min_amt = float(filtered["amount"].min())
        max_amt = float(filtered["amount"].max())
        amt_range = st.sidebar.slider(
            "Amount Range",
            min_value=float(min_amt),
            max_value=float(max_amt),
            value=(float(min_amt), float(max_amt)),
        )
        filtered = filtered[
            filtered["amount"].between(amt_range[0], amt_range[1], inclusive="both")
        ]

    fraud_only = st.sidebar.checkbox("Fraud Only")
    if fraud_only and "is_fraud_label" in filtered.columns:
        filtered = filtered[filtered["is_fraud_label"] == 1]

    return filtered


def get_priority(score: float) -> str:
    if score >= 90:
        return "Critical"
    if score >= 80:
        return "High"
    if score >= HIGH_RISK_THRESHOLD:
        return "Medium"
    return "Low"


def get_risk_signals(row: pd.Series) -> list[str]:
    signals: list[str] = []
    if row.get("risk_score", 0) >= HIGH_RISK_THRESHOLD:
        signals.append("High risk score")
    if row.get("amount", 0) >= 10000:
        signals.append("Large amount")
    if row.get("geo_mismatch_flag", 0) == 1:
        signals.append("Geo mismatch")
    if row.get("velocity_flag", 0) == 1:
        signals.append("Velocity spike")
    if row.get("beneficiary_change_flag", 0) == 1:
        signals.append("Beneficiary changed")
    if str(row.get("status", "")).lower() == "flagged":
        signals.append("Flagged status")
    if str(row.get("payment_rail", "")).lower() == "wire":
        signals.append("Wire rail sensitivity")
    return signals or ["Standard monitoring"]


def get_recommended_action(row: pd.Series) -> str:
    score = float(row.get("risk_score", 0))
    amount = float(row.get("amount", 0))
    if score >= 90:
        return "Block or escalate immediately"
    if score >= 80:
        return "Send for manual review"
    if score >= HIGH_RISK_THRESHOLD:
        return "Review customer and payment context"
    if amount >= 10000:
        return "Validate payment details"
    return "Approve with monitoring"


def render_priority_badge(priority: str) -> None:
    if priority == "Critical":
        cls = "rl-badge rl-badge-red"
    elif priority == "High":
        cls = "rl-badge rl-badge-amber"
    elif priority == "Medium":
        cls = "rl-badge rl-badge-blue"
    else:
        cls = "rl-badge rl-badge-green"
    st.markdown(f"<span class='{cls}'>{priority}</span>", unsafe_allow_html=True)


def generate_case_notes(result_df: pd.DataFrame) -> str:
    if result_df.empty:
        return "No records available for case note generation."

    top_rail = result_df["payment_rail"].mode().iloc[0] if "payment_rail" in result_df.columns else "N/A"
    high_risk = int((result_df["risk_score"] >= HIGH_RISK_THRESHOLD).sum())
    fraud_count = int(result_df["is_fraud_label"].sum()) if "is_fraud_label" in result_df.columns else 0
    avg_amount = float(result_df["amount"].mean()) if "amount" in result_df.columns else 0.0

    return f"""Case Summary
Transactions analyzed: {len(result_df)}
High-risk transactions: {high_risk}
Fraud-labelled transactions: {fraud_count}
Average amount: ${avg_amount:,.2f}
Dominant payment rail: {top_rail}

Assessment
The reviewed set shows elevated payment risk indicators across rail behavior, risk score distribution, and transaction context. Highest attention should be placed on large-value and flagged items.

Recommended Actions
- Prioritize critical and high-risk transactions
- Validate customer, beneficiary, and channel context
- Escalate flagged wire transactions
- Capture analyst notes for audit trail
"""


def derive_investigation_results(question: str, df: pd.DataFrame) -> tuple[str, pd.DataFrame]:
    q = (question or "").strip().lower()
    if not q:
        return "Enter a question to investigate.", pd.DataFrame()

    result_df = df.copy()

    if "txn-" in q and "transaction_id" in result_df.columns:
        words = q.replace("?", "").split()
        txn_ids = [w.upper() for w in words if w.upper().startswith("TXN-")]
        if txn_ids:
            txid = txn_ids[0]
            result_df = result_df[result_df["transaction_id"].str.upper() == txid]
            if not result_df.empty:
                row = result_df.iloc[0]
                return (
                    f"{txid} is scored at {int(row['risk_score'])}. Signals: {', '.join(get_risk_signals(row))}. "
                    f"Recommended action: {get_recommended_action(row)}.",
                    result_df,
                )

    if "high-risk ach" in q or "high risk ach" in q:
        result_df = result_df[
            (result_df["payment_rail"].str.lower() == "ach")
            & (result_df["risk_score"] >= HIGH_RISK_THRESHOLD)
        ]
        return f"Found {len(result_df)} high-risk ACH transactions.", result_df

    if "highest fraud rate" in q or "most fraud" in q:
        grouped = (
            result_df.groupby("payment_rail", dropna=False)["is_fraud_label"]
            .mean()
            .reset_index()
            .sort_values("is_fraud_label", ascending=False)
        )
        if not grouped.empty:
            top = grouped.iloc[0]
            return (
                f"{top['payment_rail']} has the highest fraud rate at {top['is_fraud_label']:.2%}.",
                grouped,
            )

    if "manual review" in q:
        result_df = result_df[result_df["risk_score"] >= HIGH_RISK_THRESHOLD]
        return f"Found {len(result_df)} transactions requiring review.", result_df

    if "summarize" in q or "pattern" in q:
        flagged = int((result_df["status"].str.lower() == "flagged").sum())
        high_risk = int((result_df["risk_score"] >= HIGH_RISK_THRESHOLD).sum())
        top_rail = result_df["payment_rail"].mode().iloc[0]
        return (
            f"Summary: {len(result_df)} transactions, {high_risk} high-risk, {flagged} flagged. "
            f"Most active rail: {top_rail}.",
            result_df.head(25),
        )

    return "No exact pattern matched. Showing a sample of filtered transactions.", result_df.head(25)


def render_transaction_detail(row: pd.Series) -> None:
    st.markdown("### Selected Transaction")
    c1, c2, c3 = st.columns(3)
    c1.metric("Transaction ID", row["transaction_id"])
    c2.metric("Amount", f"${row['amount']:,.2f}")
    c3.metric("Risk Score", int(row["risk_score"]))

    priority = get_priority(float(row["risk_score"]))
    render_priority_badge(priority)

    a, b, c = st.columns(3)
    a.write(f"**Customer ID:** {row.get('customer_id', 'N/A')}")
    b.write(f"**Rail:** {row.get('payment_rail', 'N/A')}")
    c.write(f"**Channel:** {row.get('channel', 'N/A')}")

    d, e, f = st.columns(3)
    d.write(f"**Currency:** {row.get('currency', 'N/A')}")
    e.write(f"**Status:** {row.get('status', 'N/A')}")
    f.write(f"**Direction:** {row.get('direction', 'N/A')}")

    st.markdown("#### Signals")
    for s in get_risk_signals(row):
        st.write(f"- {s}")

    st.markdown("#### Recommended Action")
    st.success(get_recommended_action(row))


def render_command_center(df: pd.DataFrame, role: str) -> None:
    st.markdown("<div class='rl-section'>Command Center</div>", unsafe_allow_html=True)

    total_volume = len(df)
    approval_rate = (
        (df["status"].str.lower() == "completed").mean() * 100 if "status" in df.columns else 0
    )
    review_queue = int((df["risk_score"] >= HIGH_RISK_THRESHOLD).sum())
    fraud_rate = df["is_fraud_label"].mean() * 100 if "is_fraud_label" in df.columns else 0
    failure_rate = (
        (df["status"].str.lower().isin(["failed", "flagged"])).mean() * 100
        if "status" in df.columns
        else 0
    )
    top_risk_rail = (
        df.groupby("payment_rail")["risk_score"].mean().sort_values(ascending=False).index[0]
        if "payment_rail" in df.columns
        else "N/A"
    )

    k1, k2, k3, k4, k5, k6 = st.columns(6)
    with k1:
        render_kpi_card("Total Volume", f"{total_volume:,}")
    with k2:
        render_kpi_card("Approval Rate", f"{approval_rate:.1f}%")
    with k3:
        render_kpi_card("Review Queue", f"{review_queue:,}")
    with k4:
        render_kpi_card("Failure Rate", f"{failure_rate:.1f}%")
    with k5:
        render_kpi_card("Fraud Rate", f"{fraud_rate:.1f}%")
    with k6:
        render_kpi_card("Top Risk Rail", top_risk_rail)

    c1, c2 = st.columns([1.1, 1])

    with c1:
        rail_stats = (
            df.groupby("payment_rail")
            .agg(
                transactions=("transaction_id", "count"),
                avg_risk=("risk_score", "mean"),
                fraud_rate=("is_fraud_label", "mean"),
            )
            .reset_index()
        )
        rail_stats["fraud_rate"] = rail_stats["fraud_rate"] * 100
        fig = px.bar(
            rail_stats,
            x="payment_rail",
            y="avg_risk",
            color="fraud_rate",
            title="Payment Rail Risk Intelligence",
            labels={"avg_risk": "Average Risk Score", "fraud_rate": "Fraud Rate %"},
        )
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        status_counts = (
            df.groupby("status", dropna=False)
            .size()
            .reset_index(name="count")
            .sort_values("count", ascending=False)
        )
        fig2 = px.pie(status_counts, names="status", values="count", title="Status Mix")
        st.plotly_chart(fig2, use_container_width=True)

    d1, d2 = st.columns(2)
    with d1:
        fig3 = px.scatter(
            df,
            x="amount",
            y="risk_score",
            color="payment_rail",
            hover_data=["transaction_id", "customer_id", "channel"],
            title="Amount vs Risk Score",
        )
        st.plotly_chart(fig3, use_container_width=True)

    with d2:
        geo_view = (
            df.groupby(["origin_country", "destination_country"], dropna=False)
            .agg(avg_risk=("risk_score", "mean"), txns=("transaction_id", "count"))
            .reset_index()
        )
        geo_view["corridor"] = geo_view["origin_country"] + " → " + geo_view["destination_country"]
        fig4 = px.bar(
            geo_view.sort_values("avg_risk", ascending=False).head(8),
            x="corridor",
            y="avg_risk",
            hover_data=["txns"],
            title="Top Risk Corridors",
        )
        st.plotly_chart(fig4, use_container_width=True)

    if role == "Product Manager":
        st.info(
            "Product view: focus on rail-level friction, fraud concentration, and approval-rate tradeoffs."
        )
    elif role == "Payments Ops Manager":
        st.info(
            "Ops view: focus on exception load, flagged queue, and payment rail performance."
        )
    elif role == "Compliance Reviewer":
        st.info(
            "Compliance view: focus on alert rationale, audit trail, and repeat high-risk behavior."
        )


def render_investigations(df: pd.DataFrame, query_engine: QueryEngine) -> None:
    st.markdown("<div class='rl-section'>Investigations</div>", unsafe_allow_html=True)

    left, right = st.columns([1.25, 0.85])

    with left:
        st.markdown("#### Investigation Assistant")
        e1, e2, e3, e4 = st.columns(4)
        if e1.button("Why was TXN-30002 flagged?"):
            st.session_state["prompt"] = "Why was TXN-30002 flagged?"
        if e2.button("Show high-risk ACH transactions"):
            st.session_state["prompt"] = "Show high-risk ACH transactions"
        if e3.button("Which payment rail has highest fraud rate?"):
            st.session_state["prompt"] = "Which payment rail has highest fraud rate?"
        if e4.button("Summarize suspicious patterns"):
            st.session_state["prompt"] = "Summarize suspicious patterns"

        prompt = st.text_input(
            "Ask a question",
            value=st.session_state.get("prompt", ""),
            placeholder="Type analyst-style investigation prompt",
        )

        if st.button("Run Investigation", type="primary") or prompt:
            summary, result_df = derive_investigation_results(prompt, df)
            st.markdown("##### Findings")
            st.info(summary)

            kb = query_engine.answer(prompt)
            if kb:
                st.markdown("##### Knowledge Context")
                st.write(kb)

            st.markdown("##### Matching Records")
            st.dataframe(result_df, use_container_width=True, height=300)

            if not result_df.empty:
                st.markdown("##### Case Notes Generator")
                notes = generate_case_notes(result_df)
                st.text_area("Analyst Case Notes", notes, height=220)

                csv = result_df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    "Download Investigation Report",
                    data=csv,
                    file_name="investigation_report.csv",
                    mime="text/csv",
                )

                st.session_state["investigation_result"] = result_df

    with right:
        st.markdown("#### Transaction Detail")
        current = st.session_state.get("investigation_result")
        if isinstance(current, pd.DataFrame) and not current.empty:
            render_transaction_detail(current.reset_index(drop=True).iloc[0])
        else:
            st.markdown("<div class='rl-card'>Run an investigation to inspect a selected transaction.</div>", unsafe_allow_html=True)


def render_payment_intelligence(df: pd.DataFrame) -> None:
    st.markdown("<div class='rl-section'>Payment Intelligence</div>", unsafe_allow_html=True)

    rail_cards = df.groupby("payment_rail").agg(
        txns=("transaction_id", "count"),
        avg_risk=("risk_score", "mean"),
        fail_rate=("status", lambda x: (x.str.lower().isin(["failed", "flagged"])).mean() * 100),
    ).reset_index()

    cols = st.columns(min(4, len(rail_cards)))
    for col, (_, row) in zip(cols, rail_cards.iterrows()):
        with col:
            st.markdown(
                f"""
                <div class="rl-card">
                    <div class="rl-section" style="font-size:1.0rem;margin-bottom:0.2rem;">{row['payment_rail']}</div>
                    <div class="rl-small">{int(row['txns'])} transactions</div>
                    <div class="rl-small">Avg risk: {row['avg_risk']:.1f}</div>
                    <div class="rl-small">Fail / review rate: {row['fail_rate']:.1f}%</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    c1, c2 = st.columns(2)
    with c1:
        channel_risk = (
            df.groupby(["channel", "payment_rail"], dropna=False)["risk_score"]
            .mean()
            .reset_index()
        )
        fig = px.bar(
            channel_risk,
            x="channel",
            y="risk_score",
            color="payment_rail",
            barmode="group",
            title="Risk by Channel and Rail",
        )
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        customer_risk = (
            df.groupby("customer_id", dropna=False)
            .agg(txns=("transaction_id", "count"), avg_risk=("risk_score", "mean"), amount=("amount", "sum"))
            .reset_index()
            .sort_values(["avg_risk", "amount"], ascending=False)
            .head(10)
        )
        fig2 = px.bar(
            customer_risk,
            x="customer_id",
            y="avg_risk",
            hover_data=["txns", "amount"],
            title="Top Customer Risk Profiles",
        )
        st.plotly_chart(fig2, use_container_width=True)

    if "timestamp" in df.columns and df["timestamp"].notna().any():
        trend = (
            df.assign(hour=df["timestamp"].dt.hour)
            .groupby("hour", dropna=False)
            .agg(txns=("transaction_id", "count"), avg_risk=("risk_score", "mean"))
            .reset_index()
        )
        fig3 = px.line(trend, x="hour", y="avg_risk", markers=True, title="Hourly Risk Trend")
        st.plotly_chart(fig3, use_container_width=True)


def render_alerts_and_cases(df: pd.DataFrame) -> None:
    st.markdown("<div class='rl-section'>Alerts & Cases</div>", unsafe_allow_html=True)

    queue = df[(df["risk_score"] >= HIGH_RISK_THRESHOLD) | (df["status"].str.lower() == "flagged")].copy()
    if queue.empty:
        st.info("No alerts currently meet the review threshold.")
        return

    queue["priority"] = queue["risk_score"].apply(get_priority)
    queue["recommended_action"] = queue.apply(get_recommended_action, axis=1)
    queue["signals"] = queue.apply(lambda r: ", ".join(get_risk_signals(r)), axis=1)
    queue["case_status"] = "Open"
    queue["assigned_to"] = queue["priority"].map(
        {"Critical": "Tier 2 Analyst", "High": "Fraud Analyst", "Medium": "Payments Ops", "Low": "Monitor"}
    )

    st.dataframe(
        queue[
            [
                "transaction_id",
                "customer_id",
                "payment_rail",
                "amount",
                "risk_score",
                "priority",
                "assigned_to",
                "case_status",
                "recommended_action",
                "signals",
            ]
        ].sort_values(["risk_score", "amount"], ascending=False),
        use_container_width=True,
        height=420,
    )


def render_rules_explainability(df: pd.DataFrame) -> None:
    st.markdown("<div class='rl-section'>Rules & Explainability</div>", unsafe_allow_html=True)

    sample_row = df.sort_values("risk_score", ascending=False).iloc[0]
    st.markdown("#### Risk Breakdown Example")
    parts = []
    if sample_row["amount"] >= 10000:
        parts.append(("Large amount", 25))
    if sample_row["geo_mismatch_flag"] == 1:
        parts.append(("Geo mismatch", 20))
    if sample_row["velocity_flag"] == 1:
        parts.append(("Velocity", 18))
    if sample_row["beneficiary_change_flag"] == 1:
        parts.append(("Beneficiary change", 17))
    if str(sample_row["payment_rail"]).lower() == "wire":
        parts.append(("Wire sensitivity", 12))

    breakdown = pd.DataFrame(parts, columns=["signal", "points"])
    if breakdown.empty:
        breakdown = pd.DataFrame([("Base monitoring", int(sample_row["risk_score"]))], columns=["signal", "points"])

    fig = px.bar(
        breakdown,
        x="signal",
        y="points",
        title=f"Explainability for {sample_row['transaction_id']}",
    )
    st.plotly_chart(fig, use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### Rule Triggers")
        for sig in get_risk_signals(sample_row):
            st.write(f"- {sig}")

    with c2:
        st.markdown("#### Recommendation")
        st.success(get_recommended_action(sample_row))


def render_admin_data(df: pd.DataFrame) -> None:
    st.markdown("<div class='rl-section'>Admin / Data</div>", unsafe_allow_html=True)
    st.markdown("#### Loaded Schema")
    st.dataframe(pd.DataFrame({"column_name": df.columns}), use_container_width=True, height=280)

    with st.expander("Sample schema expectations"):
        for c in REQUIRED_COLUMNS:
            st.write(f"- {c}")


def main() -> None:
    apply_custom_css()

    if "prompt" not in st.session_state:
        st.session_state["prompt"] = ""

    with st.sidebar:
        st.markdown("## RiskLens AI")
        role = st.selectbox("Role View", ROLE_OPTIONS, index=0)
        page = st.radio("Navigate", PAGE_OPTIONS)
        st.markdown("---")
        uploaded_file = st.file_uploader("Upload transaction CSV", type=["csv"])
        use_sample = st.checkbox("Use built-in sample dataset", value=True)

    try:
        if uploaded_file is not None:
            df = load_transactions(uploaded_file=uploaded_file)
            dataset_label = f"Uploaded file: {uploaded_file.name}"
        elif use_sample:
            df = load_transactions(DEFAULT_DATA_PATH)
            dataset_label = "Built-in sample dataset"
        else:
            st.warning("Upload a CSV or enable the sample dataset.")
            return

        df = coerce_types(df)
        missing = validate_dataframe(df)
        if missing:
            st.error(f"Unable to load dataset: Dataset is missing required columns: {missing}")
            return

    except Exception as exc:
        st.error(f"Unable to load dataset: {exc}")
        return

    filtered_df = add_filter_sidebar(df)
    query_engine = build_query_engine()

    render_header(role)
    st.write(f"**Loaded dataset:** {dataset_label}")

    if page == "Command Center":
        render_command_center(filtered_df, role)
    elif page == "Investigations":
        render_investigations(filtered_df, query_engine)
    elif page == "Payment Intelligence":
        render_payment_intelligence(filtered_df)
    elif page == "Alerts & Cases":
        render_alerts_and_cases(filtered_df)
    elif page == "Rules & Explainability":
        render_rules_explainability(filtered_df)
    elif page == "Admin / Data":
        render_admin_data(filtered_df)


if __name__ == "__main__":
    main()
