from __future__ import annotations


class QueryEngine:
    def __init__(self, retriever=None):
        self.retriever = retriever

    def answer(self, question: str) -> str:
        if not question or self.retriever is None:
            return ""

        try:
            results = self.retriever.retrieve(question)
        except Exception:
            return ""

        if not results:
            return ""

        if isinstance(results, list):
            cleaned = []
            for item in results[:3]:
                if isinstance(item, dict):
                    text = item.get("text") or item.get("content") or str(item)
                else:
                    text = str(item)
                cleaned.append(text)
            return "\n\n".join(cleaned)

        return str(results)
