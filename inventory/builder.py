import mimetypes
from pathlib import Path

from analysis.hashing import calculate_sha256
from core.models import Artifact
from inventory.classifier import classify_artifact


class ArtifactBuilder:
    """
    Converts a filesystem path into a structured Artifact.
    """

    def __init__(self, project_root: Path):
        self.project_root = project_root.resolve()

    def build(self, path: Path, artifact_id: str) -> Artifact:
        path = path.resolve()

        stat = path.stat()
        relative_path = path.relative_to(self.project_root)

        mime_type, _ = mimetypes.guess_type(path.name)

        created_at = None
        modified_at = None

        if stat.st_ctime:
            from datetime import datetime

            created_at = datetime.fromtimestamp(stat.st_ctime)

        if stat.st_mtime:
            from datetime import datetime

            modified_at = datetime.fromtimestamp(stat.st_mtime)

        return Artifact(
            id=artifact_id,
            path=str(relative_path),
            name=path.name,
            extension=path.suffix.lower(),
            artifact_type=classify_artifact(path),
            size=stat.st_size,
            sha256=calculate_sha256(path),
            mime_type=mime_type,
            created_at=created_at,
            modified_at=modified_at,
            metadata={},
        )