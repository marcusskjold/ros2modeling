from roserer.rosgraph import GraphNode, filter_list_by_type, find_in_list
from roserer.types import NodeType

def test_filter_list_by_type() -> None:
    n1 = GraphNode("node1", NodeType.CALLBACK)
    n2 = GraphNode("node2", NodeType.TIMER)
    n3 = GraphNode("node3", NodeType.HOST)
    n4 = GraphNode("node4", NodeType.HOST)
    nodes = [n1, n2, n3, n4]

    assert filter_list_by_type(nodes, [NodeType.CALLBACK]) == [n1]
    assert filter_list_by_type(nodes, [NodeType.HOST]) == [n3,n4]
    assert filter_list_by_type(nodes, []) == []
    assert filter_list_by_type(nodes, NodeType) == [n1, n2, n3, n4]

def test_filter_in_list() -> None:
    n1 = GraphNode("node1", NodeType.CALLBACK)
    n2 = GraphNode("node2", NodeType.HOST)
    n3 = GraphNode("node3", NodeType.HOST)
    nodes = [n1, n2, n3]

    assert find_in_list(nodes, NodeType.HOST, "node2") == n2
    assert find_in_list(nodes, NodeType.HOST, "node3") == n3
    assert find_in_list(nodes, NodeType.CALLBACK, "node3") is None
