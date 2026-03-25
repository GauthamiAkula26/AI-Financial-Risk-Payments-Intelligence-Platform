from __future__ import annotations

from typing import Dict, List


def explain_transaction(txn: Dict, retrieved_docs: List[Dict]) -> str:
    reasons = txn.get("risk_reasons", "")
    related_context = " ".join([doc["content"] for doc in retrieved_docs[:2]])

    return (
        f"Transaction {txn['transaction_id']} is classified as {txn['risk_band']} risk with a score of "
        f"{txn['risk_score']}. Key reasons: {reasons if reasons else 'No major rule triggers found'}. "
        f"Current status is {txn['status']} on rail {txn['payment_rail']} for amount {txn['amount']} {txn['currency']}. "
        f"Context: {related_context}"
    )


def explain_failure_summary(failure_df) -> str:
    if failure_df.empty:
        return "No payment rail data available."

    top = failure_df.iloc[0]
    return (
        f"The highest failure rate is on {top['payment_rail']} at {top['failure_rate_pct']}%. "
        f"This rail has {int(top['failed_transactions'])} failed transactions out of "
        f"{int(top['total_transactions'])}."
    )


def explain_risk_patterns(pattern_df) -> str:
    top_rows = pattern_df.head(3).to_dict("records")
    if not top_rows:
        return "No significant risk patterns were found."
    pattern_text = ", ".join([f"{row['pattern']} ({row['count']})" for row in top_rows])
    return f"Top observed risk patterns are: {pattern_text}."
