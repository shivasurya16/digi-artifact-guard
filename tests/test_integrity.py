from analysis.integrity import find_empty_artifacts
from ingestion.local import LocalProjectSource
from inventory.generator import ManifestGenerator


def test_empty_artifact_detection(tmp_path):
    project = tmp_path / "project"
    project.mkdir()

    (project / "empty.txt").write_text("")
    (project / "normal.txt").write_text("content")

    source = LocalProjectSource(project)
    manifest = ManifestGenerator(source).generate()

    empty = find_empty_artifacts(
        manifest.artifacts
    )

    assert len(empty) == 1
    assert empty[0].name == "empty.txt"