from __future__ import annotations

import argparse
import json
from pathlib import Path

from ingestion.local import LocalProjectSource
from inventory.generator import ManifestGenerator

from analysis.duplicates import find_duplicate_groups
from analysis.integrity import find_empty_artifacts
from analysis.reference_engine import ReferenceEngine
from analysis.gaps import GapDetector

from core.heritage import HeritageScoreEngine

from backup.engine import ImportantArtifactBackup
from backup.integration import (
    build_existing_reference_counts,
)


# ============================================================
# JSON HELPERS
# ============================================================


def write_json(
    path: Path,
    data,
) -> None:
    """
    Write JSON data to disk.
    """

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with path.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            data,
            file,
            indent=2,
            ensure_ascii=False,
            default=str,
        )


def serialize_objects(
    items,
) -> list:
    """
    Convert dataclass/model objects into
    JSON-compatible dictionaries where possible.
    """

    result = []

    for item in items:

        if hasattr(
            item,
            "to_dict",
        ):

            result.append(
                item.to_dict()
            )

        elif hasattr(
            item,
            "__dict__",
        ):

            result.append(
                item.__dict__
            )

        else:

            result.append(
                item
            )

    return result


# ============================================================
# MAIN
# ============================================================


def main():

    parser = argparse.ArgumentParser(
        description=(
            "Digi Artifact Guard - "
            "Digital Artifact Analysis, "
            "Preservation and Recovery"
        )
    )

    parser.add_argument(
        "project_path",
        help=(
            "Path to the project/folder "
            "to analyze"
        ),
    )

    parser.add_argument(
        "--output",
        default="artifact_guard_output",
        help=(
            "Output directory "
            "(default: artifact_guard_output)"
        ),
    )

    args = parser.parse_args()

    # ========================================================
    # INPUT PATH
    # ========================================================

    project_path = (
        Path(
            args.project_path
        )
        .expanduser()
        .resolve()
    )

    print()
    print("=" * 60)
    print("DIGI ARTIFACT GUARD")
    print("=" * 60)
    print()

    if not project_path.exists():

        raise FileNotFoundError(
            "Project path does not exist: "
            f"{project_path}"
        )

    if not project_path.is_dir():

        raise NotADirectoryError(
            "Project path is not a directory: "
            f"{project_path}"
        )

    output_dir = (
        Path(
            args.output
        )
        .expanduser()
        .resolve()
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    # ========================================================
    # SOURCE
    # ========================================================

    source = LocalProjectSource(
        project_path
    )

    print(
        f"Source : {source}"
    )

    print(
        f"Root   : {project_path}"
    )

    # ========================================================
    # INVENTORY
    # ========================================================

    manifest = (
        ManifestGenerator(
            source
        ).generate()
    )

    artifacts = manifest.artifacts

    total_size = sum(
        getattr(
            artifact,
            "size",
            0,
        )
        for artifact in artifacts
    )

    print()
    print("INVENTORY")
    print("-" * 60)

    print(
        f"Files discovered : "
        f"{len(artifacts)}"
    )

    print(
        f"Total size       : "
        f"{total_size} bytes"
    )

    # ========================================================
    # INTEGRITY
    # ========================================================

    duplicate_groups = (
        find_duplicate_groups(
            artifacts
        )
    )

    empty_artifacts = (
        find_empty_artifacts(
            artifacts
        )
    )

    duplicate_files = sum(
        len(group)
        for group in duplicate_groups
    )

    print()
    print("INTEGRITY")
    print("-" * 60)

    print(
        f"Duplicate groups : "
        f"{len(duplicate_groups)}"
    )

    print(
        f"Duplicate files  : "
        f"{duplicate_files}"
    )

    print(
        f"Empty artifacts  : "
        f"{len(empty_artifacts)}"
    )

    # ========================================================
    # REFERENCE ANALYSIS
    # ========================================================

    reference_engine = (
        ReferenceEngine(
            project_path
        )
    )

    references = (
        reference_engine.analyze(
            artifacts
        )
    )

    print()
    print("REFERENCE ANALYSIS")
    print("-" * 60)

    print(
        f"References found : "
        f"{len(references)}"
    )

    # ========================================================
    # GAP ANALYSIS
    # ========================================================

    gap_detector = GapDetector()

    gaps = (
        gap_detector.detect(
            references
        )
    )

    print()
    print("GAP ANALYSIS")
    print("-" * 60)

    print(
        f"Missing artifacts: "
        f"{len(gaps)}"
    )

    # ========================================================
    # RECOVERY PLANS
    # ========================================================

    restoration_plans = []

    try:

        from recovery.candidates import (
            RecoveryCandidateEngine,
        )

        from restoration.planner import (
            RestorationPlanner,
        )

        recovery_engine = (
            RecoveryCandidateEngine()
        )

        planner = RestorationPlanner()

        for gap in gaps:

            try:

                candidates = (
                    recovery_engine.find_candidates(
                        gap.referenced_path,
                        artifacts,
                        project_path,
                    )
                )

                plan = planner.create_plan(
                    gap,
                    candidates,
                )

                restoration_plans.append(
                    plan
                )

            except Exception as exc:

                print(
                    "Warning: recovery planning "
                    f"failed for "
                    f"{gap.referenced_path}: "
                    f"{exc}"
                )

    except ImportError:

        # Recovery planning is optional.
        restoration_plans = []

    # ========================================================
    # HERITAGE SCORE
    # ========================================================

    heritage_engine = (
        HeritageScoreEngine()
    )

    heritage = (
        heritage_engine.calculate(
            artifacts=artifacts,
            gaps=gaps,
            references=references,
            duplicate_groups=duplicate_groups,
            restoration_plans=restoration_plans,
        )
    )

    print()
    print("HERITAGE SCORE CARD")
    print("-" * 60)

    print(
        f"Heritage Score   : "
        f"{heritage.score}/100"
    )

    print(
        f"Confidence       : "
        f"{heritage.confidence}%"
    )

    print(
        f"Preservation     : "
        f"{heritage.preservation}"
    )

    print(
        f"Integrity        : "
        f"{heritage.integrity}"
    )

    print(
        f"Completeness     : "
        f"{heritage.completeness}"
    )

    print(
        f"Evidence Coverage: "
        f"{heritage.evidence_coverage}"
    )

    print(
        f"Reconstruction   : "
        f"{heritage.reconstruction}"
    )

    # ========================================================
    # IMPORTANT ARTIFACT BACKUP
    # ========================================================

    print()
    print("IMPORTANT ARTIFACT BACKUP")
    print("-" * 60)

    # Count how many surviving artifacts reference
    # existing artifacts.
    reference_counts = (
        build_existing_reference_counts(
            references
        )
    )

    backup_engine = ImportantArtifactBackup(
        project_root=project_path,
        output_root=output_dir,
    )

    backup_manifest = (
        backup_engine.create_backup(
            references=reference_counts,
        )
    )

    backup_manifest_path = (
        output_dir
        / "backup_manifest.json"
    )

    backup_directory = (
        output_dir
        / "important"
    )

    print(
        f"Artifacts backed up : "
        f"{backup_manifest['artifact_count']}"
    )

    print(
        f"Artifacts excluded  : "
        f"{backup_manifest['excluded_count']}"
    )

    print(
        f"Backup manifest     : "
        f"{backup_manifest_path}"
    )

    print(
        f"Backup directory    : "
        f"{backup_directory}"
    )

    # ========================================================
    # OUTPUT PATHS
    # ========================================================

    manifest_path = (
        output_dir
        / "manifest.json"
    )

    integrity_path = (
        output_dir
        / "integrity.json"
    )

    references_path = (
        output_dir
        / "references.json"
    )

    gaps_path = (
        output_dir
        / "gaps.json"
    )

    heritage_path = (
        output_dir
        / "heritage_card.json"
    )

    restoration_plans_path = (
        output_dir
        / "restoration_plans.json"
    )

    # ========================================================
    # MANIFEST OUTPUT
    # ========================================================

    write_json(
        manifest_path,
        {
            "project_root":
                manifest.project_root,

            "generated_at":
                manifest.generated_at,

            "artifact_count":
                len(artifacts),

            "artifacts":
                serialize_objects(
                    artifacts
                ),
        },
    )

    # ========================================================
    # INTEGRITY OUTPUT
    # ========================================================

    write_json(
        integrity_path,
        {
            "duplicate_group_count":
                len(duplicate_groups),

            "duplicate_file_count":
                duplicate_files,

            "empty_artifact_count":
                len(empty_artifacts),

            "duplicate_groups":
                serialize_objects(
                    duplicate_groups
                ),

            "empty_artifacts":
                serialize_objects(
                    empty_artifacts
                ),
        },
    )

    # ========================================================
    # REFERENCES OUTPUT
    # ========================================================

    write_json(
        references_path,
        {
            "reference_count":
                len(references),

            "references":
                serialize_objects(
                    references
                ),
        },
    )

    # ========================================================
    # GAPS OUTPUT
    # ========================================================

    write_json(
        gaps_path,
        {
            "gap_count":
                len(gaps),

            "gaps":
                serialize_objects(
                    gaps
                ),
        },
    )

    # ========================================================
    # RESTORATION PLANS OUTPUT
    # ========================================================

    write_json(
        restoration_plans_path,
        {
            "plan_count":
                len(restoration_plans),

            "plans":
                serialize_objects(
                    restoration_plans
                ),
        },
    )

    # ========================================================
    # HERITAGE CARD OUTPUT
    # ========================================================

    write_json(
        heritage_path,
        heritage.to_dict(),
    )

    # ========================================================
    # FINAL OUTPUT
    # ========================================================

    print()
    print("OUTPUT")
    print("-" * 60)

    print(
        f"Manifest         : "
        f"{manifest_path}"
    )

    print(
        f"Integrity        : "
        f"{integrity_path}"
    )

    print(
        f"References       : "
        f"{references_path}"
    )

    print(
        f"Gaps             : "
        f"{gaps_path}"
    )

    print(
        f"Heritage Card    : "
        f"{heritage_path}"
    )

    print(
        f"Restoration Plans: "
        f"{restoration_plans_path}"
    )

    print(
        f"Backup Manifest  : "
        f"{backup_manifest_path}"
    )

    print(
        f"Important Backup : "
        f"{backup_directory}"
    )

    print()
    print(
        "Status : ANALYSIS COMPLETE"
    )
    print()


if __name__ == "__main__":
    main()