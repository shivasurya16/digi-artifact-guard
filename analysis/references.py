from pathlib import Path
import re

from core.models import Artifact
from core.relationships import ArtifactReference


class ReferenceExtractor:
    """
    Extract explicit file/path references from textual artifacts.
    """

    TEXT_EXTENSIONS = {
        ".py",
        ".pyw",
        ".js",
        ".jsx",
        ".ts",
        ".tsx",
        ".java",
        ".c",
        ".h",
        ".cpp",
        ".hpp",
        ".cs",
        ".go",
        ".rs",
        ".rb",
        ".php",
        ".swift",
        ".kt",
        ".kts",
        ".scala",
        ".sh",
        ".bat",
        ".ps1",
        ".md",
        ".markdown",
        ".txt",
        ".rst",
        ".json",
        ".yaml",
        ".yml",
        ".toml",
        ".ini",
        ".cfg",
        ".conf",
        ".xml",
        ".html",
        ".htm",
        ".css",
        ".scss",
        ".log",
    }

    FILE_PATTERN = re.compile(
        r"[A-Za-z0-9_.-]+(?:[\\/][A-Za-z0-9_.-]+)*\.[A-Za-z0-9]+"
    )

    def _is_textual(self, artifact: Artifact) -> bool:
        extension = artifact.extension.lower()
        return extension in self.TEXT_EXTENSIONS

    def extract(
        self,
        artifact: Artifact,
        absolute_path: Path,
        known_artifacts: list[Artifact],
    ) -> list[ArtifactReference]:

        if not self._is_textual(artifact):
            return []

        try:
            content = absolute_path.read_text(
                encoding="utf-8",
                errors="ignore",
            )
        except OSError:
            return []

        known_paths: dict[str, Artifact] = {}

        for item in known_artifacts:
            normalized_path = (
                item.path
                .replace("\\", "/")
                .lower()
            )

            known_paths[normalized_path] = item

            filename = Path(item.path).name.lower()

            known_paths.setdefault(
                filename,
                item,
            )

        references: list[ArtifactReference] = []
        seen: set[str] = set()

        for match in self.FILE_PATTERN.finditer(content):

            reference = match.group(0)

            reference = reference.rstrip(
                ".,;:!?)]}"
            )

            if not reference:
                continue

            normalized = (
                reference
                .replace("\\", "/")
                .lower()
            )

            if normalized in seen:
                continue

            seen.add(normalized)

            target = known_paths.get(normalized)

            references.append(
                ArtifactReference(
                    source_artifact_id=artifact.id,
                    source_path=artifact.path,
                    reference=reference,
                    reference_type="file_reference",
                    target_exists=target is not None,
                    target_artifact_id=(
                        target.id
                        if target is not None
                        else None
                    ),
                    metadata={
                        "normalized_reference": normalized,
                    },
                )
            )

        return references