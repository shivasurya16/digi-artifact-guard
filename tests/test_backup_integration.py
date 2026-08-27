from backup.integration import (
    build_existing_reference_counts,
)


def test_existing_reference_counts():
    class Reference:
        def __init__(
            self,
            reference,
            target_exists,
        ):
            self.reference = reference
            self.target_exists = target_exists

    references = [
        Reference(
            "models/model.pkl",
            True,
        ),
        Reference(
            "models/model.pkl",
            True,
        ),
        Reference(
            "config/settings.json",
            True,
        ),
        Reference(
            "models/missing.pkl",
            False,
        ),
    ]

    counts = build_existing_reference_counts(
        references
    )

    assert counts == {
        "models/model.pkl": 2,
        "config/settings.json": 1,
    }


def test_missing_references_are_not_counted():
    class Reference:
        def __init__(
            self,
            reference,
            target_exists,
        ):
            self.reference = reference
            self.target_exists = target_exists

    references = [
        Reference(
            "models/missing.pkl",
            False,
        )
    ]

    counts = build_existing_reference_counts(
        references
    )

    assert counts == {}