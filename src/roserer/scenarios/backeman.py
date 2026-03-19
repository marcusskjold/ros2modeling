import pytest
import roserer.ros2system as ros
from roserer.ros2system import EXECUTOR, DISTRIBUTION
from roserer.patterns.backeman import (
        add_datagenerator,
        add_subscriber,
        add_timer
        )
from dotenv import load_dotenv

# This setup is exactly translated from backeman/demo.py:validation_ss(), -st(), -tt(), and -ts()
# Except: We assume that fusion should read from the filters, not the sensors.
#         Therefor we assume that it is a mistake in the original function.

def new_default_backeman_system(name: str) -> tuple[ros.System, ros.Executor]:
    s = ros.System(name)
    s.default_qos.depth = 20

    h = s.add_host()
    e = h.add_executor(
            implementation=EXECUTOR.SingleThreadedExecutor,
            ros_distribution=DISTRIBUTION.Eloquent)
    return s, e

def backeman_st_scenario() -> ros.System:
    load_dotenv()
    s, e = new_default_backeman_system("backeman_st")

    add_datagenerator(e, "SENSOR1", 10, 420, 0)
    add_datagenerator(e, "SENSOR2", 20, 420, 0)
    add_subscriber(e, "FILTER1", 10, "SENSOR1")
    add_subscriber(e, "FILTER2", 20, "SENSOR2")
    add_subscriber(e, "FUSION1", 30, "FILTER1", ["FILTER2"], [30])
    add_subscriber(e, "FILTER3", 30, "FUSION1")
    add_timer(e, "ACTUATOR1", 30, 840, 0, ["FILTER3"], [30])
    return s

def backeman_ss_scenario() -> ros.System:
    load_dotenv()
    s, e = new_default_backeman_system("backeman_ss")

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
    s, e = new_default_backeman_system("backeman_ss")

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
    s, e = new_default_backeman_system("backeman_ss")

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
    s, e = new_default_backeman_system("backeman_ss")

    add_datagenerator(e, "SENSOR1", 10, 230, 0)
    add_datagenerator(e, "SENSOR2", 20, 220, 0)
    add_subscriber(e, "FILTER1", 10, "SENSOR1")
    add_subscriber(e, "FILTER2", 20, "SENSOR2")
    add_subscriber(e, "FUSION1", 50, "FILTER1", ["SENSOR2"], [50])
    add_subscriber(e, "FILTER3", 30, "FUSION1")
    add_subscriber(e, "ACTUATOR1", 30, "FILTER3")
    return s

# def backeman_ss_scenario_variant() -> ros.System:
#     """
#     Another example of an error resulting in wrong system declaration
#     """
#     load_dotenv()
#     s, e = new_default_backeman_system("backeman_ss")
#
#     add_datagenerator(e, "SENSOR1", 10, 230, 0)
#     add_datagenerator(e, "SENSOR2", 20, 220, 0)
#     add_subscriber(e, "FILTER1", 10, "SENSOR1")
#     add_subscriber(e, "FILTER2", 20, "SENSOR2")
#     add_subscriber(e, "FUSION1", 50, "FILTER1", ["FILTER2"], [50])
#     add_subscriber(e, "FILTER3", 30, "FUSION1")
#     add_subscriber(e, "ACTUATOR1", 30, "FILTER3")
#     return s
#
# def backeman_ss_scenario_variant_erroneous() -> ros.System:
#     load_dotenv()
#     s, e = new_default_backeman_system("backeman_ss")
#
#     add_datagenerator(e, "SENSOR1", 10, 230, 0)
#     add_datagenerator(e, "SENSOR2", 20, 220, 0)
#     add_subscriber(e, "FILTER1", 10, "SENSOR1")
#     add_subscriber(e, "FILTER2", 20, "SENSOR2")
#     add_subscriber(e, "FUSION1", 50, "FILTER1", ["FILTER2"], [50])
#     add_subscriber(e, "FILTER3", 30, "SENSOR2")
#     add_subscriber(e, "ACTUATOR1", 30, "FILTER3")
#     return s
