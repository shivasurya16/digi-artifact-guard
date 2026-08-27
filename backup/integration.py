from __future__ import annotations

from collections import Counter
from typing import Iterable

from core.relationships import ArtifactReference


def build_reference_counts(
    references: Iterable[ArtifactReference],
) -> dict[str, int]:
    """
    Build a mapping:

        referenced path -> number of references

    Example:

        models/model.pkl -> 3
    """

    counts: Counter[str] = Counter()

    for reference in references:

        if reference.target_exists:
            continue

        # Missing artifacts are not available to backup,
        # so they are deliberately ignored here.
        continue

    return dict(counts)


def build_existing_reference_counts(
    references: Iterable[ArtifactReference],
) -> dict[str, int]:
    """
    Count references to artifacts that actually exist.

    These artifacts receive additional backup importance.
    """

    counts: Counter[str] = Counter()

    for reference in references:

        if not reference.target_exists:
            continue

        path = str(
            reference.reference
        ).replace("\\", "/")

        counts[path] += 1

    return dict(counts)