from roserer.types import DISTRIBUTION
import logging
import roserer.ros2system as ros
from roserer.patterns.backeman import (
        new_default_backeman_system,
        add_datagenerator,
        add_probabilistic_datagenerator,
        add_subscriber,
        add_timer
        )
from dotenv import load_dotenv
import roserer.adapters.backeman_adapter as ba
import roserer.backeman.system as backeman

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

def backeman_st_scenario_erroneous(name: str = "backeman_st_erroneous") -> ros.System:
    load_dotenv()
    s, e = new_default_backeman_system(name)

    add_datagenerator(e, "SENSOR1", 10, 420, 0)
    add_datagenerator(e, "SENSOR2", 20, 420, 0)
    add_subscriber(e, "FILTER1", 10, "SENSOR1")
    add_subscriber(e, "FILTER2", 20, "SENSOR2")
    add_subscriber(e, "FUSION1", 30, "SENSOR1", ["SENSOR2"], [30])
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

# Case study has following parameters:
# - cameras: No. of cameras
# - prob: probability of each camera being used (load)
# - mcamera: which camera should be monitored
# - subcription: if True, subscription is used of fusion (otherwise Timer)
#
def case_study(cameras, prob, mcamera, subscription, fusion_period=500) -> backeman.System | None:
    log = logging.getLogger(__name__)

    CAMERAWCET = 20
    CAMERAPER = 1000
    OBJDETWCET = 50
    FUSIONSUBWCET = 90
    FUSIONSUB = 10
    FUSIONTIMERWCET = 90
    ACTUATORWCET = 50
    
    if mcamera >= cameras:
        return None

    if subscription:
        name = "casestudy" + str(cameras) + "_" + str(mcamera) + "_sub" + str(prob)
    else:
        name = "casestudy" + str(cameras) + "_" + str(mcamera) + "_tmr" + str(prob)

    system = ros.System(name)
    e = system.add_host("host").add_executor("executor", ros_distribution=DISTRIBUTION.Humble)

    for i in range(cameras):
        add_probabilistic_datagenerator(
                e, "CAMERA" + str(i), CAMERAWCET, CAMERAPER, 0, prob)
        add_subscriber(e, "OBJDET" + str(i), OBJDETWCET, "CAMERA" + str(i))

    if subscription:
        add_subscriber(
                e,
                "FUSION",
                FUSIONSUBWCET,
                "OBJDET0",
                ["OBJDET" + str(i) for i in range(1,cameras)],
                [FUSIONSUB]*(cameras-1))
    else:
        add_timer(
                e,
                "FUSION",
                FUSIONTIMERWCET,
                fusion_period,
                0,
                ["OBJDET" + str(i) for i in range(cameras)],
                [FUSIONSUB]*cameras)
    add_subscriber(e, "ACTUATOR", ACTUATORWCET, "FUSION")
    feedback, bms = ba.transform_system(system, (f"CAMERA{mcamera}", "ACTUATOR"))
    # for node in RosGraphView(system).get_all_nodes():
    #     log.debug(node)
    log = logging.getLogger(__name__)
    for ln in feedback.errors:
        log.info(ln)
    assert isinstance(bms, backeman.System)
    return bms

