from core.models import Artifact


def test_artifact_creation():
    artifact = Artifact(
        id="artifact_000001",
        path="src/model.py",
        name="model.py",
        extension=".py",
        artifact_type="source_code",
        size=100,
        sha256="abc123",
        mime_type="text/plain",
        created_at=None,
        modified_at=None,
    )

    assert artifact.id == "artifact_000001"
    assert artifact.name == "model.py"
    assert artifact.artifact_type == "source_code"
    assert artifact.size == 100