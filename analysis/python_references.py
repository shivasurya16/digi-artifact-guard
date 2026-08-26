import ast
from pathlib import Path

from core.models import Artifact
from core.relationships import ArtifactReference


class PythonReferenceExtractor:
    """
    Extract references from Python source code using AST analysis.

    Detects:
    - import statements
    - from-import statements
    - string literals that look like file paths
    """

    def extract(
        self,
        artifact: Artifact,
        absolute_path: Path,
        known_artifacts: list[Artifact],
    ) -> list[ArtifactReference]:

        if artifact.extension.lower() != ".py":
            return []

        try:
            source = absolute_path.read_text(
                encoding="utf-8",
                errors="ignore",
            )
        except OSError:
            return []

        try:
            tree = ast.parse(
                source,
                filename=str(absolute_path),
            )
        except SyntaxError:
            return []

        references: list[ArtifactReference] = []

        references.extend(
            self._extract_imports(
                artifact,
                tree,
                known_artifacts,
            )
        )

        references.extend(
            self._extract_string_paths(
                artifact,
                tree,
                known_artifacts,
            )
        )

        return references

    def _extract_imports(
        self,
        artifact: Artifact,
        tree: ast.AST,
        known_artifacts: list[Artifact],
    ) -> list[ArtifactReference]:

        references: list[ArtifactReference] = []

        for node in ast.walk(tree):

            if isinstance(node, ast.Import):

                for alias in node.names:

                    references.append(
                        self._build_import_reference(
                            artifact,
                            alias.name,
                            known_artifacts,
                        )
                    )

            elif isinstance(node, ast.ImportFrom):

                if node.module is None:
                    continue

                references.append(
                    self._build_import_reference(
                        artifact,
                        node.module,
                        known_artifacts,
                    )
                )

        return references

    def _build_import_reference(
        self,
        artifact: Artifact,
        module: str,
        known_artifacts: list[Artifact],
    ) -> ArtifactReference:

        possible_paths = self._module_paths(
            module
        )

        target = self._resolve_target(
            possible_paths,
            known_artifacts,
        )

        return ArtifactReference(
            source_artifact_id=artifact.id,
            source_path=artifact.path,
            reference=module,
            reference_type="python_import",
            target_exists=target is not None,
            target_artifact_id=(
                target.id
                if target is not None
                else None
            ),
            metadata={
                "possible_paths": possible_paths,
            },
        )

    def _module_paths(
        self,
        module: str,
    ) -> list[str]:

        normalized = module.replace(
            ".",
            "/",
        )

        return [
            f"{normalized}.py",
            f"{normalized}/__init__.py",
        ]

    def _extract_string_paths(
        self,
        artifact: Artifact,
        tree: ast.AST,
        known_artifacts: list[Artifact],
    ) -> list[ArtifactReference]:

        references: list[ArtifactReference] = []

        for node in ast.walk(tree):

            if not isinstance(
                node,
                ast.Constant,
            ):
                continue

            if not isinstance(
                node.value,
                str,
            ):
                continue

            value = node.value.strip()

            if not self._looks_like_file_path(
                value
            ):
                continue

            target = self._resolve_target(
                [value],
                known_artifacts,
            )

            references.append(
                ArtifactReference(
                    source_artifact_id=artifact.id,
                    source_path=artifact.path,
                    reference=value,
                    reference_type="python_file_reference",
                    target_exists=target is not None,
                    target_artifact_id=(
                        target.id
                        if target is not None
                        else None
                    ),
                    metadata={},
                )
            )

        return references

    def _looks_like_file_path(
        self,
        value: str,
    ) -> bool:

        if "/" in value:
            return True

        if "\\" in value:
            return True

        suffixes = (
            ".pkl",
            ".pt",
            ".pth",
            ".json",
            ".csv",
            ".txt",
            ".yaml",
            ".yml",
            ".onnx",
            ".bin",
            ".ckpt",
            ".joblib",
        )

        return value.lower().endswith(
            suffixes
        )

    def _resolve_target(
        self,
        possible_paths: list[str],
        known_artifacts: list[Artifact],
    ) -> Artifact | None:

        lookup: dict[str, Artifact] = {}

        for artifact in known_artifacts:

            normalized = (
                artifact.path
                .replace("\\", "/")
                .lower()
            )

            lookup[normalized] = artifact

        for path in possible_paths:

            normalized = (
                path
                .replace("\\", "/")
                .lower()
            )

            if normalized in lookup:
                return lookup[normalized]

        return None