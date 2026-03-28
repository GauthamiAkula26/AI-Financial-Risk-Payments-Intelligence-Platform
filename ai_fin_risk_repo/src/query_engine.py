from __future__ import annotations

from typing import Optional


class QueryEngine:
    def __init__(self, retriever=None):
        self.retriever = retriever

    def answer(self, question: str) -> str:
        if not question:
            return ""

        if self.retriever is None:
            return ""

        try:
            results = self.retriever.retrieve(question)
        except Exception:
            return ""

        if not results:
            return ""

        if isinstance(results, list):
            return "\n\n".join(str(r) for r in results[:3])

        return str(results)
