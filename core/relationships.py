from dataclasses import dataclass
from typing import Any


@dataclass
class ArtifactReference:
    """
    Represents evidence that one artifact refers to another
    artifact or path.
    """

    source_artifact_id: str
    source_path: str
    reference: str
    reference_type: str
    target_exists: bool
    target_artifact_id: str | None = None
    metadata: dict[str, Any] | None = None