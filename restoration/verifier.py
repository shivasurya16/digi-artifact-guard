from dataclasses import dataclass
from pathlib import Path
import hashlib


@dataclass
class VerificationResult:
    source_path: str
    restored_path: str
    source_hash: str | None
    restored_hash: str | None
    verified: bool
    status: str
    message: str


class RestorationVerifier:
    """
    Verifies that a restored artifact is byte-for-byte
    identical to its recovery source using SHA-256.
    """

    CHUNK_SIZE = 1024 * 1024

    def calculate_hash(
        self,
        path,
    ) -> str:

        path = Path(path)

        digest = hashlib.sha256()

        with path.open("rb") as file:

            while True:

                chunk = file.read(
                    self.CHUNK_SIZE
                )

                if not chunk:
                    break

                digest.update(chunk)

        return digest.hexdigest()

    def verify(
        self,
        source_path,
        restored_path,
    ) -> VerificationResult:

        source = Path(source_path)
        restored = Path(restored_path)

        if not source.exists():

            return VerificationResult(
                source_path=str(source),
                restored_path=str(restored),
                source_hash=None,
                restored_hash=None,
                verified=False,
                status="FAILED",
                message="Source file does not exist.",
            )

        if not restored.exists():

            return VerificationResult(
                source_path=str(source),
                restored_path=str(restored),
                source_hash=None,
                restored_hash=None,
                verified=False,
                status="FAILED",
                message="Restored file does not exist.",
            )

        source_hash = self.calculate_hash(
            source
        )

        restored_hash = self.calculate_hash(
            restored
        )

        if source_hash == restored_hash:

            return VerificationResult(
                source_path=str(source),
                restored_path=str(restored),
                source_hash=source_hash,
                restored_hash=restored_hash,
                verified=True,
                status="VERIFIED",
                message=(
                    "Restored artifact matches "
                    "the recovery source."
                ),
            )

        return VerificationResult(
            source_path=str(source),
            restored_path=str(restored),
            source_hash=source_hash,
            restored_hash=restored_hash,
            verified=False,
            status="CORRUPTED",
            message=(
                "Restored artifact differs "
                "from the recovery source."
            ),
        )