from __future__ import annotations


class LocalRetriever:
    def __init__(self, documents):
        self.documents = documents or []

    def retrieve(self, query: str, top_k: int = 3):
        if not query:
            return []

        q_terms = set(query.lower().split())
        scored = []

        for doc in self.documents:
            text = str(doc)
            lowered = text.lower()
            score = sum(1 for t in q_terms if t in lowered)
            if score > 0:
                scored.append((score, text))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [text for _, text in scored[:top_k]]
