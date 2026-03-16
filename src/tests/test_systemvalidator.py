import roserer.yamlParser as yparser
import roserer.systemvalidator as sv
import pytest

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
