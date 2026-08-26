from types import SimpleNamespace

from recovery.candidates import (
    RecoveryCandidateEngine,
)


def artifact(
    path,
    artifact_id="artifact",
    size=100,
):

    return SimpleNamespace(
        id=artifact_id,
        path=path,
        extension="".join(
            __import__("os").path.splitext(path)[1:]
        ),
        size=size,
    )


def test_versioned_model_candidate():

    engine = RecoveryCandidateEngine()

    artifacts = [
        artifact(
            "models/model_v1.pkl",
            "artifact_001",
        ),
        artifact(
            "models/model_v3.pkl",
            "artifact_002",
        ),
        artifact(
            "src/main.py",
            "artifact_003",
        ),
    ]

    candidates = engine.find_candidates(
        "models/model_v2.pkl",
        artifacts,
    )

    assert len(candidates) == 2

    assert (
        candidates[0].candidate_path
        in {
            "models/model_v1.pkl",
            "models/model_v3.pkl",
        }
    )


def test_same_filename_is_strong_candidate():

    engine = RecoveryCandidateEngine()

    artifacts = [
        artifact(
            "backup/model_v2.pkl",
            "artifact_001",
        ),
        artifact(
            "models/model_v1.pkl",
            "artifact_002",
        ),
    ]

    candidates = engine.find_candidates(
        "models/model_v2.pkl",
        artifacts,
    )

    assert len(candidates) == 2

    assert (
        candidates[0].candidate_path
        == "backup/model_v2.pkl"
    )

    assert (
        candidates[0].score
        >= candidates[1].score
    )