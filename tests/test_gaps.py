from analysis.gaps import GapDetector
from analysis.reference_engine import ReferenceEngine
from ingestion.local import LocalProjectSource
from inventory.generator import ManifestGenerator


def test_gap_detection(tmp_path):
    project = tmp_path / "project"
    project.mkdir()

    readme = project / "README.md"

    readme.write_text(
        """
        The trained model is located at
        models/model_v2.pkl.
        """
    )

    source = LocalProjectSource(project)

    manifest = ManifestGenerator(
        source
    ).generate()

    references = ReferenceEngine(
        project
    ).analyze(
        manifest.artifacts
    )

    gaps = GapDetector().detect(
        references
    )

    assert len(gaps) == 1

    gap = gaps[0]

    assert gap.gap_id == "GAP-000001"
    assert gap.referenced_path == "models/model_v2.pkl"
    assert gap.source_path == "README.md"
    assert gap.severity == "LOST"
    assert gap.confidence == 0.95