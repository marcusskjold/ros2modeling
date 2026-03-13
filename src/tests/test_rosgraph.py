import pytest
import roserer.rosgraph as rosgraph
import roserer.ros2system as ros

def test_one():
    sys = ros.System("test")
    n = sys.add_host().add_executor().add_node("n")
    cb0 = n.add_callback(0, name="cb0")
    n.add_callback(1, name="cb1", calls="cb0")
    n.add_callback(2, name="cb2", calls="cb1")
    n.add_timer(period=10, callback=cb0)
    graph = rosgraph.get_graph_view_from(sys)

