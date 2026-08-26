from datetime import datetime
from pathlib import Path

from ingestion.source import ProjectSource
from inventory.builder import ArtifactBuilder
from inventory.manifest import ArtifactManifest
from inventory.scanner import ProjectScanner


class ManifestGenerator:
    """
    Generates a complete ArtifactManifest from a project source.
    """

    def __init__(self, source: ProjectSource):
        self.source = source

    def generate(self) -> ArtifactManifest:
        root = self.source.get_root()

        scanner = ProjectScanner(self.source)
        builder = ArtifactBuilder(root)

        artifacts = []

        for index, path in enumerate(
            scanner.scan(),
            start=1,
        ):
            artifact = builder.build(
                path,
                f"artifact_{index:06d}",
            )

            artifacts.append(artifact)

        return ArtifactManifest(
            project_root=str(root),
            generated_at=datetime.now(),
            artifacts=artifacts,
        )