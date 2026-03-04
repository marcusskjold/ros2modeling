from roserer.systemvalidator import is_valid_value
import roserer.yamlParser as yparser
import roserer.systemvalidator as sv
import pytest as pt


def test_is_valid_value_dds_positive() -> None:
    """
    The list of valid dds implementations are taken from
    https://docs.ros.org/en/rolling/Installation/RMW-Implementations/DDS-Implementations.html
    Accessed 2026-01-19
    """
    assert is_valid_value("dds", "Generic") == []
    assert is_valid_value("dds", "Cyclone") == []
    assert is_valid_value("dds", "Fast") == []
    assert is_valid_value("dds", "Connext") == []
    assert is_valid_value("dds", "Gurum") == []


def test_is_valid_value_dds_negative() -> None:
    assert is_valid_value("dds", "") != []
    assert is_valid_value("dds", "Cyclon") != []


def test_is_valid_value_executor_positive() -> None:
    """
    The most common executors are SingleThreadedExecutor and MultiThreadedExecutor:
    https://docs.ros.org/en/rolling/Concepts/Intermediate/About-Executors.html
    Accessed 2026-01-19

    The EventsExecutor was first introduced with Iron Irwini:
    https://docs.ros.org/en/rolling/Releases/Release-Iron-Irwini.html#introduction-of-a-new-executor-type-the-events-executor
    Accessed 2026-01-19
    """
    assert is_valid_value("executor", "SingleThreadedExecutor") == []
    assert is_valid_value("executor", "MultiThreadedExecutor") == []
    assert is_valid_value("executor", "EventsExecutor") == []

def test_validate_calls_detects_cycle() -> None:
    """
    Tests that a callback-function doesn't call itself infinitely.
    """
    test_sys = yparser.parse_yaml("src/tests/input/system_validator/test_validate_calls_detects_cycle.yaml")
    val_result = sv.validate_system(test_sys)     
    assert val_result.errors[0] == "The chain of calls, ['cb', 'nested_cb', 'nested_nested_cb'], is circular. Ensure acyclic chain of calls between callbacks."

def test_validate_calls_registers_root() -> None:
    """
    Tests that root_node is registered as sending messages to same topics/services as chained cb's
    in 'calls'
    """
    test_sys = yparser.parse_yaml("src/tests/input/system_validator/test_validate_calls_registers_root.yaml")
    val_result = sv.validate_system(test_sys)
    expected_interf = {
        "services requested" :
            {"service_1" : ["nested_nested_cb", "cb", "nested_cb"]},
        "services offered" : 
            {"service_1" : ["service_cb"]},
        "services received from":
            {"service_1" : ["response_cb"]},
        "topics published to" :
            {"topic_1" : ["nested_cb", "cb"]},
        "topics subscribed to" :
            {"topic_1" : ["sub_cb"]},
        "variables read from" :
            {},
        "variables written to" : 
            {}
    }
    # TODO: might as well check graph-object here?
    assert val_result.interfaces == expected_interf

def test_add_interface_registers_wall_times() -> None:
    """
    Tests that services/subscriptions with wall_times are validated such that
    their corresponding service/topics are listed as posted to.
    """
    test_sys = yparser.parse_yaml("src/tests/input/system_validator/test_add_interface_registers_wall_times.yaml")
    val_result = sv.validate_system(test_sys)
    assert "service_1" in val_result.interfaces["services requested"]
    assert "topic_1" in val_result.interfaces["topics published to"]

#### tests that fails until specific features implemented ####
# def test_validate_system_detects_no_activity() -> None:
#     """
#     Tests that a system with parts lacking any activity is not accepted by the system_validator.
#     (Message must flow through the system)
#     """
#     test_sys = yparser.parse_yaml("src/tests/input/system_validator/test_validate_system_detects_no_activity.yaml")
#     val_result = sv.validate_system(test_sys)
#     print(val_result.errors)
#     assert val_result.errors != []

# def test_validation_results_detects_nested_cycle() -> None:
#     """
#     Tests that cycle resulting from a nested is detected.
#         cb has nested_cb in calls, and nested_cb calls cb_2, which calls cb_1
#     """
#     with pt.raises(Exception) as e:
#         test_sys = yparser.parse_yaml("src/tests/input/system_validator/test_validation_results_detects_nested_topic_cycle.yaml")
#         sv.validate_system(test_sys)
#     assert "There is a cycle in the graph from " in str(e.value)


# def test_validation_results_detects_nested_service_cycle() -> None:
#     """
#     Tests that cycle resulting from a nested is detected.
#         cb has nested_cb in calls, and nested_cb calls cb_2, which calls cb_1
#     """
#     with pt.raises(Exception) as e:
#         test_sys = yparser.parse_yaml("src/tests/input/system_validator/test_validation_results_detects_nested_service_cycle.yaml")
#         sv.validate_system(test_sys)
#     assert "There is a cycle in the graph from " in str(e.value)