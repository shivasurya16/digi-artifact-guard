from pathlib import Path

from backup.engine import ImportantArtifactBackup


def test_important_artifacts_are_backed_up(tmp_path):
    project = tmp_path / "project"
    output = tmp_path / "output"

    project.mkdir()

    (project / "README.md").write_text(
        "Digi Artifact Guard",
        encoding="utf-8",
    )

    (project / "main.py").write_text(
        "print('hello')",
        encoding="utf-8",
    )

    backup = ImportantArtifactBackup(
        project,
        output,
    )

    manifest = backup.create_backup()

    assert manifest["artifact_count"] == 2

    assert (
        output / "important" / "README.md"
    ).exists()

    assert (
        output / "important" / "main.py"
    ).exists()


def test_low_value_files_are_excluded(tmp_path):
    project = tmp_path / "project"
    output = tmp_path / "output"

    project.mkdir()

    (project / "README.md").write_text(
        "Digi Artifact Guard",
        encoding="utf-8",
    )

    (project / "debug.log").write_text(
        "temporary",
        encoding="utf-8",
    )

    cache = project / "__pycache__"
    cache.mkdir()

    (cache / "test.pyc").write_text(
        "temporary",
        encoding="utf-8",
    )

    backup = ImportantArtifactBackup(
        project,
        output,
    )

    manifest = backup.create_backup()

    assert (
        output / "important" / "README.md"
    ).exists()

    assert not (
        output / "important" / "debug.log"
    ).exists()

    assert not (
        output
        / "important"
        / "__pycache__"
        / "test.pyc"
    ).exists()

    assert manifest["excluded_count"] == 2


def test_backup_manifest_contains_hash(tmp_path):
    project = tmp_path / "project"
    output = tmp_path / "output"

    project.mkdir()

    file = project / "main.py"

    file.write_text(
        "print('hello')",
        encoding="utf-8",
    )

    backup = ImportantArtifactBackup(
        project,
        output,
    )

    manifest = backup.create_backup()

    assert manifest["artifact_count"] == 1

    artifact = manifest["artifacts"][0]

    assert artifact["sha256"]
    assert len(artifact["sha256"]) == 64
    assert artifact["verified"] is True