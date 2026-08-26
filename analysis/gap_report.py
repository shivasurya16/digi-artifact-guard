import json
from pathlib import Path

from core.findings import ArtifactGap


def save_gap_report(
    gaps: list[ArtifactGap],
    output_path: Path,
) -> None:
    """
    Save detected gaps as JSON.
    """

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    data = {
        "gap_count": len(gaps),
        "gaps": [
            {
                "gap_id": gap.gap_id,
                "referenced_path": gap.referenced_path,
                "source_artifact_id": (
                    gap.source_artifact_id
                ),
                "source_path": gap.source_path,
                "gap_type": gap.gap_type,
                "severity": gap.severity,
                "confidence": gap.confidence,
                "reason": gap.reason,
                "evidence": gap.evidence,
                "metadata": gap.metadata,
            }
            for gap in gaps
        ],
    }

    with output_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            data,
            file,
            indent=2,
            ensure_ascii=False,
        )