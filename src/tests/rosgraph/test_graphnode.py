from roserer.types import NodeType
from roserer.rosgraph import GraphNode, RosGraphView

def test_graphnode_equivalent_positive_base() -> None:
    n1 = GraphNode("node1", NodeType.NODE)
    n2 = GraphNode("node1", NodeType.NODE)
    assert n1.equivalent(n2)
    assert n2.equivalent(n1)

def test_graphnode_equivalent_positive_different_parents() -> None:
    p1 = GraphNode("parent1", NodeType.EXECUTOR)
    p2 = GraphNode("parent2", NodeType.CALLBACK)
    n1 = GraphNode("node1", NodeType.NODE, p1)
    n2 = GraphNode("node1", NodeType.NODE, p2)
    assert n1.equivalent(n2)
    assert n2.equivalent(n1)

def test_graphnode_equivalent_positive_different_links() -> None:
    g1 = RosGraphView()
    n1 = g1.add(GraphNode("node1", NodeType.CALLBACK))
    n3 = g1.add(GraphNode("node2", NodeType.CALLBACK))
    n1.outgoing.append(n3)
    n3.incoming.append(n1)
    g2 = RosGraphView()
    n2 = g2.add(GraphNode("node1", NodeType.CALLBACK))
    n2.outgoing.append(n1)

    assert n1.equivalent(n2)
    assert n2.equivalent(n1)

def test_graphnode_equivalent_negative_type() -> None:
    n1 = GraphNode("node1", NodeType.CALLBACK)
    n2 = GraphNode("node1", NodeType.EXECUTOR)

    assert not n1.equivalent(n2)
    assert not n2.equivalent(n1)

def test_graphnode_equivalent_negative_name() -> None:
    n1 = GraphNode("node1", NodeType.CALLBACK)
    n2 = GraphNode("node2", NodeType.CALLBACK)

    assert not n1.equivalent(n2)
    assert not n2.equivalent(n1)

def test_graphnode_add_edge_to_positive() -> None:
    n1 = GraphNode("node1", NodeType.CALLBACK)
    n2 = GraphNode("node2", NodeType.CALLBACK)
    n3 = GraphNode("node3", NodeType.CALLBACK)

    n1.add_edge_to(n2)
    n1.add_edge_to(n3)

    assert n1.outgoing == [n2, n3]
    assert n2.incoming == [n1]
    assert n3.incoming == [n1]

def test_graphnode_weakly_connected_with() -> None:
    n1 = GraphNode("node1", NodeType.CALLBACK)
    n2 = GraphNode("node2", NodeType.CALLBACK)
    n3 = GraphNode("node3", NodeType.CALLBACK)
    n4 = GraphNode("node4", NodeType.CALLBACK)
    n5 = GraphNode("node5", NodeType.CALLBACK)
    n6 = GraphNode("node6", NodeType.CALLBACK)
    n1.add_edge_to(n2)
    n2.add_edge_to(n3)
    n4.add_edge_to(n1)
    n5.add_edge_to(n6)

    actual = n1.weakly_connected_with()
    expected = [n1, n2, n3, n4]
    for n in actual:
        assert n in expected
    assert len(actual) == len(expected)

def test_graphnode_check_for_cycles_negative_base() -> None:
    n1 = GraphNode("node1", NodeType.CALLBACK)
    assert not n1.check_for_cycles()

def test_graphnode_check_for_cycles_negative_n2() -> None:
    n1 = GraphNode("node1", NodeType.CALLBACK)
    n2 = GraphNode("node2", NodeType.CALLBACK)
    n1.add_edge_to(n2)
    assert not n1.check_for_cycles()
    assert not n2.check_for_cycles()

def test_graphnode_check_for_cycles_positive_base() -> None:
    n1 = GraphNode("node1", NodeType.CALLBACK)
    assert n1.check_for_cycles([],[n1])

def test_graphnode_check_for_cycles_positive_n2() -> None:
    n1 = GraphNode("node1", NodeType.CALLBACK)
    n2 = GraphNode("node2", NodeType.CALLBACK)
    n1.add_edge_to(n2)
    n2.add_edge_to(n1)
    assert n1.check_for_cycles()
    assert n2.check_for_cycles()

def test_graphnode_check_for_cycles_positive_n3() -> None:
    n1 = GraphNode("node1", NodeType.CALLBACK)
    n2 = GraphNode("node2", NodeType.CALLBACK)
    n3 = GraphNode("node3", NodeType.CALLBACK)
    n1.add_edge_to(n2)
    n2.add_edge_to(n3)
    n3.add_edge_to(n1)
    assert n1.check_for_cycles()
    assert n2.check_for_cycles()
    assert n3.check_for_cycles()

def test_graphnode_check_for_cycles_positive_indirect() -> None:
    n1 = GraphNode("node1", NodeType.CALLBACK)
    n2 = GraphNode("node2", NodeType.CALLBACK)
    n3 = GraphNode("node3", NodeType.CALLBACK)
    n1.add_edge_to(n2)
    n2.add_edge_to(n3)
    n3.add_edge_to(n2)
    assert n1.check_for_cycles()

def test_graphnode_get_paths_to_base_positive() -> None:
    n1 = GraphNode("node1", NodeType.CALLBACK)
    assert n1.get_paths_to(n1) == [[n1]]

def test_graphnode_get_paths_to_negative() -> None:
    n1 = GraphNode("node1", NodeType.CALLBACK)
    n2 = GraphNode("node2", NodeType.CALLBACK)
    assert n1.get_paths_to(n2) == []

def test_graphnode_get_paths_to_n3() -> None:
    n1 = GraphNode("node1", NodeType.CALLBACK)
    n2 = GraphNode("node2", NodeType.CALLBACK)
    n3 = GraphNode("node3", NodeType.CALLBACK)
    n1.add_edge_to(n2)
    n2.add_edge_to(n3)
    assert n1.get_paths_to(n1) == [[n1]]
    assert n1.get_paths_to(n2) == [[n1,n2]]
    assert n1.get_paths_to(n3) == [[n1,n2,n3]]
    assert n2.get_paths_to(n2) == [[n2]]
    assert n2.get_paths_to(n3) == [[n2,n3]]
    assert n3.get_paths_to(n3) == [[n3]]
    assert n3.get_paths_to(n2) == []
    assert n3.get_paths_to(n1) == []

def test_graphnode_get_paths_to_n3_multipath() -> None:
    n1 = GraphNode("node1", NodeType.CALLBACK)
    n2 = GraphNode("node2", NodeType.CALLBACK)
    n3 = GraphNode("node3", NodeType.CALLBACK)
    n4 = GraphNode("node4", NodeType.CALLBACK)
    n1.add_edge_to(n2)
    n1.add_edge_to(n3)
    n2.add_edge_to(n3)
    n2.add_edge_to(n4)
    n3.add_edge_to(n4)
    assert n1.get_paths_to(n3) == [[n1,n3],[n1,n2,n3]]
    assert n1.get_paths_to(n4) == [[n1,n3,n4],[n1,n2,n4],[n1,n2,n3,n4]]
    assert n2.get_paths_to(n4) == [[n2,n4],[n2,n3,n4]]

def test_graphnode_contract() -> None:
    p1 = GraphNode("parent", NodeType.NODE)
    n1 = GraphNode("node1", NodeType.CALLBACK, p1)
    n2 = GraphNode("node2", NodeType.CALLBACK, p1)
    n3 = GraphNode("node3", NodeType.CALLBACK)
    c1 = GraphNode("child1", NodeType.CALLBACK,n2)
    n1.add_edge_to(n2)
    n2.add_edge_to(n3)
    c1.add_edge_to(n1)

    assert p1.children == [n1,n2]
    assert n1.outgoing == [n2]
    assert n1.incoming == [c1]
    assert n3.incoming == [n2]
    assert c1.parent == n2
    n2.contract()
    assert p1.children == [n1]
    assert n1.outgoing == [n3]
    assert n1.incoming == [c1]
    assert n3.incoming == [n1]
    assert c1.parent == p1
    
