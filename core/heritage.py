from dataclasses import dataclass, field


@dataclass
class HeritageScore:
    """
    Overall preservation and recoverability assessment
    for a digital artifact collection.
    """

    score: int
    confidence: int

    preservation: str
    integrity: str
    completeness: str
    evidence_coverage: str
    reconstruction: str

    artifact_count: int
    missing_count: int
    duplicate_group_count: int
    reference_count: int
    recoverable_count: int

    breakdown: dict = field(
        default_factory=dict
    )

    def to_dict(self) -> dict:
        return {
            "heritage_score": self.score,
            "confidence": self.confidence,

            "preservation": self.preservation,
            "integrity": self.integrity,
            "completeness": self.completeness,
            "evidence_coverage": self.evidence_coverage,
            "reconstruction": self.reconstruction,

            "artifact_count": self.artifact_count,
            "missing_count": self.missing_count,
            "duplicate_group_count":
                self.duplicate_group_count,
            "reference_count":
                self.reference_count,
            "recoverable_count":
                self.recoverable_count,

            "breakdown": self.breakdown,
        }


class HeritageScoreEngine:
    """
    Calculates a deterministic Heritage Score from
    Digi Artifact Guard analysis results.
    """

    WEIGHTS = {
        "preservation": 25,
        "integrity": 20,
        "completeness": 25,
        "evidence": 15,
        "reconstruction": 15,
    }

    def calculate(
        self,
        artifacts,
        gaps,
        references,
        duplicate_groups,
        restoration_plans,
    ) -> HeritageScore:

        artifact_count = len(artifacts)
        missing_count = len(gaps)
        reference_count = len(references)
        duplicate_group_count = len(
            duplicate_groups
        )

        recoverable_count = sum(
            1
            for plan in restoration_plans
            if plan.status == "HIGH_CONFIDENCE"
        )

        # --------------------------------------------------
        # EMPTY PROJECT
        # --------------------------------------------------

        if artifact_count == 0:

            return HeritageScore(
                score=0,
                confidence=0,

                preservation="LOW",
                integrity="LOW",
                completeness="LOW",
                evidence_coverage="LOW",
                reconstruction="NONE",

                artifact_count=0,
                missing_count=missing_count,
                duplicate_group_count=
                    duplicate_group_count,
                reference_count=reference_count,
                recoverable_count=recoverable_count,

                breakdown={
                    "preservation": 0,
                    "integrity": 0,
                    "completeness": 0,
                    "evidence": 0,
                    "reconstruction": 0,
                },
            )

        # --------------------------------------------------
        # PRESERVATION
        # --------------------------------------------------

        empty_count = sum(
            1
            for artifact in artifacts
            if getattr(
                artifact,
                "size",
                0,
            ) == 0
        )

        empty_ratio = (
            empty_count / artifact_count
        )

        preservation_score = max(
            0.0,
            1.0 - empty_ratio,
        )

        # --------------------------------------------------
        # INTEGRITY
        # --------------------------------------------------

        duplicate_penalty = min(
            duplicate_group_count
            / artifact_count,
            0.5,
        )

        integrity_score = max(
            0.0,
            1.0 - duplicate_penalty,
        )

        # --------------------------------------------------
        # COMPLETENESS
        # --------------------------------------------------

        missing_ratio = min(
            missing_count
            / max(artifact_count, 1),
            1.0,
        )

        completeness_score = (
            1.0 - missing_ratio
        )

        # --------------------------------------------------
        # EVIDENCE COVERAGE
        # --------------------------------------------------

        referenced_sources = len(
            {
                getattr(
                    reference,
                    "source_artifact_id",
                    None,
                )
                for reference in references
                if getattr(
                    reference,
                    "source_artifact_id",
                    None,
                )
            }
        )

        if not references:

            evidence_score = 0.5

        else:

            evidence_score = min(
                referenced_sources
                / artifact_count,
                1.0,
            )

        # --------------------------------------------------
        # RECONSTRUCTION
        # --------------------------------------------------

        if missing_count == 0:

            reconstruction_score = 1.0

        else:

            reconstruction_score = min(
                recoverable_count
                / missing_count,
                1.0,
            )

        # --------------------------------------------------
        # WEIGHTED SCORE
        # --------------------------------------------------

        weighted_score = (
            preservation_score
            * self.WEIGHTS["preservation"]
            +
            integrity_score
            * self.WEIGHTS["integrity"]
            +
            completeness_score
            * self.WEIGHTS["completeness"]
            +
            evidence_score
            * self.WEIGHTS["evidence"]
            +
            reconstruction_score
            * self.WEIGHTS["reconstruction"]
        )

        score = round(
            weighted_score
        )

        # --------------------------------------------------
        # CONFIDENCE
        # --------------------------------------------------

        confidence = self._confidence(
            artifact_count,
            reference_count,
            missing_count,
        )

        # --------------------------------------------------
        # QUALITATIVE STATUS
        # --------------------------------------------------

        preservation = self._level(
            preservation_score
        )

        integrity = self._level(
            integrity_score
        )

        completeness = self._level(
            completeness_score
        )

        evidence_coverage = self._level(
            evidence_score
        )

        reconstruction = (
            self._reconstruction_level(
                missing_count,
                recoverable_count,
            )
        )

        return HeritageScore(
            score=score,
            confidence=confidence,

            preservation=preservation,
            integrity=integrity,
            completeness=completeness,
            evidence_coverage=
                evidence_coverage,
            reconstruction=
                reconstruction,

            artifact_count=
                artifact_count,
            missing_count=
                missing_count,
            duplicate_group_count=
                duplicate_group_count,
            reference_count=
                reference_count,
            recoverable_count=
                recoverable_count,

            breakdown={
                "preservation": round(
                    preservation_score
                    * self.WEIGHTS[
                        "preservation"
                    ],
                    2,
                ),

                "integrity": round(
                    integrity_score
                    * self.WEIGHTS[
                        "integrity"
                    ],
                    2,
                ),

                "completeness": round(
                    completeness_score
                    * self.WEIGHTS[
                        "completeness"
                    ],
                    2,
                ),

                "evidence": round(
                    evidence_score
                    * self.WEIGHTS[
                        "evidence"
                    ],
                    2,
                ),

                "reconstruction": round(
                    reconstruction_score
                    * self.WEIGHTS[
                        "reconstruction"
                    ],
                    2,
                ),
            },
        )

    def _level(
        self,
        value: float,
    ) -> str:

        if value >= 0.80:
            return "HIGH"

        if value >= 0.50:
            return "MEDIUM"

        return "LOW"

    def _reconstruction_level(
        self,
        missing_count: int,
        recoverable_count: int,
    ) -> str:

        if missing_count == 0:
            return "COMPLETE"

        if recoverable_count == 0:
            return "NONE"

        if recoverable_count >= missing_count:
            return "COMPLETE"

        return "PARTIAL"

    def _confidence(
        self,
        artifact_count: int,
        reference_count: int,
        missing_count: int,
    ) -> int:

        if artifact_count == 0:
            return 0

        confidence = 60

        if artifact_count >= 10:
            confidence += 15

        elif artifact_count >= 5:
            confidence += 10

        if reference_count > 0:
            confidence += 10

        if missing_count > 0:
            confidence += 5

        return min(
            confidence,
            95,
        )