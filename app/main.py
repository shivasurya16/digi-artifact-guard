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


def write_json(path: Path, data) -> None:
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


def serialize_objects(items) -> list:
    """
    Convert dataclass/model objects into JSON-compatible
    dictionaries where possible.
    """

    result = []

    for item in items:

        if hasattr(item, "to_dict"):
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
            result.append(item)

    return result


def main():

    parser = argparse.ArgumentParser(
        description=(
            "Digi Artifact Guard - "
            "Digital Artifact Analysis and Recovery"
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

    # ---------------------------------------------------------
    # INPUT PATH
    # ---------------------------------------------------------

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
            f"Project path does not exist: "
            f"{project_path}"
        )

    if not project_path.is_dir():

        raise NotADirectoryError(
            f"Project path is not a directory: "
            f"{project_path}"
        )

    output_dir = (
        Path(args.output)
        .expanduser()
        .resolve()
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    # ---------------------------------------------------------
    # SOURCE
    # ---------------------------------------------------------

    source = LocalProjectSource(
        project_path
    )

    print(
        f"Source : {source}"
    )

    print(
        f"Root   : {project_path}"
    )

    # ---------------------------------------------------------
    # INVENTORY
    # ---------------------------------------------------------

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

    # ---------------------------------------------------------
    # INTEGRITY
    # ---------------------------------------------------------

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

    # ---------------------------------------------------------
    # REFERENCE ANALYSIS
    # ---------------------------------------------------------

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

    # ---------------------------------------------------------
    # GAP ANALYSIS
    # ---------------------------------------------------------

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

    # ---------------------------------------------------------
    # RECOVERY PLANS
    #
    # The project can contain recovery modules with different
    # APIs. Keep this section defensive so analysis can still
    # complete even when no recovery planner is installed.
    # ---------------------------------------------------------

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
                    f"Warning: recovery planning "
                    f"failed for {gap.referenced_path}: "
                    f"{exc}"
                )

    except ImportError:

        # Recovery planning is optional at this stage.
        restoration_plans = []

    # ---------------------------------------------------------
    # HERITAGE SCORE
    # ---------------------------------------------------------

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

    # ---------------------------------------------------------
    # OUTPUT
    # ---------------------------------------------------------

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

    write_json(
        heritage_path,
        heritage.to_dict(),
    )

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

    print()
    print(
        "Status : ANALYSIS COMPLETE"
    )
    print()


if __name__ == "__main__":
    main()