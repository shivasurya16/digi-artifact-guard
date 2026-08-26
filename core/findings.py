from dataclasses import dataclass, field
from typing import Any


@dataclass
class ArtifactGap:
    """
    Represents a potentially missing digital artifact.
    """

    gap_id: str
    referenced_path: str
    source_artifact_id: str
    source_path: str
    gap_type: str
    severity: str
    confidence: float
    reason: str
    evidence: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)