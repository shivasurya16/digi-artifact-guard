from __future__ import annotations

import io
import json
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path

import streamlit as st 

from ingestion.local import LocalProjectSource
from inventory.generator import ManifestGenerator

from analysis.integrity import find_empty_artifacts
from analysis.duplicates import find_duplicate_groups
from analysis.reference_engine import ReferenceEngine
from analysis.gaps import GapDetector

from core.heritage import HeritageScoreEngine

from backup.engine import ImportantArtifactBackup
from backup.integration import (
    build_existing_reference_counts,
)


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Digi Artifact Guard",
    page_icon="🛡️",
    layout="wide",
)


# ============================================================
# SESSION STATE
# ============================================================

if "analysis" not in st.session_state:
    st.session_state.analysis = None

if "workspace" not in st.session_state:
    st.session_state.workspace = None


# ============================================================
# HELPERS
# ============================================================


def serialize_object(obj):
    if hasattr(obj, "to_dict"):
        return obj.to_dict()

    if hasattr(obj, "__dict__"):
        return obj.__dict__

    return obj


def serialize_objects(items):
    return [
        serialize_object(item)
        for item in items
    ]


def safe_extract_zip(
    uploaded_file,
    destination: Path,
) -> Path:
    """
    Safely extract a ZIP archive.

    Prevents ZIP path traversal.
    """

    destination.mkdir(
        parents=True,
        exist_ok=True,
    )

    with zipfile.ZipFile(
        io.BytesIO(
            uploaded_file.getvalue()
        )
    ) as archive:

        destination_resolved = (
            destination.resolve()
        )

        for member in archive.infolist():

            member_path = (
                destination
                / member.filename
            ).resolve()

            if not str(
                member_path
            ).startswith(
                str(destination_resolved)
            ):

                raise ValueError(
                    "Unsafe ZIP archive detected."
                )

        archive.extractall(
            destination
        )

    # Handle ZIPs containing one top-level
    # directory.
    children = list(
        destination.iterdir()
    )

    if len(children) == 1 and children[0].is_dir():

        return children[0]

    return destination


def save_uploaded_files(
    uploaded_files,
    destination: Path,
) -> Path:
    """
    Save multiple uploaded files while preserving
    their relative paths when Streamlit provides them.
    """

    destination.mkdir(
        parents=True,
        exist_ok=True,
    )

    for uploaded_file in uploaded_files:

        relative_name = getattr(
            uploaded_file,
            "name",
            "uploaded_file",
        )

        relative_path = Path(
            relative_name
        )

        # Never allow an uploaded filename to escape
        # the temporary workspace.
        relative_path = Path(
            *[
                part
                for part in relative_path.parts
                if part not in ("", ".", "..")
            ]
        )

        if not relative_path.parts:
            continue

        target = (
            destination
            / relative_path
        )

        target.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with target.open(
            "wb"
        ) as file:

            file.write(
                uploaded_file.getbuffer()
            )

    return destination


def find_project_root(
    workspace: Path,
) -> Path:
    """
    Detect a project root when an uploaded archive
    contains a single project directory.
    """

    children = list(
        workspace.iterdir()
    )

    if len(children) == 1:

        only_child = children[0]

        if only_child.is_dir():

            return only_child

    return workspace


def clone_github_repository(
    repository_url: str,
    destination: Path,
) -> Path:
    """
    Clone a GitHub repository into a temporary workspace.

    Uses the local git executable.
    """

    repository_url = (
        repository_url
        .strip()
    )

    if not repository_url:

        raise ValueError(
            "GitHub repository URL is required."
        )

    if not (
        repository_url.startswith(
            "https://github.com/"
        )
        or repository_url.startswith(
            "http://github.com/"
        )
        or repository_url.startswith(
            "git@github.com:"
        )
    ):

        raise ValueError(
            "Only GitHub repository URLs are supported."
        )

    destination.mkdir(
        parents=True,
        exist_ok=True,
    )

    command = [
        "git",
        "clone",
        "--depth",
        "1",
        repository_url,
        str(destination),
    ]

    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=300,
    )

    if completed.returncode != 0:

        raise RuntimeError(
            "GitHub repository could not be cloned.\n\n"
            + completed.stderr
        )

    return destination


def run_analysis(
    project_path: Path,
    output_dir: Path,
):
    """
    Run the complete Digi Artifact Guard analysis
    against a real project workspace.
    """

    source = LocalProjectSource(
        project_path
    )

    manifest = (
        ManifestGenerator(
            source
        ).generate()
    )

    artifacts = manifest.artifacts

    # --------------------------------------------------------
    # INTEGRITY
    # --------------------------------------------------------

    empty_artifacts = (
        find_empty_artifacts(
            artifacts
        )
    )

    duplicate_groups = (
        find_duplicate_groups(
            artifacts
        )
    )

    # --------------------------------------------------------
    # REFERENCES
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # GAPS
    # --------------------------------------------------------

    gap_detector = GapDetector()

    gaps = (
        gap_detector.detect(
            references
        )
    )

    # --------------------------------------------------------
    # RECOVERY
    # --------------------------------------------------------

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

            except Exception:
                continue

    except ImportError:

        restoration_plans = []

    # --------------------------------------------------------
    # HERITAGE SCORE
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # IMPORTANT ARTIFACT BACKUP
    # --------------------------------------------------------

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
            references=reference_counts
        )
    )

    return {
        "project_path":
            project_path,

        "manifest":
            manifest,

        "artifacts":
            artifacts,

        "empty":
            empty_artifacts,

        "duplicates":
            duplicate_groups,

        "references":
            references,

        "gaps":
            gaps,

        "plans":
            restoration_plans,

        "heritage":
            heritage,

        "backup":
            backup_manifest,

        "backup_directory":
            output_dir / "important",
    }


# ============================================================
# HEADER
# ============================================================

st.title(
    "🛡️ Digi Artifact Guard"
)

st.markdown(
    """
### Digital Artifact Preservation & Recovery

Analyze your **own files, folder, ZIP archive, or GitHub
repository**. Digi Artifact Guard identifies important
artifacts, missing references, integrity problems, recovery
possibilities, and generates a Heritage Score Card.
"""
)

st.divider()


# ============================================================
# INPUT METHOD
# ============================================================

st.header(
    "1. Choose Input"
)

input_method = st.radio(
    "How do you want to provide the project?",
    [
        "📁 Folder / Files",
        "📦 ZIP Archive",
        "🐙 GitHub Repository",
    ],
    horizontal=True,
)


# ============================================================
# INPUT
# ============================================================

uploaded_files = None
uploaded_zip = None
github_url = ""


if input_method == "📁 Folder / Files":

    st.subheader(
        "Upload project files"
    )

    uploaded_files = st.file_uploader(
        "Select one or more project files",
        accept_multiple_files=True,
        help=(
            "You can upload source code, configuration, "
            "models, documentation and other project artifacts."
        ),
    )

    st.caption(
        "For a complete folder, select all files from the "
        "project folder. Folder structure is preserved when "
        "the browser provides relative paths."
    )


elif input_method == "📦 ZIP Archive":

    st.subheader(
        "Upload project ZIP"
    )

    uploaded_zip = st.file_uploader(
        "Choose a .zip project archive",
        type=["zip"],
    )


else:

    st.subheader(
        "GitHub repository"
    )

    github_url = st.text_input(
        "GitHub repository URL",
        placeholder=(
            "https://github.com/username/repository"
        ),
    )

    st.caption(
        "Public repositories can be analyzed directly. "
        "Private repositories will require authentication "
        "in a future version."
    )


analyze_button = st.button(
    "🔍 Analyze Project",
    type="primary",
    use_container_width=True,
)


# ============================================================
# ANALYSIS TRIGGER
# ============================================================

if analyze_button:

    try:

        with st.spinner(
            "Preparing project..."
        ):

            temp_root = Path(
                tempfile.mkdtemp(
                    prefix="digi_artifact_guard_"
                )
            )

            project_workspace = (
                temp_root
                / "project"
            )

            output_workspace = (
                temp_root
                / "output"
            )

            # ------------------------------------------------
            # UPLOADED FILES
            # ------------------------------------------------

            if input_method == "📁 Folder / Files":

                if not uploaded_files:

                    st.error(
                        "Please upload at least one file."
                    )

                    shutil.rmtree(
                        temp_root,
                        ignore_errors=True,
                    )

                    st.stop()

                project_path = (
                    save_uploaded_files(
                        uploaded_files,
                        project_workspace,
                    )
                )

            # ------------------------------------------------
            # ZIP
            # ------------------------------------------------

            elif input_method == "📦 ZIP Archive":

                if uploaded_zip is None:

                    st.error(
                        "Please upload a ZIP archive."
                    )

                    shutil.rmtree(
                        temp_root,
                        ignore_errors=True,
                    )

                    st.stop()

                project_path = (
                    safe_extract_zip(
                        uploaded_zip,
                        project_workspace,
                    )
                )

                project_path = (
                    find_project_root(
                        project_path
                    )
                )

            # ------------------------------------------------
            # GITHUB
            # ------------------------------------------------

            else:

                if not github_url.strip():

                    st.error(
                        "Please enter a GitHub repository URL."
                    )

                    shutil.rmtree(
                        temp_root,
                        ignore_errors=True,
                    )

                    st.stop()

                github_workspace = (
                    temp_root
                    / "github"
                )

                project_path = (
                    clone_github_repository(
                        github_url,
                        github_workspace,
                    )
                )

            # ------------------------------------------------
            # ANALYSIS
            # ------------------------------------------------

            with st.spinner(
                "Analyzing artifacts, references, "
                "gaps, heritage and backup priorities..."
            ):

                analysis = run_analysis(
                    project_path,
                    output_workspace,
                )

            st.session_state.analysis = (
                analysis
            )

            st.session_state.workspace = (
                temp_root
            )

        st.success(
            "Analysis complete."
        )

    except Exception as exc:

        st.error(
            "Analysis failed."
        )

        st.exception(
            exc
        )


# ============================================================
# NO ANALYSIS
# ============================================================

analysis = (
    st.session_state.get(
        "analysis"
    )
)

if analysis is None:

    st.info(
        "Provide a project using one of the input methods "
        "above and click Analyze Project."
    )

    st.stop()


# ============================================================
# DATA
# ============================================================

artifacts = analysis[
    "artifacts"
]

empty_artifacts = analysis[
    "empty"
]

duplicate_groups = analysis[
    "duplicates"
]

references = analysis[
    "references"
]

gaps = analysis[
    "gaps"
]

plans = analysis[
    "plans"
]

heritage = analysis[
    "heritage"
]

backup_manifest = analysis[
    "backup"
]

backup_directory = analysis[
    "backup_directory"
]


# ============================================================
# HERITAGE SCORE CARD
# ============================================================

st.header(
    "🏛️ Heritage Score Card"
)

score_col, details_col = st.columns(
    [1, 2]
)

with score_col:

    st.metric(
        "Heritage Score",
        f"{heritage.score}/100",
    )

    st.metric(
        "Confidence",
        f"{heritage.confidence}%",
    )


with details_col:

    st.write(
        f"**Preservation:** "
        f"{heritage.preservation}"
    )

    st.write(
        f"**Integrity:** "
        f"{heritage.integrity}"
    )

    st.write(
        f"**Completeness:** "
        f"{heritage.completeness}"
    )

    st.write(
        f"**Evidence Coverage:** "
        f"{heritage.evidence_coverage}"
    )

    st.write(
        f"**Reconstruction:** "
        f"{heritage.reconstruction}"
    )


# ============================================================
# SCORE BREAKDOWN
# ============================================================

with st.expander(
    "📊 Score Breakdown"
):

    breakdown = heritage.breakdown

    breakdown_rows = [
        {
            "Dimension":
                "Preservation",
            "Points":
                breakdown.get(
                    "preservation",
                    0,
                ),
        },
        {
            "Dimension":
                "Integrity",
            "Points":
                breakdown.get(
                    "integrity",
                    0,
                ),
        },
        {
            "Dimension":
                "Completeness",
            "Points":
                breakdown.get(
                    "completeness",
                    0,
                ),
        },
        {
            "Dimension":
                "Evidence",
            "Points":
                breakdown.get(
                    "evidence",
                    0,
                ),
        },
        {
            "Dimension":
                "Reconstruction",
            "Points":
                breakdown.get(
                    "reconstruction",
                    0,
                ),
        },
    ]

    st.dataframe(
        breakdown_rows,
        use_container_width=True,
        hide_index=True,
    )


st.divider()


# ============================================================
# PROJECT METRICS
# ============================================================

st.header(
    "2. Project Overview"
)

col1, col2, col3, col4, col5, col6 = (
    st.columns(6)
)

with col1:

    st.metric(
        "Artifacts",
        len(artifacts),
    )

with col2:

    st.metric(
        "Empty",
        len(empty_artifacts),
    )

with col3:

    st.metric(
        "Duplicates",
        len(duplicate_groups),
    )

with col4:

    st.metric(
        "References",
        len(references),
    )

with col5:

    st.metric(
        "Missing",
        len(gaps),
    )

with col6:

    st.metric(
        "Backed Up",
        backup_manifest.get(
            "artifact_count",
            0,
        ),
    )


# ============================================================
# IMPORTANT BACKUP
# ============================================================

st.header(
    "🛡️ Important Artifact Backup"
)

backup_col1, backup_col2 = st.columns(2)

with backup_col1:

    st.metric(
        "Important Artifacts",
        backup_manifest.get(
            "artifact_count",
            0,
        ),
    )

with backup_col2:

    st.metric(
        "Excluded / Low Importance",
        backup_manifest.get(
            "excluded_count",
            0,
        ),
    )

st.caption(
    "The backup intentionally prioritizes important "
    "artifacts and avoids low-value/disposable files."
)

backup_json = json.dumps(
    backup_manifest,
    indent=2,
    ensure_ascii=False,
    default=str,
)

st.download_button(
    "⬇️ Download Backup Manifest",
    data=backup_json,
    file_name="backup_manifest.json",
    mime="application/json",
)


# ============================================================
# INVENTORY
# ============================================================

with st.expander(
    "📦 Artifact Inventory"
):

    inventory = []

    for artifact in artifacts:

        inventory.append(
            {
                "ID":
                    getattr(
                        artifact,
                        "id",
                        "",
                    ),

                "Path":
                    getattr(
                        artifact,
                        "path",
                        "",
                    ),

                "Type":
                    getattr(
                        artifact,
                        "artifact_type",
                        "",
                    ),

                "Extension":
                    getattr(
                        artifact,
                        "extension",
                        "",
                    ),

                "Size":
                    getattr(
                        artifact,
                        "size",
                        0,
                    ),
            }
        )

    st.dataframe(
        inventory,
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# INTEGRITY
# ============================================================

with st.expander(
    "🔐 Integrity Analysis"
):

    st.write(
        f"Duplicate groups: "
        f"{len(duplicate_groups)}"
    )

    st.write(
        f"Empty artifacts: "
        f"{len(empty_artifacts)}"
    )


# ============================================================
# REFERENCES
# ============================================================

with st.expander(
    "🔗 Reference Analysis"
):

    if not references:

        st.info(
            "No references detected."
        )

    else:

        reference_rows = []

        for reference in references:

            reference_rows.append(
                {
                    "Source":
                        getattr(
                            reference,
                            "source_path",
                            "",
                        ),

                    "Reference":
                        getattr(
                            reference,
                            "reference",
                            "",
                        ),

                    "Type":
                        getattr(
                            reference,
                            "reference_type",
                            "",
                        ),

                    "Target Exists":
                        getattr(
                            reference,
                            "target_exists",
                            False,
                        ),
                }
            )

        st.dataframe(
            reference_rows,
            use_container_width=True,
            hide_index=True,
        )


# ============================================================
# GAPS
# ============================================================

st.header(
    "3. Detected Gaps"
)

if not gaps:

    st.success(
        "No missing artifacts detected."
    )

else:

    for gap in gaps:

        st.error(
            f"{gap.gap_id} — "
            f"{gap.referenced_path}"
        )

        st.write(
            gap.reason
        )

        st.caption(
            f"Source: {gap.source_path}"
        )


# ============================================================
# RECOVERY
# ============================================================

st.header(
    "4. Recovery Intelligence"
)

if not plans:

    if gaps:

        st.warning(
            "Missing artifacts were detected, "
            "but no recovery plans are available."
        )

    else:

        st.info(
            "No recovery is required."
        )

else:

    for plan in plans:

        missing_path = getattr(
            plan,
            "missing_path",
            "Unknown",
        )

        status = getattr(
            plan,
            "status",
            "UNKNOWN",
        )

        confidence = getattr(
            plan,
            "confidence",
            0,
        )

        candidate = getattr(
            plan,
            "recommended_candidate",
            None,
        )

        st.subheader(
            missing_path
        )

        if status == "HIGH_CONFIDENCE":

            st.success(
                "HIGH CONFIDENCE RECOVERY"
            )

        elif status == "REVIEW_RECOMMENDED":

            st.warning(
                "MANUAL REVIEW RECOMMENDED"
            )

        elif status == "UNRECOVERABLE":

            st.error(
                "NO SUITABLE RECOVERY CANDIDATE"
            )

        else:

            st.info(
                f"Status: {status}"
            )

        if isinstance(
            confidence,
            (int, float),
        ):

            st.write(
                f"Confidence: "
                f"{confidence:.1%}"
            )

        if candidate:

            st.write(
                f"Recommended candidate: "
                f"`{candidate}`"
            )


# ============================================================
# SAFE RESTORATION
# ============================================================

st.header(
    "5. Safe Restoration"
)

high_confidence_plans = [
    plan
    for plan in plans
    if getattr(
        plan,
        "status",
        None,
    ) == "HIGH_CONFIDENCE"
]


if not high_confidence_plans:

    st.info(
        "There are currently no high-confidence "
        "artifacts eligible for automatic restoration."
    )

else:

    st.warning(
        """
        Restoration is performed into a separate recovery
        workspace. The submitted project is not modified.
        """
    )

    restore_button = st.button(
        "🛡️ Restore High-Confidence Artifacts"
    )

    if restore_button:

        recovery_root = (
            Path(
                tempfile.gettempdir()
            )
            / "digi_artifact_guard_recovery"
        )

        try:

            from restoration.executor import (
                RestorationExecutor,
            )

            executor = (
                RestorationExecutor(
                    recovery_root
                )
            )

            results = []

            for plan in high_confidence_plans:

                result = executor.restore(
                    plan,
                    analysis["project_path"],
                )

                results.append(
                    result
                )

            st.subheader(
                "Restoration Results"
            )

            for result in results:

                if (
                    result.status
                    == "RESTORED_VERIFIED"
                ):

                    st.success(
                        f"{result.gap_id}: "
                        f"RESTORED + VERIFIED"
                    )

                    st.write(
                        "Destination:",
                        result.destination_path,
                    )

                    st.write(
                        "SHA-256:"
                    )

                    st.code(
                        result.source_hash
                    )

                elif (
                    result.status
                    == "CORRUPTED"
                ):

                    st.error(
                        f"{result.gap_id}: "
                        "SHA-256 verification failed."
                    )

                else:

                    st.warning(
                        f"{result.gap_id}: "
                        f"{result.status}"
                    )

        except ImportError:

            st.error(
                "Restoration executor is "
                "not available yet."
            )

        except Exception as exc:

            st.error(
                "Restoration failed."
            )

            st.exception(
                exc
            )


# ============================================================
# HERITAGE JSON
# ============================================================

with st.expander(
    "📄 Heritage Card JSON"
):

    st.json(
        heritage.to_dict()
    )


# ============================================================
# FINAL STATUS
# ============================================================

st.divider()

st.success(
    "🛡️ DIGI ARTIFACT GUARD — ANALYSIS COMPLETE"
)