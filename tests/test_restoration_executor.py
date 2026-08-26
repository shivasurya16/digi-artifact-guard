from pathlib import Path
from types import SimpleNamespace
from unittest import result

from restoration.executor import (
    RestorationExecutor,
)


def make_plan(
    candidate,
    status="HIGH_CONFIDENCE",
):

    return SimpleNamespace(
        gap_id="GAP-000001",
        missing_path="models/model_v2.pkl",
        status=status,
        recommended_candidate=candidate,
    )


def test_safe_restoration(tmp_path):

    project = tmp_path / "project"

    candidate = (
        project
        / "models"
        / "model_v3.pkl"
    )

    candidate.parent.mkdir(
        parents=True
    )

    candidate.write_bytes(
        b"MODEL DATA"
    )

    recovery = (
        tmp_path
        / "recovered"
    )

    executor = RestorationExecutor(
        recovery
    )

    plan = make_plan(
        "models/model_v3.pkl"
    )

    result = executor.restore(
        plan,
        project,
    )

    assert result.status == "RESTORED_VERIFIED"
    assert result.status == "RESTORED_VERIFIED"
    assert result.verified is True

    assert (
    result.source_hash
    == result.restored_hash
)

    restored = (
        recovery
        / "models"
        / "model_v2.pkl"
    )

    assert restored.exists()

    assert (
        restored.read_bytes()
        == b"MODEL DATA"
    )

    # Original survives unchanged.
    assert candidate.exists()


def test_low_confidence_requires_review(
    tmp_path,
):

    project = tmp_path / "project"

    candidate = (
        project
        / "model.pkl"
    )

    candidate.parent.mkdir(
        parents=True
    )

    candidate.write_text(
        "data"
    )

    recovery = (
        tmp_path
        / "recovered"
    )

    executor = RestorationExecutor(
        recovery
    )

    plan = make_plan(
        "model.pkl",
        status="REVIEW_RECOMMENDED",
    )

    result = executor.restore(
        plan,
        project,
    )

    assert (
        result.status
        == "REVIEW_REQUIRED"
    )

    assert not recovery.exists()


def test_missing_candidate_fails(
    tmp_path,
):

    project = tmp_path / "project"

    project.mkdir()

    recovery = (
        tmp_path
        / "recovered"
    )

    executor = RestorationExecutor(
        recovery
    )

    plan = make_plan(
        "models/missing.pkl"
    )

    result = executor.restore(
        plan,
        project,
    )

    assert result.status == "FAILED"