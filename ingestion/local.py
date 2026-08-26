from pathlib import Path

from ingestion.source import ProjectSource


class LocalProjectSource(ProjectSource):
    """
    Represents a project located on the local filesystem.
    """

    def __init__(self, path: str | Path):
        self.path = Path(path).expanduser().resolve()

        if not self.path.exists():
            raise FileNotFoundError(
                f"Project path does not exist: {self.path}"
            )

        if not self.path.is_dir():
            raise NotADirectoryError(
                f"Project path is not a directory: {self.path}"
            )

    def get_root(self) -> Path:
        return self.path

    def describe(self) -> str:
        return f"Local project: {self.path}"