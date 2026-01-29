"""Simple actor linker with a mock mode for CI and a GPU-backed placeholder.

API:
  ActorLinker(mode='auto'|'mock'|'gpu')
    add_actor(name, embedding)
    match_embedding(embedding, threshold=0.7) -> {'matched': bool, 'name': str, 'confidence': float, 'distance': float}

The mock mode uses small float vectors and cosine similarity.
"""

from typing import Dict, List, Optional
import math


def _cosine_similarity(a: List[float], b: List[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


class ActorLinker:
    def __init__(self, mode: str = "auto"):
        self.mode = mode
        self.actors: Dict[str, List[float]] = {}

    def add_actor(self, name: str, embedding: List[float]):
        self.actors[name] = embedding

    def match_embedding(self, embedding: List[float], threshold: float = 0.7) -> Dict:
        best_name: Optional[str] = None
        best_score = -1.0
        for name, emb in self.actors.items():
            s = _cosine_similarity(embedding, emb)
            if s > best_score:
                best_score = s
                best_name = name
        if best_name is None or best_score < threshold:
            return {
                "matched": False,
                "name": "unknown",
                "confidence": float(best_score),
                "distance": 1.0 - float(best_score),
            }
        return {
            "matched": True,
            "name": best_name,
            "confidence": float(best_score),
            "distance": 1.0 - float(best_score),
        }


__all__ = ["ActorLinker"]
