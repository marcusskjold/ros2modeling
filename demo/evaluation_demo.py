import roserer.ros2system as ros
from roserer.patterns.backeman import (
        new_default_backeman_system,
        add_datagenerator,
        add_subscriber,
        add_timer
        )

import roserer.adapters.backeman_adapter as ba
def backeman_st_scenario(name: str = "backeman_st") -> ros.System:
    s, e = new_default_backeman_system(name)

    add_datagenerator(e, "SENSOR1", 10, 420, 0)
    add_datagenerator(e, "SENSOR2", 20, 420, 0)
    add_subscriber(e, "FILTER1", 10, "SENSOR1")
    add_subscriber(e, "FILTER2", 20, "SENSOR2")
    add_subscriber(e, "FUSION1", 30, "FILTER1", ["FILTER2"], [30])
    add_subscriber(e, "FILTER3", 30, "FUSION1")
    add_timer(e, "ACTUATOR1", 30, 840, 0, ["FILTER3"], [30])
    return s

feedback, system = ba.transform_system(
        backeman_st_scenario(), ("SENSOR1", "ACTUATOR1"), True)
print(feedback)
assert system is not None
mrt, _, _ = system.max_reaction_time()
print(mrt)
