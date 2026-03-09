import roserer.yamlParser as yparser
from tests.input.yaml_parser.parse_system_maps_correctly import sys as expected_sys
import pytest
import roserer.ros2system as ros

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

def test_parse_timer_interval_endpoints_parsed() -> None:
    """ 
    Tests that the interval specified in begin and end of a timer is correctly parsed.
    """
    test_sys = yparser.parse_yaml("src/tests/input/yaml_parser/test_parse_timer_interval_endpoints_parsed.yaml")
    actual_timers = [timer.__dict__ for timer in test_sys.hosts[0].executors[0].nodes[0].timers]
    expected_timers = {
        'timer_1': {
            'name' : 'timer_1',
            'callback' : 'cb_1',
            'period' : 5,
            'offset' : 0,
            'interval' : (2,20)
        },
        'timer_2': {
            'name' : 'timer_2',
            'callback' : 'cb_1',
            'period' : 6,
            'offset' : 0,
            'interval' : (0,20)
        }
    }
    assert expected_timers['timer_1'] in actual_timers
    assert expected_timers['timer_2'] in actual_timers
    
def test_parse_timer_missing_endpoints_caught() -> None:
    """
    Tests that a timer with only begin-interval raises an error.
    """
    with pytest.raises(SyntaxError):
        yparser.parse_yaml("src/tests/input/yaml_parser/test_parse_timer_missing_endpoints_caught.yaml")

def test_parse_system_duplicate_keys_caught() -> None:
    """
    Tests that parser doesn't silently fails if multiple keys are present.
    """
    with pytest.raises(Exception) as e:
        yparser.parse_yaml("src/tests/input/yaml_parser/test_parse_system_duplicate_keys_caught.yaml")
    assert 'found duplicate key' in str(e.value)

def test_validate_attributes_invalid_attributes_caught() -> None:
    """ 
    Tests that invalid keys in a YAML-specification is caught.
    """
    with pytest.raises(TypeError):
        yparser.parse_yaml("src/tests/input/yaml_parser/test_validate_attributes_invalid_attributes_caught.yaml")


parse_time_unit__valid = [
        ('ns', ros.TimeUnit.NANOSECONDS),
        ('nanoseconds', ros.TimeUnit.NANOSECONDS),
        ('us', ros.TimeUnit.MICROSECONDS),
        ('microseconds', ros.TimeUnit.MICROSECONDS),
        ('ms', ros.TimeUnit.MILLISECONDS),
        ('milliseconds', ros.TimeUnit.MILLISECONDS),
        ('sec', ros.TimeUnit.SECONDS),
        ('seconds', ros.TimeUnit.SECONDS),
        ('min', ros.TimeUnit.MINUTES),
        ('minutes', ros.TimeUnit.MINUTES)
        ]
@pytest.mark.parametrize("input,exp_enum", parse_time_unit__valid)
def test_validate_time_unit_enums_created(input, exp_enum)-> None:
    """
    Tests that all valid time-units are parsed to enums according to expectations
    """
    assert yparser.parse_time_unit(input) == exp_enum

def test_parse_system_invalid_time_unit_caught()-> None:
    """
    Tests that a system with an invalid time unit raises an error.
    """
    with pytest.raises(ValueError):
        yparser.parse_yaml("src/tests/input/yaml_parser/test_parse_system_invalid_time_unit_caught.yaml")