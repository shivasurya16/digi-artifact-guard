from abc import ABC, abstractmethod
from pathlib import Path


class ProjectSource(ABC):
    """
    Abstract interface for any Digi Artifact Guard project source.

    Future implementations can represent:
    - local directories
    - uploaded archives
    - cloud storage
    """

    @abstractmethod
    def get_root(self) -> Path:
        """Return the local root path exposed to the analysis engine."""
        raise NotImplementedError

    @abstractmethod
    def describe(self) -> str:
        """Return a human-readable description of the source."""
        raise NotImplementedError