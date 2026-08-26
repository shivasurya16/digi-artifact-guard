import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from core.models import Artifact


@dataclass
class ArtifactManifest:
    """
    Complete inventory generated from a project.
    """

    project_root: str
    generated_at: datetime
    artifacts: list[Artifact] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "project_root": self.project_root,
            "generated_at": self.generated_at.isoformat(),
            "artifact_count": len(self.artifacts),
            "artifacts": [
                artifact.to_dict()
                for artifact in self.artifacts
            ],
        }

    def save(self, output_path: Path) -> None:
        """
        Save the manifest as formatted JSON.
        """

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with output_path.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                self.to_dict(),
                file,
                indent=2,
                ensure_ascii=False,
            )