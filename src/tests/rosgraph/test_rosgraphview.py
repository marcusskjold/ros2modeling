import pytest
from roserer.types import NodeType
import roserer.rosgraph as rosgraph
from roserer.rosgraph import RosGraphView, GraphNode
import roserer.ros2system as ros


@pytest.fixture
def test_system() -> tuple[RosGraphView, ros.System, ros.Node]:
    g = RosGraphView()
    s = ros.System("test")
    _s = g.add(GraphNode("test", NodeType.SYSTEM))
    h = s.add_host("h")
    _h = g.add(GraphNode("h", NodeType.HOST, _s))
    e = h.add_executor()
    _e = g.add(GraphNode("e", NodeType.EXECUTOR, _h))
    n = e.add_node()
    _n = g.add(GraphNode("n", NodeType.NODE, _e))

    return g, s, n

@pytest.fixture
def nodelistn3() -> list[GraphNode]:
    n1 = GraphNode("node1", NodeType.CALLBACK)
    n2 = GraphNode("node2", NodeType.HOST)
    n3 = GraphNode("node3", NodeType.HOST)
    return [n1, n2, n3]

def test_rosgraphview_init_default_neg() -> None:
    g = RosGraphView()
    assert g[NodeType.SYSTEM] is not None

def test_rosgraphview_init_default_pos() -> None:
    empty_graph = {
            NodeType.CALLBACK: {},
            NodeType.HOST: {},
            NodeType.ACTION: {},
            NodeType.CLIENT: {},
            NodeType.SERVICE: {},
            NodeType.SUBSCRIBER: {},
            NodeType.TOPIC: {},
            NodeType.TIMER: {},
            NodeType.EXECUTOR: {},
            NodeType.EXTERNAL_INPUT: {},
            NodeType.EXTERNAL_OUTPUT: {},
            NodeType.NODE: {},
            NodeType.PUBLISHER: {},
            NodeType.VARIABLE: {},
            NodeType.SYSTEM: {}
            }
    g = RosGraphView()
    assert g.items() == empty_graph.items()
    assert g[NodeType.SYSTEM] == {}

def test_rosgraphview_init_from_list_neg(nodelistn3) -> None:
    nodes = nodelistn3
    _, n2, _ = nodelistn3
    g = RosGraphView(nodes)

    expected = RosGraphView()
    assert g != expected
    assert not (g == expected)
    assert not g[NodeType.HOST] == {"node2": n2}

def test_rosgraphview_init_from_list_pos(nodelistn3) -> None:
    nodes = nodelistn3
    n1, n2, n3 = nodelistn3
    g = RosGraphView(nodes)

    assert g[NodeType.CALLBACK] == {"node1": n1}
    assert g[NodeType.HOST] == {"node2": n2, "node3": n3}


@pytest.mark.skip("Not implemented")
def test_rosgraphview_init_from_system(test_system) -> None:
    g, s, _ = test_system
    assert RosGraphView(s) == g

def test_rosgraphview_add_list(nodelistn3) -> None:
    nodes = nodelistn3
    n1, n2, n3 = nodelistn3
    g = RosGraphView()
    empty = RosGraphView()
    assert g[NodeType.CALLBACK] == {}
    assert g[NodeType.HOST] == {}
    assert g == empty
    assert not g != empty
    g.add_list(nodes)
    assert g[NodeType.CALLBACK] == {"node1": n1}
    assert g[NodeType.HOST] == {"node2": n2, "node3": n3}
    assert g != empty
    assert not (g == empty)
    

@pytest.mark.skip("Not implemented")
def test_rosgraphview_add_to_empty() -> None:
    pass

@pytest.mark.skip("Not implemented")
def test_rosgraphview_add_to_full() -> None:
    pass

@pytest.mark.skip("Not implemented")
def test_rosgraphview_string_resolve_pos() -> None:
    pass

@pytest.mark.skip("Not implemented")
def test_rosgraphview_string_resolve_neg() -> None:
    pass

@pytest.mark.skip("Not implemented")
def test_rosgraphview_resolve_element_graphnode() -> None:
    pass

@pytest.mark.skip("Not implemented")
def test_rosgraphview_resolve_element_str() -> None:
    pass

@pytest.mark.skip("Not implemented")
def test_rosgraphview_resolve_element_list() -> None:
    pass

@pytest.mark.skip("Not implemented")
def test_rosgraphview_resolve_element_list_invalid() -> None:
    pass

@pytest.mark.skip("Not implemented")
def test_rosgraphview_add_edges() -> None:
    pass

@pytest.mark.skip("Not implemented")
def test_rosgraphview_get_all_nodes_empty() -> None:
    pass

@pytest.mark.skip("Not implemented")
def test_rosgraphview_get_all_nodes_filled() -> None:
    pass

@pytest.mark.skip("Not implemented")
def test_rosgraphview_clone_base() -> None:
    pass

@pytest.mark.skip("Not implemented")
def test_rosgraphview_clone_full() -> None:
    pass

@pytest.mark.skip("Not implemented")
def test_rosgraphview_clone_mod() -> None:
    pass

@pytest.mark.skip("Not implemented")
def test_rosgraphview_get_sinks() -> None:
    pass

@pytest.mark.skip("Not implemented")
def test_rosgraphview_get_sources() -> None:
    pass

@pytest.mark.skip("Not implemented")
def test_rosgraphview_check_for_cycles_split_pos() -> None:
    pass

@pytest.mark.skip("Not implemented")
def test_rosgraphview_check_for_cycles_split_neg() -> None:
    pass

@pytest.mark.skip("Not implemented")
def test_rosgraphview_get_all_chains() -> None:
    pass

@pytest.mark.skip("Not implemented")
def test_rosgraphview_find_equivalent_chain() -> None:
    pass

@pytest.mark.skip("Not implemented")
def test_rosgraphview_get_contracted_view() -> None:
    pass

@pytest.mark.skip("Not implemented")
def test_rosgraphview_get_graph_view_from() -> None:
    pass


@pytest.mark.skip("Not implemented")
def test_rosgraphview_add_system_base(test_system) -> None:
    g, s, _ = test_system
    graph = RosGraphView()
    graph._add_system(s)
    assert graph == g

    #
    # v1 = n.add_variable("v1")
    # _v1 = g.add(GraphNode("v1", NodeType.VARIABLE, _n))
    # v2 = n.add_variable("v2")
    # _v2 = g.add(GraphNode("v2", NodeType.VARIABLE, _n))
    # cb = n.add_callback(1, "cb")
    # _cb = g.add(GraphNode("cb", NodeType.CALLBACK, _n))
