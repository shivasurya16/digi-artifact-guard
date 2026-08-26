from pathlib import Path


EXTENSION_TYPES = {
    # Source code
    ".py": "source_code",
    ".js": "source_code",
    ".ts": "source_code",
    ".java": "source_code",
    ".c": "source_code",
    ".cpp": "source_code",
    ".h": "source_code",
    ".hpp": "source_code",
    ".cs": "source_code",
    ".go": "source_code",
    ".rs": "source_code",
    ".php": "source_code",
    ".rb": "source_code",

    # Configuration
    ".json": "configuration",
    ".yaml": "configuration",
    ".yml": "configuration",
    ".toml": "configuration",
    ".ini": "configuration",
    ".cfg": "configuration",
    ".env": "configuration",

    # Documents
    ".md": "document",
    ".txt": "document",
    ".rst": "document",
    ".pdf": "document",
    ".docx": "document",

    # Data
    ".csv": "data",
    ".tsv": "data",
    ".xml": "data",
    ".parquet": "data",
    ".sqlite": "database",
    ".db": "database",

    # Images
    ".png": "image",
    ".jpg": "image",
    ".jpeg": "image",
    ".gif": "image",
    ".bmp": "image",
    ".webp": "image",

    # Archives
    ".zip": "archive",
    ".tar": "archive",
    ".gz": "archive",
    ".7z": "archive",

    # Models / ML artifacts
    ".pkl": "model",
    ".pickle": "model",
    ".joblib": "model",
    ".pt": "model",
    ".pth": "model",
    ".onnx": "model",
    ".h5": "model",
    ".keras": "model",

    # Logs
    ".log": "log",
}


def classify_artifact(path: Path) -> str:
    """
    Classify an artifact using its file extension.

    Unknown extensions are intentionally preserved as 'unknown'
    rather than being guessed.
    """

    extension = path.suffix.lower()

    return EXTENSION_TYPES.get(extension, "unknown")