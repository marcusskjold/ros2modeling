import roserer.ros2system as ros
from roserer.patterns.backeman import (
        new_default_backeman_system,
        add_datagenerator,
        add_subscriber,
        add_timer
        )
from dotenv import load_dotenv
import roserer.adapters.backeman_adapter as ba

# This setup is exactly translated from backeman/demo.py:validation_ss(), -st(), -tt(), and -ts()
# Except: We assume that fusion should read from the filters, not the sensors.
#         Therefor we assume that it is a mistake in the original function.

def backeman_ss_scenario(name: str = "backeman_ss") -> ros.System:
    load_dotenv()
    s, e = new_default_backeman_system(name)

    add_datagenerator(e, "SENSOR1", 10, 360, 0)
    add_datagenerator(e, "SENSOR2", 20, 360, 0)
    add_subscriber(e, "FILTER1", 10, "SENSOR1")
    add_subscriber(e, "FILTER2", 20, "SENSOR2")
    add_subscriber(e, "FUSION1", 30, "FILTER1", ["FILTER2"], [30])
    add_subscriber(e, "FILTER3", 30, "FUSION1")
    add_subscriber(e, "ACTUATOR1", 30, "FILTER3")
    return s

def backeman_ss_scenario_erroneous() -> ros.System:
    load_dotenv()
    s, e = new_default_backeman_system("backeman_ss_erroneous")

    add_datagenerator(e, "SENSOR1", 10, 360, 0)
    add_datagenerator(e, "SENSOR2", 20, 360, 0)
    add_subscriber(e, "FILTER1", 10, "SENSOR1")
    add_subscriber(e, "FILTER2", 20, "SENSOR2")
    add_subscriber(e, "FUSION1", 30, "SENSOR1", ["SENSOR2"], [30])
    add_subscriber(e, "FILTER3", 30, "FUSION1")
    add_subscriber(e, "ACTUATOR1", 30, "FILTER3")
    return s

def backeman_ss_scenario_variant() -> ros.System:
    load_dotenv()
    s, e = new_default_backeman_system("backeman_ss_variant")

    add_datagenerator(e, "SENSOR1", 10, 230, 0)
    add_datagenerator(e, "SENSOR2", 20, 220, 0)
    add_subscriber(e, "FILTER1", 10, "SENSOR1")
    add_subscriber(e, "FILTER2", 20, "SENSOR2")
    add_subscriber(e, "FUSION1", 50, "FILTER1", ["FILTER2"], [50])
    add_subscriber(e, "FILTER3", 30, "FUSION1")
    add_subscriber(e, "ACTUATOR1", 30, "FILTER3")
    return s

def backeman_ss_scenario_variant_erroneous() -> ros.System:
    load_dotenv()
    s, e = new_default_backeman_system("backeman_ss_variant_erroneous")

    add_datagenerator(e, "SENSOR1", 10, 230, 0)
    add_datagenerator(e, "SENSOR2", 20, 220, 0)
    add_subscriber(e, "FILTER1", 10, "SENSOR1")
    add_subscriber(e, "FILTER2", 20, "SENSOR2")
    add_subscriber(e, "FUSION1", 50, "FILTER1", ["SENSOR2"], [50])
    add_subscriber(e, "FILTER3", 30, "FUSION1")
    add_subscriber(e, "ACTUATOR1", 30, "FILTER3")
    return s

def backeman_st_scenario(name: str = "backeman_st") -> ros.System:
    load_dotenv()
    s, e = new_default_backeman_system(name)

    add_datagenerator(e, "SENSOR1", 10, 420, 0)
    add_datagenerator(e, "SENSOR2", 20, 420, 0)
    add_subscriber(e, "FILTER1", 10, "SENSOR1")
    add_subscriber(e, "FILTER2", 20, "SENSOR2")
    add_subscriber(e, "FUSION1", 30, "FILTER1", ["FILTER2"], [30])
    add_subscriber(e, "FILTER3", 30, "FUSION1")
    add_timer(e, "ACTUATOR1", 30, 840, 0, ["FILTER3"], [30])
    return s

def backeman_ts_scenario(name: str = "backeman_ts") -> ros.System:
    load_dotenv()
    s, e = new_default_backeman_system(name)

    add_datagenerator(e, "SENSOR1", 10, 420, 0)
    add_datagenerator(e, "SENSOR2", 20, 420, 0)
    add_subscriber(e, "FILTER1", 10, "SENSOR1")
    add_subscriber(e, "FILTER2", 20, "SENSOR2")
    add_timer(e, "FUSION1", 30, 840, 0, ["FILTER1", "FILTER2"], [30, 30])
    add_subscriber(e, "FILTER3", 30, "FUSION1")
    add_subscriber(e, "ACTUATOR1", 30, "FILTER3")
    return s

def backeman_tt_scenario(name: str = "backeman_tt") -> ros.System:
    load_dotenv()
    s, e = new_default_backeman_system(name)

    add_datagenerator(e, "SENSOR1", 10, 480, 0)
    add_datagenerator(e, "SENSOR2", 20, 480, 0)
    add_subscriber(e, "FILTER1", 10, "SENSOR1")
    add_subscriber(e, "FILTER2", 20, "SENSOR2")
    add_timer(e, "FUSION1", 30, 960, 0, ["FILTER1", "FILTER2"], [30, 30])
    add_subscriber(e, "FILTER3", 30, "FUSION1")
    add_timer(e, "ACTUATOR1", 30, 960, 0, ["FILTER3"], [30])
    return s

def backeman_prio_inversion_scenario(name: str = "backeman_prio_inv"):
    s, e = new_default_backeman_system(name)
    add_datagenerator(e, "SENSOR1", 50, 150, 0)
    add_subscriber(e, "FILTER", 30, "SENSOR1" )
    add_datagenerator(e, "SENSOR2", 30, 150, 50)
    add_subscriber(e, "ACTUATOR", 10, "FILTER", ["SENSOR2"], [10])
    return s

