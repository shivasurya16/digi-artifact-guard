from ingestion.local import LocalProjectSource
from inventory.generator import ManifestGenerator
from analysis.reference_engine import ReferenceEngine


def test_missing_reference_detection(tmp_path):
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

    engine = ReferenceEngine(project)

    references = engine.analyze(
        manifest.artifacts
    )

    assert len(references) == 1

    reference = references[0]

    assert reference.reference == "models/model_v2.pkl"
    assert reference.target_exists is False
    assert reference.target_artifact_id is None
    