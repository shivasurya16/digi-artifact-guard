from ingestion.local import LocalProjectSource
from inventory.generator import ManifestGenerator
from analysis.duplicates import find_duplicate_groups


def test_duplicate_detection(tmp_path):
    project = tmp_path / "project"
    project.mkdir()

    first = project / "first.txt"
    second = project / "second.txt"
    third = project / "unique.txt"

    first.write_text("same content")
    second.write_text("same content")
    third.write_text("different content")

    source = LocalProjectSource(project)
    manifest = ManifestGenerator(source).generate()

    groups = find_duplicate_groups(
        manifest.artifacts
    )

    assert len(groups) == 1
    assert len(groups[0]) == 2

    paths = {
        artifact.path
        for artifact in groups[0]
    }

    assert paths == {
        "first.txt",
        "second.txt",
    }