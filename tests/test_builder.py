from ingestion.local import LocalProjectSource
from inventory.builder import ArtifactBuilder
from inventory.scanner import ProjectScanner


def test_artifact_builder(tmp_path):
    project = tmp_path / "project"
    project.mkdir()

    source = project / "src"
    source.mkdir()

    file = source / "hello.py"
    file.write_text("print('hello')")

    project_source = LocalProjectSource(project)
    scanner = ProjectScanner(project_source)
    builder = ArtifactBuilder(project)

    paths = list(scanner.scan())

    artifact = builder.build(
        paths[0],
        "artifact_000001",
    )

    assert artifact.id == "artifact_000001"
    assert artifact.path == "src\\hello.py"
    assert artifact.name == "hello.py"
    assert artifact.extension == ".py"
    assert artifact.artifact_type == "source_code"
    assert artifact.size > 0
    assert len(artifact.sha256) == 64