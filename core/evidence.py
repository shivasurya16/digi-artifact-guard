from dataclasses import dataclass, field
from typing import Any


@dataclass
class EvidenceNode:
    """
    A node in the artifact evidence graph.
    """

    node_id: str
    node_type: str
    path: str
    metadata: dict[str, Any] = field(
        default_factory=dict
    )


@dataclass
class EvidenceEdge:
    """
    A directed relationship between two evidence nodes.
    """

    source_id: str
    target_id: str
    relationship: str
    confidence: float
    metadata: dict[str, Any] = field(
        default_factory=dict
    )


class EvidenceGraph:
    """
    Graph containing artifacts and the relationships
    discovered during analysis.
    """

    def __init__(self):
        self.nodes: dict[str, EvidenceNode] = {}
        self.edges: list[EvidenceEdge] = []

    def add_node(
        self,
        node_id: str,
        node_type: str,
        path: str,
        metadata: dict[str, Any] | None = None,
    ) -> EvidenceNode:

        if node_id in self.nodes:
            return self.nodes[node_id]

        node = EvidenceNode(
            node_id=node_id,
            node_type=node_type,
            path=path,
            metadata=metadata or {},
        )

        self.nodes[node_id] = node

        return node

    def add_edge(
        self,
        source_id: str,
        target_id: str,
        relationship: str,
        confidence: float = 1.0,
        metadata: dict[str, Any] | None = None,
    ) -> EvidenceEdge:

        edge = EvidenceEdge(
            source_id=source_id,
            target_id=target_id,
            relationship=relationship,
            confidence=confidence,
            metadata=metadata or {},
        )

        self.edges.append(edge)

        return edge

    def outgoing(
        self,
        node_id: str,
    ) -> list[EvidenceEdge]:

        return [
            edge
            for edge in self.edges
            if edge.source_id == node_id
        ]

    def incoming(
        self,
        node_id: str,
    ) -> list[EvidenceEdge]:

        return [
            edge
            for edge in self.edges
            if edge.target_id == node_id
        ]

    def to_dict(self) -> dict[str, Any]:

        return {
            "nodes": [
                {
                    "node_id": node.node_id,
                    "node_type": node.node_type,
                    "path": node.path,
                    "metadata": node.metadata,
                }
                for node in self.nodes.values()
            ],
            "edges": [
                {
                    "source_id": edge.source_id,
                    "target_id": edge.target_id,
                    "relationship": edge.relationship,
                    "confidence": edge.confidence,
                    "metadata": edge.metadata,
                }
                for edge in self.edges
            ],
        }
    