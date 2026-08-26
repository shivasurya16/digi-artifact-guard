import json
import importlib
import tempfile
from pathlib import Path

# Load Streamlit dynamically so static analysis does not require the optional
# UI dependency to be installed while inspecting the project modules.
st = importlib.import_module("streamlit")

from ingestion.local import LocalProjectSource
from inventory.generator import ManifestGenerator

from analysis.integrity import (
    find_empty_artifacts,
)

from analysis.duplicates import (
    find_duplicate_groups,
)

from analysis.reference_engine import (
    ReferenceEngine,
)

from analysis.gaps import (
    GapDetector,
)

from core.heritage import (
    HeritageScoreEngine,
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
# HELPERS
# ============================================================

def serialize_object(obj):
    """
    Convert an application model into a displayable
    dictionary.
    """

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


def clean_user_path(value: str) -> str:
    """
    Accept paths with or without surrounding quotes.
    """

    return (
        value
        .strip()
        .strip('"')
        .strip("'")
    )


# ============================================================
# HEADER
# ============================================================

st.title(
    "🛡️ Digi Artifact Guard"
)

st.markdown(
    """
## Digital Artifact Preservation & Recovery

Analyze a user-selected project, detect missing artifacts,
evaluate integrity, reconstruct references, and calculate
a Heritage Score representing the preservation state.
"""
)

st.divider()


# ============================================================
# INPUT
# ============================================================

st.header(
    "1. Select Project"
)

project_path_text = st.text_input(
    "Local project/folder path",
    placeholder=r"D:\my_project",
    help=(
        "Enter any local project folder. "
        "Paths with or without quotation marks "
        "are supported."
    ),
)

analyze_button = st.button(
    "🔍 Analyze Project",
    type="primary",
)


# ============================================================
# ANALYSIS
# ============================================================

if analyze_button:

    cleaned_path = clean_user_path(
        project_path_text
    )

    if not cleaned_path:

        st.error(
            "Please enter a project folder path."
        )

        st.stop()

    project_path = (
        Path(cleaned_path)
        .expanduser()
        .resolve()
    )

    if not project_path.exists():

        st.error(
            f"Project path does not exist:\n"
            f"{project_path}"
        )

        st.stop()

    if not project_path.is_dir():

        st.error(
            "The selected path is not a folder."
        )

        st.stop()

    with st.spinner(
        "Analyzing project artifacts..."
    ):

        try:

            # ------------------------------------------------
            # INVENTORY
            # ------------------------------------------------

            source = LocalProjectSource(
                project_path
            )

            manifest = (
                ManifestGenerator(
                    source
                ).generate()
            )

            artifacts = (
                manifest.artifacts
            )

            # ------------------------------------------------
            # INTEGRITY
            # ------------------------------------------------

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

            # ------------------------------------------------
            # REFERENCES
            # ------------------------------------------------

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

            # ------------------------------------------------
            # GAPS
            # ------------------------------------------------

            gap_detector = GapDetector()

            gaps = (
                gap_detector.detect(
                    references
                )
            )

            # ------------------------------------------------
            # RECOVERY
            # ------------------------------------------------

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

                planner = (
                    RestorationPlanner()
                )

                for gap in gaps:

                    try:

                        candidates = (
                            recovery_engine.find_candidates(
                                gap.referenced_path,
                                artifacts,
                                project_path,
                            )
                        )

                        plan = (
                            planner.create_plan(
                                gap,
                                candidates,
                            )
                        )

                        restoration_plans.append(
                            plan
                        )

                    except Exception:
                        continue

            except ImportError:

                restoration_plans = []

            # ------------------------------------------------
            # HERITAGE SCORE
            # ------------------------------------------------

            heritage_engine = (
                HeritageScoreEngine()
            )

            heritage = (
                heritage_engine.calculate(
                    artifacts=artifacts,
                    gaps=gaps,
                    references=references,
                    duplicate_groups=
                        duplicate_groups,
                    restoration_plans=
                        restoration_plans,
                )
            )

            # ------------------------------------------------
            # SAVE STATE
            # ------------------------------------------------

            st.session_state.analysis = {

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
            }

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

            st.stop()


# ============================================================
# NO ANALYSIS YET
# ============================================================

analysis = st.session_state.get(
    "analysis"
)

if analysis is None:

    st.info(
        "Enter a project folder above and "
        "click Analyze Project."
    )

    st.stop()


# ============================================================
# DATA
# ============================================================

artifacts = (
    analysis["artifacts"]
)

empty_artifacts = (
    analysis["empty"]
)

duplicate_groups = (
    analysis["duplicates"]
)

references = (
    analysis["references"]
)

gaps = (
    analysis["gaps"]
)

plans = (
    analysis["plans"]
)

heritage = (
    analysis["heritage"]
)


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

col1, col2, col3, col4, col5 = (
    st.columns(5)
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
# RESTORATION
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
        workspace. The original project is not modified.
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
                        f"SHA-256 verification failed."
                    )

                else:

                    st.warning(
                        f"{result.gap_id}: "
                        f"{result.status}"
                    )

        except ImportError:

            st.error(
                "Restoration executor is not "
                "available yet."
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
    "DIGI ARTIFACT GUARD — ANALYSIS COMPLETE"
)