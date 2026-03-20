from roserer.rosgraph import RosGraphView
from roserer.types import NodeType
import logging
import roserer.ros2system as ros
import roserer.scenarios.backeman as bmscenario
from roserer.printers.graph_printer import GraphDrawer

def test_graph_printer_base():
    log = logging.getLogger(__name__)
    s = ros.System("test")
    n = s.add_host().add_executor().add_node()
    cb1 = n.add_callback(30, "cb1")
    n.add_timer(10, cb1, "timer1")
    gd = GraphDrawer(s)
    assert gd.A.edges() == [("TIMER timer1", "CALLBACK cb1")]
    gd.save_to_file("results/test/test_graph_printer_base.svg")
    assert gd.A.nodes() == ["TIMER timer1", "CALLBACK cb1"]

def test_graph_printer_backeman_scenario():
    log = logging.getLogger(__name__)
    s = bmscenario.backeman_ss_scenario()
    gd = GraphDrawer(s)
    gd.save_to_file("results/test/test_graph_printer_backeman_scenario_full.svg")
    GraphDrawer(s,[NodeType.CALLBACK]).save_to_file("results/test/test_graph_printer_backeman_scenario_cb.svg")
    GraphDrawer(s,[NodeType.TOPIC]).save_to_file("results/test/test_graph_printer_backeman_scenario_topic.svg")
    GraphDrawer(s,[NodeType.NODE,
                   NodeType.CALLBACK,
                   NodeType.TIMER
                   ]).save_to_file("results/test/test_graph_printer_backeman_scenario_many.svg")

    g = GraphDrawer(s,[
        NodeType.CALLBACK,
        # NodeType.EXECUTOR,
        # NodeType.VARIABLE,
        # NodeType.TIMER,
        NodeType.NODE,
        # NodeType.HOST,
        NodeType.SYSTEM,
        # NodeType.TOPIC
        ]).save_to_file("results/test/test_graph_printer_backeman_scenario_many2.svg")
    log.debug(str(g))
    # log.debug(str(g))
    # log.debug(str(RosGraphView(s).get_contracted_view([NodeType.CALLBACK, NodeType.NODE, NodeType.SYSTEM])))
