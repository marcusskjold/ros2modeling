import logging
import pytest
from roserer.types import NodeType
from roserer.rosgraph import RosGraphView, GraphNode
import roserer.yamlParser as yparse
import roserer.ros2system as ros
import roserer.adapters.backeman_adapter as ba
import roserer.qos as qos
import roserer.scenarios.backeman as bms

def blank_node() -> ros.Node:
    return ros.Node(
            name="node",
            default_qos=qos.qos_profile_default(),
            subscriptions=[],
            callbacks=[],
            timers=[],
            publishers=[],
            variables=[],
            services=[],
            actions=[],
            external_inputs=[],
            external_outputs=[],
            clients=[]
            )

def test_is_valid_subscriber_negative() -> None:
    n = blank_node()
    assert not ba.is_valid_subscriber(n)

def test_is_valid_subscriber_positive() -> None:
    n = blank_node()
    n.add_callback(10)
    n.add_subscription("test", "node_cb0")
    assert ba.is_valid_subscriber(n)

def test_e101() -> None:
    g = RosGraphView()
    g.add(GraphNode("host1", NodeType.HOST))
    g.add(GraphNode("host2", NodeType.HOST))
    assert (ba.error_graph_limited_node_types(g) == 
            ["[E101]: System has 2 hosts, but target metamodel supports at most 1"])

def test_e102() -> None:
    g = RosGraphView()
    cb1 = g.add(GraphNode("cb1", NodeType.CALLBACK))
    tim = g.add(GraphNode("timer", NodeType.TIMER))
    sub = g.add(GraphNode("sub", NodeType.SUBSCRIBER))
    tim.add_edge_to(cb1)
    sub.add_edge_to(cb1)
    assert (ba.error_graph_multiple_callback_triggers(g) ==
            ["[E104]: Callback 'cb1' has more than one trigger"])


def test_w101() -> None:
    g = RosGraphView()
    g.add(GraphNode("topic1", NodeType.TOPIC))
    assert (ba.warning_topic_case_insensitive(g) ==
            ["[W101]: Topic 'topic1' is not upper case, model assumes upper"
             "case names. Name is forced to upper case during transformation"])

def test_validate_chain() -> None:
    s = bms.backeman_ss_scenario()
    g = RosGraphView(s)
    c = [GraphNode("test1", NodeType.ACTION), GraphNode("test2", NodeType.TIMER)]
    r = ba.validate_chain(c, g)
    assert r == [
        "[E105] Invalid chain: Monitored chain starts with a non-timer object",
        "[E106] Invalid chain: Monitored chain ends with a TIMER",
        "[E107] Invalid chain: test1 is not linked to test2",
        "[E108] Invalid chain: Graph and chain does not refer to equivalent systems. There is no equivalent to test1 in graph"]

def test_name_force_upper() -> None:
    node = GraphNode("node", NodeType.NODE)
    cb = GraphNode("testcb", NodeType.CALLBACK, node)
    var = GraphNode("var", NodeType.VARIABLE)
    cb2 = GraphNode("testcb2", NodeType.CALLBACK)
    sub = GraphNode("testsub", NodeType.SUBSCRIBER)
    top = GraphNode("topic2Geo", NodeType.TOPIC)
    chain = [top, sub, cb2, var, cb]
    top.add_edge_to(sub)
    sub.add_edge_to(cb2)
    cb2.add_edge_to(var)
    var.add_edge_to(cb)
    result = ba.get_data_source_for_cb_in_chain(chain, cb)
    assert result == "NODExTOPIC2GEO_data"

def test_invalid_bcet() -> None:
    s = bms.backeman_ss_scenario()
    s.get_node("SENSOR1").callbacks[0].bcet = 100000
    feedback = ba.validate_system(s, [])
    assert feedback.errors != []
    assert len(feedback.errors) == 1
    assert feedback.contains("[E123]")

def test_dust_system_is_rejected() -> None:
    ros_system = yparse.parse_yaml("src/tests/input/dust_scenario_1_EXV1_holistic.yaml")
    feedback = ba.validate_system(ros_system, [])
    assert feedback.errors != []
    for error in ("[E101]","[E114]", "[E116]", "[E118]", "[E120]", "[E122]",):
        assert feedback.contains(error)
