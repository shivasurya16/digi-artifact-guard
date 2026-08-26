from analysis.python_references import (
    PythonReferenceExtractor,
)
from ingestion.local import LocalProjectSource
from inventory.generator import ManifestGenerator


def test_python_import_reference(tmp_path):

    project = tmp_path / "project"

    project.mkdir()

    src = project / "src"
    src.mkdir()

    main_file = src / "main.py"

    main_file.write_text(
        """
from src.dataset import Dataset

print("hello")
"""
    )

    dataset_file = src / "dataset.py"

    dataset_file.write_text(
        """
class Dataset:
    pass
"""
    )

    source = LocalProjectSource(
        project
    )

    manifest = ManifestGenerator(
        source
    ).generate()

    extractor = PythonReferenceExtractor()

    artifact = next(
        artifact
        for artifact in manifest.artifacts
        if artifact.path.replace("\\", "/")
        == "src/main.py"
    )

    references = extractor.extract(
        artifact,
        project / "src" / "main.py",
        manifest.artifacts,
    )

    assert len(references) == 1

    reference = references[0]

    assert reference.reference == "src.dataset"
    assert reference.reference_type == "python_import"
    assert reference.target_exists is True