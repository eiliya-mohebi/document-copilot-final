"""Enforce the trust contract: every citation maps to a retrieved passage."""

from __future__ import annotations

import uuid
from typing import Mapping

from app.assistant.outputs import GroundedAnswer, SourcePassage


class GroundingError(Exception):
    """The answer's citations are not supported by retrieved passages."""


def validate_grounding(
    answer: GroundedAnswer,
    retrieved: Mapping[uuid.UUID, SourcePassage],
) -> list[SourcePassage]:
    """Return the cited passages in marker order, or fail closed.

    An answer that reports insufficient evidence is allowed to carry no
    citations; anything else must cite at least one retrieved passage, and
    may only cite passages that were actually retrieved for this turn.
    """
    if answer.insufficient_evidence:
        return []

    if not answer.citations:
        raise GroundingError("Answer has no citations and does not report insufficient evidence")

    cited: list[SourcePassage] = []
    seen: set[uuid.UUID] = set()
    for citation in sorted(answer.citations, key=lambda c: c.marker):
        passage = retrieved.get(citation.chunk_id)
        if passage is None:
            raise GroundingError(
                f"Citation [{citation.marker}] references chunk {citation.chunk_id} "
                "which was not retrieved for this request"
            )
        if citation.chunk_id not in seen:
            seen.add(citation.chunk_id)
            cited.append(passage)
    return cited
