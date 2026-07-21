"""Reciprocal Rank Fusion merges ranked lists into one hybrid ranking."""

from __future__ import annotations

from app.retrieval.fusion import reciprocal_rank_fusion


def test_item_in_both_lists_outranks_single_list_items() -> None:
    semantic = ["a", "b", "c"]
    lexical = ["b", "d"]

    fused = reciprocal_rank_fusion([semantic, lexical])

    assert fused[0] == "b"
    assert set(fused) == {"a", "b", "c", "d"}


def test_preserves_order_within_a_single_list() -> None:
    fused = reciprocal_rank_fusion([["x", "y", "z"]])
    assert fused == ["x", "y", "z"]


def test_empty_rankings_fuse_to_empty() -> None:
    assert reciprocal_rank_fusion([]) == []
    assert reciprocal_rank_fusion([[], []]) == []


def test_known_rrf_scores_with_k_zero_worked_example() -> None:
    # With k=0 the score is sum of 1/rank: a -> 1/1 + 1/2 = 1.5,
    # b -> 1/2 + 1/1 = 1.5 (tie broken by first-seen), c -> 1/3.
    fused = reciprocal_rank_fusion([["a", "b", "c"], ["b", "a"]], k=0)
    assert fused == ["a", "b", "c"]
