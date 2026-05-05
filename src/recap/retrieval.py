"""BM25 retrieval over patient events. No external deps."""

import re
from collections import Counter
from math import log

from recap.models import Event


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[A-Za-z0-9]+", text.lower())


def retrieve(query: str, events: list[Event], top_k: int = 5) -> list[Event]:
    """Rank events by BM25 over title+body.

    On no-match, falls back to the first `top_k` events so the caller always
    gets something to send to the LLM rather than an empty context.
    """
    if not events:
        return []

    query_tokens = _tokenize(query)
    if not query_tokens:
        return events[:top_k]

    docs = [_tokenize(f"{e.title} {e.body}") for e in events]
    avgdl = sum(len(d) for d in docs) / len(docs)

    df: Counter = Counter()
    for d in docs:
        for tok in set(d):
            df[tok] += 1

    n = len(docs)
    k1, b = 1.5, 0.75

    scores: list[tuple[float, int]] = []
    for i, d in enumerate(docs):
        score = 0.0
        tf = Counter(d)
        for q in query_tokens:
            if q not in tf:
                continue
            idf = log((n - df[q] + 0.5) / (df[q] + 0.5) + 1)
            num = tf[q] * (k1 + 1)
            den = tf[q] + k1 * (1 - b + b * len(d) / max(avgdl, 1))
            score += idf * num / den
        scores.append((score, i))

    scores.sort(reverse=True)
    ranked = [events[i] for s, i in scores[:top_k] if s > 0]
    return ranked or events[:top_k]
