from collections import defaultdict

from core.models import Artifact


def find_duplicate_groups(
    artifacts: list[Artifact],
) -> list[list[Artifact]]:
    """
    Find groups of artifacts with identical SHA-256 hashes.

    Each returned group contains two or more artifacts
    with identical byte content.
    """

    hash_groups: dict[str, list[Artifact]] = defaultdict(list)

    for artifact in artifacts:
        hash_groups[artifact.sha256].append(artifact)

    return [
        group
        for group in hash_groups.values()
        if len(group) > 1
    ]