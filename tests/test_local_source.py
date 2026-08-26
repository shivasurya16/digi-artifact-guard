from ingestion.local import LocalProjectSource


def test_local_project_source(tmp_path):
    project = tmp_path / "project"
    project.mkdir()

    source = LocalProjectSource(project)

    assert source.get_root() == project.resolve()
    assert "Local project:" in source.describe()