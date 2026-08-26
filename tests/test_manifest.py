import json

from ingestion.local import LocalProjectSource
from inventory.generator import ManifestGenerator


def test_manifest_generation(tmp_path):
    project = tmp_path / "project"
    project.mkdir()

    (project / "README.md").write_text(
        "Digi Artifact Guard"
    )

    src = project / "src"
    src.mkdir()

    (src / "main.py").write_text(
        "print('hello')"
    )

    source = LocalProjectSource(project)

    generator = ManifestGenerator(source)

    manifest = generator.generate()

    assert manifest.project_root == str(project.resolve())
    assert len(manifest.artifacts) == 2

    output = tmp_path / "manifest.json"

    manifest.save(output)

    assert output.exists()

    data = json.loads(
        output.read_text(encoding="utf-8")
    )

    assert data["artifact_count"] == 2
    assert len(data["artifacts"]) == 2