from core.models import Artifact


def build_integrity_summary(
    artifacts: list[Artifact],
) -> dict:
    """
    Build deterministic integrity statistics.
    """

    from analysis.duplicates import find_duplicate_groups
    from analysis.integrity import find_empty_artifacts

    duplicate_groups = find_duplicate_groups(
        artifacts
    )

    empty_artifacts = find_empty_artifacts(
        artifacts
    )

    return {
        "artifact_count": len(artifacts),
        "duplicate_group_count": len(duplicate_groups),
        "duplicate_artifact_count": sum(
            len(group)
            for group in duplicate_groups
        ),
        "empty_artifact_count": len(
            empty_artifacts
        ),
    }