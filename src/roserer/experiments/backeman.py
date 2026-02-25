import roserer.ros2system as ros
import roserer.systemvalidator as sv
import roserer.adapters.backeman_adapter as ba
import logging


def backeman_rt_experiment(
        s: ros.System,
        r: sv.ValidationResult,
        monitor: str,
        actuator: str,
        ) -> int:
    logger = logging.getLogger(__name__)
    monitor_cb: str = ""
    actuator_cb: str = ""
    for n in s.get_nodes():
        if n.name == monitor:
            for cb in n.callbacks:
                if cb.publishers != []:
                    monitor_cb = cb.name
            assert monitor_cb != ""
        if n.name == actuator:
            for cb in n.callbacks:
                if cb.publishers != []:
                    actuator_cb = cb.name
            assert actuator_cb != ""
    chain = r.get_paths_from(monitor_cb , actuator_cb)[0]
    logger.info(f"Chain to monitor: {chain}")
    logger.info("Transforming system")
    errors, warnings, bksystem = ba.transform_system(s, chain)
    for ln in errors:
        logger.error(ln)
    for ln in warnings:
        logger.warning(ln)
    if bksystem is not None:
        ba.monitor(bksystem, monitor, actuator)
        logger.info("Measuring max reaction time of chain")
        time, _, _ = bksystem.max_reaction_time(gen_graph=False)
        if time is not None:
            logger.info(f"Max reaction time: {time}")
            return time
    return -1
