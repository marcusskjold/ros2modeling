from roserer.types import NodeType
from roserer.rosgraph import GraphNode, RosGraphView
import roserer.ros2system as ros

def test_one():
    sys = ros.System("test")
    n = sys.add_host().add_executor().add_node("n")
    cb0 = n.add_callback(0, name="cb0")
    n.add_callback(1, name="cb1", calls="cb0")
    n.add_callback(2, name="cb2", calls="cb1")
    n.add_timer(period=10, callback=cb0)
    graph = RosGraphView(sys)

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



def test_graphnode_weakly_connected_with_positive_base() -> None:
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


