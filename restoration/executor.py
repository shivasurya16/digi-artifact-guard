from dataclasses import dataclass
from pathlib import Path
import shutil

from restoration.verifier import RestorationVerifier


@dataclass
class RestorationResult:
    gap_id: str
    source_path: str | None
    destination_path: str | None
    status: str
    message: str
    source_hash: str | None = None
    restored_hash: str | None = None
    verified: bool = False


class RestorationExecutor:
    """
    Safely restores artifacts into a separate recovery
    workspace and cryptographically verifies the result.

    The original project is never modified.
    """

    def __init__(self, recovery_root):
        self.recovery_root = Path(
            recovery_root
        )

        self.verifier = (
            RestorationVerifier()
        )

    def restore(
        self,
        plan,
        project_root,
    ) -> RestorationResult:

        if not plan.recommended_candidate:

            return RestorationResult(
                gap_id=plan.gap_id,
                source_path=None,
                destination_path=None,
                status="SKIPPED",
                message=(
                    "No recovery candidate "
                    "was recommended."
                ),
            )

        if plan.status != "HIGH_CONFIDENCE":

            return RestorationResult(
                gap_id=plan.gap_id,
                source_path=None,
                destination_path=None,
                status="REVIEW_REQUIRED",
                message=(
                    "Restoration requires "
                    "manual review."
                ),
            )

        project_root = Path(
            project_root
        ).resolve()

        source = (
            project_root
            / plan.recommended_candidate
        ).resolve()

        if not source.exists():

            return RestorationResult(
                gap_id=plan.gap_id,
                source_path=str(source),
                destination_path=None,
                status="FAILED",
                message=(
                    "Recovery candidate "
                    "does not exist."
                ),
            )

        if not source.is_file():

            return RestorationResult(
                gap_id=plan.gap_id,
                source_path=str(source),
                destination_path=None,
                status="FAILED",
                message=(
                    "Recovery candidate "
                    "is not a file."
                ),
            )

        recovery_root = (
            self.recovery_root.resolve()
        )

        destination = (
            recovery_root
            / Path(plan.missing_path)
        ).resolve()

        # --------------------------------------------------
        # Path traversal protection
        # --------------------------------------------------

        try:

            destination.relative_to(
                recovery_root
            )

        except ValueError:

            return RestorationResult(
                gap_id=plan.gap_id,
                source_path=str(source),
                destination_path=None,
                status="FAILED",
                message=(
                    "Unsafe restoration path."
                ),
            )

        recovery_root.mkdir(
            parents=True,
            exist_ok=True,
        )

        destination.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        if destination.exists():

            return RestorationResult(
                gap_id=plan.gap_id,
                source_path=str(source),
                destination_path=str(
                    destination
                ),
                status="SKIPPED",
                message=(
                    "Destination already exists."
                ),
            )

        # --------------------------------------------------
        # Copy
        # --------------------------------------------------

        try:

            shutil.copy2(
                source,
                destination,
            )

        except OSError as exc:

            return RestorationResult(
                gap_id=plan.gap_id,
                source_path=str(source),
                destination_path=str(
                    destination
                ),
                status="FAILED",
                message=(
                    f"Restoration failed: {exc}"
                ),
            )

        # --------------------------------------------------
        # Cryptographic verification
        # --------------------------------------------------

        verification = (
            self.verifier.verify(
                source,
                destination,
            )
        )

        if not verification.verified:

            return RestorationResult(
                gap_id=plan.gap_id,
                source_path=str(source),
                destination_path=str(
                    destination
                ),
                status="CORRUPTED",
                message=(
                    "Artifact was copied but "
                    "SHA-256 verification failed."
                ),
                source_hash=(
                    verification.source_hash
                ),
                restored_hash=(
                    verification.restored_hash
                ),
                verified=False,
            )

        return RestorationResult(
            gap_id=plan.gap_id,
            source_path=str(source),
            destination_path=str(
                destination
            ),
            status="RESTORED_VERIFIED",
            message=(
                "Artifact restored and "
                "SHA-256 verified successfully."
            ),
            source_hash=(
                verification.source_hash
            ),
            restored_hash=(
                verification.restored_hash
            ),
            verified=True,
        )