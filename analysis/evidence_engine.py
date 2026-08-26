from core.evidence import EvidenceGraph


class EvidenceEngine:
    """
    Builds an evidence graph from artifacts and references.
    """

    def build(self, artifacts, references):

        graph = EvidenceGraph()

        # Artifact nodes
        for artifact in artifacts:
            graph.add_node(
                node_id=artifact.id,
                node_type="artifact",
                path=artifact.path,
                metadata={
                    "artifact_type": artifact.artifact_type,
                    "extension": artifact.extension,
                    "size": artifact.size,
                },
            )

        # Reference relationships
        for reference in references:

            if reference.target_exists:
                target_id = reference.target_artifact_id

            else:
                target_id = self._missing_node_id(
                    reference.reference
                )

                graph.add_node(
                    node_id=target_id,
                    node_type="missing_artifact",
                    path=reference.reference,
                    metadata={
                        "reference_type":
                            reference.reference_type,
                    },
                )

            graph.add_edge(
                source_id=reference.source_artifact_id,
                target_id=target_id,
                relationship=reference.reference_type,
                confidence=self._confidence(reference),
                metadata=reference.metadata,
            )

        return graph

    def _missing_node_id(self, reference):

        normalized = (
            reference
            .replace("\\", "/")
            .lower()
        )

        return f"missing:{normalized}"

    def _confidence(self, reference):

        confidence_map = {
            "file_reference": 0.95,
            "python_import": 0.90,
            "python_file_reference": 0.90,
        }

        return confidence_map.get(
            reference.reference_type,
            0.75,
        )