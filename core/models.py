from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class Artifact:
    """
    Represents one digital artifact discovered by Digi Artifact Guard.
    """

    id: str
    path: str
    name: str
    extension: str
    artifact_type: str
    size: int
    sha256: str
    mime_type: str | None
    created_at: datetime | None
    modified_at: datetime | None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the artifact into a JSON-serializable dictionary.
        """

        data = asdict(self)

        if self.created_at is not None:
            data["created_at"] = self.created_at.isoformat()

        if self.modified_at is not None:
            data["modified_at"] = self.modified_at.isoformat()

        return data