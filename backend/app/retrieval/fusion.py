"""Reciprocal Rank Fusion for hybrid (semantic + lexical) retrieval."""

from __future__ import annotations

from typing import Hashable, TypeVar

ItemT = TypeVar("ItemT", bound=Hashable)

# Standard RRF dampening constant from the original Cormack et al. paper;
# keeps a top rank in one list from completely dominating the fusion.
DEFAULT_RRF_K = 60


def reciprocal_rank_fusion(
    rankings: list[list[ItemT]],
    k: int = DEFAULT_RRF_K,
) -> list[ItemT]:
    """Fuse ranked lists: score(item) = sum over lists of 1 / (k + rank).

    Ties break by first appearance across the input lists, which keeps the
    result stable for equal scores.
    """
    scores: dict[ItemT, float] = {}
    for ranking in rankings:
        for rank, item in enumerate(ranking, start=1):
            scores[item] = scores.get(item, 0.0) + 1.0 / (k + rank)
    return sorted(scores, key=lambda item: scores[item], reverse=True)
