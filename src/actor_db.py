"""Simple in-memory actor database for canonical actor embeddings.

This stores actor names with representative embeddings and metadata. It's
meant as a lightweight, testable replacement for a production actor store.

Supports persistence: save() / load() for JSON-based storage.
"""

from typing import Dict, List, Any, Optional, Tuple
import math
import json
from pathlib import Path


def _cosine(a: List[float], b: List[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


class ActorDB:
    def __init__(self, dim: int):
        self.dim = dim
        self._actors: Dict[str, Dict[str, Any]] = {}

    def add_actor(
        self, name: str, embedding: List[float], metadata: Dict[str, Any] = None
    ):
        if len(embedding) != self.dim:
            raise ValueError("embedding dimension mismatch")
        self._actors[name] = {"embedding": embedding, "metadata": metadata or {}}

    def find_best(
        self, embedding: List[float], threshold: float = 0.7
    ) -> Dict[str, Any]:
        best_name: Optional[str] = None
        best_score = -1.0
        for name, rec in self._actors.items():
            s = _cosine(embedding, rec["embedding"])
            if s > best_score:
                best_score = s
                best_name = name
        if best_name is None or best_score < threshold:
            return {
                "matched": False,
                "name": "unknown",
                "confidence": float(best_score if best_score >= 0 else 0.0),
            }
        return {"matched": True, "name": best_name, "confidence": float(best_score)}

    def list_actors(self) -> List[str]:
        return list(self._actors.keys())

    def save(self, path: str):
        """Save actor database to JSON file."""
        data = {"dim": self.dim, "actors": self._actors}
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    @staticmethod
    def load(path: str) -> "ActorDB":
        """Load actor database from JSON file."""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        db = ActorDB(data["dim"])
        for name, rec in data.get("actors", {}).items():
            db._actors[name] = rec
        return db


__all__ = ["ActorDB"]
