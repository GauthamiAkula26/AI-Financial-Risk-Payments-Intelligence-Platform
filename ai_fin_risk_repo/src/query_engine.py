from __future__ import annotations

import re
from typing import Dict

from src.analytics import AnalyticsEngine
from src.explainer import explain_failure_summary, explain_risk_patterns, explain_transaction


class QueryEngine:
    def __init__(self, analytics: AnalyticsEngine, retriever):
        self.analytics = analytics
        self.retriever = retriever

    def answer(self, query: str) -> Dict:
        query_clean = query.strip()
        query_lower = query_clean.lower()

        txn_match = re.search(r"(txn-\d+)", query_lower)
        if txn_match:
            txn_id = txn_match.group(1).upper()
            txn = self.analytics.get_transaction(txn_id)
            if not txn:
                return {"answer": f"I could not find transaction {txn_id} in the loaded dataset.", "docs": []}
            docs = self.retriever.search(query_clean, top_k=2)
            return {"answer": explain_transaction(txn, docs), "docs": docs}

        if "failure rate" in query_lower or "highest failure" in query_lower or "ach failures" in query_lower or "show failures" in query_lower:
            df = self.analytics.failures_by_rail()
            docs = self.retriever.search(query_clean, top_k=2)
            return {"answer": explain_failure_summary(df), "docs": docs, "table": df}

        if "risk pattern" in query_lower or "suspicious patterns" in query_lower or "top risk" in query_lower:
            df = self.analytics.risk_patterns()
            docs = self.retriever.search(query_clean, top_k=2)
            return {"answer": explain_risk_patterns(df), "docs": docs, "table": df}

        docs = self.retriever.search(query_clean, top_k=2)
        if docs:
            answer = " ".join([f"{doc['title']}: {doc['content']}" for doc in docs])
            return {"answer": answer, "docs": docs}
        return {"answer": "I could not find relevant context for that question.", "docs": []}
