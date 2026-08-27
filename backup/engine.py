from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from backup.importance import classify_artifact


def sha256_file(path: Path) -> str:
    """
    Calculate SHA-256 hash of a file.
    """

    digest = hashlib.sha256()

    with path.open("rb") as file:
        for chunk in iter(
            lambda: file.read(1024 * 1024),
            b"",
        ):
            digest.update(chunk)

    return digest.hexdigest()


class ImportantArtifactBackup:
    """
    Creates a backup containing only important artifacts.

    The source project is never modified.
    """

    def __init__(
        self,
        project_root: Path,
        output_root: Path,
    ) -> None:

        self.project_root = Path(
            project_root
        ).resolve()

        self.output_root = Path(
            output_root
        ).resolve()

        self.backup_root = (
            self.output_root / "important"
        )

    def _relative_path(
        self,
        path: Path,
    ) -> Path:

        return path.resolve().relative_to(
            self.project_root
        )

    def _iter_files(
        self,
    ) -> Iterable[Path]:

        for path in self.project_root.rglob("*"):

            if not path.is_file():
                continue

            # Never backup our own generated output if it
            # happens to be inside the project.
            try:
                path.resolve().relative_to(
                    self.output_root
                )
                continue
            except ValueError:
                pass

            yield path

    def create_backup(
        self,
        *,
        references: dict[str, int] | None = None,
    ) -> dict:

        references = references or {}

        self.backup_root.mkdir(
            parents=True,
            exist_ok=True,
        )

        backed_up = []
        excluded = []

        for path in self._iter_files():

            relative = self._relative_path(path)

            relative_key = str(
                relative
            ).replace("\\", "/")

            reference_count = references.get(
                relative_key,
                0,
            )

            result = classify_artifact(
                relative,
                referenced=reference_count > 0,
                referenced_by_count=reference_count,
                exists=True,
            )

            if not result.backup:

                excluded.append(
                    {
                        "source_path": relative_key,
                        "importance": result.level,
                        "score": result.score,
                        "reasons": result.reasons,
                    }
                )

                continue

            destination = (
                self.backup_root / relative
            )

            destination.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            shutil.copy2(
                path,
                destination,
            )

            source_hash = sha256_file(path)
            backup_hash = sha256_file(destination)

            verified = (
                source_hash == backup_hash
            )

            if not verified:
                raise IOError(
                    "Backup verification failed for "
                    f"{relative_key}"
                )

            backed_up.append(
                {
                    "source_path": relative_key,
                    "backup_path": str(
                        destination.relative_to(
                            self.output_root
                        )
                    ).replace("\\", "/"),
                    "importance": result.level,
                    "score": result.score,
                    "reasons": result.reasons,
                    "size": path.stat().st_size,
                    "sha256": source_hash,
                    "verified": verified,
                }
            )

        manifest = {
            "backup_policy": (
                "important_artifacts_only"
            ),
            "generated_at": datetime.now(
                timezone.utc
            ).isoformat(),
            "project_root": str(
                self.project_root
            ),
            "artifact_count": len(
                backed_up
            ),
            "excluded_count": len(
                excluded
            ),
            "artifacts": backed_up,
            "excluded": excluded,
        }

        manifest_path = (
            self.output_root
            / "backup_manifest.json"
        )

        manifest_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        manifest_path.write_text(
            json.dumps(
                manifest,
                indent=2,
            ),
            encoding="utf-8",
        )

        return manifest