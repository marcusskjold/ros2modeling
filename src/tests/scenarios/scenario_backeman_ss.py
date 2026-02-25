import roserer.ros2system as ros
import roserer.experiments.backeman as be
import roserer.experiments.experimenter as exp
from roserer.patterns.backeman import (
        add_datagenerator,
        add_subscriber,
        )


def scenario_backeman_ss() -> None:
    from dotenv import load_dotenv
    load_dotenv()
    print("Constructing system")

    s = ros.System("test", dds_implementation="Generic")
    s.default_qos.depth = 20

    h = s.add_host(operating_system="Generic")
    e = h.add_executor(implementation="SingleThreadedExecutor", ros_distribution="Eloquent")

    # This setup is exactly translated from backeman/demo.py:validation_ss()
    # Except: We assume that fusion should read from the filters, not the sensors.
    #         Therefor we assume that it is a mistake in the original function.
    add_datagenerator(e, "SENSOR1", 10, 360, 0)
    add_datagenerator(e, "SENSOR2", 20, 360, 0)
    add_subscriber(e, "FILTER1", 10, "SENSOR1")
    add_subscriber(e, "FILTER2", 20, "SENSOR2")
    add_subscriber(e, "FUSION1", 30, "FILTER1", ["FILTER2"], [30])
    add_subscriber(e, "FILTER3", 30, "FUSION1")
    add_subscriber(e, "ACTUATOR1", 30, "FILTER3")
    
    result = exp.perform_reaction_time_experiment(s, "backeman-ss", be.backeman_rt_experiment)
    # See Backeman & Seceleanu (2025) Table 3 (p.310)
    assert result == 540
