from dataclasses import dataclass, field


@dataclass
class RestorationPlan:
    gap_id: str
    missing_path: str
    status: str
    recommended_candidate: str | None
    confidence: float
    candidates: list[dict] = field(
        default_factory=list
    )
    reasons: list[str] = field(
        default_factory=list
    )


class RestorationPlanner:
    """
    Converts recovery candidates into a safe
    restoration recommendation.

    This planner NEVER modifies the project.
    """

    HIGH_CONFIDENCE = 0.85
    MEDIUM_CONFIDENCE = 0.65

    def create_plan(
        self,
        gap,
        candidates,
    ) -> RestorationPlan:

        candidate_data = []

        for candidate in candidates:

            candidate_data.append(
                {
                    "path":
                        candidate.candidate_path,

                    "score":
                        candidate.score,

                    "reasons":
                        candidate.reasons,

                    "metadata":
                        candidate.metadata,
                }
            )

        if not candidates:

            return RestorationPlan(
                gap_id=gap.gap_id,
                missing_path=gap.referenced_path,
                status="UNRECOVERABLE",
                recommended_candidate=None,
                confidence=0.0,
                candidates=[],
                reasons=[
                    "No surviving recovery candidates "
                    "were found."
                ],
            )

        best = candidates[0]

        confidence = best.score

        if confidence >= self.HIGH_CONFIDENCE:

            status = "HIGH_CONFIDENCE"

        elif confidence >= self.MEDIUM_CONFIDENCE:

            status = "REVIEW_RECOMMENDED"

        else:

            status = "LOW_CONFIDENCE"

        reasons = list(
            best.reasons
        )

        if status != "HIGH_CONFIDENCE":

            reasons.append(
                "Automatic restoration is not "
                "recommended."
            )

        return RestorationPlan(
            gap_id=gap.gap_id,
            missing_path=gap.referenced_path,
            status=status,
            recommended_candidate=(
                best.candidate_path
            ),
            confidence=confidence,
            candidates=candidate_data,
            reasons=reasons,
        )