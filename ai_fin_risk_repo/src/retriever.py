from __future__ import annotations

from typing import List, Dict

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class LocalRetriever:
    def __init__(self, docs: List[Dict[str, str]]):
        self.docs = docs
        corpus = [f"{d['title']} {d['content']}" for d in docs]
        self.vectorizer = TfidfVectorizer(stop_words="english")
        self.matrix = self.vectorizer.fit_transform(corpus)

    def search(self, query: str, top_k: int = 2) -> List[Dict[str, str]]:
        query_vec = self.vectorizer.transform([query])
        sims = cosine_similarity(query_vec, self.matrix).flatten()
        ranked_idx = sims.argsort()[::-1][:top_k]
        results = []
        for idx in ranked_idx:
            doc = self.docs[idx].copy()
            doc["score"] = float(sims[idx])
            results.append(doc)
        return results
