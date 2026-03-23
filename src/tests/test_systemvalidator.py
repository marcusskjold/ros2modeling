from roserer.ros2system import System
import roserer.yamlParser as yparser
import roserer.systemvalidator as sv
import pytest

def test_parse_system_connected_hosts_allowed() -> None:
    """
    Tests that hosts connected by topic-communication doesn't prompt a warning 
    about being disconnected
    """
    test_sys = yparser.parse_yaml("src/tests/input/yaml_parser/test_parse_system_connected_hosts_allowed.yaml")
    feedback = sv.validate_system(test_sys) 
    assert not any("Not all hosts are connected" in warn for warn in feedback.warnings)

def test_validate_calls_detects_cycle() -> None:
    """
    Tests that a callback-function doesn't call itself infinitely.
    """
    test_sys = yparser.parse_yaml("src/tests/input/system_validator/test_validate_calls_detects_cycle.yaml")
    val_result = sv.validate_system(test_sys)     
    assert val_result.errors == ["[E004]: Graph of system contains cycles. Only acyclic systems may be analyzed"]

@pytest.mark.skip("This check is not implemented yet. It requires that wall_times are moved to external input")
def test_validate_system_detects_no_activity() -> None:
    """
    Tests that a system with parts lacking any activity is not accepted by the system_validator.
    (Message must flow through the system)
    """
    test_sys = yparser.parse_yaml("src/tests/input/system_validator/test_validate_system_detects_no_activity.yaml")
    val_result = sv.validate_system(test_sys)
    print(val_result.errors)
    assert val_result.errors != []

def test_validation_results_detects_nested_cycle() -> None:
    """
    Tests that cycle resulting from a nested is detected.
        cb has nested_cb in calls, and nested_cb calls cb_2, which calls cb_1
    """
    test_sys = yparser.parse_yaml("src/tests/input/system_validator/test_validation_results_detects_nested_topic_cycle.yaml")
    feedback = sv.validate_system(test_sys)
    assert feedback.errors == ["[E004]: Graph of system contains cycles. Only acyclic systems may be analyzed"]


def test_validation_results_detects_nested_service_cycle() -> None:
    """
    Tests that cycle resulting from a nested is detected.
        cb has nested_cb in calls, and nested_cb calls cb_2, which calls cb_1
    """
    test_sys = yparser.parse_yaml("src/tests/input/system_validator/test_validation_results_detects_nested_service_cycle.yaml")
    feedback = sv.validate_system(test_sys)
    assert feedback.errors == ["[E004]: Graph of system contains cycles. Only acyclic systems may be analyzed"]

def test_warning_graph_disconnected_at_host_level() -> None:
    sys = System("test")
    h1 = sys.add_host("host1")
    h2 = sys.add_host("host2")
    n1 = h1.add_executor().add_node("node1")
    n1.add_publisher("node1topic", name="pub1")
    n1.add_callback(30, "cb1", publishers=["pub1"])
    n1.add_timer(200, "cb1")
    n2 = h1.add_executor().add_node("node2")
    n2.add_callback(30, "cb2")
    n2.add_subscription("node1topic", callback="cb2")

    n3 = h2.add_executor().add_node("node3")
    n3.add_publisher("node3topic", name="pub3")
    n3.add_callback(30, "cb3", publishers=["pub3"])
    n3.add_timer(200, "cb3")
    n4 = h2.add_executor().add_node("node4")
    n4.add_callback(30, "cb4")
    n4.add_subscription("node3topic", callback="cb4")
    feedback = sv.validate_system(sys)
    assert feedback.errors == []
    assert feedback.warnings == ["[W005]: Not all hosts are connected, for example no object"
                                 " in host1 communicates with any object in host2"]

def test_warning_system_timer_period_too_small_wcet_greater_than_period() -> None:
    """
    Tests that a net sum wcet of a callback above the period of its timer
    is caught (when individual wcet of calls is below)
    """
    test_sys = yparser.parse_yaml("src/tests/input/dust/test_validate_timer_invalid_wcet_sum_caught.yaml")
    feedback = sv.validate_system(test_sys)
    assert feedback.contains("[W006]")

def test_warning_system_timer_period_too_small_wcet_and_period_equal() -> None:
    """
    Tests that a net sum wcet of a callback equal to period of timer is accepted
    """
    test_sys = yparser.parse_yaml("src/tests/input/dust/test_validate_timer_edge_wcet_sum_accepted.yaml")
    feedback = sv.validate_system(test_sys)
    assert not feedback.contains("[W006]")
