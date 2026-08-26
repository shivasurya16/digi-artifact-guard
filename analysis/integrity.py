from core.models import Artifact


def find_empty_artifacts(
    artifacts: list[Artifact],
) -> list[Artifact]:
    """
    Return artifacts whose size is zero bytes.
    """

    return [
        artifact
        for artifact in artifacts
        if artifact.size == 0
    ]