from pathlib import Path

from analysis.references import ReferenceExtractor
from analysis.python_references import PythonReferenceExtractor


class ReferenceEngine:

    def __init__(self, project_root):

        self.project_root = Path(
            project_root
        )

        self.extractors = [
            ReferenceExtractor(),
            PythonReferenceExtractor(),
        ]

    def analyze(self, artifacts):

        references = []

        for artifact in artifacts:

            absolute_path = (
                self.project_root
                / artifact.path
            )

            for extractor in self.extractors:

                extracted = extractor.extract(
                    artifact,
                    absolute_path,
                    artifacts,
                )

                references.extend(
                    extracted
                )

        return references