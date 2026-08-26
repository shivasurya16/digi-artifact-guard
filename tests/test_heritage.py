from types import SimpleNamespace

from core.heritage import (
    HeritageScoreEngine,
)


def artifact(
    path,
    size=100,
):

    return SimpleNamespace(
        id=path,
        path=path,
        size=size,
        artifact_type="source_code",
    )


def gap(
    path,
):

    return SimpleNamespace(
        gap_id="GAP-000001",
        referenced_path=path,
    )


def reference():

    return SimpleNamespace(
        source_artifact_id="artifact_000001",
        source_path="README.md",
        reference="models/model.pkl",
        target_exists=False,
    )


def plan(
    status,
):

    return SimpleNamespace(
        status=status
    )


def test_healthy_project_gets_high_score():

    engine = HeritageScoreEngine()

    result = engine.calculate(
        artifacts=[
            artifact("README.md"),
            artifact("src/main.py"),
            artifact("config.json"),
        ],
        gaps=[],
        references=[
            reference()
        ],
        duplicate_groups=[],
        restoration_plans=[],
    )

    assert result.score >= 70
    assert result.preservation == "HIGH"
    assert result.completeness == "HIGH"
    assert result.reconstruction == "COMPLETE"


def test_missing_artifact_reduces_completeness():

    engine = HeritageScoreEngine()

    result = engine.calculate(
        artifacts=[
            artifact("README.md"),
            artifact("src/main.py"),
        ],
        gaps=[
            gap("models/model.pkl")
        ],
        references=[
            reference()
        ],
        duplicate_groups=[],
        restoration_plans=[
            plan("UNRECOVERABLE")
        ],
    )

    assert result.missing_count == 1
    assert result.completeness == "MEDIUM"
    assert result.reconstruction == "NONE"


def test_recoverable_gap_is_partial_or_complete():

    engine = HeritageScoreEngine()

    result = engine.calculate(
        artifacts=[
            artifact("README.md"),
            artifact("model_v1.pkl"),
        ],
        gaps=[
            gap("model_v2.pkl")
        ],
        references=[
            reference()
        ],
        duplicate_groups=[],
        restoration_plans=[
            plan("HIGH_CONFIDENCE")
        ],
    )

    assert result.recoverable_count == 1
    assert result.reconstruction == "COMPLETE"


def test_empty_project():

    engine = HeritageScoreEngine()

    result = engine.calculate(
        artifacts=[],
        gaps=[],
        references=[],
        duplicate_groups=[],
        restoration_plans=[],
    )

    assert result.score == 0
    assert result.confidence == 0