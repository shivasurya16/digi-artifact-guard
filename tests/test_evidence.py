from core.evidence import EvidenceGraph


def test_evidence_graph_nodes_and_edges():

    graph = EvidenceGraph()

    graph.add_node(
        node_id="artifact_001",
        node_type="artifact",
        path="README.md",
    )

    graph.add_node(
        node_id="missing:model.pkl",
        node_type="missing_artifact",
        path="models/model.pkl",
    )

    graph.add_edge(
        source_id="artifact_001",
        target_id="missing:model.pkl",
        relationship="file_reference",
        confidence=0.95,
    )

    assert len(graph.nodes) == 2
    assert len(graph.edges) == 1

    assert (
        graph.edges[0].relationship
        == "file_reference"
    )

    assert (
        graph.edges[0].confidence
        == 0.95
    )


def test_evidence_graph_incoming_outgoing():

    graph = EvidenceGraph()

    graph.add_node(
        "a",
        "artifact",
        "README.md",
    )

    graph.add_node(
        "b",
        "missing_artifact",
        "models/model.pkl",
    )

    graph.add_edge(
        "a",
        "b",
        "file_reference",
    )

    assert len(graph.outgoing("a")) == 1
    assert len(graph.incoming("b")) == 1