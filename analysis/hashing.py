import hashlib
from pathlib import Path


def calculate_sha256(path: Path, chunk_size: int = 1024 * 1024) -> str:
    """
    Calculate the SHA-256 hash of a file.

    Files are read in chunks so large artifacts do not need to
    be loaded entirely into memory.
    """

    sha256 = hashlib.sha256()

    with path.open("rb") as file:
        while chunk := file.read(chunk_size):
            sha256.update(chunk)

    return sha256.hexdigest()