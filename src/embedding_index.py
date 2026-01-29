"""Simple in-memory embedding index for per-scene embeddings.

This is a lightweight, dependency-free implementation used for testing and
prototyping. It supports adding scene embeddings and nearest-neighbor queries
using cosine similarity. The module is mock-friendly and intended to be
replaced with a production vector DB (FAISS/annoy/Opensearch) later.
"""

from typing import Dict, List, Any, Tuple
import math


def _cosine(a: List[float], b: List[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


class EmbeddingIndex:
    def __init__(self, dim: int):
        self.dim = dim
        self._store: Dict[str, Dict[str, Any]] = {}

    def add(
        self, scene_id: str, embedding: List[float], metadata: Dict[str, Any] = None
    ):
        if len(embedding) != self.dim:
            raise ValueError("embedding dimension mismatch")
        self._store[scene_id] = {"embedding": embedding, "metadata": metadata or {}}

    def query(
        self, embedding: List[float], top_k: int = 5
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        if len(embedding) != self.dim:
            raise ValueError("embedding dimension mismatch")
        scores = []
        for sid, rec in self._store.items():
            sc = _cosine(embedding, rec["embedding"])
            scores.append((sid, float(sc), rec.get("metadata", {})))
        scores.sort(key=lambda t: t[1], reverse=True)
        return scores[:top_k]

    def size(self) -> int:
        return len(self._store)


__all__ = ["EmbeddingIndex"]
