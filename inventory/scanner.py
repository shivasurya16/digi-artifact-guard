from pathlib import Path
from typing import Iterator

from ingestion.source import ProjectSource


class ProjectScanner:
    """
    Recursively scans a project source and yields discovered files.

    The scanner is read-only. It never modifies the source project.
    """

    def __init__(self, source: ProjectSource):
        self.source = source

    def scan(self) -> Iterator[Path]:
        """
        Yield every regular file inside the project.

        Directories themselves are not yielded as artifacts yet.
        """
        root = self.source.get_root()

        for path in root.rglob("*"):
            if path.is_file():
                yield path