import roserer.yamlParser as yparser
from tests.input.yaml_parser.parse_system_maps_correctly import sys as expected_sys
import pytest

def test_parse_system_maps_correctly() -> None:
    """ 
    Tests that a basic ROS2 system specified in YAML is mapped according to expectations.
    """
    test_sys = yparser.parse_yaml("src/tests/input/yaml_parser/test_parse_system_maps_correctly.yaml")
    assert test_sys.__dict__ == expected_sys.__dict__

def test_parse_system_cb_order_maintained() -> None:
    """
    Tests that order of callbacks are maintained when creating a system from
    a yaml file. The order in the ros2system.System object should reflect the
    order listed in the yaml-file.
    """
    test_sys = yparser.parse_yaml("src/tests/input/yaml_parser/test_parse_system_cb_order_maintained.yaml")
    actual_callback_names = [cb.name for cb in test_sys.hosts[0].executors[0].nodes[0].callbacks]
    assert actual_callback_names == ['cb_1', 'cb_2', 'cb_3']
