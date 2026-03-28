from __future__ import annotations

from typing import Any


class LocalRetriever:
    def __init__(self, documents: list[Any]):
        self.documents = documents or []

    def retrieve(self, query: str, top_k: int = 3) -> list[str]:
        if not query:
            return []

        q_terms = set(query.lower().split())
        scored = []

        for doc in self.documents:
            if isinstance(doc, dict):
                text = str(doc.get("text") or doc.get("content") or "")
            else:
                text = str(doc)

            text_lower = text.lower()
            score = sum(1 for term in q_terms if term in text_lower)
            if score > 0:
                scored.append((score, text))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [text for _, text in scored[:top_k]]
