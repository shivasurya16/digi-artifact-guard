from core.findings import ArtifactGap
from core.relationships import ArtifactReference


class GapDetector:
    """
    Converts missing artifact references into structured gaps.
    """

    def detect(
        self,
        references: list[ArtifactReference],
    ) -> list[ArtifactGap]:

        gaps: list[ArtifactGap] = []

        gap_number = 1

        for reference in references:

            if reference.target_exists:
                continue

            gap = ArtifactGap(
                gap_id=f"GAP-{gap_number:06d}",
                referenced_path=reference.reference,
                source_artifact_id=(
                    reference.source_artifact_id
                ),
                source_path=reference.source_path,
                gap_type="missing_artifact",
                severity="LOST",
                confidence=0.95,
                reason=(
                    "Artifact is explicitly referenced by "
                    "a surviving project artifact, but the "
                    "referenced target is absent."
                ),
                evidence=[
                    (
                        f"Referenced by "
                        f"{reference.source_path}"
                    ),
                ],
                metadata={
                    "reference_type": (
                        reference.reference_type
                    ),
                },
            )

            gaps.append(gap)

            gap_number += 1

        return gaps