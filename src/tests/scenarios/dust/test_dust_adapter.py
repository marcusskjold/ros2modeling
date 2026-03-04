from roserer.systemvalidator import is_valid_value
import roserer.yamlParser as yparser
import roserer.systemvalidator as sv
import pytest as pt
import roserer.adapters.dust_adapter as da

def test_transform_system_no_duplicate_subscribers() -> None:
    """
    Tests that a callback- and topic-template is made for each publisher to a given topic,
    but only 1 subscription-callback for each subscription to a topic is made.
    """
    test_sys = yparser.parse_yaml("src/tests/input/dust/test_transform_system_no_duplicate_subscribers.yaml")
    errors, warnings, dust_sys = da.transform_system(test_sys)
    assert errors == []
    assert warnings == []
    assert len(dust_sys.topics) == 2
    assert len(dust_sys.callbacks) == 3

def test_transform_system_detects_duplicate_service_calls() -> None:
    """
    Tests service invoked from more sources isn't accepted by validator
    """ 
    test_sys = yparser.parse_yaml("src/tests/input/dust/test_transform_system_detects_duplicate_service_calls.yaml")
    errors, warnings, dust_sys = da.transform_system(test_sys)
    assert "The same service is being requested from multiple sources. This model only support a service being requested from one place." in errors


# def test_transform_system_unique_service_client() -> None:
#     """
#     Tests that a unique topic-templates are made for each client-service-communication
#     """
#     test_sys = yparser.parse_yaml("src/tests/input/dust/test_transform_system_unique_service_client.yaml")
#     errors, warnings, dust_sys = da.transform_system(test_sys)
#     assert errors == []
#     assert warnings == []
#     print(dust_sys.gen_system())
#     assert len(dust_sys.topics) == 4
#     assert len(dust_sys.callbacks) == 3

def test_transform_system_nested_calls_collapsed() -> None:
    """
    Tests that a callback with nested calls is collapsed into a single callback
    with wcet = the sum of the callbacks and correct arrays for sending.
    """