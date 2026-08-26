from dataclasses import dataclass, field
from pathlib import Path
import hashlib
import re


@dataclass
class RecoveryCandidate:
    missing_path: str
    candidate_path: str
    score: float
    reasons: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


class RecoveryCandidateEngine:

    VERSION_PATTERN = re.compile(
        r"^(.*?)(?:[_\- ]?v?)(\d+)(\.[^.]+)?$",
        re.IGNORECASE,
    )

    def find_candidates(
        self,
        missing_path: str,
        artifacts,
        project_root=None,
    ) -> list[RecoveryCandidate]:

        missing = Path(missing_path)

        candidates = []

        for artifact in artifacts:

            candidate_path = Path(
                artifact.path
            )

            score, reasons = self._score(
                missing,
                candidate_path,
                artifact,
                project_root,
            )

            if score <= 0:
                continue

            candidates.append(
                RecoveryCandidate(
                    missing_path=str(missing_path),
                    candidate_path=str(
                        artifact.path
                    ),
                    score=round(score, 3),
                    reasons=reasons,
                    metadata={
                        "candidate_artifact_id":
                            artifact.id,
                        "candidate_extension":
                            artifact.extension,
                        "candidate_size":
                            artifact.size,
                    },
                )
            )

        candidates.sort(
            key=lambda item: item.score,
            reverse=True,
        )

        return candidates

    def _score(
        self,
        missing: Path,
        candidate: Path,
        artifact,
        project_root=None,
    ):

        score = 0.0
        reasons = []

        # --------------------------------------------------
        # Extension
        # --------------------------------------------------

        if (
            missing.suffix.lower()
            == candidate.suffix.lower()
        ):
            score += 0.20
            reasons.append(
                "Same file extension"
            )

        # --------------------------------------------------
        # Exact filename
        # --------------------------------------------------

        if (
            missing.stem.lower()
            == candidate.stem.lower()
        ):
            score += 0.50
            reasons.append(
                "Exact filename match"
            )

        # --------------------------------------------------
        # Version family
        # --------------------------------------------------

        elif (
            self._remove_version(
                missing.stem
            )
            ==
            self._remove_version(
                candidate.stem
            )
        ):
            score += 0.45
            reasons.append(
                "Same versioned artifact family"
            )

        # --------------------------------------------------
        # Directory
        # --------------------------------------------------

        missing_parent = (
            str(missing.parent)
            .replace("\\", "/")
            .lower()
        )

        candidate_parent = (
            str(candidate.parent)
            .replace("\\", "/")
            .lower()
        )

        if missing_parent == candidate_parent:

            score += 0.15

            reasons.append(
                "Same directory"
            )

        # --------------------------------------------------
        # Filename token similarity
        # --------------------------------------------------

        missing_tokens = set(
            self._tokens(
                missing.stem
            )
        )

        candidate_tokens = set(
            self._tokens(
                candidate.stem
            )
        )

        if missing_tokens and candidate_tokens:

            intersection = (
                missing_tokens
                & candidate_tokens
            )

            union = (
                missing_tokens
                | candidate_tokens
            )

            similarity = (
                len(intersection)
                / len(union)
            )

            if similarity >= 0.5:

                score += (
                    0.15
                    * similarity
                )

                reasons.append(
                    "Similar filename tokens"
                )

        # --------------------------------------------------
        # Artifact type
        # --------------------------------------------------

        artifact_type = getattr(
            artifact,
            "artifact_type",
            None,
        )

        if artifact_type:

            inferred_type = (
                self._infer_type(
                    candidate
                )
            )

            if artifact_type == inferred_type:

                score += 0.10

                reasons.append(
                    "Same artifact type"
                )

        # --------------------------------------------------
        # Candidate existence
        # --------------------------------------------------

        actual_candidate = self._resolve(
            candidate,
            project_root,
        )

        if actual_candidate is not None:

            if actual_candidate.is_file():

                reasons.append(
                    "Candidate exists on disk"
                )

        return min(score, 1.0), reasons

    def _resolve(
        self,
        path: Path,
        project_root,
    ):

        if path.is_absolute():

            if path.exists():
                return path

            return None

        if project_root is not None:

            resolved = (
                Path(project_root)
                / path
            )

            if resolved.exists():
                return resolved

        if path.exists():
            return path

        return None

    def _infer_type(
        self,
        path: Path,
    ) -> str:

        extension = (
            path.suffix.lower()
        )

        mapping = {
            ".py": "source_code",
            ".js": "source_code",
            ".ts": "source_code",
            ".java": "source_code",
            ".cpp": "source_code",
            ".c": "source_code",

            ".json": "configuration",
            ".yaml": "configuration",
            ".yml": "configuration",
            ".toml": "configuration",
            ".ini": "configuration",

            ".md": "document",
            ".txt": "document",

            ".pkl": "model",
            ".pt": "model",
            ".pth": "model",
            ".onnx": "model",
        }

        return mapping.get(
            extension,
            "unknown",
        )

    def _remove_version(
        self,
        name: str,
    ) -> str:

        match = self.VERSION_PATTERN.match(
            name
        )

        if not match:
            return name

        return match.group(1).rstrip(
            "_- "
        )

    def _tokens(
        self,
        value: str,
    ) -> list[str]:

        return [
            token
            for token in re.split(
                r"[_\-\s]+",
                value.lower(),
            )
            if token
        ]