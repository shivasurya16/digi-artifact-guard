from ingestion.local import LocalProjectSource
from inventory.scanner import ProjectScanner


def test_scanner_discovers_files(tmp_path):
    project = tmp_path / "project"

    src = project / "src"
    config = project / "config"

    src.mkdir(parents=True)
    config.mkdir(parents=True)

    (project / "README.md").write_text("test")
    (src / "main.py").write_text("print('hello')")
    (config / "settings.json").write_text("{}")

    source = LocalProjectSource(project)
    scanner = ProjectScanner(source)

    files = list(scanner.scan())

    assert len(files) == 3

    names = {file.name for file in files}

    assert names == {
        "README.md",
        "main.py",
        "settings.json",
    }