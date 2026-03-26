import logging
import pytest
from roserer.types import OPERATING_SYSTEM, DISTRIBUTION, EXECUTOR, DDS_IMPLEMENTATION
from roserer.printers.graph_printer import GraphDrawer
import roserer.experiments.backeman as be
import roserer.experiments.experimenter as exp
import roserer.patterns.backeman as bmp
import roserer.scenarios.backeman as bs
from roserer.systemvalidator import validate_system
import roserer.ros2system as ros
from functools import partial
from dotenv import load_dotenv

# ===================================== Manual vs pattern based equivalence

def gen_backeman_ss_manual() -> ros.System:
    load_dotenv()

    system = ros.System("backeman_ss", dds_implementation=DDS_IMPLEMENTATION.Generic)
    system.default_qos.depth = 20

    host = system.add_host(operating_system=OPERATING_SYSTEM.Generic)
    executor = host.add_executor(
            implementation=EXECUTOR.SingleThreadedExecutor,
            ros_distribution=DISTRIBUTION.Eloquent)

    s1 = executor.add_node(name="SENSOR1")
    s2 = executor.add_node(name="SENSOR2")
    f1 = executor.add_node(name="FILTER1")
    f2 = executor.add_node(name="FILTER2")
    fu = executor.add_node(name="FUSION1")
    f3 = executor.add_node(name="FILTER3")
    act = executor.add_node(name="ACTUATOR1")

    pub1 = s1.add_publisher(topic="SENSOR1")
    cb1 = s1.add_callback(wcet=10, publishers=[pub1])
    s1.add_timer(period=360, callback=cb1)

    pub2 = s2.add_publisher(topic="SENSOR2")
    cb2 = s2.add_callback(wcet=20, publishers=[pub2])
    s2.add_timer(period=360, callback=cb2)

    pub3 = f1.add_publisher(topic="FILTER1")
    cb3 = f1.add_callback(wcet=10, publishers=[pub3])
    f1.add_subscription(topic="SENSOR1", callback=cb3)


    pub4 = f2.add_publisher(topic="FILTER2")
    cb4 = f2.add_callback(wcet=20, publishers=[pub4])
    f2.add_subscription(topic="SENSOR2", callback=cb4)

    var1 = fu.add_variable()
    cb5 = fu.add_callback(wcet=30, write_variables=[var1])
    fu.add_subscription(topic="FILTER2", callback=cb5)
    pub5 = fu.add_publisher(topic="FUSION1")
    cb6 = fu.add_callback(wcet=30, publishers=[pub5], read_variables=[var1])
    fu.add_subscription(topic="FILTER1", callback=cb6)

    pub6 = f3.add_publisher(topic="FILTER3")
    cb7 = f3.add_callback(wcet=30, publishers=[pub6])
    f3.add_subscription(topic="FUSION1", callback=cb7)

    pub7 = act.add_publisher(topic="ACTUATOR1")
    cb8 = act.add_callback(wcet=30, publishers=[pub7])
    act.add_subscription(topic="FILTER3", callback=cb8)

    return system

def test_backeman_scenarios_are_equivalent() -> None:

    pattern = bs.backeman_ss_scenario()
    manual = gen_backeman_ss_manual()

    assert pattern == manual

# ===================== Results tests

def scenario_backeman_ss() -> None:
    from dotenv import load_dotenv
    load_dotenv()

    s = bs.backeman_ss_scenario()

    experiment = partial(be.backeman_rt_experiment,
                         monitor="SENSOR1",
                         actuator="ACTUATOR1",
                         external_event=True)

    result = exp.perform_reaction_time_experiment(s, "backeman/ss", experiment)
    # See Backeman & Seceleanu (2025) Table 3 (p.310)
    assert result == 540

def scenario_backeman_ss_erroneous() -> None:
    """
    Even though this system is erroneous, the results are the same as the
    correct version.
    """
    from dotenv import load_dotenv
    load_dotenv()
    s = bs.backeman_ss_scenario_erroneous()
    experiment = partial(be.backeman_rt_experiment,
                         monitor="SENSOR1",
                         actuator="ACTUATOR1",
                         external_event=True)
    result = exp.perform_reaction_time_experiment(
            s, "backeman/ss-errroneous", experiment)
    # See Backeman & Seceleanu (2025) Table 3 (p.310)
    assert result == 540


def scenario_backeman_ss_variant() -> None:
    """
    This test shows that:
    - The mistake found in the backeman validation cases can result in different results
      if the system in question has different timing specification.
    - That our validation gives a warning that would help the user discover this error.
    - That this is made clear by the graphic representation of the systems
    """
    from dotenv import load_dotenv
    load_dotenv()
    s1 = bs.backeman_ss_scenario_variant()
    s2 = bs.backeman_ss_scenario_variant_erroneous()
    experiment = partial(be.backeman_rt_experiment,
                         monitor="SENSOR2",
                         actuator="ACTUATOR1",
                         external_event=True)
    result1 = exp.perform_reaction_time_experiment(
            s1, "backeman/ss-variant", experiment)
    result2 = exp.perform_reaction_time_experiment(
            s2, "backeman/ss-variant-erroneous", experiment)
    # See Backeman & Seceleanu (2025) Table 3 (p.310)
    assert result1 == 660
    assert result2 == 650
    assert result1 != result2
    assert not any("[W001]: topic FILTER2 is published to, but not subscribed to"
                   in warn for warn in validate_system(s1).warnings)
    assert any("[W001]: topic FILTER2 is published to, but not subscribed to"
               in warn for warn in validate_system(s2).warnings)

def scenario_backeman_st() -> None:
    from dotenv import load_dotenv
    load_dotenv()
    s = bs.backeman_st_scenario()
    experiment = partial(be.backeman_rt_experiment,
                         monitor="SENSOR1",
                         actuator="ACTUATOR1",
                         external_event=True)
    result = exp.perform_reaction_time_experiment(s, "backeman/st", experiment)
    # See Backeman & Seceleanu (2025) Table 3 (p.310)
    assert result == 1320

def scenario_backeman_ts() -> None:
    from dotenv import load_dotenv
    load_dotenv()
    s = bs.backeman_ts_scenario()
    experiment = partial(be.backeman_rt_experiment,
                         monitor="SENSOR1",
                         actuator="ACTUATOR1",
                         external_event=True)
    result = exp.perform_reaction_time_experiment(s, "backeman/ts", experiment)
    # See Backeman & Seceleanu (2025) Table 3 (p.310)
    assert result == 1470

def scenario_backeman_tt() -> None:
    from dotenv import load_dotenv
    load_dotenv()
    s = bs.backeman_tt_scenario()
    experiment = partial(be.backeman_rt_experiment,
                         monitor="SENSOR1",
                         actuator="ACTUATOR1",
                         external_event=True)
    result = exp.perform_reaction_time_experiment(s, "backeman/tt", experiment)
    # See Backeman & Seceleanu (2025) Table 3 (p.310)
    assert result == 2490

def scenario_backeman_prio_inversion():
    """
    This is a validation case that demonstrates how the worst case reaction time may
    be greater for non-deterministic models that allow for callbacks to be executed
    faster than wcet.
    In the report (Backeman & Seceleanu 2025), the results are reported as 80 & 230 for
    the deterministic and nondeterministic case respectively (p. 303, 311)
    This is because this is measuring the reaction time of the *job chain*, meaning the
    time it takes from the moment a timer releases a task till the moment the actuator
    callback has been completed. The semantics of the monitor template (p.308) explain
    that the worst-case reaction time from an external event occuring is equal to the
    reaction time of the job chain + the period of the data generator.
    In our modelling of the system, we have decided that we stick to measuring the
    worst case reaction time for external events.
    Therefor we expect the results to be 80 + 150 = 230 and 230 + 150 = 380.
    """
    from dotenv import load_dotenv
    load_dotenv()
    s = bs.backeman_prio_inversion_scenario()
    experiment = partial(be.backeman_rt_experiment,
                         monitor="SENSOR2",
                         actuator="ACTUATOR",
                         external_event=True)
    result1 = exp.perform_reaction_time_experiment(s, "backeman/prio_inversion", experiment)
    # 80 + 150 == 230
    assert result1 == 230
    bmp.make_nondeterministic(s)
    experiment = partial(be.backeman_rt_experiment,
                         monitor="SENSOR2",
                         actuator="ACTUATOR",
                         external_event=True)
    result2 = exp.perform_reaction_time_experiment(s, "backeman/prio_inversion", experiment)
    # 230 + 150 == 380
    assert result2 == 380
