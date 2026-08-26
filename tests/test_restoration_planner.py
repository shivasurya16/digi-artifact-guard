from types import SimpleNamespace

from restoration.planner import (
    RestorationPlanner,
)


def gap():

    return SimpleNamespace(
        gap_id="GAP-000001",
        referenced_path="models/model_v2.pkl",
    )


def candidate(
    path,
    score,
):

    return SimpleNamespace(
        candidate_path=path,
        score=score,
        reasons=[
            "Same versioned artifact family"
        ],
        metadata={},
    )


def test_high_confidence_plan():

    planner = RestorationPlanner()

    plan = planner.create_plan(
        gap(),
        [
            candidate(
                "models/model_v3.pkl",
                0.91,
            )
        ],
    )

    assert plan.status == "HIGH_CONFIDENCE"

    assert (
        plan.recommended_candidate
        == "models/model_v3.pkl"
    )

    assert plan.confidence == 0.91


def test_review_plan():

    planner = RestorationPlanner()

    plan = planner.create_plan(
        gap(),
        [
            candidate(
                "models/model_v1.pkl",
                0.72,
            )
        ],
    )

    assert plan.status == "REVIEW_RECOMMENDED"


def test_unrecoverable_plan():

    planner = RestorationPlanner()

    plan = planner.create_plan(
        gap(),
        [],
    )

    assert plan.status == "UNRECOVERABLE"

    assert (
        plan.recommended_candidate
        is None
    )