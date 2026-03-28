import roserer.ros2system as ros
import roserer.adapters.backeman_adapter as ba
from roserer.backeman.system import System
from roserer.patterns.backeman import (
        new_default_backeman_system,
        add_datagenerator,
        add_subscriber,
        add_timer
        )

# Backeman original validation case
def validation_st():
    system = System("st")
    system.add_datagenerator("SENSOR1", 420, 10, 0, True, 6)
    system.add_datagenerator("SENSOR2", 420, 20, 0, False, 5)
    system.add_subscriber("FILTER1", "SENSOR1", 10, [], [], "pd")
    system.add_subscriber("FILTER2", "SENSOR2", 20, [], [], "pd")
    system.add_subscriber("FUSION1", "SENSOR1", 30, ["SENSOR2"], [30], "pd")
    system.add_subscriber("FILTER3", "FUSION1", 30, [], [], "pd")
    system.add_timer("ACTUATOR1", 840, 0, 30, ["FILTER3"], [30],
                     "ACTUATOR1xFILTER3_data", 4, [-3])
    system.monitor("ACTUATOR1", 420)
    return system

# Recreating the validation case
def backeman_st_scenario(name: str = "backeman_st") -> ros.System:
    s, e = new_default_backeman_system(name)

    add_datagenerator(e, "SENSOR1", 10, 420, 0)
    add_datagenerator(e, "SENSOR2", 20, 420, 0)
    add_subscriber(e, "FILTER1", 10, "SENSOR1")
    add_subscriber(e, "FILTER2", 20, "SENSOR2")
    add_subscriber(e, "FUSION1", 30, "SENSOR1", ["SENSOR2"], [30])
    add_subscriber(e, "FILTER3", 30, "FUSION1")
    add_timer(e, "ACTUATOR1", 30, 840, 0, ["FILTER3"], [30])
    return s

feedback, system = ba.transform_system(backeman_st_scenario(), ("SENSOR1", "ACTUATOR1"), True)

assert system is not None
bmsystem = validation_st()

# The only line of difference in the UPPAAL output is the priority array.
# This array still results in the exact same prioritization order.
# The difference is caused by the original Backeman priorities being made by hand,
# where our version has to assign priorities programatically.
for ln1, ln2 in zip((system.gen_declaration() + system.gen_system()).split(),
                    (bmsystem.gen_declaration() + bmsystem.gen_system()).split()):
    if ln1 != ln2:
        print("Difference:")
        print(ln1)
        print("==================")
        print(ln2)
        print()


print("BACKEMAN ORIGINAL FEEDBACK, observe warnings for FILTER1 and FILTER2")
print(feedback)
print()

def backeman_st_scenario_fixed(name: str = "backeman_st_fixed") -> ros.System:
    s, e = new_default_backeman_system(name)

    add_datagenerator(e, "SENSOR1", 10, 420, 0)
    add_datagenerator(e, "SENSOR2", 20, 420, 0)
    add_subscriber(e, "FILTER1", 10, "SENSOR1")
    add_subscriber(e, "FILTER2", 20, "SENSOR2")
    add_subscriber(e, "FUSION1", 30, "FILTER1", ["FILTER2"], [30])
    add_subscriber(e, "FILTER3", 30, "FUSION1")
    add_timer(e, "ACTUATOR1", 30, 840, 0, ["FILTER3"], [30])
    return s

feedback, system = ba.transform_system(backeman_st_scenario_fixed(), ("SENSOR1", "ACTUATOR1"), True)

print("BACKEMAN ST FIXED FEEDBACK, observe now we only get a warning for the ACTUATOR1 topic")
print(feedback)

assert system is not None
mrt, _, _ = system.max_reaction_time()
print(mrt)
