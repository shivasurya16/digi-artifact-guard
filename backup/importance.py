from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ImportanceResult:
    """
    Importance classification for an artifact.

    score:
        0-100 importance score.

    level:
        HIGH, MEDIUM, or LOW.

    reasons:
        Human-readable evidence explaining the score.

    backup:
        Whether the artifact should be included in the
        important-artifact backup.
    """

    score: int
    level: str
    reasons: list[str]
    backup: bool


# Files that are normally disposable and should not consume
# backup space.
LOW_VALUE_NAMES = {
    ".ds_store",
    "thumbs.db",
    "desktop.ini",
}

LOW_VALUE_EXTENSIONS = {
    ".pyc",
    ".pyo",
    ".tmp",
    ".temp",
    ".bak",
    ".swp",
    ".swo",
    ".log",
    ".cache",
}

LOW_VALUE_DIRECTORIES = {
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".tox",
    ".coverage",
    "node_modules",
    ".git",
    ".idea",
    ".vscode",
}


# Strong indicators that an artifact is important.
HIGH_VALUE_EXTENSIONS = {
    # Source code
    ".py",
    ".js",
    ".ts",
    ".jsx",
    ".tsx",
    ".java",
    ".c",
    ".cpp",
    ".h",
    ".hpp",
    ".cs",
    ".go",
    ".rs",
    ".rb",
    ".php",
    ".swift",
    ".kt",

    # Configuration
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".ini",
    ".cfg",
    ".conf",
    ".xml",

    # Models / checkpoints
    ".pkl",
    ".pickle",
    ".joblib",
    ".pt",
    ".pth",
    ".onnx",
    ".h5",
    ".hdf5",
    ".ckpt",
    ".safetensors",

    # Notebooks
    ".ipynb",

    # Databases / schemas
    ".sql",
    ".db",
    ".sqlite",
    ".sqlite3",

    # Documentation
    ".md",
    ".rst",
}

MEDIUM_VALUE_EXTENSIONS = {
    # Data
    ".csv",
    ".tsv",
    ".jsonl",
    ".parquet",

    # Common project assets
    ".txt",
    ".html",
    ".css",
    ".scss",

    # Environment/project files
    ".env",
}


IMPORTANT_NAMES = {
    "readme",
    "readme.md",
    "readme.txt",
    "license",
    "license.md",
    "requirements.txt",
    "requirements-dev.txt",
    "pyproject.toml",
    "setup.py",
    "setup.cfg",
    "package.json",
    "package-lock.json",
    "poetry.lock",
    "pipfile",
    "pipfile.lock",
    "dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
    ".gitignore",
}


def _normalise(value: str) -> str:
    return value.replace("\\", "/").lower().strip("/")


def _is_inside_low_value_directory(path: Path) -> bool:
    parts = {
        part.lower()
        for part in path.parts
    }

    return bool(parts.intersection(LOW_VALUE_DIRECTORIES))


def classify_artifact(
    path: Path,
    *,
    referenced: bool = False,
    referenced_by_count: int = 0,
    exists: bool = True,
) -> ImportanceResult:
    """
    Classify one artifact for important-artifact backup.

    The original file is NEVER modified or deleted.

    Parameters
    ----------
    path:
        Artifact path.

    referenced:
        True when another surviving artifact explicitly references
        this artifact.

    referenced_by_count:
        Number of surviving artifacts that reference this artifact.

    exists:
        Whether the artifact currently exists.
    """

    name = path.name.lower()
    suffix = path.suffix.lower()

    reasons: list[str] = []
    score = 0

    # Missing artifacts cannot themselves be copied into a backup.
    if not exists:
        return ImportanceResult(
            score=0,
            level="LOW",
            reasons=["Artifact does not currently exist."],
            backup=False,
        )

    # Disposable directory takes priority.
    if _is_inside_low_value_directory(path):
        return ImportanceResult(
            score=0,
            level="LOW",
            reasons=[
                "Located inside a disposable/cache directory."
            ],
            backup=False,
        )

    # Explicit disposable names.
    if name in LOW_VALUE_NAMES:
        return ImportanceResult(
            score=0,
            level="LOW",
            reasons=["Known disposable system artifact."],
            backup=False,
        )

    # Explicit disposable extensions.
    if suffix in LOW_VALUE_EXTENSIONS:
        return ImportanceResult(
            score=5,
            level="LOW",
            reasons=[
                f"Disposable/generated extension: {suffix}"
            ],
            backup=False,
        )

    # Important project names.
    if name in IMPORTANT_NAMES:
        score += 90
        reasons.append("Important project metadata/documentation.")

    # High-value artifact types.
    if suffix in HIGH_VALUE_EXTENSIONS:
        score += 70
        reasons.append(
            f"Important artifact type: {suffix}"
        )

    # Medium-value artifact types.
    elif suffix in MEDIUM_VALUE_EXTENSIONS:
        score += 40
        reasons.append(
            f"Supporting artifact type: {suffix}"
        )

    # Explicit references are very strong evidence.
    if referenced:
        score += 25

        if referenced_by_count > 1:
            score += min(
                referenced_by_count * 5,
                20,
            )

        reasons.append(
            "Explicitly referenced by surviving project artifacts."
        )

    # Files with no recognized value still get a small baseline.
    if score == 0:
        score = 15
        reasons.append(
            "No strong preservation indicators detected."
        )

    # Cap score.
    score = min(score, 100)

    if score >= 70:
        level = "HIGH"
        backup = True

    elif score >= 40:
        level = "MEDIUM"
        backup = True

    else:
        level = "LOW"
        backup = False

    return ImportanceResult(
        score=score,
        level=level,
        reasons=reasons,
        backup=backup,
    )